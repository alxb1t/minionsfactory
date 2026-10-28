---
version: v0.33
---

# Serial integration

`mf-integrate` brings each finished version onto the latest default branch, in cut order, and hands what it cannot
settle to the person.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

Versions now build side by side, but the merge-in a moved base needs is by hand: `CHANGELOG.md` conflicts every
time, two branches take the same decision id, a spec fold can overwrite a requirement `main` changed, and converge's
catch-up round would re-read all of `main`'s changes. Release precondition 9 names a `git merge` and stops.

## What Changes

- **`mf-integrate`**, a new station run in the primary: it picks the lowest-id open version, merges the default
  branch into its worktree, applies fixed rules, gates, and commits the merge.
- **A bundled `integrate.py`** for the exact parts: the queue, the CHANGELOG order, decision renumbering, and the
  delta-against-`main` check.
- **A semantic conflict halts with the merge open**, a note holding both intents and a proposal.
- **Converge's catch-up round judges a merge-in by its remerge-diff**, not by `main`'s changes.
- **Release precondition 9 names `/mf-integrate`.**
- **D45**, and *an id in force is never reused or renumbered* in `docs/decisions.md`; README's runbook gains the
  steps the move needed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - ADDED *The integrate station merges the default branch into the next version*.
  - ADDED *The integrate station resolves mechanical conflicts by fixed rules*.
  - ADDED *A semantic conflict is handed to the person with the merge open*.
  - MODIFIED *The release ships only a reviewed head* — the catch-up over a merge-in.
  - MODIFIED *The release merges and pushes on the person's yes* — the halt names `/mf-integrate`.

## Impact

Adds `skills/mf-integrate/SKILL.md`, `skills/mf-integrate/scripts/integrate.py` and `tests/test_integrate.py`. Changes
`skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`, `tests/test_skills.py`, `docs/decisions.md`,
`AGENTS.md` and `README.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none — the standard library, git and make. The gate recipe stays unchanged.

## Not in this change

Running versions side by side here: the pilot is the two versions after this one. No unattended dispatch, scheduler
or model router. No `merge=union`. The station releases nothing and pushes nothing.
