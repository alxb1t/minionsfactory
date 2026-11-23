# Run fields — tasks

The run log gains a build's phase, the load, a halt's cause and the gates' lines, and its readers show them; each phase ends with its tests turned.

## Progress

- [x] 1 — The phase on a build's spawn line · moderate
- [x] 2 — The load on spawn and finish lines · moderate
- [x] 3 — A halt's cause · moderate
- [x] 4 — The gates' lines · moderate
- [x] 5 — The readers · moderate
- [x] 6 — The records · moderate

## 1 — The phase on a build's spawn line

- [x] 1.1 In `skills/mf-ship/scripts/conduct.py` add the constant `REPAIR_PHASE = "repair"`. Give `Run.spawn` and `Run.worker` the keyword `phase`, `None` by default, and write the spawn line as `<station> · <phase> · model …` when it is given ([D1](design.md#d1)).
  Verify: `git grep -n -e "REPAIR_PHASE" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.2 In `advance` pass `phase N` for a numbered phase and `close` for the close to the build spawn. In `Run.gate_built` pass `phase=REPAIR_PHASE` to the repair spawn. No other call passes one.
  Verify: `git grep -n -e "phase=REPAIR_PHASE" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.3 In `tests/test_conduct.py` the tests `test_a_build_runs_a_worker_per_phase`, `test_the_close_runs_on_the_close_table_then_moderate_then_build` and `test_a_red_gate_after_the_last_phase_is_repaired_once` split a build spawn line on `" · spawn — build · "`; make each expect the phase before the model. Add `test_a_build_spawn_line_names_its_phase`: phase 2, the close and the repair carry theirs, a release's spawn carries none.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_build_spawn_line_names_its_phase` exits 0.

## 2 — The load on spawn and finish lines

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py` add `def _load_tail`: ` · load <n>` from `os.getloadavg()[0]`, one decimal, and `""` when the read raises `OSError` ([D2](design.md#d2)). End the spawn and finish lines of `Run.worker` with it.
  Verify: `git grep -n -e "def _load_tail" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 2.2 End the converge script's spawn and finish lines in `Run.conducted` with the tail, so the spawn line is built as `script{_load_tail()}`.
  Verify: `git grep -n -F -e "script{_load_tail" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 2.3 In `tests/test_conduct.py` add an autouse fixture that fixes `os.getloadavg`, and make each assertion that ends a spawn, finish or converge-finish line take the load ([D6](design.md#d6)). Do the same for the whole-line assertion of `test_case_m_the_spawn_finish_denied_and_limited_lines` in `tests/test_claim.py`. Add `test_a_spawn_and_finish_end_with_the_load`, `test_a_load_that_cannot_be_read_leaves_the_field_out` and `test_the_converge_script_pair_ends_with_the_load` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_spawn_and_finish_end_with_the_load or test_a_load_that_cannot_be_read_leaves_the_field_out or test_the_converge_script_pair_ends_with_the_load"` exits 0.

## 3 — A halt's cause

- [x] 3.1 In `skills/mflib/runlog.py` add `CAUSES`, the list of [D3](design.md#d3), and `cause_suffix`, which returns ` · cause <word>` and raises `ValueError` on a word off the list. Add `test_the_cause_list_and_its_suffix` to `tests/test_runlog.py`.
  Verify: `uv run pytest tests/test_runlog.py -q -k test_the_cause_list_and_its_suffix` exits 0.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py` add `def cause_of(who, reason)`: the table of [D3](design.md#d3), its rows in that order, first row that holds wins, `other` for none.
  Verify: `git grep -n -e "def cause_of" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 3.3 `Run.halt` writes the reason and `cause_suffix(cause_of(…))` and keeps the bare reason in `self.halts`. `Run.final` ends with the cause of its first reason. The early crash's line in `run` ends with the cause `run`. The calls of `Run.closing` carry none.
  Verify: `git grep -n -e "cause_suffix(" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 3.4 In `tests/test_conduct.py` make each assertion that ends a halt line, the final halt of `test_wait_halt_ends_at_a_final_halt` and the rescue and supervision text of `test_a_stuck_stage_halt_names_its_rescue_and_supervision` take the cause. Add `test_a_halt_line_ends_with_its_cause` for each row of the table, its cases holding the real texts `converge check fail — the status log halts: …`, `integrate check fail — integrate halted — red gate …` and `probe check fail — …`, `test_a_halt_that_fits_no_row_is_other`, `test_the_final_halt_carries_the_first_reasons_cause`, `test_the_run_closing_line_carries_no_cause` over the closing line and the person's stop line, `test_a_converge_halt_is_classed_by_its_words`, `test_a_workers_text_after_a_failed_check_is_no_cause` and `test_an_early_crash_ends_with_the_cause_run`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_halt_line_ends_with_its_cause or test_a_halt_that_fits_no_row_is_other or test_the_final_halt_carries_the_first_reasons_cause or test_the_run_closing_line_carries_no_cause or test_a_converge_halt_is_classed_by_its_words or test_a_workers_text_after_a_failed_check_is_no_cause or test_an_early_crash_ends_with_the_cause_run"` exits 0.

## 4 — The gates' lines

- [x] 4.1 In `_run_gate` of `skills/mf-ship/scripts/conduct.py` say `check — gate · start` before each gate run, the rerun after a load wait included ([D4](design.md#d4)).
  Verify: `git grep -n -e "gate · start" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 4.2 Add `def logged(self, change, event, detail)` to `Run` in `skills/mf-ship/scripts/conduct.py`, one run-log line, and the same method to the `Host` protocol of `skills/mf-converge/scripts/converge.py`.
  Verify: `git grep -n -e "def logged" -- skills/mf-converge/scripts/converge.py` exits 0.
- [x] 4.3 In `skills/mf-converge/scripts/converge.py` add `def gate_line`, which times a gate and writes `check — gate · pass · <n>s` or `check — gate · fail — red · <n>s` through the host. Call it at `gated`, in `fix` at each fixer pass, and in `finish`; write no start line.
  Verify: `git grep -n -e "def gate_line" -- skills/mf-converge/scripts/converge.py` exits 0.
- [x] 4.4 In `tests/test_conduct.py` make the tests that count or order `check — gate` lines, among them `_gate_lines` and the load-wait order of `test_a_gate_red_under_load_waits_and_runs_again` and the printed lines of `test_close_on_a_green_gate_prints_the_gate_line`, `test_close_on_a_red_gate_writes_gate_red_and_build_halt` and `test_a_red_gate_after_simplify_drops_its_commit`, expect each start. Add `test_a_gate_logs_its_start_before_its_result` and `test_a_gate_rerun_after_a_load_wait_logs_a_second_start`. Give the fake hosts of `tests/test_converge.py` a `logged` method and add `test_converge_logs_each_gate_with_its_seconds` and `test_a_reused_gate_record_is_logged_as_a_pass`.
  Verify: `uv run pytest tests/test_conduct.py tests/test_converge.py -q -k "test_a_gate_logs_its_start_before_its_result or test_a_gate_rerun_after_a_load_wait_logs_a_second_start or test_converge_logs_each_gate_with_its_seconds or test_a_reused_gate_record_is_logged_as_a_pass"` exits 0.

## 5 — The readers

- [x] 5.1 In `skills/mf-ui/scripts/viewer.py` give each worker a `phase`, read from its spawn line, and each version a `gate_running` flag, true only under a live claim, and a `cause` ([D5](design.md#d5)). In `skills/mf-ui/page/index.html` show the phase on the worker's row, a running gate and the cause, each as text.
  Verify: `git grep -n -e "gate_running" -- skills/mf-ui/scripts/viewer.py` exits 0.
- [x] 5.2 In `skills/mf-review-metrics/scripts/review_metrics.py` add `_phases`, which matches each build log to its spawn line by the stamp and the ordinal its name holds. Add `phases` rows to `review-metrics.json`, and `def phase_table` as a table of each repo's section.
  Verify: `git grep -n -e "def phase_table" -- skills/mf-review-metrics/scripts/review_metrics.py` exits 0.
- [x] 5.3 In `tests/test_viewer.py` add `test_a_worker_shows_its_phase`, `test_a_running_gate_is_the_versions_last_line`, `test_a_stale_claim_shows_no_running_gate` and `test_a_halt_shows_its_cause`, and put the fields in its fixtures. In `tests/test_review_metrics.py` add `test_build_cost_is_booked_by_phase` and `test_the_phase_table_has_a_row_per_build_log`. In `tests/test_metric_scripts.py` add `test_run_reads_a_log_with_the_new_fields`, over lines that hold a phase, a load and a cause.
  Verify: `uv run pytest tests/test_viewer.py tests/test_review_metrics.py tests/test_metric_scripts.py -q -k "test_a_worker_shows_its_phase or test_a_running_gate_is_the_versions_last_line or test_a_stale_claim_shows_no_running_gate or test_a_halt_shows_its_cause or test_build_cost_is_booked_by_phase or test_the_phase_table_has_a_row_per_build_log or test_run_reads_a_log_with_the_new_fields"` exits 0.

## 6 — The records

- [x] 6.1 In `docs/decisions.md` add `### D90 · The run log carries a build's phase, the load, a halt's cause and each gate`, after D89: the fields and their reach as [design](design.md) states them, with Why, Accepts and Rejected.
  Verify: `git grep -n -e "### D90" -- docs/decisions.md` exits 0.
- [x] 6.2 In `skills/mf-review-metrics/SKILL.md` add the data key `phases` beside `stations`: one row per build log, its phase, dollars, turns, tokens, seconds and first-turn context.
  Verify: `git grep -n -i -e "phases" -- skills/mf-review-metrics/SKILL.md` exits 0.
