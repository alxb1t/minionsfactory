"""The ship script: stages and checks from disk, the run log, the loop, the workers.

Real git in scratch repositories with linked worktrees; `fake_worker.py` is the fake
agent `MF_SHIP_AGENT` names. Why: 0040-mf-ship design D2.
"""

import fnmatch
import json
import os
import re
import runpy
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fake_worker import _IDENTITY, _cards, _commit, _done, _findings, _git

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-ship" / "scripts" / "conduct.py"
_WORKER = Path(__file__).with_name("fake_worker.py")
_WORKTREES = (
    "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
)


def _primary(tmp_path: Path, agents: str = _WORKTREES) -> Path:
    """Return a primary checkout on `main`, its `AGENTS.md` holding `agents`."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "mf")
    _git(root, "config", "user.email", "mf@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    _commit(root, {".gitignore": ".minions/\n", "AGENTS.md": agents}, "base")
    return root.resolve()


def _version(root: Path, change: str, progress: str, after: str = "") -> Path:
    """Cut `change` on a branch of that name, linked, `progress` its list."""
    tree = root.parent / change
    _git(root, "worktree", "add", "-q", "-b", change, str(tree))
    folder = f"openspec/changes/{change}"
    line = f"after: [{after}]\n" if after else ""
    files = {
        f"{folder}/proposal.md": f"---\nbump: minor\n{line}---\n",
        f"{folder}/tasks.md": f"## Progress\n\n{progress}",
    }
    _commit(tree, files, f"cut {change}")
    return tree.resolve()


def _released(
    root: Path, tag: str, by_hand: bool = False, files: dict[str, str] | None = None
) -> None:
    """Merge a branch into `main` whose tip is `tag`'s annotated release commit.

    A run's release is in the release ledger; one by hand is not. Its build commit
    writes `files`, or none.
    """
    branch = f"release-{tag}"
    _git(root, "switch", "-q", "-c", branch)
    if files:
        _commit(root, files, f"build {tag}")
    else:
        _git(root, "commit", "-q", "--allow-empty", "-m", f"build {tag}")
    if not by_hand:
        head = _git(root, "rev-parse", "HEAD").strip()
        _conduct()["_record_release"](root, branch, head)
    _git(root, "commit", "-q", "--allow-empty", "-m", f"chore(release): {tag}")
    _git(root, "tag", "-a", "-m", tag, tag)
    _git(root, "switch", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "-m", f"Merge branch '{branch}'", branch)


def _lstart(pid: int) -> str:
    command = ["env", "LC_ALL=C", "TZ=UTC0", "ps", "-o", "lstart=", "-p", str(pid)]
    return subprocess.run(command, capture_output=True, text=True).stdout.strip()


_FAKE_PS = """
import os
import sys
from pathlib import Path

_, field, _, pid = sys.argv[1:]
try:
    os.kill(int(pid), 0)
except PermissionError:
    pass
except (OSError, OverflowError, ValueError):
    sys.exit(1)
known = Path(os.environ["FAKE_PS_REGISTRY"], f"{pid}.{field.rstrip('=')}")
if known.is_file():
    print(known.read_text())
else:
    print({"lstart=": "Mon Nov  3 10:00:00 2026", "comm=": "python3"}[field])
"""
_GROUP_START = "Mon Nov  3 09:00:00 2026"


@pytest.fixture(autouse=True)
def ps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `ps` first on `PATH`; return the registry it reads.

    A worker's sandbox refuses the real one. Why: 0058-sandboxed-gate design D1.
    """
    folder = tmp_path / "ps-bin"
    folder.mkdir()
    fake = folder / "ps"
    fake.write_text(f"#!{sys.executable} -S{_FAKE_PS}")
    fake.chmod(0o755)
    registry = tmp_path / "ps-registry"
    registry.mkdir()
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setenv("FAKE_PS_REGISTRY", str(registry))
    return registry


def _register(pid: int, comm: str, lstart: str) -> None:
    """Have the fake `ps` answer `comm` and `lstart` for `pid`."""
    registry = Path(os.environ["FAKE_PS_REGISTRY"])
    (registry / f"{pid}.comm").write_text(comm)
    (registry / f"{pid}.lstart").write_text(lstart)


def _no_ps(tmp_path: Path) -> str:
    """Return a folder whose `ps` prints nothing, to put first on `PATH`."""
    folder = tmp_path / "no-ps"
    folder.mkdir()
    ps = folder / "ps"
    ps.write_text("#!/bin/sh\nexit 1\n")
    ps.chmod(0o755)
    return str(folder)


def _conduct() -> dict[str, Any]:
    return runpy.run_path(str(_SCRIPT))


def _main(
    conduct: dict[str, Any], cwd: Path, *args: str, monkeypatch: pytest.MonkeyPatch
) -> int:
    monkeypatch.chdir(cwd)
    return conduct["main"](list(args))


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., Path]:
    """Point `MF_SHIP_AGENT` at `fake_worker.py`; return a setter of its modes."""
    calls = tmp_path / "calls.txt"

    # A gate run inside a worker inherits `HOOKS_OFF`, and these fixtures fire hooks.
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    # A remote call's scratch stands in the home folder.
    home = tmp_path / "operator-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    def modes(*names: str) -> Path:
        monkeypatch.setenv(
            "MF_SHIP_AGENT", shlex.join([sys.executable, "-S", str(_WORKER)])
        )
        monkeypatch.setenv("FAKE_CALLS", str(calls))
        monkeypatch.setenv("FAKE_MODE", ",".join(names))
        return calls

    modes()
    return modes


def _calls(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.is_file() else []


def _log(root: Path) -> list[str]:
    logs = sorted((root / ".minions" / "runs").glob("*.md"))
    return logs[-1].read_text().splitlines()[2:]


def _when_logged(
    root: Path, said: tuple[str, ...], act: Callable[[], None], hold: Path
) -> Callable[[], None]:
    """Run `act` beside the run once its log holds each of `said`, then make `hold`.

    Return the join, which raises what `act` raised.
    """
    raised: list[BaseException] = []

    def logged() -> bool:
        if not list((root / ".minions" / "runs").glob("*.md")):
            return False
        lines = _log(root)
        return all(any(part in line for line in lines) for part in said)

    def wait() -> None:
        deadline = time.monotonic() + 60
        while not logged() and time.monotonic() < deadline:
            time.sleep(0.05)
        # The halted version's thread returns after its halt line.
        time.sleep(0.5)
        try:
            act()
        except BaseException as error:
            raised.append(error)
        finally:
            hold.touch()

    thread = threading.Thread(target=wait)
    thread.start()

    def join() -> None:
        thread.join(timeout=60)
        if raised:
            raise raised[0]

    return join


def test_status_reads_each_stage_from_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — One\n")
    tasks = tree / "openspec/changes/0001-todo/tasks.md"

    def stage() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip()

    assert stage() == "0001-todo · build"
    _git(root, "remote", "add", "origin", "https://example.invalid/r.git")
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 1
    assert capsys.readouterr().out.strip() == (
        "conduct: halt — origin has no main: push it by hand"
    )
    _git(root, "remote", "remove", "origin")
    stray = root.parent / "0009-stray"
    _git(root, "worktree", "add", "-q", "-b", "0009-stray", str(stray))
    _commit(stray, {"stray.txt": "x\n"}, "not a version")
    assert stage() == "0001-todo · build"
    tasks.write_text("## Progress\n\n- [x] 1 — One\n")
    assert stage() == "0001-todo · build"
    tasks.write_text("## Progress\n\n- [x] 1 — One\n- [ ] 2 — Ship **HUMAN**\n")
    _commit(tree, {}, "a human phase")
    assert stage().endswith(" · human")
    tasks.write_text("## Progress\n\n- [x] 1 — One\n")
    _commit(tree, {}, "build")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    assert stage().endswith(" · converge")
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 3 · halt — cap reached\n")
    assert stage().endswith(" · converge-halted")
    log.write_text("# t\n\n## Run 2 — d\n10:00:00 · round 1 · done — ok\n")
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD"), verdict="blocking")
    assert stage().endswith(" · converge")
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    assert stage().endswith(" · release")
    _commit(root, {"moved.txt": "x\n"}, "main moves")
    assert stage().endswith(" · integrate")

    _commit(tree, {"moved.txt": "y\n"}, "the version moves too")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main", check=False)
    marks = root / ".minions" / "changes" / "0001-todo"
    marks.mkdir(parents=True, exist_ok=True)
    stage_of, find = conduct["stage_of"], conduct["find_version"]
    version = find(root, "0001-todo")
    assert stage() == "0001-todo · integrate"
    assert stage_of(root, version)[1].startswith("interrupted")
    ran = tmp_path / "ran.txt"
    planted = tmp_path / "planted.sh"
    planted.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(ran))}\ncat\n")
    planted.chmod(0o755)
    (root / ".git" / "info" / "attributes").write_text("* filter=probe\n")
    _git(root, "config", "filter.probe.clean", str(planted))
    os.utime(tree / "AGENTS.md", (1, 1))
    with pytest.raises(conduct["Stop"], match="filter.probe.clean"):
        stage_of(root, version)
    assert not ran.exists()
    _git(root, "config", "--unset", "filter.probe.clean")
    (marks / "integrate.md").write_text("note\n")
    assert stage_of(root, version)[1].startswith("semantic conflict")
    # A red gate an earlier committed merge left hides no open merge's note.
    older = _git(tree, "rev-parse", "HEAD~1")
    (marks / "integrate.red").write_text(f"gate red\n2026-11-05\nhead: {older}\n")
    assert stage() == "0001-todo · integrating"
    assert stage_of(root, version)[1].startswith("semantic conflict")
    (marks / "integrate.red").write_text("gate red\n")
    assert stage() == "0001-todo · integrating"
    assert stage_of(root, version)[1].startswith("red gate")
    _git(tree, "checkout", "--theirs", "moved.txt")
    _git(tree, "add", "moved.txt")
    assert stage() == "0001-todo · integrating"
    (marks / "integrate.red").unlink()
    assert stage_of(root, version)[1].startswith("semantic conflict")
    (marks / "integrate.md").unlink()
    assert stage() == "0001-todo · integrate"
    _git(tree, "merge", "--abort")

    # A red gate over the committed merge names the head it judged.
    message = "chore(integrate): merge main into 0001-todo"
    _git(tree, "merge", "-q", "--no-ff", "-s", "ours", "-m", message, "main")
    red = marks / "integrate.red"
    head = _git(tree, "rev-parse", "HEAD")
    for named in (head, head[:7]):
        red.write_text(f"gate red\n2026-11-05\nhead: {named}\n")
        assert stage() == "0001-todo · integrating"
        assert stage_of(root, version)[1].startswith("red gate")
    for named in (_git(tree, "rev-parse", "HEAD~1"), "0" * 40):
        red.write_text(f"gate red\n2026-11-05\nhead: {named}\n")
        assert stage() == "0001-todo · integrate"
    red.write_bytes(b"gate red\nhead: \xff\n")
    assert conduct["_red"](root, tree, "0001-todo") is None
    red.unlink()

    _git(tree, "commit", "-q", "--allow-empty", "-m", "chore(release): v0.1.0")
    _git(tree, "tag", "v0.1.0")
    assert stage().endswith(" · released")


@pytest.mark.slow
def test_each_check_passes_only_on_disk_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — One\n")

    def check(stage: str, target: str = "0001-todo") -> tuple[int, str]:
        capsys.readouterr()
        code = _main(conduct, root, "check", stage, target, monkeypatch=monkeypatch)
        return code, capsys.readouterr().out.strip()

    assert check("build") == (1, "check: build · fail — phase 1 unticked")
    tasks = tree / "openspec/changes/0001-todo/tasks.md"
    tasks.write_text("## Progress\n\n- [x] 1 — One\n")
    assert check("build") == (1, "check: build · fail — phase 1 unticked")
    _commit(tree, {}, "build")
    open_build = (
        "check: build · fail — no .minions/changes/0001-todo/build.done names HEAD"
    )
    assert check("build") == (1, open_build)
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD~1"))
    assert check("build") == (1, open_build)
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    assert check("build") == (0, "check: build · pass")
    (tree / "stray.txt").write_text("x\n")
    assert check("build") == (1, "check: build · fail — the tree is not clean")
    (tree / "stray.txt").unlink()
    ran = tmp_path / "ran.txt"
    planted = tmp_path / "planted.sh"
    planted.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(ran))}\ncat\n")
    planted.chmod(0o755)
    (root / ".git" / "info" / "attributes").write_text("* filter=probe\n")

    def filtered(stage: str, seconds: int) -> None:
        _git(tree, "config", "filter.probe.clean", str(planted))
        os.utime(tasks, (seconds, seconds))
        code, out = check(stage)
        assert (code, "filter.probe.clean" in out) == (1, True)
        assert not ran.exists()
        _git(tree, "config", "--unset", "filter.probe.clean")

    filtered("build", 1)

    no_done = (1, "check: converge · fail — the status log has no done")
    assert check("converge") == no_done
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n")
    assert check("converge") == (1, "check: converge · fail — no review findings file")
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD~1"))
    assert check("converge")[1].endswith(", not HEAD")
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 3 · halt — cap reached\n")
    assert check("converge") == (
        1,
        "check: converge · fail — the status log halts: 10:00:00 · round 3 · halt"
        " — cap reached",
    )
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · pickup — R1 · done — x\n")
    assert check("converge") == no_done
    log.unlink()
    assert check("converge") == no_done
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    assert check("converge") == (0, "check: converge · pass")
    filtered("converge", 2)

    _commit(root, {"moved.txt": "x\n"}, "main moves")
    assert check("integrate")[1].startswith("check: integrate · fail — HEAD is not")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main")
    marks = root / ".minions" / "changes" / "0001-todo"
    (marks / "integrate.md").write_text("note\n")
    assert check("integrate") == (
        1,
        "check: integrate · fail — integrate halted — semantic conflict,"
        " see .minions/changes/0001-todo/integrate.md",
    )
    older = _git(tree, "rev-parse", "HEAD")
    (marks / "integrate.red").write_text(f"gate red\n2026-11-05\nhead: {older}\n")
    assert check("integrate")[1].endswith(
        "semantic conflict, see .minions/changes/0001-todo/integrate.md"
    )
    (marks / "integrate.md").unlink()
    assert check("integrate") == (1, "check: integrate · fail — a merge is still open")
    (marks / "integrate.md").write_text("note\n")
    (marks / "integrate.red").write_text("gate red\n")
    assert check("integrate") == (
        1,
        "check: integrate · fail — integrate halted — red gate,"
        " see .minions/changes/0001-todo/integrate.red",
    )
    _git(tree, "merge", "--abort")
    _git(
        tree,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "chore(integrate): merge main into x",
        "main",
    )
    assert check("integrate")[0] == 1
    _git(
        tree,
        "commit",
        "-q",
        "--amend",
        "-m",
        "chore(integrate): merge main into 0001-todo",
    )
    assert check("integrate") == (0, "check: integrate · pass")
    red = marks / "integrate.red"
    red.write_text(f"gate red\n2026-11-05\nhead: {_git(tree, 'rev-parse', 'HEAD')}\n")
    assert check("integrate") == (
        1,
        "check: integrate · fail — integrate halted — red gate,"
        " see .minions/changes/0001-todo/integrate.red",
    )
    # The person's fix after the merge: the gate judged an ancestor, and the
    # check passes only once a green gate deletes `.red`.
    _commit(tree, {"fix.txt": "x\n"}, "fix the merged test")
    assert check("integrate") == (
        1,
        "check: integrate · fail — integrate halted — red gate,"
        " see .minions/changes/0001-todo/integrate.red",
    )
    red.unlink()
    assert check("integrate") == (0, "check: integrate · pass")

    assert check("release") == (
        1,
        "check: release · fail — main does not contain 0001-todo",
    )
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch '0001-todo'", "0001-todo")
    assert check("release") == (
        1,
        "check: release · fail — 0001-todo has no release commit",
    )
    _git(tree, "commit", "-q", "--allow-empty", "-m", "chore(release): v0.1.0")
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge the release", "0001-todo")
    assert check("release") == (1, "check: release · fail — v0.1.0 does not exist")
    _git(root, "tag", "v0.1.0", "main~1")
    assert check("release") == (
        1,
        "check: release · fail — v0.1.0 is not the tip of 0001-todo",
    )
    _git(root, "tag", "-f", "-a", "-m", "v0.1.0", "v0.1.0", "0001-todo")
    assert check("release") == (0, "check: release · pass")
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    monkeypatch.setenv("MF_SHIP_AGENT", "true")
    home = tmp_path / "operator-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _git(root, "remote", "add", "origin", str(origin))
    conduct["_keep_origin"](root)
    assert check("release") == (1, "check: release · fail — v0.1.0 is not on origin")
    runs = root / ".minions" / "runs"
    runs.mkdir()
    (runs / "1.md").write_text("10:00:00 · 0001-todo · spawn — release\n")

    def pushed() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.split(" · ")[3]

    _git(root, "push", "-q", "origin", "main~1:refs/tags/v0.1.0")
    assert check("release") == (1, "check: release · fail — v0.1.0 is not on origin")
    assert pushed() == "not pushed"
    _git(root, "push", "-q", "origin", "0001-todo:refs/tags/refs/tags/v0.1.0")
    assert check("release") == (1, "check: release · fail — v0.1.0 is not on origin")
    _git(root, "push", "-q", "origin", ":refs/tags/refs/tags/v0.1.0")
    _git(root, "push", "-q", "-f", "origin", "v0.1.0")
    assert check("release") == (0, "check: release · pass")
    assert pushed() == "pushed"
    _git(root, "tag", "-f", "v0.1.0", "0001-todo")
    _git(root, "push", "-q", "-f", "origin", "v0.1.0")
    assert check("release") == (0, "check: release · pass")
    assert pushed() == "pushed"
    _git(tree, "commit", "-q", "--allow-empty", "-m", "chore(release): v0.1.0")
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge the forged tip", "0001-todo")
    assert check("release") == (
        1,
        "check: release · fail — v0.1.0 is not the tip of 0001-todo",
    )
    assert pushed() == "not pushed"

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    mark = home / conduct["KEPT_ORIGINS"] / "probe-codex-1"
    mark.touch(mode=0o600)
    _git(scratch, "init", "-q")
    gate_file = conduct["probe_gate"](mark, conduct["_native"]())
    _commit(scratch, {"Makefile": gate_file}, "init")
    assert check("probe", str(scratch)) == (
        1,
        "check: probe · fail — HEAD holds no probe.txt",
    )
    _commit(scratch, {"probe.txt": "ok\n"}, "probe")
    assert check("probe", str(scratch)) == (
        1,
        "check: probe · fail — make gate left no .gated",
    )

    def gate() -> int:
        return subprocess.run(
            ["make", "gate"], cwd=scratch, capture_output=True
        ).returncode

    mark.chmod(0o400)
    assert gate() == 0
    assert check("probe", str(scratch)) == (0, "check: probe · pass")
    assert conduct["check_probe"](scratch, mark) is None
    # Twin: a mark the gate can write is written, and the gate fails.
    escaped = "codex wrote outside its reach: it runs unsandboxed"
    mark.chmod(0o600)
    (scratch / ".gated").unlink()
    assert gate() != 0
    assert not (scratch / ".gated").exists()
    assert conduct["check_probe"](scratch, mark) == escaped
    mark.unlink()
    assert conduct["check_probe"](scratch, mark) == escaped


def test_log_verify_finds_an_unpaired_spawn_and_an_open_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct = _conduct()
    start = "10:00:00 · run · start — executor claude"
    spawn = "10:00:01 · 0001-todo · spawn — build · model default"
    finish = "10:00:09 · 0001-todo · finish — build · exit 0 · 8s"
    denied = "10:00:09 · 0001-todo · denied — build · Bash(rm -rf build)"
    done = "10:00:10 · run · done — released v0.1.0"
    cases = {
        "complete": ([start, spawn, finish, denied, done], 0, "log: complete"),
        "unpaired": (
            [start, spawn, done],
            1,
            "log: incomplete — a spawn with no finish: 0001-todo build",
        ),
        "open": (
            [start, spawn, finish],
            1,
            "log: incomplete — the run ends on neither halt nor done",
        ),
        "unknown": (
            [start, "10:00:02 · run · retry — build", done],
            1,
            "log: incomplete — unknown event: 10:00:02 · run · retry — build",
        ),
    }
    for name, (lines, code, printed) in cases.items():
        log = tmp_path / f"{name}.md"
        log.write_text("# Ship run x\n\n" + "\n".join(lines) + "\n")
        capsys.readouterr()
        got = _main(
            conduct, tmp_path, "log", "--verify", str(log), monkeypatch=monkeypatch
        )
        assert (got, capsys.readouterr().out.strip()) == (code, printed), name

    runs = tmp_path / "runs"
    first, second = (conduct["RunLog"](runs, "20261029-163000") for _ in "ab")
    assert (first.path.name, second.path.name) == (
        "20261029-163000.md",
        "20261029-163000-2.md",
    )
    assert second.stamp == "20261029-163000-2"
    assert conduct["last_log"](runs) == second.path


@pytest.mark.slow
def test_a_ready_version_ships_past_a_slow_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("slow-0001-todo", "by-rule")
    root = _primary(tmp_path)
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    seen = _calls(calls)
    assert seen[0] == "probe"
    assert seen.index("build 0001-todo") < seen.index("converge 0001-todo")
    between = seen[
        seen.index("release 0002-marks") + 1 : seen.index("release 0001-todo")
    ]
    assert between[-2:] == ["integrate 0001-todo", "converge 0001-todo"]
    assert _git(root, "tag", "-l").split() == ["v0.1.0", "v0.2.0"]
    assert _git(root, "rev-parse", "v0.1.0") == _git(root, "rev-parse", "0002-marks")
    assert _git(root, "rev-parse", "v0.2.0") == _git(root, "rev-parse", "0001-todo")
    assert _git(root, "branch", "--no-merged", "main") == ""
    assert _git(root, "log", "-1", "--format=%s", "v0.2.0") == "chore(release): v0.2.0"
    assert "chore(integrate): merge main into 0001-todo" in _git(
        root, "log", "--format=%s", "main"
    )
    # The catch-up over the integrate merge replays by rule, with no worker.
    findings = root / ".minions" / "changes" / "0001-todo"
    assert "\n## By rule\n" in (findings / "review.md").read_text()
    assert " · by rule — clean, " in (findings / "status_log.md").read_text()
    lines = _log(root)
    assert lines[-1].endswith(" · run · done — released v0.1.0 v0.2.0")
    assert any(line.endswith(" · spawn — build · model default") for line in lines)
    assert not (root / ".minions" / "runs" / "active").exists()
    log = conduct["last_log"](root / ".minions" / "runs")
    assert (
        _main(conduct, root, "log", "--verify", str(log), monkeypatch=monkeypatch) == 0
    )
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    report = capsys.readouterr().out.splitlines()
    assert report[0].startswith("0001-todo · v0.2.0 · merge ")
    # The by-rule catch-up is the merges-only count's round: one past the judged one.
    assert report[0].endswith(
        " · no origin · round 2 · cards none · denied none · metrics: none"
    )
    assert report[-1] == lines[-1]
    for change in ("0001-todo", "0002-marks"):
        assert not (root.parent / change).exists()
        assert _git(root, "branch", "--list", change)
    assert _git(root, "worktree", "list", "--porcelain").count("worktree ") == 1

    elsewhere = tmp_path / "elsewhere" / "0003-more"
    _git(root, "worktree", "add", "-q", "-b", "0003-more", str(elsewhere))
    folder = "openspec/changes/0003-more"
    cut = {
        f"{folder}/proposal.md": "---\nbump: minor\n---\n",
        f"{folder}/tasks.md": "## Progress\n\n- [ ] 1 — More\n",
    }
    _commit(elsewhere, cut, "cut 0003-more")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )
    assert elsewhere.is_dir()
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert (
        f" · 0003-more · kept — {elsewhere.resolve()}: not at the cut's path\n" in log
    )

    listed = _version(root, "0004-listed", "- [ ] 1 — Listed\n")
    (listed / ".minions").mkdir()
    (listed / ".minions" / "local.db").write_text("x\n")
    run = conduct["Run"](root, "claude")
    version = conduct["Version"]("0004-listed", listed)
    found = run.remove_tree.__globals__
    real = found["_maybe"]

    def unlisted(cwd: Path, *args: str) -> str | None:
        return None if args[0] == "ls-files" else real(cwd, *args)

    monkeypatch.setitem(found, "_maybe", unlisted)
    run.remove_tree(version)
    assert (listed / ".minions" / "local.db").is_file()
    unlisted_line = (
        f" · 0004-listed · kept — {listed}: its ignored paths could not be listed\n"
    )
    assert unlisted_line in run.log.path.read_text()
    monkeypatch.setitem(found, "_maybe", real)
    run.remove_tree(version)
    assert not listed.exists()
    assert f" · 0004-listed · removed — {listed}: ignored .minions/\n" in (
        run.log.path.read_text()
    )

    # A config that changed, or that git would run a program from, keeps the tree.
    held = _version(root, "0005-config", "- [ ] 1 — Config\n")
    kept = conduct["Version"]("0005-config", held)
    _git(root, "config", "alias.planted", "!true")
    run.remove_tree(kept)
    assert held.is_dir()
    assert (
        f" · 0005-config · kept — {held}: the local git config changed during the"
        " run: .git/config differs\n"
    ) in run.log.path.read_text()
    fresh = conduct["Run"](root, "claude")
    fresh.remove_tree(kept)
    assert held.is_dir()
    assert (
        f" · 0005-config · kept — {held}: conduct: halt — the repo's git config holds a"
        " key that could name a program: alias.planted;"
    ) in fresh.log.path.read_text()
    _git(root, "config", "--unset", "alias.planted")
    clean = conduct["Run"](root, "claude")

    # A link at the cut's path keeps the tree it resolves to.
    moved = tmp_path / "moved-0006-linked"
    _git(root, "worktree", "move", str(_version(root, "0006-linked", "")), str(moved))
    (root.parent / "0006-linked").symlink_to(moved)
    clean.remove_tree(conduct["Version"]("0006-linked", moved))
    assert moved.is_dir()
    assert (
        f" · 0006-linked · kept — {moved}: a link at the cut's path\n"
    ) in clean.log.path.read_text()

    # A tree git refuses to remove stays, its untracked file with it.
    dirty = _version(root, "0007-dirty", "- [ ] 1 — Dirty\n")
    (dirty / "notes.txt").write_text("x\n")
    clean.remove_tree(conduct["Version"]("0007-dirty", dirty))
    assert (dirty / "notes.txt").is_file()
    assert f" · 0007-dirty · kept — {dirty}: fatal: " in clean.log.path.read_text()

    # A link swapped in at the cut's path while the listing runs keeps the tree.
    swap = _version(root, "0008-swapped", "- [ ] 1 — Swapped\n")
    aside = tmp_path / "aside-0008-swapped"

    def swapping(cwd: Path, *args: str) -> str | None:
        paths = real(cwd, *args)
        if args[0] == "ls-files":
            _git(root, "worktree", "move", str(swap), str(aside))
            swap.symlink_to(aside)
        return paths

    monkeypatch.setitem(found, "_maybe", swapping)
    clean.remove_tree(conduct["Version"]("0008-swapped", swap))
    monkeypatch.setitem(found, "_maybe", real)
    assert aside.is_dir()
    assert (
        f" · 0008-swapped · kept — {swap}: a link at the cut's path\n"
    ) in clean.log.path.read_text()

    # A filter planted while the listing runs keeps the tree.
    planted = _version(root, "0009-planted", "- [ ] 1 — Planted\n")

    def planting(cwd: Path, *args: str) -> str | None:
        paths = real(cwd, *args)
        if args[0] == "ls-files":
            _git(root, "config", "filter.planted.clean", "true")
        return paths

    monkeypatch.setitem(found, "_maybe", planting)
    clean.remove_tree(conduct["Version"]("0009-planted", planted))
    monkeypatch.setitem(found, "_maybe", real)
    assert planted.is_dir()
    assert (
        f" · 0009-planted · kept — {planted}: the local git config changed during the"
        " run: .git/config differs\n"
    ) in clean.log.path.read_text()


@pytest.mark.slow
def test_after_waits_for_its_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    fired = tmp_path / "fired.txt"
    hook = root / ".git" / "hooks" / "post-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text(f"#!/bin/sh\ngit log -1 --format=%s >> {shlex.quote(str(fired))}\n")
    hook.chmod(0o755)

    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
    assert "0002-marks · waiting" in capsys.readouterr().out.splitlines()

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    seen = _calls(calls)
    assert seen.index("release 0001-todo") < seen.index("build 0002-marks")
    assert "chore(integrate): merge main into 0002-marks" in _git(
        root, "log", "--format=%s", "0002-marks"
    )
    planted = fired.read_text().splitlines()
    assert "build" in planted
    assert "chore(integrate): merge main into 0002-marks" not in planted
    assert "Change: 0002-marks" in _git(root, "log", "--format=%B", "0002-marks")
    assert _git(root, "tag", "-l").split() == ["v0.1.0", "v0.2.0"]


@pytest.mark.slow
def test_a_dependents_delta_halts_as_integrating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    second = _primary(tmp_path)
    living = "openspec/specs/sdd/spec.md"
    _commit(second, {living: "### Requirement: First\n\nThe base.\n"}, "spec")
    first = _version(second, "0001-todo", "- [ ] 1 — Todo\n")
    fold = {living: "### Requirement: First\n\nThe dependency's.\n"}
    _commit(first, fold, "fold\n\nChange: 0001-todo")
    tree = _version(second, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    delta = "## MODIFIED Requirements\n\n### Requirement: First\n\nThe dependent's.\n"
    _commit(tree, {"openspec/changes/0002-marks/specs/sdd/spec.md": delta}, "delta")

    def again(code: int) -> str:
        assert (
            _main(
                conduct, second, "run", "--executor", "claude", monkeypatch=monkeypatch
            )
            == code
        )
        return conduct["last_log"](second / ".minions" / "runs").read_text()

    log = again(1)
    assert "build 0002-marks" not in _calls(calls)
    halted = (
        " · 0002-marks · halt — integrating — semantic conflict:"
        " .minions/changes/0002-marks/integrate.md\n"
    )
    assert halted in log
    assert " · run · halt — halted 0002-marks · blocked none · released v0.1.0" in log
    assert _git(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)
    note = second / ".minions" / "changes" / "0002-marks" / "integrate.md"
    held = note.read_text()
    assert held.startswith("## sdd: First\n")
    assert "`openspec/changes/0002-marks/design.md`" in held
    assert "`openspec/changes/archive/0001-todo/design.md`" in held

    _version(second, "0003-more", "- [ ] 1 — More\n")
    calls.unlink()
    assert halted in again(1)
    assert "build 0002-marks" not in _calls(calls)
    assert "release 0003-more" in _calls(calls)
    assert note.read_text() == held

    # A link at the change's folder halts the version, not the run; nothing written.
    marks, aside = note.parent, tmp_path / "aside"
    marks.rename(aside)
    (aside / "integrate.md").unlink()
    marks.symlink_to(aside)
    log = again(1)
    assert (
        " · 0002-marks · halt — conduct: halt — cannot write"
        " .minions/changes/0002-marks/integrate.md — "
    ) in log
    assert " · run · halt — halted 0002-marks · blocked none · " in log
    assert not (aside / "integrate.md").exists()
    marks.unlink()
    aside.rename(marks)
    note.write_text(held)

    _git(tree, "commit", "-q", "-m", "chore(integrate): merge main into 0002-marks")
    note.unlink()
    calls.unlink()
    again(0)
    assert "build 0002-marks" in _calls(calls)


@pytest.mark.slow
def test_a_crashed_integrate_script_halts_and_a_rerun_merges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    module = conduct["main"].__globals__
    crashed = _primary(tmp_path)
    _version(crashed, "0001-todo", "- [ ] 1 — Todo\n")
    dependent = _version(crashed, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    crash = tmp_path / "crash.py"
    crash.write_text(
        "def delta(tree):\n    raise OSError('no fork')\n\n"
        "changelog = decisions = delta\n"
    )
    script = module["INTEGRATE"]
    monkeypatch.setitem(module, "INTEGRATE", crash)
    assert _run_claude(conduct, crashed, monkeypatch) == 1
    assert "build 0002-marks" not in _calls(calls)
    assert any(
        line.endswith(
            " · 0002-marks · halt — conduct: cannot run — integrate.py delta:"
            " OSError: no fork"
        )
        for line in _log(crashed)
    )
    assert _git(dependent, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)
    monkeypatch.setitem(module, "INTEGRATE", script)
    assert _run_claude(conduct, crashed, monkeypatch) == 0
    assert "chore(integrate): merge main into 0002-marks" in _git(
        crashed, "log", "--format=%s", "0002-marks"
    )


def test_a_merge_in_refuses_a_planted_hook(
    tmp_path: Path, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    hooked = _primary(tmp_path)
    waiting = _version(hooked, "0002-marks", "- [ ] 1 — Marks\n")
    _commit(hooked, {"moved.txt": "x\n"}, "main moves")
    ran = tmp_path / "merge-hook-ran.txt"
    _git(hooked, "config", "hook.probe.event", "pre-commit")
    _git(hooked, "config", "hook.probe.command", f"touch {shlex.quote(str(ran))}")
    held_run = conduct["Run"](hooked, "claude")
    held_run.git_state = conduct["_git_state"](hooked)
    with pytest.raises(conduct["Stop"], match="hook.probe.event"):
        held_run.merge_in(waiting, "0002-marks", "main")
    assert not ran.exists()
    assert not _git(waiting, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)


@pytest.mark.slow
def test_the_integrate_script_is_loaded_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    module = conduct["main"].__globals__
    planted = _primary(tmp_path)
    _version(planted, "0001-todo", "- [ ] 1 — Todo\n")
    _version(planted, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    held = tmp_path / "held.py"
    held.write_text(module["INTEGRATE"].read_text())
    monkeypatch.setitem(module, "INTEGRATE", held)
    monkeypatch.setenv("FAKE_SCRIPT", str(held))
    assert _run_claude(conduct, planted, monkeypatch) == 0
    assert held.read_text().startswith("raise OSError")
    assert "chore(integrate): merge main into 0002-marks" in _git(
        planted, "log", "--format=%s", "0002-marks"
    )


def _behind(tmp_path: Path, moved: str, started: bool) -> tuple[Path, Path]:
    """Return a primary and `0001-todo`'s cut, `main` moved `moved` since."""
    base = _primary(tmp_path)
    cut = _version(base, "0001-todo", "- [ ] 1 — Todo\n")
    if started:
        _commit(cut, {"work.txt": "x\n"}, "build: a first part")
    _commit(base, {moved: "x\n"}, "main moves")
    return base, cut


_MERGED = "chore(integrate): merge main into 0001-todo"
_GATE_HALT = "conduct: halt — main changed Makefile"


def test_a_cut_only_version_merges_in_before_its_first_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    cut_only, _ = _behind(tmp_path, "Makefile", started=False)
    assert _run_claude(conduct, cut_only, monkeypatch) == 0
    assert _calls(calls) == [
        "probe",
        "build 0001-todo",
        "converge 0001-todo",
        "release 0001-todo",
    ]
    assert _MERGED in _git(cut_only, "log", "--format=%s", "0001-todo")


def test_a_cut_only_version_merged_in_once_merges_again(
    tmp_path: Path, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    # A `merge_in` commit does not mark a cut-only version started: a later move of
    # the default branch, outside `GATE_FILES`, is merged in too.
    # Why: 0071-ship-fixes design D4.
    once, cut = _behind(tmp_path, "Makefile", started=False)
    caught = conduct["Run"](once, "claude")
    caught.merge_in(cut, "0001-todo", "main")
    _commit(once, {"README.md": "x\n"}, "main moves outside the gate")
    caught.catch_up(conduct["find_version"](once, "0001-todo"))
    assert conduct["_ancestor"](once, "main", "0001-todo")
    assert _git(once, "rev-list", "--count", "--merges", "main..0001-todo") == "2"


def test_a_clean_merge_in_builds_on_the_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    gated, _ = _behind(tmp_path, "Makefile", started=True)
    assert _run_claude(conduct, gated, monkeypatch) == 0
    assert _calls(calls)[1] == "build 0001-todo"
    assert _MERGED in _git(gated, "log", "--format=%s", "0001-todo")


def test_a_changelog_conflict_is_settled_by_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    logged = _primary(tmp_path)
    entries = "# Changelog\n\n## [Unreleased]\n"
    _commit(logged, {"CHANGELOG.md": entries}, "changelog")
    logged_tree = _version(logged, "0001-todo", "- [ ] 1 — Todo\n")
    mine = f"{entries}\n- The branch's entry.\n"
    _commit(logged_tree, {"CHANGELOG.md": mine}, "build: a first part")
    release = f"{entries}\n## [0.1.0] - 2026-11-04\n\n- A release.\n"
    _commit(logged, {"Makefile": "x\n", "CHANGELOG.md": release}, "main releases")
    assert _run_claude(conduct, logged, monkeypatch) == 0
    assert _calls(calls)[1] == "build 0001-todo"
    assert _MERGED in _git(logged, "log", "--format=%s", "0001-todo")
    assert _git(logged, "show", "0001-todo:CHANGELOG.md") == (
        "# Changelog\n\n## [Unreleased]\n\n- The branch's entry.\n\n"
        "## [0.1.0] - 2026-11-04\n\n- A release."
    )


def test_a_merge_in_conflict_halts_naming_the_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    clashed, clashed_tree = _behind(tmp_path, "Makefile", started=False)
    _commit(clashed_tree, {"Makefile": "y\n"}, "build: a first part")
    assert _run_claude(conduct, clashed, monkeypatch) == 1
    assert _calls(calls) == ["probe"]
    assert any(
        line.endswith(
            " · 0001-todo · halt — conduct: halt — merging main into 0001-todo"
            " conflicts in Makefile: git -C"
            f" {shlex.quote(str(clashed_tree))} merge main, then re-run"
        )
        for line in _log(clashed)
    )
    assert not _git(
        clashed_tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    assert _MERGED not in _git(clashed, "log", "--format=%s", "0001-todo")
    # A worker can name the default branch: the remedy line quotes it.
    hostile = "x$(touch pwned)"
    remedy = f"merge {shlex.quote(hostile)}, then re-run"
    with pytest.raises(conduct["Stop"], match=re.escape(remedy) + "$"):
        conduct["Run"](clashed, "claude").settle(clashed_tree, "0001-todo", hostile)


def test_a_started_version_behind_an_unchanged_gate_builds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    # Twin: a started version behind a `main` that changed neither builds.
    moved, _ = _behind(tmp_path, "moved.txt", started=True)
    assert _run_claude(conduct, moved, monkeypatch) == 0
    assert "build 0001-todo" in _calls(calls)


def test_a_ticked_version_goes_to_integrate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    built, built_tree = _behind(tmp_path, "Makefile", started=True)
    ticked = {"openspec/changes/0001-todo/tasks.md": "## Progress\n\n- [x] 1 — Todo\n"}
    _commit(built_tree, ticked, "build")
    assert _run_claude(conduct, built, monkeypatch) == 0
    assert "integrate 0001-todo" in _calls(calls)
    assert not any(_GATE_HALT in line for line in _log(built))


def test_an_open_merge_with_no_note_halts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    opened, opened_tree = _behind(tmp_path, "Makefile", started=True)
    _git(opened_tree, "merge", "-q", "--no-ff", "--no-commit", "main")
    assert _run_claude(conduct, opened, monkeypatch) == 1
    assert _calls(calls) == ["probe"]
    assert any(
        line.endswith(
            " · 0001-todo · halt — conduct: halt — a merge is open in 0001-todo's"
            " worktree with no note while phase 1 is unticked: finish it with"
            f" git -C {shlex.quote(str(opened_tree))} commit, then re-run"
        )
        for line in _log(opened)
    )
    assert not any(_GATE_HALT in line for line in _log(opened))
    assert _git(opened_tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)


def test_an_open_merge_with_its_note_halts_as_integrating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    # Twin: with its note beside it, the open merge is the `integrating` halt.
    noted, noted_tree = _behind(tmp_path, "Makefile", started=True)
    _git(noted_tree, "merge", "-q", "--no-ff", "--no-commit", "main")
    marks = noted / ".minions" / "changes" / "0001-todo"
    marks.mkdir(parents=True, exist_ok=True)
    (marks / "integrate.md").write_text("## sdd: First\n")
    assert _run_claude(conduct, noted, monkeypatch) == 1
    assert _calls(calls) == []
    assert any(
        line.endswith(
            " · 0001-todo · halt — integrating — semantic conflict:"
            " .minions/changes/0001-todo/integrate.md"
        )
        for line in _log(noted)
    )
    assert not any(_GATE_HALT in line for line in _log(noted))


def test_a_started_dependents_open_merge_is_merge_ins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    # Twin: a started dependent's open merge, its dependency shipped, is merge_in's.
    shipped = _primary(tmp_path)
    waits = _version(shipped, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    _commit(waits, {"work.txt": "x\n"}, "build: a first part")
    archive = {"openspec/changes/archive/0001-todo/proposal.md": "x\n"}
    _commit(shipped, archive, "chore(release): 0001-todo")
    _git(waits, "merge", "-q", "--no-ff", "--no-commit", "main")
    assert _run_claude(conduct, shipped, monkeypatch) == 0
    assert _calls(calls)[1] == "build 0002-marks"
    assert "chore(integrate): merge main into 0002-marks" in _git(
        shipped, "log", "--format=%s", "0002-marks"
    )


@pytest.mark.slow
def test_a_halted_dependency_blocks_a_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("liar-0001-todo")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    _version(root, "0003-more", "- [ ] 1 — More\n", after="0002-marks")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    seen = _calls(calls)
    assert "build 0002-marks" not in seen
    assert "build 0003-more" not in seen
    lines = _log(root)
    assert any(
        line.endswith(" · 0002-marks · blocked — by 0001-todo") for line in lines
    )
    assert any(
        line.endswith(" · 0003-more · blocked — by 0002-marks") for line in lines
    )
    assert lines[-1].endswith(
        " · run · halt — halted 0001-todo · blocked 0002-marks 0003-more"
        " · released none"
    )
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    report = capsys.readouterr().out.splitlines()
    assert report[1].startswith("0002-marks · ")
    assert report[1].endswith(" · blocked by 0001-todo")
    assert report[2].startswith("0003-more · ")
    assert report[2].endswith(" · blocked by 0002-marks")


def test_a_lone_dependent_is_blocked_by_its_halt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    lone = _primary(tmp_path)
    _version(lone, "0001-todo", "- [ ] 1 — Ship **HUMAN**\n")
    _version(lone, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    _version(lone, "0003-more", "- [ ] 1 — More\n", after="0002-marks")
    assert _run_claude(conduct, lone, monkeypatch) == 1
    assert _calls(calls) == []
    lines = _log(lone)
    assert any(
        line.endswith(" · 0003-more · blocked — by 0002-marks") for line in lines
    )
    assert lines[-1].endswith(
        " · run · halt — halted 0001-todo · blocked 0002-marks 0003-more"
        " · released none"
    )


def test_a_free_version_ships_past_a_blocked_chain(
    tmp_path: Path, fake: Callable[..., Path]
) -> None:
    calls = fake("liar-0001-todo")
    hand = _primary(tmp_path)
    _version(hand, "0001-todo", "- [ ] 1 — Todo\n", after="0002-marks")
    _version(hand, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    _version(hand, "0003-self", "- [ ] 1 — Self\n", after="0003-self")
    _version(hand, "0004-free", "- [ ] 1 — Free\n")
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "run", "--executor", "claude"],
        cwd=hand,
        capture_output=True,
        timeout=60,
    )
    assert done.returncode == 1
    seen = _calls(calls)
    assert "release 0004-free" in seen
    assert not {"build 0001-todo", "build 0002-marks", "build 0003-self"} & set(seen)
    lines = _log(hand)
    for blocked in (
        " · 0001-todo · blocked — by 0002-marks",
        " · 0002-marks · blocked — by 0001-todo",
        " · 0003-self · blocked — by 0003-self",
    ):
        assert any(line.endswith(blocked) for line in lines)
    assert " · run · halt — halted none · blocked " in lines[-1]
    assert lines[-1].endswith(" · released v0.1.0")


@pytest.mark.slow
def test_a_dependent_waits_while_its_dependency_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake("after-self-0001-todo", "slow-0002-marks")
    late = _primary(tmp_path)
    _version(late, "0001-todo", "- [ ] 1 — Todo\n")
    _version(late, "0002-marks", "- [ ] 1 — Marks\n")
    assert _run_claude(conduct, late, monkeypatch) == 1
    assert [line.split(" · ", 1)[1] for line in _log(late) if " · halt — " in line] == [
        "0001-todo · halt — waiting — after 0001-todo",
        "run · halt — halted 0001-todo · blocked none · released v0.1.0",
    ]


@pytest.mark.slow
def test_a_rejoined_dependency_brings_its_chain_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    # A rejoin of the dependency alone brings back the chain it blocked.
    # Why: 0071-ship-fixes design D4.
    conduct["main"].__globals__["REJOIN_POLL"] = 0.1
    hold = tmp_path / "hold"
    monkeypatch.setenv("FAKE_HOLD", str(hold))
    calls = fake("liar-0001-todo", "hold-0004-free")
    linked = _primary(tmp_path)
    first = _version(linked, "0001-todo", "- [ ] 1 — Todo\n")
    _version(linked, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    _version(linked, "0003-more", "- [ ] 1 — More\n", after="0002-marks")
    _version(linked, "0004-free", "- [ ] 1 — Free\n")

    def fix() -> None:
        tasks = first / "openspec/changes/0001-todo/tasks.md"
        _commit(first, {str(tasks): "## Progress\n\n- [x] 1 — Todo\n"}, "a fix")
        _done(linked, "0001-todo", _git(first, "rev-parse", "HEAD"))
        fake()
        assert conduct["rejoin"](linked, "0001-todo") == "rejoin: requested 0001-todo"

    said = (" · 0001-todo · halt — ", " · 0003-more · blocked — by 0002-marks")
    join = _when_logged(linked, said, fix, hold)
    assert _run_claude(conduct, linked, monkeypatch) == 0
    join()
    lines = _log(linked)
    for change in ("0002-marks", "0003-more"):
        assert any(
            line.endswith(f" · run · rejoin — {change}: waiting") for line in lines
        )
        assert f"release {change}" in _calls(calls)
    assert lines[-1].endswith(" · run · done — released v0.1.0 v0.2.0 v0.3.0 v0.4.0")


def test_run_halts_on_a_human_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [x] 1 — Todo\n- [ ] 2 — Ship **HUMAN**\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "release 0002-marks" in _calls(calls)
    lines = _log(root)
    assert any(
        line.endswith(" · 0001-todo · halt — human — phase 2 — Ship **HUMAN**")
        for line in lines
    )
    assert lines[-1].endswith(
        " · run · halt — halted 0001-todo · blocked none · released v0.1.0"
    )
    assert _git(root, "tag", "-l") == "v0.1.0"

    only = tmp_path / "only"
    only.mkdir()
    lone = _primary(only)
    _version(lone, "0001-todo", "- [ ] 1 — Ship **HUMAN**\n")
    calls.unlink()
    assert (
        _main(conduct, lone, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == []

    # A build that stops at a HUMAN phase gets no rescue: the phase needs the person.
    stops = tmp_path / "stops"
    stops.mkdir()
    built = _primary(stops)
    _version(built, "0001-todo", "- [ ] 1 — Todo\n- [ ] 2 — Ship **HUMAN**\n")
    fake("rescue-fix")
    assert (
        _main(conduct, built, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == ["probe", "build 0001-todo"]
    assert _log(built)[-2].endswith(
        " · 0001-todo · halt — build check fail — phase 2 unticked"
    )

    # A HUMAN phase whose title names a cap, over small open blockers, gets no grant.
    named = tmp_path / "named"
    named.mkdir()
    capped = _primary(named)
    phase = 'phase 1 — Check the "cap reached" banner **HUMAN**'
    tree = _version(capped, "0001-todo", f"- [ ] {phase.removeprefix('phase ')}\n")
    _cards(capped, "0001-todo", _git(tree, "rev-parse", "HEAD"), "a test")
    calls.unlink()
    fake()
    assert (
        _main(conduct, capped, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == []
    assert not any(" · grant — " in line or "re-plan" in line for line in _log(capped))
    # Nor in the version's own pass, as beside a version that builds.
    conductor = conduct["Run"](capped, "claude")
    version = conduct["find_version"](capped, "0001-todo")
    conductor.read_plan([version])
    conductor.advance(version, ())
    assert _calls(calls) == []
    assert conductor.halts == [("0001-todo", f"human — {phase}")]
    conductor.log.path.unlink()


@pytest.mark.slow
def test_run_halts_when_a_worker_claims_what_disk_does_not_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("deny", "liar")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    # A halt file naming another head is stale, and an unreadable one is none: the
    # halt line leaves them out.
    stale = root / ".minions" / "changes" / "0001-todo" / "build.halt"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"\xff")
    halt = conduct["_build_halt"]
    assert halt(root / ".minions", tree, "0001-todo") is None
    base = _git(root, "rev-parse", "HEAD")
    stale.write_text(f"sub-task: 9.9\nstop: 1\nevidence: old\nhead: {base}\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo", "rescue 0001-todo"]
    lines = _log(root)
    assert any(re.search(r" · finish — build · exit 0 · \d+s$", line) for line in lines)
    assert any(
        line.endswith(
            " · 0001-todo · halt — build check fail — phase 1 unticked"
            " · denied: Bash(rm -rf build)"
        )
        for line in lines
    )

    fake("halt-0001-todo")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    logs = (root / ".minions" / "runs").glob("*.md")
    assert any(
        line.endswith(
            " · 0001-todo · halt — build check fail — phase 1 unticked · 1.1: 3"
        )
        for log in logs
        for line in log.read_text().splitlines()
    )

    _commit(
        tree,
        {"openspec/changes/0001-todo/tasks.md": "## Progress\n\n- [x] 1 — Todo\n"},
        "build",
    )
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    calls.unlink()
    fake()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )
    assert _calls(calls) == ["probe", "converge 0001-todo", "release 0001-todo"]
    assert _git(root, "tag", "-l") == "v0.1.0"

    other = tmp_path / "other"
    other.mkdir()
    second = _primary(other)
    _version(second, "0001-todo", "- [ ] 1 — Todo\n")
    calls.unlink()
    fake("liar-probe")
    assert (
        _main(conduct, second, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == ["probe"]
    assert _log(second)[-1].endswith(
        " · run · halt — halted run · blocked none · released none"
    )

    third = tmp_path / "third"
    third.mkdir()
    crashed = _primary(third)
    _version(crashed, "0001-todo", "- [ ] 1 — Todo\n")
    _version(crashed, "0002-marks", "- [ ] 1 — Marks\n")
    models = crashed / ".minions" / "changes" / "0001-todo"
    models.mkdir(parents=True)
    (models / "models.toml").write_bytes(b"\xff")
    calls.unlink()
    fake()
    assert (
        _main(conduct, crashed, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert "converge 0002-marks" not in _calls(calls)
    lines = _log(crashed)
    assert any(" · run · halt — conduct.py failed: " in line for line in lines)
    assert lines[-1].endswith(
        " · run · halt — halted run · blocked none · released none"
    )


def test_a_rescue_fixes_a_plan_halt_in_its_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("halt-0001-todo", "rescue-fix")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    assert _calls(calls) == [
        "probe",
        "build 0001-todo",
        "rescue 0001-todo",
        "build 0001-todo",
        "converge 0001-todo",
        "release 0001-todo",
    ]
    grep = ("--grep=amend the change", "0001-todo")
    amend = _git(root, "log", "-1", "--format=%H", *grep)[:7]
    lines = _log(root)
    assert any(
        line.endswith(
            " · 0001-todo · halt — build check fail — phase 1 unticked · 1.1: 3"
        )
        for line in lines
    )
    assert any(
        line.endswith(f" · run · rescue — 0001-todo: fixed · 1.1 · {amend}")
        for line in lines
    )
    assert lines[-1].endswith(" · run · done — released v0.1.0")
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    said = capsys.readouterr().out.splitlines()
    halt = next(i for i, line in enumerate(said) if " · 0001-todo · halt — " in line)
    assert said.index(f"0001-todo · rescued 1.1 · {amend}") > halt


@pytest.mark.slow
def test_a_rescue_diagnoses_a_decision_halt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("halt-0001-todo", "rescue-diagnose")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo", "rescue 0001-todo"]
    lines = _log(root)
    diagnosis = ".minions/changes/0001-todo/rescue.md"
    assert any(
        line.endswith(f" · run · rescue — 0001-todo: diagnosed · {diagnosis}")
        for line in lines
    )
    assert any(
        line.endswith(f" · 0001-todo · halt — rescue diagnosed — {diagnosis}")
        for line in lines
    )
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    said = capsys.readouterr().out.splitlines()
    first, second = (line for line in lines if " · 0001-todo · halt — " in line)
    assert said[-4:] == [first, f"0001-todo · diagnosed {diagnosis}", second, lines[-1]]

    # The diagnosis an earlier rescue left is not this one's.
    calls.unlink()
    fake("halt-0001-todo")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == ["probe", "build 0001-todo", "rescue 0001-todo"]
    assert _log(root)[-2].endswith(
        " · 0001-todo · halt — rescue wrote no amend and no diagnosis"
    )

    # A rescue worker that fails halts as any worker does.
    fake("halt-0001-todo", "dies-rescue")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _log(root)[-2].endswith(" · 0001-todo · halt — rescue worker exit 1")


def test_a_rescue_outside_the_plan_halts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("halt-0001-todo", "rescue-wild")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo", "rescue 0001-todo"]
    assert _log(root)[-2].endswith(" · 0001-todo · halt — rescue touched src.py")
    assert not any(" · run · rescue — " in line for line in _log(root))

    # A rescue that rewrites the history its amend is judged against halts too.
    before = _git(tree, "rev-parse", "HEAD")[:7]
    fake("halt-0001-todo", "rescue-rewrite")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _log(root)[-2].endswith(
        f" · 0001-todo · halt — rescue moved HEAD off {before}"
    )

    # An amend is one commit with the amend's subject and trailer, and none at a
    # converge or integrate halt.
    amend, tasks = conduct["_amend"], "openspec/changes/0001-todo/tasks.md"
    start = _git(tree, "rev-parse", "HEAD")
    named = "docs(0001-todo): amend the change directory\n\nRescue: 1.1"
    _commit(tree, {tasks: "## Progress\n\n- [ ] 1 — Todo\n"}, named)
    assert amend(tree, "0001-todo", start, ("tasks.md",))[0]
    assert amend(tree, "0001-todo", start, ())[1] == f"rescue touched {tasks}"
    _git(tree, "commit", "-q", "--allow-empty", "-m", "an amend")
    head = _git(tree, "rev-parse", "HEAD")[:7]
    for since in (start, _git(tree, "rev-parse", "HEAD~1")):
        assert amend(tree, "0001-todo", since, ("tasks.md",)) == (
            None,
            f"rescue commit {head} is not one amend with a Rescue: trailer",
        )


def test_a_sub_task_is_rescued_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("halt-0001-todo", "rescue-hollow")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == [
        "probe",
        "build 0001-todo",
        "rescue 0001-todo",
        "build 0001-todo",
    ]
    assert _log(root)[-2].endswith(
        " · 0001-todo · halt — build check fail — phase 1 unticked · 1.1: 3"
        " · rescued 1.1"
    )

    # The fourth halt gets none, whatever its sub-task.
    conductor = conduct["Run"](root, "claude")
    conductor.rescues["0001-todo"] = ["1.1", "1.2", "1.3"]
    assert conductor.rescued("0001-todo", "2.1") == " · rescued 1.1 1.2 1.3"
    assert conductor.rescued("0001-todo", "1.2") == " · rescued 1.1 1.2 1.3"
    assert conductor.rescued("0002-marks", "1.1") == ""


def test_rescue_skip_runs_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("halt-0001-todo", "rescue-fix")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    minions = root / ".minions"
    table = minions / "changes" / "0001-todo" / "models.toml"
    table.parent.mkdir(parents=True)
    table.write_text("[rescue]\nskip = true\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo"]
    # The rescue runs on its own table, else the build's: an empty one is not absent.
    models = conduct["_models"]
    table.write_text('[build]\nmodel = "m"\n')
    assert models(minions, "0001-todo", "rescue", "claude") == ("claude", "m", None)
    table.write_text('[build]\nmodel = "m"\n[rescue]\n')
    assert models(minions, "0001-todo", "rescue", "claude") == ("claude", None, None)
    # A table TOML cannot read halts, naming the file in the change's folder.
    table.write_text("[build\n")
    with pytest.raises(
        conduct["Stop"], match=r"halt — changes/0001-todo/models\.toml: "
    ):
        models(minions, "0001-todo", "rescue", "claude")


def test_a_linked_rejoin_folder_deletes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    runs = tmp_path / "runs"
    folder = runs / "rejoin"
    folder.mkdir(parents=True)
    (folder / "all").touch()
    elsewhere = tmp_path / "operator-files"
    elsewhere.mkdir()
    (elsewhere / "all").touch()
    unlink = os.unlink

    # A worker swaps the folder for a link once the run has listed it.
    def swap(path: str | Path, *, dir_fd: int | None = None) -> None:
        if not folder.is_symlink():
            folder.rename(runs / "listed")
            folder.symlink_to(elsewhere)
        unlink(path, dir_fd=dir_fd)

    monkeypatch.setattr(os, "unlink", swap)
    assert conduct["_requests"](runs) == {"all"}
    assert (elsewhere / "all").is_file()
    assert not (runs / "listed" / "all").exists()

    # A folder that cannot be listed holds no request.
    def refuse(fd: int) -> list[str]:
        raise PermissionError(fd)

    (runs / "listed" / "all").touch()
    monkeypatch.setattr(os, "listdir", refuse)
    assert conduct["_entries"](runs / "listed", empty=True) == []
    assert (runs / "listed" / "all").is_file()


def test_a_later_version_halts_and_the_earlier_ships(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("liar-0002-marks", "slow-0001-todo")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "release 0001-todo" in _calls(calls)
    assert "release 0002-marks" not in _calls(calls)
    assert _git(root, "tag", "-l") == "v0.1.0"
    lines = _log(root)
    # The build check's halt, then its rescue's.
    halts = [line for line in lines if " · 0002-marks · halt — " in line]
    halted = halts[0]
    assert halts[1].endswith(" · halt — rescue wrote no amend and no diagnosis")
    spawned = next(line for line in lines if " · 0001-todo · spawn — release" in line)
    assert lines.index(halted) < lines.index(spawned)
    assert lines[-1].endswith(
        " · run · halt — halted 0002-marks · blocked none · released v0.1.0"
    )
    log = conduct["last_log"](root / ".minions" / "runs")
    assert (
        _main(conduct, root, "log", "--verify", str(log), monkeypatch=monkeypatch) == 0
    )
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    report = capsys.readouterr().out.splitlines()
    assert report[-3:] == [*halts, lines[-1]]


def test_a_later_version_ships_past_a_halted_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("liar-0001-todo")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "release 0002-marks" in _calls(calls)
    assert _log(root)[-1].endswith(
        " · run · halt — halted 0001-todo · blocked none · released v0.1.0"
    )


@pytest.mark.slow
def test_a_fixed_version_rejoins_a_live_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    conduct["main"].__globals__["REJOIN_POLL"] = 0.1
    hold = tmp_path / "hold"
    monkeypatch.setenv("FAKE_HOLD", str(hold))
    calls = fake("liar-0001-todo", "hold-0002-marks")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    _version(root, "0003-hand", "- [ ] 1 — Hand **HUMAN**\n")
    rejoin, stop = conduct["rejoin"], conduct["Stop"]
    with pytest.raises(stop, match="^rejoin: no run is live — run /mf-ship$"):
        rejoin(root, None)

    def fix() -> None:
        tasks = tree / "openspec/changes/0001-todo/tasks.md"
        _commit(tree, {str(tasks): "## Progress\n\n- [x] 1 — Todo\n"}, "a fix")
        _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
        fake("hold-0002-marks")
        with pytest.raises(stop, match="no open version holds 0009-none"):
            rejoin(root, "0009-none")
        assert rejoin(root, None) == "rejoin: requested every halted version"

    halted = (" · 0001-todo · halt — ", " · 0003-hand · halt — ")
    join = _when_logged(root, halted, fix, hold)
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    join()

    lines = _log(root)
    assert any(line.endswith(" · run · rejoin — 0001-todo: converge") for line in lines)
    assert any(
        line.endswith(
            " · run · rejoin — 0003-hand: still human — phase 1 — Hand **HUMAN**"
        )
        for line in lines
    )
    made = _calls(calls)
    assert made.count("build 0001-todo") == made.count("build 0002-marks") == 1
    assert {"release 0001-todo", "release 0002-marks"} <= set(made)
    assert lines[-1].endswith(
        " · run · halt — halted 0003-hand · blocked none · released v0.1.0 v0.2.0"
    )
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    said = capsys.readouterr().out.splitlines()
    halt = next(i for i, line in enumerate(said) if " · 0001-todo · halt — " in line)
    assert said.index("0001-todo · rejoined converge") > halt
    assert not any("0003-hand · rejoined" in line for line in said)

    # A skipped request names no version: report keeps its line as it stands.
    log = conduct["last_log"](root / ".minions" / "runs")
    skipped = "10:00:00 · run · rejoin — skipped — conduct: cannot run — git failed"
    *body, closing = log.read_text().splitlines()
    log.write_text("\n".join([*body, skipped, closing]) + "\n")
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    said = capsys.readouterr().out.splitlines()
    assert "skipped — conduct · rejoined cannot run — git failed" not in said
    assert skipped in said


@pytest.mark.slow
def test_a_new_executor_is_probed_mid_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    conduct["main"].__globals__["REJOIN_POLL"] = 0.1
    probe = " · 0002-marks · spawn — probe-codex · model default · executor codex"
    for missing, code in ((False, 0), (True, 1)):
        scratch = tmp_path / f"missing-{missing}"
        scratch.mkdir()
        hold = scratch / "hold"
        monkeypatch.setenv("FAKE_HOLD", str(hold))
        calls = fake("hold-0001-todo")
        calls.unlink(missing_ok=True)
        asked: list[str] = []
        conduct["main"].__globals__["_executor_missing"] = (
            lambda name, missing=missing, asked=asked: (
                asked.append(name) or (missing and name == "codex")
            )
        )
        root = _primary(scratch)
        _version(root, "0001-todo", "- [ ] 1 — Todo\n")
        # A failed probe is kept: a second version on codex halts on it, unprobed.
        joining = ("0002-marks", "0003-hand") if missing else ("0002-marks",)

        def cut(
            root: Path = root,
            joining: tuple[str, ...] = joining,
            missing: bool = missing,
        ) -> None:
            # A folder no unlink removes: the poll skips it, and the run goes on.
            # Why: 0063-rejoin design D2.
            (root / ".minions" / "runs" / "rejoin" / "planted").mkdir(parents=True)
            for change in joining:
                table = root / ".minions" / "changes" / change / "models.toml"
                table.parent.mkdir(parents=True, exist_ok=True)
                table.write_text('[converge]\nexecutor = "codex"\n')
                _version(root, change, "- [ ] 1 — Marks\n")
            requested = conduct["rejoin"](root, None if missing else "0002-marks")
            if not missing:
                assert requested == "rejoin: requested 0002-marks"

        join = _when_logged(root, (" · 0001-todo · spawn — build",), cut, hold)
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == code
        )
        join()

        lines = _log(root)
        made = _calls(calls)
        assert "release 0001-todo" in made
        if missing:
            assert "build 0002-marks" not in made
            assert made.count("probe") == 1
            assert asked.count("codex") == 1
            for change in joining:
                assert not any(f" · rejoin — {change}" in line for line in lines)
                assert any(
                    line.endswith(
                        f" · {change} · halt — probe-codex — codex is not on PATH"
                    )
                    for line in lines
                )
            assert lines[-1].endswith(
                " · run · halt — halted 0002-marks 0003-hand · blocked none"
                " · released v0.1.0"
            )
        else:
            assert made.count("probe") == 2
            assert "release 0002-marks" in made
            assert any(
                line.endswith(" · run · rejoin — 0002-marks: build") for line in lines
            )
            taken = next(i for i, line in enumerate(lines) if "rejoin — 0002" in line)
            assert any(line.endswith(probe) for line in lines[:taken])
            assert any(
                line.endswith(" · 0002-marks · check — probe-codex · pass")
                for line in lines[:taken]
            )
            assert any(
                line.endswith(
                    " · 0002-marks · spawn — converge · model default · executor codex"
                )
                for line in lines
            )
            assert lines[-1].endswith(" · run · done — released v0.1.0 v0.2.0")

            stale = root / ".minions" / "runs" / "rejoin" / "all"
            stale.touch()
            assert (
                _main(
                    conduct,
                    root,
                    "run",
                    "--executor",
                    "claude",
                    monkeypatch=monkeypatch,
                )
                == 0
            )
            assert not stale.exists()

            # A worker may link the folder elsewhere: the poll reads no link, deletes
            # nothing. Why: 0063-rejoin design D2.
            elsewhere = scratch / "operator-files"
            elsewhere.mkdir()
            (elsewhere / "kept-urls").touch()
            (elsewhere / "kept.gate").mkdir()
            shutil.rmtree(stale.parent)
            stale.parent.symlink_to(elsewhere)
            assert conduct["_requests"](root / ".minions" / "runs") == set()
            assert (elsewhere / "kept-urls").is_file()


def test_a_station_runs_on_its_executor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    minions = root / ".minions"
    (minions / "changes" / "0001-todo").mkdir(parents=True)
    table = (
        '[converge]\nexecutor = "codex"\n[release]\nmodel = "opus"\neffort = "high"\n'
    )
    (minions / "changes" / "0001-todo" / "models.toml").write_text(table)
    started: list[tuple[str, str]] = []
    argv = conduct["argv"]

    def spy(executor: str, prompt: str, *rest: object) -> list[str]:
        found = re.search(r"Run the mf-(\w+) skill", prompt)
        started.append((found[1] if found else "probe", executor))
        return argv(executor, prompt, *rest)

    conduct["main"].__globals__["argv"] = spy
    models = conduct["_models"]
    assert models(minions, "0001-todo", "converge", "claude") == ("codex", None, None)
    assert models(minions, "0001-todo", "build", "claude") == ("claude", None, None)
    assert models(minions, "0001-todo", "integrate", "claude") == (
        "claude",
        "opus",
        "high",
    )

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    assert _calls(calls)[:2] == ["probe", "probe"]
    spawned = [
        line.split(" · spawn — ")[1] for line in _log(root) if " · spawn — " in line
    ]
    assert spawned[:2] == [
        "probe · model default",
        "probe-codex · model default · executor codex",
    ]
    assert "build · model default" in spawned
    assert "converge · model default · executor codex" in spawned
    # A models file's effort is in the spawn line; none, and the line reads as before.
    assert "release · model opus · effort high" in spawned
    assert started == [
        ("probe", "claude"),
        ("probe", "codex"),
        ("build", "claude"),
        ("converge", "codex"),
        ("release", "claude"),
    ]

    other = tmp_path / "other"
    other.mkdir()
    second = _primary(other)
    _version(second, "0001-todo", "- [ ] 1 — Todo\n")
    (second / ".minions" / "changes" / "0001-todo").mkdir(parents=True)
    (second / ".minions" / "changes" / "0001-todo" / "models.toml").write_text(table)
    conduct["main"].__globals__["_executor_missing"] = lambda name: name == "codex"
    calls.unlink()
    assert (
        _main(conduct, second, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == ["probe"]
    assert any(
        line.endswith(" · run · halt — probe-codex — codex is not on PATH")
        for line in _log(second)
    )


def test_a_models_mismatch_halts_its_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    table = root / ".minions" / "changes" / "0001-todo" / "models.toml"
    table.parent.mkdir(parents=True)
    table.write_text('[converge]\nexecutor = "gemini"\n')

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "release 0002-marks" in _calls(calls)
    assert "build 0001-todo" not in _calls(calls)
    assert _calls(calls).count("probe") == 1
    assert any(
        line.endswith(
            " · 0001-todo · halt — conduct: halt — changes/0001-todo/models.toml:"
            " executor 'gemini' unknown"
        )
        for line in _log(root)
    )

    table.write_text('[converge]\nexecutor = "codex"\nmodel = "claude-opus-5-5"\n')
    _version(root, "0003-more", "- [ ] 1 — More\n")
    calls.unlink()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert "release 0003-more" in _calls(calls)
    assert "build 0001-todo" not in _calls(calls)
    assert _calls(calls).count("probe") == 1
    assert any(
        line.endswith(
            " · 0001-todo · halt — conduct: halt — changes/0001-todo/models.toml:"
            " converge on codex, model claude-opus-5-5"
        )
        for line in _log(root)
    )


@pytest.mark.slow
def test_a_changed_git_config_halts_a_merge_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    changed = " · 0002-marks · halt — the local git config changed during the run:"
    held = (
        " · run · halt — conduct: halt — the repo's git config holds a key that could"
        " name a program: mf.planted; move it to the global config or remove it"
    )
    for mode, said, remote in (
        ("plant-config", f"{changed} .git/config differs", False),
        ("plant-attributes", f"{changed} .git/info/attributes differs", False),
        ("plant-held", held, False),
        ("plant-held", held, True),
    ):
        scratch = tmp_path / f"{mode}-{remote}"
        scratch.mkdir()
        root = _primary(scratch)
        if remote:
            origin = scratch / "origin.git"
            _git(scratch, "init", "-q", "--bare", "-b", "main", str(origin))
            _git(root, "remote", "add", "origin", str(origin))
            _git(root, "push", "-q", "origin", "main")
        _version(root, "0001-todo", "- [ ] 1 — Todo\n")
        tree = _version(root, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
        calls = fake(mode)

        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == 1
        )

        assert "release 0001-todo" in _calls(calls)
        assert "build 0002-marks" not in _calls(calls)
        assert any(line.endswith(said) for line in _log(root))
        assert not _git(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)
        assert "chore(integrate)" not in _git(root, "log", "--format=%s", "0002-marks")


def test_run_halts_on_a_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    conduct["main"].__globals__["TIMEOUT"] = 2
    fake("sleep")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    started = time.monotonic()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert time.monotonic() - started < 20
    lines = _log(root)
    assert any(" · 0001-todo · finish — build · exit -9 · " in line for line in lines)
    assert any(
        line.endswith(
            " · 0001-todo · halt — build timed out after 2s; its group was killed"
        )
        for line in lines
    )
    assert lines[-1].endswith(
        " · run · halt — halted 0001-todo · blocked none · released none"
    )


def test_a_dead_converge_halts_and_a_rerun_finishes_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("dies-converge")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "release 0001-todo" not in _calls(calls)
    assert _git(root, "tag", "-l") == ""
    assert any(
        line.endswith(" · 0001-todo · halt — converge worker exit 1")
        for line in _log(root)
    )
    head = _git(tree, "rev-parse", "HEAD")
    findings = root / ".minions" / "changes" / "0001-todo"
    assert f"head: {head}\n" in (findings / "review.md").read_text()
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
    assert capsys.readouterr().out.strip() == "0001-todo · converge"
    stage_of, find = conduct["stage_of"], conduct["find_version"]
    assert stage_of(root, find(root, "0001-todo"))[1] == (
        "unfinished run: 10:00:00 · round 1 · pickup — R1"
    )

    calls.unlink()
    fake()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    assert _calls(calls) == ["probe", "converge 0001-todo", "release 0001-todo"]
    assert _git(root, "tag", "-l") == "v0.1.0"


def test_a_build_dead_in_simplify_resumes_at_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("dies-simplify")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    stage_of, find = conduct["stage_of"], conduct["find_version"]
    marker = root / ".minions" / "changes" / "0001-todo" / "build.done"

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo"]
    assert not marker.exists()
    tasks = tree / "openspec/changes/0001-todo/tasks.md"
    assert tasks.read_text() == "## Progress\n\n- [x] 1 — Todo\n"
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
    assert capsys.readouterr().out.strip() == "0001-todo · build"
    closing = ("build", "closing steps left")
    assert stage_of(root, find(root, "0001-todo")) == closing

    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD~1"))
    assert stage_of(root, find(root, "0001-todo")) == closing
    marker.write_text("simplify: lean already\n")
    assert stage_of(root, find(root, "0001-todo")) == closing
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    assert stage_of(root, find(root, "0001-todo"))[0] == "converge"
    marker.write_bytes(b"\xff")
    assert stage_of(root, find(root, "0001-todo")) == closing
    marker.unlink()
    # A read of a FIFO waits for a writer.
    os.mkfifo(marker)
    assert stage_of(root, find(root, "0001-todo")) == closing
    marker.unlink()
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · pickup — R1\n")
    assert stage_of(root, find(root, "0001-todo")) == (
        "converge",
        "unfinished run: 10:00:00 · round 1 · pickup — R1",
    )
    log.unlink()

    calls.unlink()
    fake()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    assert _calls(calls) == [
        "probe",
        "build 0001-todo",
        "converge 0001-todo",
        "release 0001-todo",
    ]
    assert _git(root, "tag", "-l") == "v0.1.0"


def test_a_stale_lock_is_cleared_and_converge_resumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _findings(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    stage_of, find = conduct["stage_of"], conduct["find_version"]

    def halted(why: str) -> tuple[str, str]:
        log.write_text(f"# t\n\n## Run 1 — d\n10:00:00 · round 1 · halt — {why}\n")
        return stage_of(root, find(root, "0001-todo"))

    def run() -> int:
        return _main(
            conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch
        )

    # Twin: a halt on anything else is the person's.
    assert halted("cap reached")[0] == "converge-halted"
    for name in ("debt", "backlog"):
        assert halted(f"waited 2 minutes for .minions/{name}.lock") == (
            "converge",
            "halted on the debt lock: resumes at Step 9",
        )
    lock = root / ".minions" / "debt.lock"
    lock.mkdir()
    stale = time.time() - 601
    os.utime(lock, (stale, stale))

    assert run() == 0
    assert _calls(calls) == ["probe", "converge 0001-todo", "release 0001-todo"]
    assert not lock.exists()
    assert any(
        re.search(r" · run · unlock — \.minions/debt\.lock, 6\d\ds old$", line)
        for line in _log(root)
    )

    lock.mkdir()
    young = time.time() - 599
    os.utime(lock, (young, young))
    assert run() == 0
    assert lock.is_dir()
    assert not any(" · unlock — " in line for line in _log(root))


def test_a_run_moves_an_old_backlog_to_the_debt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root = _primary(tmp_path)
    minions = root / ".minions"
    minions.mkdir(exist_ok=True)
    old, new = minions / "backlog.md", minions / "debt.md"
    lock, held = minions / "backlog.lock", minions / "debt.lock"
    moved = " · run · move — .minions/backlog.md → .minions/debt.md"
    both = "run · halt — .minions/backlog.md and .minions/debt.md both stand"

    def start() -> tuple[int, str]:
        conductor = conduct["Run"](root, "claude")
        code = conductor.ship()
        logs = (minions / "runs").glob("*.md")
        return code, "".join(log.read_text() for log in sorted(logs))

    def stale_lock(path: Path = lock) -> None:
        path.mkdir()
        past = time.time() - 601
        os.utime(path, (past, past))

    old.write_text("# Backlog\n\n## 0001-a\n\n- **0001·R1 — a**\n")
    code, text = start()
    assert code == 0
    assert not old.exists() and "0001·R1" in new.read_text()
    assert text.count(moved) == 1

    # Twin: a second start has nothing to move.
    code, text = start()
    assert code == 0 and text.count(moved) == 1

    # A stale old lock with no old file is removed.
    stale_lock()
    code, text = start()
    unlocked = r" · run · unlock — \.minions/backlog\.lock, 6\d\ds old"
    assert code == 0 and not lock.exists()
    assert len(re.findall(unlocked, text)) == 1 and text.count(moved) == 1

    # A linked old file halts: the debt never becomes a second name of its target.
    new.unlink()
    key = tmp_path / "id_ed25519"
    key.write_text("key\n")
    old.symlink_to(key)
    code, text = start()
    assert key.stat().st_nlink == 1 and not new.exists()
    assert code == 1 and old.is_symlink()
    assert "run · halt — .minions/backlog.md is a link" in text

    # Beside an old file, the move follows it.
    old.unlink()
    old.write_text("# Backlog\n")
    stale_lock()
    code, text = start()
    assert code == 0 and not lock.exists() and new.is_file()
    assert len(re.findall(unlocked, text)) == 2 and text.count(moved) == 2

    # Both files, or a young old lock, halt before any move.
    old.write_text("# Backlog\n")
    code, text = start()
    assert code == 1 and old.is_file() and new.is_file()
    assert both in text
    new.unlink()
    lock.mkdir()
    code, text = start()
    assert code == 1 and old.is_file() and not new.exists() and lock.is_dir()
    assert "run · halt — .minions/backlog.lock is held" in text
    assert text.count(moved) == 2

    # With no old file, neither a young old lock nor a plain file there halts.
    old.unlink()
    code, text = start()
    assert code == 0 and lock.is_dir() and not new.exists()
    lock.rmdir()
    lock.write_text("")
    code, text = start()
    assert code == 0 and lock.is_file() and not new.exists()

    # Beside an old file, a plain file at the old lock halts, naming its kind.
    old.write_text("# Backlog\n")
    code, text = start()
    assert code == 1 and old.is_file() and not new.exists() and lock.is_file()
    assert "run · halt — .minions/backlog.lock is a file" in text
    assert text.count(moved) == 2

    # A young debt lock halts the move: a hand-run converge writes the debt.
    lock.unlink()
    held.mkdir()
    code, text = start()
    assert code == 1 and old.is_file() and not new.exists() and held.is_dir()
    assert "run · halt — .minions/debt.lock is held" in text
    assert text.count(moved) == 2

    # Twin: a stale debt lock is removed, and the move releases its own.
    held.rmdir()
    stale_lock(held)
    code, text = start()
    assert code == 0 and not old.exists() and new.is_file() and not held.exists()
    assert (
        len(re.findall(r" · run · unlock — \.minions/debt\.lock, 6\d\ds old", text))
        == 1
    )
    assert text.count(moved) == 3

    # A debt file its lock's holder writes after the check stands, not replaced.
    new.unlink()
    old.write_text("# Backlog\n")
    module = conduct["Run"].migrate_debt.__globals__
    clear = module["_clear_stale_lock"]

    def write_debt(primary: Path, name: str = ".minions/debt.lock") -> int | None:
        if name.endswith("backlog.lock"):
            new.write_text("# Debt\n\n## 0002-b\n\n- **0002·R1 — b**\n")
        return clear(primary, name)

    monkeypatch.setitem(module, "_clear_stale_lock", write_debt)
    code, text = start()
    assert code == 1 and old.is_file() and "0002·R1" in new.read_text()
    assert text.count(both) == 2 and text.count(moved) == 3


def _old_layout(root: Path) -> tuple[Path, Path]:
    """Return a built version and one halted in its build, their files at old paths.

    The first is clean at its head; the second holds a build halt, a models file
    and a gate-check export. Strays the move leaves stand beside them.
    """
    built = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    halted = _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    head = _git(built, "rev-parse", "HEAD")
    _done(root, "0001-todo", head)
    _findings(root, "0001-todo", head)
    minions = root / ".minions"
    marks = minions / "changes" / "0002-marks"
    (marks / "gate-check" / "base").mkdir(parents=True)
    halt = f"sub-task: 1.1\nstop: 3\nhead: {_git(halted, 'rev-parse', 'HEAD')}\n"
    (marks / "build.halt").write_text(halt)
    (marks / "models.toml").write_text('[build]\nmodel = "m"\n')
    return built, halted


_OLD = {
    "0001-todo": {
        "review.md": "findings/0001-todo_review.md",
        "security.md": "findings/0001-todo_security.md",
        "status_log.md": "findings/0001-todo_status_log.md",
        "build.done": "build/0001-todo.done",
    },
    "0002-marks": {
        "build.halt": "build/0002-marks.halt",
        "models.toml": "models/0002-marks.toml",
        "gate-check": "gate-check/0002-marks",
    },
}
_STRAYS = (
    "findings/0034-fix-red.txt",
    "findings/0030_review.md",
    "findings/0001-todo_review.run1.md",
    "release/fold.py",
    "runs/20261101-230000/run_probe.log",
    "runs/20261101-230000/0001-todo_Notes.log",
)


def _to_old(root: Path) -> None:
    """Move each `_OLD` file to its old path, add a worker log, and write `_STRAYS`."""
    minions = root / ".minions"
    for change, names in _OLD.items():
        for new, old in names.items():
            (minions / old).parent.mkdir(parents=True, exist_ok=True)
            (minions / "changes" / change / new).rename(minions / old)
    log = minions / "runs" / "20261101-230000" / "0001-todo_converge-2.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("converge\n")
    for stray in _STRAYS:
        (minions / stray).parent.mkdir(parents=True, exist_ok=True)
        (minions / stray).write_text("x\n")


def test_a_run_moves_an_old_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    built, halted = _old_layout(root)
    minions = root / ".minions"
    find, stage_of = conduct["find_version"], conduct["stage_of"]

    def stages() -> list[Any]:
        read = [stage_of(root, find(root, c)) for c in ("0001-todo", "0002-marks")]
        return [*read, conduct["_build_halt"](minions, halted, "0002-marks")]

    expected = stages()
    assert expected[0][0] == "release" and expected[2] == ("1.1", "3")
    _to_old(root)
    assert stages() != expected

    conductor = conduct["Run"](root, "claude")
    assert conductor.migrate_layout() is None
    text = conductor.log.path.read_text()
    assert " · run · move — 0001-todo: 5 files\n" in text
    assert " · run · move — 0002-marks: 3 files\n" in text
    assert stages() == expected
    logs = minions / "changes" / "0001-todo" / "logs"
    assert (logs / "20261101-230000-converge-2.log").read_text() == "converge\n"
    assert (minions / "changes" / "0002-marks" / "gate-check" / "base").is_dir()
    assert all((minions / stray).is_file() for stray in _STRAYS)
    # Twin: a second start moves nothing.
    again = conduct["Run"](root, "claude")
    assert again.migrate_layout() is None
    assert " · move — " not in again.log.path.read_text()

    # An old file beside its new one halts the run before any worker.
    old = minions / "findings" / "0001-todo_review.md"
    old.write_text("old\n")
    run = ("run", "--executor", "claude")
    assert _main(conduct, root, *run, monkeypatch=monkeypatch) == 1
    assert _calls(calls) == []
    both = (
        " · run · halt — .minions/findings/0001-todo_review.md and"
        " .minions/changes/0001-todo/review.md both stand"
    )
    logs = (minions / "runs").glob("*.md")
    assert both in "".join(log.read_text() for log in logs)
    assert old.read_text() == "old\n"
    old.unlink()

    # A link at an old file, or at a change's folder, halts with nothing moved.
    target = tmp_path / "elsewhere.toml"
    target.write_text("[build]\n")
    linked = minions / "models" / "0001-todo.toml"
    linked.symlink_to(target)
    assert conduct["Run"](root, "claude").migrate_layout() == (
        ".minions/models/0001-todo.toml is a link: a person settles what it names"
    )
    linked.unlink()
    folder, aside = minions / "changes" / "0002-marks", tmp_path / "aside"
    folder.rename(aside)
    folder.symlink_to(aside)
    (minions / "rescue").mkdir()
    (minions / "rescue" / "0002-marks.md").write_text("diagnosis\n")
    assert conduct["Run"](root, "claude").migrate_layout() == (
        ".minions/changes/0002-marks is a link: a person settles what it names"
    )
    assert not (aside / "rescue.md").exists()
    assert (minions / "rescue" / "0002-marks.md").is_file()
    folder.unlink()
    aside.rename(folder)

    # A link at an old folder halts too, and nothing moves from where it points.
    outside, kept = tmp_path / "outside", tmp_path / "kept"
    (outside / "0009-x").mkdir(parents=True)
    held = ["0009-x", "0009-x_converge.log", "0009-x_review.md"]
    for name in held[1:]:
        (outside / name).write_text("theirs\n")
    for old in ("findings", "gate-check", "runs/20261101-230000"):
        (minions / old).rename(kept)
        (minions / old).symlink_to(outside)
        assert conduct["Run"](root, "claude").migrate_layout() == (
            f".minions/{old} is a link: a person settles what it names"
        )
        assert sorted(path.name for path in outside.iterdir()) == held
        (minions / old).unlink()
        kept.rename(minions / old)


def test_status_names_an_old_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root = _primary(tmp_path)
    _old_layout(root)
    status, report = conduct["status"], conduct["report"]
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    (runs / "20261101-230000.md").write_text(
        "# Ship run 20261101-230000\n\n"
        "10:00:00 · 0001-todo · spawn — build · model m\n"
        "10:00:01 · run · done — released none\n"
    )
    assert status(root).splitlines() == ["0001-todo · release", "0002-marks · build"]
    assert report(root).splitlines()[0].startswith("0001-todo · no tag · ")

    _to_old(root)
    old = "0001-todo · old layout — a run moves it"
    assert status(root).splitlines() == [
        old,
        "0002-marks · old layout — a run moves it",
    ]
    assert report(root).splitlines()[0] == old
    with pytest.raises(
        conduct["Stop"],
        match="grant: cannot run — .minions/build/0001-todo.done is the old layout:"
        " /mf-ship moves it",
    ):
        conduct["grant"](root, "0001-todo", "claude")


@pytest.mark.slow
def test_a_rerun_recovers_a_dead_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("dies-release-fold")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    def run(code: int) -> None:
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == code
        )

    def stage() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip()

    run(1)
    assert _git(tree, "status", "--porcelain")
    assert _git(root, "tag", "-l") == ""
    assert stage() == "0001-todo · release"
    calls.unlink()
    fake()
    run(0)
    assert _calls(calls) == ["probe", "release 0001-todo"]
    assert _git(root, "tag", "-l") == "v0.1.0"

    _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    calls.unlink()
    fake("dies-release-tag")
    run(1)
    assert _git(root, "tag", "-l").split() == ["v0.1.0", "v0.2.0"]
    assert _git(root, "branch", "--no-merged", "main").endswith(" 0002-marks")
    assert stage() == "0002-marks · release"
    stage_of, find = conduct["stage_of"], conduct["find_version"]
    assert stage_of(root, find(root, "0002-marks"))[1] == (
        "v0.2.0 is tagged; the merge is left"
    )
    # A person's no outlasts the death: the stage reads `released`, and nothing merges.
    held = root / ".minions" / "changes" / "0002-marks" / "release.held"
    held.parent.mkdir(parents=True, exist_ok=True)
    held.write_text("no: the preamble needs reading\n")
    said = (
        "v0.2.0: .minions/changes/0002-marks/release.held holds a person's no:"
        " /mf-release 0002-marks merges it on their yes"
    )
    assert stage_of(root, find(root, "0002-marks")) == ("released", said)
    calls.unlink()
    fake()
    run(1)
    assert _calls(calls) == []
    assert any(
        line.endswith(f" · 0002-marks · halt — released — {said}")
        for line in _log(root)
    )
    assert _git(root, "branch", "--no-merged", "main").endswith(" 0002-marks")
    held.unlink()
    run(0)
    assert _calls(calls) == ["probe", "release 0002-marks"]
    assert _git(root, "tag", "-l").split() == ["v0.1.0", "v0.2.0"]
    assert _git(root, "branch", "--no-merged", "main") == ""


@pytest.mark.slow
def test_a_release_cut_short_is_recovered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("dies-release-tag")
    root = _primary(tmp_path)
    # The fake worker numbers its tag by the tags it finds.
    _released(root, "v0.1.0")
    _released(root, "v0.2.0")
    stage_of, find = conduct["stage_of"], conduct["find_version"]

    def run(code: int) -> None:
        assert _run_claude(conduct, root, monkeypatch) == code

    def stage() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip()

    _version(root, "0003-more", "- [ ] 1 — More\n")
    run(1)
    _commit(root, {"moved.txt": "x\n"}, "main moves")
    assert stage() == "0003-more · released"
    calls.unlink()
    fake()
    run(1)
    assert _calls(calls) == []
    assert any(
        line.endswith(
            " · 0003-more · halt — released — v0.3.0 is tagged; main moved, so recover"
            " by hand: git tag -d v0.3.0, git reset --hard HEAD~1, then"
            " /mf-integrate 0003-more, /mf-converge, /mf-release"
        )
        for line in _log(root)
    )
    _git(root, "tag", "-d", "v0.3.0")
    assert stage_of(root, find(root, "0003-more")) == (
        "released",
        "v0.3.0 is not tagged; main moved, so recover by hand: git reset --hard HEAD~1,"
        " then /mf-integrate 0003-more, /mf-converge, /mf-release",
    )
    _git(root, "tag", "v0.3.0", "0003-more")

    def last() -> str:
        return stage().splitlines()[-1]

    _version(root, "0004-four", "- [ ] 1 — Four\n")
    fake("dies-release-commit")
    run(1)
    assert "v0.4.0" not in _git(root, "tag", "-l").split()
    assert last() == "0004-four · release"
    assert stage_of(root, find(root, "0004-four"))[1] == (
        "v0.4.0 is not tagged; the merge is left"
    )
    calls.unlink()
    fake()
    run(1)
    assert "release 0004-four" in _calls(calls)
    assert "v0.4.0" in _git(root, "tag", "-l").split()
    assert "0004-four" not in _git(root, "branch", "--no-merged", "main")

    _version(root, "0005-five", "- [ ] 1 — Five\n")
    calls.unlink()
    fake("stops-release-tag")
    run(1)
    assert "v0.5.0" in _git(root, "tag", "-l").split()
    assert last() == "0005-five · released"
    assert stage_of(root, find(root, "0005-five"))[1] == (
        "v0.5.0 is tagged; the release stopped before its merge:"
        " /mf-release 0005-five merges it on a person's yes"
    )
    calls.unlink()
    fake()
    run(1)
    assert "release 0005-five" not in _calls(calls)

    forged = _version(root, "0006-six", "- [ ] 1 — Six\n")
    _git(forged, "commit", "-q", "--allow-empty", "-m", "chore(release): v0.1.0")
    assert last() == "0006-six · released"
    assert stage_of(root, find(root, "0006-six"))[1] == (
        "v0.1.0 is tagged on another commit: a person reads this tip"
    )
    subject = "chore(release): v9.0.0"
    _git(forged, "commit", "-q", "--amend", "--allow-empty", "-m", subject)
    assert last() == "0006-six · released"
    assert stage_of(root, find(root, "0006-six"))[1] == (
        "v9.0.0 is not tagged; no review findings file: a person reads this tip"
    )
    _findings(root, "0006-six", _git(forged, "rev-parse", "HEAD~1"))
    _git(forged, "tag", "v9.0.0")
    assert last() == "0006-six · released"


@pytest.mark.slow
def test_a_dead_integrate_is_resumed_by_a_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("dies-integrate")
    stage_of, find = conduct["stage_of"], conduct["find_version"]
    second = _primary(tmp_path)
    moved = _version(second, "0001-todo", "- [x] 1 — Todo\n")
    _commit(moved, {"moved.txt": "theirs\n"}, "the version")
    _findings(second, "0001-todo", _git(moved, "rev-parse", "HEAD"))
    _commit(second, {"moved.txt": "ours\n"}, "main moves")
    assert _run_claude(conduct, second, monkeypatch) == 1
    assert _calls(calls) == ["probe", "integrate 0001-todo"]
    assert stage_of(second, find(second, "0001-todo")) == (
        "integrate",
        "interrupted: a merge is open with no note",
    )
    calls.unlink()
    fake()
    assert _run_claude(conduct, second, monkeypatch) == 0
    assert _calls(calls) == [
        "probe",
        "integrate 0001-todo",
        "converge 0001-todo",
        "release 0001-todo",
    ]
    assert "chore(integrate): merge main into 0001-todo" in _git(
        second, "log", "--format=%s", "main"
    )


@pytest.mark.slow
def test_a_rerun_pushes_what_a_release_left(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "operator.gitconfig"))
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    _released(root, "v0.1.0")
    _git(root, "tag", "unrelated")

    def status() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip()

    def run(code: int) -> None:
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == code
        )

    # Before a first run `status` calls nothing, and the run's own read finds the tag.
    unread = "run · unread — a run reads origin's tags, and keeps its URLs"
    assert status() == f"run · unpushed main\n{unread}"
    _git(root, "config", "--global", "hook.operator.event", "pre-push")
    _git(root, "config", "--global", "hook.operator.command", "exit 1")
    run(0)
    _git(root, "config", "--global", "--remove-section", "hook.operator")
    assert _calls(calls) == []
    lines = _log(root)
    assert [line.split(" · ", 1)[1] for line in lines[1:]] == [
        "run · push — main",
        "run · push — v0.1.0",
        "run · done — nothing to ship",
    ]
    log = conduct["last_log"](root / ".minions" / "runs")
    assert (
        _main(conduct, root, "log", "--verify", str(log), monkeypatch=monkeypatch) == 0
    )
    head = _git(root, "rev-parse", "main")
    assert head in _git(root, "ls-remote", "origin", "refs/heads/main")
    assert "refs/tags/v0.1.0" in _git(root, "ls-remote", "--tags", "origin")
    assert status() == "status: none — no open version"

    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(origin), str(other))
    _commit(other, {"theirs.txt": "x\n"}, "origin moves")
    _git(other, "push", "-q", "origin", "main")
    _released(root, "v0.2.0")
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 1
    moved = _git(other, "rev-parse", "--short=7", "main").strip()
    assert capsys.readouterr().out.strip() == (
        f"conduct: halt — origin's main is at {moved}, which this repo lacks:"
        " a person fetches"
    )
    _git(root, "fetch", "-q", "origin")
    assert status() == "run · unpushed main v0.2.0"
    run(1)
    assert _calls(calls) == []
    lines = _log(root)
    assert lines[-2].endswith(" · run · halt — git push origin main failed, exit 1")
    assert lines[-1].endswith(
        " · run · halt — halted run · blocked none · released none"
        " · unpushed main v0.2.0"
    )
    tagged = _git(root, "rev-parse", "v0.1.0^{commit}")
    assert tagged in _git(root, "ls-remote", "origin", "refs/tags/v0.1.0^{}")


def _left_unpushed(
    tmp_path: Path, conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Return a primary and its origin: a run pushed `v0.1.0`, and `v0.2.0` waits."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "operator.gitconfig"))
    root, origin = _with_origin(tmp_path)
    _released(root, "v0.1.0")
    assert _run_claude(conduct, root, monkeypatch) == 0
    _released(root, "v0.2.0")
    return root, origin


def _planted(tmp_path: Path) -> tuple[Path, Path]:
    """Return a script that touches a file and fails, and that file's path."""
    ran = tmp_path / "ran.txt"
    planted = tmp_path / "planted.sh"
    planted.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(ran))}\nexit 1\n")
    planted.chmod(0o755)
    return planted, ran


def _status(
    conduct: dict[str, Any],
    root: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    code: int = 0,
) -> str:
    """Return what `status` prints in `root`, asserting it exits `code`."""
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == code
    return capsys.readouterr().out.strip()


@pytest.mark.slow
def test_a_planted_remote_key_refuses_status_and_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root, _ = _left_unpushed(tmp_path, conduct, monkeypatch)
    planted, ran = _planted(tmp_path)

    _git(root, "config", "protocol.version", "2")
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0

    _git(root, "config", "remote.origin.uploadpack", str(planted))
    assert "remote.origin.uploadpack" in _status(conduct, root, capsys, monkeypatch, 1)
    assert _run_claude(conduct, root, monkeypatch) == 1
    assert not ran.exists()
    log = conduct["last_log"](root / ".minions" / "runs")
    assert " · run · halt — conduct: halt — " in log.read_text()
    _git(root, "config", "--unset", "remote.origin.uploadpack")

    def refused(named: str) -> None:
        assert named in _status(conduct, root, capsys, monkeypatch, 1)
        assert _run_claude(conduct, root, monkeypatch) == 1
        assert not ran.exists()

    command = str(planted)
    (root / ".git" / "info" / "attributes").write_text("* filter=probe\n")
    os.utime(root / "AGENTS.md", (1, 1))
    _git(root, "config", "filter.probe.clean", command)
    refused("filter.probe.clean")
    log = conduct["last_log"](root / ".minions" / "runs")
    assert "filter.probe.clean" in log.read_text()
    _git(root, "config", "--unset", "filter.probe.clean")
    for key, value in (
        ("hook.probe.event", "pre-push"),
        ("hook.probe.command", command),
        ("filter.probe.clean", command),
        ("merge.probe.driver", command),
        ("include.path", "absent.gitconfig"),
        ("a.key.git.adds.later", command),
    ):
        _git(root, "config", key, value)
        refused(key)
        _git(root, "config", "--unset", key)

    elsewhere = _elsewhere(tmp_path)
    hook = elsewhere / "hooks" / "pre-receive"
    hook.write_text(planted.read_text())
    hook.chmod(0o755)
    _git(root, "config", "remote.origin.pushurl", str(elsewhere))
    refused("remote.origin.pushurl")
    _git(root, "config", "--unset", "remote.origin.pushurl")

    _git(root, "remote", "remove", "origin")
    _git(root, "config", "hook.probe.event", "pre-push")
    refused("hook.probe.event")
    log = conduct["last_log"](root / ".minions" / "runs")
    assert "hook.probe.event" in log.read_text()


@pytest.mark.slow
def test_a_key_set_after_the_refusal_reaches_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, origin = _left_unpushed(tmp_path, conduct, monkeypatch)
    planted, ran = _planted(tmp_path)
    # Origin's main moved ahead and was fetched, so the push is refused.
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(origin), str(other))
    _commit(other, {"theirs.txt": "x\n"}, "origin moves")
    _git(other, "push", "-q", "origin", "main")
    _git(root, "fetch", "-q", "origin")

    # A worker's toggle: the refusal reads the file clean, then the key stands. Each
    # remote call reads no repo's config, and the push keeps the run's first URL.
    conductor = conduct["Run"](root, "claude")
    module = conduct["main"].__globals__
    monkeypatch.setitem(module, "_refuse_config_commands", lambda _: None)
    for key in ("remote.origin.uploadpack", "remote.origin.receivepack"):
        _git(root, "config", key, str(planted))
    conductor.git_state = conduct["_git_state"](root)
    conductor.push_left((0,))
    assert not ran.exists()
    assert conduct["_pushed"](root, "release-v0.2.0", "v0.2.0") is False
    assert not ran.exists()
    conduct["_kept_file"](root).unlink()
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(decoy))
    _git(root, "remote", "set-url", "origin", str(decoy))
    conductor.git_state = conduct["_git_state"](root)
    conductor.push_left((0,))
    assert _git(decoy, "for-each-ref") == ""


def test_the_scratch_stands_outside_the_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, _ = _with_origin(tmp_path)
    # The scratch stands where no worker writes, and a sandboxed `status` still runs.
    with conduct["_scratch"]() as scratch:
        assert Path(scratch).parent == Path.home()
    with monkeypatch.context() as patch:
        patch.setenv("HOME", str(tmp_path / "absent"))
        with conduct["_scratch"]() as scratch:
            assert Path(scratch).is_dir()
        conduct["_keep_origin"](root)
        assert conduct["_kept_origin"](root) is None


def test_a_local_origin_url_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root, _ = _left_unpushed(tmp_path, conduct, monkeypatch)
    # With no URLs kept, the URL's own form is what refuses it.
    conduct["_kept_file"](root).unlink()
    planted, ran = _planted(tmp_path)
    command = str(planted)
    elsewhere = _elsewhere(tmp_path)
    with monkeypatch.context() as patch:
        patch.delenv("MF_SHIP_AGENT")
        for url in (
            str(elsewhere),
            f"file://{elsewhere}",
            "./elsewhere.git",
            f"ext::{command}",
        ):
            _git(root, "remote", "set-url", "origin", url)
            said = _status(conduct, root, capsys, monkeypatch, 1)
            assert "points origin at a local repo" in said
            conductor = conduct["Run"](root, "claude")
            conductor.push_left((0,))
            assert [who for who, _ in conductor.halts] == ["run"]
            conductor.log.path.unlink()
            assert not ran.exists()
    for url in ("https://example.invalid/r.git", "git@example.invalid:r.git"):
        assert conduct["NETWORK_URL"].fullmatch(url)


def test_a_tag_alone_starts_one_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "operator.gitconfig"))

    def status() -> str:
        return _status(conduct, root, capsys, monkeypatch)

    # No run kept this repo, and it merged no tag to read for: no line, so no run.
    root, _ = _with_origin(tmp_path)
    assert status() == "status: none — no open version"

    # A tag alone: `status` calls nothing, its line starts the run, and that run's own
    # read finds the tag. It keeps the URLs, so no second run starts.
    _released(root, "v0.3.0")
    _git(root, "push", "-q", "origin", "main")
    assert status() == "run · unread — a run reads origin's tags, and keeps its URLs"
    assert _run_claude(conduct, root, monkeypatch) == 0
    assert "refs/tags/v0.3.0" in _git(root, "ls-remote", "--tags", "origin")
    assert status() == "status: none — no open version"


def _origin_judged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> tuple[dict[str, Any], Path, Callable[..., None]]:
    """Return the conductor, a primary with its `origin` kept, and `halts_on`.

    `halts_on(name, push)` asserts status and a run halt on `name`, pushing nothing.
    """
    conduct = _conduct()
    calls = fake()
    root, _ = _with_origin(tmp_path)
    conduct["_keep_origin"](root)
    pushed = _git(root, "rev-parse", "main")

    def halts_on(name: str, push: str = "main") -> None:
        said = (
            f"conduct: halt — main holds {name}, no run's release: a person reads it,"
            f" then git push origin {push}"
        )
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 1
        assert capsys.readouterr().out.strip() == said
        assert _run_claude(conduct, root, monkeypatch) == 1
        log = conduct["last_log"](root / ".minions" / "runs").read_text()
        assert f" · run · halt — {said}\n" in log
        assert _git(root, "ls-remote", "origin", "refs/heads/main").split()[0] == pushed
        assert _calls(calls) == []

    return conduct, root, halts_on


def test_a_plain_commit_on_main_is_not_pushed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    _, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    _commit(root, {"mine.txt": "x\n"}, "a person's commit")
    halts_on(_git(root, "rev-parse", "main")[:7])


def test_a_tagged_side_merge_is_not_pushed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    _, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    _git(root, "switch", "-q", "-c", "side")
    _git(root, "commit", "-q", "--allow-empty", "-m", "feat: side")
    _git(root, "tag", "v0.9.0")
    _git(root, "switch", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch 'side'", "side")
    halts_on(_git(root, "rev-parse", "main")[:7])


def test_a_release_merge_no_run_made_is_not_pushed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    _, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    refused = ("v0.7.0", "v0.8.0")
    for tag in refused:
        _git(root, "switch", "-q", "-c", f"release-{tag}", "main")
        _commit(root, {tag: "x\n"}, f"chore(release): {tag}")
        _git(root, "tag", "-a", "-m", tag, tag)
    _git(root, "switch", "-q", "main")
    for tag in refused:
        _git(root, "merge", "-q", "--no-ff", "-m", "a merge", f"release-{tag}")
    halts_on(_git(root, "rev-parse", "main")[:7])


def test_a_bare_version_tag_is_not_pushed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    _, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    _git(root, "tag", "v0.45.0")
    halts_on("v0.45.0", "v0.45.0")
    assert _git(root, "ls-remote", "--tags", "origin") == ""


def test_a_hand_release_is_the_persons_to_push(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    _, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    _released(root, "v0.3.0", by_hand=True)
    halts_on(_git(root, "rev-parse", "main")[:7])
    assert _git(root, "ls-remote", "--tags", "origin") == ""


@pytest.mark.slow
def test_a_stray_tag_on_a_run_release_halts_until_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct, root, halts_on = _origin_judged(tmp_path, monkeypatch, capsys, fake)
    _released(root, "v0.1.0")
    _git(root, "tag", "v0.2.0", "release-v0.1.0")
    halts_on("v0.2.0", "v0.2.0")
    _git(root, "tag", "-d", "v0.2.0")
    assert conduct["_ledger_heads"](root) == {
        _git(root, "rev-parse", "v0.1.0^{commit}^")
    }
    assert _run_claude(conduct, root, monkeypatch) == 0
    on_origin = _git(root, "ls-remote", "origin", "refs/heads/main").split()[0]
    assert on_origin == _git(root, "rev-parse", "main")
    assert "refs/tags/v0.1.0" in _git(root, "ls-remote", "--tags", "origin")
    assert conduct["_ledger_heads"](root) == set()


def test_a_secret_in_the_push_range_halts_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    conduct["_keep_origin"](root)
    pushed = _git(root, "ls-remote", "origin")
    # Built from parts so this file never matches the gate's scan.
    key = "gh" + "p_" + "4Fq9Lx2Rm7Tv" + "5Wk8Zn3Yb6Hc" + "1Jd0Sg7Pu2Ea"
    _released(root, "v0.1.0", files={"settings.txt": f"token: {key}\n"})
    leaked = _git(root, "rev-parse", "v0.1.0^{commit}^").strip()

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    said = (
        "conduct: halt — the push range holds a secret: github-pat in settings.txt"
        f" at {leaked[:7]}; nothing pushed"
    )
    assert f" · run · halt — {said}\n" in log
    assert key not in log
    assert _git(root, "ls-remote", "origin") == pushed
    assert _calls(calls) == []

    # A key that only a merge commit adds, staged while the merge was open, halts too.
    tip = _git(root, "rev-parse", "main")
    _git(root, "switch", "-q", "-c", "side")
    _commit(root, {"side.txt": "x\n"}, "a side commit")
    _git(root, "switch", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "--no-commit", "side")
    _commit(root, {"merged.txt": f"token: {key}\n"}, "a merge")
    merge = _git(root, "rev-parse", "HEAD")
    assert _git(root, "rev-list", "--count", "--merges", f"{tip}..{merge}") == "1"
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_scan"](root, tip, merge)
    assert str(stopped.value) == (
        "conduct: halt — the push range holds a secret: github-pat in merged.txt"
        f" at {merge[:7]}; nothing pushed"
    )

    # An allow comment a worker writes on the key's line does not hide it.
    tip = _git(root, "rev-parse", "main")
    _commit(root, {"allowed.txt": f"token: {key}  # gitleaks:allow\n"}, "allowed")
    allowed = _git(root, "rev-parse", "HEAD")
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_scan"](root, tip, allowed)
    assert str(stopped.value) == (
        "conduct: halt — the push range holds a secret: github-pat in allowed.txt"
        f" at {allowed[:7]}; nothing pushed"
    )

    # git shows no octopus merge's diff, so a key one adds halts as unreadable.
    tip = _git(root, "rev-parse", "main")
    for side in ("left", "right"):
        _git(root, "switch", "-q", "-c", side, tip)
        _commit(root, {f"{side}.txt": "x\n"}, f"a {side} commit")
    _git(root, "switch", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "--no-commit", "left", "right")
    _commit(root, {"octopus.txt": f"token: {key}\n"}, "an octopus merge")
    octopus = _git(root, "rev-parse", "HEAD")
    assert _git(root, "rev-list", "--count", "--min-parents=3", f"{tip}..main") == "1"
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_scan"](root, tip, octopus)
    assert str(stopped.value) == (
        "conduct: halt — the push range holds an octopus merge, which the scan cannot"
        f" read: {octopus[:7]}; nothing pushed"
    )

    # An ignore file a worker writes into the primary, the conductor's folder, does not.
    tip = _git(root, "rev-parse", "main")
    _commit(root, {"ignored.txt": f"token: {key}\n"}, "ignored")
    ignored = _git(root, "rev-parse", "HEAD")
    (root / ".gitleaksignore").write_text(f"{ignored}:ignored.txt:github-pat:1\n")
    monkeypatch.chdir(root)
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_scan"](root, tip, ignored)
    assert str(stopped.value) == (
        "conduct: halt — the push range holds a secret: github-pat in ignored.txt"
        f" at {ignored[:7]}; nothing pushed"
    )

    # A scan that fails, or cannot start, halts as a hit does.
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_scan"](root, None, "0" * 40)
    assert stopped.value.code == 1
    assert str(stopped.value).startswith("conduct: halt — the secret scan failed: ")
    assert str(stopped.value).endswith("; nothing pushed")
    failing = tmp_path / "failing-scan"
    failing.write_text("#!/bin/sh\necho 'no repo here' >&2\nexit 1\n")
    failing.chmod(0o755)
    for scanner, why in (
        (str(failing), "the secret scan failed: no repo here"),
        (str(tmp_path / "absent"), "the secret scan cannot run: "),
    ):
        conduct["main"].__globals__["SCANNER"] = scanner
        with pytest.raises(conduct["Stop"]) as stopped:
            conduct["_scan"](root, None, leaked)
        assert stopped.value.code == 1
        assert f"conduct: halt — {why}" in str(stopped.value)
        assert str(stopped.value).endswith("; nothing pushed")


def test_a_run_without_betterleaks_stops_at_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    conduct["main"].__globals__["SCANNER"] = "betterleaks-absent"

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )

    assert capsys.readouterr().out.strip() == (
        "run: cannot run — betterleaks-absent is not on PATH:"
        " brew install betterleaks-absent"
    )
    assert _calls(calls) == []
    assert not (root / ".minions" / "runs").exists()


def test_a_run_holds_the_machine_awake(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    folder = tmp_path / "caffeinate-bin"
    folder.mkdir()
    argv = tmp_path / "caffeinate-argv.txt"
    tool = folder / "caffeinate"
    tool.write_text(f'#!/bin/sh\necho "$@" >> {shlex.quote(str(argv))}\n')
    tool.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)

    assert conduct["_hold_awake"](4242) == "awake: held"
    deadline = time.monotonic() + 10
    while not (argv.is_file() and argv.read_text()) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert argv.read_text() == "-is -w 4242\n"

    conduct["_hold_awake"].__globals__["CAFFEINATE"] = "caffeinate-absent"
    assert conduct["_hold_awake"](4242) == "awake: not held — caffeinate not on PATH"
    assert argv.read_text() == "-is -w 4242\n"

    # A run's `start` line ends with the field, after the release, and the run goes on
    # without the tool.
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    root = _primary(tmp_path)
    kept = Path.home() / conduct["KEPT_ORIGINS"]
    kept.mkdir()
    (kept / "pending").write_text("v9.9.9\n")
    for name, field in (
        ("caffeinate", "awake: held"),
        ("caffeinate-absent", "awake: not held — caffeinate not on PATH"),
    ):
        conduct["_hold_awake"].__globals__["CAFFEINATE"] = name
        conductor = conduct["Run"](root, "claude")
        assert conductor.ship() == 0
        lines = conductor.log.path.read_text().splitlines()[2:]
        assert " · run · start — " in lines[0]
        assert lines[0].endswith(f" · pending v9.9.9 · {field}")
        assert lines[-1].endswith(" · run · done — nothing to ship")


def _run_claude(
    conduct: dict[str, Any], root: Path, monkeypatch: pytest.MonkeyPatch
) -> int:
    return _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)


def _halts_on_main(
    conduct: dict[str, Any], root: Path, calls: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert a run halts on `main`'s head, pushing nothing and starting no worker."""
    listed = _git(root, "ls-remote", "origin")
    name = _git(root, "rev-parse", "main")[:7]
    assert _run_claude(conduct, root, monkeypatch) == 1
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert f" · run · halt — conduct: halt — main holds {name}, no run's" in log
    assert _git(root, "ls-remote", "origin") == listed
    assert _calls(calls) == []


_VIEWS = ("replace", "graft", "shallow")


def _push_then_forge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake: Callable[..., Path],
    *cases: tuple[str, ...],
) -> None:
    """Push a run's release per case, mutated as it names, then forge one on its head.

    The forged release halts the next run, and the pushed head is retired.
    """
    conduct = _conduct()
    calls = fake()
    root, _ = _with_origin(tmp_path)
    conduct["_keep_origin"](root)
    module = conduct["main"].__globals__
    outside = module["_outside"]
    close = module["_close_releases"]
    git_dir = root / ".git"
    for number, mutation in enumerate(cases, start=1):
        tag = f"v0.{number}.0"
        branch = f"refs/heads/release-{tag}"
        _released(root, tag)
        commit = _git(root, "rev-parse", f"{tag}^{{commit}}")
        head = _git(root, "rev-parse", f"{commit}^")

        def push(
            cwd: Path,
            *args: str,
            timeout: int = conduct["GIT_TIMEOUT"],
            mutation: tuple[str, ...] = mutation,
            tag: str = tag,
            branch: str = branch,
            commit: str = commit,
        ) -> subprocess.CompletedProcess[str]:
            if (
                "failed-push" in mutation
                and args[0] == "push"
                and args[-1].endswith(":refs/heads/main")
            ):
                return subprocess.CompletedProcess(args, 1, "", "rejected")
            done = outside(cwd, *args, timeout=timeout)
            if (
                args[0] == "push"
                and args[-1].endswith(f":refs/tags/{tag}")
                and done.returncode == 0
            ):
                if "delete" in mutation:
                    _git(root, "update-ref", "-d", branch)
                # Each makes the release commit read as a root, its head gone.
                if "replace" in mutation:
                    _git(root, "replace", "--graft", commit)
                if "graft" in mutation:
                    (git_dir / "info").mkdir(exist_ok=True)
                    (git_dir / "info" / "grafts").write_text(f"{commit}\n")
                if "shallow" in mutation:
                    (git_dir / "shallow").write_text(f"{commit}\n")
            return done

        module["_outside"] = push
        if "resume" in mutation:
            # The conductor died after both pushes, before retiring the entry.
            module["_close_releases"] = lambda *_: None
        if "hand-finished" not in mutation:
            code = 1 if "failed-push" in mutation else 0
            assert _run_claude(conduct, root, monkeypatch) == code
        module["_outside"] = outside
        module["_close_releases"] = close
        if "failed-push" in mutation or "hand-finished" in mutation:
            # A person lands a halted run's release or finishes a release by hand.
            _git(root, "push", "-q", "origin", "main", tag)
        assert tag in _git(root, "ls-remote", "--tags", "origin")
        assert conduct["_ledger_heads"](root) == (
            {head}
            if any(
                case in mutation for case in ("resume", "failed-push", "hand-finished")
            )
            else set()
        ), mutation

        forged = f"v9.{number}.0"
        _git(root, "switch", "-q", "-c", "forged", head)
        _git(root, "commit", "-q", "--allow-empty", "-m", f"chore(release): {forged}")
        _git(root, "tag", "-a", "-m", forged, forged)
        _git(root, "switch", "-q", "main")
        _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch 'forged'", "forged")
        if "failed-push" in mutation or "hand-finished" in mutation:
            # Retirement is only cleanup: a landed head refuses even with it absent.
            module["_close_releases"] = lambda *_: None
            with pytest.raises(conduct["Stop"], match="no run's release"):
                conduct["_unpushed"](root, first_read=True)
            assert conduct["_ledger_heads"](root) == {head}, mutation
            module["_close_releases"] = close
        _halts_on_main(conduct, root, calls, monkeypatch)
        assert conduct["_ledger_heads"](root) == set(), mutation
        _git(root, "reset", "-q", "--hard", "HEAD~1")
        _git(root, "tag", "-d", forged)
        _git(root, "branch", "-D", "forged")
        if "replace" in mutation:
            _git(root, "replace", "-d", commit)
        (git_dir / "info" / "grafts").unlink(missing_ok=True)
        (git_dir / "shallow").unlink(missing_ok=True)


@pytest.mark.slow
def test_a_forged_release_is_not_pushed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root, _ = _with_origin(tmp_path)
    conduct["_keep_origin"](root)

    # A worker moves the local remote ref: the base is origin's own head.
    _commit(root, {"mine.txt": "x\n"}, "a plain commit")
    _git(root, "update-ref", "refs/remotes/origin/main", "main")
    _halts_on_main(conduct, root, calls, monkeypatch)


@pytest.mark.slow
def test_a_pushed_release_retires_its_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    _push_then_forge(tmp_path, monkeypatch, fake, ("keep",))


@pytest.mark.slow
def test_a_resumed_push_retires_at_the_next_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    # The conductor dies after both pushes, before retiring the entry; a concurrent
    # worker deletes its version ref, or rewrites the release commit's history with
    # a replace ref, a graft or `shallow`.
    cases = (("resume",), ("resume", "delete", *_VIEWS))
    _push_then_forge(tmp_path, monkeypatch, fake, *cases)


@pytest.mark.slow
def test_a_release_a_person_landed_refuses_a_forged_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    _push_then_forge(tmp_path, monkeypatch, fake, ("hand-finished",), ("failed-push",))


@pytest.mark.slow
def test_local_history_records_no_forged_release(
    tmp_path: Path, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, _ = _with_origin(tmp_path)
    conduct["_keep_origin"](root)
    git_dir = root / ".git"
    # A landed release merge, whose head the shallow view hides.
    _released(root, "v0.1.0", by_hand=True)
    _git(root, "push", "-q", "origin", "main", "v0.1.0")

    # Local history must not turn an unauthorized release into a recorded one.
    for number, view in enumerate(_VIEWS, start=20):
        tag = f"v9.{number}.0"
        base = _git(root, "rev-parse", "main")
        _released(root, tag, by_hand=True)
        commit = _git(root, "rev-parse", f"{tag}^{{commit}}")
        if view == "shallow":
            # A shallow base hides a ledger head that has already landed.
            head = _git(root, "rev-parse", f"{base}^2^")
            _git(root, "replace", "--graft", commit, head)
            replacement = _git(root, "rev-parse", f"refs/replace/{commit}")
            _git(root, "replace", "-d", commit)
            _git(root, "tag", "-f", tag, replacement)
            _git(root, "reset", "-q", "--hard", base)
            _git(root, "merge", "-q", "--no-ff", "-m", "forged", replacement)
            (git_dir / "shallow").write_text(f"{base}\n")
        else:
            head = _git(
                root, "commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "recorded"
            )
            if view == "replace":
                _git(root, "replace", "--graft", commit, head)
            else:
                (git_dir / "info" / "grafts").write_text(f"{commit} {head}\n")
        conduct["_record_release"](root, "recorded", head)
        listed = _git(root, "ls-remote", "origin")
        with pytest.raises(conduct["Stop"], match="no run's release"):
            conduct["_unpushed"](root, first_read=True)
        assert _git(root, "ls-remote", "origin") == listed
        if view == "replace":
            _git(root, "replace", "-d", commit)
        (git_dir / "info" / "grafts").unlink(missing_ok=True)
        (git_dir / "shallow").unlink(missing_ok=True)
        _git(root, "reset", "-q", "--hard", base)
        _git(root, "tag", "-d", tag)
        conduct["_ledger"](root).joinpath("recorded").unlink(missing_ok=True)


@pytest.mark.slow
def test_a_forged_release_on_an_older_default_is_not_pushed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root, origin = _with_origin(tmp_path)
    conduct["_keep_origin"](root)

    def run() -> int:
        return _run_claude(conduct, root, monkeypatch)

    # A worker points `origin/HEAD` at an older origin branch and forges a release
    # there, on a head that landed on origin's own default: the push judges `main`.
    older = _git(root, "rev-parse", "main")
    _git(root, "push", "-q", "origin", "main:refs/heads/maintenance")
    _released(root, "v0.30.0")
    head = _git(root, "rev-parse", "v0.30.0^{commit}^")
    _git(root, "push", "-q", "origin", "main", "v0.30.0")
    _git(root, "update-ref", "refs/remotes/origin/maintenance", older)
    _git(
        root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/maintenance",
    )
    _git(root, "switch", "-q", "-c", "forged", head)
    _git(root, "commit", "-q", "--allow-empty", "-m", "chore(release): v9.30.0")
    _git(root, "tag", "-a", "-m", "v9.30.0", "v9.30.0")
    _git(root, "switch", "-q", "-c", "maintenance", older)
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch 'forged'", "forged")
    listed = _git(root, "ls-remote", "origin")
    assert run() == 0
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert " · run · push — " not in log
    assert _git(root, "ls-remote", "origin") == listed
    assert _calls(calls) == []
    _git(root, "switch", "-q", "main")
    _git(root, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    _git(root, "branch", "-D", "maintenance", "forged")
    _git(root, "tag", "-d", "v9.30.0")

    # Origin's own HEAD leaves the name the run kept: a run's release is not pushed.
    _released(root, "v0.31.0")
    kept = conduct["_kept_file"](root)
    named = kept.with_name(f"{kept.name}.default")
    _git(origin, "symbolic-ref", "HEAD", "refs/heads/maintenance")
    listed = _git(root, "ls-remote", "origin")
    assert run() == 1
    said = (
        "conduct: halt — origin's HEAD names maintenance, and the run kept main: a"
        f" person decides, then removes ~/.mf-ship-origin/{named.name}"
    )
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert f" · run · halt — {said}\n" in log
    assert _git(root, "ls-remote", "origin") == listed
    # Twin: a person restores it and removes the kept name; the run keeps it anew.
    _git(origin, "symbolic-ref", "HEAD", "refs/heads/main")
    named.unlink()
    assert run() == 0
    assert "refs/tags/v0.31.0" in _git(root, "ls-remote", "--tags", "origin")
    assert named.read_text() == "main"
    assert _calls(calls) == []


@pytest.mark.slow
def test_no_worker_pushes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, _ = _shipped_once(tmp_path, conduct, monkeypatch)

    lines = [line.split(" · ", 1)[1] for line in _log(root)]
    # Twin: a home folder that takes the file logs no `unkept`.
    assert not any(line.startswith("run · unkept") for line in lines)
    finish = next(
        i for i, line in enumerate(lines) if line.startswith("0001-todo · finish — rel")
    )
    assert lines[finish + 1 :] == [
        "run · push — main",
        "run · push — v0.1.0",
        "0001-todo · check — release · pass",
        f"0001-todo · removed — {root.parent / '0001-todo'}: ignored none",
        "run · done — released v0.1.0",
    ]
    assert _git(root, "rev-parse", "main") in _git(root, "ls-remote", "origin", "main")
    assert "refs/tags/v0.1.0" in _git(root, "ls-remote", "--tags", "origin")
    assert conduct["_ledger_heads"](root) == set()


_PUSH_COMMANDS = (("status",), ("check", "release", "0001-todo"), ("report",))


def _spied(
    conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, ...]]:
    """Return the args of each remote call the conductor makes from now on."""
    module = conduct["main"].__globals__
    outside = module["_outside"]
    reached: list[tuple[str, ...]] = []

    def spy(
        primary: Path, *args: str, timeout: int = 60
    ) -> subprocess.CompletedProcess[str]:
        reached.append(args)
        return outside(primary, *args, timeout=timeout)

    monkeypatch.setitem(module, "_outside", spy)
    return reached


def _elsewhere(tmp_path: Path) -> Path:
    """Return a bare repo a worker would point `origin` at."""
    elsewhere = tmp_path / "elsewhere.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(elsewhere))
    return elsewhere


def _shipped_once(
    tmp_path: Path, conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Return a primary whose clean run pushed `0001-todo`'s release, and its origin."""
    root, origin = _with_origin(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    assert _run_claude(conduct, root, monkeypatch) == 0
    return root, origin


@pytest.mark.slow
def test_a_worker_repointing_origin_reaches_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    # A worker repoints `origin`, a plain key at a network URL's form: nothing leaves.
    fake("plant-origin")
    root, origin = _with_origin(tmp_path)
    elsewhere = _elsewhere(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    reached = _spied(conduct, monkeypatch)

    assert _run_claude(conduct, root, monkeypatch) == 1

    assert _git(elsewhere, "for-each-ref") == ""
    said = " · run · halt — the local git config changed during the run: .git/config"
    assert any(line.endswith(f"{said} differs") for line in _log(root))
    # An `ls-remote` leaves no ref there: the URL itself is what would leave.
    assert not any(str(elsewhere) in args for args in reached)
    for command in _PUSH_COMMANDS:
        assert _main(conduct, root, *command, monkeypatch=monkeypatch) == 1
    assert not any(str(elsewhere) in args for args in reached)

    # A re-run is no first read: the URLs a run kept stand until a person acts.
    fake()

    def rerun(code: int) -> str:
        assert _run_claude(conduct, root, monkeypatch) == code
        return conduct["last_log"](root / ".minions" / "runs").read_text()

    log = rerun(1)
    assert _git(elsewhere, "for-each-ref") == ""
    assert " · run · halt — conduct: halt — the repo's git config points origin" in log
    assert str(elsewhere) not in log

    _git(root, "remote", "set-url", "origin", str(origin))
    assert " · run · done — " in rerun(0)
    assert _git(root, "rev-parse", "main") in _git(root, "ls-remote", "origin", "main")


def _aside(tmp_path: Path, origin: Path, elsewhere: Path) -> Path:
    """Return a worker's clone of `origin`, its own `origin` pointed `elsewhere`."""
    aside = tmp_path / "aside"
    _git(tmp_path, "clone", "-q", str(origin), str(aside))
    _git(aside, "remote", "set-url", "origin", str(elsewhere))
    return aside


@pytest.mark.slow
def test_a_redirected_git_dir_reaches_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, origin = _shipped_once(tmp_path, conduct, monkeypatch)
    elsewhere = _elsewhere(tmp_path)
    reached = _spied(conduct, monkeypatch)
    # A worker redirects git to a repo of its own, which no kept URLs guard.
    aside = _aside(tmp_path, origin, elsewhere)

    def redirected() -> None:
        codes = [
            _main(conduct, root, *command, monkeypatch=monkeypatch)
            for command in _PUSH_COMMANDS
        ]
        assert not any(str(elsewhere) in args for args in reached)
        assert codes == [1, 1, 1]

    commondir = root / ".git" / "commondir"
    commondir.write_text(f"{aside / '.git'}\n")
    redirected()
    commondir.unlink()

    _git(aside, "worktree", "add", "-q", "-b", "forged", str(tmp_path / "forged"))
    moved = root / ".git-moved"
    (root / ".git").rename(moved)
    (root / ".git").symlink_to(aside / ".git")
    redirected()
    (root / ".git").unlink()
    for target in (aside / ".git", aside / ".git" / "worktrees" / "forged"):
        (root / ".git").write_text(f"gitdir: {target}\n")
        redirected()
        (root / ".git").unlink()
    moved.rename(root / ".git")


@pytest.mark.slow
def test_a_repo_inside_a_worktree_reads_only_local(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root, origin = _shipped_once(tmp_path, conduct, monkeypatch)
    elsewhere = _elsewhere(tmp_path)
    reached = _spied(conduct, monkeypatch)
    aside = _aside(tmp_path, origin, elsewhere)

    # A linked worktree stands once a run kept its repo, and not redirected.
    tree = _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    assert _main(conduct, tree, "status", monkeypatch=monkeypatch) == 0
    entry = root / ".git" / "worktrees" / "0002-marks" / "commondir"
    held = entry.read_text()
    entry.write_text(f"{aside / '.git'}\n")
    assert _main(conduct, tree, "status", monkeypatch=monkeypatch) == 1
    assert not any(str(elsewhere) in args for args in reached)
    entry.write_text(held)

    # A repo a worker puts inside that worktree makes it the primary, and no run kept
    # that folder: each reads what is local, and calls nothing.
    inside = tree / ".x"
    _git(tmp_path, "clone", "-q", "--bare", str(origin), str(inside))
    _git(inside, "remote", "set-url", "origin", str(elsewhere))
    _git(inside, "update-ref", "refs/remotes/origin/main", "main")
    _git(inside, "update-ref", "refs/heads/0001-todo", "v0.1.0^{commit}")
    (tree / ".minions" / "runs").mkdir(parents=True)
    (tree / ".minions" / "runs" / "1.md").write_text(
        "10:00:00 · 0001-todo · finish — release · exit 0 · 1s\n"
    )

    def unkept() -> None:
        capsys.readouterr()
        codes = [
            _main(conduct, tree, *command, monkeypatch=monkeypatch)
            for command in _PUSH_COMMANDS
        ]
        said = capsys.readouterr().out
        assert not any(str(elsewhere) in args for args in reached)
        assert codes == [0, 1, 0]
        assert said.startswith("run · unread — ")
        assert "check: release · fail — v0.1.0 is not on origin\n" in said
        assert " · not pushed · " in said

    entry.write_text(f"{inside}\n")
    unkept()
    entry.write_text(held)

    link = (tree / ".git").read_text()
    (tree / ".git").write_text(f"gitdir: {inside}\n")
    unkept()
    (tree / ".git").unlink()
    inside.rename(tree / ".git")
    _git(tree, "config", "core.bare", "false")
    unkept()
    shutil.rmtree(tree / ".git")
    (tree / ".git").write_text(link)


@pytest.mark.slow
def test_the_kept_urls_stand_past_a_repoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, origin = _shipped_once(tmp_path, conduct, monkeypatch)
    elsewhere = _elsewhere(tmp_path)
    reached = _spied(conduct, monkeypatch)
    tree = _version(root, "0002-marks", "- [ ] 1 — Marks\n")

    _git(root, "remote", "set-url", "origin", str(elsewhere))
    conductor = conduct["Run"](root, "claude")
    assert conductor.pushes == [str(origin)]
    conductor.log.path.unlink()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 1
    kept = conduct["_kept_file"](root)
    assert kept.parent == Path.home() / ".mf-ship-origin"
    assert kept.stat().st_mode & 0o777 == 0o600
    kept.unlink()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
    assert not any(str(elsewhere) in args for args in reached)
    assert _main(conduct, tree, "status", monkeypatch=monkeypatch) == 1


@pytest.mark.slow
def test_a_refused_home_folder_still_pushes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    # Where the home folder refuses the file, a run still reads its own `origin`.
    root, _ = _with_origin(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    monkeypatch.setenv("HOME", str(tmp_path / "absent"))
    assert _run_claude(conduct, root, monkeypatch) == 0
    assert conduct["_kept_origin"](root) is None
    refusal = " · run · unkept — No such file or directory"
    assert sum(line.endswith(refusal) for line in _log(root)) == 1
    assert "refs/tags/v0.1.0" in _git(root, "ls-remote", "--tags", "origin")


def test_a_planted_promisor_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    # A worker plants a promisor and deletes a blob: git reads the blob from no URL,
    # and the key halts where any off-list key does.
    root = _primary(tmp_path)
    holder = tmp_path / "holder.git"
    _git(tmp_path, "clone", "-q", "--bare", str(root), str(holder))
    _git(root, "config", "remote.x.url", str(holder))
    _git(root, "config", "remote.x.promisor", "true")
    blob = _git(root, "rev-parse", "HEAD:AGENTS.md").strip()
    (root / ".git" / "objects" / blob[:2] / blob[2:]).unlink()
    assert conduct["_show"](root, "HEAD", "AGENTS.md") is None
    capsys.readouterr()
    assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 1
    assert "remote.x.promisor" in capsys.readouterr().out


def _with_origin(tmp_path: Path) -> tuple[Path, Path]:
    """Return a primary, its `origin` a bare repo holding its `main`, and that repo."""
    root = _primary(tmp_path)
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    return root, origin


def test_anchor_seeds_the_offline_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    monkeypatch.setenv("HOME", str(tmp_path / "operator-home"))
    (tmp_path / "operator-home").mkdir()
    root = _primary(tmp_path)

    def anchor(code: int, *args: str) -> str:
        capsys.readouterr()
        assert _main(conduct, root, "anchor", *args, monkeypatch=monkeypatch) == code
        return capsys.readouterr().out.strip()

    assert anchor(2) == "anchor: cannot run — origin/main is missing"
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    assert anchor(2) == "anchor: cannot run — origin/main is no release merge"
    _released(root, "v0.1.0")
    _git(root, "push", "-q", "origin", "main")
    tracked = _git(root, "rev-parse", "origin/main").strip()
    off = _git(root, "commit-tree", "-p", "main", "-m", "off", "main^{tree}").strip()
    _git(root, "update-ref", "refs/remotes/origin/main", off)
    assert anchor(2) == "anchor: cannot run — origin/main is not on main"
    _git(root, "update-ref", "refs/remotes/origin/main", tracked)

    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    (active / "pid").write_text(str(os.getpid()))
    (active / "start").write_text("Mon Nov  3 10:00:00 2026")
    assert anchor(2) == (
        "anchor: cannot run — a run is live: .minions/runs/active exists"
    )
    shutil.rmtree(active)

    # The person sees the sha and subject, and names the sha they checked.
    assert anchor(1) == (
        f"anchor: check {tracked} · Merge branch 'release-v0.1.0' against origin's"
        f" main, then run conduct.py anchor --yes {tracked}"
    )
    assert anchor(2, "--yes", off) == (
        f"anchor: cannot run — origin/main is {tracked}, not {off}"
    )
    assert conduct["_offline_base"](root) is None
    assert anchor(0, "--yes", tracked) == (
        f"anchor: {tracked} · Merge branch 'release-v0.1.0'"
    )
    assert conduct["_offline_base"](root) == tracked
    assert conduct["_pushed_file"](root).stat().st_mode & 0o777 == 0o600
    name = conduct["_pushed_file"](root).name
    assert anchor(2) == (
        f"anchor: cannot run — an offline base stands: ~/.mf-ship-origin/{name}"
    )


def _offline_retries(
    tmp_path: Path, conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Callable[..., list[str]]]:
    """Return a primary, its `origin`, and a run returning its log lines.

    The run tries `origin` with no wait between tries.
    """
    module = conduct["main"].__globals__
    monkeypatch.setitem(module, "RETRIES", (0, 0, 0))
    monkeypatch.setitem(module, "PUSH_RETRIES", (0, 0))
    root, origin = _with_origin(tmp_path)

    def run(code: int = 1) -> list[str]:
        assert _run_claude(conduct, root, monkeypatch) == code
        log = conduct["last_log"](root / ".minions" / "runs")
        return [line.split(" · ", 1)[1] for line in log.read_text().splitlines()[2:]]

    return root, origin, run


def _origin_down(
    tmp_path: Path, conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Callable[..., list[str]]]:
    """Return a primary, the path its `origin` moved to, and a run.

    The primary holds `0001-todo` and its dependent `0002-marks`.
    """
    root, origin, run = _offline_retries(tmp_path, conduct, monkeypatch)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    _version(root, "0002-marks", "- [ ] 1 — Marks\n", after="0001-todo")
    away = tmp_path / "origin.away"
    origin.rename(away)
    return root, away, run


def _waits(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith("run · push — waiting: ")]


def test_a_run_with_no_offline_base_halts_when_origin_is_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    _, _, run = _origin_down(tmp_path, conduct, monkeypatch)

    # No offline base: three tries, then the run halts before any worker.
    lines = run()
    assert lines[0].endswith(" · origin: unreachable — pushes wait")
    assert lines[1:4] == _waits(lines)
    assert lines[4:] == [
        "run · halt — conduct: halt — cannot read origin, and no offline base: a"
        " person runs conduct.py anchor",
        "run · halt — halted run · blocked none · released none",
    ]
    assert _calls(calls) == []


def test_a_commit_past_the_offline_base_halts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake()
    root, _, run = _origin_down(tmp_path, conduct, monkeypatch)

    # Past the offline base, a commit no release explains halts the run.
    conduct["_keep_base"](root, _git(root, "rev-parse", "main").strip())
    _commit(root, {"mine.txt": "x\n"}, "a person's commit")
    mine = _git(root, "rev-parse", "--short=7", "main").strip()
    assert run()[4] == (
        f"run · halt — conduct: halt — main holds {mine}, no run's release: a person"
        " reads it, then git push origin main"
    )
    assert _calls(calls) == []


@pytest.mark.slow
def test_a_run_goes_on_while_origin_is_down(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root, away, run = _origin_down(tmp_path, conduct, monkeypatch)
    conduct["_keep_base"](root, _git(root, "rev-parse", "main").strip())

    # A release made offline passes as released locally; its dependent merges it.
    held = _git(away, "rev-parse", "main")
    lines = run(0)
    assert _calls(calls) == [
        "probe",
        *(f"{station} 0001-todo" for station in ("build", "converge", "release")),
        *(f"{station} 0002-marks" for station in ("build", "converge", "release")),
    ]
    for change in ("0001-todo", "0002-marks"):
        assert f"{change} · check — release · pass" in lines
        assert not (root.parent / change).exists()
    assert lines[0].endswith(" · origin: unreachable — pushes wait")
    assert lines[1:4] == _waits(lines)[:3]
    for tag in ("v0.1.0", "v0.2.0"):
        assert f"run · push — waiting: {tag} released locally" in lines
    assert lines[-2:] == [
        _waits(lines)[-1],
        "run · done — released v0.1.0 v0.2.0 · unpushed main v0.1.0 v0.2.0",
    ]
    capsys.readouterr()
    assert _main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    report = capsys.readouterr().out.splitlines()
    said = [line.replace("push — waiting: ", "waited ") for line in _waits(lines)]
    assert report[: len(said)] == said
    assert report[len(said)].startswith("0001-todo · v0.1.0 · ")
    archived = "0002-marks:openspec/changes/archive/0001-todo"
    assert _git(root, "cat-file", "-t", archived) == "tree"
    assert _git(root, "tag", "--merged", "main").split() == ["v0.1.0", "v0.2.0"]
    assert _git(away, "rev-parse", "main") == held
    assert _git(away, "tag", "-l") == ""
    assert len(conduct["_ledger_heads"](root)) == 2


@pytest.mark.slow
def test_a_local_release_is_pushed_when_origin_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root, origin, run = _offline_retries(tmp_path, conduct, monkeypatch)
    held = _git(root, "rev-parse", "main").strip()
    conduct["_keep_base"](root, held)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    away = tmp_path / "origin.away"

    origin.rename(away)
    assert run(0)[-1] == "run · done — released v0.1.0 · unpushed main v0.1.0"
    away.rename(origin)

    # Origin's main moved meanwhile: the push is refused, and nothing lands.
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(origin), str(other))
    _commit(other, {"theirs.txt": "x\n"}, "origin moves")
    _git(other, "push", "-q", "origin", "main")
    _git(root, "fetch", "-q", "origin")
    assert run(1)[-2] == "run · halt — git push origin main failed, exit 1"
    assert _git(root, "ls-remote", "--tags", "origin") == ""
    assert conduct["_offline_base"](root) == _git(other, "rev-parse", "main").strip()
    _git(other, "push", "-q", "-f", "origin", f"{held}:refs/heads/main")

    assert run(0)[1:] == [
        "run · push — main",
        "run · push — v0.1.0",
        "run · done — nothing to ship",
    ]
    main = _git(root, "rev-parse", "main").strip()
    assert main in _git(root, "ls-remote", "origin", "refs/heads/main")
    assert "refs/tags/v0.1.0" in _git(root, "ls-remote", "--tags", "origin")
    assert conduct["_offline_base"](root) == main
    assert conduct["_ledger_heads"](root) == set()


@pytest.mark.slow
def test_a_push_that_lands_before_origin_flaps_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    module = conduct["main"].__globals__
    root, origin, run = _offline_retries(tmp_path, conduct, monkeypatch)
    away = tmp_path / "origin.away"
    _released(root, "v0.1.0")
    _git(root, "push", "-q", "origin", "main", "v0.1.0")
    conduct["_keep_base"](root, _git(root, "rev-parse", "main").strip())

    # Origin flaps: the release's push lands, and the check's read of the tag fails.
    _version(root, "0002-marks", "- [ ] 1 — Marks\n")
    left = module["Run"].push_left

    def flap(self: object, tries: tuple[int, ...]) -> bool:
        pushed: bool = left(self, tries)
        if tries == module["PUSH_RETRIES"]:
            origin.rename(away)
        return pushed

    monkeypatch.setattr(module["Run"], "push_left", flap)
    lines = run(0)
    assert "0002-marks · check — release · pass" in lines
    assert "run · push — waiting: v0.2.0 released locally" in lines
    assert lines[-1] == "run · done — released v0.2.0"
    assert "refs/tags/v0.2.0" in _git(away, "ls-remote", "--tags", str(away))


def test_the_remote_calls_carry_the_ssh_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "operator.gitconfig"))
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    monkeypatch.delenv("GIT_SSH", raising=False)
    root = _primary(tmp_path)
    folder = tmp_path / "ssh-bin"
    folder.mkdir()
    said = tmp_path / "ssh-calls.txt"
    ssh = folder / "ssh"
    ssh.write_text(f'#!/bin/sh\necho "$*" >> {shlex.quote(str(said))}\nexit 255\n')
    ssh.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)

    def reached() -> str:
        said.unlink(missing_ok=True)
        url = "ssh://example.invalid/r.git"
        assert conduct["_outside"](root, "ls-remote", "--", url).returncode != 0
        return said.read_text()

    assert "-o ConnectTimeout=15 -o BatchMode=yes" in reached()
    # Twin: the operator's own ssh command stands.
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -o Operator=yes")
    assert "Operator=yes" in reached()
    assert "BatchMode" not in reached()
    monkeypatch.delenv("GIT_SSH_COMMAND")
    _git(root, "config", "--global", "core.sshCommand", "ssh -o Global=yes")
    assert "Global=yes" in reached()
    assert "BatchMode" not in reached()
    # Twin: one a file the global config includes sets stands too.
    _git(root, "config", "--global", "--unset", "core.sshCommand")
    included = tmp_path / "included.gitconfig"
    included.write_text("[core]\n\tsshCommand = ssh -o Included=yes\n")
    _git(root, "config", "--global", "include.path", str(included))
    assert "Included=yes" in reached()
    assert "BatchMode" not in reached()


def test_the_plan_is_read_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("plant-network", "plant-executor")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    started: list[tuple[object, ...]] = []
    argv = conduct["argv"]

    def spy(*args: object) -> list[str]:
        started.append(args)
        return argv(*args)

    conduct["main"].__globals__["argv"] = spy

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "build 0001-todo", "converge 0001-todo"]
    assert any(
        line.endswith(
            " · 0001-todo · halt — conduct: halt — changes/0001-todo/models.toml"
            " changed during the run"
        )
        for line in _log(root)
    )

    # A request takes back no version whose models file left the run's plan: the plan
    # stays as read, and the halt stands. Why: 0063-rejoin design D2.
    conductor = conduct["Run"](root, "claude")
    conductor.take = lambda *args: None
    conductor.read_plan([conduct["find_version"](root, "0001-todo")])
    read = dict(conductor.plan)
    table = root / ".minions" / "changes" / "0001-todo" / "models.toml"
    table.write_text('[converge]\nexecutor = "codex"\n')
    changed = "conduct: halt — changes/0001-todo/models.toml changed during the run"
    conductor.halt("0001-todo", changed)
    request = root / ".minions" / "runs" / "rejoin" / "0001-todo"
    request.parent.mkdir(parents=True, exist_ok=True)
    request.touch()
    assert not conductor.take_requests({})
    last = conductor.log.path.read_text().splitlines()[-1]
    assert last.endswith(
        " · run · rejoin — 0001-todo: still halted — changes/0001-todo/models.toml"
        " changed during the run"
    )
    assert conductor.plan == read and conductor.stopped("0001-todo")

    # A rejoin of a planned version compares its models file and reads no plan again.
    # Why: 0071-ship-fixes design D4.
    again = conduct["Run"](root, "claude")
    again.take = lambda *args: None
    again.read_plan([conduct["find_version"](root, "0001-todo")])
    again.probed |= {"claude", "codex"}
    reads: list[object] = []
    again.read_plan = reads.append
    request.touch()
    assert again.take_requests({})
    assert reads == []
    assert (
        again.log.path.read_text()
        .splitlines()[-1]
        .endswith(" · run · rejoin — 0001-todo: release")
    )

    # A blocked version's poll that cannot list the versions skips, raising nothing.
    def unlisted(primary: Path) -> list[object]:
        raise conduct["Stop"](2, "conduct: cannot run — git failed")

    again.blocked.append("0002-none")
    listing = conduct["main"].__globals__["open_versions"]
    conduct["main"].__globals__["open_versions"] = unlisted
    again._unblock({})
    conduct["main"].__globals__["open_versions"] = listing
    assert (
        again.log.path.read_text()
        .splitlines()[-1]
        .endswith(" · run · rejoin — skipped — conduct: cannot run — git failed")
    )

    # A take-back that fails halts its version and raises nothing.
    version = conduct["find_version"](root, "0001-todo")
    for raised, said in (
        (conduct["Stop"](1, "conduct: halt — stopped"), "conduct: halt — stopped"),
        (ValueError("broken"), "conduct.py failed: broken"),
    ):

        def failing(*args: object, raised: Exception = raised) -> bool:
            raise raised

        again.take_back = failing
        assert not again.take_back_safely(version, {})
        assert again.halts[-1] == ("0001-todo", said)

    def domains(*args: object) -> list[str]:
        command = argv(*args)
        settings = json.loads(command[command.index("--settings") + 1])
        return settings["sandbox"]["network"]["allowedDomains"]

    monkeypatch.delenv("MF_SHIP_AGENT")
    assert "later.example" not in domains(*started[-1])
    assert "later.example" in domains(*started[-1][:6])

    fake()
    calls.unlink()
    agents = _WORKTREES + "- **Ship network:** `*.example`\n"
    _commit(root, {"AGENTS.md": agents}, "a wildcard")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == []
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert " · run · halt — conduct: halt — AGENTS.md: Ship network '*.example'" in log

    # A repo that still declares the removed line halts the run, any value.
    _commit(root, {"AGENTS.md": _WORKTREES + "- **Ship loopback:** yes\n"}, "loopback")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == []
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert (
        " · run · halt — conduct: halt — AGENTS.md: Ship loopback: was removed"
        " (change 0056-loopback-removal): delete the line"
    ) in log


def test_a_commit_during_a_run_halts_before_integrate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("person-commits")
    root = _primary(tmp_path)
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    pushed = _git(root, "rev-parse", "main")
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert "converge 0001-todo" in _calls(calls)
    assert "integrate 0001-todo" not in _calls(calls)
    commit = _git(root, "rev-parse", "main")[:7]
    said = (
        f" · 0001-todo · halt — conduct: halt — main holds {commit}, no run's release:"
        " a person reads it, then git push origin main"
    )
    assert any(line.endswith(said) for line in _log(root))
    assert pushed in _git(root, "ls-remote", "origin", "refs/heads/main")


def test_a_mixed_key_list_gets_no_lfs_remedy(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    _git(root, "config", "lfs.repositoryformatversion", "0")
    for key in ("core.sshCommand", "lfs.probe"):
        _git(root, "config", key, "planted")
        with pytest.raises(conduct["Stop"], match=key.lower()) as held:
            conduct["_refuse_config_commands"](root)
        assert str(held.value).endswith("move it to the global config or remove it")
        _git(root, "config", "--unset", key)
    # LFS's own key, naming a program LFS never wrote.
    _git(root, "config", "--unset", "lfs.repositoryformatversion")
    _git(root, "config", "filter.lfs.clean", "./planted.sh %f")
    with pytest.raises(conduct["Stop"], match="filter.lfs.clean") as held:
        conduct["_refuse_config_commands"](root)
    assert str(held.value).endswith("move it to the global config or remove it")


def test_no_hook_runs_in_a_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    root = _primary(tmp_path)
    marker = tmp_path / "hook-ran"
    tooling = tmp_path / "tooling"
    for folder in (root / ".git" / "hooks", tooling):
        folder.mkdir(exist_ok=True)
        hook = folder / "pre-commit"
        hook.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
        hook.chmod(0o755)
    monkeypatch.delenv("MF_SHIP_AGENT")
    size = len(conduct["HOOKS_OFF"])

    def commit(extra: dict[str, str]) -> None:
        subprocess.run(
            ["git", *_IDENTITY, "commit", "-q", "--allow-empty", "-m", "worker"],
            cwd=root,
            env={**os.environ, **extra},
            check=True,
        )

    def fires(extra: dict[str, str]) -> bool:
        marker.unlink(missing_ok=True)
        commit(extra)
        return marker.exists()

    repo = (root, root / ".git")
    for executor in conduct["EXECUTORS"]:
        command = conduct["argv"](executor, "Do it.", root, None, None, repo)
        assert command[:3] == ["env", "-u", "VIRTUAL_ENV"]
        pairs = dict(arg.split("=", 1) for arg in command[3 : size + 3])
        assert not fires(pairs)
        assert fires({})

    _git(root, "config", "core.hooksPath", str(tooling))
    conduct["_refuse_config_commands"](root)
    assert not fires(pairs)
    assert fires({})

    _git(root, "config", "lfs.repositoryformatversion", "0")
    with pytest.raises(conduct["Stop"], match="lfs.repositoryformatversion") as held:
        conduct["_refuse_config_commands"](root)
    assert "a run cannot upload LFS objects" in str(held.value)
    assert "remove it" not in str(held.value)
    _git(root, "config", "--unset", "lfs.repositoryformatversion")
    _git(root, "config", "filter.lfs.clean", "git-lfs clean -- %f")
    with pytest.raises(conduct["Stop"], match="filter.lfs.clean.*cannot upload LFS"):
        conduct["_refuse_config_commands"](root)


def test_stop_ends_a_live_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root = _primary(tmp_path)
    runs = root / ".minions" / "runs"
    active = runs / "active"
    runs.mkdir(parents=True)

    def stop() -> str:
        capsys.readouterr()
        assert _main(conduct, root, "stop", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip()

    assert stop() == "stop: none — no run is live"

    active.mkdir()
    (active / "start").write_text(_lstart(1))
    signalled: list[tuple[int, int]] = []
    with monkeypatch.context() as patch:
        # On a stop with no guard, -1 would reach every process the operator owns.
        patch.setattr(os, "kill", lambda pid, sig: signalled.append((pid, sig)))
        for pid in ("-1", "0", "1"):
            (active / "pid").write_text(pid)
            assert stop() == "stop: none — no run is live"
    assert signalled == []
    shutil.rmtree(active)

    log = runs / "20261101-120000.md"
    opening = (
        "# Ship run 20261101-120000\n\n"
        "10:00:00 · run · start — executor claude\n"
        "10:00:01 · 0001-todo · spawn — build · model default\n"
    )
    log.write_text(opening)
    sleep = shutil.which("sleep")
    assert sleep
    executor = tmp_path / "claude"
    executor.symlink_to(sleep)
    conductor = subprocess.Popen(["sleep", "60"], start_new_session=True)
    worker = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(worker.pid, str(executor), _GROUP_START)
    active.mkdir()
    (active / "pid").write_text(str(conductor.pid))
    (active / str(worker.pid)).write_text(_lstart(worker.pid))

    (active / "start").write_text("Thu Jan  1 00:00:00 1970\n")
    assert stop() == "stop: none — no run is live"
    assert (conductor.poll(), worker.poll()) == (None, None)
    assert (active / "pid").is_file()

    (active / "start").write_text(_lstart(conductor.pid))
    no_ps = _no_ps(tmp_path)
    with monkeypatch.context() as patch:
        patch.setenv("PATH", no_ps, prepend=os.pathsep)
        for command in (("status",), ("stop",), ("run", "--executor", "claude")):
            capsys.readouterr()
            assert _main(conduct, root, *command, monkeypatch=patch) == 2
            assert f"ps cannot read pid {conductor.pid}" in capsys.readouterr().out
    assert (conductor.poll(), worker.poll()) == (None, None)
    assert (active / "pid").is_file()

    ps_environments: list[dict[str, str]] = []
    run_ps = subprocess.run

    def read_ps(
        command: list[str],
        *,
        capture_output: bool,
        encoding: str,
        errors: str,
        timeout: float,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        observed = env if env is not None else os.environ
        ps_environments.append(
            {name: observed.get(name, "") for name in ("LC_ALL", "TZ")}
        )
        return run_ps(
            command,
            capture_output=capture_output,
            encoding=encoding,
            errors=errors,
            timeout=timeout,
            env=env,
        )

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "run", read_ps)
        patch.setenv("LC_ALL", "POSIX")
        patch.setenv("TZ", "Asia/Tokyo")
        (active / "start").write_text(conduct["_ps"](conductor.pid, "lstart="))
        patch.setenv("TZ", "America/New_York")
        assert conduct["_claim"](active) == "live"
        assert ps_environments == [{"LC_ALL": "C", "TZ": "UTC0"}] * 2

    (active / "start").write_text(_lstart(conductor.pid))
    assert stop() == f"stop: stopped · .minions/runs/{log.name}"

    assert conductor.wait(timeout=10) == -signal.SIGKILL
    assert worker.wait(timeout=10) == -signal.SIGKILL
    assert not active.exists()
    assert (
        log.read_text()
        .splitlines()[-1]
        .endswith(" · run · halt — stopped by the person")
    )
    verify = ("log", "--verify", str(log))
    assert _main(conduct, root, *verify, monkeypatch=monkeypatch) == 0

    log.write_text(log.read_text().replace("stopped by the person", "a crash"))
    assert _main(conduct, root, *verify, monkeypatch=monkeypatch) == 1

    with monkeypatch.context() as patch:
        patch.setenv("PATH", no_ps, prepend=os.pathsep)
        capsys.readouterr()
        run = ("run", "--executor", "claude")
        assert _main(conduct, root, *run, monkeypatch=patch) == 2
        assert "start time" in capsys.readouterr().out
    assert not active.exists()

    log.write_text(opening)
    conductor = subprocess.Popen(["sleep", "60"], start_new_session=True)
    foreign = subprocess.Popen(["sleep", "60"], start_new_session=True)
    _register(foreign.pid, "sleep", _GROUP_START)
    active.mkdir()
    (active / "pid").write_text(str(conductor.pid))
    (active / "start").write_text(_lstart(conductor.pid))
    (active / str(foreign.pid)).write_text(_lstart(foreign.pid))
    capsys.readouterr()
    assert _main(conduct, root, "stop", monkeypatch=monkeypatch) == 2
    said = capsys.readouterr().out
    assert conductor.wait(timeout=10) == -signal.SIGKILL
    assert foreign.poll() is None
    assert (active / "pid").is_file()
    assert (
        log.read_text()
        .splitlines()[-1]
        .endswith(" · run · halt — stopped by the person")
    )
    assert said.startswith("stop: ") and f"group {foreign.pid} " in said
    assert _main(conduct, root, *verify, monkeypatch=monkeypatch) == 0
    assert stop() == "stop: none — no run is live"
    foreign.kill()
    foreign.wait(timeout=10)


@pytest.mark.slow
def test_a_small_cap_is_granted_automatically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("cap-small")
    root = _primary(tmp_path)
    minions = root / ".minions"
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    head = _git(tree, "rev-parse", "HEAD")
    _done(root, "0001-todo", head)

    # The run reads each open blocking card's id and size; a missing file is none.
    blockers = conduct["_open_blockers"]
    assert blockers(minions, "0001-todo") is None
    _cards(root, "0001-todo", head, "a test")
    assert blockers(minions, "0001-todo") == [("R1", "one line"), ("S1", "a test")]
    security = minions / "changes" / "0001-todo" / "security.md"
    cards = security.read_text()
    unsized = cards.replace("high ·", "critical ·").replace(" · size: a test.", "")
    security.write_text(unsized)
    assert blockers(minions, "0001-todo")[1] == ("S1", "a design change")
    security.write_text(cards)
    # A Priority or a size wrapped in backticks, as stations write them, reads the same.
    review = minions / "changes" / "0001-todo" / "review.md"
    plain = review.read_text()
    quoted = plain.replace(
        "blocking · review · stability", "`blocking · review · stability`"
    )
    review.write_text(quoted.replace("size: one line.", "size: `one line`."))
    assert blockers(minions, "0001-todo") == [("R1", "one line"), ("S1", "a test")]
    # One that is no regular file is unread: a device or a FIFO could hang the run.
    review.unlink()
    review.symlink_to(os.devnull)
    assert blockers(minions, "0001-todo") is None
    review.unlink()
    review.write_bytes(b"\xff")
    assert blockers(minions, "0001-todo") is None
    review.write_text(plain)
    # A file with no card, as a station that found nothing writes it, holds none.
    security.write_text("---\nverdict: clean\n---\n\n## Refuted\n\n## Summary\n")
    assert blockers(minions, "0001-todo") == [("R1", "one line")]
    security.write_text(cards)

    def run() -> int:
        return _main(
            conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch
        )

    # A cap of small cards standing at the start gets its round in the run.
    assert run() == 0
    assert _calls(calls) == [
        "probe",
        "converge 0001-todo and grant=yes",
        "release 0001-todo",
    ]
    lines = _log(root)
    granted = " · run · grant — 0001-todo: automatic · R1 S1"
    assert any(line.endswith(granted) for line in lines)
    assert not (minions / "grants").exists()
    assert not any(" · halt — " in line for line in lines)

    # So does one reached inside the run, its halt cleared.
    calls.unlink()
    tree = _version(root, "0002-marks", "- [x] 1 — Marks\n")
    _done(root, "0002-marks", _git(tree, "rev-parse", "HEAD"))
    assert run() == 0
    assert _calls(calls) == [
        "probe",
        "converge 0002-marks",
        "converge 0002-marks and grant=yes",
        "release 0002-marks",
    ]
    lines = _log(root)
    assert any(
        line.endswith(" · run · grant — 0002-marks: automatic · R1 S1")
        for line in lines
    )
    assert lines[-1].endswith(" · run · done — released v0.2.0")
    assert not (minions / "grants").exists()
    # Each converge spawn in the run keeps its own log.
    stamp = sorted((minions / "runs").glob("*.md"))[-1].stem
    folder = minions / "changes" / "0002-marks" / "logs"
    logs = sorted(path.name for path in folder.glob(f"{stamp}-converge*.log"))
    assert logs == [f"{stamp}-converge-2.log", f"{stamp}-converge.log"]

    # The granted round is checked as a person's is: one with no `done` halts there.
    calls.unlink()
    fake("cap-small", "grant-unfinished")
    tree = _version(root, "0003-tags", "- [x] 1 — Tags\n")
    _done(root, "0003-tags", _git(tree, "rev-parse", "HEAD"))
    assert run() == 1
    assert _calls(calls) == [
        "probe",
        "converge 0003-tags",
        "converge 0003-tags and grant=yes",
    ]
    unfinished = " · 0003-tags · check — converge · fail — the status log has no done"
    assert any(line.endswith(unfinished) for line in _log(root))


def _replanned(root: Path, ids: str) -> list[str]:
    """Return the run log; 0001-todo's `re-plan` halt is the last before its rescue."""
    lines = _log(root)
    replan = f" · 0001-todo · halt — re-plan: {ids}"
    at = next(i for i, line in enumerate(lines) if line.endswith(replan))
    assert " · 0001-todo · spawn — rescue · " in lines[at + 1]
    return lines


def test_a_design_change_cap_halts_as_replan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("cap-design")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "converge 0001-todo", "rescue 0001-todo"]
    lines = _replanned(root, "R1 S1")
    assert not any(" · grant — " in line for line in lines)
    assert not (root / ".minions" / "grants").exists()


def test_an_auto_granted_round_that_blocks_halts_as_replan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("cap-again")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))

    def run() -> int:
        return _main(
            conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch
        )

    assert run() == 1

    assert _calls(calls) == [
        "probe",
        "converge 0001-todo",
        "converge 0001-todo and grant=yes",
        "rescue 0001-todo",
    ]
    lines = _replanned(root, "R1 S1")
    granted = [line for line in lines if " · run · grant — " in line]
    assert len(granted) == 1
    assert granted[0].endswith(" · run · grant — 0001-todo: automatic · R1 S1")

    # A later run grants no round past a granted round's cap: a re-plan, no worker.
    calls.unlink()
    assert run() == 1
    assert _calls(calls) == []
    lines = _log(root)
    assert not any(" · grant — " in line for line in lines)
    assert lines[-2].endswith(" · 0001-todo · halt — re-plan: R1 S1")


def test_auto_grant_false_grants_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("cap-small")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    head = _git(tree, "rev-parse", "HEAD")
    _done(root, "0001-todo", head)
    _cards(root, "0001-todo", head, "a test")
    minions = root / ".minions"
    table = minions / "changes" / "0001-todo" / "models.toml"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("[converge]\nauto_grant = false\n")

    # A cap of small cards standing at the start halts as a re-plan: no worker starts.
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )
    assert _calls(calls) == []
    lines = _log(root)
    assert lines[-2].endswith(" · 0001-todo · halt — re-plan: R1 S1")
    assert not any(" · grant — " in line for line in lines)

    # So does one the version's own pass meets, as beside a version that builds.
    conductor = conduct["Run"](root, "claude")
    version = conduct["find_version"](root, "0001-todo")
    conductor.read_plan([version])
    conductor.skips.add("0001-todo")
    conductor.advance(version, ())
    assert conductor.halts[-1] == ("0001-todo", "re-plan: R1 S1")
    conductor.log.path.unlink()

    # Twin: `true`, an absent key, another table and no file each allow it.
    auto = conduct["_auto_grants"]
    assert not auto(minions, "0001-todo")
    for text in ("[converge]\nauto_grant = true\n", "[converge]\n", "[build]\n"):
        table.write_text(text)
        assert auto(minions, "0001-todo")
    table.unlink()
    assert auto(minions, "0001-todo")


@pytest.mark.slow
def test_a_grant_buys_one_round(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake("grant-halts")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    version = conduct["find_version"](root, "0001-todo")
    grants = root / ".minions" / "grants" / "0001-todo"
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    runner = conduct["main"].__globals__["run"]
    started: list[tuple[Path, str, bool]] = []

    def spy(cwd: Path, executor: str, detach: bool) -> int:
        started.append((cwd, executor, detach))
        return 0

    conduct["main"].__globals__["run"] = spy

    def grant() -> tuple[int, str]:
        capsys.readouterr()
        args = ("grant", "0001-todo", "--executor", "claude")
        code = _main(conduct, root, *args, monkeypatch=monkeypatch)
        return code, capsys.readouterr().out.strip()

    refused = (
        "grant: cannot run — 0001-todo is at {}: run /mf-ship; grant once converge caps"
    )
    assert grant() == (2, refused.format("converge"))
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 2 · halt — a scope failure\n")
    assert grant() == (2, refused.format("converge-halted"))
    assert started == [] and not grants.exists()

    capped = "# t\n\n## Run 1 — d\n10:00:00 · round 3 · halt — cap reached\n"
    log.write_text(capped)
    assert conduct["stage_of"](root, version)[0] == "converge-halted"
    assert grant() == (0, "")
    assert started == [(root, "claude", True)]
    assert conduct["stage_of"](root, version) == ("converge", "granted")
    waiting = "grant: cannot run — 0001-todo has a grant waiting: run /mf-ship"
    assert grant() == (2, waiting)
    assert started == [(root, "claude", True)]

    conduct["main"].__globals__["run"] = runner

    def run() -> None:
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == 1
        )

    fake("grant-halts", "rescue-diagnose")
    run()
    assert "converge 0001-todo and grant=yes" in _calls(calls)
    assert not grants.exists()
    assert conduct["stage_of"](root, version)[0] == "converge-halted"
    assert _git(tree, "status", "--porcelain") == ""
    lines = _log(root)
    assert " · versions 0001-todo · grant 0001-todo" in lines[0]
    assert any(
        line.endswith(" · run · grant — 0001-todo: one more round past the cap")
        for line in lines
    )
    # The cap reached in the run gets its rescue in that run.
    assert _calls(calls)[-1] == "rescue 0001-todo"
    diagnosis = ".minions/changes/0001-todo/rescue.md"
    assert lines[-3].endswith(f" · run · rescue — 0001-todo: diagnosed · {diagnosis}")
    assert lines[-2].endswith(f" · 0001-todo · halt — rescue diagnosed — {diagnosis}")
    # The granted round's cap is the run's second, and no card is read: a re-plan.
    _replanned(root, "no open blocking card read")

    # A person's grant still buys a round on a re-plan halt.
    conduct["main"].__globals__["run"] = spy
    assert grant() == (0, "")
    conduct["main"].__globals__["run"] = runner
    calls.unlink()
    run()
    assert _calls(calls) == [
        "probe",
        "converge 0001-todo and grant=yes",
        "rescue 0001-todo",
    ]
    assert not grants.exists()

    # A rescue that answers the cap on disk, here by a grant, and asks to rejoin keeps
    # the halt for the run. Why: 0067-rescue design D3.
    calls.unlink()
    log.unlink()
    fake("grant-halts", "rescue-answers")
    run()
    assert _calls(calls) == ["probe", "converge 0001-todo", "rescue 0001-todo"]
    answered = "rescue answered its halt — converge: granted"
    lines = _log(root)
    assert any(line.endswith(f" · 0001-todo · halt — {answered}") for line in lines)
    assert any(
        line.endswith(f" · run · rejoin — 0001-todo: still halted — {answered}")
        for line in lines
    )
    grants.unlink()

    calls.unlink()
    # A grants folder a worker linked elsewhere lists nothing on the start line.
    elsewhere = tmp_path / "operator-files"
    elsewhere.mkdir()
    (elsewhere / "kept-urls").touch()
    grants.parent.rmdir()
    grants.parent.symlink_to(elsewhere)
    run()
    assert _calls(calls) == []
    assert " · grant " not in _log(root)[0]
    # A grant behind that link is none, and the run deletes nothing through it.
    (elsewhere / "0001-todo").touch()
    run()
    assert (elsewhere / "0001-todo").is_file()
    assert _calls(calls) == []
    # Nor does a converge that starts with the folder linked.
    log.unlink()
    run()
    assert (elsewhere / "0001-todo").is_file()
    assert _calls(calls) == ["probe", "converge 0001-todo", "rescue 0001-todo"]
    calls.unlink()
    grants.parent.unlink()
    grants.parent.mkdir()

    log.write_text(capped)
    active = root / ".minions" / "runs" / "active"
    active.mkdir()
    (active / "pid").write_text(str(os.getpid()))
    (active / "start").write_text(conduct["_ps"](os.getpid(), "lstart="))
    # While the live run's rescue of the version runs, a grant is refused and writes
    # nothing: one written then is the rescue's. Why: 0067-rescue design D3.
    runs = root / ".minions" / "runs"
    newest = conduct["last_log"](runs)
    with newest.open("a") as file:
        file.write("12:00:00 · 0001-todo · spawn — rescue · model default\n")
    rescuing = (
        "grant: cannot run — 0001-todo is at converge-halted with its rescue running:"
        " grant once it ends"
    )
    assert grant() == (2, rescuing)
    assert not grants.exists() and not (runs / "rejoin" / "0001-todo").exists()
    with newest.open("a") as file:
        file.write("12:00:09 · 0001-todo · finish — rescue · exit 0 · 9s\n")
    assert grant() == (0, "grant: recorded — the live run takes 0001-todo back")
    assert grants.is_file()
    assert (root / ".minions" / "runs" / "rejoin" / "0001-todo").is_file()
    assert started == [(root, "claude", True)] * 2
    assert _calls(calls) == []
    shutil.rmtree(active)


def test_a_fix_after_a_cap_halt_converges_afresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("amends")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    judged = _git(tree, "rev-parse", "HEAD")
    _findings(root, "0001-todo", judged, "blocking")
    log = root / ".minions" / "changes" / "0001-todo" / "status_log.md"
    capped = f"10:00:00 · round 3 · halt — cap reached · head {judged}"
    log.write_text(f"# t\n\n## Run 1 — d\n{capped}\n")
    grants = root / ".minions" / "grants" / "0001-todo"
    version = conduct["find_version"](root, "0001-todo")
    stage_of, check = conduct["stage_of"], conduct["check"]
    assert stage_of(root, version) == ("converge-halted", capped)
    assert check(root, "converge", version) == f"the status log halts: {capped}"

    _commit(tree, {"fix.txt": "fixed\n"}, "a person's fix")
    fixed = _git(tree, "rev-parse", "HEAD")
    # The lock case comes first, as in mf-converge's Resuming a run.
    # Why: 0063-rejoin design D4.
    locked = f"halt — waited 2 minutes for .minions/debt.lock · head {judged}"
    log.write_text(f"# t\n\n## Run 1 — d\n10:00:00 · round 3 · {locked}\n")
    lock = ("converge", "halted on the debt lock: resumes at Step 9")
    assert stage_of(root, version) == lock
    # Twin: a halt past the judged head is converge's own — a fix's, a catch-up's,
    # and a person's commit past it answers none (0063-rejoin design D4).
    for run, why in (("1 — d", "the verify fan-out"), ("2 — d · catch-up", "red")):
        own = f"10:00:00 · round 3 · halt — {why} · head {fixed}"
        log.write_text(f"# t\n\n## Run {run}\n{own}\n")
        assert stage_of(root, version) == ("converge-halted", own)
        assert check(root, "converge", version) == f"the status log halts: {own}"
        _commit(tree, {"later.txt": "later\n"}, "a person's commit past the halt")
        assert stage_of(root, version) == ("converge-halted", own)
        _git(tree, "reset", "-q", "--hard", fixed)
    log.write_text(f"# t\n\n## Run 1 — d\n{capped}\n")
    amended = ("converge", "amended: HEAD past the halted head")
    assert stage_of(root, version) == amended
    assert check(root, "converge", version) == "the status log has no done"
    # A rewritten history answers no halt: converge would halt it again.
    # Why: 0063-rejoin design D4.
    _git(tree, "reset", "-q", "--soft", "HEAD~2")
    _git(tree, "commit", "-q", "-m", "the cut and the fix, squashed")
    assert stage_of(root, version) == ("converge-halted", capped)
    assert check(root, "converge", version) == f"the status log halts: {capped}"
    _git(tree, "reset", "-q", "--hard", fixed)
    grants.parent.mkdir(parents=True)
    grants.touch()
    assert stage_of(root, version) == amended

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )

    assert _calls(calls) == ["probe", "converge 0001-todo", "release 0001-todo"]
    assert not grants.exists()
    assert log.read_text().startswith("# t\n\n## Run 2 — d · amended\n")
    assert _git(root, "tag", "-l") == "v0.1.0"

    # The person's amends answer a clean catch-up halt, a verify halt and an
    # `amend needed` halt; any other commit past the halt does not.
    # Why: 0071-ship-fixes design D5, D6.
    (tmp_path / "caught").mkdir()
    base = _primary(tmp_path / "caught")
    cut = _version(base, "0001-todo", "- [x] 1 — Todo\n")
    _done(base, "0001-todo", _git(cut, "rev-parse", "HEAD"))
    _findings(base, "0001-todo", _git(cut, "rev-parse", "HEAD"))
    _commit(base, {"README.md": "x\n"}, "main moves")
    message = "chore(integrate): merge main into 0001-todo"
    _git(cut, "merge", "-q", "--no-ff", "-m", message, "main")
    merged = _git(cut, "rev-parse", "HEAD")
    tasks = "openspec/changes/0001-todo/tasks.md"
    design = "openspec/changes/0001-todo/design.md"
    amend = "docs(0001-todo): amend the change directory"
    _commit(cut, {tasks: "## Progress\n\n- [x] 1 — Todo\n\nAmended.\n"}, amend)
    amended_head = _git(cut, "rev-parse", "HEAD")
    log = base / ".minions" / "changes" / "0001-todo" / "status_log.md"
    version = conduct["find_version"](base, "0001-todo")
    halts = {
        "2 — d · catch-up": "halt — red",
        "3 — d": "halt — verify: halt — 1.1",
        "4 — d": "halt — amend needed — R1",
    }
    for run, why in halts.items():
        halt = f"10:00:00 · round 1 · {why} · head {merged}"
        log.write_text(f"# t\n\n## Run {run}\n{halt}\n")
        assert stage_of(base, version) == amended
        for files, message in (
            ({"src.txt": "x\n"}, "a person's commit past the halt"),
            ({design: "x\n", "src.txt": "x\n"}, amend),
        ):
            _commit(cut, files, message)
            assert stage_of(base, version) == ("converge-halted", halt)
            _git(cut, "reset", "-q", "--hard", amended_head)
        _git(cut, "switch", "-q", "-c", "side", "HEAD~1")
        _commit(cut, {design: "side\n"}, amend)
        _git(cut, "switch", "-q", "0001-todo")
        _git(cut, "merge", "-q", "--no-ff", "-X", "theirs", "-m", amend, "side")
        assert stage_of(base, version) == ("converge-halted", halt)
        _git(cut, "reset", "-q", "--hard", amended_head)
        _git(cut, "branch", "-q", "-D", "side")
        _git(cut, "reset", "-q", "--soft", "HEAD~2")
        _git(cut, "commit", "-q", "-m", amend)
        assert stage_of(base, version) == ("converge-halted", halt)
        _git(cut, "reset", "-q", "--hard", amended_head)
    # A catch-up halt over a findings file no longer clean is converge's own.
    review = base / ".minions" / "changes" / "0001-todo" / "review.md"
    clean = review.read_text()
    review.write_text(clean.replace("verdict: clean", "verdict: blocking"))
    halt = f"10:00:00 · round 1 · halt — red · head {merged}"
    log.write_text(f"# t\n\n## Run 2 — d · catch-up\n{halt}\n")
    assert stage_of(base, version) == ("converge-halted", halt)
    review.write_text(clean)
    assert stage_of(base, version) == amended

    calls = fake("by-rule")
    calls.unlink()
    assert (
        _main(conduct, base, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )
    assert _calls(calls) == ["probe", "converge 0001-todo", "release 0001-todo"]
    assert f"- {amended_head} — the person's amend" in review.read_text()
    assert _git(base, "tag", "-l") == "v0.1.0"


def test_a_verify_halt_is_diagnosed_without_a_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("verify-halts")
    root = _primary(tmp_path)
    tree = _version(root, "0001-todo", "- [x] 1 — Todo\n")
    _done(root, "0001-todo", _git(tree, "rev-parse", "HEAD"))
    head = _git(tree, "rev-parse", "HEAD")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert _calls(calls) == ["probe", "converge 0001-todo"]
    name = ".minions/changes/0001-todo/rescue.md"
    halt = f"10:00:00 · round 1 · halt — verify: halt — 1.1 · head {head}"
    assert (root / name).read_text() == (
        f"# 0001-todo — rescue diagnosis\n\nhalt: {halt}\nsub-task: none\n"
        "cause: a Verify: changed since the cut\n"
        "proposal: commit docs(0001-todo): amend the change directory, then"
        " conduct.py rejoin 0001-todo, or /mf-ship with no run live\n"
    )
    lines = _log(root)
    assert any(
        line.endswith(f" · run · rescue — 0001-todo: diagnosed · {name}")
        for line in lines
    )
    assert any(
        line.endswith(f" · 0001-todo · halt — rescue diagnosed — {name}")
        for line in lines
    )

    # The run's diagnosis writes through no link, counts no rescue, and a skip skips it.
    version = conduct["find_version"](root, "0001-todo")
    outside = tmp_path / "outside.md"
    outside.write_text("the person's\n")
    (root / name).unlink()
    (root / name).symlink_to(outside)
    conductor = conduct["Run"](root, "claude")
    assert not conductor.rescue(version, "converge-halted", ())
    assert outside.read_text() == "the person's\n"
    assert conductor.halts[-1][1].startswith(f"rescue: cannot write {name} — ")
    assert conductor.rescues == {}
    (root / name).unlink()
    # A link at the change's folder holds no diagnosis either.
    folder = root / ".minions" / "changes" / "0001-todo"
    elsewhere = tmp_path / "elsewhere"
    folder.rename(elsewhere)
    folder.symlink_to(elsewhere)
    conductor = conduct["Run"](root, "claude")
    assert not conductor.rescue(version, "converge-halted", ())
    assert not (elsewhere / "rescue.md").exists()
    assert conductor.halts[-1][1].startswith(f"rescue: cannot write {name} — ")
    folder.unlink()
    elsewhere.rename(folder)
    conductor.skips.add("0001-todo")
    assert not conductor.rescue(version, "converge-halted", ())
    assert not (root / name).exists()

    # The person's amend answers it: the version converges afresh, as
    # test_a_fix_after_a_cap_halt_converges_afresh runs an answered halt to release.
    tasks = "openspec/changes/0001-todo/tasks.md"
    amend = "docs(0001-todo): amend the change directory"
    _commit(tree, {tasks: "## Progress\n\n- [x] 1 — Todo\n\nAmended.\n"}, amend)
    amended = ("converge", "amended: HEAD past the halted head")
    assert conduct["stage_of"](root, version) == amended


def test_a_missing_skill_stops_a_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root = _primary(tmp_path)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("MF_SHIP_AGENT")
    conduct["main"].__globals__["_executor_missing"] = lambda name: False
    names = sorted(path.name for path in (_REPO / "skills").glob("mf-*"))
    assert "mf-ship" in names
    for folder in conduct["SKILLS"].values():
        (home / folder).mkdir(parents=True)
        for name in names:
            (home / folder / name).symlink_to(_REPO / "skills" / name)

    (home / conduct["SKILLS"]["claude"] / "mf-ship").unlink()
    capsys.readouterr()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )
    assert capsys.readouterr().out.strip() == (
        "run: cannot run — mf-ship is not linked; make install-skills"
    )
    assert not (root / ".minions" / "runs").exists()

    conduct["_unlinked"]("codex")
    (home / conduct["SKILLS"]["codex"] / "mf-build").unlink()
    with pytest.raises(conduct["Stop"], match="mf-build is not linked"):
        conduct["_unlinked"]("codex")
    conductor = conduct["Run"](root, "claude")
    conductor.probe("codex")
    assert conductor.halts == [
        (
            "run",
            "probe-codex — run: cannot run — mf-build is not linked;"
            " make install-skills",
        )
    ]

    (home / conduct["SKILLS"]["claude"] / "mf-ship").symlink_to(
        _REPO / "skills/mf-ship"
    )
    other = tmp_path / "other" / "skills" / "mf-build"
    (home / conduct["SKILLS"]["codex"] / "mf-build").symlink_to(other)
    with pytest.raises(conduct["Stop"]) as stop:
        conduct["_unlinked"]("claude")
    assert str(stop.value) == (
        "run: cannot run — the mf-* links point into more than one tree:"
        " ~/.agents/skills/mf-build; make install-skills"
    )


def test_a_run_marks_itself_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    mark = Path.home() / ".mf-ship-origin" / "live" / conduct["_digest"](root)
    seen: list[str | None] = []

    def ship(self: object) -> int:
        seen.append(mark.read_text() if mark.is_file() else None)
        return 0

    conduct["Run"].ship = ship

    def run() -> None:
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == 0
        )

    run()
    assert seen == [f"{os.getpid()}\n"]
    assert not mark.exists()

    (root / "stray.txt").write_text("")
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )
    assert not mark.exists()
    (root / "stray.txt").unlink()

    claim = conduct["_claim"]
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    conduct["run"].__globals__["_claim"] = lambda path: "none"
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )
    assert not mark.exists()
    conduct["run"].__globals__["_claim"] = claim
    active.rmdir()

    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        mark.write_text(f"{other.pid}\n")
        run()
        assert seen[-1] == f"{other.pid}\n"
        assert mark.read_text() == f"{other.pid}\n"
    finally:
        other.kill()
        other.wait()

    shutil.rmtree(mark.parent.parent)
    mark.parent.parent.write_text("")
    run()
    assert seen[-1] is None


def test_the_last_run_moves_the_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    pin = runpy.run_path(str(_SCRIPT.with_name("pin.py")))
    root = _primary(tmp_path)
    mf = tmp_path / "mf"
    mf.mkdir()
    _git(mf, "init", "-q", "-b", "main")
    _commit(mf, {"skills/mf-build/SKILL.md": "1\n"}, "v1")
    _git(mf, "tag", "v0.1.0")
    _commit(mf, {"skills/mf-build/SKILL.md": "2\n"}, "v2")
    _git(mf, "tag", "v0.2.0")
    data = Path(os.environ["XDG_DATA_HOME"]) / "minionsfactory"
    links = [Path.home() / folder / "mf-build" for folder in conduct["SKILLS"].values()]
    assert pin["install"](mf, "v0.1.0") == "pin: linked v0.1.0"
    other = Path.home() / ".mf-ship-origin" / "live" / "other"
    other.parent.mkdir()
    other.write_text(f"{os.getpid()}\n")
    assert pin["install"](mf, "v0.2.0") == "pin: pending v0.2.0 — a run is live"

    def run() -> list[str]:
        capsys.readouterr()
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
            == 0
        )
        return capsys.readouterr().out.splitlines()

    assert run()[1:] == []
    assert _log(root)[0].endswith(" · versions none · mf v0.1.0 · pending v0.2.0")
    assert [os.readlink(link) for link in links] == [
        str(data / "v0.1.0" / "skills" / "mf-build")
    ] * 2

    other.unlink()
    assert run()[1:] == ["pin: moved to v0.2.0"]
    assert [os.readlink(link) for link in links] == [
        str(data / "v0.2.0" / "skills" / "mf-build")
    ] * 2
    assert not (Path.home() / ".mf-ship-origin" / "pending").exists()


def test_a_stale_claim_is_cleared(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)

    def status() -> list[str]:
        capsys.readouterr()
        assert _main(conduct, root, "status", monkeypatch=monkeypatch) == 0
        return capsys.readouterr().out.strip().splitlines()

    stale = ["run · stale — a run clears it, or stops naming why", "0001-todo · build"]
    assert status() == stale
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    (active / "pid").write_text(str(dead.pid))
    assert status() == stale

    (active / "pid").write_text(str(os.getpid()))
    (active / "start").write_text("Thu Jan  1 00:00:00 1970\n")
    assert status() == stale
    (active / "pid").write_text("9" * 30)
    assert status() == stale
    (active / "pid").write_text(str(os.getpid()))
    (active / "start").write_text(_lstart(os.getpid()))
    assert status() == ["run · live", "0001-todo · build"]
    capsys.readouterr()
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )
    assert "a run is live" in capsys.readouterr().out
    assert _calls(calls) == []

    (active / "pid").write_text(str(dead.pid))
    executor = tmp_path / "claude"
    sleep = shutil.which("sleep")
    assert sleep
    executor.symlink_to(sleep)
    group = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(group.pid, str(executor), _GROUP_START)
    (active / str(group.pid)).write_text(_lstart(group.pid))
    recycled = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(recycled.pid, str(executor), _GROUP_START)
    (active / str(recycled.pid)).write_text("Thu Jan  1 00:00:00 1970\n")
    unstamped = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(unstamped.pid, str(executor), _GROUP_START)
    (active / str(unstamped.pid)).touch()
    (active / "0").touch()
    (active / "7").mkdir()
    (active / "8").write_bytes(b"\xff")
    claims: list[str] = []
    ship = conduct["Run"].ship

    def spy(conductor: object) -> int:
        claims.append(conduct["_claim"](active))
        return ship(conductor)

    with monkeypatch.context() as patch:
        patch.setattr(conduct["Run"], "ship", spy)
        assert (
            _main(conduct, root, "run", "--executor", "claude", monkeypatch=patch) == 0
        )
    assert claims == ["live"]
    assert group.wait(timeout=10) == -signal.SIGKILL
    assert (recycled.poll(), unstamped.poll()) == (None, None)
    recycled.kill()
    unstamped.kill()
    assert "release 0001-todo" in _calls(calls)
    assert not active.exists()

    active.mkdir()
    (active / "pid").write_text(str(dead.pid))
    foreign = subprocess.Popen(["sleep", "60"], start_new_session=True)
    _register(foreign.pid, "sleep", _GROUP_START)
    (active / str(foreign.pid)).write_text(_lstart(foreign.pid))
    sibling = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(sibling.pid, str(executor), _GROUP_START)
    (active / str(sibling.pid)).write_text(_lstart(sibling.pid))
    with pytest.raises(conduct["Stop"], match=f"group {foreign.pid} .*no executor"):
        conduct["_clear"](active)
    assert sibling.wait(timeout=10) == -signal.SIGKILL
    assert foreign.poll() is None
    assert (active / str(foreign.pid)).is_file()
    capsys.readouterr()
    detach = ("run", "--executor", "claude", "--detach")
    assert _main(conduct, root, *detach, monkeypatch=monkeypatch) == 2
    assert f"group {foreign.pid} " in capsys.readouterr().out
    assert foreign.poll() is None
    assert (active / str(foreign.pid)).is_file()
    foreign.kill()
    foreign.wait(timeout=10)
    conduct["_clear"](active)
    assert not active.exists()

    active.mkdir()
    (active / "pid").write_text(str(dead.pid))
    refusing = subprocess.Popen([str(executor), "60"], start_new_session=True)
    _register(refusing.pid, str(executor), _GROUP_START)
    (active / str(refusing.pid)).write_text(_lstart(refusing.pid))
    held = (active / "pid", active / str(refusing.pid))

    def refuse(group: int, _: int) -> None:
        raise PermissionError(1, "not permitted", str(group))

    with monkeypatch.context() as patch:
        patch.setattr(os, "killpg", refuse)
        with pytest.raises(conduct["Stop"], match=f"group {refusing.pid} survives"):
            conduct["_clear"](active)
    assert all(path.exists() for path in held)
    with monkeypatch.context() as patch:
        patch.setenv("PATH", _no_ps(tmp_path), prepend=os.pathsep)
        with pytest.raises(conduct["Stop"], match=f"read pid {refusing.pid},"):
            conduct["_clear"](active)
    assert all(path.exists() for path in held)
    refusing.kill()
    for process in (recycled, unstamped, refusing):
        process.wait(timeout=10)


def test_a_usage_limit_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake("dies-limit")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 1
    )

    assert any(
        line.endswith(
            " · 0001-todo · halt — build worker exit 1 · stopped by a usage limit"
            " · resets 5:50pm (Europe/Athens)"
        )
        for line in _log(root)
    )


def test_run_refuses_without_worktrees_declared(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    calls = fake()
    root = _primary(tmp_path, agents="# agents\n")
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")

    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 2
    )

    assert capsys.readouterr().out.strip() == (
        "run: cannot run — AGENTS.md declares no **Worktrees:**"
    )
    assert _calls(calls) == []
    assert not (root / ".minions" / "runs").exists()


def test_a_claude_worker_starts_in_the_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    root = _primary(tmp_path, agents=_WORKTREES + "- **Ship network:** `ghcr.io`\n")
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    repo = (root, root / ".git")

    def settings() -> dict[str, Any]:
        command = conduct["argv"]("claude", "Do it.", root, None, None, repo)
        return json.loads(command[command.index("--settings") + 1])

    assert settings() == {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "allowWrite": [str(root), str(tree), str(root / ".git")],
                "denyRead": list(conduct["SECRETS"]),
            },
            "credentials": {
                "envVars": [
                    {"name": name, "mode": "deny"} for name in conduct["TOKENS"]
                ],
            },
            "network": {"allowedDomains": [*conduct["NETWORK"], "ghcr.io"]},
        }
    }
    # A plain-text store is a credential, and a registry that takes writes is a way out.
    assert "~/.git-credentials" in conduct["SECRETS"]
    assert "~/.codex/auth.json" in conduct["SECRETS"]
    assert "registry.npmjs.org" not in conduct["NETWORK"]
    assert {"name": "NPM_TOKEN", "mode": "deny"} in (
        settings()["sandbox"].get("credentials", {}).get("envVars", [])
    )
    # A project's settings and `.mcp.json` are worker-written, and run at a start.
    command = conduct["argv"]("claude", "Do it.", root, None, None, repo)
    assert command[command.index("--setting-sources") + 1] == "user"
    # No MCP server starts, the operator's own included.
    assert command.index("--strict-mcp-config") < command.index("--allowedTools")
    assert "--mcp-config" not in command

    # The conductor's uv environment is not the worker's `.venv`.
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "conductor-venv"))
    for executor in ("claude", "codex"):
        command = conduct["argv"](executor, "Do it.", root, None, None, repo)
        prefix = command[: command.index(executor)]
        shown = subprocess.run([*prefix, "env"], capture_output=True, text=True)
        assert "UV_CACHE_DIR=" in shown.stdout
        assert "VIRTUAL_ENV=" not in shown.stdout

    # No worker binds loopback, and a leftover line halts.
    assert "allowLocalBinding" not in settings()["sandbox"]["network"]
    (root / "AGENTS.md").write_text("- **Ship loopback:** yes — the gate serves\n")
    with pytest.raises(conduct["Stop"]) as stop:
        settings()
    assert stop.value.code == 1
    assert str(stop.value) == (
        "conduct: halt — AGENTS.md: Ship loopback: was removed"
        " (change 0056-loopback-removal): delete the line"
    )

    for value in ("*.example.com", "example.com/simple", "https://example.com"):
        (root / "AGENTS.md").write_text(f"- **Ship network:** `{value}`\n")
        with pytest.raises(conduct["Stop"]) as stop:
            settings()
        assert stop.value.code == 1
        assert value in str(stop.value)


def test_a_probe_halts_on_a_write_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    calls = fake("unsandboxed")
    root = _primary(tmp_path)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    marks = Path.home() / conduct["KEPT_ORIGINS"]

    def run() -> int:
        return _main(
            conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch
        )

    assert run() == 1
    assert _calls(calls) == ["probe"]
    assert any(
        line.endswith(
            " · run · halt — probe check fail — claude wrote outside its reach:"
            " it runs unsandboxed"
        )
        for line in _log(root)
    )
    assert not list(marks.glob("probe-*"))

    calls.unlink()
    fake("translated")
    assert run() == 1
    assert _calls(calls) == ["probe"]
    native = conduct["_native"]()
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert (
        " · run · halt — probe check fail — claude's shell runs as i386 on a"
        f" {native} host\n"
    ) in log

    # `.arch` is read before `probe.txt`, never through a link, named only as a shell.
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / ".gated").write_text("")
    arch = scratch / ".arch"
    arch.write_text("i386\n")
    assert (
        conduct["check_probe"](scratch, None)
        == f"the worker's shell runs as i386 on a {native} host"
    )
    unreadable = f"the worker's shell runs an unreadable .arch on a {native} host"
    arch.write_text("not an architecture\n")
    assert conduct["check_probe"](scratch, None) == unreadable
    arch.unlink()
    (scratch / "target").write_text("i386\n")
    arch.symlink_to(scratch / "target")
    assert conduct["check_probe"](scratch, None) == unreadable
    arch.unlink()
    arch.write_text("i386\n")
    os.link(arch, scratch / "twin")
    assert conduct["check_probe"](scratch, None) == unreadable

    # A Claude worker's `init` event lists every MCP server it started.
    calls.unlink()
    fake("mcp")
    assert run() == 1
    assert _calls(calls) == ["probe"]
    assert any(
        line.endswith(
            " · run · halt — probe check fail — claude started an MCP server:"
            " runpod, claude.ai Claude Docs"
        )
        for line in _log(root)
    )
    none = {"type": "system", "subtype": "init", "mcp_servers": []}
    other = {"type": "user", "mcp_servers": ["named in a tool result"]}
    planted = tmp_path / "init.log"
    cut = '{"mcp_servers": [cut\n{"type": "assistant"}\n'
    planted.write_text(cut + f"{json.dumps(other)}\n{json.dumps(none)}\n")
    assert conduct["mcp_started"]("claude", planted) is None

    # Twin: a sandbox refuses the write, the shell runs native, and the run ships.
    calls.unlink()
    fake()
    assert run() == 0
    assert _calls(calls) == [
        "probe",
        "build 0001-todo",
        "converge 0001-todo",
        "release 0001-todo",
    ]
    assert not list(marks.glob("probe-*"))


def test_a_worker_carries_the_allowlist_and_a_denial_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    rules = conduct["SHELL_RULES"]
    assert rules.endswith(
        "Give these rules, word for word, to every subagent you start."
    )
    root = _primary(tmp_path, agents=_WORKTREES + "- **Ship tools:** `npm`, `pnpm`\n")
    tree = _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    container = root.parent.resolve()
    argv = conduct["argv"]

    outside = tmp_path / "home"
    outside.mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    (sibling / ".git").write_text(f"gitdir: {tmp_path}/other/.git/worktrees/sibling\n")
    for branch, path in (("0002-forged", outside), ("0003-foreign", sibling)):
        _git(root, "branch", branch, "0001-todo")
        entry = root / ".git" / "worktrees" / branch
        entry.mkdir()
        (entry / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
        (entry / "commondir").write_text("../..\n")
        (entry / "gitdir").write_text(f"{path}/.git\n")
    listed = _git(root, "worktree", "list", "--porcelain")
    assert f"worktree {outside.resolve()}\n" in listed
    assert f"worktree {sibling.resolve()}\n" in listed
    assert conduct["reach"](root) == [root, tree]
    assert conduct["find_version"](root, "0002-forged").tree is None
    forged = root / ".git" / "worktrees" / "zz"
    forged.mkdir()
    (forged / "HEAD").write_text("ref: refs/heads/0002-forged\n")
    (forged / "commondir").write_text("../..\n")
    (forged / "gitdir").write_text(f"{tree}/.git\n")
    listed = _git(root, "worktree", "list", "--porcelain")
    assert listed.count(f"worktree {tree}\n") == 2
    assert conduct["find_version"](root, "0002-forged").tree is None
    assert conduct["find_version"](root, "0001-todo").tree == tree
    shutil.rmtree(forged)
    pointer = tree / ".git"
    absolute = pointer.read_text()
    pointer.write_text("gitdir: ../main/.git/worktrees/0001-todo\n")
    assert conduct["reach"](root) == [root, tree]
    pointer.write_text(absolute)
    assert conduct["reach"](tmp_path) == [tmp_path.resolve()]
    repo = (root, root / ".git")
    monkeypatch.delenv("MF_SHIP_AGENT")
    hooks_off = list(conduct["HOOKS_OFF"])
    cache = f"UV_CACHE_DIR={root / '.minions' / 'uv-cache'}"
    claude = argv("claude", "Do it.", root, "opus", "high", repo)
    unset = ["env", "-u", "VIRTUAL_ENV"]
    assert claude[: len(hooks_off) + 4] == [*unset, *hooks_off, cache]
    claude = claude[len(hooks_off) + 4 :]
    assert claude[:3] == ["claude", "-p", f"Do it.\n\n{rules}"]
    assert claude[3:7] == ["--model", "opus", "--effort", "high"]
    assert "--settings" in claude
    added = [claude[i + 1] for i, arg in enumerate(claude) if arg == "--add-dir"]
    assert added == [str(root), str(tree)]
    allowed = claude[
        claude.index("--allowedTools") + 1 : claude.index("--disallowedTools")
    ]
    assert {f"Edit(/{root}/**)", f"Edit(/{tree}/**)"} <= set(allowed)
    assert f"Edit(/{container}/**)" not in allowed
    assert allowed[-2:] == ["Bash(npm:*)", "Bash(pnpm:*)"]
    assert {"Skill", "Agent", "Bash(git:*)", "Bash(cp:*)", "Bash(rm:*)"} <= set(allowed)
    assert not any(rule.startswith(("Write(", "Bash(cd:")) for rule in allowed)
    denied = claude[claude.index("--disallowedTools") + 1 :]
    assert "Bash(git push --force:*)" in denied
    # The sandbox holds Bash; the Read tool answers to these rules alone.
    for secret in conduct["SECRETS"]:
        assert {f"Read({secret})", f"Read({secret}/**)"} <= set(denied)
    # The host's own words for a denied `Read`, as a real worker's log holds them.
    use = {"id": "t1", "type": "tool_use", "name": "Read"}
    said = "File is in a directory that is denied by your permission settings."
    result = {"type": "tool_result", "tool_use_id": "t1", "is_error": True}
    blocks = [
        {**use, "input": {"file_path": "~/.ssh/key"}},
        {**result, "content": f"<tool_use_error>{said}</tool_use_error>"},
    ]
    worker_log = tmp_path / "read.log"
    worker_log.write_text(json.dumps({"message": {"content": blocks}}) + "\n")
    assert conduct["denials"](worker_log) == ["Read(~/.ssh/key)"]

    def refused(command: str) -> bool:
        # Claude Code reads a trailing `:*` as ` *`, which also matches the bare prefix.
        for rule in denied:
            pattern = rule[5:-1]
            if pattern.endswith(":*"):
                pattern = pattern[:-2] + " *"
            bare = pattern.endswith(" *") and pattern.count("*") == 1
            if fnmatch.fnmatchcase(command, pattern) or (
                bare and command == pattern[:-2]
            ):
                return True
        return False

    for command in (
        "git push --force-with-lease origin main",
        "git push -fu origin main",
        "git clean -fdx",
        "git worktree remove -f /r/wt",
        "git -C /r worktree remove -f /r/wt",
        "git -C /r reset --hard HEAD~1",
        "git -C /r clean -fdx",
        "git -C /r clean -n -fdx",
        "git push origin main --force",
        "git push origin +main",
        "git -C /r push --force origin main",
        "git -C /r push origin main -f",
        "git -C /r push origin +main",
        "git -C /r push origin main --force-with-lease",
        "git -C /r branch -D 0001-todo",
        "git -C /r tag -d v0.1.0",
        "git -C /r worktree remove --force /r/wt",
    ):
        assert refused(command), command
    for command in (
        "git -C /r commit -m 'refactor: clean up the parser'",
        "git commit -q -m 'feat: read' -m 'a clean sibling counts' -m 'Change: 0045'",
        "git -C /r push origin main",
        "git -C /r push origin v0.1.0",
        "git -C /r merge --no-ff -m 'Merge branch 0001-todo' 0001-todo",
        "git -C /r worktree remove /r/wt",
        "git -C /r branch -d 0001-todo",
    ):
        assert not refused(command), command
    codex = argv("codex", "Do it.", root, None, None, repo)
    roots = json.dumps([str(root / ".git"), str(root), str(tree)])
    assert codex[: len(hooks_off) + 4] == [*unset, *hooks_off, cache]
    codex = codex[len(hooks_off) + 4 :]
    assert codex[0].startswith("PATH=/usr/bin:/bin:/usr/sbin:/sbin:")
    assert codex[1:5] == ["codex", "exec", "-s", "workspace-write"]
    assert "allow_login_shell=false" in codex
    assert f"sandbox_workspace_write.writable_roots={roots}" in codex
    assert "sandbox_workspace_write.network_access=false" in codex
    assert codex[-3:] == ["-C", str(root), f"Do it.\n\n{rules}"]
    # Twin: the drill's trusted plant, the same table trusted, loads the plant.
    table = ",".join(
        f'{json.dumps(str(path.resolve()))}={{trust_level="untrusted"}}'
        for path in (root, tree)
    )
    trust = f"projects={{{table}}}"
    assert sum(arg.startswith("projects") for arg in codex) == 1
    start = codex.index("sandbox_workspace_write.network_access=false") + 1
    assert codex[start:-3] == ["-c", trust]

    neighbour = tmp_path / "neighbour"
    neighbour.mkdir()
    _git(neighbour, "init", "-q", "-b", "main")
    _commit(neighbour, {"x.txt": "x\n"}, "base")
    spawned: list[list[str]] = []

    def worker(
        command: list[str], cwd: Path, out: Path | int, claim: Path | None
    ) -> tuple[int, bool]:
        spawned.append(command)
        with open(out, "w") as sink:
            sink.write("streamed\n")
        return 0, False

    started = conduct["main"].__globals__["work"]
    conduct["main"].__globals__["work"] = worker
    conductor = conduct["Run"](root, "codex")

    def next_roots() -> list[str]:
        models = ("codex", None, None)
        conductor.spawn("0001-todo", "build", tree, "Do it.", models)
        key = "sandbox_workspace_write.writable_roots="
        found = next(arg for arg in spawned[-1] if arg.startswith(key))
        return json.loads(found.removeprefix(key))

    pointer.write_text(f"gitdir: {neighbour}/.git\n")
    assert next_roots() == [str(root / ".git"), str(root)]
    pointer.write_text(absolute)
    inner = root / ".minions" / "inner"
    inner.mkdir()
    entry = root / ".git" / "worktrees" / "0004-inner"
    entry.mkdir()
    (entry / "HEAD").write_text("ref: refs/heads/0002-forged\n")
    (entry / "commondir").write_text("../..\n")
    (entry / "gitdir").write_text(f"{inner}/.git\n")
    (inner / ".git").write_text(f"gitdir: {entry}\n")
    assert conduct["reach"](root) == [root, tree]
    shutil.rmtree(entry)
    shutil.rmtree(inner)
    aside = root / ".git-aside"
    (root / ".git").rename(aside)
    (root / ".git").symlink_to(neighbour / ".git")
    with pytest.raises(conduct["Stop"]) as stop:
        conduct["preconditions"](root, "codex")
    assert "not the primary checkout" in str(stop.value)
    assert conduct["reach"](root) == [root]
    with pytest.raises(conduct["Stop"]) as stop:
        next_roots()
    assert "the primary's .git moved" in str(stop.value)
    (root / ".git").unlink()
    (root / ".git").write_text(f"gitdir: {neighbour}/.git\n")
    with pytest.raises(conduct["Stop"]):
        conduct["preconditions"](root, "codex")
    with pytest.raises(conduct["Stop"]) as stop:
        next_roots()
    assert "the primary's .git moved" in str(stop.value)
    (root / ".git").write_text("gitdir: nowhere\n")
    with pytest.raises(conduct["Stop"]) as stop:
        next_roots()
    assert "the primary's .git moved" in str(stop.value)
    planted = root / ".minions" / "planted"
    planted.mkdir()
    _git(planted, "init", "-q", "-b", "main")
    _git(planted, "config", "core.worktree", str(planted))
    (root / ".git").write_text(f"gitdir: {planted}/.git\n")
    with pytest.raises(conduct["Stop"]):
        conduct["preconditions"](root, "codex")
    (root / ".git").unlink()
    aside.rename(root / ".git")
    shutil.rmtree(planted)
    commondir = root / ".git" / "worktrees" / "0001-todo" / "commondir"
    kept = commondir.read_text()
    commondir.write_text(f"{neighbour}/.git\n")
    assert next_roots() == [str(root / ".git"), str(root), str(tree)]
    commondir.write_text(kept)
    # A worker that swaps a fresh log for a link before the spawn writes it gains
    # nothing: the conductor writes the file it made, never the link's target.
    target = tmp_path / "operator.rc"
    target.write_text("kept\n")
    made = conduct["_free_log"]

    def swapped(root: Path, parts: tuple[str, ...], name: str) -> object:
        found = made(root, parts, name)
        log = root.joinpath(*parts) / f"{name}.log"
        log.unlink()
        log.symlink_to(target)
        return found

    conduct["main"].__globals__["_free_log"] = swapped
    conductor.spawn("0009-swap", "build", tree, "Do it.", ("codex", None, None))
    conduct["main"].__globals__["_free_log"] = made
    assert target.read_text() == "kept\n"
    conduct["main"].__globals__["work"] = started
    conductor.log.path.unlink()

    assert conduct["PROMPTS"]["converge"].format(change="0001-todo", grant="") == (
        "Run the mf-converge skill for change 0001-todo."
    )
    models = root / ".minions" / "changes" / "0001-todo"
    models.mkdir(parents=True, exist_ok=True)
    (models / "models.toml").write_text('[converge]\ntier = "high"\n')

    work = conduct["work"]
    claim = tmp_path / "claim"
    claim.mkdir()
    sees_itself = (
        "import os, sys, time\n"
        "for _ in range(500):\n"
        "    held = os.listdir(sys.argv[1])\n"
        "    if held == [str(os.getpid())]:\n"
        "        if open(os.path.join(sys.argv[1], held[0])).read().strip():\n"
        "            sys.exit(0)\n"
        "    time.sleep(0.01)\n"
        "sys.exit(1)\n"
    )
    command = [sys.executable, "-c", sees_itself, str(claim)]
    assert work(command, tmp_path, tmp_path / "held.log", claim) == (0, False)
    assert list(claim.iterdir()) == []
    assert work([sys.executable, "-c", ""], tmp_path, tmp_path / "w.log", None) == (
        0,
        False,
    )

    calls = fake("deny", "heredoc")
    assert argv("claude", "Do it.", root, None, None, repo) == [
        sys.executable,
        "-S",
        str(_WORKER),
        f"Do it.\n\n{rules}",
    ]
    assert (
        _main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)
        == 0
    )
    assert "converge 0001-todo" in _calls(calls)
    lines = _log(root)
    assert any(
        line.endswith(" · 0001-todo · denied — build · Bash(rm -rf build)")
        for line in lines
    )
    log = conduct["last_log"](root / ".minions" / "runs")
    assert (
        _main(conduct, root, "log", "--verify", str(log), monkeypatch=monkeypatch) == 0
    )
    capsys.readouterr()
    _main(conduct, root, "report", monkeypatch=monkeypatch)
    assert (
        ' · denied Bash(rm -rf build), Bash(git commit -m "$(cat <<EOF build EOF )") · '
    ) in capsys.readouterr().out


def test_approve_gate_records_the_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "operator-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    root = _primary(tmp_path)
    _commit(root, {"Makefile": "gate:\n\techo a\n"}, "gate")
    change = "0002-gate"
    tree = _version(root, change, "- [ ] 1 — One\n")
    _commit(tree, {f"openspec/changes/{change}/design.md": "# X\n"}, "design")
    # make runs `$(shell)` as it reads: the worker's makefile is code it wrote.
    ran = tmp_path / "ran.log"
    gate = f"$(shell echo ran >> {ran})\n.IGNORE:\ngate:\n\techo a\n"
    _commit(tree, {"Makefile": gate}, "build")
    conduct = _conduct()
    base = _git(tree, "merge-base", "main", "HEAD")
    script = _REPO / "skills" / "mf-converge" / "scripts" / "gate_check.py"
    gate_check = [sys.executable, str(script), "--change", change]

    def check(*args: str) -> subprocess.CompletedProcess[str]:
        argv = [*gate_check, "--base", base, *args]
        return subprocess.run(argv, cwd=tree, capture_output=True, text=True)

    def approve(*args: str) -> tuple[int, str]:
        capsys.readouterr()
        code = _main(
            conduct, root, "approve-gate", change, *args, monkeypatch=monkeypatch
        )
        return code, capsys.readouterr().out

    # The check, run in the worker's sandbox, prints the hash in the halt it shows.
    hashed = check("--digest").stdout.strip()
    halt = check()
    assert halt.returncode == 1, halt.stdout
    assert "\n  added: Makefile: .IGNORE:\n" in halt.stdout
    assert halt.stdout.endswith(f"/mf-ship approve-gate {change} {hashed}.\n")

    assert approve("--yes", "not-a-hash")[0] == 1
    folder = home / ".mf-ship-origin" / f"{conduct['_digest'](root)}.gate"
    assert not folder.exists()
    ran.unlink()
    lapses = []
    code, out = approve("--yes", hashed)
    assert (code, out) == (0, f"approve-gate: approved — {hashed} · {change}\n")
    assert (folder / change).read_text() == f"{hashed}\n"
    assert (
        folder.stat().st_mode & 0o777,
        (folder / change).stat().st_mode & 0o777,
    ) == (
        0o700,
        0o600,
    )
    # Outside the sandbox, approve-gate runs none of the branch's makefiles.
    if ran.exists():
        lapses.append("approve-gate ran the branch's makefile")

    # The digest conduct.py names the folder by is the one gate_check.py reads.
    checked = check()
    assert checked.stdout.startswith(f"gate: approved — {hashed}\n"), checked.stdout

    # A phase's halt on its staged tree is approved by the hash that halt names.
    (tree / "Makefile").write_text(f"{gate}\techo b\n")
    _git(tree, "add", "Makefile")
    staged = _git(tree, "write-tree")
    hashed = check("--digest", "--head", staged).stdout.strip()
    code, out = approve("--yes", hashed)
    if code != 0:
        lapses.append(f"the staged tree's hash: {out.strip()}")
    checked = check("--head", staged)
    if not checked.stdout.startswith(f"gate: approved — {hashed}\n"):
        lapses.append(f"the staged check: {checked.stdout.splitlines()[0]}")
    assert not lapses, lapses
