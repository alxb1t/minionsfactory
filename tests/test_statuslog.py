"""The status log's writer and parser in the home, each function a case.

Why: 0136-status-log design D1, D6, D7, D8 and D13.
"""

import os
from datetime import datetime
from pathlib import Path

import pytest
from mflib import statefile, statuslog

_CHANGE = "0001-a"
_NOW = datetime(2026, 11, 7, 10, 2, 3)
_START = "10:00:00 · round 1 · start — base a"
# The newest run: two events, a blank line, a stray line, then an older run.
_LOG = (
    "# t\n\n## Run 2 — d · catch-up\n10:00:01 · round 2 · fix — R1\n"
    f"{_START}\n\nstray\n## Run 1 — d\n10:00:00 · round 1 · halt — old\n"
)


@pytest.fixture(autouse=True)
def _clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(statuslog, "_now", lambda: _NOW)


def _log(tmp_path: Path, text: str) -> Path:
    log = tmp_path / "status_log.md"
    log.write_text(text)
    return log


def test_names_are_the_specs_event_names_in_its_order() -> None:
    assert list(statuslog.NAMES) == [
        "start",
        "freeze",
        "fan-out",
        "verdicts",
        "shadow",
        "fix",
        "verify",
        "pickup",
        "catch-up",
        "by rule",
        "debt",
        "halt",
        "done",
    ]


def test_the_clock_is_the_local_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.undo()
    before = datetime.now()

    assert before <= statuslog._now() <= datetime.now()


def test_title_names_the_change() -> None:
    assert statuslog.title(_CHANGE) == "# 0001-a — converge status"


def test_create_writes_the_title_and_leaves_a_log_that_stands(tmp_path: Path) -> None:
    log = tmp_path / "status_log.md"

    statuslog.create(log, _CHANGE)
    assert log.read_text() == "# 0001-a — converge status\n"

    log.write_text("# kept\n")
    statuslog.create(log, _CHANGE)
    assert log.read_text() == "# kept\n"


def test_heading_takes_the_number_the_time_and_a_mark() -> None:
    assert statuslog.heading(4, _NOW, None) == "## Run 4 — 2026-11-07 10:02"
    assert statuslog.heading(4, _NOW, "grant") == "## Run 4 — 2026-11-07 10:02 · grant"


def test_mark_of_takes_the_text_after_the_first_dot_as_it_stands() -> None:
    assert statuslog.mark_of("## Run 3 — d · catch-up") == "catch-up"
    assert statuslog.mark_of("## Run 3 — d · grant ") == "grant"
    assert statuslog.mark_of("## Run 3 — d · a · b") == "a · b"
    assert statuslog.mark_of("## Run 3 — d") is None
    assert statuslog.mark_of("## Run 3 — d ·  ") is None


def test_marked_tests_the_end_with_trailing_blanks_dropped() -> None:
    assert statuslog.marked("## Run 4 — d · grant  ", "grant")
    assert not statuslog.marked("## Run 4 — d · catch-up", "grant")
    assert not statuslog.marked("## Run 4 — d · regrant", "grant")
    assert not statuslog.marked("## Run 4 — d · grant · x", "grant")


def test_is_heading_tests_the_run_prefix() -> None:
    assert statuslog.is_heading("## Run 1 — d")
    assert not statuslog.is_heading("# t")
    assert not statuslog.is_heading(" ## Run 1")


def test_parse_event_needs_a_round_and_a_dash() -> None:
    parse, event = statuslog.parse_event, statuslog.Event
    assert parse("10:00:00 · round 12 · verify — ") == event(12, "verify", "")
    assert parse("10:00:00 · round 1 · by rule — R1") == event(1, "by rule", "R1")
    assert parse("10:00:00 · round 1 · start — a — b") == event(1, "start", "a — b")
    assert parse("10:00:00 · anything goes") is None
    assert parse("10:00:00 · round 1 · done") == event(1, "done", "")
    assert parse("  10:00:00 · round 1 · halt — x  ") == event(1, "halt", "x")


def test_is_event_tests_the_name_before_the_first_dash() -> None:
    assert statuslog.is_event("10:00:00 · round 1 · done — ok", "done")
    assert statuslog.is_event("10:00:00 · round 1 · done", "done")
    assert not statuslog.is_event("10:00:00 · round 1 · fix — x · done", "done")
    assert not statuslog.is_event("10:00:00 · anything goes", "done")
    assert not statuslog.is_event("10:00:00 · round 1 · halt — a · done — b", "done")
    assert not statuslog.is_event("10:00:00 · done — ok", "done")


def test_ends_names_done_or_halt_and_nothing_else() -> None:
    assert statuslog.ends("10:00:00 · round 1 · done — ok") == "done"
    assert statuslog.ends("10:00:00 · round 1 · halt — red") == "halt"
    assert statuslog.ends("10:00:00 · round 1 · predone — x") is None
    assert statuslog.ends("10:00:00 · round 1 · verify — x") is None


def test_newest_holds_the_lines_its_extent_names() -> None:
    lines = ["10:00:01 · round 2 · fix — R1", _START, "stray"]

    assert statuslog.newest(_LOG) == ("## Run 2 — d · catch-up", lines)


def test_newest_of_a_run_just_opened_over_an_older_one() -> None:
    text = "# t\n\n## Run 2 — d\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n"

    assert statuslog.newest(text) == ("## Run 2 — d", [])


def test_newest_of_no_run_is_none() -> None:
    assert statuslog.newest("# t\n") is None


def test_latest_is_the_runs_mark_and_events_to_a_blank_line() -> None:
    event = statuslog.Event

    assert statuslog.latest(_LOG) == (
        "catch-up",
        [event(2, "fix", "R1"), event(1, "start", "base a")],
    )
    past = "# t\n\n## Run 1 — d\n10:00:01 · round 1 · fix — R1\n\n" + _START
    assert statuslog.latest(past).events[1] == event(1, "start", "base a")
    assert statuslog.latest("# t\n\n## Run 1 — d\nstray\n") == (None, [])
    assert statuslog.latest("# t\n") == (None, [])


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("halt — waited for .minions/debt.lock", True),
        ("halt — waited for .minions/backlog.lock", True),
        ("halt — waited for debt.lock", False),
    ],
    ids=["debt-lock", "backlog-lock", "bare"],
)
def test_names_lock_needs_the_run_folder(text: str, names: bool) -> None:
    assert statuslog.names_lock(text) == names


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("converge-conformance-r1 worker exit 1 · head abc1234", True),
        ("converge-fix-r2 worker exit -9", True),
        ("converge-fix-r1 timed out after 3600s; its group was killed", True),
        ("the gate is red before round 1: gate_run.py exit 2", False),
        ("converge-fix-r1 worker exit", False),
        ("cap reached, R1 open · head abc1234", False),
    ],
    ids=["exit", "signal", "timeout", "gate", "no-code", "cap"],
)
def test_names_worker_reads_a_workers_halt(text: str, names: bool) -> None:
    assert statuslog.names_worker(text) == names


def test_insert_opens_a_run_under_the_title() -> None:
    lines, written = statuslog.insert("# t\n\n\n## Run 1 — d\n", [], 2, "grant")

    heading = "## Run 2 — 2026-11-07 10:02 · grant"
    assert written == [heading]
    assert lines == ["# t", "", heading, "", "## Run 1 — d"]
    assert statuslog.insert("# t\n", [], 1, None)[0] == [
        "# t",
        "",
        "## Run 1 — 2026-11-07 10:02",
    ]


@pytest.mark.parametrize("text", ["", "no title\n"])
def test_insert_refuses_a_run_with_no_title(text: str) -> None:
    with pytest.raises(statuslog.Refused, match="no # title"):
        statuslog.insert(text, [], 1, None)


def test_insert_puts_the_events_on_top_the_last_given_on_top() -> None:
    lines, written = statuslog.insert(
        f"# t\n\n## Run 1 — d\n{_START}\n",
        ["round 1 · freeze — a", "round 1 · fix"],
        None,
        None,
    )

    assert written == ["10:02:03 · round 1 · freeze — a", "10:02:03 · round 1 · fix"]
    assert lines[2:] == ["## Run 1 — d", written[1], written[0], _START]


@pytest.mark.parametrize(
    ("text", "events", "reason"),
    [
        ("# t\n", ["round 1 · start"], "no ## Run heading"),
        (
            "# t\n\n## Run 1 — d\n",
            ["round 1 · done — ok", "round 1 · fix"],
            "done goes last in a call",
        ),
        (
            "# t\n\n## Run 1 — d\n\n10:00:00 · round 1 · done — ok\n",
            ["round 2 · start"],
            "the run ends on done: open a ## Run for a new event",
        ),
        (
            "# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — .minions/debt.lock\n",
            ["round 2 · start"],
            "the run ends on done: open a ## Run for a new event",
        ),
        (
            "# t\n\n## Run 1 — d\n10:00:00 · round 1 · halt — red\n",
            ["round 2 · start"],
            "the run ends on halt: open a ## Run for a new event",
        ),
    ],
    ids=["no-heading", "done-first", "done-past-a-blank", "done-naming-lock", "halt"],
)
def test_insert_refuses(text: str, events: list[str], reason: str) -> None:
    with pytest.raises(statuslog.Refused) as refused:
        statuslog.insert(text, events, None, None)

    assert str(refused.value) == reason


@pytest.mark.parametrize(
    "top",
    [
        "10:00:00 · round 1 · halt — waited for .minions/debt.lock",
        "10:00:00 · round 1 · predone — x",
    ],
    ids=["halt-naming-lock", "predone"],
)
def test_insert_takes_an_event_over_a_top_that_ends_no_run(top: str) -> None:
    _, written = statuslog.insert(
        f"# t\n\n## Run 1 — d\n{top}\n", ["round 1 · start"], None, None
    )

    assert written == ["10:02:03 · round 1 · start"]


def test_read_refuses_a_link_and_a_missing_log(tmp_path: Path) -> None:
    log = tmp_path / "status_log.md"
    with pytest.raises(statuslog.Refused) as missing:
        statuslog.read(log)
    assert str(missing.value) == f"{log}: No such file or directory"

    (tmp_path / "outside").write_text("# t\n")
    log.symlink_to(tmp_path / "outside")
    with pytest.raises(statuslog.Refused) as linked:
        statuslog.read(log)
    assert str(linked.value) == f"{log} is a link"


def test_read_raises_on_a_byte_that_is_not_utf_8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "status_log.md"
    log.write_bytes(b"# t \xff\n\n## Run 1 - d\n")

    assert statuslog.read(log) == "# t �\n\n## Run 1 - d\n"
    with pytest.raises(statuslog.Refused, match="holds a byte that is not UTF-8"):
        statuslog.stamp(log, ["round 1 · verify"], None, None)
    assert statuslog.command(log, ["round 1 · verify"], None, None) == 2
    said = f"stamp: cannot stamp — {log} holds a byte that is not UTF-8\n"
    assert capsys.readouterr().out == said
    assert log.read_bytes() == b"# t \xff\n\n## Run 1 - d\n"


def test_stamp_writes_the_lines_and_returns_them(tmp_path: Path) -> None:
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{_START}\n")

    written = statuslog.stamp(log, ["round 1 · verify — ok"], None, None)

    assert written == ["10:02:03 · round 1 · verify — ok"]
    assert log.read_text() == f"# t\n\n## Run 1 — d\n{written[0]}\n{_START}\n"


def test_stamp_flattens_each_run_of_line_breaks_to_one_space(tmp_path: Path) -> None:
    # Why: 0136-status-log design D8.
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{_START}\n")

    written = statuslog.stamp(log, ["round 1 · halt — a\nb\r\n\nc"], None, None)

    assert written == ["10:02:03 · round 1 · halt — a b c"]
    assert log.read_text().splitlines()[3:] == [written[0], _START]


def test_stamp_words_a_create_that_fails(tmp_path: Path) -> None:
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{_START}\n")
    (tmp_path / "status_log.md.tmp").mkdir()

    with pytest.raises(statuslog.Refused) as refused:
        statuslog.stamp(log, ["round 1 · verify"], None, None)

    assert str(refused.value) == "status_log.md.tmp could not be created"
    assert (tmp_path / "status_log.md.tmp").is_dir()


def test_stamp_words_a_rename_that_fails_and_removes_the_staged_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = f"# t\n\n## Run 1 — d\n{_START}\n"
    log = _log(tmp_path, text)

    def refusing(*_: object, **__: object) -> None:
        raise PermissionError(1, "refused")

    monkeypatch.setattr(statefile.os, "replace", refusing)

    with pytest.raises(statuslog.Refused) as refused:
        statuslog.stamp(log, ["round 1 · verify"], None, None)

    monkeypatch.undo()
    assert str(refused.value) == "status_log.md could not be replaced"
    assert log.read_text() == text
    assert not os.path.lexists(tmp_path / "status_log.md.tmp")


def test_command_prints_each_line_written_and_exits_0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{_START}\n")

    assert (
        statuslog.command(log, ["round 1 · fix — a", "round 1 · fix — b"], None, None)
        == 0
    )

    assert capsys.readouterr().out == (
        "10:02:03 · round 1 · fix — a\n10:02:03 · round 1 · fix — b\n"
    )


def test_command_prints_a_refusal_and_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path, "# t\n")

    assert statuslog.command(log, ["round 1 · start"], None, None) == 2

    assert capsys.readouterr().out == "stamp: cannot stamp — no ## Run heading\n"
    assert log.read_text() == "# t\n"


def test_open_run_makes_the_folder_and_the_log(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "changes" / _CHANGE / "status_log.md"

    assert statuslog.open_run(log, _CHANGE) == 0

    heading = "## Run 1 — 2026-11-07 10:02"
    assert log.read_text() == f"# 0001-a — converge status\n\n{heading}\n"
    assert capsys.readouterr().out == f"{heading}\n"


def test_open_run_counts_the_runs_by_their_heading_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(
        tmp_path, "# t\n\n## Run 1 — d\n10:00:00 · round 1 · halt — x ## Run 7\n"
    )

    assert statuslog.open_run(log, _CHANGE, "amend") == 0

    assert capsys.readouterr().out == "## Run 2 — 2026-11-07 10:02 · amend\n"


@pytest.mark.parametrize("given", [True, False], ids=["folder-given", "folder-opened"])
def test_card_0109_s1_a_change_folder_swapped_after_the_read_is_not_followed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    given: bool,
) -> None:
    # Why: card 0109·S1; 0136-status-log design D7.
    run_dir = tmp_path / ".minions"
    log = run_dir / "changes" / _CHANGE / "status_log.md"
    log.parent.mkdir(parents=True)
    log.write_text(f"# t\n\n## Run 1 — d\n{_START}\n")
    outside, moved = tmp_path / "outside", tmp_path / "moved"
    outside.mkdir()
    (outside / "status_log.md").write_text("the person's\n")
    real = statuslog.insert

    def swapping(
        text: str, events: list[str], run: int | None, mark: str | None
    ) -> tuple[list[str], list[str]]:
        log.parent.rename(moved)
        log.parent.symlink_to(outside)
        return real(text, events, run, mark)

    monkeypatch.setattr(statuslog, "insert", swapping)
    fd = statefile.folder(run_dir, "changes", _CHANGE) if given else None
    try:
        assert statuslog.command(log, ["round 1 · verify"], None, None, fd) == 0
    finally:
        if fd is not None:
            os.close(fd)

    capsys.readouterr()
    assert (outside / "status_log.md").read_text() == "the person's\n"
    assert sorted(path.name for path in outside.iterdir()) == ["status_log.md"]
    assert "10:02:03 · round 1 · verify" in (moved / "status_log.md").read_text()


def test_a_missing_log_folder_keeps_the_missing_log_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "gone" / "status_log.md"

    assert statuslog.command(log, ["round 1 · verify"], None, None) == 2

    said = f"stamp: cannot stamp — {log}: No such file or directory\n"
    assert capsys.readouterr().out == said
    assert not log.parent.exists()


def test_open_run_raises_on_a_link_at_the_log(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("# t\n\n## Run 1 — d\n")
    log = tmp_path / "status_log.md"
    log.symlink_to(outside)

    with pytest.raises(statuslog.Refused, match="is a link"):
        statuslog.open_run(log, _CHANGE)

    assert outside.read_text() == "# t\n\n## Run 1 — d\n"


def test_runs_give_each_run_newest_first() -> None:
    found = statuslog.runs(_LOG)

    assert [(run.number, run.mark) for run in found] == [(2, "catch-up"), (1, None)]
    assert found[0].events == [
        statuslog.Event(2, "fix", "R1"),
        statuslog.Event(1, "start", "base a"),
    ]
    assert found[1].events == [statuslog.Event(1, "halt", "old")]
    assert statuslog.runs("# t\n10:00:00 · round 1 · start\n") == []
    latest = statuslog.latest(_LOG)
    assert (found[0].mark, found[0].events) == (latest.mark, latest.events)


def test_runs_read_running_as_a_heading_with_no_number() -> None:
    text = (
        "# t\n\n## Running\n10:00:02 · round 3 · done\n"
        "## Run 12 — d · a · b\n10:00:01 · round 2 · fix — R1\n"
        "## Run ٣ — d\n## Run x\n"
    )

    found = statuslog.runs(text)

    assert [(run.number, run.mark) for run in found] == [
        (None, None),
        (12, "a · b"),
        (None, None),
        (None, None),
    ]
    assert found[0].events == [statuslog.Event(3, "done", "")]
    assert found[1].events == [statuslog.Event(2, "fix", "R1")]


def test_spent_words_a_string_fallback_as_failed() -> None:
    models = ("claude", None, "high")

    assert statuslog.spent(models, 1200, False) == (
        "executor claude · model default · effort high · tokens 1200"
    )
    assert statuslog.spent(("codex", "m", None), 0, False).endswith(
        "effort default · tokens 0"
    )
    assert statuslog.spent(models, None, False).endswith("tokens unavailable")
    assert statuslog.spent(models, 5, True).endswith(f"tokens 5 · {statuslog.FALLBACK}")
    assert statuslog.spent(models, 5, "").endswith(f"tokens 5 · {statuslog.FAILED}")
    assert statuslog.spent(models, 5, "limit").endswith(
        f"tokens 5 · {statuslog.FAILED}"
    )
    assert statuslog.FALLBACK == "fallback: codex usage limit"
    assert statuslog.FAILED == "fallback: codex failed"


def test_verdicts_read_a_line_the_writer_wrote() -> None:
    spent = statuslog.spent(("codex", "gpt-6.1-sol-x", None), 1200, True)
    text = statuslog.verdicts_line("adversarial", "clean", 0, spent)

    assert text == (
        "verdicts — adversarial clean · open_blocking 0 · executor codex"
        " · model gpt-6.1-sol-x · effort default · tokens 1200"
        f" · {statuslog.FALLBACK}"
    )
    event = statuslog.parse_event(f"10:00:00 · round 1 · {text}")
    assert event is not None
    assert statuslog.verdicts(event) == statuslog.Verdicts(
        "adversarial", "codex", "gpt-6.1-sol-x", "default", 1200, True
    )


def _verdicts(detail: str, name: str = "verdicts") -> statuslog.Verdicts | None:
    return statuslog.verdicts(statuslog.Event(1, name, detail))


def test_verdicts_read_an_event_of_the_modules_form() -> None:
    plain = "conformance clean · open_blocking 10 · tokens 5"
    assert _verdicts(plain) == statuslog.Verdicts(
        "conformance", None, None, None, 5, False
    )
    found = _verdicts(
        f"adversarial x · open_blocking 0 · tokens 5 · {statuslog.FAILED}"
    )
    assert found is not None
    assert found.fallback
    found = _verdicts(f"adversarial x · open_blocking 0 · tokens 5 {statuslog.FAILED}")
    assert found is not None
    assert not found.fallback
    early = (
        f"{statuslog.FAILED} · verdicts — adversarial x · open_blocking 0 · tokens 5"
    )
    assert statuslog.parse_event(f"10:00:00 · round 1 · {early}") is None
    found = _verdicts("conformance executor · open_blocking 0 · tokens 5")
    assert found is not None
    assert (found.executor, found.tokens) == (None, 5)
    found = _verdicts("conformance clean · open_blocking 0 · tokens ٣")
    assert found is not None
    assert found.tokens is None
    assert _verdicts("other clean · open_blocking 0 · x") is None
    assert _verdicts("conformance clean · open_blocking 0 · tokens 5", "fix") is None
    assert _verdicts("x verdicts — conformance clean · open_blocking 0 · y") is None
