from pathlib import Path

from orchestrator.gate import (
    FakeGate,
    GateResult,
    StepResult,
    SubprocessGate,
    read_gate_commands,
)


def test_read_gate_commands_parses_the_ordered_list(tmp_path: Path) -> None:
    (tmp_path / "minions.toml").write_text(
        'gate = [\n "uv run ruff check .", \n "uv run pytest",\n]\n'
    )

    commands = read_gate_commands(tmp_path)

    assert commands == ["uv run ruff check .", "uv run pytest"]


def test_run_gate_passes_when_every_command_succeeds(tmp_path: Path) -> None:
    (tmp_path / "minions.toml").write_text('gate = ["step-a", "step-b", "step-c"]\n')

    def runner(command: str, repo: Path) -> StepResult:
        return StepResult(command=command, exit_code=0, output="")

    result = SubprocessGate(runner=runner).run_gate(tmp_path)

    assert result.passed is True
    assert [step.command for step in result.steps] == ["step-a", "step-b", "step-c"]


def test_run_gate_stops_at_the_first_failing_command(tmp_path: Path) -> None:
    (tmp_path / "minions.toml").write_text('gate = ["step-a", "step-b", "step-c"]\n')

    def runner(command: str, repo: Path) -> StepResult:
        exit_code = 1 if command == "step-b" else 0
        return StepResult(command=command, exit_code=exit_code, output="")

    result = SubprocessGate(runner=runner).run_gate(tmp_path)

    assert result.passed is False
    assert [step.command for step in result.steps] == ["step-a", "step-b"]
    assert result.steps[-1].exit_code == 1


def test_fake_gate_returns_the_scripted_result() -> None:
    scripted = GateResult(passed=True, steps=())

    result = FakeGate(scripted).run_gate(Path("/tmp/repo"))

    assert result is scripted
