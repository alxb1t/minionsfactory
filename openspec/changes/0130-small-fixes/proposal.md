---
bump: patch
after: [0129-queue-cap]
debt: [0107·S1]
---

# Small fixes

Copies of one rule that disagree are made to agree, the cap's missing case is added, and the port's failing real-sandbox case is replaced.

Reading map: [design](design.md) holds the decisions, the test cost and the premise of the debt card, [tasks](tasks.md) holds the phases: a phase and an id, the lock and the card, the prose, the cap's case, the port's case.

## Why

Several places state one rule and disagree:

- Converge reads a ticked phase as `[ xX]`, the conductor and integrate as `[ x]`; on a `tasks.md` with no `## Progress` line converge passes and the other two halt.
- The conductor and integrate take a change id with a trailing or doubled hyphen, which D20 and the conductor's own slug refuse.
- The release's text says the debt lock is waited for 2 minutes, converge for 600 s.
- The release's text and the spec ask for a blocking card `verified`, converge also passes `accepted`.
- `mf-build`, `mf-plan`, `mf-cut-change`, `mf-release` and `mf-integrate` name the run directory with a command substitution, which the conductor's shell rules forbid.
- `mf-converge`'s text omits `evidence.py` and `gate_integrity.py`, which converge loads.

One case is missing: `cap_of`'s `and` can become `or` and no test fails. And the port's real-sandbox case, the cut's hold under the rule, can never pass: it runs `ps`, a setuid binary Seatbelt refuses to run, so CI's macOS job is red. The pin stays where it is until that job is green.

## What Changes

- Converge reads a ticked phase as `[ x]` and halts when `tasks.md` has no `## Progress` list, as the conductor and integrate do.
- The conductor's and integrate's change id is the strict form: no trailing hyphen, no doubled hyphen.
- The release's text and the spec wait ten minutes for the debt lock, as converge does.
- The release passes a blocking card that is `accepted`, as converge does; the release's text, the spec's requirement and its scenario say so.
- Those skills name the run directory in the plain form `mf-rescue` uses, and a test holds every `SKILL.md` free of a command substitution.
- `mf-converge`'s text lists every script converge loads, and a test holds the list against the module map's row.
- A test holds that a resumed counted catch-up halts `cap reached` at round 3.
- The real-sandbox case of the cut's hold goes; a case in its place has one process signal a process its sibling started in a session of its own.
- A premise check that the profile holds the signal rule closes card `0107·S1`; the release clears it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, requirement *Every worktree shares the primary's run directory*: the debt lock is waited for ten minutes, not two.
- `sdd`, requirement *The release reads the findings files' frontmatter and card lines*: a blocking card `verified` or `accepted` passes; a scenario for `accepted` is added.

## Impact

- `skills/mf-converge/scripts/converge.py`, `skills/mf-ship/scripts/conduct.py` and `skills/mf-integrate/scripts/integrate.py`: converge's `PROGRESS` and its halt, the `CHANGE_ID` of the conductor and of integrate.
- `skills/mf-release/SKILL.md`, `skills/mf-converge/SKILL.md` and the run-directory sentence of `skills/mf-build/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md` and `skills/mf-integrate/SKILL.md`.
- `tests/test_converge.py`, `tests/test_integrate.py`, `tests/test_conduct.py`, `tests/test_skills.py` and `tests/test_sandboxed.py`.
- The `sdd` spec, folded from [the delta](specs/sdd/spec.md) by the release.
- `docs/modules.md`: read by a test, not edited.
- `.minions/debt.md`: the release deletes card `0107·S1`.

## Not in this change

- H5, the bootstrap template's missing `Worktrees:` line: it flips an opt-in default, so it is a bootstrap question.
- Any new station, parameter, decision or requirement: this is a patch.
- The rest of the disagreements the audit lists: they go with the version that moves their region.
- The pin's move: it waits for CI's macOS job to be green after this change's push.
