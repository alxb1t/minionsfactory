from collections.abc import Sequence
from pathlib import Path

import pytest

from orchestrator.findings import FindingsState
from orchestrator.gate import GateResult
from orchestrator.release import (
    Commit,
    FakeReleaseGit,
    ReleaseStatus,
    ReleaseVerdict,
    _apply_fold,
    _backlog_blocker,
    _bump_pyproject,
    _changelog_blocker,
    _cut_changelog,
    _specs_blocker,
    _trailer_blocker,
    fold_change,
    prepare_release,
    verify_release_gate,
)

# A backlog with one OPEN item in the current-release section,
# and an open item in Future (which must be ignored).
_BACKLOG_OPEN = """\
# MinionsFactory — Backlog

## Current release (`v0.2`) — close before release

- [x] a closed loose end
- [ ] a still-open loose end

## Future / unversioned

- [ ] a deferred feature (NOT release-gating)
"""


# The same, but the current-release section is fully closed.
_BACKLOG_CLEAR = """\
# MinionsFactory — Backlog

## Current release (`v0.2`) — close before release

- [x] a closed loose end

## Future / unversioned

- [ ] a deferred feature (NOT release-gating)
"""


_CHANGELOG_READY = """\
# Changelog

## [Unreleased]

### Added

- a real unreleased entry

## [0.1.0] — 2026-08-17

### Added

- initial release
"""


_CHANGELOG_EMPTY = """\
# Changelog

## [Unreleased]

## [0.1.0] — 2026-08-17

### Added

- initial release
"""


_GREEN = GateResult(passed=True, steps=())
_RED = GateResult(passed=False, steps=())
_CLEAN = FindingsState(verdict="clean", open_blocking=0, round=1, head="h")
_REQUESTED = FindingsState(
    verdict="changes-requested", open_blocking=1, round=1, head="h"
)
_ALL_CLEAN: tuple[FindingsState | None, ...] = (_CLEAN, _CLEAN, _CLEAN)


def _verify(
    *,
    version: str = "v0.2",
    gate_result: GateResult = _GREEN,
    findings: Sequence[FindingsState | None] = _ALL_CLEAN,
    backlog_text: str = _BACKLOG_CLEAR,
    changelog_text: str = _CHANGELOG_READY,
    existing_tags: Sequence[str] = ("v0.1.0",),
    tree_is_clean: bool = True,
    specs_valid: bool = True,
    change_folded: bool = True,
    commits: Sequence[Commit] = (),
    known_change_ids: Sequence[str] = (),
) -> ReleaseVerdict:
    """All preconditions met; override one keyword to break exactly one."""
    return verify_release_gate(
        version=version,
        gate_result=gate_result,
        findings=findings,
        backlog_text=backlog_text,
        changelog_text=changelog_text,
        existing_tags=existing_tags,
        tree_is_clean=tree_is_clean,
        specs_valid=specs_valid,
        change_folded=change_folded,
        commits=commits,
        known_change_ids=known_change_ids,
    )


@pytest.mark.spec("release:release-gate:open-backlog-item-blocks")
def test_open_item_in_current_release_section_blocks_release() -> None:
    assert _backlog_blocker(_BACKLOG_OPEN, "0.2") is not None


@pytest.mark.spec("release:failclosed-guards:backlog-clear-passes")
def test_clear_current_release_section_does_not_block() -> None:
    assert _backlog_blocker(_BACKLOG_CLEAR, "v0.2") is None


@pytest.mark.spec("release:failclosed-guards:backlog-missing-section-blocks")
def test_missing_current_release_section_fails_closed() -> None:
    text = "# Backlog\n\n## Future / unversioned\n\n- [x] all closed\n"
    assert _backlog_blocker(text, "v0.2") is not None


@pytest.mark.spec("release:failclosed-guards:changelog-with-entries-passes")
def test_unreleased_with_entries_does_not_block() -> None:
    assert _changelog_blocker(_CHANGELOG_READY) is None


@pytest.mark.spec("release:failclosed-guards:changelog-empty-blocks")
def test_empty_unreleased_blocks_release() -> None:
    assert _changelog_blocker(_CHANGELOG_EMPTY) is not None


@pytest.mark.spec("release:failclosed-guards:changelog-missing-section-blocks")
def test_missin_unreleased_section_fails_closed() -> None:
    text = "# Changelog\n\n## [0.1.0] — 2026-08-17\n\n- initial\n"
    assert _changelog_blocker(text) is not None


@pytest.mark.spec("release:release-gate:all-met-releasable")
def test_all_preconditions_met_is_releasable() -> None:
    assert _verify().ok is True


@pytest.mark.spec("release:release-gate:red-gate-blocks")
def test_red_gate_blocks_release() -> None:
    assert _verify(gate_result=_RED).ok is False


@pytest.mark.spec("release:release-gate:unclean-findings-block")
def test_unclean_findings_block_release() -> None:
    assert _verify(findings=(_CLEAN, _REQUESTED, _CLEAN)).ok is False


@pytest.mark.spec("release:release-gate:unclean-findings-block")
def test_missing_findings_file_blocks_release() -> None:
    assert _verify(findings=(_CLEAN, None, _CLEAN)).ok is False


@pytest.mark.spec("release:release-gate:open-backlog-item-blocks")
def test_open_backlog_item_blocks_release() -> None:
    assert _verify(backlog_text=_BACKLOG_OPEN).ok is False


@pytest.mark.spec("release:release-gate:existing-tag-blocks")
def test_existing_release_tag_blocks_release() -> None:
    verdict = _verify(version="v0.2.0", existing_tags=("v0.1.0", "v0.2.0"))
    assert verdict.ok is False
    assert "v0.2.0" in verdict.reason


@pytest.mark.spec("release:failclosed-guards:changelog-empty-blocks")
def test_empty_changelog_blocks_release() -> None:
    assert _verify(changelog_text=_CHANGELOG_EMPTY).ok is False


@pytest.mark.spec("release:release-gate:dirty-tree-blocks")
def test_dirty_tree_blocks_release() -> None:
    assert _verify(tree_is_clean=False).ok is False


@pytest.mark.spec("release:changelog-cut:promotes-unreleased-dated")
def test_cut_changelog_promotes_unreleased_to_a_dated_release() -> None:
    out = _cut_changelog(_CHANGELOG_READY, "v0.2", "2026-08-21")
    assert "## [0.2.0] - 2026-08-21" in out
    # the fresh [Unreleased] sits above the dated release
    assert out.index("## [Unreleased]") < out.index("## [0.2.0]")
    # the entry moved DOWN under the dated release (Unreleased is now empty)
    above_release = out.split("## [0.2.0]")[0]
    assert "a real unreleased entry" not in above_release


@pytest.mark.spec("release:changelog-cut:leaves-fresh-empty-unreleased")
def test_cut_changelog_leaves_a_fresh_empty_unreleased() -> None:
    out = _cut_changelog(_CHANGELOG_READY, "v0.2", "2026-28-21")
    assert _changelog_blocker(out) is not None  # empty again — nothing to release yet


@pytest.mark.spec("release:version-bump:sets-project-version")
def test_bump_pyproject_sets_the_project_version() -> None:
    text = '[project]\nname = "minions-factory"\nversion = "0.1.0"\n'
    out = _bump_pyproject(text, "v0.2")
    assert 'version = "0.2.0"' in out
    assert 'version = "0.1.0"' not in out


@pytest.mark.spec("release:version-bump:preserves-other-lines")
def test_bump_pyproject_preserves_other_lines() -> None:
    text = '[project]\nname = "x"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    out = _bump_pyproject(text, "v0.2")
    assert 'name = "x"' in out
    assert 'requires-python = ">=3.12"' in out


@pytest.mark.spec("release:prepare-or-refuse:red-verdict-refused-no-git")
def test_prepare_release_refuses_on_a_red_verdict(tmp_path: Path) -> None:
    git = FakeReleaseGit()
    result = prepare_release(
        ReleaseVerdict(ok=False, reason="gate is red"),
        repo=tmp_path,
        vault_dir=tmp_path,
        version="v0.2",
        today="2026-08-21",
        branch="v0.2_loop_closure",
        git=git,
    )
    assert result.status is ReleaseStatus.REFUSED
    assert result.reason == "gate is red"
    assert git.commits == []
    assert git.tags == []


@pytest.mark.spec("release:prepare-or-refuse:green-prepares-commit-and-tag")
def test_prepare_release_cuts_bumps_commits_and_tags_on_green(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "CHANGELOG.md").write_text(_CHANGELOG_READY)
    (repo / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n')
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "release_log.md").write_text("# Release log\n\n<!-- format -->\n")
    git = FakeReleaseGit()

    result = prepare_release(
        ReleaseVerdict(ok=True, reason=""),
        repo=repo,
        vault_dir=vault,
        version="v0.2",
        today="2026-08-21",
        branch="v0.2_loop_closure",
        git=git,
        change_id="0003-sdd-adoption",
    )

    assert result.status is ReleaseStatus.PREPARED
    assert "## [0.2.0] - 2026-08-21" in (repo / "CHANGELOG.md").read_text()
    assert 'version = "0.2.0"' in (repo / "pyproject.toml").read_text()
    assert git.commits[0].startswith("chore(release): v0.2.0")
    assert (
        "Change: 0003-sdd-adoption" in git.commits[0]
    )  # release commit carries trailer
    assert git.tags == ["v0.2.0"]
    assert "v0.2.0" in (vault / "release_log.md").read_text()
    assert "git push origin v0.2.0" in result.handoff


@pytest.mark.spec("release:prepare-or-refuse:refused-leaves-repo-untouched")
def test_prepare_release_leaves_the_repo_untouched_when_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "CHANGELOG.md").write_text(_CHANGELOG_READY)
    (repo / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n')

    prepare_release(
        ReleaseVerdict(ok=False, reason="working tree has uncommitted changes"),
        repo=repo,
        vault_dir=tmp_path,
        version="v0.2",
        today="2026-08-21",
        branch="b",
        git=FakeReleaseGit(),
    )

    assert 'version = "0.1.0"' in (repo / "pyproject.toml").read_text()
    assert "## [0.2.0]" not in (repo / "CHANGELOG.md").read_text()


# --- spec-delta fold + commit-traceability (0003 phase 5) ---------------------


_DELTA_ADDED = """\
# Spec delta — capability: `cap`

Intro prose that must NOT be folded into the living spec.

## ADDED Requirements

### Requirement: New thing
The system SHALL do the new thing.

#### Scenario: It happens
- **Key:** `cap:new-thing:happens`
- **Layers:** unit
- **WHEN** a trigger
- **THEN** the new thing happens
"""


_TARGET_OLD = """\
# Capability: `cap`

## Requirements

### Requirement: Thing
The system SHALL do the OLD thing.

#### Scenario: Old behaviour
- **Key:** `cap:thing:old`
- **Layers:** unit
- **WHEN** old
- **THEN** old result
"""


_DELTA_MODIFIED = """\
# Spec delta — capability: `cap`

## MODIFIED Requirements

### Requirement: Thing
The system SHALL do the NEW thing.

#### Scenario: New behaviour
- **Key:** `cap:thing:new`
- **Layers:** unit
- **WHEN** new
- **THEN** new result
"""


def _write_delta(repo: Path, change_id: str, capability: str, body: str) -> None:
    """Write a delta spec under openspec/changes/<id>/specs/<capability>/spec.md."""
    delta = repo / "openspec" / "changes" / change_id / "specs" / capability
    delta.mkdir(parents=True)
    (delta / "spec.md").write_text(body)


def _write_target(repo: Path, capability: str, body: str) -> None:
    """Write a shipped spec at openspec/specs/<capability>/spec.md."""
    target = repo / "openspec" / "specs" / capability
    target.mkdir(parents=True)
    (target / "spec.md").write_text(body)


def _always_valid(repo: Path) -> bool:
    return True


def _always_invalid(repo: Path) -> bool:
    return False


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_apply_fold_adds_modifies_and_removes_by_title() -> None:
    target = (
        "# Capability: cap\n\n"
        "### Requirement: Keep\nSHALL keep.\n\n"
        "### Requirement: Thing\nSHALL do OLD.\n"
    )
    from orchestrator.release import _parse_requirement_blocks

    _, delta_blocks = _parse_requirement_blocks(
        "## MODIFIED Requirements\n\n### Requirement: Thing\nSHALL do NEW.\n\n"
        "## REMOVED Requirements\n\n### Requirement: Keep\nSHALL keep.\n"
    )
    new_text, edits = _apply_fold(target, delta_blocks, "cap")
    assert "SHALL do NEW." in new_text
    assert "SHALL do OLD." not in new_text
    assert "### Requirement: Keep" not in new_text
    assert ("modified", "Thing") in edits
    assert ("removed", "Keep") in edits


@pytest.mark.spec("sdd:release-fold:fold-applied")
def test_fold_applies_added_requirement_and_archives(tmp_path: Path) -> None:
    _write_delta(tmp_path, "0007-x", "cap", _DELTA_ADDED)

    result = fold_change(tmp_path, "0007-x", validator=_always_valid)

    assert result.ok is True
    assert result.moved is True
    spec = (tmp_path / "openspec" / "specs" / "cap" / "spec.md").read_text()
    assert "### Requirement: New thing" in spec
    assert "cap:new-thing:happens" in spec
    assert "must NOT be folded" not in spec  # delta preamble discarded
    assert not (tmp_path / "openspec" / "changes" / "0007-x").exists()
    assert (tmp_path / "openspec" / "changes" / "archive" / "0007-x").exists()


@pytest.mark.spec("sdd:release-fold:modified-overwrites-whole")
def test_fold_modified_overwrites_the_whole_requirement(tmp_path: Path) -> None:
    _write_target(tmp_path, "cap", _TARGET_OLD)
    _write_delta(tmp_path, "0007-x", "cap", _DELTA_MODIFIED)

    result = fold_change(tmp_path, "0007-x", validator=_always_valid)

    assert result.ok is True
    spec = (tmp_path / "openspec" / "specs" / "cap" / "spec.md").read_text()
    assert "NEW thing" in spec and "cap:thing:new" in spec
    # the whole prior requirement is replaced, not patched or appended
    assert "OLD thing" not in spec
    assert "cap:thing:old" not in spec
    assert spec.count("### Requirement: Thing") == 1


@pytest.mark.spec("sdd:release-fold:invalid-specs-halts")
def test_fold_halts_and_does_not_move_when_specs_invalid(tmp_path: Path) -> None:
    _write_delta(tmp_path, "0007-x", "cap", _DELTA_ADDED)

    result = fold_change(tmp_path, "0007-x", validator=_always_invalid)

    assert result.ok is False
    assert "invalid" in result.reason
    # the change is NOT moved to archive when the fold leaves specs invalid
    assert (tmp_path / "openspec" / "changes" / "0007-x").exists()
    assert not (tmp_path / "openspec" / "changes" / "archive" / "0007-x").exists()


@pytest.mark.spec("sdd:release-fold:dry-run-writes-nothing")
def test_fold_dry_run_writes_nothing(tmp_path: Path) -> None:
    _write_delta(tmp_path, "0007-x", "cap", _DELTA_ADDED)

    def _must_not_run(repo: Path) -> bool:
        raise AssertionError("validator must not run in dry-run")

    result = fold_change(tmp_path, "0007-x", dry_run=True, validator=_must_not_run)

    assert result.changed is True
    assert result.edits  # planned edits are reported
    assert result.moved is False
    assert not (tmp_path / "openspec" / "specs").exists()  # nothing written
    assert (tmp_path / "openspec" / "changes" / "0007-x").exists()  # not moved


@pytest.mark.spec("sdd:release-fold:idempotent-rerun")
def test_fold_is_idempotent_on_rerun(tmp_path: Path) -> None:
    _write_delta(tmp_path, "0007-x", "cap", _DELTA_ADDED)

    first = fold_change(tmp_path, "0007-x", validator=_always_valid)
    assert first.ok and first.moved and first.changed
    after_first = (tmp_path / "openspec" / "specs" / "cap" / "spec.md").read_text()

    second = fold_change(tmp_path, "0007-x", validator=_always_valid)

    assert second.ok is True
    assert second.changed is False  # nothing to do the second time
    assert second.moved is False  # already archived
    after_second = (tmp_path / "openspec" / "specs" / "cap" / "spec.md").read_text()
    assert after_second == after_first  # no duplicate / double-append
    assert after_second.count("### Requirement: New thing") == 1


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_specs_blocker_blocks_invalid_or_unfolded() -> None:
    assert _specs_blocker(specs_valid=True, change_folded=True) is None
    assert _specs_blocker(specs_valid=False, change_folded=True) is not None
    assert _specs_blocker(specs_valid=True, change_folded=False) is not None


@pytest.mark.spec("sdd:commit-traceability:missing-trailer-halts")
def test_trailer_blocker_blocks_and_names_an_untrailed_commit() -> None:
    commits = (Commit(sha="aaa111", change="0003-x"), Commit(sha="bbb222", change=None))

    reason = _trailer_blocker(commits, ("0003-x",))

    assert reason is not None
    assert "bbb222" in reason


@pytest.mark.spec("sdd:commit-traceability:missing-trailer-halts")
def test_release_gate_blocks_on_an_untrailed_commit() -> None:
    verdict = _verify(
        commits=(Commit(sha="bbb222", change=None),), known_change_ids=("0003-x",)
    )
    assert verdict.ok is False
    assert "bbb222" in verdict.reason


@pytest.mark.spec("sdd:commit-traceability:trailer-resolves")
def test_trailer_blocker_passes_when_every_commit_resolves() -> None:
    commits = (
        Commit(sha="aaa111", change="0003-x"),
        Commit(sha="bbb222", change="0003-x"),
    )
    assert _trailer_blocker(commits, ("0003-x",)) is None


@pytest.mark.spec("sdd:commit-traceability:trailer-resolves")
def test_release_gate_passes_with_all_trailed_and_resolving_commits() -> None:
    verdict = _verify(
        commits=(Commit(sha="aaa111", change="0003-x"),), known_change_ids=("0003-x",)
    )
    assert verdict.ok is True


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_trailer_blocker_blocks_a_trailer_resolving_to_no_known_change() -> None:
    commits = (Commit(sha="ccc333", change="9999-ghost"),)
    reason = _trailer_blocker(commits, ("0003-x",))
    assert reason is not None
    assert "ccc333" in reason
