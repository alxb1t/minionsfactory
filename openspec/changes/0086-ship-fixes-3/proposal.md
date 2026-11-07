---
bump: patch
debt: [0064·R6]
---

# Ship fixes 3

The gaps the 2026-11-06 runs hit, fixed so a run needs no person for them: a decision id the plan cites, taken by the default
branch while the version waits; a delta that only inserts, flagged as a semantic conflict; and a git failure reported as "not in a
git repository".

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`0085-self-healing-ship` planned D59 in its prose alone. The merge of the default branch brought `0083-plan-queues`' built D59, the
decision rule saw no new heading on the branch, and the build halted at its decisions task until a person amended the plan.
The same merge flagged a requirement whose delta only inserted into the default branch's block, a conflict no one had to judge.
`python3 conduct.py` under an Intel Python printed "not in a git repository" for a git that failed on its architecture.

## What Changes

- **A planned decision id renumbered** — `integrate.py decisions` also counts an id the change's plan cites with its title, above
  the base's highest and not yet built, and renumbers it with the branch's new ones; an id whose heading on the default branch
  carries the plan's title is a dependency's, left alone. `gate_check.renumbered` follows the same rule. `conduct.py` and
  `integrate.py replay` run the `decisions` rule on every merge, conflicted or clean, which closes `0064·R6`.
- **An insert-only delta kept** — `integrate.py delta` keeps a MODIFIED requirement whose delta only inserts into the default
  branch's current block, whitespace ignored, and keeps nothing the default branch removed; a delta that changes or removes a line
  of that block, one that keeps what the default branch removed, and every REMOVED title the default branch changed, still flag. `replay` and `conduct.py`'s merge read the same rule.
- **Git's own error** — `conduct.py`'s `primary_of`, `awake.py` and `integrate.py`'s `_tree` say "not in a git repository", or
  "not a worktree root", only when git says so; any other git failure prints git's first stderr line and
  `run it as uv run --script <path>`.
- **The record** — D45 amended; `skills/mf-integrate/SKILL.md`'s `decisions` and `delta` rows.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The integrate station resolves mechanical conflicts by fixed rules* — MODIFIED: the planned id, the dependency's title, the
    `decisions` rule on every merge, the insert-only delta.
  - *A semantic conflict is handed to the person with the merge open* — MODIFIED: a delta that only inserts is no semantic
    conflict.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: replay runs the `decisions` rule on
    every merge, and reads the insert-only delta.

## Impact

Changes `skills/mf-integrate/scripts/integrate.py`, `skills/mf-converge/scripts/gate_check.py`, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-cut-change/scripts/awake.py`, `skills/mf-integrate/SKILL.md`, `docs/decisions.md` (D45), `tests/test_integrate.py`,
`tests/test_conduct.py` and `tests/test_awake.py`.

Closes `0064·R6`. Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- `0034·R9`, a failure hidden in a file the gate reads at parse time — its fix is a design no decision settles; it stays carded,
  per [D5](design.md#d5).
- Amending the archives already released stale, and the stale-archive cards — debt paydown 2.
- The cut reserving a decision id — the merge settles it.
- Drift that wants the person's amend — `drift-amends`, the parallel version.
- A requirement for the git error's text — no requirement states it; the fix is a defect's.
