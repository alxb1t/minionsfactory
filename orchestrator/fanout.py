"""End-of-plan fan-out: run review ‖ security ‖ simplify.

Read-only over the frozen diff.
"""

from collections.abc import Callable, Mapping, Sequence
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


def build_inputs_block(
    change_dir: Path,
    findings: Mapping[str, Path],
    head: str,
    version: str,
    vault_dir: Path,
    lead_lines: Sequence[str] = (),
) -> str:
    """Build the Inputs block a role receives — path resolution lives here, in code.

    Every role gets one: the three read-only fan-out roles, and the coder, fixer and
    release roles. A role has no shell with which to resolve paths (and deriving them
    by shell is what this replaces), so the orchestrator names the change directory,
    the findings paths the role needs, the git head and the declared release version.

    `lead_lines` carries the role-specific bullets a caller wants above the common
    core — the fan-out's mode, diff and single write target.
    """
    lines = [
        "## Inputs (supplied by the orchestrator — do not re-derive these)",
        *lead_lines,
        f"- Change (proposal · design · tasks): {change_dir}",
        f"- Release version: {version}",
        f"- head (the branch tip the orchestrator read): {head}",
    ]
    lines += [f"- Findings ({role}): {path}" for role, path in findings.items()]
    lines.append(f"- Context: {vault_dir / 'overview.md'}, {vault_dir / 'log.md'}")
    return "\n".join(lines) + "\n\n---\n\n"


def assemble_prompt(inputs_block: str, role_body: str) -> str:
    """Assemble a role's final prompt: the Inputs block first, then the role's body.

    A one-liner on purpose — it makes "the prompt leads with the Inputs block" a fact
    a unit test can assert, rather than a property of `__main__`'s wiring.
    """
    return inputs_block + role_body


def run_fanout(
    provider: Provider,
    repo: Path,
    vault_dir: Path,
    change_id: str,
    version: str,
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
        prompt = assemble_prompt(
            build_inputs_block(
                change_dir,
                {str(role.name): findings_file},
                head,
                version,
                vault_dir,
                lead_lines=[
                    f"- Mode: {mode}",
                    f"- Diff to review (read this file): {diff_path}",
                    f"- Findings file (write ONLY this): {findings_file}",
                ],
            ),
            role.prompt,
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
