# Cap policy — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The automatic grant
- [x] 2 — The re-plan
- [ ] 3 — The record

## 1 — The automatic grant

- [x] 1.1 Add `_open_blockers`, `_auto_grants`, `self.capped`, `self.grants_auto`, `_would_grant` and `Run.auto_grant`, called where
  [D2](design.md#d2) names, in `skills/mf-ship/scripts/conduct.py`; add the `_cards` helper and the `cap-small` mode to
  `tests/fake_worker.py`, and `test_a_small_cap_is_granted_automatically` to `tests/test_conduct.py`, per [D1](design.md#d1),
  [D2](design.md#d2) and [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k small_cap_is_granted_automatically` reports `1 passed`.

## 2 — The re-plan

- [x] 2.1 Halt a cap the rule refuses as `re-plan`; add the `cap-design` and `cap-again` modes and
  `test_a_design_change_cap_halts_as_replan`, `test_an_auto_granted_round_that_blocks_halts_as_replan` and
  `test_auto_grant_false_grants_none`; add a person's grant on a re-plan halt to `test_a_grant_buys_one_round`, per [D3](design.md#d3)
  and [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "replan or auto_grant_false or grant_buys_one_round"` reports `4 passed`.
- [x] 2.2 Name `/mf-plan … from=` in `skills/mf-rescue/SKILL.md`'s cap diagnosis, per [D3](design.md#d3).
  Verify: `grep -n 're-plan' skills/mf-rescue/SKILL.md` prints a line.

## 3 — The record

- [ ] 3.1 Amend D47 and add D54 in `docs/decisions.md`; add the `re-plan` row to `skills/mf-ship/SKILL.md`'s halt table, per
  [D5](design.md#d5).
  Verify: `grep -n 'D54' docs/decisions.md` prints a line, and `grep -n 're-plan' skills/mf-ship/SKILL.md` prints a line.
