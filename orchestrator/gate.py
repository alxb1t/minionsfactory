"""Gate runner: run the target repo's own quality gate and report the result."""

import shlex
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StepResult:
    """Outcome of running one gate command."""

    command: str
    exit_code: int
    output: str


@dataclass(frozen=True)
class GateResult:
    """Aggregate result of a gate run — the verdict plus each step's outcome."""

    passed: bool
    steps: tuple[StepResult, ...]


CommandRunner = Callable[[str, Path], StepResult]


def run_command(command: str, repo: Path) -> StepResult:
    """Run one gate command in `repo` (no shell) and capture its outcome."""
    argv = shlex.split(command)
    completed = subprocess.run(
        argv, cwd=repo, capture_output=True, text=True, check=False
    )
    return StepResult(
        command=command,
        exit_code=completed.returncode,
        output=completed.stdout + completed.stderr,
    )


def read_gate_commands(repo: Path) -> list[str]:
    """Read the ordered gate command list from the target repo's minions.toml."""
    config_path = repo / "minions.toml"
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)
    return config["gate"]


class SubprocessGate:
    """Real Gate: run the target repo's gate commands in order.

    Stops at the first failure.
    """

    def __init__(self, runner: CommandRunner = run_command) -> None:
        """Store the command runner (defaults to the real subprocess executor)."""
        self._runner = runner

    def run_gate(self, repo: Path) -> GateResult:
        """Run each gate command from the repo's minions.toml; stop at the first red."""
        commands = read_gate_commands(repo)
        steps: list[StepResult] = []
        for command in commands:
            step = self._runner(command, repo)
            steps.append(step)
            if step.exit_code != 0:
                return GateResult(passed=False, steps=tuple(steps))
        return GateResult(passed=True, steps=tuple(steps))


class Gate(Protocol):
    """The seam the driver depends on: run a repo's gate, get a typed verdict."""

    def run_gate(self, repo: Path) -> GateResult:
        """Run `repo`'s gate and return the aggregate result."""
        ...


class FakeGate:
    """Scripted Gate double for tests — returns a preset GateResult, runs nothing."""

    def __init__(self, result: GateResult) -> None:
        """Store the GateResult to return from every run_gate call."""
        self._result = result

    def run_gate(self, repo: Path) -> GateResult:
        """Return the scripted result, ignoring the repo."""
        return self._result
