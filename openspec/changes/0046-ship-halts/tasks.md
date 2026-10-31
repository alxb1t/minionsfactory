# Ship halts — tasks

Build the settled [design](design.md), one phase at a time. The skill, decision and principle text is the design's,
word for word.

## Progress

- [ ] 1 — Per-version halts
- [ ] 2 — The catch-up's count

## 1 — Per-version halts

- [ ] 1.1 In `skills/mf-ship/scripts/conduct.py`, add `Run.stopped` and open `advance`'s loop on it, per
  [D1](design.md#d1); add `Run.deliver`, and call it from `ship` in place of stage B's loop, per [D2](design.md#d2).
  Verify: `grep -c 'while not self.stopped(version.change):' skills/mf-ship/scripts/conduct.py` prints `1`.
- [ ] 1.2 In `skills/mf-ship/scripts/conduct.py`, log a halt inside `Run.halt`, drop `ship`'s end-of-run loop over the
  halts, and add `Run.closing` with its closing event, per [D3](design.md#d3).
  Verify: `grep -c 'for who, reason in self.halts' skills/mf-ship/scripts/conduct.py` prints `0`.
- [ ] 1.3 In `skills/mf-ship/scripts/conduct.py`, make `report` print every `halt` line and the `held behind` field, per
  [D4](design.md#d4).
  Verify: `grep -c 'held behind' skills/mf-ship/scripts/conduct.py` prints `1`.
- [ ] 1.4 In `tests/test_conduct.py`, add the `liar-<name>` mode to `_fake`, and add
  `test_a_later_version_halts_and_the_earlier_ships` and `test_an_earlier_version_halts_and_the_later_is_held`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "later_version_halts or later_is_held"` reports `2 passed`.
- [ ] 1.5 In `tests/test_conduct.py`, edit `test_run_halts_on_a_human_phase`, `test_run_halts_on_a_timeout`,
  `test_run_halts_when_a_worker_claims_what_disk_does_not_show`,
  `test_log_verify_finds_an_unpaired_spawn_and_an_open_end` and
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, and merge `test_a_rerun_resumes_from_disk` away, per
  [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py` reports `11 passed`.
- [ ] 1.6 Edit `skills/mf-ship/SKILL.md`'s diagram and Step 4, per [D6](design.md#d6).
  Verify: `grep -c 'a halt stops only its version' skills/mf-ship/SKILL.md` prints `1`.

## 2 — The catch-up's count

- [ ] 2.1 Edit `skills/mf-converge/SKILL.md`'s `## Catch-up round` diagram, its items 2 and 4, and Step 7, per
  [D5](design.md#d5).
  Verify: `grep -c 'the selection merges only' skills/mf-converge/SKILL.md` prints `1`.
- [ ] 2.2 Amend D47 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -c 'the first failed check halts the run' docs/decisions.md` prints `0`.
- [ ] 2.3 Add the **A merge** bullet to `docs/principles.md`'s *Every edit opens a round*, per [D6](design.md#d6).
  Verify: `grep -c 'a catch-up over merges only counts its own rounds' docs/principles.md` prints `1`.
