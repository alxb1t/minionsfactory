---
bump: patch
after: [0086-ship-fixes-3, 0087-drift-amends]
debt: [0076·R3, 0079·R5, 0082·R8, 0083·R5, 0083·S3, 0085·R10, 0085·R11, 0071·R7, 0076·R2, 0083·R4, 0084·R4, 0084·R6, 0085·R12, 0049·R15, 0064·S4, 0049·S7, 0049·S5, 0050·R11, 0052·S15, hand·N1]
---

# Debt paydown 2

The debt brought back toward its line: the small cards fixed, the stale archives corrected in place, the stale, fixed and
accepted cards settled closed, and converge's status-log times stamped by a script.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The debt stands far past its watch line ([measured](design.md#context)). Its small cards are one-line fixes, its drift cards
are archived designs the shipped code contradicts, and the rest settled here are stale, fixed or recorded as accepted in
`THREAT_MODEL.md`. None needs a decision.

## What Changes

- **`conduct.py`** — a plain file at `.minions/debt.lock` halts the move as a file, not a lock (`0079·R5`); a re-cut halted on a
  kept worktree names its remedy (`0082·R8`); a request taken at a poll's bottom waits out the poll (`0085·R10`); an amend that
  answers a rescued halt drops the stale diagnosis (`0085·R11`).
- **`mf-ship`'s `cut-halted` row** — a kept-worktree halt is no plan's: a person removes or moves that worktree, then rejoins.
- **`brief_check.py`** — halts on a `## For the cut` item that does not open `<n>. ` and one space, on a head with a second
  `after:`, on a models line not written `- models:` or a second one, and on a line of `## Decisions` or `## For the cut`
  holding whitespace other than a space or a tab (`0083·S3`); its docstring cites a tracked reason (`0083·R5`).
- **The stamp** — `skills/mf-converge/scripts/stamp.py` writes each status-log event and run heading with the clock's time;
  converge's status log takes no time by hand (`hand·N1`).
- **The archives** — the designs of `0071`, `0076`, `0083`, `0084` and `0085`, and `0083`'s proposal, say what the code does
  (`0071·R7`, `0076·R2`, `0083·R4`, `0084·R4`, `0084·R6`, `0085·R12`).
- **`THREAT_MODEL.md`** — *Known gaps* lists only cards still in the debt, and keeps each accepted route as its record.
- **Settled closed** — `0049·R15`, `0049·S7` (stale or fixed) and `0049·S5`, `0050·R11`, `0052·S15`, `0064·S4` (accepted in the
  threat model; `0064·S4`'s filter and merge-driver route is *Known gaps*' config-race line) leave the debt at this release.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Every worktree shares the primary's run directory* — MODIFIED: a file at `.minions/debt.lock` halts the move, named as a
    file (`0079·R5`).
  - *A worker runs in an OS sandbox* — MODIFIED: the run's probe fails when a Claude worker's `init` event lists an MCP server,
    naming it (`0076·R3`).
  - *A hard brief is checked before it is queued* — MODIFIED: an item that does not open `<n>. ` and one space, a head with a
    second `after:`, a models line not written `- models:` or a second one, and a checked line holding whitespace other than
    a space or a tab, halt (`0083·S3`).
  - *Converge keeps a status log* — MODIFIED: each line and run heading is written by `stamp.py`, which takes the clock's
    time, not taken from `date` (`hand·N1`).
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a file at `.minions/debt.lock` is among the halts that
    need the person (`0079·R5`).

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-plan/scripts/brief_check.py`,
`skills/mf-converge/SKILL.md`, `THREAT_MODEL.md`, `tests/test_conduct.py`, `tests/test_brief_check.py`, `tests/test_skills.py`,
and the archived
`design.md` of `0071-ship-fixes`, `0076-context-cost`, `0083-plan-queues`, `0084-ship-fixes-2` and `0085-self-healing-ship`, with
`0083-plan-queues`' `proposal.md`. Adds `skills/mf-converge/scripts/stamp.py` and `tests/test_stamp.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The cards kept — `0034·R9`, `0050·R5`, `0050·S7`, `0060·S6`, `0062·S1`, `0065·R8`, `0068·S3`, `0071·S2`, `0082·S5`,
  `0085·R3`, `0085·S1`, `0085·S2` — design changes or decisions, each at its trigger.
- Editing `.minions/debt.md` — `mf-release` deletes the cards `debt:` lists.
- A decision or a new requirement — this is a patch; the requirements above are corrected, none added.
