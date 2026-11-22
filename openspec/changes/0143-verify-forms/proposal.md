---
bump: minor
---

# Verify forms

What a `Verify:` may be, and how the cut, the build and the close judge it: one reading of its words, one form for a count, a check at the phase that wrote it, and a limit a repository sets.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) its phases: the judge, the cut, the build and time.

## Why

Runs of other repositories halted on a `Verify:` the cut passed and the close refused. A span read as a command, a count form that no grep prints, a check of the state before an edit that the close ran after it, and a limit of 600 s no repository could change.

The judges disagree today: the cut reads a `Verify:` as text, the build runs it in the worker's shell, and the close runs it through `plan_check.py`. A form the close refuses must fail at the cut, or at the phase that wrote it.

## What Changes

- The plan check's span rule stays as it is. The cut refuses a `Verify:` that puts a command after an output verb in one clause, the form that halted probe 7.
- It compares stdout alone, and shows stderr on a failure.
- It starts a command only while the load is under the core count, and always when none runs.
- It reads a command's limit from the repository's `**Verify timeout:**`, 600 s where none, and `--only` judges a `**HALT CHECK**` sub-task it is named for.
- The cut refuses a count on anything but `grep -c` or `--count` over one file, `-L` and `--files-without-match`, and in a plain `Verify:` a line number, a prose phrase and a `<default>..HEAD` range.
- The build runs a phase's `**HALT CHECK**` sub-tasks first, and each other sub-task's `Verify:` through `plan_check.py --only`, both as one background command waited on once.
- The build's close takes its base from `stacked-on` while it stands.
- Converge's freeze reads a command past its limit as timed out, and raises no card on it alone.
- A line per requirement the delta touches:
  - **A plan check holds the plan to the built tree** — the parser, the compared stream, the load, the limit, `--only` and a HALT CHECK, the build's close.
  - **A Verify: is one plain command and counts honestly** — the count form, the absence form, the plain forms.
  - **A dependent builds on its dependency's built head** — the plan check takes `stacked-on`.
  - **Converge writes the evidence of each freeze** — a timeout is no failure.
  - **The build judges each Verify: with the plan check** — new.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements named above, and one added.

## Impact

- `skills/mf-converge/scripts/plan_check.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-cut-change/scripts/verify_check.py`.
- `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/references/fix.md`, `skills/mf-converge/references/worker.md`.
- `docs/decisions.md` (D72, D74, D79) and `docs/modules.md`; the living spec changes at the release's fold.
- Tests: `tests/test_plan_check.py`, `tests/test_verify_check.py`, `tests/test_converge.py`, `tests/test_staged_writes.py`, and `tests/test_skills.py` and `tests/test_structure.py`, which stay green.

## Not in this change

- A new kind of `Verify:`: a check of the state before an edit is a `**HALT CHECK**` sub-task placed before the edits, and D74 stands.
- isekai's `tools/mutate.py` and its line ranges: a check that names lines runs at its phase, never at the close.
- A `**Verify timeout:**` line in this repository's `AGENTS.md`: 600 s holds here.
- Converge's fixer, which keeps its foreground plan check, and a bound on the whole check.
- The settle, the rescue's routes, the cut's own gate and a run's survival: each is planned when a run halts on it.
