"""The viewer: the projector's state tree, read from real repositories and run files.

Real git in scratch repositories with linked worktrees; no socket is opened.
Why: 0120-ui-state design, *Tests*.
"""

import json
import os
import runpy
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fake_worker import _commit, _git

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-ui" / "scripts" / "viewer.py"
_CONVERGE = _REPO / "skills" / "mf-converge" / "scripts" / "converge.py"
_WORKTREES = (
    "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
)
_START = "Mon Nov  3 10:00:00 2026"
_STAMP = "20261103-100000"
_CUT = {
    "bump": "minor",
    "brief": "b",
    "after": [],
    "executor": None,
    "model": None,
    "effort": None,
    "halt": None,
}


@pytest.fixture(autouse=True)
def _ps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a fake `ps` first on `PATH`: every pid started at `_START`."""
    folder = tmp_path / "ps-bin"
    folder.mkdir()
    fake = folder / "ps"
    fake.write_text(f"#!/bin/sh\necho '{_START}'\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)


def _primary(tmp_path: Path) -> Path:
    """Return a primary checkout on `main`, `.minions/` ignored."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _commit(root, {".gitignore": ".minions/\n", "AGENTS.md": _WORKTREES}, "base")
    return root.resolve()


def _version(
    root: Path, change: str, progress: str, after: str = "", base: str = ""
) -> Path:
    """Cut `change` on a branch of that name, linked, `progress` its tasks."""
    tree = root.parent / change
    _git(
        root,
        "worktree",
        "add",
        "-q",
        "-b",
        change,
        str(tree),
        *([base] if base else []),
    )
    folder = f"openspec/changes/{change}"
    line = f"after: [{after}]\n" if after else ""
    files = {
        f"{folder}/proposal.md": f"---\nbump: minor\n{line}---\n",
        f"{folder}/tasks.md": f"## Progress\n\n{progress}",
    }
    _commit(tree, files, f"cut {change}")
    return tree.resolve()


def _write(path: Path, text: str) -> None:
    """Write `text` at `path`, its folders made."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _run_log(root: Path, lines: list[str], stamp: str = _STAMP) -> Path:
    """Write a run log of `lines` and return it."""
    log = root / ".minions" / "runs" / f"{stamp}.md"
    _write(log, f"# Ship run {stamp}\n\n" + "".join(f"{line}\n" for line in lines))
    return log


def _live(root: Path) -> None:
    """Hold a live claim: this process's pid, started at `_START`."""
    active = root / ".minions" / "runs" / "active"
    _write(active / "pid", str(os.getpid()))
    _write(active / "start", _START)


def _halt(root: Path, change: str, tree: Path) -> None:
    """Write a `build.halt` that names the tree's `HEAD`."""
    head = _git(tree, "rev-parse", "HEAD")
    text = f"sub-task: 1.1\nstop: 3\nevidence: e\nhead: {head}\n"
    _write(root / ".minions" / "changes" / change / "build.halt", text)


def _queue(root: Path, entries: dict[str, str | None]) -> None:
    """Queue a cut for each id, its halt the value."""
    conduct = runpy.run_path(
        str(_REPO / "skills" / "mf-ship" / "scripts" / "conduct.py")
    )
    folder = (
        Path.home() / ".mf-ship-origin" / f"{conduct['_digest'](root)}.queue" / "cuts"
    )
    for name, halt in entries.items():
        _write(folder / name, json.dumps({**_CUT, "halt": halt}))


def _tree(
    root: Path, only: str | None = None, now: float | None = None
) -> dict[str, Any]:
    """Return what the projector prints for `root`, as JSON reads it."""
    shown = runpy.run_path(str(_SCRIPT))["project"](
        root, only, time.time() if now is None else now
    )
    return json.loads(shown)


def _by_id(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a project's versions by id."""
    return {each["id"]: each for each in tree["versions"]}


def test_read_part_reads_a_regular_file_only(tmp_path: Path) -> None:
    read_part = runpy.run_path(str(_SCRIPT))["read_part"]
    part = read_part.__globals__["PART"]
    plain = tmp_path / "plain"
    plain.write_text("hello")
    big = tmp_path / "big"
    big.write_text("a" * part + "b" * 10)
    os.mkfifo(tmp_path / "pipe")
    (tmp_path / "link").symlink_to(plain)
    assert read_part(plain) == "hello"
    assert read_part(big) == "a" * part
    assert read_part(big, tail=True) == "a" * (part - 10) + "b" * 10
    assert read_part(tmp_path / "pipe") is None
    assert read_part(tmp_path / "link") is None
    assert read_part(tmp_path / "missing") is None
    assert read_part(tmp_path) is None


def test_main_dispatches_its_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _primary(tmp_path)
    main = runpy.run_path(str(_SCRIPT))["main"]
    assert main(["project", str(root)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["name"] == "main"
    assert (shown["unread"], shown["for_you"], shown["versions"], shown["queue"]) == (
        None,
        [],
        [],
        [],
    )
    assert shown["run"] == {"claim": "none", "log": None, "last": None}
    for argv in ([], ["bogus"], ["project"], ["project", "a", "--only", "bogus"]):
        assert main(argv) == 2
    assert "usage: viewer.py project" in capsys.readouterr().err
    with pytest.raises(SystemExit, match="not in a git repository"):
        main(["project", str(tmp_path)])


def test_a_version_shows_its_phases_with_the_trees_ticks(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tasks = (
        "- [x] 1 — One · moderate\n- [ ] 2 — Two · hard\n- [ ] 3 — Three **HUMAN**\n"
    )
    sections = "\n## 2 — Two\n\n- [ ] 2.1 a\n- [ ] 2.2 b\n- [ ] 2.3 c\n"
    tree = _version(root, "0001-a", tasks + sections)
    _write(
        tree / "openspec/changes/0001-a/tasks.md",
        f"## Progress\n\n{tasks}\n## 2 — Two\n\n- [x] 2.1 a\n- [ ] 2.2 b\n"
        "- [x] 2.3 c\n",
    )
    phases = _by_id(_tree(root))["0001-a"]["phases"]
    assert phases == [
        {"number": "1", "title": "One", "rating": "moderate", "box": True}
        | {"done": 0, "total": 0},
        {"number": "2", "title": "Two", "rating": "hard", "box": False}
        | {"done": 2, "total": 3},
        {"number": "3", "title": "Three **HUMAN**", "rating": "hard", "box": False}
        | {"done": 0, "total": 0},
    ]
    (tree / "openspec/changes/0001-a/tasks.md").unlink()
    gone = _by_id(_tree(root))["0001-a"]["phases"]
    assert [(p["box"], p["done"], p["total"]) for p in gone] == [
        (True, None, None),
        (False, None, None),
        (False, None, None),
    ]


def test_workers_are_the_unfinished_spawns(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — One\n")
    _version(root, "0002-b", "- [ ] 1 — One\n")
    lines = [
        "10:00:00 · 0001-a · spawn — build · model claude-sonnet-5-5 · effort high",
        "10:05:00 · 0001-a · finish — build · exit 0 · 300s",
        "10:05:01 · 0001-a · spawn — converge.conformance · model gpt-6.1-sol"
        " · effort medium · executor codex",
        "10:05:02 · 0001-a · spawn — converge.adversarial · model claude-opus-5-5",
        "10:05:03 · 0001-a · spawn — rescue · model m",
        "10:06:00 · 0001-a · finish — rescue · exit 0 · 60s",
        "10:06:01 · 0002-b · spawn — converge · script",
        "10:06:02 · 0002-b · finish — supervise · exit 0 · 1s",
        "10:06:03 · run · spawn — probe-codex · model m",
        "23:59:59 · 0001-a · spawn — fix · model m · other part",
        "00:00:05 · 0001-a · spawn — fix2 · model m",
    ]
    _run_log(root, lines)
    shown = _by_id(_tree(root))
    day = datetime(2026, 11, 3)
    at = lambda *clock: day.replace(hour=clock[0], minute=clock[1], second=clock[2])  # noqa: E731
    assert shown["0001-a"]["workers"] == [
        {
            "station": "converge.conformance",
            "model": "gpt-6.1-sol",
            "effort": "medium",
            "executor": "codex",
            "started": at(10, 5, 1).timestamp(),
        },
        {
            "station": "converge.adversarial",
            "model": "claude-opus-5-5",
            "effort": None,
            "executor": None,
            "started": at(10, 5, 2).timestamp(),
        },
        {
            "station": "fix",
            "model": "m",
            "effort": None,
            "executor": None,
            "started": at(23, 59, 59).timestamp(),
        },
        {
            "station": "fix2",
            "model": "m",
            "effort": None,
            "executor": None,
            "started": at(0, 0, 5).timestamp() + 86400,
        },
    ]
    assert shown["0002-b"]["workers"] == [
        {"station": "converge", "model": None, "effort": None, "executor": None}
        | {"started": at(10, 6, 1).timestamp()}
    ]
    assert _tree(root)["run"]["last"] == lines[-1]
    assert shown["0001-a"]["state"] == "idle"
    _live(root)
    states = {each: shown["state"] for each, shown in _by_id(_tree(root)).items()}
    assert states == {"0001-a": "running", "0002-b": "running"}
    assert _tree(root)["run"]["claim"] == "live"


def test_the_projector_gives_each_state_its_why(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    one = "- [ ] 1 — One\n"
    _version(root, "0001-a", "- [ ] 1 — Hand **HUMAN**\n")
    halted = _version(root, "0002-b", one)
    _halt(root, "0002-b", halted)
    _version(root, "0003-c", one, after="0001-a")
    _version(root, "0004-d", one, after="0090-gone")
    _version(root, "0005-e", one)
    _version(root, "0006-f", one)
    stacked = _version(
        root, "0007-g", "- [x] 1 — Done\n", after="0004-d", base="0004-d"
    )
    _write(
        root / ".minions/changes/0007-g/stacked-on", _git(root, "rev-parse", "0004-d")
    )
    _write(
        root / ".minions/changes/0007-g/build.done",
        f"head: {_git(stacked, 'rev-parse', 'HEAD')}\n",
    )
    _version(root, "0008-h", one)
    converged = _version(root, "0009-i", "- [x] 1 — Done\n")
    _write(
        root / ".minions/changes/0009-i/build.done",
        f"head: {_git(converged, 'rev-parse', 'HEAD')}\n",
    )
    _write(
        root / ".minions/changes/0009-i/status_log.md",
        "# 0009-i — converge status\n\n## Run 1 — 2026-11-03 10:00\n\n"
        "10:01:00 · round 1 · halt — plan check failed\n",
    )
    _run_log(
        root,
        [
            "10:00:00 · 0005-e · spawn — build · model m",
            "10:00:01 · 0008-h · spawn — rescue · model m",
            "10:00:02 · 0008-h · finish — rescue · exit 0 · 1s",
            "10:00:03 · 0008-h · halt — rescue diagnosed"
            " — .minions/changes/0008-h/rescue.md",
        ],
    )
    _live(root)
    got = {
        each: (v["state"], v["stage"], v["why"])
        for each, v in _by_id(_tree(root)).items()
    }
    assert got == {
        "0001-a": ("needs you", "human", "phase 1 — Hand **HUMAN**"),
        "0002-b": ("halted", "build", "phase 1 unticked"),
        "0003-c": ("blocked", "waiting", "after 0001-a"),
        "0004-d": ("waiting", "waiting", "after 0090-gone"),
        "0005-e": ("running", "build", "phase 1 unticked"),
        "0006-f": ("idle", "build", "phase 1 unticked"),
        "0007-g": (
            "stacked",
            "stacked",
            f"built on 0004-d at {_git(root, 'rev-parse', '0004-d')[:7]}:"
            " waits for its release",
        ),
        "0008-h": ("halted", "build", "phase 1 unticked"),
        "0009-i": (
            "halted",
            "converge-halted",
            "10:01:00 · round 1 · halt — plan check failed",
        ),
    }


def test_a_version_that_raises_is_unread_alone(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "")
    _version(root, "0002-b", "- [ ] 1 — One\n")
    shown = _by_id(_tree(root))
    assert shown["0001-a"]["state"] == "unread"
    assert (
        shown["0001-a"]["unread"]
        == "conduct: halt — 0001-a: tasks.md has no ## Progress list"
    )
    assert shown["0001-a"]["stage"] is None
    assert shown["0001-a"]["phases"] == []
    assert shown["0002-b"]["state"] == "idle"
    assert shown["0002-b"]["unread"] is None


def test_converge_shows_its_round_cap_blockers_and_each_role(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    for change in ("0001-a", "0002-b", "0003-c"):
        _version(root, change, "- [x] 1 — One\n")
    folder = root / ".minions/changes/0001-a"
    _write(
        folder / "status_log.md",
        "# 0001-a — converge status\n\n## Run 2 — 2026-11-03 11:00 · amend\n\n"
        "11:05:00 · round 2 · fix — sent R1\n"
        "11:04:00 · round 2 · verdicts — adversarial changes-requested"
        " · open_blocking 1 · executor codex · model gpt-6.1-sol"
        " · effort medium · tokens unavailable"
        " · fallback: codex usage limit\n"
        "11:03:00 · round 2 · verdicts — conformance clean · open_blocking 0"
        " · executor claude · model default · effort high · tokens 1200\n\n"
        "## Run 1 — 2026-11-03 10:00\n\n"
        "10:30:00 · round 1 · verdicts — conformance changes-requested"
        " · open_blocking 2 · executor claude · model old · effort low · tokens 5\n",
    )
    _write(
        folder / "conformance.md",
        "---\nverdict: clean\nopen_blocking: 0\nround: 2\n---\n",
    )
    _write(
        folder / "adversarial.md",
        "---\nverdict: changes-requested\nopen_blocking: 1\nround: 1\n---\n",
    )
    _write(
        root / ".minions/changes/0002-b/status_log.md",
        "# 0002-b — converge status\n\n## Run 1 — 2026-11-03 10:00\n\n"
        "10:30:00 · round 1 · start — base a\n",
    )
    shown = _by_id(_tree(root))
    cap = runpy.run_path(str(_CONVERGE))["CAP"]
    assert shown["0001-a"]["converge"] == {
        "run": 2,
        "mark": "amend",
        "round": 2,
        "cap": cap,
        "fixing": True,
        "roles": {
            "conformance": {
                "verdict": "clean",
                "open_blocking": 0,
                "executor": "claude",
                "model": "default",
                "effort": "high",
                "tokens": 1200,
                "fallback": False,
            },
            "adversarial": {
                "verdict": "changes-requested",
                "open_blocking": 1,
                "executor": "codex",
                "model": "gpt-6.1-sol",
                "effort": "medium",
                "tokens": None,
                "fallback": True,
            },
        },
    }
    bare = {"verdict": None, "open_blocking": None} | dict.fromkeys(
        ("executor", "model", "effort", "tokens", "fallback")
    )
    assert shown["0002-b"]["converge"] == {
        "run": 1,
        "mark": None,
        "round": None,
        "cap": cap,
        "fixing": False,
        "roles": {"conformance": bare, "adversarial": bare},
    }
    assert shown["0003-c"]["converge"] is None


def test_liveness_is_active_then_quiet(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — One\n")
    _version(root, "0002-b", "- [ ] 1 — One\n")
    _run_log(root, ["10:00:00 · 0001-a · spawn — build · model m"])
    log = root / f".minions/changes/0001-a/logs/{_STAMP}-build-2.log"
    _write(log, '{"type":"system"}\n')
    now = time.time()
    levels = {
        age: _by_id(_tree(root, now=now + age))["0001-a"]["liveness"]["level"]
        for age in (0, 100, 400)
    }
    assert levels == {0: "active", 100: "recent", 400: "quiet"}
    assert _by_id(_tree(root))["0002-b"]["liveness"] is None
    _write(log, '{"timestamp":"garbage"}\n')
    assert _by_id(_tree(root))["0001-a"]["liveness"]["level"] == "active"
    _write(
        log,
        '{"timestamp":"2099-01-01T00:00:00+00:00"}\n{"timestamp":"2099-01-02T00:00:00Z"}\n',
    )
    last = datetime(2099, 1, 2, tzinfo=UTC).timestamp()
    assert _by_id(_tree(root))["0001-a"]["liveness"] == {
        "level": "active",
        "last": last,
    }


def test_for_you_holds_what_needs_a_person(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — Hand **HUMAN**\n")
    halted = _version(root, "0002-b", "- [ ] 1 — One\n")
    _halt(root, "0002-b", halted)
    _version(root, "0003-c", "- [ ] 1 — One\n")
    _queue(root, {"0003-c": None, "0010-cut": "the cut halted", "0011-cut": None})
    _write(root / ".minions/runs/active/pid", "garbage")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    _commit(root, {"ahead.txt": "x"}, "ahead")
    notes = [
        "10:00:00 · run · rescue — 0001-a: decided · amended tasks.md · abc1234",
        "10:00:01 · run · supervise — 0001-a: settled the note",
        "10:00:02 · run · rescue — 0001-a: diagnosed · .minions/0001-a/rescue.md",
        "10:00:03 · run · supervise — 0002-b: settled",
    ]
    limited = "10:00:04 · run · limited — codex limited until "
    _run_log(root, [*notes, limited + "2099-01-01 00:00"])
    shown = _tree(root)
    assert [(row["kind"], row["id"]) for row in shown["for_you"]] == [
        ("needs you", "0001-a"),
        ("halted", "0002-b"),
        ("cut halted", "0010-cut"),
        ("stale run", None),
        ("usage limit", None),
        ("unpushed", None),
    ]
    whys = {row["kind"]: row["why"] for row in shown["for_you"]}
    assert whys["needs you"] == "phase 1 — Hand **HUMAN**"
    assert whys["cut halted"] == "the cut halted"
    assert whys["stale run"] == "a run clears it, or stops naming why"
    assert whys["usage limit"] == "codex limited until 2099-01-01 00:00"
    assert whys["unpushed"] == "main is ahead of origin"
    assert shown["queue"] == [
        {"id": "0003-c", "state": "cut", "halt": None},
        {"id": "0010-cut", "state": "cut halted", "halt": "the cut halted"},
        {"id": "0011-cut", "state": "cut", "halt": None},
    ]
    assert sorted(_by_id(shown)) == ["0001-a", "0002-b"]
    assert _by_id(shown)["0001-a"]["notes"] == [
        {"text": f"rescue — {notes[0].split(' — ', 1)[1]}"},
        {"text": f"supervise — {notes[1].split(' — ', 1)[1]}"},
    ]
    assert "usage limit" not in _kinds(root, "2000-01-01 00:00")
    assert "usage limit" in _kinds(root, "a reset it did not name")


def _kinds(root: Path, until: str) -> list[str]:
    """Return the `for_you` kinds of a project whose run log's limit ends `until`."""
    _run_log(root, [f"10:00:04 · run · limited — codex limited until {until}"])
    return [row["kind"] for row in _tree(root)["for_you"]]


def test_the_only_options_print_liveness_and_the_fingerprint(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — One\n")
    _version(root, "0002-b", "- [ ] 1 — One\n")
    log = _run_log(root, ["10:00:00 · 0001-a · spawn — build · model m"])
    main = runpy.run_path(str(_SCRIPT))["main"]
    assert main(["project", str(root), "--only", "liveness"]) == 0
    lively = json.loads(capsys.readouterr().out)
    assert list(lively) == ["0001-a"]
    assert lively["0001-a"]["level"] == "active"
    assert main(["project", str(root), "--only", "fingerprint"]) == 0
    first = json.loads(capsys.readouterr().out)["fingerprint"]
    assert main(["project", str(root), "--only", "fingerprint"]) == 0
    assert json.loads(capsys.readouterr().out)["fingerprint"] == first
    with log.open("a") as file:
        file.write("10:00:01 · 0001-a · finish — build · exit 0 · 1s\n")
    assert main(["project", str(root), "--only", "fingerprint"]) == 0
    assert json.loads(capsys.readouterr().out)["fingerprint"] != first


def _snapshot(top: Path) -> dict[str, tuple[int, int]]:
    """Return the mtime and size of every path under `top`."""
    found = {}
    for folder, names, files in os.walk(top):
        for name in (*names, *files):
            status = (Path(folder) / name).lstat()
            found[str(Path(folder, name))] = (status.st_mtime_ns, status.st_size)
    return found


def test_the_projector_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _primary(tmp_path)
    halted = _version(root, "0001-a", "- [ ] 1 — One\n")
    _halt(root, "0001-a", halted)
    _version(root, "0002-b", "- [x] 1 — One\n", after="0001-a")
    _queue(root, {"0010-cut": None})
    _run_log(root, ["10:00:00 · 0001-a · spawn — build · model m"])
    _live(root)
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    before = _snapshot(tmp_path)
    _tree(root)
    _tree(root, "liveness")
    _tree(root, "fingerprint")
    assert _snapshot(tmp_path) == before


def test_a_claim_ps_cannot_read_is_unread(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — One\n")
    _version(root, "0002-b", "- [ ] 1 — One\n")
    _run_log(root, ["10:00:00 · 0001-a · spawn — build · model m"])
    _live(root)
    fake = tmp_path / "ps-bin" / "ps"
    fake.write_text("#!/bin/sh\nexit 1\n")
    shown = _tree(root)
    assert shown["run"]["claim"] == "unread"
    assert {each: v["state"] for each, v in _by_id(shown).items()} == {
        "0001-a": "idle",
        "0002-b": "idle",
    }
    assert "stale run" not in [row["kind"] for row in shown["for_you"]]


def _viewer() -> dict[str, Any]:
    """Return the viewer's definitions, loaded by path."""
    return runpy.run_path(str(_SCRIPT))


def test_the_projects_come_from_the_record_and_the_config(tmp_path: Path) -> None:
    ns = _viewer()
    top = tmp_path.resolve()
    for name in ("a", "b", "c", "e"):
        (top / name / ".minions").mkdir(parents=True)
    (top / "d").mkdir()
    listed = [top / name for name in ("a", "b", "d")] + [Path(), top / "e", top / "a"]
    record = top / "repos"
    record.write_text("".join(f"{line}\n" if line.name else "\n" for line in listed))
    rows = [
        {"path": str(top / "c"), "name": "See"},
        {"path": str(top / "b"), "name": "Bee"},
        {"path": str(top / "a"), "hide": True},
        {"path": str(top / "missing")},
    ]
    found = ns["projects"](record, rows)
    assert [(each.path, each.name) for each in found] == [
        (top / "c", "See"),
        (top / "b", "Bee"),
        (top / "e", "e"),
    ]
    assert [each.name for each in ns["projects"](top / "none", rows)] == ["See", "Bee"]
    config = top / "ui.toml"
    assert ns["read_config"](config) == (8737, [])
    config.write_text('port = 9000\n[[container]]\npath = "x"\nname = "X"\n')
    assert ns["read_config"](config) == (9000, [{"path": "x", "name": "X"}])


def test_a_bad_config_exits_2_naming_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    read_config = _viewer()["read_config"]
    config = tmp_path / "ui.toml"
    bad = (
        b"[[[ nope",
        b"\xff\xfe",
        b'port = "x"',
        b"port = true",
        b"port = 0",
        b"port = 70000",
        b'[[container]]\nname = "x"\n',
        b"[[container]]\npath = 3\n",
        b'container = "x"',
    )
    for text in bad:
        config.write_bytes(text)
        with pytest.raises(SystemExit) as caught:
            read_config(config)
        assert caught.value.code == 2
        assert str(config) in capsys.readouterr().err


def test_a_project_read_past_its_bound_is_killed(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [ ] 1 — One\n")
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    os.mkfifo(active / "pid")
    began = time.monotonic()
    shown = _viewer()["read_project"](root, None, 1)
    assert time.monotonic() - began < 8
    assert (shown["name"], shown["unread"], shown["versions"]) == (
        "main",
        "read past 1 s",
        [],
    )


def test_a_child_that_fails_or_prints_no_state_shows_its_project_unread(
    tmp_path: Path,
) -> None:
    read_project = _viewer()["read_project"]
    assert "not in a git repository" in read_project(tmp_path, None)["unread"]
    script = tmp_path / "child.py"
    read_project.__globals__["SELF"] = script
    for body, reason in (
        ("raise SystemExit(3)", "exit 3"),
        ("print('nope')", "no state read"),
        ("print('[]')", "no state read"),
    ):
        script.write_text(f"{body}\n")
        assert read_project(tmp_path, None)["unread"] == reason
    script.write_text('print(\'{"name": "x"}\')\n')
    assert read_project(tmp_path, "fingerprint") == {"name": "x"}


def test_a_frame_numbers_the_whole_state() -> None:
    ns = _viewer()
    state = ns["State"]()
    assert state.latest() == (0, [])
    assert state.publish([]) is True
    assert state.publish([]) is False
    shown = [{"name": "a"}]
    assert state.publish(shown) is True
    assert state.latest() == (2, shown)
    assert state.wait(2, 0) is False
    assert state.wait(1, 0) is True
    assert ns["frame"](2, shown) == (
        'id: 2\nevent: state\ndata: {"seq":2,"projects":[{"name":"a"}]}\n\n'
    )


def test_the_routes_answer_and_refuse(tmp_path: Path) -> None:
    ns = _viewer()
    route = ns["route"]
    page = tmp_path / "index.html"
    page.write_text("<p>page</p>")
    route.__globals__["PAGE"] = page
    state = ns["State"]()
    shown = [{"name": "a"}]
    state.publish(shown)
    local = "127.0.0.1:8737"
    status, headers, body = route("/", local, 8737, state)
    assert (status, headers["Content-Type"], body) == (
        200,
        "text/html; charset=utf-8",
        "<p>page</p>",
    )
    assert headers["Content-Security-Policy"].startswith("default-src 'none'")
    status, headers, body = route("/state?x=1", "localhost:8737", 8737, state)
    assert (status, headers["Content-Type"]) == (200, "application/json")
    assert json.loads(body) == {"seq": 1, "projects": shown}
    assert "Content-Security-Policy" not in headers
    status, headers, body = route("/events", local, 8737, state)
    assert (status, headers["Content-Type"]) == (200, "text/event-stream")
    assert next(body) == ns["frame"](1, shown)
    assert route("/nope", local, 8737, state)[0] == 404
    for path in ("/", "/state", "/events", "/nope"):
        for host in (None, "evil.test:8737", "127.0.0.1:9", "127.0.0.1"):
            assert route(path, host, 8737, state)[0] == 403
        for host in (local, "127.0.0.1:9", None):
            answer = route(path, host, 8737, state)[1]
            for name in ("Cache-Control", "X-Content-Type-Options", "Referrer-Policy"):
                assert name in answer


def test_the_stream_sends_each_new_state_once() -> None:
    ns = _viewer()
    state = ns["State"]()
    state.publish([{"name": "a"}])
    frames = ns["stream"](state, keepalive=0)
    assert next(frames) == ns["frame"](1, [{"name": "a"}])
    assert next(frames) == ": keep-alive\n\n"
    assert state.publish([{"name": "a"}]) is False
    assert next(frames) == ": keep-alive\n\n"
    state.publish([{"name": "b"}])
    assert next(frames) == ns["frame"](2, [{"name": "b"}])
    assert next(frames) == ": keep-alive\n\n"


def test_a_tick_reads_on_a_change_and_on_time() -> None:
    ns = _viewer()
    mark, calls = {"now": "m1"}, []
    lively = {"level": "quiet", "last": 1.0}

    def read(path: Path, only: str | None) -> dict[str, Any]:
        calls.append(only)
        if only == "fingerprint":
            return {"fingerprint": mark["now"]} if mark["now"] else {"unread": "x"}
        if only == "liveness":
            return {"0001-a": lively}
        return {
            "name": path.name,
            "unread": None,
            "versions": [{"id": "0001-a", "liveness": None}],
        }

    entries = [ns["Entry"](Path("p1"), "One"), ns["Entry"](Path("p2"), "Two")]
    memory: dict[Path, list[Any]] = {}

    def run(now: float) -> list[dict[str, Any]]:
        calls.clear()
        shown = ns["tick"](now, entries, memory, read)
        assert [each["name"] for each in shown] == ["One", "Two"]
        return shown

    run(0)
    assert sorted(calls, key=str) == [None, None, "fingerprint", "fingerprint"]
    run(2)
    assert calls == ["fingerprint", "fingerprint"]
    shown = run(5)
    assert sorted(calls) == ["fingerprint", "fingerprint", "liveness", "liveness"]
    assert shown[0]["versions"][0]["liveness"] == lively
    run(6)
    assert calls == ["fingerprint", "fingerprint"]
    mark["now"] = "m2"
    shown = run(7)
    assert sorted(calls, key=str) == [None, None, "fingerprint", "fingerprint"]
    assert shown[0]["versions"][0]["liveness"] is None
    run(16)
    assert sorted(calls) == ["fingerprint", "fingerprint", "liveness", "liveness"]
    run(17)
    assert sorted(calls, key=str) == [None, None, "fingerprint", "fingerprint"]
    mark["now"] = ""
    run(18)
    assert sorted(calls, key=str) == [None, None, "fingerprint", "fingerprint"]


class _Child:
    """A started process: it stays alive, or has exited."""

    def __init__(self, pid: int, exits: bool) -> None:
        self.pid = pid
        self.exits = exits

    def wait(self, timeout: float) -> int:
        if self.exits:
            return 1
        raise subprocess.TimeoutExpired("viewer", timeout)


def _serving(pid: int) -> str:
    """Return the command line of a server at pid 4242 and of any pid at or below 1."""
    return "python viewer.py serve" if pid in (1, 4242) else "vim notes"


def test_start_finds_and_stop_removes_the_pid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ns = _viewer()
    folder = tmp_path / "state" / "minionsfactory"
    config = tmp_path / "ui.toml"
    config.write_text("port = 9123\n")
    spawned: list[tuple[list[str], Path]] = []
    killed: list[tuple[int, int]] = []

    def spawn(argv: list[str], log: Path) -> _Child:
        spawned.append((argv, log))
        return _Child(4242, False)

    assert ns["start"](folder, config, spawn, _serving, wait=0) == 0
    assert capsys.readouterr().out == "http://127.0.0.1:9123/\n"
    assert spawned == [([sys.executable, str(_SCRIPT), "serve"], folder / "viewer.log")]
    assert (folder / "viewer.pid").read_text() == "4242\n"
    assert (folder / "viewer.port").read_text() == "9123\n"
    assert folder.stat().st_mode & 0o777 == 0o700
    assert (folder / "viewer.pid").stat().st_mode & 0o777 == 0o600
    config.write_text("port = 9999\n")
    assert ns["start"](folder, config, spawn, _serving, wait=0) == 0
    assert capsys.readouterr().out == "http://127.0.0.1:9123/\n"
    assert len(spawned) == 1
    assert ns["stop"](folder, _serving, lambda pid, sig: killed.append((pid, sig))) == 0
    assert capsys.readouterr().out == "viewer: stopped\n"
    assert killed == [(4242, signal.SIGTERM)]
    assert not (folder / "viewer.pid").exists()
    assert not (folder / "viewer.port").exists()
    exited = ns["start"](folder, config, lambda *_: _Child(5, True), _serving, wait=0)
    assert exited == 1
    log = folder / "viewer.log"
    assert capsys.readouterr().out == f"viewer: the server exited — see {log}\n"
    assert not (folder / "viewer.pid").exists()
    out = tmp_path / "child.log"
    child = ns["spawn"]([sys.executable, "-c", "print('hi')"], out)
    assert child.wait(timeout=30) == 0
    assert out.read_text() == "hi\n"
    assert out.stat().st_mode & 0o777 == 0o600
    assert ns["run_ps"](os.getpid()) == _START


def test_stop_signals_only_the_servers_pid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stop = _viewer()["stop"]
    killed: list[tuple[int, int]] = []

    def kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))

    for held in ("7\n", "1\n", "abc\n", None):
        if held is not None:
            (tmp_path / "viewer.pid").write_text(held)
        assert stop(tmp_path, _serving, kill) == 0
        assert capsys.readouterr().out == "viewer: not running\n"
        assert killed == []
        assert not (tmp_path / "viewer.pid").exists()
    (tmp_path / "viewer.pid").write_text("4242\n")
    assert stop(tmp_path, _serving, kill) == 0
    assert capsys.readouterr().out == "viewer: stopped\n"
    assert killed == [(4242, signal.SIGTERM)]


def test_main_runs_serve_start_and_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ns = _viewer()
    main = ns["main"]
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    seen: dict[str, tuple[object, ...]] = {}

    def fake(name: str, code: int) -> Callable[..., int]:
        def run(*args: object) -> int:
            seen[name] = args
            return code

        return run

    main.__globals__.update(
        serve=fake("serve", 11), start=fake("start", 12), stop=fake("stop", 13)
    )
    assert [main(["serve"]), main(["start"]), main(["stop"])] == [11, 12, 13]
    config = tmp_path / "cfg" / "minionsfactory" / "ui.toml"
    folder = tmp_path / "state" / "minionsfactory"
    assert seen["serve"] == (config,)
    assert seen["start"] == (folder, config, ns["spawn"], ns["run_ps"])
    assert seen["stop"] == (folder, ns["run_ps"], os.kill)
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.delenv("XDG_STATE_HOME")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert ns["config_path"]() == tmp_path / "home/.config/minionsfactory/ui.toml"
    assert ns["state_folder"]() == tmp_path / "home/.local/state/minionsfactory"
    assert ns["recorded"]() == tmp_path / "home/.mf-ship-origin/repos"
