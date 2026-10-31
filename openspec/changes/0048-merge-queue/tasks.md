# Merge queue — tasks

Build the settled [design](design.md), one phase at a time. The skill and decision text is the design's, word for word.

## Progress

- [ ] 1 — The cut and I17
- [ ] 2 — The merge side
- [ ] 3 — The conductor
- [ ] 4 — The record

## 1 — The cut and I17

- [ ] 1.1 Edit `skills/mf-cut-change/SKILL.md`: the `after` parameter, per [D2](design.md#d2); `I10` and `I17`, per
  [D6](design.md#d6); Steps 1, 6 and 11, per [D7](design.md#d7).
  Verify: `grep -c 'Next: /mf-ship, in the primary.' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.2 Edit `skills/mf-build/SKILL.md`: `I10`, `I17` and Step 1, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_skills.py -k same_contract_ids` reports `1 passed`, and
  `grep -c 'I17' skills/mf-build/SKILL.md` prints `2`.

## 2 — The merge side

- [ ] 2.1 In `skills/mf-integrate/scripts/integrate.py`, add `_after` and `_shipped`, per [D2](design.md#d2), and give
  `next` its optional `change`, per [D5](design.md#d5).
  Verify: `grep -c 'def _shipped' skills/mf-integrate/scripts/integrate.py` prints `1`.
- [ ] 2.2 In `tests/test_integrate.py`, rewrite `test_next_picks_the_lowest_open_id_and_halts_on_an_unready_one` as
  `test_next_picks_the_named_or_the_lowest_ready_id`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_integrate.py -k named_or_the_lowest_ready` reports `1 passed`.
- [ ] 2.3 Edit `skills/mf-integrate/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -c 'Never skip ahead' skills/mf-integrate/SKILL.md` prints `0`.
- [ ] 2.4 Replace precondition 10 in `skills/mf-release/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -c 'Earlier cuts have shipped' skills/mf-release/SKILL.md` prints `0`.

## 3 — The conductor

- [ ] 3.1 In `skills/mf-ship/scripts/conduct.py`, replace `deliver` with `Run.take` and `Run.ready`, and start a thread for
  every version, per [D1](design.md#d1), [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c 'def deliver' skills/mf-ship/scripts/conduct.py` prints `0`.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py`, add `waiting` and `blocked` to `stage_of`, `EVENTS`, `closing` and `report`,
  and drop `held`, per [D4](design.md#d4).
  Verify: `grep -c 'held behind' skills/mf-ship/scripts/conduct.py` prints `0`.
- [ ] 3.3 In `tests/test_conduct.py`, edit `_version`, `_primary` and `_fake`, and rewrite
  `test_run_ships_two_versions_in_cut_order` and `test_an_earlier_version_halts_and_the_later_is_held`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "past_a_slow_one or past_a_halted_one"` reports `2 passed`.
- [ ] 3.4 In `tests/test_conduct.py`, add `test_after_waits_for_its_dependency` and
  `test_a_halted_dependency_blocks_a_chain`, and edit `test_a_later_version_halts_and_the_earlier_ships`,
  `test_run_halts_on_a_human_phase`, `test_run_halts_on_a_timeout` and
  `test_run_halts_when_a_worker_claims_what_disk_does_not_show`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py` reports `13 passed`.
- [ ] 3.5 Edit `skills/mf-ship/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -c 'cut order' skills/mf-ship/SKILL.md` prints `0`.

## 4 — The record

- [ ] 4.1 Edit `skills/mf-plan/SKILL.md`'s *parallel with* row, per [D7](design.md#d7).
  Verify: `grep -c 'proposed in an order' skills/mf-plan/SKILL.md` prints `0`.
- [ ] 4.2 Amend D20, D44, D45 and D47 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -c 'cut order' docs/decisions.md` prints `1`.
