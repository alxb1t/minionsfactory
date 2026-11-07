# Lighter converge — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `0092-amend-round` merges in
before this build: find each section by its heading, never by a line number.

## Progress

- [x] 1 — Worker models
- [x] 2 — The bundle
- [ ] 3 — Security by recomputation
- [ ] 4 — The record

## 1 — Worker models

- [x] 1.1 Add `test_a_worker_clause_names_its_model_and_effort` to `tests/test_conduct.py` and extend the tests the design's
  `## Tests` names in it, then `WORKERS`, `TOKEN`, `_table`, `_models`, `_worker_clause`, `PROMPTS` and `Run.advance` in
  `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k "worker_clause or station_runs_on_its_executor or plan_is_read_once or carries_the_allowlist"` reports `4 passed`.
- [x] 1.2 Add the **Worker models** paragraph to *The workers* in `skills/mf-converge/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -n 'Worker models' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.3 Rewrite the `verdicts` row of *The status log*'s event table in `skills/mf-converge/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -n 'worker was given' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.4 Rewrite Step 6's dispatch line in `skills/mf-converge/SKILL.md` for the fixer's model, per [D3](design.md#d3), "sent is
  blocking" on one line.
  Verify: `grep -n 'sent is blocking' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.5 Edit *Suggesting models* in `skills/mf-cut-change/SKILL.md` — the Converge bullet, the worker-table sentence and the TOML
  template — per [D4](design.md#d4).
  Verify: `grep -c '^\[converge\.' skills/mf-cut-change/SKILL.md` prints `3`.

## 2 — The bundle

- [x] 2.1 Add `skills/mf-converge/scripts/bundle.py`, per [D5](design.md#d5), and `tests/test_bundle.py`, as the design's
  `## Tests` names its tests.
  Verify: `uv run pytest -q tests/test_bundle.py` reports `2 passed`.
- [x] 2.2 Add `bundle.py` to `_METRICS_SCRIPTS` and its `not named` line to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`, per [D5](design.md#d5).
  Verify: `grep -n '"scripts/bundle.py"' tests/test_skills.py` prints a line.
- [x] 2.3 Add **Write the bundle** to Step 2, and the bundle's rewrite to Step 6's re-freeze, in `skills/mf-converge/SKILL.md`,
  per [D6](design.md#d6).
  Verify: `grep -n 'scripts/bundle.py' skills/mf-converge/SKILL.md` prints a line.
- [x] 2.4 Rewrite Step 3's context bullet and add the bundle bullet in `skills/mf-converge/SKILL.md`, per [D6](design.md#d6),
  "index of all" on one line.
  Verify: `grep -n 'index of all' skills/mf-converge/SKILL.md` prints a line.
- [x] 2.5 Rewrite the packet, **Spec** and **Architecture** of `skills/mf-converge/references/generic-review.md`, per
  [D6](design.md#d6).
  Verify: `grep -n 'bundle' skills/mf-converge/references/generic-review.md` prints a line.
- [x] 2.6 Add the worker line to `AGENTS.md`, per [D7](design.md#d7).
  Verify: `grep -n 'bundle.md' AGENTS.md` prints a line.
- [x] 2.7 Rewrite D48's and D49's bold text in `docs/decisions.md`, per [D7](design.md#d7), "its bundle" and "in a bundle" each
  on one line.
  Verify: `grep -c -e 'its bundle' -e 'in a bundle' docs/decisions.md` prints `2`.

## 3 — Security by recomputation

- [ ] 3.1 Add `skills/mf-converge/scripts/surfaces.py`, per [D8](design.md#d8), and `tests/test_surfaces.py`, as the design's
  `## Tests` names its tests.
  Verify: `uv run pytest -q tests/test_surfaces.py` reports `2 passed`.
- [ ] 3.2 Add `surfaces.py` to `_METRICS_SCRIPTS` and its `not named` line to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`, per [D8](design.md#d8).
  Verify: `grep -n '"scripts/surfaces.py"' tests/test_skills.py` prints a line.
- [ ] 3.3 Add the surfaces run and the security head by rule to Step 7 of `skills/mf-converge/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n 'scripts/surfaces.py' skills/mf-converge/SKILL.md` prints a line.
- [ ] 3.4 Edit the status log's `by rule` row, the resume table's `by rule` row and *Never*'s findings-file line in
  `skills/mf-converge/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n 'review dispatch' skills/mf-converge/SKILL.md` prints a line.
- [ ] 3.5 Add `## Surfaces` and the *Out of scope* sentence to `THREAT_MODEL.md`, per [D8](design.md#d8).
  Verify: `grep -n '^## Surfaces' THREAT_MODEL.md` prints a line.
- [ ] 3.6 Add `## Surfaces` to `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`, per [D8](design.md#d8).
  Verify: `grep -n '^## Surfaces' skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl` prints a line.
- [ ] 3.7 Add the `fix-surfaces` mode to `tests/fake_worker.py` and `test_a_fix_reaching_no_surface_takes_security_by_rule` to
  `tests/test_conduct.py`, as the design's `## Tests` says.
  Verify: `uv run pytest -q tests/test_conduct.py -k fix_reaching_no_surface` reports `1 passed`.
- [ ] 3.8 Add the recomputed security head and its test to *Nothing reads as clean by being absent* in `docs/principles.md`, per
  [D8](design.md#d8).
  Verify: `grep -n 'test_a_fix_that_reaches_no_surface_is_by_rule' docs/principles.md` prints a line.

## 4 — The record

- [ ] 4.1 Add D64 after D40 in `docs/decisions.md`, and `D64` to the map's check-loop list, per [D9](design.md#d9).
  Verify: `grep -n '^### D64 · Converge spends where judgment is$' docs/decisions.md` prints a line.
- [ ] 4.2 Amend D11's last bold sentence and D41's models-file clause in `docs/decisions.md`, per [D9](design.md#d9).
  Verify: `grep -c 'd64--converge-spends-where-judgment-is' docs/decisions.md` prints `2`.
- [ ] 4.3 Extend `test_reading_sets_count_words` in `tests/test_metric_scripts.py`, then the `worker` set's index in
  `scripts/metrics/reading_set.py`, per [D10](design.md#d10).
  Verify: `uv run --script scripts/metrics/reading_set.py worker` prints a number below `10500`.
- [ ] 4.4 Add `watch = 10500` to `converge-worker-reading-set` in `metrics/catalogue.toml`, per [D10](design.md#d10).
  Verify: `grep -c '^watch = 10500$' metrics/catalogue.toml` prints `2`.
- [ ] 4.5 Add the converge sentence to *Execution* in `README.md`, per [D11](design.md#d11).
  Verify: `grep -n 'd64--converge-spends-where-judgment-is' README.md` prints a line.
