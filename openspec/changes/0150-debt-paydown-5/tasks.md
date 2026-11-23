# Debt paydown 5 — tasks

The phases run from the cut's rows to the texts. No task edits the debt file ([D15](design.md#d15)).

## Progress

- [x] 1 — The cut's rows · moderate
- [x] 2 — The conductor's small fixes · moderate
- [ ] 3 — The drain · hard
- [ ] 4 — Converge and the viewer · moderate
- [ ] 5 — The texts · moderate

## 1 — The cut's rows

- [x] 1.1 Make row `V2` silent on a negated word the name lacks, in `skills/mf-cut-change/scripts/cut_check.py`, per [D14](design.md#d14).
  Mend the docstring example of `selects`. Add `test_v2_is_silent_on_a_negated_word_the_name_lacks` to `tests/test_cut_check.py`; edit `test_v2_halts_only_on_a_selected_test` and `test_a_k_expression_selects_by_pytests_rules`, which the rule turns red.
  Verify: `uv run pytest -q tests/test_cut_check.py -k "test_v2_is_silent_on_a_negated_word_the_name_lacks or test_v2_halts_only_on_a_selected_test or test_a_k_expression_selects_by_pytests_rules"` exits 0.
- [x] 1.2 Add `_file_diffs` to `skills/mf-cut-change/scripts/cut_check.py` and make row `V6` read it, not `_diffs`, which row `K7` still reads, per [D14](design.md#d14).
  Add `test_v6_reads_the_searched_files_block_by_its_header` to `tests/test_cut_check.py`; give the diff blocks of `_later_task_diffs_a` a header pair naming `a.py`, which `test_each_mechanical_row_fails_by_name` and `test_a_needle_a_later_task_adds_back_passes_v6` run.
  Verify: `uv run pytest -q tests/test_cut_check.py -k "test_v6_reads_the_searched_files_block_by_its_header or test_each_mechanical_row_fails_by_name or test_a_needle_a_later_task_adds_back_passes_v6"` exits 0.

## 2 — The conductor's small fixes

- [x] 2.1 Keep the newline of a cut line in `_Tail.write` in `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Add `test_a_kept_line_cut_at_4000_characters_keeps_its_newline` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k test_a_kept_line_cut_at_4000_characters_keeps_its_newline` exits 0.
- [x] 2.2 Make `_cut_checked` in `skills/mf-ship/scripts/conduct.py` take the checker's exit 1 as a failed plan only when a line starts with `CUT_HALT`, per [D5](design.md#d5).
  Add `test_a_crash_that_quotes_the_halt_marker_mid_line_is_no_failed_plan` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k test_a_crash_that_quotes_the_halt_marker_mid_line_is_no_failed_plan` exits 0.
- [x] 2.3 Add `_operator_env()` to `skills/mf-ship/scripts/conduct.py`, and build the environments of `_sync_scripts` and `_prefetch` from it, per [D13](design.md#d13).
  Add `test_an_operators_uv_python_reaches_no_preparation_or_fetch` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k test_an_operators_uv_python_reaches_no_preparation_or_fetch` exits 0.
- [x] 2.4 Build the environment of `sandboxed()` from `_operator_env()` in `skills/mf-ship/scripts/conduct.py`, per [D13](design.md#d13).
  In `tests/test_sandboxed.py` set `UV_PYTHON` and `PIP_INDEX_URL` in `test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment` and assert neither reaches the command.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment` exits 0.
- [x] 2.5 Start each worker of `argv` in `skills/mf-ship/scripts/conduct.py` through `env -u` for every `UV_` and `PIP_` name the conductor holds, per [D13](design.md#d13).
  Add `test_an_operators_uv_python_reaches_no_worker` to `tests/test_conduct.py`, setting names in mixed order and asserting the sorted `-u` pairs; edit the tests there that read a worker command's prefix after `env -u VIRTUAL_ENV`, each clearing every `UV_` and `PIP_` variable first.
  Verify: `uv run pytest -q tests/test_conduct.py -k test_an_operators_uv_python_reaches_no_worker` exits 0.
- [x] 2.6 End an `OSError` of the log's write in the halt handler of `run()` and at both stops of `stop_run`, in `skills/mf-ship/scripts/conduct.py`, as a `Stop` of exit 2 naming the log, per [D13](design.md#d13).
  Add `test_a_run_log_removed_mid_run_ends_the_run_in_a_named_stop` to `tests/test_conduct.py`, and to `tests/test_runlog.py` `test_case_e_stop_run_names_a_log_it_cannot_write` and `test_case_e_stop_run_names_a_log_it_cannot_write_after_a_failed_clear`.
  Verify: `uv run pytest -q tests/test_conduct.py tests/test_runlog.py -k "test_a_run_log_removed_mid_run_ends_the_run_in_a_named_stop or test_case_e_stop_run_names_a_log_it_cannot_write"` exits 0.

## 3 — The drain

- [ ] 3.1 **HALT CHECK** `sandboxed()` in `skills/mf-ship/scripts/conduct.py` still reads its output in one loop over its pipe, the read this phase bounds.
  Verify: `grep -c "process.stdout or" skills/mf-ship/scripts/conduct.py` prints `1` and exits 0.
- [ ] 3.2 Bound the read of `sandboxed()` after its deadline, and close the pipe, in `skills/mf-ship/scripts/conduct.py`, per [D13](design.md#d13).
  Add `test_a_child_that_leaves_the_group_holding_the_pipe_returns_after_the_deadline` and `test_a_command_that_ends_in_time_is_read_whole` to `tests/test_sandboxed.py`; the first is red before the edit, the second a guard.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k "test_a_child_that_leaves_the_group_holding_the_pipe_returns_after_the_deadline or test_a_command_that_ends_in_time_is_read_whole"` exits 0.
- [ ] 3.3 Add `test_a_cuts_command_whose_child_holds_the_pipe_ends_at_the_deadline` and `test_a_cards_check_whose_child_holds_the_pipe_ends_at_the_deadline` to `tests/test_conduct.py`, through `_boxed` and `Run.sandboxed`; both are guards of the bound 3.2 gives.
  Verify: `uv run pytest -q tests/test_conduct.py -k "test_a_cuts_command_whose_child_holds_the_pipe_ends_at_the_deadline or test_a_cards_check_whose_child_holds_the_pipe_ends_at_the_deadline"` exits 0.

## 4 — Converge and the viewer

- [ ] 4.1 Make `plan_text` in `skills/mf-converge/scripts/converge.py` refuse a `Plan-text:` trailer that names no card of the findings files, per [D13](design.md#d13).
  Add `test_a_trailer_naming_no_card_of_the_findings_is_refused` and `test_a_trailer_with_prose_beside_a_card_id_passes` to `tests/test_converge.py`; seed a card `R1` in `test_a_fix_commit_may_edit_the_delta_with_the_trailer` and `test_a_fix_commit_editing_a_decisions_body_is_taken`.
  Verify: `uv run pytest -q tests/test_converge.py -k "test_a_trailer_naming_no_card_of_the_findings_is_refused or test_a_trailer_with_prose_beside_a_card_id_passes or test_a_fix_commit_may_edit_the_delta_with_the_trailer or test_a_fix_commit_editing_a_decisions_body_is_taken"` exits 0.
- [ ] 4.2 Say in `skills/mf-converge/references/fix.md` that the `Plan-text:` trailer names a card of the findings, and that `none` and a `misnamed` id are refused.
  Verify: `grep -n misnamed skills/mf-converge/references/fix.md` prints the line.
- [ ] 4.3 Make `start` in `skills/mf-ui/scripts/viewer.py` forget the record of a child that exited only while the pid file holds that child's pid, per [D13](design.md#d13).
  Add `test_a_start_that_loses_the_bind_leaves_the_winners_files` to `tests/test_viewer.py`.
  Verify: `uv run pytest -q tests/test_viewer.py -k test_a_start_that_loses_the_bind_leaves_the_winners_files` exits 0.

## 5 — The texts

- [ ] 5.1 Make the `<path>: the supervisor` row of Step 4's commit table in `skills/mf-integrate/SKILL.md` name each path the index changed, per [D6](design.md#d6).
  Verify: `grep -n "index changed" skills/mf-integrate/SKILL.md` prints the row.
- [ ] 5.2 Name the share's limit in the *Accepts* line of D76 in `docs/decisions.md`, as `account-wide`, per [D8](design.md#d8).
  Verify: `grep -c account-wide docs/decisions.md` prints `1`.
- [ ] 5.3 Retitle the metrics `codex-window-5h` and `codex-window-week` in `metrics/catalogue.toml` with `, account-wide`, per [D8](design.md#d8).
  Verify: `grep -c account-wide metrics/catalogue.toml` prints `2`.
