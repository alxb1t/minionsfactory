from collections.abc import Callable
from pathlib import Path

from orchestrator.converge import ConvergeResult, ConvergeStatus
from orchestrator.driver import RunStatus, decide, run
from orchestrator.findings import FindingsState
from orchestrator.gate import FakeGate, GateResult
from orchestrator.provider import FakeProvider, Profile, RoleResult
from orchestrator.state import PlanState
from orchestrator.status import Event, RunSummary

_GREEN = GateResult(passed=True, steps=())
_RED = GateResult(passed=False, steps=())
_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)


def _reader(states: list[PlanState]) -> Callable[[Path, Path], PlanState]:
    iterator = iter(states)

    def read(vault_project_dir: Path, repo: Path) -> PlanState:
        return next(iterator)

    return read


def _never_halts(vault_project_dir: Path) -> bool:
    return False


def _always_halts(vault_project_dir: Path) -> bool:
    return True


def _state(current_phase: str, head: str) -> PlanState:
    return PlanState(current_phase=current_phase, phases={}, head=head)


def test_decide_advances_on_green_gate_with_new_commit_and_moved_phase() -> None:
    decision = decide(
        _state("P1", "aaa"), _state("P2", "bbb"), _GREEN, coder_halted=False
    )
    assert decision.advance is True


def test_decide_halts_when_the_coder_wrote_a_halt_report() -> None:
    decision = decide(
        _state("P1", "aaa"), _state("P2", "bbb"), _GREEN, coder_halted=True
    )
    assert decision.advance is False
    assert "halt" in decision.reason.lower()


def test_decide_halts_on_a_red_gate() -> None:
    decision = decide(
        _state("P1", "aaa"), _state("P2", "bbb"), _RED, coder_halted=False
    )
    assert decision.advance is False
    assert "gate" in decision.reason.lower()


def test_decide_halts_when_the_phase_did_not_advance() -> None:
    # gate green, but current_phase and head are unchanged
    # → the coder didn't really finish the phase
    decision = decide(
        _state("P1", "aaa"), _state("P1", "aaa"), _GREEN, coder_halted=False
    )
    assert decision.advance is False


def test_run_advances_through_phases_until_the_plan_is_complete() -> None:
    states = [
        PlanState("P1", {"phase0": "planned", "phase1": "planned"}, "c0"),
        PlanState("P2", {"phase0": "done", "phase1": "planned"}, "c1"),
        PlanState("done", {"phase0": "done", "phase1": "done"}, "c2"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.COMPLETE
    assert result.phases_advanced == 2


def test_run_halts_when_the_gate_is_red() -> None:
    states = [
        PlanState("P1", {"phase0": "planned"}, "c0"),
        PlanState("P2", {"phase0": "done"}, "c1"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(GateResult(passed=False, steps=())),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.HALTED
    assert "gate" in result.reason.lower()
    assert result.phases_advanced == 0


def test_run_halts_when_the_coder_writes_a_halt_report() -> None:
    states = [
        PlanState("P1", {"phase0": "planned"}, "c0"),
        PlanState("P1", {"phase0": "planned"}, "c0"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_always_halts,
    )
    assert result.status is RunStatus.HALTED
    assert "halt" in result.reason.lower()


def test_run_resumes_from_the_current_phase_on_disk() -> None:
    # phase0 already done on disk; the run picks up at phase1 and finishes.
    states = [
        PlanState("P2", {"phase0": "done", "phase1": "planned"}, "c1"),
        PlanState("done", {"phase0": "done", "phase1": "done"}, "c2"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.COMPLETE
    assert result.phases_advanced == 1


def test_run_emits_the_event_stream_for_an_advancing_phase() -> None:
    states = [
        PlanState("P1", {"phase0": "planned"}, "c0"),
        PlanState("done", {"phase0": "done"}, "c1"),
    ]
    events: list[Event] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        emit_event=events.append,
    )
    assert [e.kind for e in events] == [
        "phase-start",
        "role-spawn",
        "role-returned",
        "advance",
        "run-summary",
    ]


def test_run_emits_a_complete_summary_when_the_plan_is_already_done() -> None:
    states = [PlanState("done", {"phase0": "done"}, "c0")]
    events: list[Event] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        emit_event=events.append,
    )
    assert [e.kind for e in events] == ["run-summary"]
    summary = events[-1]
    assert isinstance(summary, RunSummary)
    assert summary.status == "complete"


def test_run_triggers_fanout_when_the_plan_completes() -> None:
    states = [PlanState("done", {"phase0": "done"}, "c0")]
    calls: list[int] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: calls.append(1) or [],
    )
    assert calls == [1]


def test_run_does_not_fan_out_when_the_build_halts() -> None:
    states = [
        PlanState("P1", {"phase0": "planned"}, "c0"),
        PlanState("P1", {"phase0": "planned"}, "c0"),
    ]
    calls: list[int] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: calls.append(1) or [],
    )
    assert calls == []


def test_run_converges_after_fanout_when_the_plan_completes() -> None:
    states = [PlanState("done", {"phase0": "done"}, "c0")]
    order: list[str] = []

    def fake_fanout() -> list[FindingsState | None]:
        order.append("fanout")
        return []

    def fake_converge() -> ConvergeResult:
        order.append("converge")
        return ConvergeResult(ConvergeStatus.CONVERGED, "", 1)

    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=fake_fanout,
        converge=fake_converge,
    )
    assert order == ["fanout", "converge"]
    assert result.status is RunStatus.COMPLETE


def test_run_halts_when_converge_halts() -> None:
    states = [PlanState("done", {"phase0": "done"}, "c0")]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: [],
        converge=lambda: ConvergeResult(ConvergeStatus.HALTED, "round cap exceeded", 3),
    )
    assert result.status is RunStatus.HALTED
    assert "round cap" in result.reason
