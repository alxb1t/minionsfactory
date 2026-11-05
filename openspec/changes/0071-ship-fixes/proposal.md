---
bump: minor
backlog: [hand·N2, 0070·R8, 0061·R4, 0063·S2, 0057·R9, 0067·R8]
---

# Ship fixes

An integrate and its catch-up under `mf-ship` need no person beyond a real decision: integrate commits the merge, then gates
its worktree; the changelog renumber is a rule; a blocked dependent comes back with its dependency; the person's amend answers a
catch-up or verify halt; the converge fixer leaves the plan alone; and a verify halt gets the run's own diagnosis.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

MF's run of `0067`–`0070` on 2026-11-05 needed the person four times: `0068`'s integrator could not gate the worktree and diff-cover
read 98% on its open merge; `0069` stayed blocked after `0068`'s rejoin; `0070`'s integrate halted on its own `CHANGELOG.md` renumber.
isekai `0095`'s catch-up halted on a `Verify:` its converge fixer had edited, and after the person's amend the next run halted at
once, with no worker.

## What Changes

- **Integrate commits, then gates** — `gate_run.py --tree <path>` gates a worktree from the primary; integrate commits the merge
  first, so diff-cover reads the branch's own lines; a red gate halts with the merge committed, `.red` naming it; a test the union
  broke is fixed once in the merge commit.
- **The changelog renumber** — `integrate.py decisions` renumbers the branch's `[Unreleased]` entries, never recites `CHANGELOG.md`.
- **Dependents come back** — a version blocked by a dependency comes back when that dependency's thread starts again; a rejoin
  re-reads only an unplanned version's plan; a merge commit alone does not mark a version started.
- **An amend answers a halt** — a catch-up or verify halt followed only by the person's amends is answered; a catch-up over merges
  and amends has its own count and passes by rule.
- **The fixer and rescue** — the converge fixer never edits `tasks.md` or `design.md`; Step 7 runs `gate_check`; a verify halt is
  diagnosed by the run, no worker; a rescue proposal names the command the run takes back.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The integrate station merges the default branch into the next version* — MODIFIED: commit, then gate the worktree; a red gate
    after the commit; a broken test fixed in the merge commit.
  - *The release ships only a reviewed head* — MODIFIED: a catch-up over merges and the person's amends has its own count.
  - *A converge halt answered by the person converges afresh* — MODIFIED: the person's amends answer a catch-up or verify halt.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: the selection may hold the person's
    amends.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a red gate halts with the merge committed.
  - *The integrate station renumbers the branch's changelog entries* — ADDED.
  - *A blocked dependent comes back with its dependency* — ADDED.
  - *The converge fixer leaves the plan to the person* — ADDED.
  - *A verify halt is diagnosed by the run* — ADDED: no worker, and a proposal naming the command the run takes back.

## Impact

Changes `skills/mf-converge/scripts/gate_run.py`, `skills/mf-integrate/SKILL.md`, `skills/mf-integrate/scripts/integrate.py`,
`skills/mf-release/SKILL.md`,
`skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-rescue/SKILL.md`,
`docs/decisions.md` (D45, D47, D53), `docs/principles.md`, `tests/test_gate_run.py`, `tests/test_integrate.py`,
`tests/test_conduct.py` and `tests/fake_worker.py`.

Closes `hand·N2`, `0070·R8`, `0061·R4`, `0063·S2`, `0057·R9` and `0067·R8`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A blank-line rule for `_resolve`; edits to `0.59.0`'s released `CHANGELOG.md` entry or the archived `0070-cap-policy` artifacts;
a worker-proof rejoin mailbox (`0063·S3`); replay's rule asymmetry (`0064·R6`); a repeat card under the change's own backlog
heading keeping its grade.
