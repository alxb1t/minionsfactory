# Code metrics — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The codebase
- [ ] 2 — The tests

## 1 — The codebase

- [x] 1.1 Add `scripts/metrics/codebase.py` with the codebase's kinds, and their entries after `gate-seconds` in
  `metrics/catalogue.toml`, per [D1](design.md#d1) and [D4](design.md#d4); add `test_code_metrics_read_the_tree` and
  `test_complex_functions_are_read_from_ruff` to `tests/test_metric_scripts.py`, after
  `test_tests_collected_is_unavailable_on_a_broken_collection`.
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k "code_metrics_read_the_tree or complex_functions_are_read_from_ruff"` reports `2 passed`.

## 2 — The tests

- [ ] 2.1 Change the `gate` recipe in `Makefile` so its pytest step writes the junit report, and name the report in `AGENTS.md`'s
  account of the gate, per [D2](design.md#d2):
  ```diff
  - 	uv run coverage run -m pytest -q -n auto
  + 	uv run coverage run -m pytest -q -n auto --junitxml=.minions/test-report.xml
  ```
  Verify: `grep -n 'junitxml=.minions/test-report.xml' Makefile` prints a line.
- [ ] 2.2 Add the test kinds to `scripts/metrics/codebase.py` and their entries to `metrics/catalogue.toml`, per [D3](design.md#d3)
  and [D4](design.md#d4); add `test_test_metrics_read_the_junit_report` to `tests/test_metric_scripts.py`.
  Add `test_the_code_script_runs_as_the_collector_runs_it`.
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k "test_metrics_read_the_junit_report or code_script_runs_as_the_collector"` reports `2 passed`.
