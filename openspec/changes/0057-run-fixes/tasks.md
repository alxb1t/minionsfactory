# Run fixes — tasks

Build the settled [design](design.md), one phase at a time. The skill text is the design's, word for word.

## Progress

- [x] 1 — The probe
- [ ] 2 — The base
- [ ] 3 — The release
- [ ] 4 — The record

## 1 — The probe

- [x] 1.1 Add `_native` and the architecture line to `probe_gate`, and its reading to `check_probe`, in
  `skills/mf-ship/scripts/conduct.py`; the mode to `tests/fake_worker.py`; and its step to `test_a_probe_halts_on_a_write_out`,
  per [D1](design.md#d1).
  Verify: `grep -c 'def _native' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k probe_halts_on_a_write_out` reports `1 passed`.

## 2 — The base

- [ ] 2.1 Merge `main` into a cut-only version, and halt a started one behind a gate change, in `Run.take`; add their steps to
  `test_after_waits_for_its_dependency`, per [D2](design.md#d2).
  Verify: `grep -c 'since .*base: git -C' skills/mf-ship/scripts/conduct.py` prints a number above `0`, and
  `uv run pytest -q tests/test_conduct.py -k after_waits_for_its_dependency` reports `1 passed`.

## 3 — The release

- [ ] 3.1 Remove a released worktree in `Run.advance`, with `kept` in `EVENTS`, and add its steps to
  `test_a_ready_version_ships_past_a_slow_one`, per [D3](design.md#d3).
  Verify: `grep -c '"kept"' skills/mf-ship/scripts/conduct.py` prints a number above `0`, and
  `uv run pytest -q tests/test_conduct.py -k ready_version_ships_past` reports `1 passed`.

## 4 — The record

- [ ] 4.1 Edit `skills/mf-release/SKILL.md` Steps 4.1, 5.6 and 6, and `skills/mf-ship/SKILL.md` Step 4, per [D3](design.md#d3)
  and [D4](design.md#d4).
  Verify: `grep -c 'CI not read under mf-ship' skills/mf-release/SKILL.md` prints `1`, and
  `grep -c 'conduct.py. removes it' skills/mf-release/SKILL.md` prints a number above `0`.
