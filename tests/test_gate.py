from pathlib import Path

import pytest

from orchestrator.gate import (
    FakeGate,
    GateResult,
    StepResult,
    SubprocessGate,
    read_gate_commands,
)
from orchestrator.state import PlanContractError, read_plan_state, validate_plan


def _write_gate_config(repo: Path, body: str) -> None:
    """Write a minions.toml under the target's .minions/ dir."""
    (repo / ".minions").mkdir()
    (repo / ".minions" / "minions.toml").write_text(body)


def test_read_gate_commands_parses_the_ordered_list(tmp_path: Path) -> None:
    _write_gate_config(
        tmp_path, 'gate = [\n "uv run ruff check .", \n "uv run pytest",\n]\n'
    )
    commands = read_gate_commands(tmp_path)
    assert commands == ["uv run ruff check .", "uv run pytest"]


def test_run_gate_passes_when_every_command_succeeds(tmp_path: Path) -> None:
    _write_gate_config(tmp_path, 'gate = ["step-a", "step-b", "step-c"]\n')

    def runner(command: str, repo: Path) -> StepResult:
        return StepResult(command=command, exit_code=0, output="")

    result = SubprocessGate(runner=runner).run_gate(tmp_path)
    assert result.passed is True
    assert [step.command for step in result.steps] == ["step-a", "step-b", "step-c"]


def test_run_gate_stops_at_the_first_failing_command(tmp_path: Path) -> None:
    _write_gate_config(tmp_path, 'gate = ["step-a", "step-b", "step-c"]\n')

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


def test_read_gate_commands_errors_clearly_when_the_config_is_missing(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="minions.toml"):
        read_gate_commands(tmp_path)


def test_validate_plan_accepts_a_conforming_plan() -> None:
    validate_plan({"current_phase": "P1", "phase0": "done", "phase1": "planned"})


def test_validate_plan_rejects_empty_frontmatter() -> None:
    with pytest.raises(PlanContractError, match="no YAML frontmatter"):
        validate_plan({})


def test_validate_plan_rejects_missing_current_phase() -> None:
    with pytest.raises(PlanContractError, match="current_phase"):
        validate_plan({"phase0": "done"})


def test_validate_plan_rejects_a_plan_with_no_phase_flags() -> None:
    with pytest.raises(PlanContractError, match="phaseN"):
        validate_plan({"current_phase": "P1", "type": "overview"})


def test_read_plan_state_refuses_a_malformed_plan(tmp_path: Path) -> None:
    plans = tmp_path / "implementation_plans"
    plans.mkdir()
    (plans / "v0.1_x_implementation_plan.md").write_text("# no frontmatter here\n")

    with pytest.raises(PlanContractError):
        read_plan_state(tmp_path, tmp_path, head_reader=lambda repo: "h")
