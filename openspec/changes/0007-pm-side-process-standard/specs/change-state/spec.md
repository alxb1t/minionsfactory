# Spec delta — `change-state`

## REMOVED Requirements

**Authored by phase 10, not before, and not later.** `collect_spec_keys` discards a REMOVED key from *both* the
resolvable and the shipped sets the moment this block exists, so authoring it earlier would have dangled eleven
live test markers and held the gate red until phase 10; authoring it later, after the tests went, would have
orphaned eleven shipped scenarios. The window is one commit wide — *earlier the live markers dangle, later the
shipped scenarios orphan* — so the phase-10 commit deletes `read_vault_dir` and `verify_vault_access` and their
two call sites, deletes the fourteen bound tests, writes this block, and hand-deletes the same requirement from
`openspec/specs/change-state/spec.md`, all at once.

The `### Requirement:` heading below reproduces the shipped requirement's title **exactly**:
`release._apply_fold` matches a REMOVED block to the shipped requirement by title, and the title is what makes
the fold delete the right thing.

**Why removed rather than guarded.** The preflight resolved an absolute path out of an untrusted target's `.env`
and handed it to code that writes there. A guard narrows that; deletion closes it. Nothing downstream needs the
vault any more — findings, the HALT report and the deferred-work file all resolve under the repo's own
`.minions/` — so a target with no `.env`, no key and no settings grant runs normally.

The capability file stays in place as a **tombstone**, the shape it already carries for the reader deleted in the
previous version, rather than the directory being removed.

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
