from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from orchestrator.converge import ConvergeResult, ConvergeStatus
from orchestrator.driver import RunStatus, decide, run
from orchestrator.findings import FindingsState
from orchestrator.gate import FakeGate, GateResult
from orchestrator.provider import FakeProvider, Profile, ProviderError, RoleResult
from orchestrator.release import ReleaseResult, ReleaseStatus
from orchestrator.state import ChangeState, Phase, read_change_state
from orchestrator.status import Advance, Event, PhaseStart, RunSummary, render

_GREEN = GateResult(passed=True, steps=())
_RED = GateResult(passed=False, steps=())
_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)


def _reader(states: list[ChangeState]) -> Callable[[Path], ChangeState]:
    iterator = iter(states)

    def read(repo: Path) -> ChangeState:
        return next(iterator)

    return read


def _never_halts(vault_project_dir: Path) -> bool:
    return False


def _always_halts(vault_project_dir: Path) -> bool:
    return True


def _state(done: Sequence[bool], head: str) -> ChangeState:
    """A change whose phases carry `done`; its current phase is the first unchecked."""
    return ChangeState(
        change_id="0005-change-cutover",
        phases=tuple(
            Phase(index=i + 1, title=f"phase {i + 1}", done=flag)
            for i, flag in enumerate(done)
        ),
        head=head,
        version="v0.5",
    )


@pytest.mark.spec("build-loop:phase-decision:advances-on-commit-and-moved-phase")
def test_decide_advances_on_green_gate_with_new_commit_and_moved_phase() -> None:
    decision = decide(
        _state([False, False], "aaa"),
        _state([True, False], "bbb"),
        _GREEN,
        coder_halted=False,
    )
    assert decision.advance is True


@pytest.mark.spec("build-loop:phase-decision:coder-halt-report-halts")
def test_decide_halts_when_the_coder_wrote_a_halt_report() -> None:
    decision = decide(
        _state([False, False], "aaa"),
        _state([True, False], "bbb"),
        _GREEN,
        coder_halted=True,
    )
    assert decision.advance is False
    assert "halt" in decision.reason.lower()


@pytest.mark.spec("build-loop:phase-decision:red-gate-halts")
def test_decide_halts_on_a_red_gate() -> None:
    decision = decide(
        _state([False, False], "aaa"),
        _state([True, False], "bbb"),
        _RED,
        coder_halted=False,
    )
    assert decision.advance is False
    assert "gate" in decision.reason.lower()


@pytest.mark.spec("build-loop:phase-decision:no-advance-halts")
def test_decide_halts_when_the_phase_did_not_advance() -> None:
    # gate green, but the current-phase index and head are unchanged
    # → the coder didn't really finish the phase
    decision = decide(
        _state([False, False], "aaa"),
        _state([False, False], "aaa"),
        _GREEN,
        coder_halted=False,
    )
    assert decision.advance is False


@pytest.mark.spec("build-loop:phase-decision:no-advance-halts")
def test_decide_halts_on_a_new_commit_with_no_moved_phase() -> None:
    # a commit landed but no checkbox moved → the phase is not done
    decision = decide(
        _state([False, False], "aaa"),
        _state([False, False], "bbb"),
        _GREEN,
        coder_halted=False,
    )
    assert decision.advance is False


@pytest.mark.spec("build-loop:phase-decision:moved-checkbox-without-commit-halts")
def test_decide_halts_on_a_moved_checkbox_with_no_new_commit() -> None:
    # the checkbox alone is not evidence the phase was built — un-gameable advance
    decision = decide(
        _state([False, False], "aaa"),
        _state([True, False], "aaa"),
        _GREEN,
        coder_halted=False,
    )
    assert decision.advance is False


@pytest.mark.spec("build-loop:run:advances-until-complete")
def test_run_advances_through_phases_until_the_plan_is_complete() -> None:
    states = [
        _state([False, False], "c0"),
        _state([True, False], "c1"),
        _state([True, True], "c2"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.COMPLETE
    assert result.phases_advanced == 2


@pytest.mark.spec("build-loop:run:red-gate-halts")
def test_run_halts_when_the_gate_is_red() -> None:
    states = [
        _state([False], "c0"),
        _state([True], "c1"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(GateResult(passed=False, steps=())),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.HALTED
    assert "gate" in result.reason.lower()
    assert result.phases_advanced == 0


@pytest.mark.spec("build-loop:run:coder-halt-report-halts")
def test_run_halts_when_the_coder_writes_a_halt_report() -> None:
    states = [
        _state([False], "c0"),
        _state([False], "c0"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_always_halts,
    )
    assert result.status is RunStatus.HALTED
    assert "halt" in result.reason.lower()


@pytest.mark.spec("build-loop:run:resumes-from-disk")
def test_run_resumes_from_the_current_phase_on_disk() -> None:
    # phase0 already done on disk; the run picks up at phase1 and finishes.
    states = [
        _state([True, False], "c1"),
        _state([True, True], "c2"),
    ]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
    )
    assert result.status is RunStatus.COMPLETE
    assert result.phases_advanced == 1


@pytest.mark.spec("build-loop:run:emits-advancing-event-stream")
def test_run_emits_the_event_stream_for_an_advancing_phase() -> None:
    states = [
        _state([False], "c0"),
        _state([True], "c1"),
    ]
    events: list[Event] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        emit_event=events.append,
    )
    assert [e.kind for e in events] == [
        "phase-start",
        "role-spawn",
        "role-returned",
        "advance",
        "run-summary",
    ]


@pytest.mark.spec("build-loop:run:already-complete-summary")
def test_run_emits_a_complete_summary_when_the_plan_is_already_done() -> None:
    states = [_state([True], "c0")]
    events: list[Event] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        emit_event=events.append,
    )
    assert [e.kind for e in events] == ["run-summary"]
    summary = events[-1]
    assert isinstance(summary, RunSummary)
    assert summary.status == "complete"


@pytest.mark.spec("build-loop:end-of-plan:fanout-on-complete")
def test_run_triggers_fanout_when_the_plan_completes() -> None:
    states = [_state([True], "c0")]
    calls: list[int] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: calls.append(1) or [],
    )
    assert calls == [1]


@pytest.mark.spec("build-loop:end-of-plan:no-fanout-on-halt")
def test_run_does_not_fan_out_when_the_build_halts() -> None:
    states = [
        _state([False], "c0"),
        _state([False], "c0"),
    ]
    calls: list[int] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: calls.append(1) or [],
    )
    assert calls == []


@pytest.mark.spec("build-loop:end-of-plan:converge-after-fanout")
def test_run_converges_after_fanout_when_the_plan_completes() -> None:
    states = [_state([True], "c0")]
    order: list[str] = []

    def fake_fanout() -> list[FindingsState | None]:
        order.append("fanout")
        return []

    def fake_converge() -> ConvergeResult:
        order.append("converge")
        return ConvergeResult(ConvergeStatus.CONVERGED, "", 1)

    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=fake_fanout,
        converge=fake_converge,
    )
    assert order == ["fanout", "converge"]
    assert result.status is RunStatus.COMPLETE


@pytest.mark.spec("build-loop:end-of-plan:converge-halt-halts-run")
def test_run_halts_when_converge_halts() -> None:
    states = [_state([True], "c0")]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: [],
        converge=lambda: ConvergeResult(ConvergeStatus.HALTED, "round cap exceeded", 3),
    )
    assert result.status is RunStatus.HALTED
    assert "round cap" in result.reason


@pytest.mark.spec("build-loop:end-of-plan:release-after-converge")
def test_run_prepares_release_after_converge_when_the_plan_completes() -> None:
    states = [_state([True], "c0")]
    order: list[str] = []

    def fake_converge() -> ConvergeResult:
        order.append("converge")
        return ConvergeResult(ConvergeStatus.CONVERGED, "", 0)

    def fake_release() -> ReleaseResult:
        order.append("release")
        return ReleaseResult(ReleaseStatus.PREPARED, "", "handoff")

    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: order.append("fanout") or [],
        converge=fake_converge,
        release=fake_release,
    )
    assert order == ["fanout", "converge", "release"]
    assert result.status is RunStatus.COMPLETE


@pytest.mark.spec("build-loop:end-of-plan:release-refused-halts")
def test_run_halts_when_release_is_refused() -> None:
    states = [_state([True], "c0")]
    result = run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: [],
        converge=lambda: ConvergeResult(ConvergeStatus.CONVERGED, "", 0),
        release=lambda: ReleaseResult(
            ReleaseStatus.REFUSED, "tag v0.2.0 already exists", ""
        ),
    )
    assert result.status is RunStatus.HALTED
    assert "already exists" in result.reason


@pytest.mark.spec("build-loop:end-of-plan:no-release-when-converge-halts")
def test_run_does_not_release_when_converge_halts() -> None:
    states = [_state([True], "c0")]
    calls: list[int] = []
    run(
        Path("/repo"),
        Path("/vault"),
        FakeProvider(_ROLE),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        fanout=lambda: [],
        converge=lambda: ConvergeResult(ConvergeStatus.HALTED, "round cap exceeded", 3),
        release=lambda: (
            calls.append(1) or ReleaseResult(ReleaseStatus.PREPARED, "", "")
        ),
    )
    assert calls == []  # converge halted → the run returns before release


def _write_repo_only_change(repo: Path, phases: int = 2) -> Path:
    """Write a well-formed in-tree change; nothing about it lives in a vault."""
    change_dir = repo / "openspec" / "changes" / "0005-change-cutover"
    change_dir.mkdir(parents=True)
    (change_dir / "specs").mkdir()
    (change_dir / "proposal.md").write_text("---\nversion: v0.5\n---\n\n# proposal\n")
    (change_dir / "design.md").write_text("# design\n")
    items = "\n".join(f"- [ ] {i + 1} — Phase {i + 1}" for i in range(phases))
    (change_dir / "tasks.md").write_text(f"# Tasks\n\n## Progress\n\n{items}\n")
    return change_dir


class _TickingProvider:
    """A 'coder' that ticks the next tasks.md checkbox and lands a commit."""

    def __init__(self, tasks: Path, heads: list[str]) -> None:
        self._tasks = tasks
        self._heads = heads

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        self._tasks.write_text(self._tasks.read_text().replace("- [ ]", "- [x]", 1))
        self._heads.append(f"c{len(self._heads)}")
        return _ROLE


@pytest.mark.spec("build-loop:run:drives-with-no-vault-plan")
def test_run_drives_a_repo_only_change_with_no_vault_plan(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    change_dir = _write_repo_only_change(repo)
    vault.mkdir()  # an empty vault: no plan file, and no plan directory of any name
    heads = ["c0"]
    fanned_out: list[int] = []

    result = run(
        repo,
        vault,
        _TickingProvider(change_dir / "tasks.md", heads),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=lambda r: read_change_state(r, head_reader=lambda _: heads[-1]),
        halt_checker=_never_halts,
        fanout=lambda: fanned_out.append(1) or [],
    )

    assert result.status is RunStatus.COMPLETE
    assert result.phases_advanced == 2
    assert fanned_out == [1]  # the fan-out still fires at change-complete
    # stronger than naming the retired directory: the vault holds nothing at all,
    # so no plan file and no plan directory of any name was read or written.
    assert list(vault.iterdir()) == []


@pytest.mark.spec("build-loop:run:emits-advancing-event-stream")
def test_run_renders_each_phase_as_its_index_and_title(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    change_dir = _write_repo_only_change(repo, phases=1)
    vault.mkdir()
    heads = ["c0"]
    events: list[Event] = []

    run(
        repo,
        vault,
        _TickingProvider(change_dir / "tasks.md", heads),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=lambda r: read_change_state(r, head_reader=lambda _: heads[-1]),
        halt_checker=_never_halts,
        emit_event=events.append,
    )

    start = next(e for e in events if isinstance(e, PhaseStart))
    advance = next(e for e in events if isinstance(e, Advance))
    assert start.phase == "1: Phase 1"
    # the label survives `_short_phase` whole — index AND title, no " — " to split on
    assert render(start) == "▶ building 1: Phase 1"
    assert advance.from_phase == "1: Phase 1"
    assert advance.to_phase == "complete"  # an explicit terminal label, not `None`


class _ErroringProvider:
    """A provider whose spawn fails — simulates an API error / usage limit."""

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        raise ProviderError("claude -p exited 1 — usage limit reached")


@pytest.mark.spec("build-loop:run:provider-error-halts-cleanly")
def test_run_halts_cleanly_on_a_provider_error() -> None:
    states = [_state([False], "c0")]
    events: list[Event] = []
    result = run(
        Path("/repo"),
        Path("/vault"),
        _ErroringProvider(),
        FakeGate(_GREEN),
        "build",
        Profile(),
        state_reader=_reader(states),
        halt_checker=_never_halts,
        emit_event=events.append,
    )
    assert result.status is RunStatus.HALTED
    assert "provider error" in result.reason
    assert "halt" in [e.kind for e in events]  # a clean halt event, not a traceback
