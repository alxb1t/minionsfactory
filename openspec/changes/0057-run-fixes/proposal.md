---
bump: patch
---

# Run fixes

What isekai's first real `/mf-ship` showed the run does wrong around its stations: the probe passes a worker that cannot
run `make`, a version cut before `main` moved builds against the old gate, and a sandboxed release cannot remove its worktree
or read CI.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

On isekai, 2026-11-02 and -03: a Codex worker's shell ran as `x86_64` and every `/usr/bin` `xcrun` shim failed, while the
probe passed; `0090` and `0091` were cut before `main` changed the gate and `AGENTS.md`, and the first build hit the old gate;
both releases wrote `CI none` though CI ran, because the sandbox keeps `gh` from its config; and both released worktrees were
left, because removing a sibling folder writes its parent, outside the worker's reach.

## What Changes

- **The probe checks the shell's architecture** against the host's native one; a mismatch halts the run.
- **At a run's start, a cut-only version behind `main` gets `main` merged in**, as a dependent does; a version still
  building behind a `main` that changed its gate halts, naming the files and the merge, and one with that merge left
  open and no note halts, naming the commit that finishes it.
- **`conduct.py` removes a released worktree**, at the path the cut made, logging its ignored paths first.
- **A release under `merge=yes` writes `CI not read under mf-ship`**, and leaves its worktree to `conduct.py`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station judges every station from disk* — MODIFIED: the probe's gate checks the architecture.
  - *The ship station takes cut versions to the default branch* — MODIFIED: a version behind `main` at the start; the
    released worktree.
  - *The release merges and pushes on the person's yes* — MODIFIED: under `merge=yes`, `conduct.py` removes the worktree.
  - *The release records the gate's time* — MODIFIED: under `merge=yes`, `CI not read under mf-ship`.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-release/SKILL.md`,
`tests/test_conduct.py` and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Fetching CI times from the conductor; merging `main` into a started build without the person; a fix in Codex for its
translated shell.
