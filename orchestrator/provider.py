"""Provider seam: invoke a role headless and parse its JSON result."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class RoleResult(BaseModel):
    """Typed result of a headless role run (claude -p --output-format json)."""

    subtype: str
    is_error: bool
    result: str
    session_id: str
    total_cost_usd: float
    stop_reason: str | None = None


def parse_result(stdout: str) -> RoleResult:
    """Parse a headless JSON result string into a typed RoleResult."""
    return RoleResult.model_validate_json(stdout)


@dataclass(frozen=True)
class Profile:
    """Permission profile for a role instance (native Claude Code perms)."""

    permission_mode: str = "default"
    allowed_tools: tuple[str, ...] = ()
    disallowed_tools: tuple[str, ...] = ()


class Provider(Protocol):
    """The seam the driver depends on: run one role instance, get a typed result."""

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        """Invoke a role headless in `repo` under `profile`.

        Return its parsed result.
        """
        ...


class FakeProvider:
    """Scripted Provider double for tests.

    Returns a preset RoleResult, spawns nothing.
    """

    def __init__(self, result: RoleResult) -> None:
        """Store the RoleResult to return from every run_role call."""
        self._result = result

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        """Return the scripted result, ignoring the arguments."""
        return self._result


def build_command(role_prompt: str, profile: Profile) -> list[str]:
    """Build the `claude -p` argv for a headless role run under `profile`."""
    command = [
        "claude",
        "-p",
        role_prompt,
        "--output-format",
        "json",
        "--permission-mode",
        profile.permission_mode,
    ]

    if profile.allowed_tools:
        command += ["--allowedTools", *profile.allowed_tools]

    if profile.disallowed_tools:
        command += ["--disallowedTools", *profile.disallowed_tools]

    return command


class ClaudeCodeProvider:
    """Real Provider: run a role as a headless `claude -p` process.

    Parse its JSON result.
    """

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        """Spawn `claude -p` in `repo` under `profile`; return its parsed result."""
        command = build_command(role_prompt, profile)
        completed = subprocess.run(
            command,
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return parse_result(completed.stdout)


def read_only_profile(findings_file: Path) -> Profile:
    """Read-only role: no Bash/Edit; Write only to its findings file."""
    return Profile(
        allowed_tools=(f"Write({findings_file})",),
        disallowed_tools=("Bash", "Edit"),
    )
