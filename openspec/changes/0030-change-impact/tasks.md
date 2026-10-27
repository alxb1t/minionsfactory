# Change impact — tasks

Build the settled [design](design.md), one phase at a time. The metric ids, the exit codes and the station text are
the design's, word for word.

## Progress

- [x] 1 — Write the collector
- [ ] 2 — Write MF's catalogue and metric scripts
- [ ] 3 — Add the stations' metrics steps
- [ ] 4 — Record the design and demonstrate it on MF

## 1 — Write the collector

- [x] 1.1 **HALT CHECK** `uv` provides a Python at `>=3.12` with `tomllib`, the premise of [D2](design.md#d2).
  Verify: `uv run --no-project --python '>=3.12' python -c 'import tomllib'` exits 0.
- [x] 1.2 Write `skills/mf-build/scripts/metrics.py` per [D2](design.md#d2) through [D5](design.md#d5): `collect` and `page`, the exit codes, the `metric_argv` seam, its PEP 723 header pinning `>=3.12`.
  Verify: `uv run --script skills/mf-build/scripts/metrics.py --help` exits 0.
- [x] 1.3 Write `tests/test_metrics.py` with the tests the [Tests](design.md#tests) table names for it.
  Verify: `uv run pytest -q tests/test_metrics.py` reports `9 passed`.

## 2 — Write MF's catalogue and metric scripts

- [ ] 2.1 Write `scripts/metrics/reading_set.py`, `rule_ids.py`, `tests_collected.py`, `prose.py`, `references.py`, `conformance.py` and `backlog.py` per [D7](design.md#d7), each with a PEP 723 header.
  Verify: `ls scripts/metrics/*.py | wc -l` prints `7`.
- [ ] 2.2 Write `metrics/catalogue.toml` with [D7](design.md#d7)'s entries, in its table's order.
  Verify: `grep -c '^\[\[metric\]\]' metrics/catalogue.toml` prints `12`.
- [ ] 2.3 Write `tests/test_metric_scripts.py` with the tests the [Tests](design.md#tests) table names for it.
  Verify: `uv run pytest -q tests/test_metric_scripts.py` reports `6 passed`.

## 3 — Add the stations' metrics steps

- [ ] 3.1 Add *Step 3.5 — Collect the metrics* to `skills/mf-build/SKILL.md` and extend its Step 4 sentences, per [D6](design.md#d6).
  Verify: `grep -c '^## Step 3.5 — Collect the metrics$' skills/mf-build/SKILL.md` prints `1`, and `grep -q 'metrics: none — no catalogue' skills/mf-build/SKILL.md` exits 0.
- [ ] 3.2 Add item 2b to `skills/mf-release/SKILL.md` Step 4, and extend its item 4 and its Step 6 sentences, per [D6](design.md#d6).
  Verify: `grep -c '\*\*2b\. Metrics\.\*\*' skills/mf-release/SKILL.md` prints `1`, and `grep -c '\.\./mf-build/scripts/metrics\.py' skills/mf-release/SKILL.md` prints `1`.
- [ ] 3.3 Add `test_the_stations_run_the_bundled_metrics_script` and `test_the_metrics_script_scan_reports_a_missing_script` to `tests/test_skills.py`.
  Verify: `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.

## 4 — Record the design and demonstrate it on MF

- [ ] 4.1 In `docs/decisions.md`, add D43 after D40, extend the overview line, and amend D2 and D18, per [D8](design.md#d8).
  Verify: `grep -c "^### D43 · Project health is measured per change, from the repo's own catalogue$" docs/decisions.md` prints `1`, and `grep -c 'D11…D17, D40, D43' docs/decisions.md` prints `1`.
- [ ] 4.2 Name the new paths in `AGENTS.md`, `README.md` and `docs/README.md`, per [D8](design.md#d8).
  Verify: `grep -q 'scripts/metrics/' AGENTS.md && grep -q 'scripts/metrics/' docs/README.md && grep -q 'metrics/catalogue.toml' README.md` exits 0.
- [ ] 4.3 Collect and render this change's draft on MF, per [D9](design.md#d9): `uv run --script skills/mf-build/scripts/metrics.py collect --change 0030-change-impact --base 8c88e90 --out .minions/metrics/0030-change-impact.json`, then `uv run --script skills/mf-build/scripts/metrics.py page 0030-change-impact --data .minions/metrics/0030-change-impact.json`.
  Verify: ``uv run python -c 'import json; v = json.load(open(".minions/metrics/0030-change-impact.json"))["values"]; assert len(v) == 12 and all("value" in v[k] for k in v if k != "gate-seconds")'`` exits 0, and `grep -q 'What moved' .minions/metrics/0030-change-impact.html` exits 0.
- [ ] 4.4 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `35 tests collected`.
