"""The bundled gate run: a green run recorded by its tree, and reused only on that tree.

Real git and make in a scratch repository. Why: 0064-lighter-catch-up design D1.
"""

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "gate_run.py"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path, log: Path, recipe: str = "true") -> None:
    """Commit a repo whose gate logs each run to `log`, then runs `recipe`."""
    root.mkdir()
    _git(root, "init", "-q")
    makefile = f"gate:\n\techo run $(MODE) >> {log}\n\t{recipe}\n"
    (root / "Makefile").write_text(makefile)
    (root / ".gitignore").write_text(".minions/\n")
    (root / "README.md").write_text("x\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")


def _gate(root: Path, *extra: str, mode: str = "a") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *extra],
        cwd=root,
        env={**os.environ, "MODE": mode},
        capture_output=True,
        text=True,
    )


def _runs(log: Path) -> int:
    return len(log.read_text().splitlines()) if log.exists() else 0


def _record(root: Path) -> Path:
    return root / ".minions" / "gate" / _git(root, "write-tree")


def test_a_green_run_is_recorded_and_reused_on_the_same_tree(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log)
    tree = _git(root, "write-tree")

    first = _gate(root)
    assert first.returncode == 0, first.stdout
    assert first.stdout.splitlines()[-1].startswith(f"gate: green — {tree} · ")
    assert _runs(log) == 1
    record = _record(root).read_text().splitlines()
    assert [line.partition(": ")[0] for line in record] == ["dry", "date", "seconds"]

    again = _gate(root)
    assert again.returncode == 0, again.stdout
    assert again.stdout.startswith(f"gate: reused — {tree} · "), again.stdout
    assert _runs(log) == 1

    # A staged edit is the tree its commit will hold: the commit reuses its record.
    (root / "README.md").write_text("y\n")
    _git(root, "add", "README.md")
    staged = _gate(root)
    assert "gate: green — " in staged.stdout and _runs(log) == 2
    _git(root, "commit", "-q", "-m", "edit")
    committed = _gate(root)
    assert committed.stdout.startswith("gate: reused — "), committed.stdout
    assert _runs(log) == 2


def test_a_red_run_records_nothing(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log, recipe="false")
    for _ in range(2):
        result = _gate(root)
        assert result.returncode == 2, result.stdout
        assert result.stdout.splitlines()[-1].startswith("gate: red — exit 2 · ")
    assert _runs(log) == 2
    assert not _record(root).exists()


def test_a_gate_runs_without_the_venv_and_quiet_when_green(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    seen = tmp_path / "venv.txt"
    _repo(root, log, recipe=f"echo venv=$(VIRTUAL_ENV) > {seen}")
    env = {**os.environ, "MODE": "a", "VIRTUAL_ENV": str(tmp_path / "conductor-venv")}

    def gate() -> subprocess.CompletedProcess[str]:
        argv = [sys.executable, str(_SCRIPT)]
        return subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True)

    green = gate()
    assert green.returncode == 0, green.stdout
    [line] = green.stdout.splitlines()
    assert line.startswith("gate: green — ")
    assert seen.read_text() == "venv=\n"

    # A red gate prints make's output, then its summary last.
    (root / "Makefile").write_text("gate:\n\techo boom\n\tfalse\n")
    red = gate()
    assert red.returncode == 2, red.stdout
    lines = red.stdout.splitlines()
    assert "boom" in lines
    assert lines[-1].startswith("gate: red — exit 2 · ")


def test_reuse_is_refused_on_a_dirty_tree(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log)
    assert _gate(root).returncode == 0

    (root / "README.md").write_text("unstaged\n")
    unstaged = _gate(root)
    assert unstaged.returncode == 0
    assert "gate: green — unrecorded, the worktree is not settled" in unstaged.stdout
    (root / "README.md").write_text("x\n")
    (root / "new.txt").write_text("untracked\n")
    untracked = _gate(root)
    assert "gate: green — unrecorded" in untracked.stdout
    assert _runs(log) == 3

    # The guard's twin: the same tree, settled again, reuses the record.
    (root / "new.txt").unlink()
    assert _gate(root).stdout.startswith("gate: reused — ")
    assert _runs(log) == 3


def test_reuse_is_refused_on_another_tree(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log)
    assert _gate(root).returncode == 0
    (root / "README.md").write_text("y\n")
    _git(root, "commit", "-q", "-am", "edit")
    result = _gate(root)
    assert "gate: green — " in result.stdout, result.stdout
    assert _runs(log) == 2


def test_reuse_is_refused_on_a_changed_dry_run(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log)
    assert _gate(root, mode="a").returncode == 0
    result = _gate(root, mode="b")
    assert "gate: green — " in result.stdout, result.stdout
    assert _runs(log) == 2
    assert _gate(root, mode="b").stdout.startswith("gate: reused — ")


def test_fresh_runs_whatever_stands_and_records(tmp_path: Path) -> None:
    root, log = tmp_path / "repo", tmp_path / "runs.log"
    _repo(root, log)
    assert _gate(root).returncode == 0
    dry = _record(root).read_text().splitlines()[0]
    _record(root).write_text(f"{dry}\ndate: then\nseconds: 1\n")
    assert _gate(root).stdout.startswith("gate: reused — ")
    tree = _git(root, "write-tree")
    fresh = _gate(root, "--fresh")
    assert fresh.stdout.splitlines()[-1].startswith(f"gate: green — {tree} · ")
    assert _runs(log) == 2
    assert "date: then" not in _record(root).read_text()
    assert _gate(root).stdout.startswith("gate: reused — ")

    # A link a worker planted at the staged record is removed, not written through.
    outside = tmp_path / "home-file"
    outside.write_text("the person's\n")
    _record(root).with_name(f"{_record(root).name}.tmp").symlink_to(outside)
    planted = _gate(root, "--fresh")
    assert planted.stdout.splitlines()[-1].startswith(f"gate: green — {tree} · ")
    assert outside.read_text() == "the person's\n"
    assert not _record(root).is_symlink()
    assert _record(root).read_text().startswith("dry: ")

    # A linked record folder takes no record.
    folder = root / ".minions" / "gate"
    elsewhere = tmp_path / "elsewhere"
    folder.rename(elsewhere)
    folder.symlink_to(elsewhere)
    (elsewhere / tree).unlink()
    linked = _gate(root, "--fresh")
    assert linked.returncode == 0, linked.stdout
    assert "gate: green — unrecorded, .minions/gate is a link" in linked.stdout
    assert list(elsewhere.iterdir()) == []


def test_records_go_under_the_primary_run_directory(tmp_path: Path) -> None:
    primary, worktree = tmp_path / "primary", tmp_path / "v0.2_x"
    log = tmp_path / "runs.log"
    _repo(primary, log)
    _git(primary, "worktree", "add", "-q", "-b", "v0.2_x", str(worktree))
    assert _gate(worktree).returncode == 0
    assert (primary / ".minions" / "gate" / _git(worktree, "write-tree")).is_file()
    assert not (worktree / ".minions").exists()
    assert _gate(primary).stdout.startswith("gate: reused — ")

    # `--tree` gates the worktree from the primary, and records it under the primary.
    (worktree / "README.md").write_text("w\n")
    _git(worktree, "commit", "-q", "-am", "edit")
    tree = _git(worktree, "write-tree")
    named = _gate(primary, "--tree", str(worktree))
    assert named.returncode == 0, named.stdout
    assert named.stdout.splitlines()[-1].startswith(f"gate: green — {tree} · ")
    assert (primary / ".minions" / "gate" / tree).is_file()
    assert _runs(log) == 2

    missing = _gate(primary, "--tree", str(tmp_path / "gone"))
    assert missing.returncode == 2, missing.stdout
    assert missing.stdout.startswith("gate: cannot run — "), missing.stdout
    assert _runs(log) == 2


def test_diff_coverage_takes_the_stacked_base(tmp_path: Path) -> None:
    # Why: 0099-stacked-builds design D5.
    primary, worktree = tmp_path / "primary", tmp_path / "0002-marks"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    (primary / "Makefile").write_text((_REPO / "Makefile").read_text())
    _git(primary, "add", "Makefile")
    _git(primary, "commit", "-q", "-m", "base")
    _git(primary, "worktree", "add", "-q", "-b", "0002-marks", str(worktree))
    stacked_on = primary / ".minions" / "changes" / "0002-marks" / "stacked-on"
    stacked_on.parent.mkdir(parents=True)
    # CI's `make gate DIFF_BASE=origin/main` would pass these in.
    dropped = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "DIFF_BASE")
    env = {key: value for key, value in os.environ.items() if key not in dropped}

    def compared() -> list[str]:
        dry = subprocess.run(
            ["make", "-n", "gate"],
            cwd=worktree,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [word for word in dry.split() if word.startswith("--compare-branch=")]

    assert compared() == ["--compare-branch=main"]
    sha = _git(primary, "rev-parse", "HEAD")
    stacked_on.write_text(f"{sha}\n")
    assert compared() == [f"--compare-branch={sha}"]
    made = tmp_path / "made"
    stacked_on.write_text(f'x"; touch {made}; "\n')
    assert compared() == ["--compare-branch=main"]
    assert not made.exists()
