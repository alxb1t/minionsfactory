---
bump: patch
backlog: [0057·R6, 0057·S1, 0057·S2, 0057·S3, 0057·R7, 0051·R9, 0064·R8, 0057·R5, 0068·S4, 0061·R5, 0061·R7, 0063·R12, 0063·R13, 0063·S5, 0064·S3, 0060·R8]
---

# Paydown

The backlog back to its line: the probe reads `.arch` first and safely, `remove_tree` refuses before git and on a link, the spec,
the principles, the threat model and integrate's wording say what the code does, and the cards already settled close.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The backlog holds 41 cards against a paydown line of 10. Twelve are small, still true at `1df4e7a`, and owned by no other version;
four are fixed, wontfix or obsolete already.

## What Changes

- **The probe's `.arch`** — read right after the mark check, never through a link, at most 64 bytes, and named only when it reads
  as an architecture (`0057·R6`, `0057·S1`).
- **`remove_tree`** — the config refusal first, a link at the cut's path refused, and git's own refusal tested (`0057·S2`,
  `0057·S3`, `0057·R7`).
- **The record** — the stop order and the gate record's link rule in the spec (`0051·R9`, `0064·R8`), `CI not read under mf-ship`
  in the principles (`0057·R5`), the pin gap's run end (`0068·S4`), integrate's additive test, note-halt line and cut-only wording
  (`0061·R5`, `0061·R7`, `0063·R12`).
- **Closed with no code** — `0063·R13`, `0063·S5`, `0064·S3`, `0060·R8`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The skills run the repository's `make gate`* — MODIFIED: no record through a linked `.minions/gate` or staged record.
  - *A person can stop a run* — MODIFIED: the claim goes with its groups, before the stop line.
  - *The ship station takes cut versions to the default branch* — MODIFIED: a released worktree kept on a refused config or a link
    at the cut's path.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/SKILL.md`, `skills/mf-integrate/scripts/integrate.py`,
`docs/principles.md`, `THREAT_MODEL.md` and `tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The cards `THREAT_MODEL.md`'s Known gaps carries by id, `0049·R15`, `0049·S7`, `0050·R11`, `0052·S15`. The cards that need a decision or a design: `0034·R9`, `0049·S5`, `0050·R5`, `0050·S7`, `0060·S6`, `0062·S1`, `0063·S3`, `0064·R6`,
`0064·S4`, `0065·R8`, `0068·S3`, `hand·N1`. The cards `0071-ship-fixes`, `0073-test-speed` and `0074-lighter-cut` close.
