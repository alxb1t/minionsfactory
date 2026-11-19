"""The status log's writer and parser in the home, each function and extent a case.

Why: 0136-status-log design D1, D3, D6 and D13, and its differences.
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
    assert statuslog.mark_of("## Run 3 — d · grant ") == "grant "
    assert statuslog.mark_of("## Run 3 — d · a · b") == "a · b"
    assert statuslog.mark_of("## Run 3 — d") is None


def test_marked_tests_the_end_with_trailing_blanks_dropped() -> None:
    assert statuslog.marked("## Run 4 — d · grant  ", "grant")
    assert not statuslog.marked("## Run 4 — d · catch-up", "grant")
    assert not statuslog.marked("## Run 4 — d · regrant", "grant")


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
    assert parse("10:00:00 · round 1 · done") is None


def test_is_event_tests_the_name_before_the_first_dash() -> None:
    assert statuslog.is_event("10:00:00 · round 1 · done — ok", "done")
    assert statuslog.is_event("10:00:00 · round 1 · done", "done")
    assert not statuslog.is_event("10:00:00 · round 1 · fix — x · done", "done")
    assert not statuslog.is_event("10:00:00 · anything goes", "done")


def test_ends_names_done_or_halt_and_nothing_else() -> None:
    assert statuslog.ends("10:00:00 · round 1 · done — ok") == "done"
    assert statuslog.ends("10:00:00 · round 1 · halt — red") == "halt"
    assert statuslog.ends("10:00:00 · round 1 · predone — x") is None
    assert statuslog.ends("10:00:00 · round 1 · verify — x") is None


@pytest.mark.parametrize(
    ("extent", "lines"),
    [
        ("blank", ["10:00:01 · round 2 · fix — R1", _START]),
        ("heading", ["10:00:01 · round 2 · fix — R1", _START, "stray"]),
        ("line", ["10:00:01 · round 2 · fix — R1"]),
    ],
)
def test_newest_holds_the_lines_its_extent_names(
    extent: statuslog.Extent, lines: list[str]
) -> None:
    assert statuslog.newest(_LOG, extent=extent) == ("## Run 2 — d · catch-up", lines)


@pytest.mark.parametrize(
    ("extent", "lines"),
    [("blank", []), ("heading", []), ("line", ["## Run 1 — d"])],
)
def test_newest_of_a_run_just_opened_over_an_older_one(
    extent: statuslog.Extent, lines: list[str]
) -> None:
    text = "# t\n\n## Run 2 — d\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n"

    assert statuslog.newest(text, extent=extent) == ("## Run 2 — d", lines)


@pytest.mark.parametrize("extent", ["blank", "heading", "line"])
def test_newest_of_no_run_is_none(extent: statuslog.Extent) -> None:
    assert statuslog.newest("# t\n", extent=extent) is None


def test_latest_is_the_runs_mark_and_events_to_a_blank_line() -> None:
    event = statuslog.Event

    assert statuslog.latest(_LOG) == (
        "catch-up",
        [event(2, "fix", "R1"), event(1, "start", "base a")],
    )
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


def test_read_raises_on_a_byte_that_is_not_utf_8(tmp_path: Path) -> None:
    log = tmp_path / "status_log.md"
    log.write_bytes(b"# t \xff\n")

    with pytest.raises(UnicodeDecodeError):
        statuslog.read(log)


def test_stamp_writes_the_lines_and_returns_them(tmp_path: Path) -> None:
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{_START}\n")

    written = statuslog.stamp(log, ["round 1 · verify — ok"], None, None)

    assert written == ["10:02:03 · round 1 · verify — ok"]
    assert log.read_text() == f"# t\n\n## Run 1 — d\n{written[0]}\n{_START}\n"


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


def test_open_run_raises_on_a_link_at_the_log(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("# t\n\n## Run 1 — d\n")
    log = tmp_path / "status_log.md"
    log.symlink_to(outside)

    with pytest.raises(statuslog.Refused, match="is a link"):
        statuslog.open_run(log, _CHANGE)

    assert outside.read_text() == "# t\n\n## Run 1 — d\n"
