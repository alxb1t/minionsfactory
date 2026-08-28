# Capability: sdd

### Requirement: Enforced binding

The system SHALL fail the gate when a shipped scenario has no proving test (an **orphan**) or when a `spec`
marker references a key that resolves to no scenario (a **dangling** marker). A scenario key SHALL resolve
against the union of top-level `specs/` and the active change delta, so that scenarios still being built resolve
during the change. The binding SHALL be **layer-aware**: each scenario declares its applicable layers, and v0.3
enforces the `unit` layer only (the `e2e` layer is reserved).

#### Scenario: Orphan scenario fails
- **Key:** `sdd:enforced-binding:orphan-scenario-fails`
- **Layers:** unit
- **WHEN** `specs check` runs and a scenario in top-level `specs/` that declares the `unit` layer has no `unit`
  test referencing its key
- **THEN** it exits non-zero and names the orphan scenario key

#### Scenario: Dangling marker fails
- **Key:** `sdd:enforced-binding:dangling-marker-fails`
- **Layers:** unit
- **WHEN** `specs check` runs and a `@pytest.mark.spec("<key>")` references a key present in neither top-level
  `specs/` nor any active change delta
- **THEN** it exits non-zero and names the dangling key

#### Scenario: Pending delta scenario resolves
- **Key:** `sdd:enforced-binding:pending-delta-resolves`
- **Layers:** unit
- **WHEN** `specs check` runs and a `spec` marker references a scenario defined only in the active change delta
  (not yet folded into `specs/`)
- **THEN** the marker is treated as resolved (not dangling), and the pending delta scenario is not itself
  orphan-checked until it is folded

#### Scenario: Clean binding passes
- **Key:** `sdd:enforced-binding:clean-passes`
- **Layers:** unit
- **WHEN** `specs check` runs and every shipped `unit` scenario has a proving test and every marker resolves
- **THEN** it exits zero

#### Scenario: No specs is a green no-op
- **Key:** `sdd:enforced-binding:empty-is-noop`
- **Layers:** unit
- **WHEN** `specs check` runs against a tree with no `specs/` and no `spec` markers
- **THEN** it exits zero (there is nothing to bind — the gate step is safe to wire before any spec exists)

### Requirement: Reviewer conformance

The reviewer role SHALL flag a change whose spec delta is **not genuinely implemented**, is **not genuinely
test-backed** (a test that exists for a scenario but does not exercise it), or is **incoherent versus the diff**.
`specs check` proves a proving test *exists*; the reviewer supplies the judgment that it *bites*.

#### Scenario: Nominal-only test is blocking
- **Key:** `sdd:reviewer-conformance:nominal-only-test-blocks`
- **Layers:** e2e
- **WHEN** a scenario is bound to a test that asserts a tautology or otherwise does not exercise the scenario's
  WHEN/THEN
- **THEN** the reviewer records a `blocking` finding that the scenario is not genuinely test-backed

> `Layers: e2e` (reserved): reviewer judgment is a system-boundary behavior proven at the v0.7 e2e/dogfood tier,
> not by a v0.3 unit test. Phase 4's machine-checkable acceptance is structural — the conformance axis is present
> in `prompts/reviewer.md`.

### Requirement: Release fold

The release role SHALL fold the active change's spec delta into top-level `specs/` — **ADDED** requirements are
added, **MODIFIED** requirements overwrite the whole prior requirement, **REMOVED** requirements are deleted —
support a **dry run** that reports the planned edits without writing, **verify** that `specs/` still validates
after folding (halting without moving the change if it does not), be **idempotent** on re-run, and then move the
change to `changes/archive/<id>/`.

#### Scenario: Fold applies the delta
- **Key:** `sdd:release-fold:fold-applied`
- **Layers:** unit
- **WHEN** the release folds a change whose delta ADDs a requirement
- **THEN** top-level `specs/` gains that requirement and the change is moved to `changes/archive/<id>/`

#### Scenario: MODIFIED overwrites the whole requirement
- **Key:** `sdd:release-fold:modified-overwrites-whole`
- **Layers:** unit
- **WHEN** the release folds a delta that MODIFIES an existing requirement
- **THEN** the prior requirement text is replaced in full by the delta's revised text (not patched or appended)

#### Scenario: Invalid specs after fold halts
- **Key:** `sdd:release-fold:invalid-specs-halts`
- **Layers:** unit
- **WHEN** folding would leave `specs/` invalid (an orphan or a malformed requirement)
- **THEN** the release HALTs and the change is not moved to `changes/archive/`

#### Scenario: Dry run writes nothing
- **Key:** `sdd:release-fold:dry-run-writes-nothing`
- **Layers:** unit
- **WHEN** the fold runs in dry-run mode
- **THEN** it reports the planned edits and leaves `specs/` and `changes/` unchanged on disk

#### Scenario: Re-running the fold is idempotent
- **Key:** `sdd:release-fold:idempotent-rerun`
- **Layers:** unit
- **WHEN** the fold runs a second time against an already-folded change
- **THEN** `specs/` is unchanged (no duplicated or double-appended requirement)

### Requirement: Change structure

A change SHALL be a directory `changes/<version-id>/` containing `proposal.md`, `design.md`, `tasks.md`, and a
`specs/` delta — **both `proposal.md` and `design.md` always present** (one standard shape; a small change gets a
brief `design.md`). Its `proposal.md` SHALL declare the release version as leading `version: vX.Y` frontmatter —
the change is the unit of release, so the version travels with it. The change-state reader SHALL resolve the active
change in-tree, derive the current phase from `tasks.md`, and surface the declared version; a contract-guard SHALL
refuse a malformed change at read time with a diagnostic naming the specific problem — no active change, a change
id that is not `<digits>-<lowercase-slug>`, a missing artifact, an artifact that is unreadable or not valid UTF-8,
a `tasks.md` with no `## Progress` checklist, or a `proposal.md` with no parseable `version`.

#### Scenario: Well-formed change resolves in-tree
- **Key:** `sdd:change-structure:wellformed-resolves`
- **Layers:** unit
- **WHEN** the change-state reader runs against a repo whose active `changes/<id>/` has all four artifacts and a
  `tasks.md` progress checklist
- **THEN** it returns the ordered phases with the current phase set to the first unchecked item

#### Scenario: Missing artifact is refused
- **Key:** `sdd:change-structure:missing-artifact-refused`
- **Layers:** unit
- **WHEN** the reader runs against a `changes/<id>/` missing any of `proposal.md`, `design.md`, `tasks.md`, or
  `specs/`
- **THEN** the contract-guard raises a diagnostic error at read time (never a silent empty state)

#### Scenario: No active change is refused
- **Key:** `sdd:change-structure:no-active-change-refused`
- **Layers:** unit
- **WHEN** the reader runs against a repo with no change dir under `changes/` outside `archive/`
- **THEN** it raises a `PlanContractError` naming the changes directory — never an `IndexError`- or
  `ValueError`-class traceback from an empty candidate set

#### Scenario: A malformed change id is refused
- **Key:** `sdd:change-structure:malformed-change-id-refused`
- **Layers:** unit
- **WHEN** the active change directory's name is not `<digits>-<lowercase-slug>`
- **THEN** it raises a `PlanContractError` naming the malformed id — the id keys the findings path and is
  interpolated into the read-only role's write grant, so its shape is refused at the read site rather than carried

#### Scenario: A tasks.md with no progress checklist is refused
- **Key:** `sdd:change-structure:no-progress-checklist-refused`
- **Layers:** unit
- **WHEN** the reader runs against a change whose `tasks.md` has no `## Progress` checklist items
- **THEN** it raises a `PlanContractError` naming `tasks.md` and the missing `## Progress` checklist

#### Scenario: An unreadable change artifact is refused
- **Key:** `sdd:change-structure:undecodable-artifact-refused`
- **Layers:** unit
- **WHEN** the active change's `proposal.md` or `tasks.md` cannot be read as UTF-8 text
- **THEN** it raises a `PlanContractError` naming the artifact — never a `UnicodeDecodeError`, another
  `ValueError` sibling of `PlanContractError` that the entry point's `except` does not catch

#### Scenario: The declared version is read from the proposal
- **Key:** `sdd:change-structure:version-declared-in-proposal`
- **Layers:** unit
- **WHEN** the reader runs against a change whose `proposal.md` carries leading frontmatter declaring `version: v0.6`
- **THEN** the change state carries `v0.6` as the release version, parsed from that frontmatter and from no other
  source

#### Scenario: A change with no declared version is refused
- **Key:** `sdd:change-structure:missing-version-refused`
- **Layers:** unit
- **WHEN** the change's `proposal.md` has no frontmatter, no `version` key, or a `version` value that is not `vX.Y`
- **THEN** the contract-guard raises a `PlanContractError` naming `proposal.md` and the `version` field, at read
  time — before any role is spawned

#### Scenario: Coder reads the change in-tree
- **Key:** `sdd:change-structure:coder-reads-in-tree`
- **Layers:** e2e
- **WHEN** the coder builds a phase
- **THEN** it reads scope and acceptance from the repo `changes/<id>/` and records progress in `tasks.md`, with
  no vault plan hop

> `Layers: e2e` (reserved): the coder is an agent; its in-tree reading is a boundary behavior for the v0.7 tester.
> The unit-provable core (the reader + contract-guard) is the scenarios above.

### Requirement: Repository is the source of truth for change progress

The repository SHALL hold the active change, its progress (`changes/<id>/tasks.md`) **and the roles' working
artifacts** — findings, the HALT report and deferred work, all under `.minions/`. The **driver** SHALL determine
where the work stands with no hop outside the repository. No shipped code, role prompt or doc SHALL name the
retired plan location or its retired vocabulary, and none SHALL name the **retired vault vocabulary** — the
symbols by which the repository once reached a directory outside itself. Both retirements SHALL be scanned over
**one root set**, asserted verbatim so that narrowing it is a visible edit.

#### Scenario: Progress is read from the repo, not the vault
- **Key:** `sdd:vault-layout:progress-in-repo`
- **Layers:** unit
- **WHEN** the driver runs and determines where the work stands
- **THEN** it reads the phase state from the repo `changes/<id>/tasks.md` and consults no external plan file — the
  run drives to completion against a target that has no vault at all

#### Scenario: The retired plan model is named nowhere in code, prompts or docs
- **Key:** `sdd:vault-layout:no-plan-path-references`
- **Layers:** unit
- **WHEN** the shared root set is scanned — `orchestrator/`, `prompts/`, `docs/`, `README.md`, the root
  `CLAUDE.md`, the tracked environment example, `.github/`, `Makefile` and `pyproject.toml`
- **THEN** none of them names the retired plan directory or the retired plan vocabulary — the deleted symbols and the
  `current_phase` pointer the driver no longer reads
- **AND** the scan set excludes the specs themselves, which describe the retirement and must be able to name it, and
  the historical record (`CHANGELOG.md`, `openspec/changes/archive/`), which must keep saying what was true

#### Scenario: The retired vault vocabulary is named nowhere in shipped code, prompts or docs
- **Key:** `sdd:vault-layout:no-retired-vault-vocabulary`
- **Layers:** unit
- **WHEN** the retired vault symbols are scanned for — the declared environment key, the resolved-directory
  parameter in both its spellings, the two deleted preflight functions, and the external release-record symbol
- **THEN** none of them appears, over the **same** root set as the retired-plan needles: `orchestrator/`,
  `prompts/`, `docs/`, `README.md`, the root `CLAUDE.md`, the tracked environment example, `.github/`, `Makefile`
  and `pyproject.toml`
- **AND** the two needle sets share one root set: the split existed only because a retired *plan* needle was live
  check text inside the planning-skill surface, and that surface is deleted
- **AND** no exclusion is declared for any directory inside the scanned roots — the deletions land before the scan
  does, so nothing needs suppressing
- **AND** the exclusions are the specs, the historical record, and `tests/`, where the guard's own needles are
  literals

### Requirement: Full backfill traceability

Under strict checking, the system SHALL require that **every** collected test carries either a `@pytest.mark.spec`
marker binding it to a scenario or an explicit `@pytest.mark.spec_exempt("reason")` — bidirectional traceability,
with a reviewable exemption for genuinely structural tests.

#### Scenario: Untraceable test fails strict check
- **Key:** `sdd:full-backfill:untraceable-test-fails`
- **Layers:** unit
- **WHEN** `specs check --strict` runs and a collected test carries neither a `spec` nor a `spec_exempt` marker
- **THEN** it exits non-zero and names the untraceable test

#### Scenario: Exempt test passes strict check
- **Key:** `sdd:full-backfill:exempt-test-passes`
- **Layers:** unit
- **WHEN** `specs check --strict` runs and a structural test carries `@pytest.mark.spec_exempt("reason")`
- **THEN** that test is accepted as traceable (its reason is on record) and does not fail the check

### Requirement: Commit-to-change traceability

Every code-repo commit for a change SHALL carry a `Change: <id>` git trailer, and the release gate SHALL verify
that every `base..HEAD` commit carries a trailer resolving to an active or archived change — halting the release
if one does not.

#### Scenario: Commit missing the trailer halts release
- **Key:** `sdd:commit-traceability:missing-trailer-halts`
- **Layers:** unit
- **WHEN** the release gate inspects `base..HEAD` and a commit carries no `Change:` trailer
- **THEN** the release HALTs with a reason naming the untrailed commit

#### Scenario: Trailer resolves to a known change
- **Key:** `sdd:commit-traceability:trailer-resolves`
- **Layers:** unit
- **WHEN** the release gate inspects `base..HEAD` and every commit carries a `Change: <id>` trailer whose id
  matches an active or archived change
- **THEN** the trailer predicate passes
