# Plan queues — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — The brief check
- [ ] 2 — The plan's close

## 1 — The brief check

- [ ] 1.1 Add `skills/mf-plan/scripts/brief_check.py`, per [D1](design.md#d1).
  Verify: `uv run --script skills/mf-plan/scripts/brief_check.py openspec/changes/0083-plan-queues/no-brief.md` prints `brief: cannot check — openspec/changes/0083-plan-queues/no-brief.md: No such file or directory`.
- [ ] 1.2 Add `tests/test_brief_check.py` with `test_a_hard_brief_is_ready_for_the_cut`, `test_a_brief_out_of_shape_halts`
  and `test_what_cannot_be_checked_exits_2`, per [the design's Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_brief_check.py` reports `3 passed`.

## 2 — The plan's close

- [ ] 2.1 Add the `then` row to the *Parameters* table, the `## For the cut` item form to *The brief*, and the hard close
  to Step 6, with [D4](design.md#d4)'s Step 2 exception, of `skills/mf-plan/SKILL.md`, per [D2](design.md#d2) and
  [D3](design.md#d3).
  Verify: `grep -n 'confirm, and queue it?' skills/mf-plan/SKILL.md` prints a line.
- [ ] 2.2 Edit the role line, the diagram and *Never* of `skills/mf-plan/SKILL.md`, per [D4](design.md#d4).
  Verify: `grep -n 'on yes: conduct.py cut' skills/mf-plan/SKILL.md` prints a line.
- [ ] 2.3 Append `("mf-plan", "scripts/brief_check.py")` and `("mf-plan", "../mf-ship/scripts/conduct.py")` to
  `_METRICS_SCRIPTS`, and their `not named` lines to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script`, in `tests/test_skills.py`, per [D4](design.md#d4).
  Verify: `grep -n 'skills/mf-plan/SKILL.md: scripts/brief_check.py: not named' tests/test_skills.py` prints a line, and
  `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.
- [ ] 2.4 Add **D59 · A hard plan closes on a checked brief, and queues its cut on the person's yes** to *Planning* in
  `docs/decisions.md`, its id to the diagram's Planning list, and the D5 clause, per [D4](design.md#d4).
  Verify: `grep -n "### D59 · A hard plan closes on a checked brief" docs/decisions.md` prints a line.
