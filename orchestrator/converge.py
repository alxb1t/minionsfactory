"""Converge loop.

Drive blocking findings to clean, or halt at the round cap / a red gate.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Sequence

from orchestrator.findings import FindingsState, all_findings_clean
from orchestrator.gate import Gate
from orchestrator.provider import Profile, Provider
from orchestrator.status import Event, GateStep, RoleReturned, RoleSpawn, _no_emit


class ConvergeStatus(Enum):
    """Terminal status of a converge run.

    The findings reached clean, or the loop halted.
    """

    CONVERGED = auto()
    HALTED = auto()


@dataclass(frozen=True)
class ConvergeResult:
    """Outcome of a converge run.

    How it ended, why, and how many rounds it took.
    """

    status: ConvergeStatus
    reason: str
    rounds: int


def converge(
    provider: Provider,
    gate: Gate,
    repo: Path,
    fixer_prompt: str,
    coder_profile: Profile,
    read_states: Callable[[], Sequence[FindingsState | None]],
    run_verify: Callable[[], None],
    emit_event: Callable[[Event], None] = _no_emit,
    max_rounds: int = 3,
) -> ConvergeResult:
    """Drive blocking findings to clean, or halt at the round cap / a red gate."""
    rounds = 0

    while True:
        states = read_states()

        if all_findings_clean(states):
            return ConvergeResult(ConvergeStatus.CONVERGED, "", rounds)

        if rounds >= max_rounds:
            return ConvergeResult(ConvergeStatus.HALTED, "round cap exceeded", rounds)
        rounds += 1

        emit_event(RoleSpawn(role="coder", ts=datetime.now(timezone.utc)))
        result = provider.run_role(fixer_prompt, repo, coder_profile)
        emit_event(
            RoleReturned(
                role="coder",
                ts=datetime.now(timezone.utc),
                session_id=result.session_id,
                total_cost_usd=result.total_cost_usd,
                is_error=result.is_error,
                summary=result.result,
            )
        )

        gate_result = gate.run_gate(repo)
        emit_event(
            GateStep(
                ts=datetime.now(timezone.utc),
                command="",
                passed=gate_result.passed,
            )
        )

        if not gate_result.passed:
            return ConvergeResult(ConvergeStatus.HALTED, "gate red after fix", rounds)

        run_verify()
