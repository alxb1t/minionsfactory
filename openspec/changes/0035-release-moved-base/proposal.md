---
version: v0.31.3
---

# Release on a moved base

`mf-release` refuses a stale base before it folds, commits or tags, and every station names its default branch
the same way.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the corrected requirement.

## Why

The release checks that the default branch is an ancestor of `HEAD` only after its commit, its tag and its card
deletions. A base that moved meanwhile leaves the change archived and tagged on a stale base, a re-run halts twice,
and no skill says how to get out. Four stations use `<default-branch>` without saying which branch it is.

## What Changes

- **Release precondition 9 — the base has not moved:** checked before the fold; its halt names the merge-in.
- **Step 5.1 stays as the last guard**, its halt naming the person's recovery after a tag.
- **The default branch named once** in `mf-build`, `mf-converge`, `mf-cut-change` and `mf-release`, as `mf-plan`
  names it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, a MODIFIED requirement, corrected:
  - *The release merges and pushes on the person's yes* — the ancestry halt before the fold, the default branch
    named, the recovery after a tag.

## Impact

Changes `skills/mf-release/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and
`skills/mf-cut-change/SKILL.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Worktrees, reservations and the container layout are parallel workspaces' (v0.32); bringing the base in for many
branches and the integrator are serial integration's (v0.33). No station rewrites history: the recovery after a
tag is the person's.
