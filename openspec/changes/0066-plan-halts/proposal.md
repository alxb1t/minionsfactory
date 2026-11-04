---
bump: minor
---

# Plan halts

A plan the code cannot satisfy is caught at the cut, cheaply, not by a build worker halfway through a run.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

isekai, gpunit and MF, 2026-11-02 to -04: nine build halts came from the cut's plan — a `grep` check matching an untouched line
(`720px`, `"stock_wait"`, `(D25)`), a needle the text could never hold, a loop the worker's shell forbids, a deletion a test still
read, a target rule against `T2`, a design premise the CSS ruled out, and a `Verify:` edited in the tree with nothing to name it.
Each cost the person an amend and a re-run. The cut read every check and ran none, and read none of the target's own rules.

## What Changes

- **`verify_check.py`** — the cut runs each search's pattern at `HEAD`, as argv, and checks `I19`.
- **`I19`** — a `Verify:` is one plain command; an exact count only when the count is the point.
- **Readers and rules** — Step 3 `git grep`s what a change deletes; the cut reads `CODING_STANDARDS.md` and `CONTRIBUTING.md`,
  a target's own test rule over `T1`–`T6`.
- **A plan review** — a fresh read-only worker before the commit; the cut fixes the simple doubts, a decision goes to the person.
- **No gate at the cut** — `openspec validate`, the plan check and the search script; `I3` reworded.
- **The edited check** — `gate_check.py --change` compares every `Verify:` with the cut and its amends; the build runs it before
  each phase's first `Verify:`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A Verify: is one plain command and counts honestly* — ADDED: `I19` and the script's exits.
  - *A fresh worker reviews the plan before the cut commits* — ADDED: the review, the fixes, the readers, the standards.
  - *The build refuses an edited Verify:* — ADDED: the comparison and where the build runs it.
  - *The cut runs no check before the human reads it* — MODIFIED: the search patterns run, no gate.
  - *The cut commits without waiting, unless it adds a dependency* — MODIFIED: a plan-review doubt left to the person waits.
  - *Every station closes in a few sentences and names the next act* — MODIFIED: the cut reports its checks' exit codes.

## Impact

Changes `skills/mf-cut-change/SKILL.md`, `skills/mf-cut-change/scripts/verify_check.py` (new), `skills/mf-build/SKILL.md`,
`skills/mf-converge/scripts/gate_check.py`, `docs/decisions.md` (D7, D38, D40, D46), `docs/principles.md`,
`tests/test_verify_check.py` (new), `tests/test_gate_check.py`, `tests/test_skills.py` and `CHANGELOG.md`'s calibration record.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A cut that settles a decision itself; the build amending a `Verify:`; isekai's one-key rule in its own `CONTRIBUTING.md`;
`0034·R9`; the moved-only premise re-check and the cut's parallel helpers — *lighter cut*.
