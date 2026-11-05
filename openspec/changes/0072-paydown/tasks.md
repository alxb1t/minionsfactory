# Paydown — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — The probe's .arch
- [ ] 2 — remove_tree refuses first
- [ ] 3 — The record

## 1 — The probe's .arch

- [ ] 1.1 Read `.arch` first and safely in `check_probe`, in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1); extend
  `test_a_probe_halts_on_a_write_out` in `tests/test_conduct.py` with direct `check_probe` calls on a scratch folder: a `.gated`
  beside a mismatched `.arch`, and a `.arch` link.
  Verify: `uv run pytest -q tests/test_conduct.py -k probe_halts_on_a_write_out` reports `1 passed`, and
  `grep -n 'an unreadable .arch' skills/mf-ship/scripts/conduct.py` prints a line.

## 2 — remove_tree refuses first

- [ ] 2.1 Add the config refusal and the link check to `Run.remove_tree`, in `skills/mf-ship/scripts/conduct.py`, per
  [D2](design.md#d2); extend `test_a_ready_version_ships_past_a_slow_one` with a link at the cut's path, a refused config, and a tree
  git refuses to remove.
  Verify: `uv run pytest -q tests/test_conduct.py -k ready_version_ships_past_a_slow_one` reports `1 passed`, and
  `grep -n "a link at the cut's path" skills/mf-ship/scripts/conduct.py` prints a line.

## 3 — The record

- [ ] 3.1 Reword `docs/principles.md`'s `CI none` line and `THREAT_MODEL.md`'s pin gap line, per [D4](design.md#d4).
  Verify: `grep -n "a run's end that moves to that tag" THREAT_MODEL.md` prints a line, and
  `grep -n 'CI not read under mf-ship' docs/principles.md` prints a line.
- [ ] 3.2 Reword `skills/mf-integrate/SKILL.md`'s Step 3 item 3, its note-halt line and its close-out, and `next_version`'s
  docstring in `skills/mf-integrate/scripts/integrate.py`, per [D5](design.md#d5).
  Verify: `grep -n "is none of item 4's cases" skills/mf-integrate/SKILL.md` prints a line.
