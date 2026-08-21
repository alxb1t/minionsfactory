import json
from pathlib import Path

import pytest

from orchestrator.state import (
    PlanContractError,
    PreflightError,
    parse_frontmatter,
    read_plan_state,
    select_plan,
    validate_plan,
    verify_vault_access,
)


def test_select_plan_picks_highest_version_ignoring_archive(tmp_path: Path) -> None:
    plans = tmp_path / "implementation_plans"
    (plans / "archive").mkdir(parents=True)
    (plans / "v0.2_a_implementation_plan.md").write_text("x")
    (plans / "v0.10_b_implementation_plan.md").write_text("x")
    (plans / "archive" / "v0.99_old_implementation_plan.md").write_text("x")

    selected = select_plan(tmp_path)

    assert selected.name == "v0.10_b_implementation_plan.md"


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


def test_validate_plan_rejects_a_non_code_phase_status() -> None:
    with pytest.raises(PlanContractError, match="non-code"):
        validate_plan({"current_phase": "P1", "phase0": "research"})


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


def test_verify_vault_access_passes_when_the_vault_is_granted(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    _write_settings(repo, [str(vault)])
    verify_vault_access(repo, vault)


def test_verify_vault_access_accepts_an_ancestor_grant(tmp_path: Path) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vaults" / "project"
    _write_settings(repo, [str(tmp_path / "vaults")])
    verify_vault_access(repo, vault)


def test_verify_vault_access_fails_without_settings(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="settings.local.json"):
        verify_vault_access(tmp_path, tmp_path / "vault")


def test_verify_vault_access_fails_when_the_vault_is_not_granted(
    tmp_path: Path,
) -> None:
    repo, vault = tmp_path / "repo", tmp_path / "vault"
    _write_settings(repo, [str(tmp_path / "elsewhere")])
    with pytest.raises(PreflightError, match="vault"):
        verify_vault_access(repo, vault)
