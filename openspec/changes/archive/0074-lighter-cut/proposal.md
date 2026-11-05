---
bump: minor
version: v0.60
backlog: [0066·R12]
---

# Lighter cut

A cut re-checks only the facts whose cited files moved since the brief, reads them with up to four parallel read-only helpers,
and spends its plan review and its show-and-tell on what no script has already run.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The cuts of 2026-11-04 and -05 took 4–17 minutes of work, and up to 35 with waits: each re-checked every fact the brief held, even
at the brief's own commit, read the code one helper at a time, and echoed every `Verify:` and match back. The second plan review
earned its minutes — on `0071` and `0072` it found a missing delta, `Verify:` lines true before the build and a `.red` loop — so it
stays.

## What Changes

- **The brief's `At <sha>`** — `mf-plan` writes the commit its facts were read at under the brief's title.
- **Only moved facts re-checked** — the cut lists the cited paths that changed in `<sha>..HEAD`; a fact on an unmoved path stands,
  a moved one or one with no path is re-checked, and a brief with no `At` line is re-checked whole.
- **Helpers at the cut** — up to four fresh read-only helpers, one per area of moved facts and one per design question, each with
  five minutes before the cut reads its facts itself.
- **A narrower review and show** — the plan reviewer skips the searches `verify_check.py` ran; Step 9 points at `tasks.md` for the
  `Verify:` lines and quotes only the matches.
- **`verify_check.py`** — a link out of the tree no longer crashes a search with a path (`0066·R12`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The cut runs no check before the human reads it* — MODIFIED: Step 9 points at `tasks.md`, and quotes the matches.
  - *A fresh worker reviews the plan before the cut commits* — MODIFIED: the moved-only re-check, the helpers, the reviewer's
    narrower question.
  - *A Verify: is one plain command and counts honestly* — MODIFIED: a tree holding a link out of it exits 2, naming the sub-task.
  - *The plan station writes the brief after every round* — MODIFIED: the `At <sha>, <YYYY-MM-DD>.` line.

## Impact

Changes `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-cut-change/scripts/verify_check.py`,
`docs/decisions.md` (D7, D40) and `tests/test_verify_check.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A tasks-shaped brief; skipping the preamble's documents; scripting the I-table; a conditional second plan review.
