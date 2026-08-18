"""End-of-plan fan-out: run review ‖ security ‖ simplify.

Read-only over the frozen diff.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.diff import run_role_with_diff
from orchestrator.findings import FindingsState, read_findings_state
from orchestrator.provider import Provider, read_only_profile
from orchestrator.status import Event, Role, RoleReturned, RoleSpawn, _no_emit


@dataclass(frozen=True)
class RoleSpec:
    """One fan-out role: its name (→ findings filename) and its prompt."""

    name: Role
    prompt: str


def run_fanout(
    provider: Provider,
    repo: Path,
    vault_dir: Path,
    version: str,
    diff: str,
    diff_path: Path,
    roles: Sequence[RoleSpec],
    emit_event: Callable[[Event], None] = _no_emit,
) -> list[FindingsState | None]:
    """Run each read-only role over the frozen diff; collect each verdict from disk."""
    states: list[FindingsState | None] = []
    for role in roles:
        findings_file = vault_dir / f"{version}_{role.name}.md"
        profile = read_only_profile(findings_file)
        emit_event(RoleSpawn(ts=datetime.now(timezone.utc), role=role.name))
        result = run_role_with_diff(
            provider, role.prompt, repo, profile, diff, diff_path
        )
        emit_event(
            RoleReturned(
                ts=datetime.now(timezone.utc),
                role=role.name,
                session_id=result.session_id,
                total_cost_usd=result.total_cost_usd,
                is_error=result.is_error,
            )
        )
        states.append(read_findings_state(findings_file))
    return states
