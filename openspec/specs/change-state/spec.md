# Capability: `change-state` (where-are-we, read from disk)

Reconstruct "where are we" purely from disk — the plan's phase pointer plus git head — and refuse
a malformed plan at read time with a diagnostic rather than a silent empty state or a mid-run
`KeyError`. It also runs the zero-token vault-write preflight so a misconfigured target halts before
spending. This spec captures the **vault-plan reader** and preflight shipped in
`orchestrator/state.py`; each scenario declares `Layers: unit` and is bound to its proving test.

> The **in-tree change reader** (`read_change_state` / `validate_change` — the v0.5 sibling) is
> spec'd under the `sdd` capability (`change-structure`, `vault-layout`); its scenarios fold in on
> release. This file covers the plan reader that the loop runs today.

## Requirements

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

### Requirement: Vault-write preflight

`verify_vault_access` SHALL refuse to run unless the target's `.claude/settings.local.json` grants
the coder write access to the vault (directly or via an ancestor) under `additionalDirectories` — a
misconfigured target halts before any spawn, not mid-run.

#### Scenario: A direct grant passes
- **Key:** `change-state:vault-preflight:grant-passes`
- **Layers:** unit
- **WHEN** the settings grant the vault directory itself
- **THEN** the preflight passes

#### Scenario: An ancestor grant passes
- **Key:** `change-state:vault-preflight:ancestor-grant-passes`
- **Layers:** unit
- **WHEN** the settings grant an ancestor of the vault directory
- **THEN** the preflight passes

#### Scenario: A missing settings file fails
- **Key:** `change-state:vault-preflight:missing-settings-fails`
- **Layers:** unit
- **WHEN** the target has no `.claude/settings.local.json`
- **THEN** a `PreflightError` naming the settings file is raised

#### Scenario: An ungranted vault fails
- **Key:** `change-state:vault-preflight:ungranted-fails`
- **Layers:** unit
- **WHEN** the settings grant only unrelated directories
- **THEN** a `PreflightError` naming the vault is raised
