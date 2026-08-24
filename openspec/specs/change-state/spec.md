# Capability: `change-state` (where-are-we, read from disk)

Refuse a misconfigured target **before any spend**: this capability holds the zero-token
**vault-write preflight** shipped in `orchestrator/state.py`, which checks that the target grants
the coder write access to the vault before a single role is spawned. Its scenario declares
`Layers: unit` and is bound to its proving test.

> The reader that reconstructs "where are we" is the **in-tree change reader**
> (`read_change_state` / `select_change` / `validate_change` / `change_advanced`), spec'd under the
> `sdd` capability (`change-structure`, `vault-layout`). The vault-plan reader this capability once
> described was deleted in v0.5, along with its three requirements — see the `change-state`
> `## REMOVED Requirements` block in `changes/archive/0005-change-cutover/`.

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
