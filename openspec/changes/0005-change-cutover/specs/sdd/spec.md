# Spec delta — capability: `sdd` (spec-driven development enforcement)

v0.5 makes the in-tree change model the **running** model. Two requirements change: the change structure gains a
declared release **version** and the reader's refusals become individually diagnosable (R4, R7), and the
repository-is-source-of-truth requirement is restated at the level of the **driver** rather than a helper, with the
findings home named and a regression guard against the retired path (R1, R3, R5, R9).

Every MODIFIED requirement below reproduces **all** of its scenarios — surviving ones verbatim — because the fold
replaces the whole requirement block, matched by title. No requirement is retitled.

On release this delta folds into top-level `specs/sdd/spec.md`.

## MODIFIED Requirements

### Requirement: Change structure

A change SHALL be a directory `changes/<version-id>/` containing `proposal.md`, `design.md`, `tasks.md`, and a
`specs/` delta — **both `proposal.md` and `design.md` always present** (one standard shape; a small change gets a
brief `design.md`). Its `proposal.md` SHALL declare the release version as leading `version: vX.Y` frontmatter —
the change is the unit of release, so the version travels with it. The change-state reader SHALL resolve the active
change in-tree, derive the current phase from `tasks.md`, and surface the declared version; a contract-guard SHALL
refuse a malformed change at read time with a diagnostic naming the specific problem — no active change, a missing
artifact, a `tasks.md` with no `## Progress` checklist, or a `proposal.md` with no parseable `version`.

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

#### Scenario: A tasks.md with no progress checklist is refused
- **Key:** `sdd:change-structure:no-progress-checklist-refused`
- **Layers:** unit
- **WHEN** the reader runs against a change whose `tasks.md` has no `## Progress` checklist items
- **THEN** it raises a `PlanContractError` naming `tasks.md` and the missing `## Progress` checklist

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

The repository SHALL hold the active change and its progress (`changes/<id>/tasks.md`); the vault SHALL hold
product intent (PRD), findings (`findings/<change-id>_<role>.md`), and the narrative record. The **driver** SHALL
determine where the work stands with no vault hop, and no shipped code, role prompt or doc SHALL name the retired
plan location.

#### Scenario: Progress is read from the repo, not the vault
- **Key:** `sdd:vault-layout:progress-in-repo`
- **Layers:** unit
- **WHEN** the driver runs and determines where the work stands
- **THEN** it reads the phase state from the repo `changes/<id>/tasks.md` and consults no vault plan file — the
  run drives to completion against a target whose vault holds no plan

#### Scenario: The retired plan location is named nowhere in code, prompts or docs
- **Key:** `sdd:vault-layout:no-plan-path-references`
- **Layers:** unit
- **WHEN** `orchestrator/`, `prompts/`, `docs/` and `README.md` are scanned
- **THEN** none of them names the retired plan directory
- **AND** the scan set excludes the specs themselves, which describe the retirement and must be able to name it, and
  the historical record (`CHANGELOG.md`, `openspec/changes/archive/`), which must keep saying what was true

#### Scenario: Findings and product intent stay in the vault
- **Key:** `sdd:vault-layout:findings-and-prd-in-vault`
- **Layers:** e2e
- **WHEN** a read-only role or the PM authors findings or a PRD
- **THEN** they are written under the vault (`prd/`, `findings/`), keeping the reviewers' repo access
  fully read-only

> `Layers: e2e` (reserved): the vault directory restructure was a one-time hand op; the durable, unit-provable
> invariants are `progress-in-repo` and `no-plan-path-references` above.
