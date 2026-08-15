from pathlib import Path

from orchestrator.state import parse_frontmatter, read_plan_state, select_plan


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
