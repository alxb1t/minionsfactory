"""The cut's preconditions: real git in a scratch repository, a fake `openspec` on PATH.

Why: 0106-cut-scripts design D5.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "cut_pre.py"
_ID = "0003-new"
_GATE = "gate:\n\t@echo gating\n"
_FAKE = '#!/bin/sh\n[ "$1" = --version ] && echo 1.11.0\nexit 0\n'


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("cut_pre", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cut_pre = _load(_SCRIPT)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(root: Path, message: str) -> None:
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)


def _put(root: Path, name: str, text: str) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text)


def _repo(tmp_path: Path, agents: bool = True, gate: str = _GATE) -> Path:
    """Commit a repository on `main` holding one archived change, `0001-old`."""
    root = tmp_path / "primary"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _put(root, ".gitignore", ".minions/\n")
    _put(root, "Makefile", gate)
    _put(root, "openspec/changes/archive/0001-old/tasks.md", "x\n")
    if agents:
        _put(root, "AGENTS.md", "# agents\n")
    _commit(root, "base")
    return root


def _open_version(root: Path, name: str) -> None:
    """Leave `name` as a branch with a change of its own, unmerged into `main`."""
    _git(root, "checkout", "-q", "-b", name)
    _put(root, f"openspec/changes/{name}/tasks.md", "x\n")
    _commit(root, name)
    _git(root, "checkout", "-q", "main")


def _tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a fake `openspec` first on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "openspec"
    fake.write_text(_FAKE)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def _run(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *argv: str,
) -> tuple[int, list[str]]:
    monkeypatch.chdir(root)
    code = cut_pre.main(list(argv))
    return code, capsys.readouterr().out.splitlines()


def test_every_precondition_holds_by_hand(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _open_version(root, "0002-open")
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, _ID, "--after", "0002-open")
    assert lines == [
        "cut_pre: ok — agents",
        "cut_pre: ok — tree",
        "cut_pre: ok — openspec",
        "cut_pre: ok — gate",
        "cut_pre: ok — reserved",
        "cut_pre: ok — id",
        "cut_pre: ok — after",
    ]
    assert code == 0


def _dirty(root: Path) -> None:
    _put(root, "stray.txt", "x\n")


def _off_default(root: Path) -> None:
    _git(root, "checkout", "-q", "-b", "side")


def _taken(root: Path) -> None:
    _open_version(root, "0003-taken")


def _reserved(root: Path) -> None:
    _put(root, ".minions/cuts/0003-new", "")


def _lower_than_a_reservation(root: Path) -> None:
    _put(root, ".minions/cuts/0004-queued", "")


def _empty_gate(root: Path) -> None:
    _put(root, "Makefile", "gate:\n")
    _commit(root, "empty gate")


def _no_gate(root: Path) -> None:
    _put(root, "Makefile", "other:\n\t@echo x\n")
    _commit(root, "no gate")


@pytest.mark.parametrize(
    ("check", "setup", "argv", "agents"),
    [
        ("agents", None, [], False),
        ("tree", _dirty, [], True),
        ("tree", _off_default, [], True),
        ("id", _taken, [], True),
        ("id", _lower_than_a_reservation, [], True),
        ("reserved", _reserved, [], True),
        ("gate", _empty_gate, [], True),
        ("gate", _no_gate, [], True),
        ("after", None, ["--after", "0002-gone"], True),
    ],
)
def test_each_failed_precondition_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    check: str,
    setup: Callable[[Path], None] | None,
    argv: list[str],
    agents: bool,
) -> None:
    root = _repo(tmp_path, agents=agents)
    if setup:
        setup(root)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, _ID, *argv)
    failed = [line for line in lines if line.startswith("cut_pre: halt — ")]
    assert [line.split(" — ")[1].split(":")[0] for line in failed] == [check]
    assert code == 1
    assert all(line.startswith("cut_pre: ") for line in lines)


def test_a_queued_id_names_the_answer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _reserved(root)
    _tools(tmp_path, monkeypatch)
    _, lines = _run(root, monkeypatch, capsys, _ID)
    assert (
        "cut_pre: halt — reserved: 0003-new is queued for the cut station: answer it"
        " in the brief, then conduct.py rejoin 0003-new"
    ) in lines


def test_every_failed_check_shows_in_one_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path, gate="gate:\n")
    _dirty(root)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, _ID)
    halted = [line.split(" — ")[1].split(":")[0] for line in lines if "halt" in line]
    assert halted == ["tree", "gate"]
    assert code == 1


def test_a_missing_openspec_is_a_halt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("git", "make"):
        found = shutil.which(name)
        assert found
        (tools / name).symlink_to(found)
    monkeypatch.setenv("PATH", str(tools))
    code, lines = _run(root, monkeypatch, capsys, _ID)
    assert "cut_pre: halt — openspec: openspec is not on PATH" in lines
    assert code == 1


def test_an_openspec_that_fails_is_a_halt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    (tmp_path / "bin" / "openspec").write_text("#!/bin/sh\nexit 3\n")
    code, lines = _run(root, monkeypatch, capsys, _ID)
    assert "cut_pre: halt — openspec: `openspec --version` exited 3" in lines
    assert code == 1


def _worktree(root: Path, branch: str = _ID) -> Path:
    """Add a linked worktree on a new branch off `main`, beside the primary."""
    path = root.parent / branch
    _git(root, "worktree", "add", "-q", "-b", branch, str(path), "main")
    return path


def test_unattended_preconditions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _open_version(root, "0002-open")
    _reserved(root)
    work = _worktree(root)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(
        work, monkeypatch, capsys, _ID, "--unattended", "--after", "0002-open"
    )
    assert lines == [
        "cut_pre: ok — agents",
        "cut_pre: ok — tree",
        "cut_pre: ok — openspec",
        "cut_pre: ok — gate",
        "cut_pre: ok — reserved",
        "cut_pre: ok — after",
    ]
    assert code == 0


def _unattended_halts(
    where: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *argv: str,
) -> list[str]:
    code, lines = _run(where, monkeypatch, capsys, _ID, "--unattended", *argv)
    assert code == 1
    return [line.split(" — ")[1].split(":")[0] for line in lines if "halt" in line]


def test_an_unattended_cut_without_its_reservation_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    work = _worktree(root)
    _tools(tmp_path, monkeypatch)
    assert _unattended_halts(work, monkeypatch, capsys) == ["reserved"]


def test_an_unattended_cut_in_the_primary_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _reserved(root)
    _tools(tmp_path, monkeypatch)
    assert _unattended_halts(root, monkeypatch, capsys) == ["tree"]


def test_an_unattended_cut_on_another_branch_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _reserved(root)
    work = _worktree(root, "0003-other")
    _tools(tmp_path, monkeypatch)
    assert _unattended_halts(work, monkeypatch, capsys) == ["tree"]


def test_an_unattended_cut_past_the_default_branch_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _reserved(root)
    work = _worktree(root)
    _put(work, "more.txt", "x\n")
    _commit(work, "ahead")
    _tools(tmp_path, monkeypatch)
    assert _unattended_halts(work, monkeypatch, capsys) == ["tree"]


def test_an_unattended_after_not_lower_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _open_version(root, "0004-open")
    _reserved(root)
    work = _worktree(root)
    _tools(tmp_path, monkeypatch)
    halts = _unattended_halts(work, monkeypatch, capsys, "--after", "0004-open")
    assert halts == ["after"]


def test_an_unattended_cut_in_a_dirty_worktree_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _reserved(root)
    work = _worktree(root)
    _dirty(work)
    _tools(tmp_path, monkeypatch)
    assert _unattended_halts(work, monkeypatch, capsys) == ["tree"]


def test_the_default_branch_is_origins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    assert cut_pre.default_branch() == "main"
    _git(root, "update-ref", "refs/remotes/origin/trunk", "HEAD")
    _git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    assert cut_pre.default_branch() == "trunk"


def test_what_cannot_be_checked_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, "bad_id")
    assert code == 2
    assert lines == ["cut_pre: cannot check — `bad_id` is not <digits>-<slug>"]
    bare = tmp_path / "bare"
    bare.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    code, lines = _run(bare, monkeypatch, capsys, _ID)
    assert code == 2
    assert lines[0].startswith("cut_pre: cannot check — git rev-parse failed")
    monkeypatch.setenv("PATH", str(tmp_path / "nowhere"))
    code, lines = _run(root, monkeypatch, capsys, _ID)
    assert code == 2
    assert lines == ["cut_pre: cannot check — git rev-parse did not run"]


def test_the_script_runs_as_a_program(tmp_path: Path) -> None:
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "bad_id"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 2
    assert done.stdout == "cut_pre: cannot check — `bad_id` is not <digits>-<slug>\n"
