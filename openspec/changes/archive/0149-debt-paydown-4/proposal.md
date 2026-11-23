---
bump: patch
version: 0.119.1
debt: [0118·R2, 0119·R4, 0119·R5, 0121·R2, 0134·R2, 0136·R1, 0146·R11, 0146·S16, 0146·S13, 0146·S11, 0120·R6, 0122·S1, 0134·R1, 0146·R5, 0147·R1, 0147·S4]
---

# Debt paydown 4

The debt cards that need no decision and touch no file of the token line's last version: archived lines corrected, live words fixed, one checker row, and the cards the versions since already paid shown paid.

Reading map: [design](design.md) holds one decision per kind of card and the before and after of each edited line, [tasks](tasks.md) holds the phases.

## Why

Cards wait in the debt that need no decision. Most are a stale line of an archived change or a live text, one is a row of the cut's checker, and others were fixed by later versions with their cards left open. None touches a file `0148-run-fields` edits, so this version waits for nothing.

## What Changes

- The archived lines of `0118-debt-paydown-3a`, `0119-debt-paydown-3b`, `0099-stacked-builds`, `0100-worker-diet`, `0104-codex-limits`, `0121-ui-prepare`, `0134-run-layout` and `0136-status-log` say what the code and the later decisions hold (`0118·R2`, `0119·R4`, `0119·R5`, `0121·R2`, `0134·R2`, `0136·R1`).
- The `CHANGELOG.md` line of v0.117.0's third phase says the cut's `I14` reads each phase line of `tasks.md` (`0146·R11`, `0146·S16`).
- `worker.md` and `verify.md` leave out a fix commit's files in the spec's words: such files stand on its cards (`0146·S13`).
- Row `V8` of `cut_check.py` gives a directory operand each held file's module name, and reads an operand spelled with `./` as the tree spells it (`0146·S11`).
- The cards a later version paid are shown paid by a check of the line each fact names, with no edit (`0120·R6`, `0122·S1`, `0134·R1`, `0146·R5`, `0147·R1`, `0147·S4`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Each fix makes the text or the row meet a requirement already in force; [D1](design.md#d1) says why no delta is written.

## Impact

- Archived, edited on the lines a card names alone: `openspec/changes/archive/0118-debt-paydown-3a/design.md`, `openspec/changes/archive/0118-debt-paydown-3a/proposal.md`, `openspec/changes/archive/0119-debt-paydown-3b/proposal.md`, `openspec/changes/archive/0099-stacked-builds/design.md`, `openspec/changes/archive/0100-worker-diet/design.md`, `openspec/changes/archive/0104-codex-limits/design.md`, `openspec/changes/archive/0121-ui-prepare/design.md`, `openspec/changes/archive/0134-run-layout/design.md` and `openspec/changes/archive/0136-status-log/design.md`.
- Live: `CHANGELOG.md`, `skills/mf-converge/references/worker.md`, `skills/mf-converge/references/verify.md`, `skills/mf-cut-change/scripts/cut_check.py` and `tests/test_cut_check.py`.
- Read for the paid cards, never edited: `openspec/changes/archive/0120-ui-state/design.md`, `skills/mf-build/SKILL.md`, `tests/test_integrate.py`, `tests/test_conduct.py` and `skills/mf-converge/scripts/converge.py`.

## Not in this change

- The cards classed accepted, and the cards left for their own round after `0148-run-fields`.
- Any archived spec delta, any decision's choice, any test under an archived change.
- `0146·S8`, `0145·S5` and the other duplicates: they stay with the cards they repeat.
