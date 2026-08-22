from pathlib import Path

import pytest

from orchestrator.converge import ConvergeStatus, converge
from orchestrator.findings import FindingsState
from orchestrator.gate import FakeGate, GateResult
from orchestrator.provider import FakeProvider, Profile, RoleResult

_GREEN = GateResult(passed=True, steps=())
_RED = GateResult(passed=False, steps=())
_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)


class _RecordingProvider:
    """Records each run_role prompt; returns a scripted result."""

    def __init__(self, result: RoleResult) -> None:
        self.calls: list[str] = []
        self._result = result

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        self.calls.append(role_prompt)
        return self._result


def _open() -> FindingsState:
    return FindingsState(
        verdict="changes-requested", open_blocking=1, round=1, head="h"
    )


def _clean() -> FindingsState:
    return FindingsState(verdict="clean", open_blocking=0, round=1, head="h")


@pytest.mark.spec("converge:converge-to-clean:already-clean-zero-rounds")
def test_converge_is_clean_in_zero_rounds_when_nothing_is_blocking() -> None:
    reads = iter([[_clean(), _clean(), _clean()]])
    result = converge(
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        Path("/repo"),
        fixer_prompt="fix",
        coder_profile=Profile(),
        read_states=lambda: next(reads),
        run_verify=lambda: None,
        max_rounds=3,
    )
    assert result.status is ConvergeStatus.CONVERGED
    assert result.rounds == 0


@pytest.mark.spec("converge:converge-to-clean:fix-then-verified-clean")
def test_converge_fixes_then_verifies_to_clean_in_one_round() -> None:
    reads = iter(
        [
            [_open(), _clean(), _clean()],
            [_clean(), _clean(), _clean()],
        ]
    )
    verify_calls: list[int] = []
    provider = _RecordingProvider(_ROLE)

    result = converge(
        provider,
        FakeGate(_GREEN),
        Path("/repo"),
        fixer_prompt="fix",
        coder_profile=Profile(),
        read_states=lambda: next(reads),
        run_verify=lambda: verify_calls.append(1),
        max_rounds=3,
    )

    assert result.status is ConvergeStatus.CONVERGED
    assert result.rounds == 1
    assert provider.calls == ["fix"]
    assert verify_calls == [1]


@pytest.mark.spec("converge:converge-to-clean:reopen-then-clears")
def test_converge_continues_when_re_verify_reopens_then_clears() -> None:
    reads = iter(
        [
            [_open(), _clean(), _clean()],
            [_open(), _clean(), _clean()],
            [_clean(), _clean(), _clean()],
        ]
    )
    verify_calls: list[int] = []
    provider = _RecordingProvider(_ROLE)
    result = converge(
        provider,
        FakeGate(_GREEN),
        Path("/repo"),
        fixer_prompt="fix",
        coder_profile=Profile(),
        read_states=lambda: next(reads),
        run_verify=lambda: verify_calls.append(1),
        max_rounds=3,
    )
    assert result.status is ConvergeStatus.CONVERGED
    assert result.rounds == 2
    assert provider.calls == ["fix", "fix"]
    assert verify_calls == [1, 1]


@pytest.mark.spec("converge:bounded-termination:round-cap-halts")
def test_converge_halts_at_the_round_cap_when_it_never_clears() -> None:
    result = converge(
        _RecordingProvider(_ROLE),
        FakeGate(_GREEN),
        Path("/repo"),
        fixer_prompt="fix",
        coder_profile=Profile(),
        read_states=lambda: [_open(), _clean(), _clean()],  # always blocking
        run_verify=lambda: None,
        max_rounds=2,
    )
    assert result.status is ConvergeStatus.HALTED
    assert result.reason == "round cap exceeded"
    assert result.rounds == 2


@pytest.mark.spec("converge:bounded-termination:red-gate-halts")
def test_converge_halts_when_the_gate_is_red_after_a_fix() -> None:
    verify_calls: list[int] = []
    result = converge(
        _RecordingProvider(_ROLE),
        FakeGate(_RED),
        Path("/repo"),
        fixer_prompt="fix",
        coder_profile=Profile(),
        read_states=lambda: [_open(), _clean(), _clean()],
        run_verify=lambda: verify_calls.append(1),
        max_rounds=3,
    )
    assert result.status is ConvergeStatus.HALTED
    assert result.reason == "gate red after fix"
    assert result.rounds == 1
    assert verify_calls == []
