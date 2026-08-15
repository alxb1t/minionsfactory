"""Plan-state reader: reconstruct 'where are we' from disk (plan + git)."""

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_PLAN_PATTERN = re.compile(r"v(\d+)\.(\d+)_.*implementation_plan\.md$")


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
    phases = {
        key: value for key, value in frontmatter.items() if key.startswith("phase")
    }
    return PlanState(
        current_phase=frontmatter["current_phase"],
        phases=phases,
        head=head_reader(repo),
    )
