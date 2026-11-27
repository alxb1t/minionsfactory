---
bump: minor
version: v0.127
---

# Ship speed

A version spends less time with no model working: the plan check trusts the gate's green run, cheap checks come first and run after every phase, the fixer runs the quick check alone, and a verify's slip of one word no longer meets the cap.

Reading map: [design](design.md) holds the vouching rule, the groups of the check, `--quick`, the phase check, the fixer's order, the clean file with a card not closed, and the test cost; [tasks](tasks.md) holds the phases: the green gate vouches more, cheap first and `--quick`, the phase check collects, the fixer's check and the clean file, the words.

## Why

A version waits on machine time with no model working, most of it here:

- **The plan check** runs each pytest `Verify:` again. A `pytest` with `-n` takes every slot and runs alone, so these run one after another, in task order, behind each other and ahead of the cheap `git grep` checks. The check runs at the close and after each fix, and a rescue's amend makes it run whole again.
- **A failure known in a second** waits for every long run to end. A `-k` that selects no test, after a later phase renamed the test, ended a long check in a fraction of a second of its own.
- **The fixer** runs the whole plan check on a tree the gate has not judged, so nothing is vouched and nothing is kept.
- **A verify file** that says `verdict: clean` and `open_blocking: 0` beside a blocking card still `fixed` goes to a fixer with nothing to fix, burns a round, and meets the cap. The conductor then reads no open card and refuses the grant.

## What Changes

- **Vouching:** with the gate green at the tree, a pytest `Verify:` that expects exit 0 passes unrun also with `-n` or `--numprocesses` and `-k`, over the test files it names, once its collection finds a test.
- **Order:** the plan check judges the cheap reads first, then the quick group — the commands that run no pytest test and no `make`, and the collection of each pytest `Verify:` — then the long runs; a group that fails ends the check.
- **`--quick`:** a new mode runs the quick group alone.
- **Phase check:** the conductor runs `--quick` after each build phase but the last, over every ticked sub-task.
- **Fixer:** `references/fix.md` tells the fixer to run `--quick` before its commit; the script runs the whole check after the fix's gate.
- **Clean file:** a findings file that says clean with no open blocker while a blocking card's Status word is neither `verified` nor `accepted` is malformed: one rewrite worker of the role, then a halt naming the role, the card and the word.
- MODIFIED *A plan check holds the plan to the built tree*: the vouched options, the groups, `--quick`, the fixer's quick run.
- MODIFIED *The converge fixer leaves the plan to the person*: the fixer runs `--quick`, and the whole check runs once after the fix's gate.
- MODIFIED *Converge's conductor is a script*: the clean file with a blocking card not closed is malformed, and a second slip halts.
- ADDED *The conductor runs a quick plan check after each phase*.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *The conductor runs a quick plan check after each phase* is added. *A plan check holds the plan to the built tree*, *The converge fixer leaves the plan to the person* and *Converge's conductor is a script* are edited.

## Impact

- **Code:** `skills/mf-converge/scripts/plan_check.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-ship/scripts/conduct.py`.
- **References:** `skills/mf-converge/references/fix.md`, `skills/mf-converge/references/verify.md`.
- **Tests:** `tests/test_plan_check.py`, `tests/test_converge.py`, `tests/test_conduct.py`.
- **Record:** `docs/decisions.md`, and the living spec through the delta.
- **Behaviour:** a green gate vouches more pytest `Verify:` lines; a failing cheap check ends a plan check before a long run; a phase whose earlier `git grep` no longer holds halts at that phase; a clean file with a blocking card not closed goes to one rewrite worker, then halts.

## Not in this change

- **The gate's own run time,** the fixer's view of coverage, a lighter gate at the release, the cache's expiry, and a gate skipped on an amend of the change's folder: the secret scan and the home-path test read that folder.
- **`cut_check.py`'s output:** the cut's skill and its reviewer read its `match`, `judge` and summary lines.
- **The cut's pack and the models of a build:** the planner writes smaller briefs, and a model trial is read from the ledger. No MF change.
- **The debt's cards `0152·S2` and `0154·S2`:** no task touches their files.
