"""Plan-state reader: reconstruct 'where are we' from disk (plan + git)."""

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_PLAN_PATTERN = re.compile(r"v(\d+)\.(\d+)_.*implementation_plan\.md$")
_CODE_PHASE_STATUSES = frozenset({"done", "wip", "planned", "todo"})


def select_plan(vault_project_dir: Path) -> Path:
    """Return the highest-version plan in implementation_plans/, ignoring archive/."""
    plans_dir = vault_project_dir / "implementation_plans"
    candidates: list[tuple[tuple[int, int], Path]] = []
    for path in plans_dir.glob("v*implementation_plan.md"):
        match = _PLAN_PATTERN.match(path.name)
        if match is None:
            continue
        version = (int(match.group(1)), int(match.group(2)))
        candidates.append((version, path))
    best = max(candidates, key=lambda item: item[0])
    return best[1]


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a plan's leading YAML frontmatter into flat key -> string values."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if not separator:
            continue
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


@dataclass(frozen=True)
class PlanState:
    """Where-are-we, read from disk: the plan's phase pointer + git head."""

    current_phase: str
    phases: dict[str, str]
    head: str


def read_head(repo: Path) -> str:
    """Return the target repo's current git HEAD commit sha."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def read_plan_state(
    vault_project_dir: Path,
    repo: Path,
    head_reader: Callable[[Path], str] = read_head,
) -> PlanState:
    """Read where-are-we from disk.

    The highest-version plan's phase state + the repo's git head.
    """
    plan_path = select_plan(vault_project_dir)
    frontmatter = parse_frontmatter(plan_path.read_text())
    validate_plan(frontmatter)
    phases = {
        key: value for key, value in frontmatter.items() if key.startswith("phase")
    }
    return PlanState(
        current_phase=frontmatter["current_phase"],
        phases=phases,
        head=head_reader(repo),
    )


class PlanContractError(ValueError):
    """A plan breaks the execution contract — refused at read time with a diagnostic."""


def validate_plan(frontmatter: dict[str, str]) -> None:
    """Raise PlanContractError if the plan frontmatter breaks the execution contract.

    The contract: a YAML frontmatter fence carrying `current_phase` and at least one
    `phaseN` flag, each with a recognized code-phase status (execution plans contain
    only code phases). A malformed plan is refused here, at read time — never a silent
    empty `{}`, a mid-run KeyError, or a non-code phase the driver would false-halt on.
    """
    if not frontmatter:
        raise PlanContractError("plan has no YAML frontmatter (expected a --- fence)")
    if "current_phase" not in frontmatter:
        raise PlanContractError("plan frontmatter is missing 'current_phase'")
    phases = {
        key: value for key, value in frontmatter.items() if key.startswith("phase")
    }
    if not phases:
        raise PlanContractError("plan frontmatter has no phaseN flags")
    for name, status in phases.items():
        if status not in _CODE_PHASE_STATUSES:
            raise PlanContractError(
                f"plan phase '{name}' has non-code status '{status}' — "
                f"execution plans contain only code phases "
                f"(expected one of {sorted(_CODE_PHASE_STATUSES)})"
            )


class PreflightError(Exception):
    """The target repo isn't configured for a run — halt before spending."""


def _covers(directory: Path, target: Path) -> bool:
    """Whether `directory` is `target` or an ancestor of it."""
    return target.is_relative_to(directory)


def verify_vault_access(repo: Path, vault_project_dir: Path) -> None:
    """Raise PreflightError unless the target grants the coder vault write access.

    The coder and read-only roles write vault files (findings, bookkeeping) that live
    OUTSIDE the repo cwd, so the target's `.claude/settings.local.json` must list the
    vault (or an ancestor) under `additionalDirectories`. Checked before any spawn, so
    a misconfigured target halts before spending, not mid-run.
    """
    settings_path = repo / ".claude" / "settings.local.json"
    if not settings_path.exists():
        raise PreflightError(
            f"no .claude/settings.local.json in {repo} — the target must grant the "
            f"coder write access to the vault ({vault_project_dir})"
        )
    settings = json.loads(settings_path.read_text())
    permissions = settings.get("permissions", {})
    granted = [
        *permissions.get("additionalDirectories", []),
        *settings.get("additionalDirectories", []),
    ]
    if not any(_covers(Path(directory), vault_project_dir) for directory in granted):
        raise PreflightError(
            f"the target's .claude/settings.local.json does not grant vault access "
            f"({vault_project_dir}) via additionalDirectories"
        )
