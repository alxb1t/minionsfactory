"""Diff supply: compute a repo's diff for a commit range (list-argv git, no shell)."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from orchestrator.provider import Profile, Provider, RoleResult


def _run_git(argv: list[str], repo: Path) -> str:
    """Run a git argv in `repo` and return its stdout (the untested subprocess edge)."""
    completed = subprocess.run(
        argv,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def compute_diff(
    repo: Path,
    base: str,
    head: str,
    runner: Callable[[list[str], Path], str] = _run_git,
) -> str:
    """Return the diff for base..head in repo (list-argv git, no shell)."""
    return runner(["git", "diff", f"{base}..{head}"], repo)


def run_role_with_diff(
    provider: Provider,
    role_prompt: str,
    repo: Path,
    profile: Profile,
    diff: str,
    diff_path: Path,
) -> RoleResult:
    """Write the diff to a file the read-only role reads, then run the role."""
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(diff)
    return provider.run_role(role_prompt, repo, profile)
