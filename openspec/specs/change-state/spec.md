# Capability: `change-state` (where-are-we, read from disk)

**A tombstone.** This capability holds no requirement: everything it once described has been deleted, and the
file stays in place to record that rather than the directory being removed.

> The reader that reconstructs "where are we" is the **in-tree change reader**
> (`read_change_state` / `select_change` / `validate_change` / `change_advanced`), spec'd under the
> `sdd` capability (`change-structure`, `vault-layout`). The vault-plan reader this capability once
> described was deleted in v0.5, along with its three requirements — see the `change-state`
> `## REMOVED Requirements` block in `changes/archive/0005-change-cutover/`.

> The zero-token **vault-write preflight** (`read_vault_dir` / `verify_vault_access`) was deleted in v0.7,
> along with its single requirement and all eleven of its scenarios: it resolved an absolute path out of an
> untrusted target's `.env` and handed it to code that writes there, and nothing downstream needs a vault any
> more — findings, the HALT report and the deferred-work file all resolve under the repo's own `.minions/`. See
> the `change-state` `## REMOVED Requirements` block in `changes/archive/0007-pm-side-process-standard/`. What
> survives of the preflight is the half that was always about the repository — the change-state read — spec'd
> under the `cli` capability (*Zero-token preflight before spend*).

## Requirements

*(none — see the tombstone note above)*
