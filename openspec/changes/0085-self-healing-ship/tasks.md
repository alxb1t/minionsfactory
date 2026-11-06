# Self-healing ship — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — Rescue at amend needed
- [x] 2 — The switch
- [ ] 3 — The run goes on
- [ ] 4 — The record

## 1 — Rescue at amend needed

- [x] 1.1 Add `_rescue_amends` and `_security_blocks` to `skills/mf-ship/scripts/conduct.py`, take them at both rescue calls in
  `advance`, go on after an entry rescue's amend, and call `hold` only when no amend was taken, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -n 'def _rescue_amends' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Add the `amend-halts` converge mode and the `rescue-prose` rescue mode to `tests/fake_worker.py`, and
  `test_a_rescue_amends_at_amend_needed` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue_amends_at_amend_needed` reports `1 passed`.
- [x] 1.3 Add the `amend needed` row and the security line to `skills/mf-rescue/SKILL.md`'s kind table, per [D1](design.md#d1).
  Verify: `grep -n 'cards name, in' skills/mf-rescue/SKILL.md` prints a line.

## 2 — The switch

- [x] 2.1 Add `_decides`, `Run.decides`, the prompt's `{decide}`, `_amend`'s `decided`, the `decided` event, `Run.decided` and
  ` · decided <ids>` on the closing and `done` lines, in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3), [D4](design.md#d4)
  and [D7](design.md#d7); give `test_a_rescue_outside_the_plan_halts`' expected tuples their `False`.
  Verify: `grep -n 'def _decides' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.2 Add the `rescue-decides` rescue mode to `tests/fake_worker.py`, and `test_a_rescue_decides_under_the_switch` to
  `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue_decides_under_the_switch` reports `1 passed`.
- [x] 2.3 Add `rescues-decided` to `scripts/metrics/run.py` and `metrics/catalogue.toml`, and extend
  `test_run_metrics_read_the_run_logs` in `tests/test_metric_scripts.py`, per [D4](design.md#d4).
  Verify: `grep -n 'id = "rescues-decided"' metrics/catalogue.toml` prints a line.
- [x] 2.4 Add `decide=recommended` to `skills/mf-rescue/SKILL.md`'s *Parameter* section, the trailer to Step 3a's commit, and
  the switch's exception to each confining line [D3](design.md#d3) names.
  Verify: `grep -n 'Decided-by: rescue' skills/mf-rescue/SKILL.md` prints a line.

## 3 — The run goes on

- [ ] 3.1 Let `hold` return whether the version goes on, with the amends-only answer, in `skills/mf-ship/scripts/conduct.py`, per
  [D5](design.md#d5); add the `rescue-person-amends` mode and `test_an_amend_during_a_rescue_goes_on`, as `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k amend_during_a_rescue_goes_on` reports `1 passed`.
- [ ] 3.2 Add `Run.recheck`, `Run.seen_halts` written by `Run.halt`, and the one-window wait in `join`, to
  `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6); reorder the acts of the rejoin tests `## Tests` names.
  Verify: `grep -n 'def recheck' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 3.3 Add `_needs` and the ` · needs` part to `closing`, per [D7](design.md#d7); give each closing-line assertion in
  `tests/test_conduct.py` it turns red its part, and add `test_a_halt_answered_on_disk_comes_back`, as `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k halt_answered_on_disk_comes_back` reports `1 passed`.

## 4 — The record

- [ ] 4.1 Add D59 and amend D47 and D53 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -n '^### D59 · A run heals its own halts' docs/decisions.md` prints a line.
- [ ] 4.2 Add the amends exception and the switch's line to `THREAT_MODEL.md`, per [D8](design.md#d8).
  Verify: `grep -n 'Decided-by:' THREAT_MODEL.md` prints a line.
- [ ] 4.3 Edit the `rejoin`, `run · live`, diagnosed and frozen rows and the closing sentence of `skills/mf-ship/SKILL.md`, per
  [D8](design.md#d8).
  Verify: `grep -n 'needs <id> <action>' skills/mf-ship/SKILL.md` prints a line.
