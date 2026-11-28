"""Pins of the viewer's reads of each state format, each on today's side.

A case reaches the viewer through `project`, `projects` or `read_part`, and a module
through its public functions; no worker starts. Why: 0161-viewer design, *The cases*.
"""

import json
import os
import runpy
import subprocess
import sys
import time
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from fake_worker import _commit, _git
from mflib import kept, layout, runlog, statefile, statuslog

_REPO = Path(__file__).resolve().parent.parent
_VIEWER = _REPO / "skills" / "mf-ui" / "scripts" / "viewer.py"
_CONDUCT = _REPO / "skills" / "mf-ship" / "scripts" / "conduct.py"
_CONVERGE = _REPO / "skills" / "mf-converge" / "scripts" / "converge.py"
_START = "Mon Nov  3 10:00:00 2026"
_STAMP = "20261103-100000"
_DAY = datetime(2026, 11, 3)
_PART = 262144
_WORKTREES = (
    "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
)
_CUT = {
    "bump": "minor",
    "brief": "b",
    "after": [],
    "executor": "claude",
    "model": None,
    "effort": None,
    "halt": None,
}
_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "print(names['project'](Path(sys.argv[2]), None, 0))\n"
)


@cache
def _loaded(path: Path) -> dict[str, Any]:
    """Return a script's definitions, run once for the process."""
    return runpy.run_path(str(path))


@pytest.fixture(autouse=True)
def _machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a fake `ps` first on `PATH` and restore `GIT_OPTIONAL_LOCKS` after.

    Every pid started at `_START`.
    """
    folder = tmp_path / "ps-bin"
    folder.mkdir()
    fake = folder / "ps"
    fake.write_text(f"#!/bin/sh\necho '{_START}'\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")


def _viewer() -> dict[str, Any]:
    """Return the viewer's definitions, its loads of the other scripts cached."""
    names = runpy.run_path(str(_VIEWER))
    cached = {_CONDUCT: _loaded(_CONDUCT), _CONVERGE: _loaded(_CONVERGE)}
    names["project"].__globals__["load"] = lambda path: cached[path]
    return names


def _primary(tmp_path: Path) -> Path:
    """Return a primary checkout on `main`, `.minions/` ignored."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _commit(root, {".gitignore": ".minions/\n", "AGENTS.md": _WORKTREES}, "base")
    return root.resolve()


def _version(root: Path, change: str, progress: str = "- [x] 1 — One\n") -> Path:
    """Cut `change` on a branch of that name, linked, `progress` its tasks."""
    tree = root.parent / change
    _git(root, "worktree", "add", "-q", "-b", change, str(tree))
    folder = f"openspec/changes/{change}"
    files = {
        f"{folder}/proposal.md": "---\nbump: minor\n---\n",
        f"{folder}/tasks.md": f"## Progress\n\n{progress}",
    }
    _commit(tree, files, f"cut {change}")
    return tree.resolve()


def _built(root: Path, change: str) -> Path:
    """Cut `change` with every box ticked and `build.done` at its head."""
    tree = _version(root, change)
    done = root / ".minions" / "changes" / change / "build.done"
    _write(done, f"head: {_git(tree, 'rev-parse', 'HEAD')}\n")
    return tree


def _write(path: Path, text: str | bytes) -> None:
    """Write `text` at `path`, its folders made."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text)


def _log(root: Path, lines: list[str], stamp: str = _STAMP) -> Path:
    """Write a run log of `lines` and return it."""
    path = root / ".minions" / "runs" / f"{stamp}.md"
    _write(path, f"# Ship run {stamp}\n\n" + "".join(f"{line}\n" for line in lines))
    return path


def _raw_log(root: Path, body: str | bytes, stamp: str = _STAMP) -> Path:
    """Write a run log of exactly `body` and return it."""
    path = root / ".minions" / "runs" / f"{stamp}.md"
    _write(path, body)
    return path


def _claim(root: Path, live: bool = True) -> None:
    """Hold a claim: this process's pid, started at `_START`, or a garbled one."""
    active = root / ".minions" / "runs" / "active"
    _write(active / "pid", str(os.getpid()) if live else "garbage")
    _write(active / "start", _START)


def _status(root: Path, change: str, text: str | bytes) -> Path:
    """Write the change's status log and return it."""
    path = root / ".minions" / "changes" / change / "status_log.md"
    _write(path, text)
    return path


def _findings(root: Path, change: str, role: str, text: str | bytes) -> Path:
    """Write a role's findings file of the change and return it."""
    path = root / ".minions" / "changes" / change / f"{role}.md"
    _write(path, text)
    return path


def _entry(root: Path, name: str, text: str) -> None:
    """Write a queue entry `name` holding `text`."""
    folder = Path.home() / ".mf-ship-origin" / f"{layout.digest(root)}.queue" / "cuts"
    _write(folder / name, text)


def _tree(root: Path, now: float | None = None) -> dict[str, Any]:
    """Return what the projector prints for `root`, as JSON reads it."""
    shown = _viewer()["project"](root, None, time.time() if now is None else now)
    return json.loads(shown)


def _by_id(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a project's versions by id."""
    return {each["id"]: each for each in tree["versions"]}


def _started(root: Path, lines: list[str], stamp: str = _STAMP) -> list[float]:
    """Return the epoch seconds of 0001-a's workers read from a log of `lines`."""
    _log(root, lines, stamp)
    return [each["started"] for each in _by_id(_tree(root))["0001-a"]["workers"]]


def _at(clock: str, days: int = 0, day: datetime = _DAY) -> float:
    """Return the epoch second of `clock` on `day`, `days` later."""
    hours, minutes, seconds = (int(part) for part in clock.split(":"))
    moment = day.replace(hour=hours, minute=minutes, second=seconds)
    return (moment + timedelta(days=days)).timestamp()


def _spawn(clock: str, station: str = "w") -> str:
    """Return a spawn line of version 0001-a at `clock`."""
    return f"{clock} · 0001-a · spawn — {station} · model m"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Return a primary with the version 0001-a, every box ticked."""
    primary = _primary(tmp_path)
    _version(primary, "0001-a")
    return primary


def test_read_lines_of_a_folder_leaves_no_descriptor_open(tmp_path: Path) -> None:
    before = len(os.listdir("/dev/fd"))
    for _ in range(40):
        assert list(statefile.lines(tmp_path, _PART)) == []
    assert len(os.listdir("/dev/fd")) == before


def test_a_bad_byte_ending_a_halt_reads_as_two_replacement_characters(
    root: Path,
) -> None:
    halt = "10:00:01 · 0001-a · halt — stopped ".encode() + b"\xff\xfe"
    _raw_log(root, b"# Ship run\n\n" + _spawn("10:00:00").encode() + b"\n" + halt)
    shown = _tree(root)
    assert shown["run"]["last"] == "10:00:01 · 0001-a · halt — stopped ��"
    assert _by_id(shown)["0001-a"]["state"] == "halted"
    _raw_log(root, b"# Ship run\n\n" + _spawn("10:00:00").encode() + b"\n" + halt[:-2])
    assert _tree(root)["run"]["last"].endswith("stopped ")


def test_a_line_of_the_bound_with_its_newline_then_a_halt(root: Path) -> None:
    halt = "10:00:02 · 0001-a · halt — stopped"
    long = "10:00:01 · 0001-a · check — " + "x" * (_PART - 28)
    assert len(long) == _PART
    _raw_log(root, f"{_spawn('10:00:00')}\n{long}\n{halt}\n")
    shown = _tree(root)
    assert shown["run"]["last"] == halt
    assert _by_id(shown)["0001-a"]["state"] == "halted"
    _raw_log(root, f"{_spawn('10:00:00')}\n{halt}\n{long}")
    assert _tree(root)["run"]["last"] == long


@pytest.mark.slow
def test_a_line_past_the_bound_is_cut_and_the_rest_dropped(root: Path) -> None:
    halt = "10:00:02 · 0001-a · halt — stopped"
    head = "10:00:01 · 0001-a · check — "
    for size in (300000, 524288):
        _raw_log(root, f"{head}{'x' * size}\n{halt}\n")
        assert _child(root, 60)["run"]["last"] == halt
    _raw_log(root, f"{halt}\n{head}{'x' * 300000}")
    last = _child(root, 60)["run"]["last"]
    assert last == (head + "x" * 300000)[:_PART]
    assert len(last) == _PART


def test_a_carriage_return_ends_no_line_the_viewer_keeps_but_a_pair_is_one_end(
    root: Path,
) -> None:
    _raw_log(root, f"{_spawn('10:00:00')}\r\n{_spawn('10:00:01', 'x')}\r\n")
    last = _tree(root)["run"]["last"]
    assert "\r" not in last
    assert last == _spawn("10:00:01", "x")
    _raw_log(root, f"{_spawn('10:00:00')}\r{_spawn('10:00:01', 'x')}\n")
    shown = _tree(root)
    assert shown["run"]["last"] == _spawn("10:00:01", "x")
    assert len(_by_id(shown)["0001-a"]["workers"]) == 2


def test_a_digit_that_is_not_ascii_reads_as_no_number(root: Path) -> None:
    folder = root / ".minions" / "changes" / "0001-a"
    _findings(root, "0001-a", "conformance", "---\nopen_blocking: ٣\nround: ٢\n---\n")
    _status(
        root,
        "0001-a",
        "## Run 1 — 2026-11-03 10:00\n\n"
        "10:01:00 · round 1 · verdicts — conformance clean · open_blocking 0"
        " · tokens ٣\n",
    )
    shown = _by_id(_tree(root))["0001-a"]["converge"]
    assert shown["round"] is None
    assert shown["roles"]["conformance"]["open_blocking"] is None
    assert shown["roles"]["conformance"]["tokens"] is None
    (folder / "conformance.md").write_text("---\nopen_blocking: 3\nround: 2\n---\n")
    text = (folder / "status_log.md").read_text().replace("٣", "3")
    (folder / "status_log.md").write_text(text)
    shown = _by_id(_tree(root))["0001-a"]["converge"]
    assert shown["round"] == 2
    assert shown["roles"]["conformance"]["open_blocking"] == 3
    assert shown["roles"]["conformance"]["tokens"] == 3


def test_the_newest_log_among_its_suffixes_is_the_one_read(root: Path) -> None:
    for stamp in (_STAMP, f"{_STAMP}-2", f"{_STAMP}-10"):
        _log(root, [_spawn("10:00:05")], stamp)
    shown = _tree(root)
    assert shown["run"]["log"] == f"{_STAMP}-10"
    assert _by_id(shown)["0001-a"]["workers"][0]["started"] == _at("10:00:05")
    _log(root, [_spawn("23:59:58")], "20271231-235959-3")
    started = _by_id(_tree(root))["0001-a"]["workers"][0]["started"]
    assert started == _at("23:59:58", day=datetime(2027, 12, 31))


def test_the_event_time_is_a_float_in_the_json_text(root: Path) -> None:
    _log(root, [_spawn("10:00:05")])
    shown = _viewer()["project"](root, None, 0.0)
    assert f'"started": {_at("10:00:05")}' in shown
    assert f'"started": {int(_at("10:00:05"))}.0' in shown


def test_a_gate_start_runs_until_another_line_of_the_version(root: Path) -> None:
    _version(root, "0002-b")
    _claim(root)
    start = "0001-a · check — gate · start"
    _log(root, [f"10:00:00 · {start}", "10:00:01 · 0002-b · check — gate · pass"])
    shown = _tree(root)
    assert _by_id(shown)["0001-a"]["gate_running"] is True
    assert shown["run"]["last"] == "10:00:01 · 0002-b · check — gate · pass"


def test_the_last_line_is_the_newest_event_of_any_name(root: Path) -> None:
    _log(root, ["10:00:00 · 0001-a · check — gate · pass", _spawn("10:00:01")])
    assert _tree(root)["run"]["last"] == _spawn("10:00:01")
    _claim(root)
    lines = [
        _spawn("10:00:00"),
        "10:00:01 · 0001-a · check — gate · pass",
        "10:00:02 · run · wait — x",
        _spawn("10:00:03"),
        "10:00:04 · 0001-a · push — x",
    ]
    _log(root, lines)
    assert _tree(root)["run"]["last"] == lines[-1]


def test_l6_between_two_events_a_step_back_is_a_day_on(root: Path) -> None:
    assert _started(root, [_spawn("10:00:30"), _spawn("10:00:10", "x")]) == [
        _at("10:00:30"),
        _at("10:00:10", 1),
    ]
    steady = ["10:00:30", "10:00:30", "10:00:59", "10:01:00"]
    assert _started(root, [_spawn(clock) for clock in steady]) == [
        _at(clock) for clock in steady
    ]
    hours = ["10:59:59", "11:00:00", "11:00:59"]
    assert _started(root, [_spawn(clock) for clock in hours]) == [
        _at(clock) for clock in hours
    ]


def test_l6_days_add_across_steps_back(root: Path) -> None:
    clocks = ["11:00:00", "10:00:00", "09:00:00", "23:59:59", "00:00:05"]
    got = _started(root, [_spawn(clock) for clock in clocks])
    days = (0, 1, 2, 2, 3)
    assert got == [_at(clock, day) for clock, day in zip(clocks, days, strict=True)]


def test_l6_the_first_event_is_on_the_stems_day(root: Path) -> None:
    assert _started(root, [_spawn("00:00:00"), _spawn("00:00:01")]) == [
        _at("00:00:00"),
        _at("00:00:01"),
    ]
    assert _started(root, [_spawn("09:00:00")]) == [_at("09:00:00")]
    late = "20261103-235900"
    assert _started(root, [_spawn("00:00:01")], late) == [_at("00:00:01", 1)]
    assert _started(root, [_spawn("20:59:00")], late) == [_at("20:59:00")]


def _child(root: Path, timeout: int) -> dict[str, Any]:
    """Return what a child process's `project(root)` prints, killed past `timeout`."""
    done = subprocess.run(
        [sys.executable, "-c", _CHILD, str(_VIEWER), str(root)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    shown: dict[str, Any] = json.loads(done.stdout)
    return shown


def test_runlog_events_split_by_every_line_break_of_a_text(tmp_path: Path) -> None:
    log = tmp_path / f"{_STAMP}.md"
    log.write_text(
        "10:00:00 · a · e — x\r\n10:00:01 · a · e — y tail\n"
        "junk\x0b10:00:02 · a · e — w\n",
        newline="",
    )
    assert [event.detail for event in runlog.events(log)] == ["x", "y", "w"]


def test_runlog_events_of_a_big_log_keep_every_event(tmp_path: Path) -> None:
    log = tmp_path / f"{_STAMP}.md"
    lines = [f"10:00:00 · a · e — {n:07d} {'z' * 40}" for n in range(8000)]
    log.write_text("\n".join(lines) + "\n")
    assert log.stat().st_size > 400_000
    found = runlog.events(log)
    assert len(found) == len(lines)
    assert found[0].line == lines[0]
    assert found[-1].line == lines[-1]


def test_runlog_events_of_a_log_it_may_not_read_are_none(tmp_path: Path) -> None:
    plain = tmp_path / "plain.md"
    plain.write_text("10:00:00 · a · e — x\n")
    (tmp_path / "link.md").symlink_to(plain)
    (tmp_path / "folder.md").mkdir()
    for name in ("link.md", "missing.md", "folder.md"):
        assert runlog.events(tmp_path / name) == []
    bad = tmp_path / "bad.md"
    bad.write_bytes("10:00:00 · a · e — ".encode() + b"\xff\xfe\n")
    assert runlog.events(bad)[0].detail == "��"


def test_runlog_newest_passes_over_what_is_no_log(tmp_path: Path) -> None:
    assert runlog.newest(tmp_path / "missing") is None
    assert runlog.newest(tmp_path) is None
    (tmp_path / "notes.md").write_text("x")
    assert runlog.newest(tmp_path) is None
    for name in (_STAMP, f"{_STAMP}-2", f"{_STAMP}-10", "20261102-235959-99"):
        (tmp_path / f"{name}.md").write_text("x")
    assert runlog.newest(tmp_path) == tmp_path / f"{_STAMP}-10.md"


def test_l1_a_name_that_is_no_date_is_listed(root: Path) -> None:
    runs = root / ".minions" / "runs"
    _log(root, [_spawn("10:00:00")])
    (runs / "20261399-250000.md").write_text("# Ship run\n")
    assert runlog.newest(runs) == runs / f"{_STAMP}.md"
    shown = _tree(root)
    assert (shown["run"]["log"], shown["run"]["last"]) == (_STAMP, _spawn("10:00:00"))


@pytest.mark.slow
def test_l2_a_log_that_is_a_link_a_folder_or_empty_is_still_the_newest(
    root: Path, tmp_path: Path
) -> None:
    runs = root / ".minions" / "runs"
    other = tmp_path / "elsewhere.md"
    other.write_text(f"{_spawn('10:00:00')}\n")
    idle = {"claim": "none", "log": _STAMP, "last": None}
    for make in (
        lambda path: path.symlink_to(other),
        lambda path: path.symlink_to(tmp_path / "nowhere.md"),
        lambda path: path.mkdir(),
        lambda path: path.write_text(""),
    ):
        path = runs / f"{_STAMP}.md"
        runs.mkdir(parents=True, exist_ok=True)
        make(path)
        shown = _tree(root)
        assert shown["run"] == idle
        assert _by_id(shown)["0001-a"]["workers"] == []
        assert _by_id(shown)["0001-a"]["state"] == "idle"
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()
    assert _tree(root)["run"]["log"] is None


@pytest.mark.slow
def test_l2_a_log_that_is_a_pipe_reads_as_empty_and_blocks_nothing(root: Path) -> None:
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    os.mkfifo(runs / f"{_STAMP}.md")
    shown = _child(root, 60)
    assert shown["run"] == {"claim": "none", "log": _STAMP, "last": None}
    assert _by_id(shown)["0001-a"]["workers"] == []


def test_a_log_over_the_bound_of_short_lines_is_read_whole(root: Path) -> None:
    filler = "10:00:01 · 0002-b · check — " + "f" * 60
    count = 2 * _PART // len(filler)
    _log(root, [_spawn("10:00:00"), *[filler] * count, "10:00:02 · 0002-b · check — z"])
    shown = _tree(root)
    assert shown["run"]["last"] == "10:00:02 · 0002-b · check — z"
    assert [w["started"] for w in _by_id(shown)["0001-a"]["workers"]] == [
        _at("10:00:00")
    ]


def test_l5_a_claim_that_is_no_folder_reads_unread_and_the_log_still_reads(
    root: Path, tmp_path: Path
) -> None:
    _log(root, [_spawn("10:00:00")])
    active = root / ".minions" / "runs" / "active"
    (tmp_path / "folder").mkdir()
    for make in (
        lambda: active.write_text("x"),
        lambda: active.symlink_to(tmp_path / "folder"),
    ):
        make()
        shown = _tree(root)
        assert shown["run"]["claim"] == "unread"
        assert shown["run"]["last"] == _spawn("10:00:00")
        active.unlink()


@pytest.mark.slow
def test_l5_a_claim_that_is_a_pipe_reads_unread_and_blocks_nothing(root: Path) -> None:
    _log(root, [_spawn("10:00:00")])
    os.mkfifo(root / ".minions" / "runs" / "active")
    shown = _child(root, 60)
    assert shown["run"]["claim"] == "unread"
    assert shown["run"]["last"] == _spawn("10:00:00")


_HEAD2 = "## Run 2 — 2026-11-03 10:00 · amend"


def _converge(root: Path, text: str | bytes, change: str = "0001-a") -> dict[str, Any]:
    """Write the change's status log `text` and return what the board shows of it."""
    _status(root, change, text)
    shown: dict[str, Any] = _by_id(_tree(root))[change]["converge"]
    return shown


def _verdicts(role: str, rest: str, verdict: str = "clean") -> str:
    """Return a `verdicts` line of `role` whose spent fields are `rest`."""
    return (
        f"10:01:00 · round 1 · verdicts — {role} {verdict} · open_blocking 10 · {rest}"
    )


def test_the_spent_fields_come_from_the_text_after_open_blocking(root: Path) -> None:
    shown = _converge(root, f"{_HEAD2}\n\n{_verdicts('conformance', 'tokens 5')}\n")
    assert shown["roles"]["conformance"] == {
        "verdict": None,
        "open_blocking": None,
        "executor": None,
        "model": None,
        "effort": None,
        "tokens": 5,
        "fallback": False,
    }


def test_v6_the_words_of_a_fallback_before_verdicts_mark_none(root: Path) -> None:
    lines = [
        "10:02:00 · round 1 · fallback: codex failed · verdicts — adversarial clean"
        " · open_blocking 0 · executor codex · tokens 3",
        "10:01:00 · round 1 · verdicts — conformance executor · open_blocking 0"
        " · tokens 5",
    ]
    roles = _converge(root, f"{_HEAD2}\n\n" + "\n".join(lines) + "\n")["roles"]
    assert (roles["adversarial"]["fallback"], roles["adversarial"]["executor"]) == (
        None,
        None,
    )
    assert (roles["conformance"]["executor"], roles["conformance"]["tokens"]) == (
        None,
        5,
    )


def test_a_model_of_dots_and_dashes_reads_whole(root: Path) -> None:
    line = _verdicts("conformance", "executor codex · model gpt-6.1-sol-x · tokens 1")
    shown = _converge(root, f"{_HEAD2}\n\n{line}\n")
    assert shown["roles"]["conformance"]["model"] == "gpt-6.1-sol-x"


def test_s6_a_role_with_no_line_in_the_newest_run_shows_an_older_runs(
    root: Path,
) -> None:
    older = _verdicts("conformance", "executor claude · model old · tokens 5")
    text = (
        "## Run 3 — 2026-11-03 11:00\n\n11:01:00 · round 1 · start — x\n\n"
        f"## Run 1 — 2026-11-03 09:00\n\n{older}\n"
    )
    shown = _converge(root, text)
    assert (shown["run"], shown["roles"]["conformance"]["model"]) == (3, "old")


def test_s6_of_two_lines_of_a_role_the_first_in_the_file_wins(root: Path) -> None:
    first = _verdicts("conformance", "model first · tokens 1")
    second = _verdicts("conformance", "model second · tokens 2")
    shown = _converge(root, f"{_HEAD2}\n\n{first}\n{second}\n")
    assert shown["roles"]["conformance"]["model"] == "first"


def test_the_run_and_its_mark_come_from_the_first_heading_that_matches(
    root: Path,
) -> None:
    shown = _converge(
        root,
        "## Run 10 — 2026-11-03 11:00 · grant-x\n\n"
        "11:05:00 · round 1 · fix — sent R1\n",
    )
    assert (shown["run"], shown["mark"], shown["fixing"]) == (10, "grant-x", True)
    bare = _converge(root, "## Run 2 — 2026-11-03 10:00\n")
    assert (bare["run"], bare["mark"], bare["fixing"]) == (2, None, False)


def test_the_fixing_flag_asks_the_top_line_alone(root: Path) -> None:
    shown = _converge(root, f"{_HEAD2}\n\n11:05:00 · round 2 · fix — R1\n")
    assert shown["fixing"] is False
    no_run = _converge(root, "11:05:00 · round 1 · fix — sent R1\n")
    assert (no_run["run"], no_run["fixing"]) == (None, False)


def test_v4_a_halt_that_holds_the_words_is_not_fixing(root: Path) -> None:
    halt = "11:05:00 · round 2 · halt — the worker said · fix — sent"
    assert _converge(root, f"{_HEAD2}\n\n{halt}\n")["fixing"] is False
    sent = "11:04:00 · round 2 · fix — sent R1"
    assert _converge(root, f"{_HEAD2}\n\n{halt}\n{sent}\n")["fixing"] is False
    assert _converge(root, f"{_HEAD2}\n\n{sent}\n{halt}\n")["fixing"] is True


def test_v3_a_newest_heading_with_no_date_is_the_newest_run(
    root: Path,
) -> None:
    older = f"{_HEAD2}\n\n11:05:00 · round 2 · fix — sent R1\n"
    shown = _converge(root, f"## Run 3\n\n{older}")
    assert (shown["run"], shown["mark"], shown["fixing"]) == (3, None, False)
    shown = _converge(root, f"## Run 3 — 2026-11-03 11:00\n\n{older}")
    assert (shown["run"], shown["fixing"]) == (3, False)


def test_the_round_is_the_largest_of_the_two_findings_files(root: Path) -> None:
    _status(root, "0001-a", f"{_HEAD2}\n")
    _findings(root, "0001-a", "conformance", "---\nround: 0\n---\n")
    assert _by_id(_tree(root))["0001-a"]["converge"]["round"] == 0
    _findings(root, "0001-a", "adversarial", "---\nround: 2\n---\n")
    assert _by_id(_tree(root))["0001-a"]["converge"]["round"] == 2


def test_the_newest_run_is_the_first_heading_of_the_file(root: Path) -> None:
    text = (
        "## Run 3 — 2026-11-03 11:00 · catch-up\n\n"
        f"11:05:00 · round 3 · fix — sent R1\n\n{_HEAD2}\n"
    )
    shown = _converge(root, text)
    assert (shown["run"], shown["mark"], shown["fixing"]) == (3, "catch-up", True)


@pytest.mark.slow
def test_a_halt_names_its_cause_by_the_word_at_the_line_end(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    for change in ("0001-a", "0002-b", "0003-c", "0004-d"):
        _version(root, change)
    ends = ("· cause plan-text", "· cause other", "· cause not-listed")
    lines = [
        f"10:00:0{n} · 000{n + 1}-{'abc'[n]} · halt — build check fail — x {end}"
        for n, end in enumerate(ends)
    ]
    lines.append("10:00:03 · 0004-d · halt — worker said · cause gate-red and more")
    _log(root, lines)
    causes = {k: v["cause"] for k, v in _by_id(_tree(root)).items()}
    assert causes == {
        "0001-a": "plan-text",
        "0002-b": "other",
        "0003-c": "not-listed",
        "0004-d": None,
    }
    _log(root, ["10:00:00 · 0001-a · halt — worker said — cause gate-red"])
    assert _by_id(_tree(root))["0001-a"]["cause"] is None


def test_the_module_tells_a_heading_by_its_first_words() -> None:
    for line in ("## Run 2 — d", "## Running"):
        assert statuslog.is_heading(line)
    for line in ("## Notes", "##Run 1", "  ## Run 1"):
        assert not statuslog.is_heading(line)


def test_the_module_keeps_a_notes_heading_inside_a_run() -> None:
    text = "# t\n\n## Run 2 — d · amend\n\nline\n## Notes\nmore\n\n## Run 1 — d\nold\n"
    block = statuslog.newest(text)
    assert block is not None
    assert block.heading == "## Run 2 — d · amend"
    assert block.lines == ["line", "## Notes", "more"]
    assert statuslog.newest("# t\nline\n") is None


def test_the_module_reads_the_events_of_the_newest_run() -> None:
    text = (
        "## Run 2 — d · amend\n10:00:02 · round 2 · fix — R1\njunk\n"
        "10:00:01 · round 1 · start\n"
    )
    run = statuslog.latest(text)
    assert run.mark == "amend"
    assert run.events == [
        statuslog.Event(2, "fix", "R1"),
        statuslog.Event(1, "start", ""),
    ]
    assert statuslog.latest("no heading\n") == statuslog.Run(None, [])


def test_the_module_reads_an_event_in_the_specs_form_alone() -> None:
    for name in ("done2", "fix—x", "Fix — x"):
        assert statuslog.parse_event(f"10:00:00 · round 1 · {name}") is None
    assert statuslog.parse_event("10:00:00 · round 1 · fix — a\nb") is None
    assert statuslog.parse_event("10:00:00 · round 1 · fix —") == statuslog.Event(
        1, "fix", ""
    )
    assert statuslog.parse_event(" 10:00:00 · round 12 · fix — R1 ") == (
        statuslog.Event(12, "fix", "R1")
    )


def test_the_module_reads_the_mark_after_the_first_separator() -> None:
    older = "\n\n## Run 2 — d · amend\n"
    marks = {
        "## Run 3 — d · catch-up now": "catch-up now",
        "## Run 3 — d · catch-up ": "catch-up",
        "## Run 3 — d ": None,
        "## Run 3": None,
        "## Running": None,
        "## Run 3 — d · ": None,
        "## Run 3 — d · a · b": "a · b",
    }
    for heading, mark in marks.items():
        assert statuslog.latest(heading + older).mark == mark
    assert statuslog.latest("## Run 3 — d · catch-up\r\n\r\n## Run 2\r\n").mark == (
        "catch-up"
    )


_OLDER = (
    "## Run 2 — 2026-11-03 09:00 · amend\n\n"
    "09:01:00 · round 1 · verdicts — conformance clean · open_blocking 0"
    " · executor claude · model m · tokens 5\n"
)


def _heading_shows(root: Path, heading: str) -> tuple[Any, Any, Any]:
    """Return the run, mark and fixing the board shows for `heading` above `_OLDER`."""
    shown = _converge(root, f"{heading}\n\n{_OLDER}")
    return shown["run"], shown["mark"], shown["fixing"]


def test_s1_a_mark_of_several_words_is_the_newest_runs(root: Path) -> None:
    assert _heading_shows(root, "## Run 3 — 2026-11-03 10:00 · catch-up now") == (
        3,
        "catch-up now",
        False,
    )
    assert _heading_shows(root, "## Run 3 — 2026-11-03 10:00 · catch-up") == (
        3,
        "catch-up",
        False,
    )


def test_s2_a_trailing_space_is_the_newest_runs_heading(root: Path) -> None:
    assert _heading_shows(root, "## Run 3 — 2026-11-03 10:00 · catch-up ") == (
        3,
        "catch-up",
        False,
    )


def test_s5_a_missing_date_or_a_carriage_return_is_the_newest_runs_heading(
    root: Path,
) -> None:
    assert _heading_shows(root, "## Run 3") == (3, None, False)
    assert _heading_shows(root, "## Running") == (None, None, False)
    crlf = _converge(
        root, f"## Run 3 — 2026-11-03 10:00 · x\n\n{_OLDER}".replace("\n", "\r\n")
    )
    assert (crlf["run"], crlf["mark"], crlf["fixing"]) == (3, "x", False)
    assert crlf["roles"]["conformance"]["model"] == "m"
    assert crlf["roles"]["conformance"]["tokens"] == 5


def _remove(path: Path) -> None:
    """Remove a file, a link, a pipe or an empty folder at `path`."""
    if path.is_dir() and not path.is_symlink():
        path.rmdir()
    else:
        path.unlink()


@pytest.mark.slow
def test_s3_a_status_log_that_is_no_file_shows_its_version_unread(
    root: Path, tmp_path: Path
) -> None:
    _built(root, "0002-b")
    path = root / ".minions" / "changes" / "0002-b" / "status_log.md"
    other = tmp_path / "other.md"
    other.write_text(f"{_HEAD2}\n")
    words = "conduct: halt — .minions/changes/0002-b/status_log.md is a link"
    for make in (
        lambda: path.symlink_to(other),
        lambda: path.symlink_to(tmp_path / "nowhere.md"),
        path.mkdir,
    ):
        make()
        shown = _tree(root)
        version = _by_id(shown)["0002-b"]
        assert (version["state"], version["unread"]) == ("unread", words)
        assert version["converge"] is None
        assert shown["unread"] is None
        _remove(path)
    assert _by_id(_tree(root))["0001-a"]["unread"] is None


@pytest.mark.slow
def test_s3_a_status_log_that_is_a_pipe_shows_its_version_unread(root: Path) -> None:
    _built(root, "0002-b")
    folder = root / ".minions" / "changes" / "0002-b"
    os.mkfifo(folder / "status_log.md")
    shown = _child(root, 60)
    version = _by_id(shown)["0002-b"]
    assert version["state"] == "unread"
    assert version["unread"].endswith("0002-b/status_log.md is a link")
    assert version["converge"] is None
    assert shown["unread"] is None


@pytest.mark.slow
def test_s4_a_status_log_with_no_heading_reads_as_no_run(root: Path) -> None:
    _findings(root, "0001-a", "conformance", "---\nverdict: clean\nround: 2\n---\n")
    for text in (b"\xff\xfe", b"", "x" * _PART + f"\n{_HEAD2}\n"):
        shown = _converge(root, text)
        assert (shown["run"], shown["mark"], shown["fixing"]) == (None, None, False)
        assert shown["round"] == 2
        assert shown["roles"]["conformance"]["verdict"] == "clean"
    shown = _converge(root, f"{_HEAD2}\n" + "x" * _PART)
    assert (shown["run"], shown["mark"]) == (2, "amend")
    assert _by_id(_tree(root))["0001-a"]["unread"] is None


def test_a_missing_status_log_shows_no_converge_and_no_error(root: Path) -> None:
    version = _by_id(_tree(root))["0001-a"]
    assert (version["converge"], version["unread"]) == (None, None)


_GOOD = "---\nverdict: changes-requested\nopen_blocking: 1\nround: 2\n---\n"
_NONE = {"verdict": None, "open_blocking": None}


def _role(root: Path, role: str = "conformance") -> dict[str, Any]:
    """Return the board's fields of `role` of 0001-a, its round and its error."""
    version = _by_id(_tree(root))["0001-a"]
    assert version["unread"] is None
    shown = version["converge"]
    assert shown["round"] == 2
    return {key: shown["roles"][role][key] for key in _NONE}


@pytest.mark.slow
def test_s7_a_findings_file_that_cannot_be_read_shows_no_verdict_for_its_role(
    root: Path, tmp_path: Path
) -> None:
    _status(root, "0001-a", f"{_HEAD2}\n")
    _findings(root, "0001-a", "adversarial", _GOOD)
    path = root / ".minions" / "changes" / "0001-a" / "conformance.md"
    other = tmp_path / "other.md"
    other.write_text(_GOOD)
    path.symlink_to(other)
    assert _role(root) == _NONE
    path.unlink()
    path.symlink_to(tmp_path / "nowhere.md")
    assert _role(root) == _NONE
    path.unlink()
    path.mkdir()
    assert _role(root) == _NONE
    path.rmdir()
    assert _role(root) == _NONE
    for body in (b"", b"\xff\xfe", _GOOD.replace("\n", "\r\n"), "x" * _PART + _GOOD):
        _findings(root, "0001-a", "conformance", body)
        assert _role(root) == _NONE
    assert _role(root, "adversarial") == {"verdict": "changes-requested"} | {
        "open_blocking": 1
    }


@pytest.mark.slow
def test_s7_a_findings_file_that_is_a_pipe_blocks_nothing(root: Path) -> None:
    _status(root, "0001-a", f"{_HEAD2}\n")
    _findings(root, "0001-a", "adversarial", _GOOD)
    os.mkfifo(root / ".minions" / "changes" / "0001-a" / "conformance.md")
    version = _by_id(_child(root, 60))["0001-a"]
    assert version["unread"] is None
    assert version["converge"]["roles"]["conformance"]["verdict"] is None
    assert version["converge"]["round"] == 2


def test_s7_a_findings_file_then_past_the_bound_is_read(root: Path) -> None:
    _status(root, "0001-a", f"{_HEAD2}\n")
    _findings(root, "0001-a", "conformance", _GOOD + "x" * _PART)
    assert _role(root) == {"verdict": "changes-requested", "open_blocking": 1}


def test_s8_a_quoted_frontmatter_value_keeps_its_quotes_and_is_no_number(
    root: Path,
) -> None:
    _status(root, "0001-a", f"{_HEAD2}\n")
    quoted = '---\nverdict: "clean"\nopen_blocking: \'0\'\nround: "2"\n---\n'
    _findings(root, "0001-a", "conformance", quoted)
    shown = _by_id(_tree(root))["0001-a"]["converge"]
    assert shown["roles"]["conformance"]["verdict"] == '"clean"'
    assert shown["roles"]["conformance"]["open_blocking"] is None
    assert shown["round"] is None


_PROJECTS_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "found = names['projects'](Path(sys.argv[2]), [{'path': sys.argv[3]}])\n"
    "print(json.dumps([[str(each.path), each.name] for each in found]))\n"
)


def _site(top: Path, name: str, minions: bool = True) -> Path:
    """Make the folder `name` under `top`, `.minions` in it, and return it resolved."""
    folder = top / name
    (folder / ".minions" if minions else folder).mkdir(parents=True)
    return folder.resolve()


def _listed(record: Path | None, rows: list[dict[str, Any]] | None = None) -> list[Any]:
    """Return the `(path, name)` pairs `projects` lists for `record` and `rows`."""
    found = _viewer()["projects"](record, rows or [])
    return [(each.path, each.name) for each in found]


def _record(top: Path, text: str | bytes) -> Path:
    """Write the record `repos` of `text` under `top` and return it."""
    path = top / "repos"
    _write(path, text)
    return path


def test_p5_a_row_names_its_project_and_the_first_row_of_a_path_wins(
    tmp_path: Path, isolated_home: Path
) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    rows = [{"path": str(a), "name": "First"}, {"path": str(a), "name": "Second"}]
    assert _listed(top / "none", rows) == [(a, "First")]
    home = _site(isolated_home, "p")
    assert _listed(top / "none", [{"path": "~/p"}]) == [(home.resolve(), "p")]
    (top / "link").symlink_to(a)
    rows = [{"path": str(top / "link"), "name": "Row"}, {"path": f"{a}/../a"}]
    assert _listed(_record(top, f"{a}\n"), rows) == [(a, "Row")]


def test_p5_hide_hides_on_a_real_true_alone(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    record = _record(top, f"{a}\n")
    assert _listed(record, [{"path": str(a), "hide": True}]) == []
    for hide in ("yes", 1, False):
        assert _listed(record, [{"path": str(a), "hide": hide}]) == [(a, "a")]
    for name in ("", 5, ["x"], None):
        assert _listed(record, [{"path": str(a), "name": name}]) == [(a, "a")]


def test_p5_the_rows_come_first_then_the_record_each_path_once(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a, b, c = (_site(top, name) for name in "abc")
    record = _record(top, f"{a}\n{c}\n  {a} \t\n{b}\n")
    got = _listed(record, [{"path": str(b), "name": "Bee"}])
    assert got == [(b, "Bee"), (a, "a"), (c, "c")]


def test_p2_a_blank_line_a_tab_and_a_space_list_nothing(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    assert _listed(_record(top, f"  {a} \t\n")) == [(a, "a")]
    assert _listed(_record(top, "\n\t\n   \n")) == []


def test_p4_a_relative_line_is_no_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    _site(top, "b")
    monkeypatch.chdir(top)
    assert _listed(_record(top, f"b\n./a/../a\n{a}/../a\n")) == [(a, "a")]
    assert _listed(_record(top, "~/a\n")) == []


def test_p6_a_minions_that_is_a_link_is_no_project(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    real = top / "real"
    real.mkdir()
    a = _site(top, "a", minions=False)
    (a / ".minions").symlink_to(real)
    assert _listed(_record(top, f"{a}\n")) == []
    assert _listed(top / "none", [{"path": str(a)}]) == []
    b = _site(top / "home", "b")
    (top / "linked").symlink_to(top / "home")
    under = top / "linked" / "b"
    assert _listed(_record(top, f"{under}\n")) == [(b, "b")]
    assert _listed(top / "none", [{"path": str(under)}]) == [(b, "b")]


def test_p6_a_minions_that_is_a_file_or_a_dangling_link_is_no_project(
    tmp_path: Path,
) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a", minions=False)
    b = _site(top, "b", minions=False)
    (a / ".minions").write_text("x")
    (b / ".minions").symlink_to(top / "nowhere")
    assert _listed(_record(top, f"{a}\n{b}\n")) == []
    assert _listed(top / "none", [{"path": str(a)}, {"path": str(b)}]) == []


def test_p1_a_record_that_is_no_file_raises_broken(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    plain = _record(top / "src", f"{a}\n")
    (top / "link").symlink_to(plain)
    (top / "folder").mkdir()
    (top / "dangling").symlink_to(top / "nowhere")
    for record in ("link", "folder", "dangling"):
        with pytest.raises(kept.Broken, match="it is not a file"):
            _listed(top / record)
    assert _listed(top / "missing") == []
    assert _listed(_record(top, "")) == []
    assert _listed(plain) == [(a, "a")]


@pytest.mark.slow
def test_p1_a_record_that_is_a_pipe_raises_broken_at_once(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    os.mkfifo(top / "repos")
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            _PROJECTS_CHILD,
            str(_VIEWER),
            str(top / "repos"),
            str(a),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert done.returncode == 1
    assert done.stderr.splitlines()[-1].endswith("repos: it is not a file")


def test_p2_a_bad_byte_or_a_nul_byte_raises_broken(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    for text in (b"\xffbad\n" + f"{a}\n".encode(), b"\xff\xfe"):
        with pytest.raises(kept.Broken, match="it is not text"):
            _listed(_record(top, text))
    assert _listed(_record(top, f"{a}\n")) == [(a, "a")]
    with pytest.raises(kept.Broken, match="a line holds a NUL byte"):
        _listed(_record(top, f"{a}\nx\x00y\n"))


def test_p2_crlf_line_ends_and_a_leading_blank_line_read(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    b = _site(top, "b")
    text = f"\r\n{a}\r\n{b}\r\n".encode()
    assert _listed(_record(top, text)) == [(a, "a"), (b, "b")]


def test_p3_a_record_past_the_bound_raises_broken(tmp_path: Path) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    c = _site(top, "c")
    lead = f"{a}\n"
    for text in (
        lead + "\n" * _PART + f"{c}\n",
        lead + "\n" * (262141 - len(lead)) + f"{c}\n",
        "\n" * (_PART - 1) + f"{c}\n",
    ):
        with pytest.raises(kept.Broken, match=f"it is over {_PART} bytes"):
            _listed(_record(top, text))
    full = lead + "\n" * (_PART - len(lead) - len(f"{c}\n")) + f"{c}\n"
    assert len(full) == _PART
    assert _listed(_record(top, full)) == [(a, "a"), (c, "c")]


def test_snapshot_shows_one_row_for_a_record_that_cannot_be_read(
    tmp_path: Path,
) -> None:
    top = tmp_path.resolve()
    a = _site(top, "a")
    b = _site(top, "b")

    def read(path: Path, only: str | None) -> dict[str, Any]:
        if only == "fingerprint":
            return {"fingerprint": "f"}
        return {"name": path.name, "unread": None, "versions": []}

    snapshot = _viewer()["snapshot"]
    rows = [{"path": str(a)}]
    shown = snapshot(0.0, _record(top, "x\x00y\n"), rows, {}, read)
    assert [each["name"] for each in shown] == ["repos", "a"]
    assert shown[0]["unread"] == "repos could not be read: a line holds a NUL byte"
    assert (shown[0]["versions"], shown[0]["run"]) == ([], None)
    shown = snapshot(0.0, _record(top, f"{b}\n"), rows, {}, read)
    assert [each["name"] for each in shown] == ["a", "b"]
    assert _listed(None, rows) == [(a, "a")]


def _queued(root: Path, **entries: str) -> list[dict[str, Any]]:
    """Write each queue entry of `entries` by name and return the project's `queue`."""
    for name, text in entries.items():
        _entry(root, name.replace("_", "-"), text)
    queue: list[dict[str, Any]] = _tree(root)["queue"]
    return queue


def _cut(**fields: Any) -> str:  # noqa: ANN401
    """Return the JSON text of a queue entry of `fields` over a valid cut."""
    return json.dumps(_CUT | fields)


def test_p7_a_queue_entry_shows_its_halt_and_its_wait(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    queue = _queued(
        root,
        **{
            "0001_a": _cut(halt=""),
            "0002_b": _cut(waits=""),
            "0003_c": _cut(waits=None),
            "0004_d": _cut(waits="1 in flight, cap 1"),
            "0005_e": _cut(halt="the cut halted", waits="1 in flight, cap 1"),
        },
    )
    assert [(row["id"], row["state"], row["halt"], row["waits"]) for row in queue] == [
        ("0001-a", "cut halted", "", None),
        ("0002-b", "cut", None, ""),
        ("0003-c", "cut", None, None),
        ("0004-d", "queued", None, "1 in flight, cap 1"),
        ("0005-e", "cut halted", "the cut halted", None),
    ]


def test_p7_an_entry_that_is_no_valid_cut_is_a_halted_cut(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    broken = {
        "0001_a": _cut(halt=0),
        "0002_b": _cut(waits=5),
        "0003_c": _cut(waits=["x"]),
        "0004_d": "no json",
        "0005_e": "[1]",
        "0006_f": "",
        "0007_g": json.dumps({k: v for k, v in _CUT.items() if k != "halt"}),
    }
    queue = _queued(root, **broken)
    assert [row["id"] for row in queue] == [n.replace("_", "-") for n in broken]
    for row in queue:
        assert row["state"] == "cut halted"
        assert (row["halt"], row["waits"]) == ("the queue entry is unreadable", None)


def test_a_converge_skipped_line_is_an_event_in_its_lower_case_form(root: Path) -> None:
    _log(
        root,
        [
            "10:00:01 · x · converge skipped — plan",
            "10:00:02 · y · Converge Skipped — plan",
        ],
    )
    assert _tree(root)["run"]["last"] == "10:00:01 · x · converge skipped — plan"


def _spent_of(
    models: tuple[str, str | None, str | None] = ("claude", None, None),
    tokens: int | None = 1,
    fallback: bool | str = False,
) -> str:
    """Return the spent text converge writes for a checker's plain values."""
    return statuslog.spent(models, tokens, fallback)


def test_s9_spent_words_each_field_and_any_string_fallback_as_failed() -> None:
    base = "executor claude · model default · effort default · tokens"
    assert _spent_of(tokens=0) == f"{base} 0"
    assert _spent_of(tokens=None) == f"{base} unavailable"
    models = ("codex", "gpt-6.1-sol", "high")
    assert _spent_of(models=models) == (
        "executor codex · model gpt-6.1-sol · effort high · tokens 1"
    )
    assert _spent_of(fallback=True) == f"{base} 1 · fallback: codex usage limit"
    for text in ("", "limit"):
        assert _spent_of(fallback=text) == f"{base} 1 · fallback: codex failed"
