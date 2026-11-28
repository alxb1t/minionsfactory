# Metric scripts — tasks

The phases pin the metric scripts' reads on today's side, add the home's new pieces, move the logs, then the files, onto the home and turn the settled readings, and write the record.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · moderate
- [ ] 3 — The logs · hard
- [ ] 4 — The files · moderate
- [ ] 5 — The record · moderate

## 1 — The pin

- [x] 1.1 **HALT CHECK** `skills/mflib/prices.py` is tracked nowhere, so phase 2 adds it as a new module ([D4](design.md#d4)).
  Verify: `git ls-files --error-unmatch skills/mflib/prices.py` exits `1`.
- [x] 1.2 Add `tests/test_metric_pins.py` with its harness and the slice R cases of [the cases](cases.md#slice-r--the-run-log) on the run log's day rule, its file list and its shapes: `scripts/metrics/run.py` is loaded by `importlib.util.spec_from_file_location` as `tests/test_metric_scripts.py` does, each log is written under a `tmp_path` primary, a case reaches the code through `run.measure` and `run.Version`'s public methods and starts no worker. Name each case a row of [the turns](cases.md#the-turns) lists as that row does, `test_clock_stepping_back_under_12h_is_no_midnight` among them, type each fixture in the home's form ([D12](design.md#d12)), and run a FIFO in a child with a timeout, marked `slow` ([D14](design.md#d14)).
  Verify: `uv run pytest tests/test_metric_pins.py -k test_clock_stepping_back_under_12h_is_no_midnight -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.3 Add the slice R cases of `_versions`, `spawns`, `stage`, `minutes`, `halts`, `waits` and `after_waits` to `tests/test_metric_pins.py`, each through `Version`'s public methods; `test_a_halt_of_the_build_is_counted_by_its_words` holds the `halts` cases and `test_a_wait_ends_at_a_rejoin` the `waits` cases.
  Verify: `uv run pytest tests/test_metric_pins.py -k "test_a_halt_of_the_build_is_counted_by_its_words or test_a_wait_ends_at_a_rejoin" -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.4 Add the slice S status-log cases of [the cases](cases.md#slice-s--the-status-log-the-findings-buildone-the-proposal) to `tests/test_metric_pins.py`: `test_status_log_headings_and_marks`, `test_blockers_read_the_round_one_verdicts` and `test_status_log_file_shapes`, each status-log line typed whole as `HH:MM:SS · round N · <name> — <detail>` and each `verdicts` line with its role, verdict word, count and spent tail, but where the key says the odd form is the case, as `odd-bare-fragment-no-clock` does.
  Verify: `uv run pytest tests/test_metric_pins.py -k "test_status_log_headings_and_marks or test_blockers_read_the_round_one_verdicts or test_status_log_file_shapes" -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.5 Add the slice S findings and `build.done` cases to `tests/test_metric_pins.py`: `test_findings_cards_and_the_refuted_section`, `test_findings_file_shapes`, `test_build_done_head`, `test_build_done_file_shapes` and the cases of `commits`, `paid` and `escapes`, each card typed as a titled line `- **R1 — a title**` with indented fields, but where the key says the odd form is the case.
  Verify: `uv run pytest tests/test_metric_pins.py -k "test_findings_cards_and_the_refuted_section or test_findings_file_shapes or test_build_done_head or test_build_done_file_shapes" -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.6 Add the slice S group E cases to `tests/test_metric_pins.py` as `test_the_old_eras_from_disk`: each old log is `## Run 1 — 2026-09-28 12:00` and the real lines verbatim, read through `blockers-round-1` and `converge-rounds`, and `statuslog.verdicts` of each line.
  Verify: `uv run pytest tests/test_metric_pins.py -k test_the_old_eras_from_disk -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.7 Add the slice W worker-log cases of [the cases](cases.md#slice-w--worker-logs-prices-the-debt-file) to `tests/test_metric_pins.py`: `_spent`, `_summed`, `Version.checkers`, `Version.quota`, `Version.role_tokens` and the shapes of a worker log, each on today's side; `test_a_codex_logs_turns_are_summed_into_tokens` holds the `_summed` cases.
  Verify: `uv run pytest tests/test_metric_pins.py -k test_a_codex_logs_turns_are_summed_into_tokens -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.8 Add the slice W price cases to `tests/test_metric_pins.py`: `test_prices_toml_read_by_both_scripts_for_a_codex_log`, `test_a_codex_log_whose_model_is_null_or_has_no_row`, `test_prices_toml_for_a_claude_worker`, `test_a_claude_workers_model_and_usage_shapes`, `test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty` and `test_a_prices_file_that_is_a_fifo_blocks_both_scripts`, calling `run._priced`, `review_metrics._prices` and `review_metrics.main`; the FIFO case runs in a child with a timeout, marked `slow`, and is the one case that dies with the move.
  Verify: `uv run pytest tests/test_metric_pins.py -k "test_prices_toml_read_by_both_scripts_for_a_codex_log or test_a_codex_log_whose_model_is_null_or_has_no_row or test_prices_toml_for_a_claude_worker or test_a_claude_workers_model_and_usage_shapes or test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty or test_a_prices_file_that_is_a_fifo_blocks_both_scripts" -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.9 Add the slice W debt cases to `tests/test_metric_pins.py`: `test_the_debt_script_counts_cards_of_four_digits_at_a_line_start`, `test_the_debt_script_reads_a_link_and_reports_a_missing_file`, `test_a_debt_file_with_a_bad_byte_is_a_traceback`, `test_a_versions_debt_is_the_cards_of_its_own_section`, `test_a_versions_debt_in_odd_files` and `test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte`, `debt.py` run as a subprocess and through `debt.cards`, each card typed as `- **0023·R1 — a title**` but where the key says the odd form is the case.
  Verify: `uv run pytest tests/test_metric_pins.py -k "test_the_debt_script_counts_cards_of_four_digits_at_a_line_start or test_the_debt_script_reads_a_link_and_reports_a_missing_file or test_a_debt_file_with_a_bad_byte_is_a_traceback or test_a_versions_debt_is_the_cards_of_its_own_section or test_a_versions_debt_in_odd_files or test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte" -q` exits `0`; `uv run pytest tests/test_metric_pins.py -n auto -q` exits `0`.
- [x] 1.10 The phase edits no script and no module.
  Verify: `git diff --stat HEAD -- scripts/metrics skills/mf-review-metrics skills/mflib` prints nothing.

## 2 — The module

- [x] 2.1 Add `logs(runs)` to `skills/mflib/runlog.py` and let `timed` pass by a line whose clock is no time of day ([D1](design.md#d1)); add `test_logs_list_each_real_stamp_oldest_first`, `test_logs_pass_over_a_name_that_is_no_date`, `test_timed_passes_by_a_clock_that_is_no_time` and `test_parse_still_reads_a_clock_of_25_hours` to `tests/test_runlog.py`, and `test_a_log_with_a_clock_of_25_hours_still_shows_its_other_events` to `tests/test_viewer.py`.
  Verify: `uv run pytest tests/test_runlog.py tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 2.2 Add `blocking(event)` to `skills/mflib/statuslog.py` ([D2](design.md#d2)); add `test_blocking_reads_the_count_of_a_conformance_line`, `test_blocking_reads_a_line_with_no_verdict_word_and_no_tail`, `test_blocking_is_none_for_an_old_role_and_for_another_event` and `test_blocking_reads_the_first_count_of_a_line` to `tests/test_statuslog.py`.
  Verify: `uv run pytest tests/test_statuslog.py -q` exits `0`.
- [x] 2.3 Add `refuted(text)` to `skills/mflib/findings.py` ([D3](design.md#d3)); add `test_refuted_gives_the_top_level_entries_of_the_section`, `test_refuted_ends_at_the_next_second_level_heading`, `test_refuted_reads_a_heading_on_the_last_line_with_no_newline` and `test_refuted_is_none_without_the_heading` to `tests/test_findings.py`.
  Verify: `uv run pytest tests/test_findings.py -q` exits `0`.
- [x] 2.4 Add `skills/mflib/prices.py` with `rows(path)` and `Unreadable` ([D4](design.md#d4)), and its row in `docs/modules.md`: layer `home`, names `statefile.py`. Add `tests/test_prices.py` with a case for the table read, a row with a string price and a bool, a link, a folder, a file over `262144` bytes, text that is no TOML, a `models` that is missing and one that is no table, and a pipe read in a child with a timeout, marked `slow`; each error path of `rows` has its case ([D14](design.md#d14)).
  Verify: `uv run pytest tests/test_prices.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.5 Add `skills/mflib/eras.py` with `blocking(event)` and `refuted(text)` ([D5](design.md#d5)), and its row in `docs/modules.md`: layer `home`, names `statuslog.py`. Add `tests/test_eras.py` with the lines of isekai's `0037` (`review … open_blocking 2 (R1, R2)` and `security … open_blocking 0`), MF's `0095` lines, the colon form, today's roles giving none, and `refuted` over `## Refused` giving the entries and over `## Refuted` giving none.
  Verify: `uv run pytest tests/test_eras.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.6 No script calls the new functions, no station has `mflib.eras` and none has `import eras` ([D5](design.md#d5)).
  Verify: `git diff --stat HEAD -- scripts/metrics skills/mf-review-metrics/scripts/review_metrics.py` prints nothing; `git grep -c -e "mflib.eras" -e "import eras" -- skills/mf-ship skills/mf-converge skills/mf-build skills/mf-cut-change skills/mf-release skills/mf-integrate skills/mf-ui` prints nothing.
- [x] 2.7 The module set and the viewer set pass with the new cases ([D15](design.md#d15)).
  Verify: `uv run pytest tests/test_runlog.py tests/test_statuslog.py tests/test_findings.py tests/test_marks.py tests/test_debtfile.py tests/test_prices.py tests/test_eras.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.

## 3 — The logs

- [ ] 3.1 In `scripts/metrics/run.py` read the run log through `runlog.logs`, `statefile.lines` with the bound `262144` and `runlog.timed`, building its own `Event` from each pair, `at` the `datetime.fromtimestamp` of the moment, and import `mflib.runlog` and `mflib.statefile` under the seed line ([D6](design.md#d6)).
  `STAMP`, `EVENT`, `MIDNIGHT`, `_logs` and `_events` are removed.
  Verify: `git grep -l -e "runlog.timed" -- scripts/metrics/run.py` prints `scripts/metrics/run.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`.
- [ ] 3.2 In `tests/test_metric_pins.py` turn the slice R rows of [the turns](cases.md#the-turns) for phase 3 and no other assert ([D12](design.md#d12)); take the entry of `run.py`'s clock pattern out of `FORMAT_SITES` in `tests/test_structure.py` and make `run.py`'s row of `docs/modules.md` `layout.py, runlog.py, statefile.py` ([D13](design.md#d13)).
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 3.3 In `scripts/metrics/run.py` read the status log through `layout.status_log`, `statuslog.read`, `statuslog.runs`, `statuslog.blocking` and `eras.blocking`, in `rounds`, `blockers`, `grants` and `amends`, importing `mflib.statuslog` and `mflib.eras` under the seed line ([D7](design.md#d7)); a log `statuslog.read` refuses is the gap `no <change>/status_log.md`, reached by the `link` case of `test_status_log_file_shapes`, and the count from `eras.blocking` by the old-role cases of `test_blockers_read_the_round_one_verdicts` ([D14](design.md#d14)).
  Verify: `git grep -l -e "statuslog.runs" -- scripts/metrics/run.py` prints `scripts/metrics/run.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`.
- [ ] 3.4 In `tests/test_metric_pins.py` turn the slice S status-log rows of [the turns](cases.md#the-turns) for phase 3 and no other assert; take `run.py`'s `## Run` and `status_log.md` entries out of `FORMAT_SITES` in `tests/test_structure.py` and make `run.py`'s row of `docs/modules.md` `eras.py, layout.py, runlog.py, statefile.py, statuslog.py`.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 3.5 The phase leaves the test files that [D12](design.md#d12) closes to asserts as they were, and the module set holds.
  They are `tests/test_metric_scripts.py`, `tests/test_review_metrics.py` and `tests/test_run_dir_finders.py`.
  Verify: `git diff --stat HEAD -- tests/test_metric_scripts.py tests/test_review_metrics.py tests/test_run_dir_finders.py` prints nothing; `uv run pytest tests/test_runlog.py tests/test_statuslog.py tests/test_findings.py tests/test_marks.py tests/test_debtfile.py tests/test_prices.py tests/test_eras.py tests/test_structure.py -n auto -q` exits `0`.

## 4 — The files

- [ ] 4.1 In `scripts/metrics/run.py` read the findings through `layout.findings_file`, `findings.read`, `findings.cards` and `findings.refuted`, else `eras.refuted`, in `cards`, `confirmed`, `refuted`, `per_confirmed` and `escapes`, importing `mflib.findings` under the seed line ([D8](design.md#d8)); the gap `no <change>/<role>.md` is reached by the `link` case of `test_findings_file_shapes` and `eras.refuted` by the `odd-refused-heading` case ([D14](design.md#d14)).
  `PRIORITY` and `CONFIRMED` are removed.
  Verify: `git grep -l -e "findings.refuted" -- scripts/metrics/run.py` prints `scripts/metrics/run.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`.
- [ ] 4.2 In `tests/test_metric_pins.py` turn the slice S findings rows of [the turns](cases.md#the-turns) for phase 4 and no other assert; make `run.py`'s row of `docs/modules.md` `eras.py, findings.py, layout.py, runlog.py, statefile.py, statuslog.py`.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 4.3 In `scripts/metrics/run.py` read `build.done` through `marks.done_head` in `commits`, importing `mflib.marks` under the seed line ([D9](design.md#d9)); the gap `no head in <change>/build.done` is reached by the `link` and `bad-byte` cases of `test_build_done_file_shapes` ([D14](design.md#d14)).
  Verify: `git grep -l -e "marks.done_head" -- scripts/metrics/run.py` prints `scripts/metrics/run.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`.
- [ ] 4.4 In `tests/test_metric_pins.py` turn the slice S `build.done` rows of [the turns](cases.md#the-turns) for phase 4 and no other assert; take `run.py`'s `build.done` entry out of `FORMAT_SITES` in `tests/test_structure.py` and add `marks.py` to `run.py`'s row of `docs/modules.md`.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 4.5 Retype the typed lines of `test_the_backlog_is_read_from_the_primary_run_directory` in `tests/test_metric_scripts.py` as `- **0023·a — x**` and `- **0024·b — y**`, its assert of `2` standing ([D10](design.md#d10)).
  Verify: `git grep -l -F -e "0023·a — x" -- tests/test_metric_scripts.py` prints `tests/test_metric_scripts.py`; `uv run pytest tests/test_metric_scripts.py -q` exits `0`.
- [ ] 4.6 In `scripts/metrics/debt.py` and in `Version.debt` of `scripts/metrics/run.py` read the debt file through `debtfile.read` and count through `debtfile.count`, `debt.py`'s `__main__` exiting `no <file>: <reason>` and `Version.debt` giving the gap `no .minions/debt.md: <reason>` for `debtfile.Unreadable`, importing `mflib.debtfile` under the seed line ([D10](design.md#d10)); both lines are reached by the `link` cases of `test_the_debt_script_reads_a_link_and_reports_a_missing_file` and `test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte` ([D14](design.md#d14)).
  `CARD` is removed.
  Verify: `git grep -l -e "debtfile.count" -- scripts/metrics/debt.py` prints `scripts/metrics/debt.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`.
- [ ] 4.7 In `tests/test_metric_pins.py` turn the slice W debt rows of [the turns](cases.md#the-turns) for phase 4 and no other assert; take the `- **` entries of `run.py` and `debt.py` out of `FORMAT_SITES` in `tests/test_structure.py`, add `debtfile.py` to `run.py`'s row of `docs/modules.md` and make `debt.py`'s row `debtfile.py, layout.py`.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 4.8 Import `prices` from `mflib` in `tests/test_review_metrics.py` and re-point the lines that call `_prices` at `prices.rows(review_metrics.PRICES)`, their asserts unchanged ([D11](design.md#d11)).
  Verify: `git grep -l -e "prices.rows" -- tests/test_review_metrics.py` prints `tests/test_review_metrics.py`; `uv run pytest tests/test_review_metrics.py -q` exits `0`.
- [ ] 4.9 **CORPUS** `review-metrics` In `scripts/metrics/run.py`'s `_priced` and in `skills/mf-review-metrics/scripts/review_metrics.py` take the price table from `prices.rows`, importing `mflib.prices` under the seed line ([D11](design.md#d11)); in `run.py` an `Unreadable` is the gap `prices: <reason>` and a model with no usable row the gap `no price for model <model>`, in `review_metrics.py` it escapes, and the lines are reached by `test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty` and the pipe case of `test_a_prices_file_that_is_a_fifo_blocks_both_scripts` ([D14](design.md#d14)).
  In `review_metrics.py` `_prices` is removed and its call sites call `mflib.prices.rows(PRICES)`.
  Verify: `git grep -l -e "prices.rows" -- scripts/metrics/run.py` prints `scripts/metrics/run.py`; `uv run pytest tests/test_metric_scripts.py tests/test_run_dir_finders.py -n auto -q` exits `0`; `uv run pytest tests/test_review_metrics.py -q` exits `0`.
- [ ] 4.10 In `tests/test_metric_pins.py` turn the slice W price rows of [the turns](cases.md#the-turns) for phase 4 and no other assert; add `prices.py` to the rows of `run.py` and `review_metrics.py` in `docs/modules.md`.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py tests/test_structure.py -n auto -q` exits `0`.
- [ ] 4.11 Each set holds after the phase ([D15](design.md#d15)).
  Verify: `git diff --stat HEAD -- tests/test_run_dir_finders.py` prints nothing; `uv run pytest tests/test_runlog.py tests/test_statuslog.py tests/test_findings.py tests/test_marks.py tests/test_debtfile.py tests/test_prices.py tests/test_eras.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py -n auto -q` exits `0`; `uv run pytest tests/test_review_metrics.py -q` exits `0`.

## 5 — The record

- [ ] 5.1 In `docs/recipes.md` make the reader recipe of *A state file* name `prices.rows` for the price table and `eras` for an old form, and say the metric scripts read each state file through the module that owns it ([D17](design.md#d17)).
  Verify: `git grep -l -e "prices.rows" -- docs/recipes.md` prints `docs/recipes.md`.
- [ ] 5.2 In `THREAT_MODEL.md` add `prices.py` and `eras.py` to the list of the shared home, and say `eras.py` reads and writes nothing and no station loads it ([D17](design.md#d17)).
  Verify: `git grep -l -e "prices.py" -- THREAT_MODEL.md` prints `THREAT_MODEL.md`; `git grep -l -e "eras.py" -- THREAT_MODEL.md` prints `THREAT_MODEL.md`.
- [ ] 5.3 In `docs/decisions.md` make D83's *Accepts* line say the readers of `review_metrics.py` alone still hold theirs ([D17](design.md#d17)).
  Verify: `git grep -l -F -e "alone still" -- docs/decisions.md` prints `docs/decisions.md`.
- [ ] 5.4 The metric scripts define no format name the home owns: `run.py` has no `STAMP =`, `EVENT =`, `MIDNIGHT =`, `PRIORITY =`, `CONFIRMED =`, `def _logs` and `def _events`, `debt.py` has no `CARD =` and no `read_text`, and `review_metrics.py` has no `def _prices` ([D6](design.md#d6) to [D11](design.md#d11)).
  Verify: `git grep -c -e "STAMP =" -e "EVENT =" -e "MIDNIGHT =" -e "PRIORITY =" -e "CONFIRMED =" -e "def _logs" -e "def _events" -- scripts/metrics/run.py` prints nothing; `git grep -c -e "CARD =" -e "read_text" -- scripts/metrics/debt.py` prints nothing; `git grep -c -e "def _prices" -- skills/mf-review-metrics/scripts/review_metrics.py` prints nothing.
- [ ] 5.5 No list entry of `tests/test_structure.py` is a tuple opening `"run.py",` and `"debt.py",`, and no station calls `eras.blocking` and `eras.refuted` ([D13](design.md#d13)).
  Verify: `git grep -c -F -e '"run.py",' -e '"debt.py",' -- tests/test_structure.py` prints nothing; `git grep -c -e "eras.blocking" -e "eras.refuted" -- skills/mf-ship skills/mf-converge skills/mf-build skills/mf-cut-change skills/mf-release skills/mf-integrate skills/mf-ui` prints nothing.
- [ ] 5.6 The new modules and tests are tracked.
  Verify: `git ls-files --error-unmatch skills/mflib/prices.py skills/mflib/eras.py tests/test_metric_pins.py tests/test_prices.py tests/test_eras.py` exits `0`.
- [ ] 5.7 The metric set, the viewer set and the review set of [D15](design.md#d15) pass.
  Verify: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py -n auto -q` exits `0`; `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`; `uv run pytest tests/test_review_metrics.py -q` exits `0`.
