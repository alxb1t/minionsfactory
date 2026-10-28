---
version: v0.33.1
backlog: [0037·N1, 0034·R3]
---

# Worktree cleanup

The release names a version's worktree and its ignored paths in its one ask, and removes the worktree on yes;
README names the primary after the repository; 0034's scope claim is narrowed to what its check reads.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the corrected requirement.

## Why

Release Step 5.6 keeps a worktree that holds any ignored path, and a built worktree always holds `.venv/` and the
test and lint caches, so the cleanup never runs: v0.33.0 left its worktree behind (`0037·N1`). README's container
tree and runbook call the primary `main/`, but the primary is named after the repository. The 0034 proposal and
the `[0.31.2]` notes claim every weakened gate is caught; its design D7 says a file make reads at parse time is
out of reach (`0034·R3`).

## What Changes

- **Release Step 5's ask names the worktree and its ignored paths**, by name, never by contents.
- **Step 5.6 removes the worktree on yes**, with plain `git worktree remove`; a failed listing keeps it, and a
  refusal is reported, never forced.
- **README's tree and runbook** name the primary `<repo>/`.
- **The 0034 proposal and the `[0.31.2]` entry** claim only what the check reads.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, a MODIFIED requirement, corrected:
  - *The release merges and pushes on the person's yes* — the ask names the worktree and its ignored paths; the
    worktree is removed on yes, its scenarios rewritten.

## Impact

Changes `skills/mf-release/SKILL.md`, `README.md`, `CHANGELOG.md`'s `[0.31.2]` section and
`openspec/changes/archive/0034-gate-recipe-hardening/proposal.md`. The [delta](specs/sdd/spec.md) is folded by
release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

`0034·R9`, a gate that reads a file at parse time, is a design change of its own, due when a change opens
`gate_check.py`. No list of rebuildable outputs, in MF or in a target's `AGENTS.md`. The archived 0036 design keeps
its `<container>/main`: it is a record.
