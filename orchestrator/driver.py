"""Build-spine driver: the deterministic loop that advances a plan or halts."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from orchestrator.gate import Gate, GateResult
from orchestrator.provider import Profile, Provider
from orchestrator.state import PlanState, read_plan_state


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


def run(
    repo: Path,
    vault_project_dir: Path,
    provider: Provider,
    gate: Gate,
    coder_prompt: str,
    profile: Profile,
    state_reader: Callable[[Path, Path], PlanState] = read_plan_state,
    halt_checker: Callable[[Path], bool] = halt_report_exists,
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
            return RunResult(
                RunStatus.HALTED,
                "exceeded max phases (runaway guard)",
                advanced,
            )
        iterations += 1
        provider.run_role(coder_prompt, repo, profile)
        coder_halted = halt_checker(vault_project_dir)
        gate_result = gate.run_gate(repo)
        after = state_reader(vault_project_dir, repo)
        decision = decide(before, after, gate_result, coder_halted)
        if not decision.advance:
            return RunResult(RunStatus.HALTED, decision.reason, advanced)
        advanced += 1
        before = after
    return RunResult(RunStatus.COMPLETE, "", advanced)
