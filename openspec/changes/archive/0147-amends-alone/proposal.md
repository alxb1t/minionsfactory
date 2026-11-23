---
bump: minor
version: 0.118
---

# Amends alone

Lets the line answer a plan's own faults without a person: a halt is budgeted by its head, the fixer corrects the plan's text, the cut's review asks what else produces a rule's subject, and the models line names the rescue and the supervisor.

Reading map: [design](design.md) holds the decisions and their reach, [tasks](tasks.md) holds the phases: the budgets, the review's question, the fixer, the models parts, the Linux test and the records.

## Why

0146's amend cycles were 36% of its cost and half of its time. Its second halt found the rescue and supervisor budgets spent by a stage, though the rescue could have closed it. Its R7 and R8 were a fixer's right code with a plan text that lagged, which the fixer may not touch. Its plan review passed a rule written as one sentence whose subject the build's commits, a fix commit and the changelog also produce. Its release left one test red on Linux, which assumes `cd` is a program on `PATH`.

## What Changes

- *A halted version is rescued in its run* — MODIFIED: a rescue is counted per halt, a halted sub-task or stage at a halted head; a new head is a new halt; the cap of rescues a version stands.
- *A supervisor answers what the rescue leaves* — MODIFIED: the supervisor's try is counted per halt the same way; its cap stands.
- *The converge fixer leaves the plan to the person* — MODIFIED: the fixer may say what its own fix does in the delta and in the bodies of the decisions, in its fix commit under a `Plan-text:` trailer; `converge.py` holds the paths.
- *One module writes and parses the models file* — MODIFIED: `rescue` and `supervise` are parts of the models line, written as tables.
- *A plan review asks what else produces a rule's subject* — ADDED: the review packet's question covers each requirement the delta adds or changes and each rule a decision states.
- *A fixer's plan-text commit re-plans a stacked dependent* — ADDED: the stack's re-plan test reads a fix commit that edits a decision's body as it reads an amend.
- *Row V7 passes over a command row I19 refuses* — ADDED: the first-word row skips `cd`, a loop and an assignment, so the row reads the same on every host.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements listed above.

## Impact

- `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `skills/mflib/modelsfile.py`, `skills/mf-plan/scripts/brief_check.py` and `skills/mf-cut-change/scripts/cut_check.py`.
- `skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md` and the references `skills/mf-converge/references/fix.md`, `skills/mf-converge/references/worker.md` and `skills/mf-converge/references/verify.md`.
- `docs/decisions.md`: the decisions on the rescue, the supervisor, the fixer, the plan review, the models suggestion and the cut's checker.
- `tests/test_conduct.py`, `tests/test_converge.py`, `tests/test_cut_check.py`, `tests/test_modelsfile.py`, `tests/test_brief_check.py` and `tests/test_skills.py`.

## Not in this change

- The Codex side's dollars, and a price for a Codex window share.
- A change to what the release's gate runs are.
- A budget kept across runs: a version's caps stay a run's memory.
- The run log's fields, the cause words and the load read: they follow in their own version.
- A paydown version: it follows the token line.
