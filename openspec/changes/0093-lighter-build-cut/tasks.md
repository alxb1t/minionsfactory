# Lighter build and cut — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its text.

## Progress

- [ ] 1 — The review and the moderate build
- [ ] 2 — The record

## 1 — The review and the moderate build

- [ ] 1.1 Add `_section_rows`, `_cut_review_problems` and their constants and tests to `tests/test_skills.py`, after the plan
  station's block, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_skills.py -k plan_review_scan` reports `1 passed`.
- [ ] 1.2 Add the review table and its paragraph to Step 8.5, and edit the doubts table's first and second rows, in
  `skills/mf-cut-change/SKILL.md`, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -n 'never a message to the first' skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 1.3 Edit the moderate row of *Suggesting models* and add its sentence in `skills/mf-cut-change/SKILL.md`, per
  [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_skills.py -k plan_review` reports `2 passed`.
- [ ] 1.4 Edit *The brief*'s closing paragraph in `skills/mf-plan/SKILL.md`, per [D4](design.md#d4).
  Verify: `grep -n 'Sonnet 5.5 · high for a build' skills/mf-plan/SKILL.md` prints a line.

## 2 — The record

- [ ] 2.1 Add D65 as the last decision of *Planning* in `docs/decisions.md`, as [D6](design.md#d6) quotes it.
  Verify: `grep -n '^### D65 · A lighter plan review and build$' docs/decisions.md` prints a line.
- [ ] 2.2 Add `D65` as the last id of the map's Planning list in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'D59, .*D65' docs/decisions.md` prints a line.
- [ ] 2.3 Edit D7's bold text in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'a second review only after a fix' docs/decisions.md` prints a line.
- [ ] 2.4 Edit D40's bold text in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'never a message to the reviewer before it' docs/decisions.md` prints a line.
- [ ] 2.5 Add the *Names one model* bullet to D41 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'Names one model:' docs/decisions.md` prints a line.
- [ ] 2.6 Add the **Accepts** bullet to D42 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'the plan-review scan of' docs/decisions.md` prints a line.
