# Ship fixes 3 — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — A planned decision id renumbered
- [ ] 2 — An insert-only delta kept
- [ ] 3 — Git's own error

## 1 — A planned decision id renumbered

- [ ] 1.1 Add `TITLED`, `PLANNED` and `_planned` to `skills/mf-integrate/scripts/integrate.py`, and read the plan's planned ids
  in `decisions`, per [D1](design.md#d1).
  Verify: `grep -n '^def _planned' skills/mf-integrate/scripts/integrate.py` prints a line.
- [ ] 1.2 Run `changelog` on an unmerged `CHANGELOG.md` and `decisions` on every merge in `replay`, its line naming the paths
  per [D3](design.md#d3).
  Verify: `grep -L 'if path in _unmerged(scratch)' skills/mf-integrate/scripts/integrate.py` prints `skills/mf-integrate/scripts/integrate.py`.
- [ ] 1.3 Copy `TITLED`, `PLANNED` and `_planned` into `skills/mf-converge/scripts/gate_check.py`, and read them in
  `renumbered`, per [D2](design.md#d2).
  Verify: `grep -n '^def _planned' skills/mf-converge/scripts/gate_check.py` prints a line.
- [ ] 1.4 Add `test_decisions_renumbers_a_planned_id_the_default_branch_took` to `tests/test_integrate.py`, as the design's
  `## Tests` names it.
  Verify: `uv run pytest -q tests/test_integrate.py -k planned_id_the_default_branch_took` reports `1 passed`.
- [ ] 1.5 Run `settle` on every merge `merge_in` opens in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3); add
  `test_a_merge_in_renumbers_a_planned_decision` and edit `test_a_crashed_integrate_script_halts_and_a_rerun_merges`'s `crash.py`
  in `tests/test_conduct.py`, as `## Tests` says.
  Verify: `uv run pytest -q tests/test_conduct.py -k "merge_in_renumbers_a_planned_decision or crashed_integrate_script_halts"` reports `2 passed`.
- [ ] 1.6 Amend D45 in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -n "the plan's planned ones too" docs/decisions.md` prints a line.
- [ ] 1.7 Extend the `decisions` row of `skills/mf-integrate/SKILL.md` Step 3.2, per [D7](design.md#d7).
  Verify: `grep -n "above the base's highest" skills/mf-integrate/SKILL.md` prints a line.

## 2 — An insert-only delta kept

- [ ] 2.1 Add `_inserts_only` to `skills/mf-integrate/scripts/integrate.py` and read it in `delta`, per [D4](design.md#d4);
  add `test_delta_keeps_a_delta_that_only_inserts` to `tests/test_integrate.py`, as `## Tests` names it.
  Verify: `uv run pytest -q tests/test_integrate.py -k delta_keeps_a_delta_that_only_inserts` reports `1 passed`.
- [ ] 2.2 Extend the `delta` row of `skills/mf-integrate/SKILL.md` Step 3.2, per [D7](design.md#d7).
  Verify: `grep -n 'only inserts into the default branch' skills/mf-integrate/SKILL.md` prints a line.

## 3 — Git's own error

- [ ] 3.1 Run git through `_run` in `primary_of` in `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6); add
  `test_a_git_failure_names_its_line_and_uv` to `tests/test_conduct.py`, as `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k git_failure_names_its_line_and_uv` reports `1 passed`.
- [ ] 3.2 Name git's failure in `_record` in `skills/mf-cut-change/scripts/awake.py`, per [D6](design.md#d6); extend
  `test_stop_kills_only_a_recorded_caffeinate` in `tests/test_awake.py`, as `## Tests` says.
  Verify: `grep -n 'git rev-parse failed' skills/mf-cut-change/scripts/awake.py` prints a line.
- [ ] 3.3 Name git's failure in `_tree` in `skills/mf-integrate/scripts/integrate.py`, per [D6](design.md#d6); add
  `test_a_git_failure_names_its_line` to `tests/test_integrate.py`, as `## Tests` names it.
  Verify: `uv run pytest -q tests/test_integrate.py -k git_failure_names_its_line` reports `1 passed`.
