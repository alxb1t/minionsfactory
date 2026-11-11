---
bump: minor
debt: [0108·S4]
---

# Faster plan check

The plan check takes seconds, not minutes: a green gate stands for the tests it already ran, the rest run side by side, and no command runs twice.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) its phases.

## Why

`plan_check.py` re-ran every ticked `Verify:` one at a time, and 0110's plan checks took about 10 min each, most of it the whole-suite `pytest` lines the gate had already run. Each fix pass lost much of its wall time to it. Converge's Step 7 has no deadline to stop a hung command (debt `0108·S4`).

## What Changes

- `plan_check.py` runs each distinct command once a check, and prints each task's own line for it ([D1](design.md#d1)).
- A `pytest` `Verify:` that wants only `exits 0` passes unrun when `gate_run.py` holds a green record for the same tree and dry run ([D2](design.md#d2)).
- A result is kept by tree and command in `.minions/plan-check/`, on a settled tree only, and reused ([D3](design.md#d3)).
- The rest run in parallel on the machine's cores, printed in task order; a `pytest` with `-n` runs alone, `make` one at a time, and every `pytest` gets `-p no:cacheprovider` ([D4](design.md#d4)).
- A timed-out command loses its process group, and `sandboxed()` takes a deadline and does the same ([D5](design.md#d5)).
- The fixer and the build's close run the plan check in the foreground, within 600 s ([D6](design.md#d6)).
- `cut_check.py` gains row `V5`: a `pytest` `Verify:` names its test files ([D7](design.md#d7)).
- A catch-up's re-run of the added `Verify:` lines skips what the check skips and runs through the same runner ([D8](design.md#d8)).
- Requirement *A plan check holds the plan to the built tree*: MODIFIED — the parallel runner, the record, the group kill and the foreground run.
- Requirement *A plain command runs in an OS sandbox*: MODIFIED — a deadline.
- Requirement *An answered converge halt gets one amend round*: MODIFIED — the catch-up's re-run skips and runs through the plan check.
- Requirement *A cut's mechanical steps are scripts*: MODIFIED — row `V5`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *A plan check holds the plan to the built tree*, *A plain command runs in an OS sandbox*, *An answered converge halt gets one amend round* and *A cut's mechanical steps are scripts*.

## Impact

- `skills/mf-converge/scripts/plan_check.py` gains the runner, the record and `--only`; `skills/mf-converge/scripts/converge.py` passes the deadline and runs the catch-up through the plan check; `skills/mf-ship/scripts/conduct.py` gains the deadline.
- `skills/mf-cut-change/scripts/cut_check.py` gains `V5`; `skills/mf-cut-change/SKILL.md` names it.
- `skills/mf-converge/references/fix.md` and `skills/mf-build/SKILL.md` say to run the plan check in the foreground.
- `docs/decisions.md` amends the plan-check sentence of D74.
- `tests/test_plan_check.py`, `tests/test_sandboxed.py`, `tests/test_converge.py`, `tests/test_conduct.py` and `tests/test_cut_check.py` hold a case for each behaviour.
- No dependency. Closes debt card `0108·S4`.

## Not in this change

- A compiled rewrite of the check: the time is the commands', not Python's.
- The gate's own speed.
- A cache of the gate's per-test results: the record stands for a whole green gate only.
