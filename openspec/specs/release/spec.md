# Capability: `release` (release verification + preparation)

The run's last deterministic stage: verify every release precondition (a **pure** verdict over
already-gathered facts, the release-time analog of `driver.decide`), then prepare the release
**locally** and hand off to the human to merge + push — the boundary never crosses. This spec
captures the behavior shipped in `orchestrator/release.py`; each scenario declares `Layers: unit` and
is bound to its proving test.

## Requirements

### Requirement: Release-gate preconditions

`verify_release_gate` SHALL return releasable only when every precondition holds — a green gate, all
findings clean, no open backlog current-release item, a free release tag, a non-empty `[Unreleased]`
changelog, and a clean working tree — and otherwise SHALL return the first blocking reason. It is
pure: it judges facts gathered by the caller, never gathering them itself.

#### Scenario: All preconditions met is releasable
- **Key:** `release:release-gate:all-met-releasable`
- **Layers:** unit
- **WHEN** the gate is green, findings clean, backlog clear, tag free, changelog non-empty, tree clean
- **THEN** the verdict is `ok`

#### Scenario: A red gate blocks release
- **Key:** `release:release-gate:red-gate-blocks`
- **Layers:** unit
- **WHEN** the gathered gate result is red
- **THEN** the verdict is not `ok`

#### Scenario: Unclean or missing findings block release
- **Key:** `release:release-gate:unclean-findings-block`
- **Layers:** unit
- **WHEN** any of the review/security/simplify findings is not clean (changes-requested or absent)
- **THEN** the verdict is not `ok`

#### Scenario: An existing release tag blocks release and is named
- **Key:** `release:release-gate:existing-tag-blocks`
- **Layers:** unit
- **WHEN** the target release tag already exists among the gathered tags
- **THEN** the verdict is not `ok` and the reason names the tag

#### Scenario: An open backlog current-release item blocks release
- **Key:** `release:release-gate:open-backlog-item-blocks`
- **Layers:** unit
- **WHEN** the backlog's current-release section still has an open `- [ ]` item
- **THEN** the verdict is not `ok`

#### Scenario: A dirty working tree blocks release
- **Key:** `release:release-gate:dirty-tree-blocks`
- **Layers:** unit
- **WHEN** the working tree has uncommitted changes
- **THEN** the verdict is not `ok`

### Requirement: Fail-closed document guards

The backlog and changelog guards SHALL fail closed: a missing backlog current-release section, or a
missing or empty `[Unreleased]` changelog section, SHALL block release rather than read as all-clear;
a genuinely clear backlog and a `[Unreleased]` with entries SHALL pass.

#### Scenario: A missing backlog current-release section fails closed
- **Key:** `release:failclosed-guards:backlog-missing-section-blocks`
- **Layers:** unit
- **WHEN** the backlog has no `## Current release (<version>)` section
- **THEN** the backlog guard returns a blocking reason (not all-clear)

#### Scenario: A clear backlog current-release section passes
- **Key:** `release:failclosed-guards:backlog-clear-passes`
- **Layers:** unit
- **WHEN** the backlog's current-release section has no open items
- **THEN** the backlog guard does not block

#### Scenario: An empty `[Unreleased]` blocks release
- **Key:** `release:failclosed-guards:changelog-empty-blocks`
- **Layers:** unit
- **WHEN** the changelog `[Unreleased]` section has no `- ` entries
- **THEN** the changelog guard returns a blocking reason

#### Scenario: A missing `[Unreleased]` section fails closed
- **Key:** `release:failclosed-guards:changelog-missing-section-blocks`
- **Layers:** unit
- **WHEN** the changelog has no `## [Unreleased]` section
- **THEN** the changelog guard returns a blocking reason (not all-clear)

#### Scenario: An `[Unreleased]` with entries passes
- **Key:** `release:failclosed-guards:changelog-with-entries-passes`
- **Layers:** unit
- **WHEN** the changelog `[Unreleased]` section has at least one `- ` entry
- **THEN** the changelog guard does not block

### Requirement: Changelog cut and version bump

On release the CHANGELOG `[Unreleased]` SHALL be promoted to a dated `[X.Y.0]` release with a fresh
empty `[Unreleased]` above it, and the pyproject project version SHALL be bumped to `X.Y.0` while
other lines are preserved.

#### Scenario: The cut promotes `[Unreleased]` to a dated release
- **Key:** `release:changelog-cut:promotes-unreleased-dated`
- **Layers:** unit
- **WHEN** the changelog is cut for a version on a date
- **THEN** a `## [X.Y.0] - <date>` heading appears above the moved entries, below a fresh `[Unreleased]`

#### Scenario: The cut leaves a fresh empty `[Unreleased]`
- **Key:** `release:changelog-cut:leaves-fresh-empty-unreleased`
- **Layers:** unit
- **WHEN** the changelog is cut
- **THEN** the new `[Unreleased]` is empty (the changelog guard would block a re-release)

#### Scenario: The bump sets the project version
- **Key:** `release:version-bump:sets-project-version`
- **Layers:** unit
- **WHEN** pyproject is bumped for a version
- **THEN** the project `version` line becomes `X.Y.0` and the prior version is gone

#### Scenario: The bump preserves other lines
- **Key:** `release:version-bump:preserves-other-lines`
- **Layers:** unit
- **WHEN** pyproject is bumped
- **THEN** non-version lines (name, requires-python) are unchanged

### Requirement: Prepare locally or refuse — never ship

`prepare_release` SHALL, on a green verdict, cut the changelog, bump pyproject, commit, and
annotated-tag locally, returning the human merge+push handoff; on a red verdict it SHALL refuse and
leave the repo untouched. It SHALL never push or merge.

#### Scenario: A green verdict prepares a local commit and tag
- **Key:** `release:prepare-or-refuse:green-prepares-commit-and-tag`
- **Layers:** unit
- **WHEN** `prepare_release` runs on a green verdict
- **THEN** the changelog is cut, pyproject bumped, a release commit and local tag are made, and the
  handoff describes the merge + push the human must do

#### Scenario: A red verdict is refused with no git effect
- **Key:** `release:prepare-or-refuse:red-verdict-refused-no-git`
- **Layers:** unit
- **WHEN** `prepare_release` runs on a red verdict
- **THEN** it returns `REFUSED` with the reason and makes no commit or tag

#### Scenario: A refused release leaves the repo untouched
- **Key:** `release:prepare-or-refuse:refused-leaves-repo-untouched`
- **Layers:** unit
- **WHEN** `prepare_release` refuses
- **THEN** the CHANGELOG and pyproject on disk are unchanged
