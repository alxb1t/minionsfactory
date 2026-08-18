"""Status stream: events round-trip through disk as their typed variants."""

from datetime import datetime, timezone
from pathlib import Path

from orchestrator.status import (
    Advance,
    GateStep,
    Halt,
    PhaseStart,
    RoleReturned,
    RoleSpawn,
    RunSummary,
    append_event,
    emit,
    is_in_progress,
    read_events,
    read_status,
    render,
)


def test_appended_event_reads_back_as_its_typed_variant(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=False,
    )

    append_event(stream, event)

    assert read_events(stream) == [event]


def test_status_json_reflects_the_latest_event(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    status = tmp_path / "status.json"
    first = PhaseStart(ts=datetime.now(timezone.utc), phase="P1")
    second = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=False,
    )

    emit(stream, status, first)
    emit(stream, status, second)

    assert read_status(status) == second


def test_render_formats_a_phase_start_line() -> None:
    event = PhaseStart(ts=datetime.now(timezone.utc), phase="P1")
    assert render(event) == "▶ phase P1 — building"


def test_render_formats_a_coder_result_no_error_line() -> None:
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=False,
    )
    assert render(event) == "  coder returned (ok, $0.12)"


def test_render_formats_a_coder_result_error_line() -> None:
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=True,
    )
    assert render(event) == "  coder returned (error, $0.12)"


def test_render_formats_a_coder_spawn_in_progress_line() -> None:
    event = RoleSpawn(role="coder", ts=datetime.now(timezone.utc))
    assert render(event) == "  coder spawned — running…"


def test_snapshot_reads_in_progress_after_a_spawn(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    status = tmp_path / "status.json"
    emit(stream, status, RoleSpawn(role="coder", ts=datetime.now(timezone.utc)))
    assert is_in_progress(status) is True


def test_snapshot_reads_done_after_the_result_lands(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    status = tmp_path / "status.json"
    emit(stream, status, RoleSpawn(role="coder", ts=datetime.now(timezone.utc)))
    emit(
        stream,
        status,
        RoleReturned(
            role="coder",
            ts=datetime.now(timezone.utc),
            session_id="abc",
            total_cost_usd=0.12,
            is_error=True,
        ),
    )
    assert is_in_progress(status) is False


def test_render_formats_an_advance_line() -> None:
    event = Advance(ts=datetime.now(timezone.utc), from_phase="P1", to_phase="P2")
    assert render(event) == "Advanced P1 -> P2"


def test_render_formats_a_halt_line() -> None:
    event = Halt(ts=datetime.now(timezone.utc), reason="gate is red")
    assert render(event) == "halted: gate is red"


def test_render_shows_a_failed_gate_step() -> None:
    event = GateStep(
        ts=datetime.now(timezone.utc),
        command="pytest",
        passed=False,
    )
    assert render(event) == "  gate: pytest ✗"


def test_render_shows_a_passed_gate_step() -> None:
    event = GateStep(
        ts=datetime.now(timezone.utc),
        command="pytest",
        passed=True,
    )
    assert render(event) == "  gate: pytest ✓"


def test_render_formats_a_run_summary_line() -> None:
    event = RunSummary(
        ts=datetime.now(timezone.utc), status="complete", phases_advanced=2, reason=""
    )
    assert render(event) == "■ complete — 2 phase(s) advanced"
