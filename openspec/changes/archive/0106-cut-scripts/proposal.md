---
bump: minor
version: 0.90
debt: [0085·S2, 0103·S3, 0103·R3]
---

# Cut scripts

The cut's mechanical steps become scripts: the LLM writes the plan and judges only what no script can check.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The cut's main session was $3.39 of a $6.99 cut: its preconditions, its moved-fact check, its reader search and its
self-check table are rules a script holds, and the LLM runs them one turn at a time ([evidence](design.md#context)).
This is the first version of the token diet's fourth line: *converge script* and *evidence step* follow, each measured alone.

## What Changes

- **`brief_check.py` reads facts and models** — each `## Facts` line ends `` (`<path>:<line>[-<line>]`[, …] at `<sha>`) ``;
  `--facts <brief>` prints them as JSON and `--models <brief> <slug>` prints the item's models file.
- **`facts.py`** — places each fact at `HEAD`: **stands**, **moved** to a new range, or **unplaced**; `readers <name>…` prints
  the `git grep -nw` hits of a deleted or renamed name. Both write the cut's notes.
- **`cut_pre.py`** — runs every precondition of Step 1, one line a check, by hand or unattended.
- **`cut_check.py`** — decides the mechanical rows of the self-check, folds in `openspec validate`, the gate-edit check, the
  search script and the corpus check, and prints the rows a person or worker must judge.
- **`conduct.py` writes the models file** at queue time from `brief_check.py --models`, holds its text in the queue entry,
  and fails a cut whose file changed (debt `0085·S2`).
- **A tag that only starts like a heading** ends no section, in `brief_check.py` and `conduct.py` (debt `0103·S3`); the
  docstrings card `0103·R3` names are cut to the limit.
- **The record** — `mf-cut-change` and `mf-plan` call the scripts; `plan_check.py`'s old name "plan check" is left to it, and
  `gate_check.py --tasks` is "the gate-edit check"; `tests/test_skills.py` lists the scripts each skill names; a new
  decision, D77, amends D7, D40 and D41.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A fresh worker reviews the plan before the cut commits* — MODIFIED: the packet carries `cut_check.py`'s output; facts
    and readers come from `facts.py`; a helper starts only for an unplaced fact.
  - *An unattended cut decides by the brief's switch* — MODIFIED: the cut no longer writes `models.toml`.
  - *The cut checks the brief's `At` value before any command takes it* — MODIFIED: `facts.py` takes the value.
  - *A hard brief is checked before it is queued* — MODIFIED: the facts grammar, `--facts`, `--models`.
  - *Model suggestions use exposed capabilities* — MODIFIED: who writes the brief's models.
  - *A cut's mechanical steps are scripts* — ADDED: `cut_pre.py`, `facts.py`, `cut_check.py`; the continued brief's re-measure.
  - *A queued cut's models file is written by the queue* — ADDED: the text in the entry, the hash the cut check holds.
  - *A tag that only starts like a heading ends no section* — ADDED: both section readers.

## Impact

Changes `skills/mf-plan/scripts/brief_check.py`, `skills/mf-ship/scripts/conduct.py`, `scripts/corpus.py`,
`skills/mf-converge/scripts/plan_check.py`, `skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md`, `docs/decisions.md`,
`tests/test_brief_check.py`, `tests/test_conduct.py` and `tests/test_skills.py`. Adds `skills/mf-cut-change/scripts/facts.py`,
`cut_pre.py` and `cut_check.py`, and `tests/test_facts.py`, `tests/test_cut_pre.py` and `tests/test_cut_check.py`. No dependency;
the gate recipe is unchanged.

## Not in this change

- The converge conductor as a script: *converge script*.
- Tool evidence before the checkers, ast-grep, wider ruff: *evidence step*.
- Checking the models file's hash after the cut passes: when the switches move out of worker-writable reach. A plant in a
  later stage stays the accepted class of `THREAT_MODEL.md`, with card `0105·S2`.
- A corpus case for the new readers of `.minions/cuts/` and `models.toml`: they read names and bytes, no run data format.
- Rewriting a brief already written in the old citation form: its next `mf-plan from=` does.
- The efficiency ledger's hypothesis H14, kept outside the repository by the person.
