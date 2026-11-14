---
bump: patch
beside: [0123-linux-ci-green, 0124-structure-rules, 0122-card-title]
---

# Conductor guards

Each guard of the conductor gets the test case it lacks, and `W5` learns the rule that finds the miss.

Reading map: [design](design.md) holds the case each guard gets, [tasks](tasks.md) holds the phases: the sandbox's lists, the push guard, npm and processes, `W5`'s clause.

## Why

The tests audit found guards that no test holds. A test builds its expectation from the list it checks, so deleting an entry shrinks both sides. A guard that is a conjunction has a test where the first conjunct fails, so the others can go and the test stays green.

The audit proved each by a change to the code that left the suite green. The conductor runs outside a worker's sandbox, and these guards keep a worker from reaching the machine. The refactoring series moves this code, and a move can lose a guard no test holds.

## What Changes

- `tests/test_sandboxed.py` holds `SECRETS`, `TOKENS`, `NETWORK` and `HOOKS_OFF` as literals in one test.
- `tests/test_conduct.py` holds one case per conjunct of the push guard `_foreign_commit`, each built so that only that conjunct can halt it.
- A step of `test_a_key_set_after_the_refusal_reaches_nothing` plants a key a URL-addressed push obeys: `url.<decoy>.pushInsteadOf`, with `_urls` held at its read before the plant.
- `test_a_manifest_is_judged_by_the_rows_of_the_cut` loops over a literal of the npm sections `DIRECT` names.
- New cases hold `_clear`'s guard on groups 0 and 1, `reset_stack`'s refusal of a program key, a grant's preconditions, and `_bounded`'s refusal of a FIFO, an oversized file and a link.
- `skills/mf-build/SKILL.md`'s `W5` gains a clause: a guard that is a conjunction has one case per conjunct.

No behaviour of the conductor changes. Each new case is seen red under the audit's named change to the code, then green; the red run goes in the phase's commit body.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change declares `skip_specs: true`: no requirement changes.

## Impact

- `tests/test_sandboxed.py`, `tests/test_conduct.py`, `skills/mf-build/SKILL.md`.
- `skills/mf-ship/scripts/conduct.py` is read, never edited.
- Builds beside `0123-linux-ci-green`, `0124-structure-rules` and `0122-card-title`; it shares only its changelog entry with them.

## Not in this change

- The stations' guards: the gate, `Verify:`, the cut, converge, integrate and the viewer's bind. They are a version of their own.
- The sandbox's real-denial proofs that skip in both automatic gates (tests audit A2): the platform port's pin.
- A mutation tool in the repo. A tool is a feature version, when it is wanted.
- The `Also` items of the audit's findings: they ride with the region's version.
