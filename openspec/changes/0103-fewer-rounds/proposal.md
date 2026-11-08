---
bump: minor
after: [0102-build-per-phase]
debt: [0091·R4, 0091·S4, 0091·S5]
---

# Fewer rounds

Cut converge's extra rounds at their causes. Round 1's fix takes the pickup. A fixer records how the code now implements a
decision without an amend. A deterministic plan check and a corpus of the repo's own run data catch blockers before a reviewer
does. The Markdown readers read as CommonMark does.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Across 0080–0100, most rounds past the first were a pickup alone, an amend round over plan prose a fix left stale, or a
blocker a deterministic check could have found ([evidence](design.md#evidence)). Each such round spends a fresh checker; each
amend round spends a rescue and a round more.

## What Changes

- **The round-1 pickup** — when round 1 leaves a blocker, its fix pass also takes the cards Step 8 would pick, and round 2
  verifies them all; Step 8 then runs no pickup. A pickup whose fixer commits nothing gets no pickup check.
- **A mechanism repeat** — a finding whose mechanism a debt card holds, in another form, names `repeat of <card>` too,
  graded as it stands.
- **The fix note** — the converge fixer may append `Fix note (YYYY-MM-DD, <card id>): <one line>` as the last line of a
  `### D<n>` entry; `conduct.py`'s decision reading counts appended notes as no decision change, and converge's close-out
  names each note for the person.
- **`plan_check.py`** — a new converge script: it re-runs each ticked `Verify:`, checks the boxes, finds the diff's removed
  identifiers still named in the change directory or `openspec/specs/`, and finds the base's tests gone at the head. The build's
  close runs it before `build.done`; the converge fixer runs it after each fix, and Step 7 runs it again, halting
  `amend needed` on a line only the plan can clear, which `mf-rescue` amends.
- **`make corpus`** — runs this repo's readers of run data over the run directory and the operator's Codex sessions, out of
  `make gate`; the cut marks a sub-task that adds or alters such a reader `**CORPUS**`, the build runs `make corpus` after it,
  and the plan check finds its case.
- **CommonMark readers** — `brief_check.py` and the cut station's `## Dependencies` check parse with `markdown-it-py`; a
  deterministic fuzz corpus compares their reading with the rendered page; the cut station reads the branch as
  `refs/heads/<id>`. This closes `0091·R4`, `0091·S4` and `0091·S5`.
- **The plan review's model** — `mf-cut-change` runs its plan reviews on Opus 5.5 · high by name; `mf-plan`'s default cut
  model becomes Sonnet 5.5 · high.
- **The record** — a new decision; D2, D53, D65 and D71 edited; `CODING_STANDARDS.md`, `AGENTS.md` and the threat model.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A plan check holds the plan to the built tree* — ADDED: `plan_check.py`, its checks, and where it runs.
  - *A reader of run data has a corpus case* — ADDED: `make corpus`, the cut's `**CORPUS**` mark, the plan check's corpus
    rule.
  - *Converge keeps deferred work in one repository debt file* — MODIFIED: the round-1 pickup; no pickup check over a fix
    that committed nothing.
  - *A repeated finding escalates* — MODIFIED: a mechanism repeat names `repeat of <id>`, with no grade-up.
  - *The converge fixer leaves the plan to the person* — MODIFIED: the fix note; the fixer and Step 7 run the plan check.
  - *A rescue decides by the version's switch* — MODIFIED: appended fix notes are no decision change.
  - *A run cuts each queued brief in a station of its own* — MODIFIED: `## Dependencies` read as CommonMark and GFM render it,
    at `refs/heads/<id>`.
  - *A hard brief is checked before it is queued* — MODIFIED: sections and headings read as CommonMark does; a lone carriage
    return halts.
  - *A fresh worker reviews the plan before the cut commits* — MODIFIED: the reviewer runs on Opus 5.5 · high.

## Impact

Changes `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-plan/scripts/brief_check.py`, `skills/mf-build/SKILL.md`, `skills/mf-rescue/SKILL.md`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `CODING_STANDARDS.md`,
`AGENTS.md`, `docs/decisions.md`, `THREAT_MODEL.md`, `tests/test_conduct.py` and `tests/test_brief_check.py`. Adds
`skills/mf-converge/scripts/plan_check.py`, `scripts/corpus.py`, `scripts/corpus.toml`, `tests/test_plan_check.py`,
`tests/test_corpus.py` and `tests/test_markdown_corpus.py`.

Dependencies: `markdown-it-py >=3,<4`, approved in the brief: in the PEP 723 headers of `brief_check.py` and `conduct.py`, and
in the dev group, so the suite imports it. The gate recipe stays unchanged; the `Makefile` gains a `corpus` target.

## Not in this change

- A scenario-test check, and coverage of removed tests beyond the plan check's base-test rule.
- Changing the fixer's bound on `design.md` beyond the fix note.
- `make corpus` in `make gate` or CI.
- A lockfile for a script's PEP 723 header: when a resolved release of `markdown-it-py` breaks a reader.
