---
bump: patch
version: v0.101.2
debt: [0120·R3]
---

# Station guards

Adds the missing test case for each guard of the gate, `Verify:`, the cut, converge, integrate and the viewer, so a later move cannot delete one unseen.

Reading map: [design](design.md) holds the decisions, the test cost and the premise of the debt card, [tasks](tasks.md) holds a phase for each station.

## Why

Each guard below was removed in a scratch clone and the suite stayed green. A guard with no case is a line a refactoring may drop, and the series that follows moves the code these guards sit in. Each case here is built so that only its own guard can fail it.

```
gate        gate_check.py  plan_problems · gate_makefiles     gate_run.py  gate
            plan_check.py  passed
Verify:     verify_check.py  search · breaks
cut         cut_check.py   row_i4
converge    converge.py    _unfiled · pickup · catch_up · cap_of · blockers · BLOCKS
integrate   integrate.py   merge3 · _git
viewer      viewer.py      the loopback bind
```

## What Changes

- Each guard of the gate gets a second input: a two-task plan, an include outside the tree beside inside ones, a recipe that edits the tree, and a failing command under "prints nothing".
- `Verify:`'s shell refusals get a refusal case for each hole: a short option, a file operand, and a command after an operator. A passing case twins them.
- `row_i4`'s unheld checks get a case each, and the assert that looks for a message the code never prints is replaced.
- Converge gets a second card under a cleared card's heading, a case at round three for each cap path, and a case for an `accepted` card and a `critical` card.
- Integrate gets a table of `merge3` merges at function level and a case where git fails after the worktree is read.
- The viewer's bind address moves into a constant and a server factory, and a test asserts it on port 0.
- Debt card `0120·R3` is closed: its tests already carry the `slow` marker, which the change holds with a premise check.

No behaviour changes. `skip_specs: true`, as 0075 and 0112 were.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `tests/test_gate_check.py`, `tests/test_gate_run.py`, `tests/test_plan_check.py`: phase 1.
- `tests/test_verify_check.py`: phase 2.
- `tests/test_cut_check.py`: phase 3.
- `tests/test_converge.py`: phase 4.
- `tests/test_integrate.py`: phase 5.
- `tests/test_viewer.py` and `skills/mf-ui/scripts/viewer.py`: phase 6.

## Not in this change

- The tests audit's *Also* items for these findings: they ride with the region's version.
- A mutation tool in the repo: a feature version of its own, when wanted.
- The conductor's guards: 0125 landed them.
- Any change to what a station does.
