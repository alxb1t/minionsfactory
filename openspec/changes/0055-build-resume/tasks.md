# Build resume — tasks

Build the settled [design](design.md), one phase at a time. The skill text is the design's, word for word.

## Progress

- [ ] 1 — The marker
- [ ] 2 — The stage
- [ ] 3 — The record

## 1 — The marker

- [ ] 1.1 Write `.minions/build/<change-id>.done` after Step 3.5, and change and add the start table's rows, in
  `skills/mf-build/SKILL.md`, per [D1](design.md#d1) and [D3](design.md#d3).
  Verify: `grep -c 'build/<change-id>.done' skills/mf-build/SKILL.md` prints a number above `1`.

## 2 — The stage

- [ ] 2.1 Add `_closed` and its check to `stage_of` in `skills/mf-ship/scripts/conduct.py`, the marker and mode
  `dies-simplify` to `tests/fake_worker.py`, and a `.done` to the `tests/test_conduct.py` helpers that tick phases by hand,
  per [D2](design.md#d2) and [D4](design.md#d4).
  Verify: `grep -c 'def _closed' skills/mf-ship/scripts/conduct.py` prints `1`, and `grep -c 'dies-simplify' tests/fake_worker.py`
  prints a number above `0`.
- [ ] 2.2 Add `test_a_build_dead_in_simplify_resumes_at_it`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k dead_in_simplify` reports `1 passed`.

## 3 — The record

- [ ] 3.1 Add D4's line to `skills/mf-ship/SKILL.md` Step 4.
  Verify: `grep -c 'resumes at simplify' skills/mf-ship/SKILL.md` prints `1`.
