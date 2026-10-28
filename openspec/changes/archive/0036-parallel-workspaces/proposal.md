---
version: v0.32
---

# Parallel workspaces

Several versions are built at once, each in its own linked worktree beside a primary checkout that stays on the
default branch, sharing one run directory, released one at a time from the primary.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

Two agents writing in one checkout collided on 2026-10-26: a session switched the branch under a running build.
The line assumes one checkout throughout: the cut switches branches in place and checks ids only against the
default branch, every station and script reads `.minions/` from its own directory, and the release merges with
`git switch`, which a linked worktree refuses.

## What Changes

- **The cut makes a worktree** when `AGENTS.md` declares `Worktrees:` — the primary stays on the default branch —
  and runs a declared `Workspace setup:` in it.
- **Ids and versions are reserved** against every open version branch; versions ship in cut order.
- **One run directory**: every station and bundled script resolves `.minions/` beside the primary's git directory;
  converge and the release write the backlog under a lock.
- **The release merges in the primary** worktree, then removes the version's worktree.
- **`mf-plan` checks which versions can run side by side**: a pair touching a file in common is proposed in order.
- **MF declares its workspaces**, for the container layout the person moves it into after this release.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - ADDED *A cut makes a worktree when the repository declares one*.
  - ADDED *A cut reserves its id and version against every open version branch*.
  - ADDED *Every worktree shares the primary's run directory*.
  - ADDED *The plan station checks which versions can run side by side*.
  - MODIFIED *The release merges and pushes on the person's yes* — the merge in the primary, the worktree removed.

## Impact

Changes `skills/mf-cut-change/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`,
`skills/mf-release/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-build/scripts/metrics.py`,
`skills/mf-converge/scripts/gate_check.py`, `scripts/metrics/backlog.py`, their tests, `docs/decisions.md`,
`AGENTS.md` and `README.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The integration queue, bringing the latest base into a branch, the shared files' rules and the catch-up after a
merge-in are serial integration's (v0.33). Host-managed worktrees (`claude -w`, `codex --worktree`) are not used.
The move of MF's checkout into the container is the person's, after this release. The bootstrap templates are
unchanged: the `AGENTS.md` keys are optional.
