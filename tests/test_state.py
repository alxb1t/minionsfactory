import json
from pathlib import Path

import pytest

from orchestrator.state import (
    ChangeState,
    Phase,
    PlanContractError,
    PreflightError,
    change_advanced,
    parse_frontmatter,
    parse_progress,
    read_change_state,
    read_plan_state,
    select_change,
    select_plan,
    validate_change,
    validate_plan,
    verify_vault_access,
)


@pytest.mark.spec("change-state:plan-selection:highest-version-ignores-archive")
def test_select_plan_picks_highest_version_ignoring_archive(tmp_path: Path) -> None:
    plans = tmp_path / "implementation_plans"
    (plans / "archive").mkdir(parents=True)
    (plans / "v0.2_a_implementation_plan.md").write_text("x")
    (plans / "v0.10_b_implementation_plan.md").write_text("x")
    (plans / "archive" / "v0.99_old_implementation_plan.md").write_text("x")

    selected = select_plan(tmp_path)

    assert selected.name == "v0.10_b_implementation_plan.md"


@pytest.mark.spec("change-state:plan-state:parses-frontmatter")
def test_parse_frontmatter_reads_current_phase_and_phase_flags() -> None:
    text = (
        "---\n"
        'current_phase: "P4: reader in progress"\n'
        "phase0: done\n"
        "phase1: planned\n"
        "---\n"
        "# Body\n"
        "phase2: not-frontmatter\n"
    )

    frontmatter = parse_frontmatter(text)

    assert frontmatter["current_phase"] == "P4: reader in progress"
    assert frontmatter["phase0"] == "done"
    assert frontmatter["phase1"] == "planned"
    assert "phase2" not in frontmatter


@pytest.mark.spec("change-state:plan-state:assembles-phases-and-head")
def test_read_plan_state_assembles_phase_state_and_head(tmp_path: Path) -> None:
    plans = tmp_path / "implementation_plans"
    plans.mkdir()
    (plans / "v0.1_x_implementation_plan.md").write_text(
        "---\n"
        'current_phase: "P4 in progress"\n'
        "phase0: done\n"
        "phase1: planned\n"
        "---\n"
        "# body\n"
    )

    def fake_head(repo: Path) -> str:
        return "abc123"

    state = read_plan_state(tmp_path, tmp_path, head_reader=fake_head)

    assert state.current_phase == "P4 in progress"
    assert state.phases == {"phase0": "done", "phase1": "planned"}
    assert state.head == "abc123"


# --- plan contract guard (P7) ---


@pytest.mark.spec("change-state:plan-contract:accepts-conforming")
def test_validate_plan_accepts_a_conforming_plan() -> None:
    validate_plan({"current_phase": "P1", "phase0": "done", "phase1": "planned"})


@pytest.mark.spec("change-state:plan-contract:rejects-empty-frontmatter")
def test_validate_plan_rejects_empty_frontmatter() -> None:
    with pytest.raises(PlanContractError, match="no YAML frontmatter"):
        validate_plan({})


@pytest.mark.spec("change-state:plan-contract:rejects-missing-current-phase")
def test_validate_plan_rejects_missing_current_phase() -> None:
    with pytest.raises(PlanContractError, match="current_phase"):
        validate_plan({"phase0": "done"})


@pytest.mark.spec("change-state:plan-contract:rejects-no-phase-flags")
def test_validate_plan_rejects_a_plan_with_no_phase_flags() -> None:
    with pytest.raises(PlanContractError, match="phaseN"):
        validate_plan({"current_phase": "P1", "type": "overview"})


@pytest.mark.spec("change-state:plan-contract:rejects-non-code-status")
def test_validate_plan_rejects_a_non_code_phase_status() -> None:
    with pytest.raises(PlanContractError, match="non-code"):
        validate_plan({"current_phase": "P1", "phase0": "research"})


@pytest.mark.spec("change-state:plan-contract:accepts-conforming")
def test_validate_plan_accepts_all_code_phase_statuses() -> None:
    validate_plan(
        {
            "current_phase": "P2",
            "phase0": "done",
            "phase1": "wip",
            "phase2": "planned",
            "phase3": "todo",
        }
    )


@pytest.mark.spec("change-state:plan-contract:refuses-malformed-at-read")
def test_read_plan_state_refuses_a_malformed_plan(tmp_path: Path) -> None:
    plans = tmp_path / "implementation_plans"
    plans.mkdir()
    (plans / "v0.1_x_implementation_plan.md").write_text("# no frontmatter here\n")

    with pytest.raises(PlanContractError):
        read_plan_state(tmp_path, tmp_path, head_reader=lambda repo: "h")


# --- vault-write preflight (P7) ---


def _write_settings(repo: Path, additional: list[str]) -> None:
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "settings.local.json").write_text(
        json.dumps({"permissions": {"additionalDirectories": additional}})
    )


@pytest.mark.spec("change-state:vault-preflight:grant-passes")
def test_verify_vault_access_passes_when_the_vault_is_granted(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    _write_settings(repo, [str(vault)])
    verify_vault_access(repo, vault)


@pytest.mark.spec("change-state:vault-preflight:ancestor-grant-passes")
def test_verify_vault_access_accepts_an_ancestor_grant(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vaults" / "project"
    _write_settings(repo, [str(tmp_path / "vaults")])
    verify_vault_access(repo, vault)


@pytest.mark.spec("change-state:vault-preflight:missing-settings-fails")
def test_verify_vault_access_fails_without_settings(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="settings.local.json"):
        verify_vault_access(tmp_path, tmp_path / "vault")


@pytest.mark.spec("change-state:vault-preflight:ungranted-fails")
def test_verify_vault_access_fails_when_the_vault_is_not_granted(
    tmp_path: Path,
) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    _write_settings(repo, [str(tmp_path / "elsewhere")])
    with pytest.raises(PreflightError, match="vault"):
        verify_vault_access(repo, vault)


# --- in-tree change-state reader (0003 phase 2) ---


_PROGRESS = (
    "# Tasks\n\nintro prose\n\n"
    "**Per-phase ritual.** bullets here.\n\n"
    "## Progress\n\n"
    "- [x] 1 — First phase\n"
    "- [ ] 2 — Second phase\n"
    "- [ ] 3 — Third phase\n\n"
    "---\n\n"
    "## Phase 1 — First phase\n\nbody with a stray - [ ] 9 — not a progress item\n"
)


def _write_change(
    repo: Path,
    change_id: str = "0003-x",
    progress: str = _PROGRESS,
    proposal: str = "---\nversion: v0.1\n---\n\n# proposal\n",
) -> Path:
    """Write a well-formed change dir (four artifacts) under repo/openspec/changes/."""
    change_dir = repo / "openspec" / "changes" / change_id
    change_dir.mkdir(parents=True)
    (change_dir / "specs").mkdir()
    (change_dir / "proposal.md").write_text(proposal)
    (change_dir / "design.md").write_text("# design\n")
    (change_dir / "tasks.md").write_text(progress)
    return change_dir


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_parse_progress_reads_checked_and_unchecked_items() -> None:
    phases = parse_progress(_PROGRESS)
    assert [(p.index, p.done) for p in phases] == [(1, True), (2, False), (3, False)]
    assert phases[1].title == "Second phase"


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_parse_progress_stops_at_the_next_heading() -> None:
    # The stray checkbox under '## Phase 1' must not leak into the phase list.
    phases = parse_progress(_PROGRESS)
    assert [p.index for p in phases] == [1, 2, 3]


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_select_change_picks_highest_id_excluding_archive(tmp_path: Path) -> None:
    changes = tmp_path / "openspec" / "changes"
    (changes / "0001-old").mkdir(parents=True)
    (changes / "0003-active").mkdir()
    (changes / "archive" / "0099-archived").mkdir(parents=True)

    assert select_change(tmp_path).name == "0003-active"


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_select_change_refuses_a_repo_with_no_active_change(tmp_path: Path) -> None:
    (tmp_path / "openspec" / "changes" / "archive").mkdir(parents=True)
    with pytest.raises(PlanContractError, match="no active change"):
        select_change(tmp_path)


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_change_advanced_needs_a_new_commit_and_a_moved_phase() -> None:
    before = ChangeState(
        "0003-x", (Phase(1, "a", False), Phase(2, "b", False)), "h0", "v0.1"
    )
    moved = ChangeState(
        "0003-x", (Phase(1, "a", True), Phase(2, "b", False)), "h1", "v0.1"
    )

    assert change_advanced(before, moved) is True
    # a commit but the phase index did not move → not advanced
    assert (
        change_advanced(before, ChangeState("0003-x", before.phases, "h1", "v0.1"))
        is False
    )
    # the phase moved but no new commit landed → not advanced (un-gameable)
    assert (
        change_advanced(before, ChangeState("0003-x", moved.phases, "h0", "v0.1"))
        is False
    )


@pytest.mark.spec("sdd:change-structure:wellformed-resolves")
def test_read_change_state_resolves_ordered_phases_current_first_unchecked(
    tmp_path: Path,
) -> None:
    _write_change(tmp_path)

    state = read_change_state(tmp_path, head_reader=lambda repo: "abc123")

    assert state.change_id == "0003-x"
    assert [p.index for p in state.phases] == [1, 2, 3]
    assert state.phases[0].done is True
    assert state.phases[1].done is False
    assert state.current is not None
    assert (state.current.index, state.current.title) == (2, "Second phase")
    assert state.is_complete is False
    assert state.head == "abc123"


@pytest.mark.spec("sdd:change-structure:wellformed-resolves")
def test_read_change_state_marks_a_fully_checked_change_complete(
    tmp_path: Path,
) -> None:
    progress = "## Progress\n\n- [x] 1 — a\n- [x] 2 — b\n\n---\n\n## Phase\n"
    _write_change(tmp_path, progress=progress)

    state = read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert state.is_complete is True
    assert state.current is None
    assert state.current_index is None


@pytest.mark.spec("sdd:change-structure:wellformed-resolves")
def test_read_change_state_resolves_the_active_change_over_archive(
    tmp_path: Path,
) -> None:
    _write_change(tmp_path, change_id="0002-active")
    archived = tmp_path / "openspec" / "changes" / "archive" / "0099-old"
    archived.mkdir(parents=True)  # a bare archived dir must not be resolved

    state = read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert state.change_id == "0002-active"


@pytest.mark.spec("sdd:change-structure:missing-artifact-refused")
@pytest.mark.parametrize("missing", ["proposal.md", "design.md", "tasks.md", "specs"])
def test_read_change_state_refuses_a_change_missing_an_artifact(
    tmp_path: Path, missing: str
) -> None:
    change_dir = _write_change(tmp_path)
    target = change_dir / missing
    target.rmdir() if target.is_dir() else target.unlink()

    with pytest.raises(PlanContractError, match=missing):
        read_change_state(tmp_path, head_reader=lambda repo: "h")


@pytest.mark.spec("sdd:change-structure:version-declared-in-proposal")
def test_read_change_state_carries_the_version_declared_in_the_proposal(
    tmp_path: Path,
) -> None:
    _write_change(tmp_path, proposal="---\nversion: v0.6\n---\n\n# proposal\n")

    state = read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert state.version == "v0.6"


@pytest.mark.spec("sdd:change-structure:missing-version-refused")
@pytest.mark.parametrize(
    "proposal",
    [
        "# proposal with no frontmatter\n",
        "---\ntitle: no version key\n---\n\n# proposal\n",
        "---\nversion: 0.6\n---\n\n# proposal\n",
        "---\nversion: v0.6.1\n---\n\n# proposal\n",
        "---\nversion:\n---\n\n# proposal\n",
    ],
)
def test_read_change_state_refuses_a_change_with_no_declared_version(
    tmp_path: Path, proposal: str
) -> None:
    _write_change(tmp_path, proposal=proposal)

    with pytest.raises(PlanContractError) as excinfo:
        read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert "proposal.md" in str(excinfo.value)
    assert "version" in str(excinfo.value)


@pytest.mark.spec("sdd:vault-layout:progress-in-repo")
def test_read_change_state_consults_no_vault_path(tmp_path: Path) -> None:
    # The reader's only inputs are the repo and a head reader — there is no vault
    # parameter, so it structurally cannot hop to a vault plan file. It resolves with
    # no vault present anywhere on disk.
    repo = tmp_path / "repo"
    _write_change(repo)
    seen: dict[str, Path] = {}

    def head_reader(passed_repo: Path) -> str:
        seen["repo"] = passed_repo
        return "h"

    state = read_change_state(repo, head_reader=head_reader)

    assert state.current is not None and state.current.index == 2
    assert seen["repo"] == repo


@pytest.mark.spec("sdd:change-structure:wellformed-resolves")
def test_this_change_archived_tasks_md_stays_well_formed_after_release() -> None:
    # Dogfood: after the v0.3.0 release fold, 0003-sdd-adoption is folded + archived.
    # It stays a well-formed change (four artifacts) whose tasks.md parses to seven
    # fully checked-off phases. `read_change_state` excludes archive/, so the archived
    # change is validated + parsed directly.
    archived = (
        Path(__file__).resolve().parent.parent
        / "openspec"
        / "changes"
        / "archive"
        / "0003-sdd-adoption"
    )

    validate_change(archived)
    phases = parse_progress((archived / "tasks.md").read_text())

    assert [p.index for p in phases] == [1, 2, 3, 4, 5, 6, 7]
    assert all(p.done for p in phases)  # every phase shipped
    assert all(p.title for p in phases)
