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
