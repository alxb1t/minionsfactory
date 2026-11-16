---
bump: patch
version: 0.101.3
beside: [0126-station-guards]
---

# Test cost

The suite stops paying for work it repeats: repeated rounds, repeated compiles of the conductor, unmarked slow tests, duplicate tests, and waits that assert nothing.

Reading map: [design](design.md) holds the decisions, the `## Tests` table of what goes and what carries it, and the evidence; [tasks](tasks.md) holds the phases: one round, one compile, the slow marks, the duplicates, waits that assert.

## Why

The tests audit finds a fifth of the suite's time in work no assertion needs. `make check` runs the unmarked tests between every build phase of every version, so each phase of the series pays for it again.

```
repeated rounds of one flow      the `_uv_sync` fixture fakes the build the rounds were made to race
the conductor compiled each call every call of `_conduct` compiles the whole script again
slow tests with no `slow` mark   `make check` runs them; `T1` says it should not
duplicate tests                  a test whose proof another test already holds
waits that assert nothing        a missed line shows as a delay, then a later red
```

Each is a test-only fault. The refactoring series moves the conductor under these tests, so their cost is paid at every move.

## What Changes

- `test_three_versions_cut_built_converged_and_closed_at_once` runs one round, not ten; the archived design of `0112-uv-race` says so.
- `tests/conduct_load.py` compiles the conductor once and runs it into a fresh module for each call; `tests/test_conduct.py` and `tests/test_sandboxed.py` load it through that.
- Each unmarked test the build's durations run finds over 5 s carries `slow`.
- Each duplicate is merged or deleted, named in the `## Tests` table of the design with the test that carries it.
- A wait loop in `test_a_dependent_waits_while_its_dependency_works` asserts after it, and `_when_logged` raises when its line never comes.

No behaviour of any script changes. The change declares `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes.

## Impact

- `tests/test_conduct.py`, `tests/test_sandboxed.py`, `tests/test_plan_check.py`, `tests/test_gate_check.py`, `tests/test_stamp.py`, `tests/test_converge.py`, and a new `tests/conduct_load.py`.
- `openspec/changes/archive/0112-uv-race/design.md`: its fifth decision corrected.
- No file of `skills/` or `scripts/` is edited.
- Builds beside `0126-station-guards`. They share `tests/test_converge.py` and `tests/test_gate_check.py`; a conflict there is the integrate station's to settle.

## Not in this change

- Full flows run again to reach one assert, and the cost outside the conductor, both findings of the tests audit: they ride with the region's version.
- `brief_check.py`'s reload of the conductor on each `main()`: the other half of the compile finding, left out by the series' plan.
- The escaped-child drain test of `test_plan_check.py` that can pass without reaching the drain.
- Any other test file's load of a script by `runpy`.
- A mutation tool, and a test cut under 5 s so that it need not be marked.
