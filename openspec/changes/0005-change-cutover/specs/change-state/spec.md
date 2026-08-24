# Spec delta — capability: `change-state` (where-are-we, read from disk)

v0.5 deletes the vault-plan path (R3). `select_plan`, `read_plan_state`, `validate_plan` and `PlanState` go from
`orchestrator/state.py`, with their tests, and with them three of this capability's four requirements — **Plan
selection**, **Plan-state assembly**, **Plan contract guard**. What the capability holds after this change is the
**Vault-write preflight**, restated below: the deleted plan reader used to fail closed on a bogus vault path by
accident (it globbed the vault before any spawn), so the preflight now resolves and validates the vault itself, and
every refusal in it raises `PreflightError` rather than an exception class the entry point does not catch.

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

## MODIFIED Requirements

### Requirement: Vault-write preflight

The zero-token preflight SHALL resolve the vault from the target's `.env` and refuse to run unless it names an
existing absolute directory **and** the target's `.claude/settings.local.json` grants the coder write access to it
(directly or via an ancestor) under `additionalDirectories` — a misconfigured target halts before any spawn, not
mid-run. Every refusal SHALL raise `PreflightError`: no other exception class — a missing file, a file that is not
valid UTF-8, an unparseable or misshapen settings document — SHALL escape the preflight.

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
- **WHEN** the settings grant only unrelated directories, or grant them in a shape that names none
- **THEN** a `PreflightError` naming the vault is raised

#### Scenario: The vault is declared by the target's .env
- **Key:** `change-state:vault-preflight:vault-declared-in-env`
- **Layers:** unit
- **WHEN** the target's `.env` declares `VAULT_PROJECT_DIR` as an existing absolute directory
- **THEN** the preflight resolves the vault from it

#### Scenario: A target with no .env is refused
- **Key:** `change-state:vault-preflight:missing-env-refused`
- **Layers:** unit
- **WHEN** the target repo has no `.env` to declare its vault
- **THEN** a `PreflightError` naming the `.env` is raised — never a `FileNotFoundError` traceback

#### Scenario: An .env with no vault declaration is refused
- **Key:** `change-state:vault-preflight:missing-vault-key-refused`
- **Layers:** unit
- **WHEN** the target's `.env` carries no `VAULT_PROJECT_DIR`, or carries an empty one
- **THEN** a `PreflightError` naming the field is raised

#### Scenario: A relative vault path is refused
- **Key:** `change-state:vault-preflight:relative-vault-refused`
- **Layers:** unit
- **WHEN** the declared `VAULT_PROJECT_DIR` is a relative path
- **THEN** a `PreflightError` is raised — a relative value would resolve against the operator's working directory

#### Scenario: A vault path that is not a directory is refused
- **Key:** `change-state:vault-preflight:absent-vault-refused`
- **Layers:** unit
- **WHEN** the declared `VAULT_PROJECT_DIR` does not name an existing directory
- **THEN** a `PreflightError` is raised before any spawn — a run never creates the vault, and the fan-out would
  otherwise silently materialise a tree at that path

#### Scenario: Unreadable settings are refused as a preflight diagnostic
- **Key:** `change-state:vault-preflight:malformed-settings-refused`
- **Layers:** unit
- **WHEN** the target's `.claude/settings.local.json` is not valid JSON, or does not hold a JSON object
- **THEN** a `PreflightError` naming the problem is raised — never a `JSONDecodeError` (a `ValueError` sibling the
  entry point does not catch) or an `AttributeError`

#### Scenario: A file the preflight reads that is not UTF-8 is refused
- **Key:** `change-state:vault-preflight:undecodable-file-refused`
- **Layers:** unit
- **WHEN** the target's `.env` or `.claude/settings.local.json` is not valid UTF-8
- **THEN** a `PreflightError` naming the file is raised — never a `UnicodeDecodeError`, the `ValueError` sibling
  that `except OSError` does not catch either

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
