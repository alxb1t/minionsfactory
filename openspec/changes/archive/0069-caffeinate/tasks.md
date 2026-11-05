# Caffeinate — tasks

Build the settled [design](design.md), one phase.

## Progress

- [x] 1 — Awake

## 1 — Awake

- [x] 1.1 Add `CAFFEINATE` and `_hold_awake`, called from `ship()`, and its field in the `start` line, in
  `skills/mf-ship/scripts/conduct.py`; add `test_a_run_holds_the_machine_awake` to `tests/test_conduct.py`, per [D1](design.md#d1)
  and [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_conduct.py -k run_holds_the_machine_awake` reports `1 passed`.
- [x] 1.2 Name the lid in `skills/mf-ship/SKILL.md` Step 3, per [D3](design.md#d3).
  Verify: `grep -n 'clamshell' skills/mf-ship/SKILL.md` prints a line.
