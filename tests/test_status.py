"""Status stream: events round-trip through disk as their typed variants."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

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


@pytest.mark.spec("status:stream:append-reads-back-typed")
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


@pytest.mark.spec("status:stream:snapshot-reflects-latest")
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


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_phase_start_line() -> None:
    event = PhaseStart(ts=datetime.now(timezone.utc), phase="P1")
    assert render(event) == "▶ building P1"


@pytest.mark.spec("status:render:trims-verbose-phase")
def test_render_trims_a_verbose_phase_for_the_cli() -> None:
    verbose = "🚧 P3 in progress — " + "some long detail " * 20
    line = render(PhaseStart(ts=datetime.now(timezone.utc), phase=verbose))
    assert line.startswith("▶ building")
    assert "P3" in line
    assert len(line) < 95  # trimmed, not the full ~350-char phase string


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_coder_result_no_error_line() -> None:
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=False,
    )
    assert render(event) == "  coder returned (ok, $0.12)"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_coder_result_error_line() -> None:
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="abc",
        total_cost_usd=0.12,
        is_error=True,
    )
    assert render(event) == "  coder returned (error, $0.12)"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_coder_spawn_in_progress_line() -> None:
    event = RoleSpawn(role="coder", ts=datetime.now(timezone.utc))
    assert render(event) == "  coder spawned — running…"


@pytest.mark.spec("status:stream:in-progress-after-spawn")
def test_snapshot_reads_in_progress_after_a_spawn(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    status = tmp_path / "status.json"
    emit(stream, status, RoleSpawn(role="coder", ts=datetime.now(timezone.utc)))
    assert is_in_progress(status) is True


@pytest.mark.spec("status:stream:done-after-result")
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


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_an_advance_line() -> None:
    event = Advance(ts=datetime.now(timezone.utc), from_phase="P1", to_phase="P2")
    assert render(event) == "✅ phase done → advanced to P2"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_halt_line() -> None:
    event = Halt(ts=datetime.now(timezone.utc), reason="gate is red")
    assert render(event) == "⛔ halted: gate is red"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_shows_a_failed_gate_step() -> None:
    event = GateStep(
        ts=datetime.now(timezone.utc),
        command="pytest",
        passed=False,
    )
    assert render(event) == "  gate: pytest ✗"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_shows_a_passed_gate_step() -> None:
    event = GateStep(
        ts=datetime.now(timezone.utc),
        command="pytest",
        passed=True,
    )
    assert render(event) == "  gate: pytest ✓"


@pytest.mark.spec("status:render:formats-each-event")
def test_render_formats_a_run_summary_line() -> None:
    event = RunSummary(
        ts=datetime.now(timezone.utc), status="complete", phases_advanced=2, reason=""
    )
    assert render(event) == "■ complete — 2 phase(s) advanced"


@pytest.mark.spec("status:render:surfaces-role-summary")
def test_render_surfaces_the_role_summary_when_present() -> None:
    event = RoleReturned(
        role="coder",
        ts=datetime.now(timezone.utc),
        session_id="s",
        total_cost_usd=2.11,
        is_error=False,
        summary="Halted — stop-condition #5: the plan contradicts reality.",
    )
    line = render(event)
    assert "coder returned (ok, $2.11)" in line
    assert "stop-condition #5" in line  # the reason is surfaced, not hidden
