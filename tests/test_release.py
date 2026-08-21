from collections.abc import Sequence
from pathlib import Path

from orchestrator.findings import FindingsState
from orchestrator.gate import GateResult
from orchestrator.release import (
    FakeReleaseGit,
    ReleaseStatus,
    ReleaseVerdict,
    _backlog_blocker,
    _bump_pyproject,
    _changelog_blocker,
    _cut_changelog,
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
    )


def test_open_item_in_current_release_section_blocks_release() -> None:
    assert _backlog_blocker(_BACKLOG_OPEN, "0.2") is not None


def test_clear_current_release_section_does_not_block() -> None:
    assert _backlog_blocker(_BACKLOG_CLEAR, "v0.2") is None


def test_missing_current_release_section_fails_closed() -> None:
    text = "# Backlog\n\n## Future / unversioned\n\n- [x] all closed\n"
    assert _backlog_blocker(text, "v0.2") is not None


def test_unreleased_with_entries_does_not_block() -> None:
    assert _changelog_blocker(_CHANGELOG_READY) is None


def test_empty_unreleased_blocks_release() -> None:
    assert _changelog_blocker(_CHANGELOG_EMPTY) is not None


def test_missin_unreleased_section_fails_closed() -> None:
    text = "# Changelog\n\n## [0.1.0] — 2026-08-17\n\n- initial\n"
    assert _changelog_blocker(text) is not None


def test_all_preconditions_met_is_releasable() -> None:
    assert _verify().ok is True


def test_red_gate_blocks_release() -> None:
    assert _verify(gate_result=_RED).ok is False


def test_unclean_findings_block_release() -> None:
    assert _verify(findings=(_CLEAN, _REQUESTED, _CLEAN)).ok is False


def test_missing_findings_file_blocks_release() -> None:
    assert _verify(findings=(_CLEAN, None, _CLEAN)).ok is False


def test_open_backlog_item_blocks_release() -> None:
    assert _verify(backlog_text=_BACKLOG_OPEN).ok is False


def test_existing_release_tag_blocks_release() -> None:
    verdict = _verify(version="v0.2.0", existing_tags=("v0.1.0", "v0.2.0"))
    assert verdict.ok is False
    assert "v0.2.0" in verdict.reason


def test_empty_changelog_blocks_release() -> None:
    assert _verify(changelog_text=_CHANGELOG_EMPTY).ok is False


def test_dirty_tree_blocks_release() -> None:
    assert _verify(tree_is_clean=False).ok is False


def test_cut_changelog_promotes_unreleased_to_a_dated_release() -> None:
    out = _cut_changelog(_CHANGELOG_READY, "v0.2", "2026-08-21")
    assert "## [0.2.0] - 2026-08-21" in out
    # the fresh [Unreleased] sits above the dated release
    assert out.index("## [Unreleased]") < out.index("## [0.2.0]")
    # the entry moved DOWN under the dated release (Unreleased is now empty)
    above_release = out.split("## [0.2.0]")[0]
    assert "a real unreleased entry" not in above_release


def test_cut_changelog_leaves_a_fresh_empty_unreleased() -> None:
    out = _cut_changelog(_CHANGELOG_READY, "v0.2", "2026-28-21")
    assert _changelog_blocker(out) is not None  # empty again — nothing to release yet


def test_bump_pyproject_sets_the_project_version() -> None:
    text = '[project]\nname = "minions-factory"\nversion = "0.1.0"\n'
    out = _bump_pyproject(text, "v0.2")
    assert 'version = "0.2.0"' in out
    assert 'version = "0.1.0"' not in out


def test_bump_pyproject_preserves_other_lines() -> None:
    text = '[project]\nname = "x"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    out = _bump_pyproject(text, "v0.2")
    assert 'name = "x"' in out
    assert 'requires-python = ">=3.12"' in out


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
    )

    assert result.status is ReleaseStatus.PREPARED
    assert "## [0.2.0] - 2026-08-21" in (repo / "CHANGELOG.md").read_text()
    assert 'version = "0.2.0"' in (repo / "pyproject.toml").read_text()
    assert git.commits == ["chore(release): v0.2.0"]
    assert git.tags == ["v0.2.0"]
    assert "v0.2.0" in (vault / "release_log.md").read_text()
    assert "git push origin v0.2.0" in result.handoff


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
