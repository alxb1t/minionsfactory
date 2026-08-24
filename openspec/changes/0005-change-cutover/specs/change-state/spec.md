# Spec delta — capability: `change-state` (where-are-we, read from disk)

v0.5 deletes the vault-plan path (R3). `select_plan`, `read_plan_state`, `validate_plan` and `PlanState` go from
`orchestrator/state.py`, with their tests, and with them three of this capability's four requirements — **Plan
selection**, **Plan-state assembly**, **Plan contract guard**. What the capability holds after this change is the
**Vault-write preflight**, which is untouched and stays.

The behavior the deleted requirements described is not lost; it moved. The in-tree change reader that replaces
them is spec'd under the `sdd` capability (**Change structure**, **Repository is the source of truth**), and this
change's `sdd` delta restates it at the driver level.

> **This block is authored at build time, not at planning time — deliberately.**
> `specs.collect_spec_keys` discards a REMOVED key from **both** `resolvable` and `shipped` the moment the delta
> declares it, *before* any fold. Author it before the deletion and the nine still-present plan-test markers go
> **dangling**; author it after and the nine shipped scenarios go **orphaned**. There is exactly one green
> ordering, and it is a single commit: this file lands with the code and test deletions. See `../../design.md` §6
> and `../README.md`.

The three shipped requirement blocks are **also hand-deleted** from `openspec/specs/change-state/spec.md` in that
same commit, so the tree stops holding two requirements that assert contradictory behavior the moment the code
stops being able to satisfy either (R8). That does not conflict with this block: `release._apply_fold` skips a
REMOVED block whose title it cannot match, so the fold's REMOVED pass degrades to a no-op.

On release this delta folds into top-level `specs/change-state/spec.md`.

## REMOVED Requirements

### Requirement: Plan selection

`select_plan` SHALL return the highest-version implementation plan under `implementation_plans/`,
ignoring anything under `archive/`.

#### Scenario: The highest-version plan wins, archive is ignored
- **Key:** `change-state:plan-selection:highest-version-ignores-archive`
- **Layers:** unit
- **WHEN** several plans exist across versions, with an older one under `archive/`
- **THEN** the highest-version non-archived plan is selected

### Requirement: Plan-state assembly

The reader SHALL parse a plan's leading YAML frontmatter into `current_phase` plus its `phaseN`
flags (ignoring body lines) and assemble the phase state together with the repo's git head.

#### Scenario: Frontmatter parses current_phase and phase flags
- **Key:** `change-state:plan-state:parses-frontmatter`
- **Layers:** unit
- **WHEN** a plan's leading `---` frontmatter carries `current_phase` and `phaseN` keys
- **THEN** those keys parse out and body lines outside the fence are excluded

#### Scenario: Read assembles the phase state and head
- **Key:** `change-state:plan-state:assembles-phases-and-head`
- **Layers:** unit
- **WHEN** `read_plan_state` runs against a well-formed plan with a head reader
- **THEN** it returns the current phase, the phase flags, and the git head

### Requirement: Plan contract guard

`validate_plan` SHALL refuse a plan that breaks the execution contract at read time with a
diagnostic — a plan with no frontmatter, no `current_phase`, no `phaseN` flags, or a non-code phase
status is refused — while a conforming plan (any recognized code-phase status) is accepted.

#### Scenario: A conforming plan is accepted
- **Key:** `change-state:plan-contract:accepts-conforming`
- **Layers:** unit
- **WHEN** the frontmatter carries `current_phase` and at least one `phaseN` flag with a recognized
  code-phase status
- **THEN** validation passes

#### Scenario: Empty frontmatter is refused
- **Key:** `change-state:plan-contract:rejects-empty-frontmatter`
- **Layers:** unit
- **WHEN** the frontmatter is empty
- **THEN** a `PlanContractError` naming the missing frontmatter is raised

#### Scenario: A missing current_phase is refused
- **Key:** `change-state:plan-contract:rejects-missing-current-phase`
- **Layers:** unit
- **WHEN** the frontmatter has no `current_phase`
- **THEN** a `PlanContractError` naming `current_phase` is raised

#### Scenario: No phase flags is refused
- **Key:** `change-state:plan-contract:rejects-no-phase-flags`
- **Layers:** unit
- **WHEN** the frontmatter has `current_phase` but no `phaseN` flag
- **THEN** a `PlanContractError` naming the missing `phaseN` flags is raised

#### Scenario: A non-code phase status is refused
- **Key:** `change-state:plan-contract:rejects-non-code-status`
- **Layers:** unit
- **WHEN** a `phaseN` flag carries a status outside the recognized code-phase statuses
- **THEN** a `PlanContractError` naming the non-code status is raised

#### Scenario: A malformed plan is refused at read time
- **Key:** `change-state:plan-contract:refuses-malformed-at-read`
- **Layers:** unit
- **WHEN** `read_plan_state` runs against a plan file that breaks the contract
- **THEN** it raises `PlanContractError` rather than returning a silent empty state
