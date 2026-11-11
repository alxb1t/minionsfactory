---
bump: minor
version: 0.93
debt: [0100·R4]
---

# Plan review diet

The cut's plan reviews cost less: a script settles what a script can find, and the reviewer judges the rest on a cheaper model.

Reading map: [design](design.md) holds the decisions and the check tables, [tasks](tasks.md) its phases.

## Why

The cut's plan reviews were the dearest worker of a cut beside the cutter's own context, and most of what they raised was found by reading, not judging. Their doubts fell into classes a script can hold: a reader the cut missed, a `Verify:` that cannot run in its place, a record that disagrees with itself. The person's priority is the `mf-ship` line at its lowest token cost.

## What Changes

- The first plan review, and the conditional second, run on Sonnet 5.5 · high. A new decision, **The plan reviews run on Sonnet**, overturns [D71](../../../docs/decisions.md#d71--the-cut-and-converge-read-what-changed)'s rejection of Sonnet reviews and the Opus 5.5 of [D65](../../../docs/decisions.md#d65--a-lighter-plan-review-and-build) and [D74](../../../docs/decisions.md#d74--converges-rounds-are-cut-at-their-causes).
- `cut_check.py` settles `Verify:` sequencing, rows `V1`–`V4`, and the record's consistency, rows `K1`–`K6`, each by name.
- `facts.py readers` finds a changed signature's stand-ins and monkeypatches, a changed file's `runpy` and import readers, and a changed string's readers.
- The packet marks each settled row and each readers line, and the reviewer skips them.
- The reviewer's budget is 25 turns; the cut counts the reviewer's tool calls from its transcript and records an overrun in `cut-notes.md`.
- The cut's reading step for a conversation source names the `### D` headings of `docs/decisions.md` as the index (debt `0100·R4`).
- Requirement *A fresh worker reviews the plan before the cut commits*: MODIFIED — Sonnet 5.5 · high, the 25-turn budget, the overrun record, the settled classes.
- Requirement *A cut's mechanical steps are scripts*: MODIFIED — rows `V1`–`V4` and `K1`–`K6`, the reader kinds.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *A fresh worker reviews the plan before the cut commits* and *A cut's mechanical steps are scripts*.

## Impact

- `skills/mf-cut-change/scripts/cut_check.py` gains the rows; `skills/mf-cut-change/scripts/facts.py` gains the reader kinds.
- `skills/mf-cut-change/SKILL.md` changes Steps 3, 8 and 8.5 and its reading step; `skills/mf-plan/SKILL.md` names the reviewer's model.
- `docs/decisions.md` gains the new decision and amends D65, D71 and D74.
- `tests/test_cut_check.py` and `tests/test_facts.py` hold a case for each check and reader kind.
- No dependency. The 1-hour cache of the cut stays.

## Not in this change

- A Codex plan review: it waits for *Codex converge*, which owns the plumbing.
- Holding an amend by `mf-rescue` or `mf-supervise` to rows `V1`–`V4`: when an amend's `Verify:` again fails to run as written, a check goes where the amend is written ([D10](design.md#d10)).
- A ledger file in this repository for the hypotheses of [D8](design.md#d8): the person's ledger holds them.
