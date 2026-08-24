"""End-of-plan fan-out: run review ‖ security ‖ simplify.

Read-only over the frozen diff.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.diff import run_role_with_diff
from orchestrator.findings import FindingsState, findings_path, read_findings_state
from orchestrator.provider import Provider, read_only_profile
from orchestrator.status import Event, Role, RoleReturned, RoleSpawn, _no_emit


@dataclass(frozen=True)
class RoleSpec:
    """One fan-out role: its name (→ findings filename) and its prompt."""

    name: Role
    prompt: str


def _inputs_block(
    mode: str,
    diff_path: Path,
    findings_file: Path,
    head: str,
    change_dir: Path,
    vault_dir: Path,
) -> str:
    """Build the Inputs block a read-only role needs (it can't resolve paths itself)."""
    return (
        "## Inputs (supplied by the orchestrator — do not re-derive these)\n"
        f"- Mode: {mode}\n"
        f"- Diff to review (read this file): {diff_path}\n"
        f"- Findings file (write ONLY this): {findings_file}\n"
        f"- head (for your `head:` frontmatter field): {head}\n"
        f"- Change (proposal · design · tasks): {change_dir}\n"
        f"- Context: {vault_dir / 'overview.md'}, {vault_dir / 'log.md'}\n\n"
        "---\n\n"
    )


def run_fanout(
    provider: Provider,
    repo: Path,
    vault_dir: Path,
    change_id: str,
    diff: str,
    diff_path: Path,
    head: str,
    change_dir: Path,
    roles: Sequence[RoleSpec],
    mode: str = "review",
    emit_event: Callable[[Event], None] = _no_emit,
) -> list[FindingsState | None]:
    """Run each read-only role over the supplied diff; collect each verdict from disk.

    Each role is spawned with an orchestrator-prepended Inputs block (it has no shell
    to resolve paths itself); its findings file is resolved through `findings_path`,
    the single site the fixer, the converge loop and the release stage also read.

    The `<vault>/findings/` directory is created **before the first spawn**: a read-only
    role is granted `Write(<its findings file>)` and denied `Bash`, so it cannot create
    the directory itself, and a findings file that never lands reads as not-clean.
    """
    (vault_dir / "findings").mkdir(parents=True, exist_ok=True)
    states: list[FindingsState | None] = []
    for role in roles:
        findings_file = findings_path(vault_dir, change_id, role.name)
        profile = read_only_profile(findings_file)
        prompt = (
            _inputs_block(mode, diff_path, findings_file, head, change_dir, vault_dir)
            + role.prompt
        )
        emit_event(RoleSpawn(ts=datetime.now(timezone.utc), role=role.name))
        result = run_role_with_diff(provider, prompt, repo, profile, diff, diff_path)
        emit_event(
            RoleReturned(
                ts=datetime.now(timezone.utc),
                role=role.name,
                session_id=result.session_id,
                total_cost_usd=result.total_cost_usd,
                is_error=result.is_error,
                summary=result.result,
            )
        )
        states.append(read_findings_state(findings_file))
    return states
