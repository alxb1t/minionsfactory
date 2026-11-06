# Minions layout — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The helper, and findings in the change's folder
- [x] 2 — Worker logs in the change's folder
- [x] 3 — The rest of the change's files
- [x] 4 — The move, the halt on an old layout, both layouts read
- [ ] 5 — The record

## 1 — The helper, and findings in the change's folder

- [x] 1.1 Add `_change_dir` to `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`,
  `skills/mf-converge/scripts/gate_check.py`, `scripts/metrics/run.py` and `skills/mf-review-metrics/scripts/review_metrics.py`, and
  rename `skills/mf-build/scripts/metrics.py`'s to `_spec_dir`, per [D2](design.md#d2); move the review, security and status-log files
  and the patch to D1's names at every F1–F4 site, mf-converge's, mf-release's and mf-rescue's prose and `references/worker.md`
  included, per [D1](design.md#d1).
  Verify: `grep -n 'def _spec_dir' skills/mf-build/scripts/metrics.py` prints a line, and `uv run pytest -q -m "not slow"` exits 0.

## 2 — Worker logs in the change's folder

- [x] 2.1 Write a change's worker logs to `changes/<id>/logs/`, and read them there in `run.py`, `review_metrics.py` and mf-rescue's
  input, the newest by stamp and `n`, and name both in `skills/mf-review-metrics/SKILL.md`'s description, per [D3](design.md#d3);
  follow the F4 sites.
  Verify: `grep -n '"logs"' skills/mf-ship/scripts/conduct.py` prints a line, and
  `uv run pytest -q tests/test_review_metrics.py tests/test_metric_scripts.py` exits 0.

## 3 — The rest of the change's files

- [x] 3.1 Move the models file, integrate's notes, build's marks, rescue's diagnosis, release's `held` and the gate-check export to
  D1's names at every F1–F4 site, mf-build's, mf-integrate's, mf-cut-change's, mf-ship's, mf-release's (`held`) and mf-rescue's
  (its rescue, `build.halt` and integrate-note lines) prose included, per [D1](design.md#d1).
  Verify: `grep -n 'build.done' skills/mf-build/SKILL.md` prints a line, and
  `uv run pytest -q tests/test_conduct.py tests/test_integrate.py tests/test_gate_check.py` exits 0.

## 4 — The move, the halt on an old layout, both layouts read

- [x] 4.1 Add `Run.migrate_layout`, called in `ship()` beside `migrate_debt`; the old-layout halt in `integrate.py`,
  `gate_check.py`, `run.py`, `conduct.py`'s `grant`, mf-release's preconditions, mf-integrate's Step 2, mf-converge's start (before
  its status log) and mf-build's halt (before `build.halt`); and the `old layout` line in
  `status` and `report`, per [D4](design.md#d4) and [D6](design.md#d6); add the tests the design's `## Tests` names for them.
  Verify: `uv run pytest -q tests/test_conduct.py tests/test_integrate.py tests/test_gate_check.py tests/test_metric_scripts.py -k "old_layout"` exits 0,
  and `grep -n 'def migrate_layout' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 4.2 Read both layouts in `review_metrics.py`, per [D5](design.md#d5); add `test_both_layouts_are_read` to
  `tests/test_review_metrics.py`, and name both folders in `test_overrides_win_over_the_config`'s expected message.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k "both_layouts_are_read or overrides_win_over_the_config"` reports `2 passed`.

## 5 — The record

- [ ] 5.1 Add the decision *One folder per change in `.minions/`* to `docs/decisions.md` and follow the paths at its other sites,
  in `docs/principles.md`, `CONTRIBUTING.md` and its bootstrap template, `AGENTS.md`'s `.minions/` list and `THREAT_MODEL.md`, per
  [D6](design.md#d6).
  Verify: `grep -n 'One folder per change' docs/decisions.md` prints a line, and `grep -n 'changes/<change-id>' AGENTS.md` prints a line.
