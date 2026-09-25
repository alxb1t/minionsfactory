"""Gate runner: run the target repo's own quality gate and report the result."""

import shlex
import subprocess
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


_GATE_COMMAND = "make gate"
_DRY_RUN_COMMAND = "make -n gate"
# Lines make prints when the target exists but has no recipe to run.
_NOTHING_TO_RUN = ("is up to date", "Nothing to be done")


def resolve_gate(repo: Path, runner: CommandRunner) -> list[str]:
    """Return the gate as `["make gate"]` once `make -n gate` shows it runs a command.

    Raises `FileNotFoundError` naming the `Makefile` rather than run an empty,
    falsely-green gate.
    """
    makefile = repo / "Makefile"
    if not makefile.exists():
        raise FileNotFoundError(
            f"no gate: {makefile} is missing — "
            "the target must ship a root Makefile with a gate target"
        )
    dry_run = runner(_DRY_RUN_COMMAND, repo)
    if dry_run.exit_code != 0:
        raise FileNotFoundError(
            f"no gate: `{_DRY_RUN_COMMAND}` exited {dry_run.exit_code} — "
            f"{makefile} has no gate target\n{dry_run.output}"
        )
    lines = [line for line in dry_run.output.splitlines() if line.strip()]
    if all(any(marker in line for marker in _NOTHING_TO_RUN) for line in lines):
        raise FileNotFoundError(
            f"no gate: `{_DRY_RUN_COMMAND}` printed no command — "
            f"the gate target in {makefile} runs nothing"
        )
    return [_GATE_COMMAND]


class SubprocessGate:
    """Real Gate: run the target repo's `make gate`, checked first with `make -n gate`.

    Stops at the first failure.
    """

    def __init__(self, runner: CommandRunner = run_command) -> None:
        """Store the command runner (defaults to the real subprocess executor)."""
        self._runner = runner

    def run_gate(self, repo: Path) -> GateResult:
        """Run each resolved gate command in order; stop at the first red."""
        commands = resolve_gate(repo, self._runner)
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
