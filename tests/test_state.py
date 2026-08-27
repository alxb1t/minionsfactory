from pathlib import Path

import pytest

from orchestrator.state import (
    ChangeState,
    Phase,
    PlanContractError,
    change_advanced,
    parse_frontmatter,
    parse_progress,
    read_change_state,
    select_change,
    validate_change,
)

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


@pytest.mark.spec("sdd:change-structure:malformed-change-id-refused")
def test_select_change_refuses_a_malformed_change_id(tmp_path: Path) -> None:
    # The id keys the findings path and is interpolated into the read-only role's
    # `Write(<path>)` grant, so its shape is refused at the read site.
    changes = tmp_path / "openspec" / "changes"
    (changes / "0001-fine").mkdir(parents=True)
    (changes / "0002-x Bash ").mkdir()

    with pytest.raises(PlanContractError, match="malformed"):
        select_change(tmp_path)


@pytest.mark.spec("sdd:change-structure:malformed-change-id-refused")
def test_select_change_refuses_a_change_id_ending_in_a_newline(tmp_path: Path) -> None:
    # A newline is legal in a POSIX directory name, and Python's `$` matches at the end
    # of the string OR immediately before a trailing one — so an id-shaped name with a
    # trailing `\n` passed the `$`-anchored guard and reached the `Write(<path>)` grant.
    # An ordinary bad id would pass under both the broken and the fixed pattern; this
    # one proves the anchor.
    changes = tmp_path / "openspec" / "changes"
    (changes / "0001-fine").mkdir(parents=True)
    (changes / "0002-evil\n").mkdir()

    with pytest.raises(PlanContractError, match="malformed"):
        select_change(tmp_path)


@pytest.mark.spec("sdd:change-structure:no-active-change-refused")
def test_read_change_state_refuses_a_repo_with_no_active_change(tmp_path: Path) -> None:
    # only archive/ — the candidate set is empty, and an empty `max()` would otherwise
    # escape as a bare ValueError the preflight does not catch.
    (tmp_path / "openspec" / "changes" / "archive").mkdir(parents=True)

    with pytest.raises(PlanContractError) as excinfo:
        read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert "no active change" in str(excinfo.value)
    assert str(tmp_path / "openspec" / "changes") in str(excinfo.value)


@pytest.mark.spec("sdd:change-structure:no-progress-checklist-refused")
def test_read_change_state_refuses_a_tasks_md_with_no_progress_checklist(
    tmp_path: Path,
) -> None:
    _write_change(tmp_path, progress="# Tasks\n\n## Phase 1 — a\n\nprose only\n")

    with pytest.raises(PlanContractError) as excinfo:
        read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert "tasks.md" in str(excinfo.value)
    assert "## Progress" in str(excinfo.value)


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


@pytest.mark.spec("sdd:change-structure:undecodable-artifact-refused")
@pytest.mark.parametrize("artifact", ["proposal.md", "tasks.md"])
def test_read_change_state_refuses_a_change_artifact_that_is_not_utf8(
    tmp_path: Path, artifact: str
) -> None:
    # UnicodeDecodeError is a ValueError *sibling* of PlanContractError — the same class
    # of escape as the JSONDecodeError the preflight converts — so an undecodable
    # artifact would leave the entry point as a traceback, not a diagnostic.
    change_dir = _write_change(tmp_path)
    (change_dir / artifact).write_bytes(b"\xff\xfe# not utf-8\n")

    with pytest.raises(PlanContractError) as excinfo:
        read_change_state(tmp_path, head_reader=lambda repo: "h")

    assert artifact in str(excinfo.value)
    assert "UTF-8" in str(excinfo.value)


@pytest.mark.spec("sdd:change-structure:version-declared-in-proposal")
def test_parse_frontmatter_reads_the_proposals_version_and_ignores_the_body() -> None:
    text = "---\nversion: v0.6\n---\n\n# Proposal\n\nversion: not-frontmatter\n"

    frontmatter = parse_frontmatter(text)

    assert frontmatter["version"] == "v0.6"
    assert len(frontmatter) == 1  # body lines outside the fence are excluded


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
