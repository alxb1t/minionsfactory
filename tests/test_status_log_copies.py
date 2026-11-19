"""The copies of the status log's writer and readers, side by side as they stand.

The differences 0136-status-log design's pin names beside its cases: a link at the
log, an event outside the spec's form, a missing log, and a multi-line halt.
"""

import importlib.util
import runpy
import types
from datetime import datetime
from pathlib import Path

import pytest
from conduct_load import conduct as _conduct
from mflib import statuslog

_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "mf-converge" / "scripts"
_CHANGE = "0001-a"
_SPEC = importlib.util.spec_from_file_location("copies_stamp", _SCRIPTS / "stamp.py")
assert _SPEC and _SPEC.loader
stamp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(stamp)
converge = runpy.run_path(str(_SCRIPTS / "converge.py"))
conduct = _conduct()
_START = "10:00:00 · round 1 · start — base a"


@pytest.fixture(autouse=True)
def _clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(statuslog, "_now", lambda: datetime(2026, 11, 7, 10, 2, 3))


def _context(primary: Path) -> object:
    host = types.SimpleNamespace(primary=primary)
    return converge["Context"](host, _CHANGE, primary, {}, 1e12)


def _log(primary: Path) -> Path:
    log = primary / ".minions" / "changes" / _CHANGE / "status_log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    return log


def _run_end(primary: Path) -> str | None:
    return conduct["_run_end"](primary / ".minions", _CHANGE)


def test_a_link_at_the_log_is_refused_by_the_stamp_and_converge_and_followed_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path)
    outside = tmp_path / "outside.md"
    text = f"# t\n\n## Run 1 — d\n{_START}\n"
    outside.write_text(text)
    log.symlink_to(outside)

    assert stamp.main([str(log), "round 1 · verify"]) == 2
    assert capsys.readouterr().out == f"stamp: cannot stamp — {log} is a link\n"
    with pytest.raises(statuslog.Refused):
        converge["latest"](_context(tmp_path))
    with pytest.raises(conduct["Stop"], match=r"status_log\.md is a link"):
        _run_end(tmp_path)
    assert outside.read_text() == text


def test_an_event_outside_the_form_is_stamped_skipped_by_converge_and_read_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path)
    log.write_text(f"# t\n\n## Run 1 — d\n{_START}\n")

    assert stamp.main([str(log), "anything goes"]) == 0
    assert capsys.readouterr().out == "10:02:03 · anything goes\n"
    run = converge["latest"](_context(tmp_path))
    assert run == (None, [statuslog.Event(1, "start", "base a")])
    assert _run_end(tmp_path) == "10:02:03 · anything goes"
    assert not conduct["_is_event"]("10:02:03 · anything goes", "done")


def test_a_missing_log_exits_2_in_the_stamp_is_no_event_and_no_run_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path)

    assert stamp.main([str(log), "round 1 · verify"]) == 2
    said = f"stamp: cannot stamp — {log}: No such file or directory\n"
    assert capsys.readouterr().out == said
    assert converge["latest"](_context(tmp_path)) == (None, [])
    assert _run_end(tmp_path) is None
    assert not log.exists()


def test_a_halt_whose_detail_holds_a_line_break_puts_its_head_on_a_later_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _log(tmp_path)
    log.write_text(f"# t\n\n## Run 1 — d\n{_START}\n")
    detail = "git diff failed: fatal: a\nfatal: b · head abc123"

    assert stamp.main([str(log), f"round 1 · halt — {detail}"]) == 0
    capsys.readouterr()

    head = (
        "10:02:03 · round 1 · halt — git diff failed: fatal: a fatal: b · head abc123"
    )
    assert log.read_text().splitlines()[3:5] == [head, _START]
    [top, *_] = converge["latest"](_context(tmp_path)).events
    assert top == (1, "halt", "git diff failed: fatal: a fatal: b · head abc123")
    assert converge["HALTED"].search(top.detail)[1] == "abc123"
    assert _run_end(tmp_path) == head


def test_the_rerun_of_a_halt_whose_git_stderr_held_a_line_break_reads_its_head(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Why: 0136-status-log design D8.
    log = _log(tmp_path)
    log.write_text(f"# t\n\n## Run 1 — d\n{_START}\n")
    stderr = "fatal: bad object\r\nfatal: the remote end hung up\n\n"
    event = f"round 1 · halt — git fetch failed: {stderr} · head abc1234"

    assert statuslog.command(log, [event], None, None) == 0
    capsys.readouterr()

    halt = conduct["_converge_halt"](tmp_path / ".minions", _CHANGE)
    assert halt is not None
    assert "\n" not in halt
    assert conduct["HALT_HEAD"].search(halt)[1] == "abc1234"
