# Spec delta — `cli`

## MODIFIED Requirements

### Requirement: Zero-token preflight before spend

Before spawning any role the entry point SHALL run the **change-state** read, refusing a malformed target with a
diagnostic naming the specific problem — no active change under `changes/` outside `archive/`, a change missing one
of its four artifacts, a `tasks.md` with no `## Progress` checklist, or a `proposal.md` with no declared `version`
— rather than spending tokens mid-run. Every refusal SHALL surface as a preflight diagnostic and a non-zero exit;
no unhandled exception class SHALL be reachable from a misconfigured target. The preflight SHALL read nothing
outside the repository: no `.env`, no vault path, no settings grant.

#### Scenario: A misconfigured target is refused before spend
- **Key:** `cli:preflight:refuses-misconfigured-target`
- **Layers:** e2e
- **WHEN** the target's change is malformed or declares no version
- **THEN** the entry point prints a preflight failure naming the specific problem and exits non-zero without
  spawning a role

#### Scenario: A target with no `.env` and no settings grant runs
- **Key:** `cli:preflight:no-env-no-grant-runs`
- **Layers:** unit
- **WHEN** `run` is invoked against a repo carrying a well-formed change, no `.env`, no `VAULT_PROJECT_DIR` and no
  `.claude/settings.local.json` grant
- **THEN** the preflight passes to the change-state read and the first role is spawned — no preflight error, since
  no path outside the repository is resolved

> The vault-write half of this requirement is deleted with the `change-state` capability's *Vault-write preflight*.
> What remains is the half that was always about the repository: is there a well-formed change to build?
