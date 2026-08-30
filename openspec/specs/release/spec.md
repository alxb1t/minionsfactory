# Capability: `release` (release verification + preparation)

## Purpose

The run's last deterministic stage: verify every release precondition (a **pure** verdict over
already-gathered facts, the release-time analog of `driver.decide`), then prepare the release
**locally** and hand off to the human to merge + push — the boundary never crosses. This spec
captures the behavior shipped in `orchestrator/release.py`; each scenario declares `Layers: unit` and
is bound to its proving test.

## Requirements

### Requirement: Release-gate preconditions

`verify_release_gate` SHALL return releasable only when every precondition holds — a green gate, all
findings clean, **no deferred-work item in `<repo>/.minions/<version>_backlog.md`**, a free release tag, a
non-empty `[Unreleased]` changelog, and a clean working tree — and otherwise SHALL return the first blocking
reason. **Any list line in the deferred-work file SHALL block**, whatever its checkbox state: an item leaves that
file by being fixed and removed, or exported, never by being ticked. It is pure: it judges facts gathered by the
caller, never gathering them itself.

#### Scenario: All preconditions met is releasable
- **Key:** `release:release-gate:all-met-releasable`
- **Layers:** unit
- **WHEN** the gate is green, findings clean, no deferred work, tag free, changelog non-empty, tree clean
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

#### Scenario: Any deferred-work item blocks release
- **Key:** `release:release-gate:open-backlog-item-blocks`
- **Layers:** unit
- **WHEN** the version's deferred-work file holds any list line, ticked or unticked
- **THEN** the verdict is not `ok`

#### Scenario: A dirty working tree blocks release
- **Key:** `release:release-gate:dirty-tree-blocks`
- **Layers:** unit
- **WHEN** the working tree has uncommitted changes
- **THEN** the verdict is not `ok`

### Requirement: Fail-closed document guards

The changelog guard SHALL fail closed: a missing or empty `[Unreleased]` section SHALL block release rather than
read as all-clear. The deferred-work guard SHALL **not**: a missing `<repo>/.minions/<version>_backlog.md` means
nothing was deferred and SHALL pass. This asymmetry is deliberate — the changelog is a durable tracked document
whose absence signals damage, while the deferred-work file is per-version and lives in ignored run-artifact space,
where absence is the ordinary case. An **unreadable** deferred-work file is neither: a directory at that path, a
broken symlink, a permissions error or a file that is not valid UTF-8 means the guard cannot tell whether work was
deferred, and SHALL block with a reason naming the problem — never a traceback out of the release gate, and never a
silent pass.

#### Scenario: An unreadable deferred-work file blocks
- **Key:** `release:failclosed-guards:backlog-unreadable-blocks`
- **Layers:** unit
- **WHEN** the version's deferred-work file exists but cannot be read as text — a directory at that path, a broken
  symlink, or bytes that are not valid UTF-8
- **THEN** the deferred-work guard blocks with a reason naming the problem, rather than raising or passing

#### Scenario: A missing deferred-work file passes
- **Key:** `release:failclosed-guards:backlog-missing-file-passes`
- **Layers:** unit
- **WHEN** the version's deferred-work file does not exist
- **THEN** the deferred-work guard does not block — nothing was deferred

#### Scenario: An empty deferred-work file passes
- **Key:** `release:failclosed-guards:backlog-clear-passes`
- **Layers:** unit
- **WHEN** the version's deferred-work file exists and holds no list line
- **THEN** the deferred-work guard does not block

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
leave the repo untouched. It SHALL never push or merge, and SHALL write **nothing outside the repository** — the
durable release record is `git log`, `CHANGELOG.md` and the annotated tag.

#### Scenario: A green verdict prepares a local commit and tag
- **Key:** `release:prepare-or-refuse:green-prepares-commit-and-tag`
- **Layers:** unit
- **WHEN** `prepare_release` runs on a green verdict
- **THEN** the changelog is cut, pyproject bumped, a release commit and local tag are made, and the
  handoff describes the merge + push the human must do

#### Scenario: The release writes no record outside the repository
- **Key:** `release:prepare-or-refuse:no-external-record`
- **Layers:** unit
- **WHEN** `prepare_release` runs on a green verdict
- **THEN** every file it writes resolves under the repository — no narrative record outside it is appended to,
  and no parameter naming such a destination is accepted

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
