# Spec delta — `change-state`

## Pending removal — authored by phase 10, not before

This capability's single requirement — **Vault-write preflight** — is removed by this change, together with all
**eleven** of its `change-state:vault-preflight:*` scenarios and their fourteen bound tests.

**The live `## REMOVED Requirements` block is deliberately not written yet.** `collect_spec_keys` discards a
REMOVED key from *both* the resolvable and the shipped sets the moment the block exists, so authoring it here
would dangle eleven live test markers and hold the gate red from now until phase 10. Authoring it later would
orphan eleven shipped scenarios the instant their tests go. The window is one commit wide, which is why the
precedent for this repo states the rule as *earlier the live markers dangle, later the shipped scenarios orphan*.

**Phase 10 therefore does all of it in one commit:** delete `read_vault_dir` and `verify_vault_access` and their
two call sites, delete the fourteen bound tests, author the live `## REMOVED Requirements` block in this file, and
hand-delete the same requirement block from `openspec/specs/change-state/spec.md`.

The scenarios that go, by key:

- `change-state:vault-preflight:grant-passes`
- `change-state:vault-preflight:ancestor-grant-passes`
- `change-state:vault-preflight:missing-settings-fails`
- `change-state:vault-preflight:ungranted-fails`
- `change-state:vault-preflight:vault-declared-in-env`
- `change-state:vault-preflight:missing-env-refused`
- `change-state:vault-preflight:missing-vault-key-refused`
- `change-state:vault-preflight:relative-vault-refused`
- `change-state:vault-preflight:absent-vault-refused`
- `change-state:vault-preflight:malformed-settings-refused`
- `change-state:vault-preflight:undecodable-file-refused`

**Why removed rather than guarded.** The preflight resolved an absolute path out of an untrusted target's `.env`
and handed it to code that writes there. A guard narrows that; deletion closes it. Nothing downstream needs the
vault any more — findings, the HALT report and the deferred-work file all resolve under the repo's own
`.minions/` — so a target with no `.env`, no key and no settings grant runs normally.

The capability file stays in place as a **tombstone**, the shape it already carries for the reader deleted in the
previous version, rather than the directory being removed.
