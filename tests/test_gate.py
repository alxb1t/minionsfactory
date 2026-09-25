from pathlib import Path

import pytest

from orchestrator.gate import (
    CommandRunner,
    FakeGate,
    GateResult,
    StepResult,
    SubprocessGate,
)


def _write_makefile(repo: Path) -> None:
    """Write a root Makefile; its body is never read — the dry run is faked."""
    (repo / "Makefile").write_text("gate:\n\tuv run pytest -q\n")


def _fake_make(
    calls: list[str],
    dry_run_exit: int = 0,
    dry_run_output: str = "uv run pytest -q\n",
    gate_exit: int = 0,
) -> CommandRunner:
    """Return a runner faking `make -n gate` and `make gate`; it records each call."""

    def runner(command: str, repo: Path) -> StepResult:
        calls.append(command)
        if command == "make -n gate":
            return StepResult(command, dry_run_exit, dry_run_output)
        return StepResult(command, gate_exit, "")

    return runner


@pytest.mark.spec("gate:make-gate:resolves-to-make-gate")
def test_a_gate_target_resolves_to_make_gate(tmp_path: Path) -> None:
    _write_makefile(tmp_path)
    calls: list[str] = []

    result = SubprocessGate(runner=_fake_make(calls)).run_gate(tmp_path)

    assert [step.command for step in result.steps] == ["make gate"]
    assert calls == ["make -n gate", "make gate"]


@pytest.mark.spec("gate:run:all-green-passes")
def test_run_gate_passes_when_every_command_succeeds(tmp_path: Path) -> None:
    _write_makefile(tmp_path)

    result = SubprocessGate(runner=_fake_make([])).run_gate(tmp_path)

    assert result.passed is True
    assert [step.command for step in result.steps] == ["make gate"]


@pytest.mark.spec("gate:run:stops-at-first-red")
def test_run_gate_stops_at_the_first_failing_command(tmp_path: Path) -> None:
    _write_makefile(tmp_path)

    result = SubprocessGate(runner=_fake_make([], gate_exit=2)).run_gate(tmp_path)

    assert result.passed is False
    assert [step.command for step in result.steps] == ["make gate"]
    assert result.steps[-1].exit_code == 2


@pytest.mark.spec("gate:make-gate:missing-makefile-errors")
def test_a_missing_makefile_errors_clearly(tmp_path: Path) -> None:
    calls: list[str] = []

    with pytest.raises(FileNotFoundError, match="Makefile"):
        SubprocessGate(runner=_fake_make(calls)).run_gate(tmp_path)

    assert calls == []


@pytest.mark.spec("gate:make-gate:missing-target-errors")
def test_a_missing_gate_target_errors_clearly(tmp_path: Path) -> None:
    _write_makefile(tmp_path)
    calls: list[str] = []
    runner = _fake_make(calls, dry_run_exit=2, dry_run_output="No rule to make target")

    with pytest.raises(FileNotFoundError, match="Makefile"):
        SubprocessGate(runner=runner).run_gate(tmp_path)

    assert "make gate" not in calls


@pytest.mark.spec("gate:make-gate:empty-target-errors")
@pytest.mark.parametrize(
    "dry_run_output",
    [
        "",
        "  \n",
        "make: 'gate' is up to date.\n",
        "make: Nothing to be done for `gate'.\n",
    ],
)
def test_a_gate_target_that_runs_nothing_errors_clearly(
    tmp_path: Path, dry_run_output: str
) -> None:
    _write_makefile(tmp_path)
    calls: list[str] = []
    runner = _fake_make(calls, dry_run_output=dry_run_output)

    with pytest.raises(FileNotFoundError, match="Makefile"):
        SubprocessGate(runner=runner).run_gate(tmp_path)

    assert "make gate" not in calls


@pytest.mark.spec_exempt("test double — FakeGate scripted-result smoke")
def test_fake_gate_returns_the_scripted_result() -> None:
    scripted = GateResult(passed=True, steps=())

    result = FakeGate(scripted).run_gate(Path("/tmp/repo"))

    assert result is scripted
