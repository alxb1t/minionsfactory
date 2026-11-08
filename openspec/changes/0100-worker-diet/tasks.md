# Worker diet — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [x] 1 — The spawn
- [x] 2 — The context
- [ ] 3 — Tool output
- [ ] 4 — The metrics
- [ ] 5 — The record

## 1 — The spawn

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `grep -n -e '^def argv(' -e '^def reach(' -e '^def worker_settings(' -e '^SUPERVISOR = ' -e '^def open_versions(' -e '^def _cuts(' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'FAKE_CLAUDE_ARGV' tests/fake_claude.py` prints a line.
- [x] 1.2 Add `test_every_station_starts_lean` and the edits for D1–D3 the design's [Tests](design.md#tests) names, in
  `tests/test_conduct.py`, and [D2](design.md#d2)'s in `tests/conftest.py`; then the names [D1](design.md#d1)–[D3](design.md#d3)
  give in `skills/mf-ship/scripts/conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "every_station_starts_lean or starts_in_the_sandbox or station_runs_on_its_executor or no_hook_runs or carries_the_allowlist or plan_is_read_once"` reports `6 passed`; `grep -n -e '^STATION_TOOLS = ' -e '^WORKER_TOOLS = ' -e '^CACHE_HOUR = ' -e '^def tools_for(' -e '^def _plugins_off(' -e 'exclude-dynamic-system-prompt-sections' -e 'ENABLE_PROMPT_CACHING_1H' -e 'FORCE_PROMPT_CACHING_5M' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.3 Add `test_reach_stops_at_live_worktrees` to `tests/test_conduct.py`, then `reach` in
  `skills/mf-ship/scripts/conduct.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "reach_stops_at_live_worktrees or carries_the_allowlist or starts_in_the_sandbox"` reports `3 passed`.
- [x] 1.4 Add `test_a_worker_asking_for_a_missing_tool_halts` to `tests/test_conduct.py` and the `missing-tool` mode to
  `tests/fake_worker.py`, then `MISSING`, `lacked` and `Run.spawn` in `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k missing_tool_halts` reports `1 passed`; `grep -n -e '^MISSING = "No such tool available"$' -e '^def lacked(' -e 'asked for a tool its station lacks' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'missing-tool' tests/fake_worker.py` prints a line.
- [x] 1.5 Add `test_the_probe_reports_its_first_turn` to `tests/test_conduct.py` and the `first-turn` mode to
  `tests/fake_worker.py`, then `first_turn` and `Run.probe` in `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k probe_reports_its_first_turn` reports `1 passed`; `grep -n -e '^def first_turn(' -e 'first turn {' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'first-turn' tests/fake_worker.py` prints a line.

## 2 — The context

- [x] 2.1 Add `test_decisions_print_what_the_files_cite` to `tests/test_bundle.py`, then `decisions_text` and the
  `--decisions` form in `skills/mf-converge/scripts/bundle.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_bundle.py` reports `3 passed`; `grep -n -e '^def decisions_text(' -e '"--decisions"' skills/mf-converge/scripts/bundle.py` prints a line for each.
- [x] 2.2 Add the `mf-build` and `mf-cut-change` rows of `bundle.py` to `_METRICS_SCRIPTS` and the expected lists in
  `tests/test_skills.py`; then edit *The record* in `AGENTS.md`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
  `skills/mf-converge/SKILL.md` and `skills/mf-bootstrap/templates/AGENTS.md.tmpl`, per [D7](design.md#d7).
  Verify: `grep -n 'bundle.py --decisions' AGENTS.md skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints a line for each file; `grep -n 'no other mandatory context' skills/mf-converge/SKILL.md` prints a line; `grep -n -e 'the cut, build and converge — also read' AGENTS.md skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints nothing; `uv run pytest -q tests/test_skills.py` reports `21 passed`.
- [x] 2.3 Edit `test_reading_sets_count_words` in `tests/test_metric_scripts.py`, then `SETS["converge"]` in
  `scripts/metrics/reading_set.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k reading_sets_count_words` reports `1 passed`.
- [x] 2.4 Extend `test_the_supervisor_runs_on_its_own_table` in `tests/test_conduct.py`, then `CONDUCTOR` and `_models` in
  `skills/mf-ship/scripts/conduct.py`, per [D8](design.md#d8).
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_runs_on_its_own_table` reports `1 passed`; `grep -n '^CONDUCTOR = ("claude-sonnet-5-5", "high")$' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.5 Edit Steps 6 and 7 of `skills/mf-converge/SKILL.md` and the Converge bullet of *Suggesting models* in
  `skills/mf-cut-change/SKILL.md`, per [D8](design.md#d8), each new phrase on one line.
  Verify: `grep -n -e "always at the fixer's effort" -e "verify worker runs on its role's model" skills/mf-converge/SKILL.md` prints a line for each; `grep -n -e 'conductor, .\[converge\]., on Sonnet 5.5 · high' -e 'the fixer on the mid tier · medium' skills/mf-cut-change/SKILL.md` prints a line for each.
- [x] 2.6 Extend `test_a_stamp_writes_the_clock_time_under_the_latest_run` and `test_a_log_out_of_shape_is_not_stamped` in
  `tests/test_stamp.py`, then `skills/mf-converge/scripts/stamp.py`; edit *An event* and Step 5 of
  `skills/mf-converge/SKILL.md`, per [D9](design.md#d9), each new phrase on one line.
  Verify: `uv run pytest -q tests/test_stamp.py` reports `2 passed`; `grep -n 'nargs="\*"' skills/mf-converge/scripts/stamp.py` prints a line; `grep -n -e 'in one call' -e 'both .verdicts. lines in one' skills/mf-converge/SKILL.md` prints a line for each.

## 3 — Tool output

- [ ] 3.1 Add `test_a_gate_runs_without_the_venv_and_quiet_when_green` to `tests/test_gate_run.py`, then
  `skills/mf-converge/scripts/gate_run.py`, per [D10](design.md#d10).
  Verify: `uv run pytest -q tests/test_gate_run.py` reports `8 passed`; `grep -n -e '"VIRTUAL_ENV"' -e 'stdout=subprocess.PIPE' skills/mf-converge/scripts/gate_run.py` prints a line for each.
- [ ] 3.2 Set `addopts` in `pyproject.toml` and the pytest cell of `skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl`,
  per [D11](design.md#d11).
  Verify: `grep -n -e '--tb=short' pyproject.toml skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl` prints a line for each file.

## 4 — The metrics

- [ ] 4.1 Extend `test_run_logs_give_cost_turns_and_tokens_per_station` in `tests/test_review_metrics.py` with `cut` and
  `supervise` logs and first turns, then `STATIONS`, `first_turn`, `_results`, `_spent`, `_cost_logs` and `cost_table` in
  `skills/mf-review-metrics/scripts/review_metrics.py`, per [D12](design.md#d12).
  Verify: `uv run pytest -q tests/test_review_metrics.py -k run_logs_give_cost` reports `1 passed`; `grep -n '^def first_turn(' skills/mf-review-metrics/scripts/review_metrics.py` prints a line.
- [ ] 4.2 Add `test_workers_are_priced_per_round_and_role` and edit `test_codex_sessions_fill_the_rounds` in
  `tests/test_review_metrics.py`, then `WORKER`, `_converge_workers`, `_priced_worker`, the records' `dollars` and the data's
  `workers` and `stations` in `review_metrics.py`, and `prices.toml`'s comment, per [D12](design.md#d12).
  Verify: `uv run pytest -q tests/test_review_metrics.py -k "workers_are_priced or codex_sessions_fill"` reports `2 passed`; `grep -n -e '^WORKER = ' -e '^def _converge_workers(' -e '^def _priced_worker(' skills/mf-review-metrics/scripts/review_metrics.py` prints a line for each; `grep -n 'cache_write_1h' skills/mf-review-metrics/prices.toml` prints a line.
- [ ] 4.3 Add `test_every_repo_a_run_started_in` to `tests/test_review_metrics.py` and a step to `test_every_station_starts_lean`
  asserting the home folder's `repos`, then `recorded` and `settings` in `review_metrics.py` and `_record_repo` and `run` in
  `skills/mf-ship/scripts/conduct.py`, per [D12](design.md#d12).
  Verify: `uv run pytest -q tests/test_review_metrics.py tests/test_conduct.py -k "every_repo_a_run_started_in or no_config_exits_2 or every_station_starts_lean or runs_close_starts_the_next_run"` reports `4 passed`; `grep -n '^def _record_repo(' skills/mf-ship/scripts/conduct.py` prints a line; `grep -n '^def recorded(' skills/mf-review-metrics/scripts/review_metrics.py` prints a line.
- [ ] 4.4 Extend `test_the_page_draws_charts_and_lists_gaps` in `tests/test_review_metrics.py`, then `_role`, `model_table`
  and `summary` in `skills/mf-review-metrics/scripts/review_metrics.py`, per [D12](design.md#d12) (`0097·R4`).
  Verify: `uv run pytest -q tests/test_review_metrics.py -k page_draws_charts` reports `1 passed`; `grep -n -e 'median duration (s)' -e 'median tokens' skills/mf-review-metrics/scripts/review_metrics.py` prints a line for each.
- [ ] 4.5 Edit *Run* and *Report* in `skills/mf-review-metrics/SKILL.md` and the skill's row in `README.md`, per
  [D12](design.md#d12) (`0097·R3`).
  Verify: `grep -n 'per role, executor and model' README.md` prints a line; `grep -n 'per model' README.md` prints nothing; `grep -n -e 'first-turn context' -e 'cost per worker' skills/mf-review-metrics/SKILL.md` prints a line for each.

## 5 — The record

- [ ] 5.1 Add D69 after D67 in `docs/decisions.md`, and `D69` to the map's line of *Repo conventions*, per
  [D13](design.md#d13).
  Verify: `grep -n '^### D69 · A worker starts lean$' docs/decisions.md` prints a line; `grep -n 'D61, D67, D69' docs/decisions.md` prints a line.
- [ ] 5.2 Amend D48, D50 and D64 in `docs/decisions.md`, per [D13](design.md#d13), each new phrase on one line (`0097·R2`).
  Verify: `grep -n "Converge's conductor runs on the mid tier · medium" docs/decisions.md` prints nothing; `grep -n -e "Converge's conductor runs on Sonnet 5.5 · high" -e "adversarial running on converge's host, when a" -e 'Verify runs at medium.' -e 'reading those it cites and an index' -e 'and every repo a run started in' -e 'round, role and station, with first-turn context' docs/decisions.md` prints a line for each.
- [ ] 5.3 Edit *Trust boundaries* in `THREAT_MODEL.md` and *The repo reaches nothing outside itself* in `docs/principles.md`,
  per [D13](design.md#d13), each new phrase on one line.
  Verify: `grep -n -e "station's tools alone, and the operator's plugins" -e 'the repo and its open worktrees' THREAT_MODEL.md` prints a line for each; `grep -n -e 'or a run started in' -e 'the list of repos a run started in' docs/principles.md` prints a line for each.
