"""The run log as the conductor writes and reads it, pinned, and its module's cases.

Cases a to i and the log's pins of 0140-run-log design's pin; the module's, by function.
"""

import errno
import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from conduct_load import conduct as _conduct
from mflib import platform, runlog

conduct = _conduct()
_NAMES = conduct["main"].__globals__
_STOP_LINE = "10:20:30 · run · halt — stopped by the person\n"
_START = "10:00:00 · run · start — executor claude"
_DONE = "10:09:00 · run · done — 0 versions"


def _verify(tmp_path: Path, *lines: str) -> str | None:
    """Return the verify of a log holding a title, then `lines`."""
    log = tmp_path / "verified.md"
    log.write_text("# Ship run 20261101-100000\n\n" + "".join(f"{x}\n" for x in lines))
    return runlog.verify(log)


def _log(runs: Path, stamp: str) -> runlog.RunLog:
    """Return the run log the conductor makes."""
    return runlog.RunLog(runs, stamp)


def test_case_a_the_event_list_is_exactly_its_names() -> None:
    listed = runlog.EVENTS
    assert listed == (
        *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
        *("push", "ledger", "unlock", "unkept", "kept", "removed", "rejoin", "grant"),
        *("rescue", "move", "cut", "supervise", "wait", "stacked", "reset", "notes"),
        *("limited", "sync", "codex"),
        "converge skipped",
    )


def test_case_a_a_log_holding_each_listed_event_before_a_done_passes(
    tmp_path: Path,
) -> None:
    for name in runlog.EVENTS:
        line = f"10:00:01 · 0001-a · {name} — build · x"
        closed = ["10:00:02 · 0001-a · finish — build · exit 0 · 1s"]
        lines = [line, *closed] if name == "spawn" else [line]
        assert _verify(tmp_path, _START, *lines, _DONE) is None, name


def test_case_a_the_pattern_reads_its_parts() -> None:
    event = conduct["EVENT"]

    skipped = event.match("10:00:00 · 0001-to-do · converge skipped — plan")
    assert skipped is not None
    assert (skipped[1], skipped[2]) == ("0001-to-do", "converge skipped")
    found = event.match("10:00:00 · run · halt — a — b")
    assert found is not None
    assert found.string[found.end() :] == "a — b"
    for refused in (
        "10:00 · run · done — x",
        "10:00:00 - run · done — x",
        "10:00:00 · run - done — x",
        "10:00:00 · run · done - x",
        "10:00:00 · run · done —x",
        "10:00:00 run · done — x",
        "10:00:00 · run done — x",
    ):
        assert event.match(refused) is None, refused


def test_case_a_an_unlisted_name_matches_the_pattern_and_the_list_refuses_it(
    tmp_path: Path,
) -> None:
    line = "10:00:01 · run · retry — build"

    assert conduct["EVENT"].match(line) is not None
    assert _verify(tmp_path, _START, line, _DONE) == f"unknown event: {line}"


def test_case_c_the_verify_skips_blank_and_title_lines_alone(tmp_path: Path) -> None:
    assert _verify(tmp_path, "", "   ", "# another title", _START, _DONE) is None
    for line in ("## Run", "#title", " # title"):
        assert _verify(tmp_path, _START, line, _DONE) == f"unknown event: {line}"


def test_case_c_a_finish_with_no_spawn_passes_and_banks_nothing(
    tmp_path: Path,
) -> None:
    finish = "10:00:01 · 0001-a · finish — build · exit 0 · 1s"
    spawn = "10:00:02 · 0001-a · spawn — build · model default"

    assert _verify(tmp_path, _START, finish, _DONE) is None
    assert (
        _verify(tmp_path, _START, finish, spawn, _DONE)
        == "a spawn with no finish: 0001-a build"
    )


def test_case_c_a_finish_by_another_who_or_station_closes_nothing(
    tmp_path: Path,
) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    for finish in (
        "10:00:02 · 0002-b · finish — build · exit 0 · 1s",
        "10:00:02 · 0001-a · finish — release · exit 0 · 1s",
    ):
        assert (
            _verify(tmp_path, _START, spawn, finish, _DONE)
            == "a spawn with no finish: 0001-a build"
        ), finish


def test_case_c_the_station_is_the_detail_up_to_its_first_separator(
    tmp_path: Path,
) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    bare = "10:00:01 · 0001-a · spawn — build"
    finish = "10:00:02 · 0001-a · finish — build · exit 0 · 1s"
    assert _verify(tmp_path, _START, spawn, finish, _DONE) is None
    assert _verify(tmp_path, _START, bare, finish, _DONE) is None

    spaced = "10:00:01 · 0001-a · spawn — build x · model default"
    other = "10:00:02 · 0001-a · finish — build y · exit 0 · 1s"
    assert (
        _verify(tmp_path, _START, spaced, other, _DONE)
        == "a spawn with no finish: 0001-a build x"
    )


def test_case_c_an_open_spawn_passes_only_under_the_stop_text(
    tmp_path: Path,
) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    last = "10:00:02 · run · halt — stopped by the person"
    assert _verify(tmp_path, _START, spawn, last) is None
    for last in (
        "10:00:02 · 0001-a · halt — stopped by the person",
        "10:00:02 · run · done — stopped by the person",
        "10:00:02 · run · halt — stopped by the person!",
        "10:00:02 · run · halt — not stopped by the person",
        "10:00:02 · run · halt — build: phase 1 unticked",
    ):
        assert (
            _verify(tmp_path, _START, spawn, last)
            == "a spawn with no finish: 0001-a build"
        ), last


def test_case_c_a_complete_log_returns_none_and_an_open_end_names_itself(
    tmp_path: Path,
) -> None:
    assert _verify(tmp_path, _START, _DONE) is None
    assert _verify(tmp_path, _START, "10:00:01 · 0001-a · halt — x") is None
    assert (
        _verify(tmp_path, _START, "10:00:01 · 0001-a · check — build · pass")
        == "the run ends on neither halt nor done"
    )


def _logs(runs: Path, **logs: list[str]) -> Path:
    """Write each run log, by its stamp, holding its lines; return `runs`.

    e.g. `s1=[…]` → `20261101-100001.md`, `s1_2=[…]` → `20261101-100001-2.md`
    """
    runs.mkdir(parents=True, exist_ok=True)
    for key, lines in logs.items():
        stamp = f"20261101-10000{key[1]}" + key[2:].replace("_", "-")
        text = f"# Ship run {stamp}\n\n" + "".join(f"{line}\n" for line in lines)
        (runs / f"{stamp}.md").write_text(text)
    return runs


_SPAWN = "10:00:01 · 0001-a · spawn — release · model default"
_EXIT_0 = "10:00:02 · 0001-a · finish — release · exit 0 · 1s"


def _died(runs: Path) -> bool:
    return runlog.release_died(runs, "0001-a")


def test_case_b_the_newest_log_is_read_first_and_a_suffix_is_newer(
    tmp_path: Path,
) -> None:
    assert _died(_logs(tmp_path / "a", s1=[_EXIT_0], s1_2=[_SPAWN]))
    assert not _died(_logs(tmp_path / "b", s1=[_SPAWN], s1_2=[_EXIT_0]))
    assert not _died(_logs(tmp_path / "c", s1=[_SPAWN], s2=[_EXIT_0]))
    assert _died(_logs(tmp_path / "d", s1=[_EXIT_0], s2=[_SPAWN]))


def test_case_b_the_changes_last_release_line_decides(tmp_path: Path) -> None:
    finish = "10:00:03 · 0001-a · finish — release · "
    cases = {
        "spawn last": ([_EXIT_0, _SPAWN], True),
        "exit 0 last": ([_SPAWN, _EXIT_0], False),
        "exit 1": ([_SPAWN, f"{finish}exit 1 · 1s"], True),
        "exit 0 bare": ([_SPAWN, f"{finish}exit 0"], True),
        "exit 00": ([_SPAWN, f"{finish}exit 00 · 1s"], True),
        "check": ([_SPAWN, "10:00:03 · 0001-a · check — release · pass"], True),
        "denied": (
            [_SPAWN, _EXIT_0, "10:00:03 · 0001-a · denied — release · Bash(x)"],
            False,
        ),
        "other change": (
            [_EXIT_0, "10:00:03 · 0002-b · spawn — release · model default"],
            False,
        ),
        "releaser": (
            [_EXIT_0, "10:00:03 · 0001-a · spawn — releaser · model default"],
            False,
        ),
        "no finish": ([_SPAWN], True),
        "no release": ([_START], False),
    }
    for name, (lines, died) in cases.items():
        assert _died(_logs(tmp_path / name, s1=lines)) is died, name
    assert not _died(tmp_path / "none")


def test_case_b_a_newer_log_with_no_release_line_passes_the_read_on(
    tmp_path: Path,
) -> None:
    newer = [_START, "10:00:01 · 0001-a · spawn — build · model default"]

    assert _died(_logs(tmp_path / "a", s1=[_SPAWN], s2=newer))
    assert not _died(_logs(tmp_path / "b", s1=[_SPAWN, _EXIT_0], s2=newer))


def _rescuing(runs: Path) -> bool:
    return runlog.rescuing(runs, "0001-a")


def test_case_f_spawn_and_finish_alone_count_for_rescue_and_supervise(
    tmp_path: Path,
) -> None:
    rescue = "10:00:01 · 0001-a · spawn — rescue · model default"
    supervise = "10:00:01 · 0001-a · spawn — supervise · model default"
    cases = {
        "rescue": ([rescue], True),
        "supervise": ([supervise], True),
        "denied": ([rescue, "10:00:02 · 0001-a · denied — rescue · Bash(x)"], True),
        "rescued": ([rescue, "10:00:02 · 0001-a · finish — rescue · exit 0"], False),
        "supervised": (
            [supervise, "10:00:02 · 0001-a · finish — supervise · exit 0"],
            False,
        ),
        "mixed": ([rescue, "10:00:02 · 0001-a · finish — supervise · exit 0"], False),
        "other change": (
            ["10:00:01 · 0002-b · spawn — rescue · model default"],
            False,
        ),
        "rescuer": (["10:00:01 · 0001-a · spawn — rescuer · model default"], False),
        "none": ([_START], False),
    }
    for name, (lines, rescuing) in cases.items():
        assert _rescuing(_logs(tmp_path / name, s1=lines)) is rescuing, name
    assert not _rescuing(tmp_path / "no log")


def test_case_f_only_the_newest_log_is_read(tmp_path: Path) -> None:
    rescue = "10:00:01 · 0001-a · spawn — rescue · model default"

    assert not _rescuing(_logs(tmp_path / "a", s1=[rescue], s2=[_START]))
    assert _rescuing(_logs(tmp_path / "b", s1=[_START], s2=[rescue]))


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read every clock the conductor writes as `10:20:30`."""
    real = time.strftime
    monkeypatch.setattr(
        time,
        "strftime",
        lambda form, *at: "10:20:30" if form == "%H:%M:%S" else real(form, *at),
    )


def test_case_d_logs_made_on_one_stamp_take_suffixes_and_titles(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    made = [_log(runs, "20261101-100000") for _ in "abc"]

    stamps = ["20261101-100000", "20261101-100000-2", "20261101-100000-3"]
    assert [log.stamp for log in made] == stamps
    assert [log.path for log in made] == [runs / f"{s}.md" for s in stamps]
    assert set(runs.iterdir()) == {runs / f"{s}.md" for s in stamps}
    assert [log.path.read_text() for log in made] == [
        f"# Ship run {s}\n\n" for s in stamps
    ]
    assert [log.held for log in made] == [None] * 3


def test_case_d_a_standing_file_is_never_written_over(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "20261101-100000.md").write_text("kept\n")

    log = _log(runs, "20261101-100000")

    assert log.path.name == "20261101-100000-2.md"
    assert (runs / "20261101-100000.md").read_text() == "kept\n"


@pytest.mark.usefixtures("clock")
def test_case_d_an_event_folds_its_detail_and_a_held_event_writes_nothing(
    tmp_path: Path,
) -> None:
    log = _log(tmp_path / "runs", "20261101-100000")
    title = "# Ship run 20261101-100000\n\n"

    log.event("0001-a", "spawn", "build ·\n  model\tdefault ")
    line = "10:20:30 · 0001-a · spawn — build · model default\n"
    assert log.path.read_text() == title + line

    log.held = []
    log.event("run", "start", "a\nb")
    assert log.path.read_text() == title + line
    assert log.held == [("run", "start", "a\nb")]


@pytest.mark.usefixtures("clock")
def test_case_d_an_append_waits_for_the_process_lock(tmp_path: Path) -> None:
    log = _log(tmp_path / "runs", "20261101-100000")
    title = log.path.read_text()

    with log.lock:
        child = threading.Thread(target=lambda: log.event("run", "start", "x"))
        child.start()
        child.join(timeout=0.3)
        assert child.is_alive()
        assert log.path.read_text() == title
    child.join(timeout=10)

    assert log.path.read_text() == f"{title}10:20:30 · run · start — x\n"


@pytest.mark.usefixtures("clock")
def test_case_e_the_stop_line_goes_to_the_newest_log_alone(tmp_path: Path) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    runs = _logs(tmp_path / "runs", s1=[_START, spawn], s2=[_START, spawn])
    older = (runs / "20261101-100001.md").read_text()
    newest = runs / "20261101-100002.md"
    held = newest.read_text()

    assert runlog.stop(runs) == newest
    assert newest.read_text() == held + _STOP_LINE
    assert (runs / "20261101-100001.md").read_text() == older
    assert runlog.verify(newest) is None


def test_case_e_a_stop_with_no_log_makes_no_file(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    assert runlog.stop(runs) is None
    assert not runs.exists()
    runs.mkdir()
    (runs / "detached.log").write_text("run: done\n")
    assert runlog.stop(runs) is None
    assert sorted(path.name for path in runs.iterdir()) == ["detached.log"]


def _repo(tmp_path: Path) -> Path:
    """Return a primary checkout on `main` holding one commit, `.minions/` ignored."""
    root = (tmp_path / "main").resolve()
    root.mkdir()
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "mf"),
        ("config", "user.email", "mf@example.invalid"),
        ("config", "commit.gpgsign", "false"),
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    (root / ".gitignore").write_text(".minions/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)
    return root


@pytest.fixture
def claimed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[Path, subprocess.Popen[bytes]]]:
    """Return a primary whose claim names a live `sleep` as its conductor, and it."""
    root = _repo(tmp_path)
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    conductor = subprocess.Popen(["sleep", "60"], start_new_session=True)
    (active / "pid").write_text(str(conductor.pid))
    (active / "start").write_text("S")
    monkeypatch.setitem(_NAMES, "_started", lambda pid: "S")
    yield root, conductor
    conductor.kill()
    conductor.wait(timeout=10)


@pytest.mark.usefixtures("clock")
def test_case_e_stop_run_kills_removes_the_claim_and_names_the_log(
    claimed: tuple[Path, subprocess.Popen[bytes]],
) -> None:
    root, conductor = claimed
    runs = root / ".minions" / "runs"
    _logs(runs, s1=[_START])

    said = conduct["stop_run"](root)

    assert said == "stop: stopped · .minions/runs/20261101-100001.md"
    assert conductor.wait(timeout=10) == -signal.SIGKILL
    assert not (runs / "active").exists()
    assert (runs / "20261101-100001.md").read_text().endswith(_STOP_LINE)


def test_case_e_a_conductor_gone_reads_stopped_with_no_run_log(
    claimed: tuple[Path, subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = claimed

    def gone(pid: int, sig: int) -> None:
        raise ProcessLookupError(pid)

    with monkeypatch.context() as patch:
        patch.setattr(os, "kill", gone)
        said = conduct["stop_run"](root)

    assert said == "stop: stopped · no run log"
    assert not (root / ".minions" / "runs" / "active").exists()


def test_case_e_a_conductor_that_refuses_the_kill_keeps_the_claim(
    claimed: tuple[Path, subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, conductor = claimed

    def refuse(pid: int, sig: int) -> None:
        raise PermissionError(1, "not permitted")

    with monkeypatch.context() as patch:
        patch.setattr(os, "kill", refuse)
        with pytest.raises(conduct["Stop"]) as stopped:
            conduct["stop_run"](root)

    assert stopped.value.code == 2
    assert str(stopped.value) == (
        "stop: cannot run — the conductor survives: [Errno 1] not permitted"
    )
    assert (root / ".minions" / "runs" / "active" / "pid").is_file()
    assert conductor.poll() is None


@pytest.mark.usefixtures("clock")
def test_case_e_a_group_that_survives_still_gets_the_stop_line(
    claimed: tuple[Path, subprocess.Popen[bytes]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, conductor = claimed
    runs = root / ".minions" / "runs"
    _logs(runs, s1=[_START])
    (runs / "active" / "4242").write_text("S")
    killed: list[int] = []

    def refuse(group: int, sig: int) -> None:
        raise PermissionError(1, "not permitted")

    with monkeypatch.context() as patch:
        patch.setattr(os, "kill", lambda pid, sig: killed.append(pid))
        patch.setattr(os, "killpg", refuse)
        patch.setattr(platform, "process", lambda pid, field: "claude")
        with pytest.raises(conduct["Stop"]) as stopped:
            conduct["stop_run"](root)

    assert stopped.value.code == 2
    assert str(stopped.value) == (
        "stop: conductor stopped · conduct: cannot clear the claim — worker group"
        " 4242 survives: [Errno 1] not permitted"
    )
    assert killed == [conductor.pid]
    assert (runs / "active" / "4242").is_file()
    assert (runs / "20261101-100001.md").read_text().endswith(_STOP_LINE)


def test_case_h_the_order_key_and_the_newest_by_stamp_then_suffix(
    tmp_path: Path,
) -> None:
    assert runlog.order(Path("20261029-163000-2.md")) == (
        "20261029-163000",
        17,
        "20261029-163000-2",
    )
    runs = _logs(tmp_path / "a", s1=[], s1_2=[], s1_9=[], s1_10=[])
    assert conduct["last_log"](runs) == runs / "20261101-100001-10.md"
    _logs(runs, s2=[])
    assert conduct["last_log"](runs) == runs / "20261101-100002.md"


def test_case_h_the_newest_is_by_name_never_by_modification_time(
    tmp_path: Path,
) -> None:
    runs = _logs(tmp_path / "runs", s1=[], s2=[])
    later = time.time() + 3600
    os.utime(runs / "20261101-100001.md", (later, later))

    assert conduct["last_log"](runs) == runs / "20261101-100002.md"


def test_case_h_folders_the_claim_and_the_detached_log_are_passed_over(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    (runs / "active").mkdir(parents=True)
    (runs / "20261102-000000").mkdir()
    (runs / "detached.log").write_text("run: done\n")
    assert conduct["last_log"](runs) is None
    assert conduct["last_log"](tmp_path / "missing") is None

    _logs(runs, s1=[])
    assert conduct["last_log"](runs) == runs / "20261101-100001.md"


def _polls(
    monkeypatch: pytest.MonkeyPatch,
    claims: list[str],
    steps: list[Callable[[], object]],
) -> None:
    """Answer `_claim` from `claims`, the last kept; run `steps` at each poll."""
    answers = iter(claims)
    monkeypatch.setitem(_NAMES, "_claim", lambda active: next(answers, claims[-1]))
    planned = iter(steps)
    real = time.sleep

    def sleep(seconds: float) -> None:
        if seconds != conduct["WAIT_SECONDS"]:
            real(seconds)
            return
        next(planned, lambda: None)()

    monkeypatch.setattr(time, "sleep", sleep)


def _gain(log: Path, text: str) -> Callable[[], object]:
    """Return a step that appends `text` to `log`, making it when it stands not."""

    def step() -> None:
        with log.open("a") as handle:
            handle.write(text)

    return step


_ENDED = "wait: ended\nstatus: none — no open version\n"


def test_case_g_a_stale_claim_is_no_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path)
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    (active / "pid").write_text("x")

    assert conduct["wait_run"](root) == 0
    assert capsys.readouterr().out == "wait: none — no run is live\n"


def test_case_g_old_lines_are_not_printed_and_a_part_line_waits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    runs = _logs(root / ".minions" / "runs", s1=[_START])
    log = runs / "20261101-100001.md"
    spawn = "10:00:01 · 0001-a · spawn — build · model default\n"
    steps = [_gain(log, f"{spawn}10:00:02 · run · pa"), _gain(log, "rt\n")]
    _polls(monkeypatch, ["live"] * 3 + ["none"], steps)

    assert conduct["wait_run"](root) == 0
    assert capsys.readouterr().out == (
        f"{spawn}wait: live · +1 lines\n"
        "10:00:02 · run · part\nwait: live · +1 lines\n" + _ENDED
    )


def test_case_g_a_first_log_and_a_newer_log_are_read_from_their_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    first = f"# Ship run 20261101-100001\n\n{_START}\n"
    newer = "10:05:00 · run · start — executor codex\n"
    steps = [
        _gain(runs / "20261101-100001.md", first),
        _gain(runs / "20261101-100001-2.md", newer),
    ]
    _polls(monkeypatch, ["live"] * 3 + ["none"], steps)

    assert conduct["wait_run"](root) == 0
    assert capsys.readouterr().out == (
        f"# Ship run 20261101-100001\n\n{_START}\nwait: live · +3 lines\n"
        f"{newer}wait: live · +1 lines\n" + _ENDED
    )


def _report(root: Path, *lines: str) -> list[str]:
    """Return `report`'s lines over one run log holding a title, then `lines`."""
    _logs(root / ".minions" / "runs", s1=list(lines))
    return conduct["report"](root).splitlines()


def test_case_i_the_runs_denials_waits_versions_and_tail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    halt = "10:00:05 · 10000-b · halt — build: phase 1 unticked"
    skipped = "10:00:09 · run · rejoin — skipped — 9999-a is live"
    closing = "10:00:14 · run · halt — run: the last"

    assert _report(
        root,
        _START,
        "10:00:01 · run · denied — probe · Bash(a)",
        "a line that is no event",
        "10:00:02 · run · denied — probe · Bash(b · c)",
        "10:00:03 · run · push — waiting: origin unreachable",
        "10:00:04 · run · push — pushed main",
        halt,
        "10:00:06 · 9999-a · spawn — build · model default",
        "10:00:07 · run · rejoin — 9999-a: build",
        "10:00:08 · run · rejoin — 9999-a: still halted",
        skipped,
        "10:00:10 · run · rescue — 9999-a: fixed · tasks.md amended",
        "10:00:11 · run · rescue — 9999-a: diagnosed · rescue.md",
        "10:00:12 · run · supervise — 9999-a: decided · D3",
        "10:00:13 · run · supervise — 9999-a: spent · two rounds",
        closing,
    ) == [
        "run · denied Bash(a), Bash(b · c)",
        "run · waited origin unreachable",
        "9999-a · no version branch",
        "10000-b · no version branch",
        halt,
        "9999-a · rejoined build",
        skipped,
        "9999-a · rescued tasks.md amended",
        "9999-a · diagnosed rescue.md",
        "9999-a · supervised D3",
        "9999-a · spent two rounds",
        closing,
    ]


def test_case_i_each_versions_blocked_part(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    for change in ("0001-a", "0002-b"):
        subprocess.run(["git", "branch", change], cwd=root, check=True)

    lines = _report(
        root,
        _START,
        "10:00:01 · 0001-a · blocked — by 0003-c",
        "10:00:02 · 0001-a · blocked — by 0002-b",
        "10:00:03 · 0002-b · spawn — build · model default",
        _DONE,
    )

    assert [line.split(" · ")[0] for line in lines[:2]] == ["0001-a", "0002-b"]
    assert lines[0].endswith(" · metrics: none · blocked by 0002-b")
    assert lines[1].endswith(" · metrics: none")
    assert lines[2:] == [_DONE]


def test_case_i_no_run_and_a_log_with_no_event(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert conduct["report"](root) == "report: none — no run yet"

    assert _report(root, "no event here") == ["20261101-100001.md: no event"]


def test_pin_a_bad_byte_is_replaced_in_the_verify_the_death_and_report(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    log = runs / "20261101-100001.md"
    log.write_bytes(f"{_START}\n{_SPAWN}".encode() + b" \xff\n")

    assert runlog.verify(log) == "a spawn with no finish: 0001-a release"
    assert _died(runs)
    assert (
        conduct["report"](root).splitlines()[-1]
        == f"{_SPAWN} \N{REPLACEMENT CHARACTER}"
    )


def test_pin_a_bad_byte_is_replaced_in_the_rescues_read_and_the_wait(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    log = runs / "20261101-100001.md"
    log.write_bytes("10:00:01 · 0001-a · spawn — rescue · x".encode() + b" \xff\n")
    assert _rescuing(runs)

    def gain() -> None:
        with log.open("ab") as handle:
            handle.write(b"10:00:03 \xff\n")

    _polls(monkeypatch, ["live", "live", "none"], [gain])

    assert conduct["wait_run"](root) == 0
    assert capsys.readouterr().out == ("10:00:03 �\nwait: live · +1 lines\n" + _ENDED)


def test_pin_the_append_and_the_stop_line_refuse_a_link_naming_it(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    log = _log(runs, "20261101-100001")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n")
    log.path.unlink()
    log.path.symlink_to(outside)

    for write in (lambda: log.event("run", "start", "x"), lambda: runlog.stop(runs)):
        with pytest.raises(OSError, match=r"20261101-100001\.md") as refused:
            write()
        assert refused.value.filename == log.path.name

    assert outside.read_text() == "outside\n"
    assert log.path.is_symlink()


def test_pin_the_create_refuses_a_dangling_link_and_takes_the_next_suffix(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "20261101-100001.md").symlink_to(runs / "gone.md")

    log = _log(runs, "20261101-100001")

    assert log.path == runs / "20261101-100001-2.md"
    assert not (runs / "gone.md").exists()


def _children(calls: dict[str, Callable[[], object]]) -> dict[str, object]:
    """Run each call in a daemon thread, joined within 10 s in all; return each result.

    A call that raises `OSError` gives its errno; one still running gives `"running"`.
    """
    said: dict[str, object] = {}

    def record(name: str, call: Callable[[], object]) -> Callable[[], None]:
        def run() -> None:
            try:
                said[name] = call()
            except OSError as error:
                said[name] = error.errno

        return run

    children = {
        name: threading.Thread(target=record(name, call), daemon=True)
        for name, call in calls.items()
    }
    for child in children.values():
        child.start()
    # A pipe opened blocking would wait for its other end: the deadline bounds the run.
    deadline = time.monotonic() + 10
    for child in children.values():
        child.join(timeout=max(0.0, deadline - time.monotonic()))
    return {
        name: "running" if child.is_alive() else said.get(name)
        for name, child in children.items()
    }


def test_pin_each_reader_ends_at_once_on_a_pipe_at_the_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    pipe = runs / "20261101-100001.md"
    os.mkfifo(pipe)
    _polls(monkeypatch, ["live", "live", "none"], [])

    said = _children(
        {
            "verify": lambda: runlog.verify(pipe),
            "death": lambda: _died(runs),
            "rescue": lambda: _rescuing(runs),
            "report": lambda: conduct["report"](root),
            "wait": lambda: conduct["wait_run"](root),
        }
    )

    assert said == {
        "verify": errno.EINVAL,
        "death": False,
        "rescue": False,
        "report": "20261101-100001.md: no event",
        "wait": 0,
    }
    assert capsys.readouterr().out.startswith("wait: live · +0 lines\nwait: ended\n")


def test_pin_the_append_and_the_stop_line_end_at_once_on_a_pipe_at_the_log(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    log = _log(runs, "20261101-100001")
    log.path.unlink()
    os.mkfifo(log.path)

    said = _children(
        {
            "append": lambda: log.event("run", "start", "x"),
            "stop": lambda: runlog.stop(runs),
        }
    )

    assert said == {"append": errno.ENXIO, "stop": errno.ENXIO}
    reader = os.open(log.path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        assert _children({"append": lambda: log.event("run", "start", "x")}) == {
            "append": errno.EINVAL
        }
        assert os.read(reader, 64) == b""
    finally:
        os.close(reader)


@pytest.mark.usefixtures("clock")
def test_pin_a_name_that_is_no_stamp_is_no_log(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    runs = _logs(root / ".minions" / "runs", s1=[_EXIT_0])
    notes = runs / "notes.md"
    held = (
        "10:00:03 · 0001-a · spawn — rescue · model default\n"
        f"{_SPAWN}\n10:00:04 · run · done — notes\n"
    )
    notes.write_text(held)
    log = runs / "20261101-100001.md"

    assert conduct["last_log"](runs) == log
    assert not _rescuing(runs)
    assert not _died(runs)
    assert conduct["report"](root).splitlines()[-1] == _EXIT_0
    assert runlog.stop(runs) == log
    assert log.read_text().endswith(_STOP_LINE)
    assert notes.read_text() == held


def test_pin_a_digit_led_name_is_no_log(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "1.md").write_text(f"{_SPAWN}\n")
    assert conduct["last_log"](runs) is None
    assert not _died(runs)

    _logs(runs, s1=[_EXIT_0])
    assert conduct["last_log"](runs) == runs / "20261101-100001.md"
    assert not _died(runs)


def test_pin_a_sync_or_codex_line_passes_the_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    for line in (
        "10:00:01 · run · sync — mf-ship scripts synced",
        "10:00:01 · run · codex — not on PATH: checkers run on claude",
    ):
        log = tmp_path / "sync.md"
        log.write_text(f"# Ship run x\n\n{_START}\n{line}\n{_DONE}\n")
        assert conduct["main"](["log", "--verify", str(log)]) == 0
        assert capsys.readouterr().out == "log: complete\n"


@pytest.mark.usefixtures("clock")
def test_pin_a_planted_lock_folder_stops_neither_the_append_nor_the_stop_line(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    log = _log(runs, "20261101-100001")
    title = log.path.read_text()
    (runs / "20261101-100001.lock").mkdir()

    log.event("run", "start", "x")
    assert runlog.stop(runs) == log.path

    assert log.path.read_text() == f"{title}10:20:30 · run · start — x\n{_STOP_LINE}"


def test_pin_wait_prints_nothing_from_a_newer_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    runs = _logs(root / ".minions" / "runs", s1=[_START])
    outside = tmp_path / "outside.md"
    outside.write_text("10:00:09 · run · done — planted\n")

    def plant() -> None:
        (runs / "20261101-100001-2.md").symlink_to(outside)

    _polls(monkeypatch, ["live", "live", "none"], [plant])

    assert conduct["wait_run"](root) == 0
    assert capsys.readouterr().out == "wait: live · +0 lines\n" + _ENDED


def _module_log(runs: Path, stamp: str = "20261101-100000") -> runlog.RunLog:
    return runlog.RunLog(runs, stamp)


def test_module_title_names_the_stamp() -> None:
    assert runlog.title("20261101-100000") == "# Ship run 20261101-100000"


@pytest.mark.usefixtures("clock")
def test_module_line_folds_the_detail_and_ends_on_no_newline() -> None:
    assert runlog.line("0001-a", "spawn", " build ·\n model\tx ") == (
        "10:20:30 · 0001-a · spawn — build · model x"
    )


def test_module_parse_reads_who_name_and_detail() -> None:
    text = "10:00:00 · 0001-to-do · converge skipped — plan — a"

    assert runlog.parse(text) == runlog.Event(
        text, "0001-to-do", "converge skipped", "plan — a"
    )
    assert runlog.parse("10:00 · run · done — x") is None
    assert runlog.parse("10:00:00 · run · retry — x") == runlog.Event(
        "10:00:00 · run · retry — x", "run", "retry", "x"
    )


def test_module_order_sorts_by_stamp_then_suffix(tmp_path: Path) -> None:
    names = ["20261101-100000-10", "20261101-100001", "20261101-100000-9"]
    logs = [tmp_path / f"{name}.md" for name in names]

    assert runlog.order(logs[0]) == ("20261101-100000", 18, "20261101-100000-10")
    assert [log.stem for log in sorted(logs, key=runlog.order)] == [
        "20261101-100000-9",
        "20261101-100000-10",
        "20261101-100001",
    ]


def test_module_newest_takes_the_last_log_by_order(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    assert runlog.newest(runs) is None
    _logs(runs, s1=[], s1_2=[])
    (runs / "detached.log").write_text("run: done\n")

    assert runlog.newest(runs) == runs / "20261101-100001-2.md"


def test_module_events_returns_each_line_that_parses(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[_START, "not an event", _DONE])

    assert runlog.events(runs / "20261101-100001.md") == [
        runlog.Event(_START, "run", "start", "executor claude"),
        runlog.Event(_DONE, "run", "done", "0 versions"),
    ]


def test_module_release_died_reads_the_last_release_line(tmp_path: Path) -> None:
    assert runlog.release_died(_logs(tmp_path / "a", s1=[_EXIT_0, _SPAWN]), "0001-a")
    assert not runlog.release_died(
        _logs(tmp_path / "b", s1=[_SPAWN, _EXIT_0]), "0001-a"
    )
    assert not runlog.release_died(_logs(tmp_path / "c", s1=[_SPAWN]), "0002-b")
    assert not runlog.release_died(tmp_path / "none", "0001-a")


def test_module_rescuing_reads_the_newest_log(tmp_path: Path) -> None:
    rescue = "10:00:01 · 0001-a · spawn — rescue · model default"
    done = "10:00:02 · 0001-a · finish — rescue · exit 0"

    assert runlog.rescuing(_logs(tmp_path / "a", s1=[_START], s2=[rescue]), "0001-a")
    assert not runlog.rescuing(_logs(tmp_path / "b", s1=[rescue, done]), "0001-a")
    assert not runlog.rescuing(_logs(tmp_path / "c", s1=[rescue], s2=[]), "0001-a")
    assert not runlog.rescuing(tmp_path / "none", "0001-a")


def test_module_verify_names_what_is_incomplete(tmp_path: Path) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    stopped = f"10:00:02 · run · halt — {runlog.STOPPED}"
    cases = {
        "complete": ([_START, _DONE], None),
        "unknown": ([_START, "10:00:01 · run · retry — x", _DONE], "unknown event: "),
        "open": ([_START, spawn, _DONE], "a spawn with no finish: 0001-a build"),
        "stopped": ([_START, spawn, stopped], None),
        "no end": ([_START], "the run ends on neither halt nor done"),
    }
    for name, (lines, why) in cases.items():
        runs = _logs(tmp_path / name, s1=lines)
        said = runlog.verify(runs / "20261101-100001.md")
        if why is None:
            assert said is None, name
        else:
            assert said is not None, name
            assert said.startswith(why), name


@pytest.mark.usefixtures("clock")
def test_module_stop_appends_the_stop_line_to_the_newest_log(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[_START], s2=[_START])
    held = (runs / "20261101-100002.md").read_text()

    assert runlog.stop(runs) == runs / "20261101-100002.md"
    assert (runs / "20261101-100002.md").read_text() == held + _STOP_LINE
    assert runlog.stop(tmp_path / "none") is None
    assert not (tmp_path / "none").exists()


@pytest.mark.usefixtures("clock")
def test_module_run_log_makes_a_titled_log_and_appends_events(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    first, second = _module_log(runs), _module_log(runs)

    assert (first.stamp, second.stamp) == ("20261101-100000", "20261101-100000-2")
    first.event("run", "start", "a\nb")
    first.held = []
    first.event("run", "done", "c")

    title = "# Ship run 20261101-100000\n\n"
    assert first.path.read_text() == f"{title}10:20:30 · run · start — a b\n"
    assert first.held == [("run", "done", "c")]


def test_module_tail_polls_whole_lines_and_a_newer_log(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[_START])
    log = runs / "20261101-100001.md"
    tail = runlog.Tail(runs)
    assert tail.poll() == []

    _gain(log, "10:00:01 · run · a\n10:00:02 · run · pa")()
    assert tail.poll() == ["10:00:01 · run · a"]
    _gain(log, "rt\n")()
    assert tail.poll() == ["10:00:02 · run · part"]
    _gain(runs / "20261101-100001-2.md", "x\ny\n")()
    assert tail.poll() == ["x", "y"]
    tail.close()


def test_module_tail_reads_a_first_log_from_its_start(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    tail = runlog.Tail(runs)
    assert tail.poll() == []

    _logs(runs, s1=[_START])
    assert tail.poll() == ["# Ship run 20261101-100001", "", _START]
    tail.close()


def test_module_tail_reads_a_bounded_span_from_its_offset(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[])
    log = runs / "20261101-100001.md"
    tail = runlog.Tail(runs)
    line = "x" * 1023
    _gain(log, f"{line}\n" * 300)()

    first = tail.poll()
    assert first == [line] * (runlog.BOUND // 1024)
    assert first + tail.poll() == [line] * 300
    assert tail.poll() == []
    tail.close()


def test_module_tail_passes_over_a_line_longer_than_the_bound(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[])
    log = runs / "20261101-100001.md"
    tail = runlog.Tail(runs)
    _gain(log, "y" * (runlog.BOUND * 2 + 10))()

    assert tail.poll() == []
    assert tail.poll() == []
    _gain(log, "y" * 10)()
    assert tail.poll() == []
    _gain(log, "yy\nafter\n")()
    assert tail.poll() == ["after"]
    _gain(log, "z" * runlog.BOUND + "\nnext\n")()
    assert tail.poll() == []
    assert tail.poll() == ["next"]
    tail.close()


def test_module_tail_reads_no_link_and_no_pipe(tmp_path: Path) -> None:
    runs = _logs(tmp_path / "runs", s1=[_START])
    outside = tmp_path / "outside.md"
    outside.write_text(f"{_DONE}\n")
    tail = runlog.Tail(runs)

    (runs / "20261101-100002.md").symlink_to(outside)
    assert tail.poll() == []
    assert tail.fd is None
    os.mkfifo(runs / "20261101-100003.md")
    assert tail.poll() == []
    assert tail.fd is None
    _logs(runs, s4=[_DONE])
    assert tail.poll() == ["# Ship run 20261101-100004", "", _DONE]
    tail.close()


def test_module_tail_keeps_one_descriptor_per_log_and_close_closes_it(
    tmp_path: Path,
) -> None:
    runs = _logs(tmp_path / "runs", s1=[_START])
    tail = runlog.Tail(runs)
    held = tail.fd
    assert held is not None

    _gain(runs / "20261101-100001.md", f"{_DONE}\n")()
    assert tail.poll() == [_DONE]
    assert tail.fd == held
    _logs(runs, s2=[])
    tail.poll()
    assert tail.fd is not None
    assert os.fstat(tail.fd).st_ino == (runs / "20261101-100002.md").stat().st_ino
    last = tail.fd
    tail.close()
    assert tail.fd is None
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(last)
    tail.close()


def test_module_newest_and_the_readers_pass_over_a_name_that_is_no_stamp(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    rescue = "10:00:01 · 0001-a · spawn — rescue · model default"
    for name in ("notes", "20261101-1000", "20261101-100001-a", "x20261101-100001"):
        (runs / f"{name}.md").write_text(f"{_SPAWN}\n{rescue}\n")

    assert runlog.newest(runs) is None
    assert not runlog.release_died(runs, "0001-a")
    assert not runlog.rescuing(runs, "0001-a")
    assert runlog.stop(runs) is None


def test_module_verify_passes_an_open_spawn_under_the_runs_stop_alone(
    tmp_path: Path,
) -> None:
    spawn = "10:00:01 · 0001-a · spawn — build · model default"
    halted = "10:00:02 · 0001-a · halt — build: phase 1 unticked"
    stopped = f"10:00:03 · run · halt — {runlog.STOPPED}"

    assert _verify(tmp_path, _START, spawn, stopped) is None
    assert _verify(tmp_path, _START, spawn, halted) == (
        "a spawn with no finish: 0001-a build"
    )
    assert _verify(tmp_path, _START, spawn, stopped, halted) == (
        "a spawn with no finish: 0001-a build"
    )


def test_module_verify_raises_on_a_link(tmp_path: Path) -> None:
    log = tmp_path / "linked.md"
    (tmp_path / "outside.md").write_text(f"{_START}\n{_DONE}\n")
    log.symlink_to(tmp_path / "outside.md")

    with pytest.raises(OSError, match=r"linked\.md"):
        runlog.verify(log)
