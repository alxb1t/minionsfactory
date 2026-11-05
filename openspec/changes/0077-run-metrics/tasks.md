# Run metrics — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — Converge's record
- [ ] 2 — The run's time and loop
- [ ] 3 — The run's cost and review yield
- [ ] 4 — The review metrics data

## 1 — Converge's record

- [ ] 1.1 Rewrite the `verdicts` row and example in `skills/mf-converge/SKILL.md`, and add the `**Round**` row and its example line to
  `skills/mf-converge/references/worker.md`'s card, per [D1](design.md#d1).
  Verify: `grep -n 'effort <e> · tokens <n>' skills/mf-converge/SKILL.md` prints a line, and
  `grep -n '^| \*\*Round\*\* |' skills/mf-converge/references/worker.md` prints a line.
- [ ] 1.2 Log the effort in the spawn line, and give a later spawn in a stamp its own log, in `skills/mf-ship/scripts/conduct.py`;
  glob both log names in `review_metrics.py`'s `_cost_logs`, and name the newest build log in `skills/mf-rescue/SKILL.md`'s input
  row, per [D1](design.md#d1) and [D2](design.md#d2); extend `test_a_station_runs_on_its_executor` and
  `test_a_small_cap_is_granted_automatically` in `tests/test_conduct.py`, and `test_run_logs_give_cost_turns_and_tokens_per_station`
  in `tests/test_review_metrics.py`.
  Verify: `grep -n 'effort {effort}' skills/mf-ship/scripts/conduct.py` prints a line, `grep -n '_converge-2.log' tests/test_conduct.py`
  prints a line, and `uv run pytest -q tests/test_conduct.py tests/test_review_metrics.py -k "station_runs_on_its_executor or small_cap_is_granted_automatically or run_logs_give_cost"` reports `3 passed`.

## 2 — The run's time and loop

- [ ] 2.1 Add `scripts/metrics/run.py` with the time and loop kinds, and their entries and the `diff-lines`, `diff-files` station
  entries in `metrics/catalogue.toml`, per [D3](design.md#d3); add `test_run_metrics_read_the_run_logs` to
  `tests/test_metric_scripts.py`.
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k run_metrics_read_the_run_logs` reports `1 passed`.

## 3 — The run's cost and review yield

- [ ] 3.1 Add the cost and review kinds to `scripts/metrics/run.py` and their entries to `metrics/catalogue.toml`, per
  [D3](design.md#d3) and [D4](design.md#d4); add `test_run_metrics_read_cost_and_review_yield` to `tests/test_metric_scripts.py`.
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k run_metrics_read_cost_and_review_yield` reports `1 passed`, and
  `grep -n 'security-tokens-per-confirmed' metrics/catalogue.toml` prints a line.

## 4 — The review metrics data

- [ ] 4.1 Parse the tokens per role, read the Codex sessions and write `review-metrics.json` in
  `skills/mf-review-metrics/scripts/review_metrics.py`, and name the file in `skills/mf-review-metrics/SKILL.md`, per
  [D5](design.md#d5); add `test_tokens_are_read_per_role` and `test_codex_sessions_fill_the_rounds`, and extend
  `test_the_status_log_gives_duration_tokens_and_the_cap`, in `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k "tokens_are_read_per_role or codex_sessions_fill_the_rounds or status_log_gives_duration"` reports `3 passed`.
- [ ] 4.2 Amend D50 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'review-metrics.json' docs/decisions.md` prints a line.
