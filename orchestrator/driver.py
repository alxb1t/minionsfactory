"""Build-spine driver: the deterministic loop that advances a plan or halts."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path

from orchestrator.findings import FindingsState
from orchestrator.gate import Gate, GateResult
from orchestrator.provider import Profile, Provider
from orchestrator.state import PlanState, read_plan_state
from orchestrator.status import (
    Advance,
    Event,
    GateStep,
    Halt,
    PhaseStart,
    RoleReturned,
    RoleSpawn,
    RunSummary,
    _no_emit,
)


@dataclass(frozen=True)
class Decision:
    """The driver's verdict for one phase.

    Advance to the next, or halt with a reason.
    """

    advance: bool
    reason: str


def decide(
    before: PlanState,
    after: PlanState,
    gate_result: GateResult,
    coder_halted: bool,
) -> Decision:
    """Decide whether the phase advanced or the driver must halt (and why)."""
    if coder_halted:
        return Decision(advance=False, reason="coder wrote a HALT report")
    if not gate_result.passed:
        return Decision(advance=False, reason="gate is red")
    commited = after.head != before.head
    phase_moved = after.current_phase != before.current_phase
    if not (commited and phase_moved):
        return Decision(
            advance=False,
            reason=(
                "phase did not advance (need a new commit and a moved current_phase)"
            ),
        )
    return Decision(advance=True, reason="")


class RunStatus(Enum):
    """Terminal status of a driver run."""

    COMPLETE = auto()
    HALTED = auto()


@dataclass(frozen=True)
class RunResult:
    """Outcome of a driver run: how it ended, why, and how far it got."""

    status: RunStatus
    reason: str
    phases_advanced: int


def halt_report_exists(vault_project_dir: Path) -> bool:
    """Return whether the coder left a HALT report in the vault."""
    return (vault_project_dir / "HALT.md").exists()


def _plan_complete(state: PlanState) -> bool:
    """Return whether every phase is done (none still planned)."""
    return "planned" not in state.phases.values()


def _no_fanout() -> list[FindingsState | None]:
    """Default post-build stage: do nothing (a build-only run is valid)."""
    return []


def run(
    repo: Path,
    vault_project_dir: Path,
    provider: Provider,
    gate: Gate,
    coder_prompt: str,
    profile: Profile,
    state_reader: Callable[[Path, Path], PlanState] = read_plan_state,
    halt_checker: Callable[[Path], bool] = halt_report_exists,
    emit_event: Callable[[Event], None] = _no_emit,
    fanout: Callable[[], list[FindingsState | None]] = _no_fanout,
    max_phases: int = 100,
) -> RunResult:
    """Drive the plan phase by phase.

    Spawn coder -> gate -> detect advance -> continue or halt.
    """
    before = state_reader(vault_project_dir, repo)
    advanced = 0
    iterations = 0
    while not _plan_complete(before):
        if iterations >= max_phases:
            reason = "exceeded max phases (runaway guard)"
            emit_event(
                Halt(
                    ts=datetime.now(timezone.utc),
                    reason=reason,
                )
            )
            emit_event(
                RunSummary(
                    ts=datetime.now(timezone.utc),
                    status="halted",
                    phases_advanced=advanced,
                    reason=reason,
                )
            )
            return RunResult(RunStatus.HALTED, reason, advanced)

        emit_event(
            PhaseStart(ts=datetime.now(timezone.utc), phase=before.current_phase)
        )
        iterations += 1

        emit_event(
            RoleSpawn(
                role="coder",
                ts=datetime.now(timezone.utc),
            )
        )
        result = provider.run_role(coder_prompt, repo, profile)
        emit_event(
            RoleReturned(
                role="coder",
                ts=datetime.now(timezone.utc),
                session_id=result.session_id,
                total_cost_usd=result.total_cost_usd,
                is_error=result.is_error,
            )
        )

        coder_halted = halt_checker(vault_project_dir)

        gate_result = gate.run_gate(repo)
        for step in gate_result.steps:
            emit_event(
                GateStep(
                    ts=datetime.now(timezone.utc),
                    command=step.command,
                    passed=step.exit_code == 0,
                )
            )

        after = state_reader(vault_project_dir, repo)
        decision = decide(before, after, gate_result, coder_halted)

        if not decision.advance:
            emit_event(Halt(ts=datetime.now(timezone.utc), reason=decision.reason))
            emit_event(
                RunSummary(
                    ts=datetime.now(timezone.utc),
                    status="halted",
                    phases_advanced=advanced,
                    reason=decision.reason,
                )
            )
            return RunResult(RunStatus.HALTED, decision.reason, advanced)

        advanced += 1
        emit_event(
            Advance(
                ts=datetime.now(timezone.utc),
                from_phase=before.current_phase,
                to_phase=after.current_phase,
            ),
        )
        before = after

    fanout()

    emit_event(
        RunSummary(
            ts=datetime.now(timezone.utc),
            status="complete",
            phases_advanced=advanced,
            reason="",
        )
    )
    return RunResult(RunStatus.COMPLETE, "", advanced)
