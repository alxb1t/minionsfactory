# Cut awake — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The hold
- [x] 2 — The cut holds it

## 1 — The hold

- [x] 1.1 Add `skills/mf-cut-change/scripts/awake.py` with `start` and `stop`, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `uv run --script skills/mf-cut-change/scripts/awake.py stop 0000-none` prints `awake: none held`.
- [x] 1.2 Add `tests/test_awake.py` with `test_a_cut_holds_the_machine_awake_by_change_id`,
  `test_no_hold_starts_without_caffeinate_or_a_host` and `test_stop_kills_only_a_recorded_caffeinate`, per
  [the design's Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_awake.py` reports `3 passed`.

## 2 — The cut holds it

- [x] 2.1 Start the hold at the head of Step 1, stop it at every halt and at Step 11, and name the lid, in
  `skills/mf-cut-change/SKILL.md`, per [D3](design.md#d3).
  Verify: `grep -n 'scripts/awake.py stop <change-id>' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 2.2 Append `("mf-cut-change", "scripts/awake.py")` to `_METRICS_SCRIPTS`, after its `verify_check.py` entry, and its
  `not named` line to each expected list of `test_the_metrics_script_scan_reports_a_missing_script`, in `tests/test_skills.py`,
  per [D4](design.md#d4).
  Verify: `grep -n 'scripts/awake.py: not named' tests/test_skills.py` prints a line, and
  `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.
- [x] 2.3 Name `awake/` among D57's generic folders in `docs/decisions.md`, per [D4](design.md#d4).
  Verify: `grep -n 'awake/' docs/decisions.md` prints a line.
