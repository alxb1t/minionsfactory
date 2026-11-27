# Test speed — design

One default line in `pyproject.toml` and marks on the tests of this repository that run over 1 s. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The gate runs every test under coverage: `uv run coverage run -m pytest -q -n auto ...` at the root `Makefile`'s gate. `make check` runs `uv run pytest -q -n auto -m "not slow"` after every build phase. Both read `pyproject.toml`'s `[tool.pytest.ini_options]`, where `addopts` is `["--strict-markers", "--tb=short"]` and the one marker is `slow: over 5 s; ...`. `pytest-xdist` 3.8.0 is in `uv.lock`.

A scratch clone at the base, no ship run live, gave the measure. Each wall is the time of the command beside it, on ten workers.

| run | wall | command |
|---|---|---|
| the gate's tests as is, under coverage | 601 s | `uv run coverage run -m pytest -q -n auto --junitxml=a.xml` |
| the same with work stealing | 465 s, then 473 s | the same with `--dist worksteal` |
| `make check`'s tests as is | 115 s, then 94 s | `uv run pytest -q -n auto -m "not slow"` |
| `make check`'s tests with work stealing | 81 s | the same with `--dist worksteal` |
| the tests under 1 s | 49 s, then 35 s; 45 s with work stealing | `uv run pytest -q -n auto`, naming those tests |

`tests/test_conduct.py` is 73% of the summed seconds. A flow test is child processes, mostly `git` called by the conductor itself, not by the test kit.

## Goals / Non-Goals

- **Goal:** the gate's wall falls by scheduling, and `make check` falls to the tests under 1 s plus the whole-repo scanners.
- **Non-goal:** faster flow tests, a repository template, compile-once, fewer conductor `git` calls, a new package.
- **Non-goal:** any edit of the skills, the bootstrap template, the root `Makefile` or a `conftest.py`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `--dist=worksteal` goes in `addopts` of `pyproject.toml`; the root `Makefile` is not edited | the gate, `make check` and every run with `-n` take it; no gate-file approval; a run with no `-n` is as before | a `--dist` on each `Makefile` line: a gate-file edit |
| [D2](#d2) | In this repository `slow` means over 1 s | one marker, no hook, no package; T1's 5 s is a floor for every target, and this repository marks more | a second marker; a `conftest.py` hook |
| [D3](#d3) | The marks go on tests that exist; no test is added, deleted, merged or rewritten | the evidence's `slow` rows are the plan, not findings | marking while rewriting the long flow tests |
| [D4](#d4) | No timing is a check | a time read on a loaded machine halts a run for no fault | a gate step that reads the junit report |
| [D5](#d5) | No `Verify:` runs a whole slow file | `tests/test_conduct.py` alone is about 300 s | a `Verify:` of `tests/test_conduct.py`, `tests/test_release.py` or `tests/test_converge.py` |
| [D6](#d6) | Between phases a worker runs `make check`; every other test runs in the gate at the build's end | the gate still runs every test, so no proof is lost | `pytest-testmon`: its data is per worktree and it misses links through a subprocess |

### D1

`addopts` becomes `["--strict-markers", "--tb=short", "--dist=worksteal"]`. It covers each pytest run of this repository that carries `-n`: the gate's line, `make check`'s line, a `Verify:` with `-n`, and a run `plan_check.py` starts. It exempts a run with no `-n`, which runs in process as before, the bootstrap template and every target repo, and a `Verify:`'s own words: no `Verify:` here writes `--dist`.

`plan_check.py`'s `gate_discovers` reads `addopts` for `--ignore` and `--deselect` only, so the new flag changes nothing there. `gate_integrity.py` prints the `pyproject.toml` line for conformance to judge; it halts nothing, and the line is planned here.

### D2

A test function under `tests/` whose slowest case ran over 1 s in the measure's first run gains `@pytest.mark.slow`, on its own line directly above its `def`, below any other decorator. It exempts:

- the whole-repo scanners, which any phase can break: those of `tests/test_structure.py`, `tests/test_markdown_corpus.py` and `tests/test_ast_grep.py`. Each runs over 1 s and stays unmarked, so `make check` keeps it. Example: `test_check_cycles_holds_on_the_tree`, 1.68 s.
- a function already marked that runs under 1 s: it keeps its marker.
- T1's text and `SLOW_SECONDS = 5` in `scripts/metrics/codebase.py`: a target repo's test of 3 s needs no marker, and the metric still counts rows over 5 s.

The words follow: the marker's line in `pyproject.toml` reads `over 1 s`, and `AGENTS.md`'s line on `make check` says that here a test over 1 s is `slow`. No skill text changes.

### D3

`evidence.py` prints `slow · path:line` for each `pytest.mark.slow` line a patch adds. The lines of [the marks](#the-marks) are the plan, so conformance reads them as planned. D39's judgment of a new test's cost has nothing to judge: no test is new.

### D4

No `Verify:`, test or gate step of this version reads a duration. Each mark is held by a count of `^@pytest.mark.slow` lines per file, against [the marks](#the-marks)' table.

### D5

A file named without `-m` runs its slow tests too. The `Verify:` that proves the default parses names a small file: `uv run pytest tests/test_next_tag.py -q -n 2`. The gate holds the big files.

### D6

The build's `make check` after each phase now skips the tests the marks cover. A break in one shows at the gate that closes the build. The person accepted this at the plan.

## The marks

Each file gains the marks of the table's `added` column; its count of `^@pytest.mark.slow` lines after the change is `after`. A function below is listed once, is a module-level function of its file, and carries no `slow` marker at the base.

| file | marked now | added | after |
|---|---|---|---|
| `tests/test_release.py` | 0 | 74 | 74 |
| `tests/test_conduct.py` | 173 | 66 | 239 |
| `tests/test_converge.py` | 11 | 25 | 36 |
| `tests/test_mark_pins.py` | 2 | 23 | 25 |
| `tests/test_cut_check.py` | 0 | 18 | 18 |
| `tests/test_plan_check.py` | 4 | 13 | 17 |
| `tests/test_gate_run.py` | 1 | 10 | 11 |
| `tests/test_gate_check.py` | 3 | 8 | 11 |
| `tests/test_integrate.py` | 7 | 7 | 14 |
| `tests/test_viewer.py` | 7 | 7 | 14 |
| `tests/test_cut_context.py` | 0 | 6 | 6 |
| `tests/test_pin.py` | 0 | 6 | 6 |
| `tests/test_modelsfile.py` | 0 | 5 | 5 |
| `tests/test_queue_pins.py` | 1 | 5 | 6 |
| `tests/test_metric_scripts.py` | 1 | 4 | 5 |
| `tests/test_sandboxed.py` | 3 | 3 | 6 |
| `tests/test_brief_check.py` | 3 | 2 | 5 |
| `tests/test_next_tag.py` | 0 | 2 | 2 |
| `tests/test_awake.py` | 0 | 1 | 1 |
| `tests/test_corpus.py` | 0 | 1 | 1 |
| `tests/test_cut_pre.py` | 0 | 1 | 1 |
| `tests/test_facts.py` | 0 | 1 | 1 |
| `tests/test_metrics.py` | 1 | 1 | 2 |
| **all** | 217 | 289 | 506 |

The `marked now` column is `git grep -c -e "^@pytest.mark.slow" -- tests/<file>` at the base; the files not in it print nothing.

### tests/test_release.py

`test_a_hand_run_reads_origin_itself`, `test_a_release_commit_whose_parent_is_not_the_marks_head_halts`, `test_a_release_commit_with_a_code_path_halts`, `test_a_release_commit_without_the_mark_halts`, `test_a_release_origin_holds_is_not_dropped`, `test_a_release_the_default_branch_holds_is_not_dropped`, `test_a_run_pre_saves_a_persons_edit_and_untracked_file_before_it_restores`, `test_a_second_finish_after_a_death_at_each_step_ends_the_same`, `test_a_stranded_release_is_dropped`, `test_a_stranded_release_past_a_failed_bound_halts`, `test_a_tag_on_an_orphan_commit_is_moved`, `test_a_tag_origin_holds_halts`, `test_a_tag_the_default_branch_holds_halts`, `test_an_unreadable_origin_cannot_run`, `test_finish_archives_the_change_and_writes_its_version`, `test_finish_at_a_release_commit_halts_on_a_dirty_tree`, `test_finish_at_a_release_commit_runs_the_gate_before_tagging`, `test_finish_at_a_release_commit_tags_a_missing_tag`, `test_finish_bumps_a_version_file_with_no_lock`, `test_finish_bumps_package_json_and_its_lock`, `test_finish_bumps_the_version_file_and_its_lock`, `test_finish_cannot_run_on_a_linked_changelog`, `test_finish_cannot_run_when_a_file_cannot_be_written`, `test_finish_clears_the_paid_cards`, `test_finish_collects_the_metrics`, `test_finish_commits_once_and_tags`, `test_finish_copies_the_previous_gate_line`, `test_finish_cuts_the_changelog_heading`, `test_finish_halts_on_a_file_the_worker_broke`, `test_finish_halts_on_a_lock_of_another_shape`, `test_finish_halts_on_a_python_file`, `test_finish_halts_on_a_red_gate`, `test_finish_halts_on_a_stale_metrics_version`, `test_finish_halts_on_a_tree_dirty_after_the_commit`, `test_finish_halts_on_an_old_backlog_file`, `test_finish_halts_on_an_unstaged_change_after_the_gate`, `test_finish_halts_when_the_debt_cannot_be_cleared`, `test_finish_halts_when_uv_lock_fails`, `test_finish_halts_without_the_mark`, `test_finish_records_debt_none`, `test_finish_records_none_for_no_catalogue`, `test_finish_records_none_for_no_version_file`, `test_finish_reports_an_unknown_card`, `test_finish_states_a_skipped_converge_in_the_body`, `test_finish_stops_on_the_flag`, `test_finish_takes_the_workers_paths`, `test_finish_under_run_signs_nothing_and_runs_no_hook`, `test_finish_writes_ci_none_when_gh_fails`, `test_finish_writes_ci_not_read_under_a_run`, `test_finish_writes_the_gate_line`, `test_merge_halts_on_a_dirty_primary`, `test_merge_halts_on_a_primary_off_the_default_branch`, `test_merge_halts_on_an_untagged_branch`, `test_merge_halts_when_the_default_branch_moved`, `test_merge_halts_when_the_merged_tree_differs`, `test_merge_halts_while_the_flag_stands`, `test_merge_merges_with_its_trailer_and_the_trees_are_equal`, `test_merge_switches_a_primary_that_is_this_checkout`, `test_no_origin_is_free`, `test_pre_at_a_release_commit_restores_nothing`, `test_pre_cannot_run_when_a_script_or_file_fails`, `test_pre_cannot_run_when_the_mark_cannot_be_written`, `test_pre_halts_on_a_forged_release_commit`, `test_pre_halts_on_an_existing_tag`, `test_pre_halts_on_each_failed_precondition_of_the_findings`, `test_pre_halts_on_each_failed_precondition_of_the_tree`, `test_pre_names_a_patch_release_by_its_whole_version`, `test_pre_passes_an_after_id_archived_at_head`, `test_pre_passes_an_own_tag`, `test_pre_prints_the_tag_and_writes_the_mark`, `test_pre_reads_a_release_commit_as_a_resume`, `test_pre_reads_a_skipped_checker`, `test_pre_reads_a_skipped_converge`, `test_pre_restores_a_dead_releases_derived_work`

### tests/test_conduct.py

`test_a_build_halts_on_a_direct_npm_package_no_row_approves`, `test_a_build_runs_the_quick_plan_check_after_every_phase_but_the_last`, `test_a_claude_worker_starts_in_the_sandbox`, `test_a_codex_temp_folder_is_removed`, `test_a_cut_fetches_the_npm_rows_it_approves`, `test_a_cut_queues_its_models_file`, `test_a_cut_reservation_is_refused_at_a_link_at_minions`, `test_a_droppable_tip_reads_release`, `test_a_failed_environment_build_halts_the_run`, `test_a_grant_is_refused_at_a_link_at_minions`, `test_a_grant_is_refused_at_what_stands_at_its_name`, `test_a_limit_halts_only_the_stations_ahead`, `test_a_merge_in_refuses_a_planted_hook`, `test_a_merge_on_a_recorded_head_with_another_subject_is_not_pushed`, `test_a_missing_worktree_or_a_crash_ends_in_a_halt_line`, `test_a_plan_text_fix_commit_re_plans_a_stack`, `test_a_red_gate_after_simplify_drops_its_commit`, `test_a_red_gate_with_no_simplify_commit_fails_the_close`, `test_a_release_merge_that_adds_a_file_is_not_pushed`, `test_a_skip_is_read_once`, `test_a_start_on_linux_writes_the_marks_into_the_exclude`, `test_a_status_log_link_or_fifo_halts_the_stage_and_status`, `test_a_stuck_stage_halt_names_its_rescue_and_supervision`, `test_a_swapped_root_halts_a_codex_spawn`, `test_a_tip_no_tag_names_is_not_pushed`, `test_a_worker_carries_the_npm_settings`, `test_a_worker_halt_is_a_rerun_at_the_same_head`, `test_an_octopus_with_a_recorded_release_is_not_pushed`, `test_beside_waits_on_nothing`, `test_cap_close_starts_no_run_for_a_waiting_cut`, `test_cap_counts_only_versions_at_a_station`, `test_cap_file_that_is_bad_stops_the_run`, `test_cap_gates_the_poll_and_not_a_request`, `test_cap_status_and_cut_line`, `test_close_halts_on_a_plan_check_failure`, `test_close_on_a_green_gate_prints_the_gate_line`, `test_close_on_a_red_gate_writes_gate_red_and_build_halt`, `test_close_skips_metrics_with_no_catalogue`, `test_close_writes_build_done_with_head_and_simplify`, `test_cutcheck_cannot_run_halts`, `test_cutcheck_fails_once_then_passes`, `test_cutcheck_fails_twice_halts`, `test_cutcheck_never_resets_a_rejoin`, `test_cutcheck_passes`, `test_cutdeclared_command_passes`, `test_cutdeclared_none_runs_nothing`, `test_no_hook_runs_in_a_worker`, `test_pin_j_conduct_answered_needs_each_head`, `test_quick_built_fails_a_phase_whose_earlier_search_no_longer_holds`, `test_reach_stops_at_live_worktrees`, `test_report_with_tags_false_names_the_default_branch`, `test_report_with_tags_false_reads_not_pushed_for_a_tip_the_primary_lacks`, `test_status_names_an_old_layout`, `test_status_names_each_old_entry_alone`, `test_status_prints_a_tip_tagged_elsewhere_with_its_reason`, `test_stop_ends_a_live_run`, `test_the_conductor_merges_with_no_signing_key`, `test_the_config_guard_allows_gc_auto`, `test_the_probe_reports_its_first_turn`, `test_the_release_script_runs_boxed_with_run_and_origin`, `test_the_release_stand_in_makes_the_commit_tag_and_merge`, `test_the_remote_calls_carry_the_ssh_options`, `test_the_run_hands_converge_its_trees_and_sandbox`, `test_the_tags_origin_holds_are_made_locally`, `test_wait_halt_ends_at_a_final_halt`, `test_wait_reads_no_origin_at_a_poll`

### tests/test_converge.py

`test_a_claude_fixers_prompt_names_its_attribution`, `test_a_clean_file_still_mismatched_halts`, `test_a_clean_file_with_a_card_not_closed_gets_a_rewrite`, `test_a_file_with_no_count_keys_is_stamped`, `test_a_fix_commit_editing_a_decisions_body_is_taken`, `test_a_fix_commit_editing_the_decisions_table_halts`, `test_a_fix_note_alone_needs_no_trailer`, `test_a_granted_round_goes_one_past_the_cap`, `test_a_malformed_file_gets_a_rewrite_then_a_debt_card`, `test_a_miscounted_file_is_stamped_clean`, `test_a_pickup_check_is_stamped_and_keeps_its_round`, `test_a_red_gate_after_a_fix_gets_one_more_pass_then_the_cap`, `test_a_run_resumes_from_its_status_log`, `test_a_security_card_of_high_is_left_to_the_halt`, `test_a_skipped_checker_is_a_stub`, `test_a_timeout_alone_sends_nothing_back`, `test_a_trailer_naming_no_card_of_the_findings_is_refused`, `test_a_verify_round_is_stamped_with_the_fixs_head_and_the_round`, `test_a_verify_round_reads_a_plan_text_edit`, `test_an_accepted_blocker_converges_and_a_critical_one_blocks`, `test_changes_requested_with_no_card_gets_a_rewrite`, `test_converge_logs_each_gate_with_its_seconds`, `test_round_one_pickup_rides_with_the_fix`, `test_the_cap_halts_with_the_open_blockers`, `test_the_report_names_the_verdicts`

### tests/test_mark_pins.py

`test_case_a_a_red_gate_drops_the_simplify_commit_but_for_a_fault_not_its_own`, `test_case_d_a_side_merge_and_an_octopus_merge_refuse_the_built_head`, `test_case_d_the_built_head_refuses_what_it_does_not_hold`, `test_case_e_a_drop_with_no_flag_removes_the_mark`, `test_case_e_a_release_subject_with_more_after_it_is_no_release_commit`, `test_case_e_a_restore_of_a_clean_tree_saves_no_patch`, `test_case_e_finish_and_merge_halt_on_a_flag_of_any_shape`, `test_case_e_save_numbers_past_a_folder_and_keeps_a_binary_file`, `test_case_e_save_replaces_a_dangling_link`, `test_case_h_the_checks_and_held_name_the_sub_task`, `test_case_m_a_failed_write_stops_the_version_with_code_1`, `test_case_m_merge_in_writes_the_note_and_leaves_the_merge_open`, `test_case_m_the_note_stays_under_the_bound_its_reader_holds`, `test_case_m_the_settling_tests_stand_the_note_by_is_file`, `test_case_o_release_flag_stands_in_every_shape`, `test_case_t_opened_keeps_the_settled_time_and_settled_passes_a_new_one`, `test_case_x_the_amends_test_passes_amends_of_the_change_directory_alone`, `test_case_x_the_amends_test_resolves_the_head_it_names`, `test_loop_a_closed_build_is_not_closed_again`, `test_loop_an_open_build_is_closed_once`, `test_pin_head_forms_of_build_simplified`, `test_pin_head_forms_of_integrate_red`, `test_pin_stands_of_the_stop_marks_are_is_file`

### tests/test_cut_check.py

`test_a_change_with_no_delta_holds_skip_specs_and_a_keep_file`, `test_a_dependencies_table_is_read`, `test_a_ritual_is_each_station_the_build_owns`, `test_a_script_that_cannot_run_exits_2`, `test_each_mechanical_row_fails_by_name`, `test_first_word_of_the_tree_holds`, `test_first_word_on_path_holds`, `test_i4_names_each_defect_of_the_tasks_shape`, `test_k1_and_k2_read_each_side_of_the_record`, `test_k5_reads_the_step_and_the_constant_of_the_one_file`, `test_kexpr_naming_a_module_of_a_directory_holds`, `test_kexpr_naming_a_planned_test_holds`, `test_kexpr_naming_nothing_is_refused`, `test_person_phase_is_refused`, `test_removed_name_in_a_diff_block_is_refused`, `test_removed_name_in_design_is_refused`, `test_removed_name_with_a_removal_word_holds`, `test_the_folded_checks_report_their_failures`

### tests/test_plan_check.py

`test_a_collection_that_finds_no_test_is_a_line`, `test_a_command_starts_under_the_load_or_when_none_runs`, `test_a_failed_group_ends_the_check_before_the_next`, `test_a_quick_check_runs_no_pytest_and_no_make`, `test_a_timed_out_command_does_not_wait_on_an_escaped_childs_pipe`, `test_a_timed_out_command_loses_its_process_group`, `test_a_timed_out_line_of_the_quick_group_leaves_the_long_group_judged`, `test_a_timed_out_or_failed_collection_says_why`, `test_a_verify_timeout_line_sets_the_limit`, `test_a_waiting_command_rereads_the_load_each_second`, `test_a_wrapped_git_command_is_not_reused_once_a_branch_moves`, `test_commands_run_side_by_side_and_print_in_task_order`, `test_what_the_plan_check_cannot_read_exits_2`

### tests/test_gate_run.py

`test_a_gate_past_its_limit_is_red`, `test_a_gate_that_changes_what_it_ran_on_records_nothing`, `test_a_green_run_is_recorded_and_reused_on_the_same_tree`, `test_a_record_is_not_reused_across_inherited_make_overrides`, `test_a_red_run_records_nothing`, `test_fresh_runs_whatever_stands_and_records`, `test_records_go_under_the_primary_run_directory`, `test_reuse_is_refused_on_a_changed_dry_run`, `test_reuse_is_refused_on_a_dirty_tree`, `test_reuse_is_refused_on_another_tree`

### tests/test_gate_check.py

`test_a_bare_makefile_task_fails_the_plan_check`, `test_a_dry_run_failing_in_an_export_exits_2`, `test_a_halt_lists_every_unquoted_line`, `test_a_planned_dash_the_task_does_not_quote_halts`, `test_a_staged_tree_is_checked`, `test_exports_go_under_the_primary_run_directory`, `test_gate_check_halts_on_an_old_layout`, `test_gate_check_halts_on_each_old_entry_alone`

### tests/test_integrate.py

`test_a_hand_run_station_halts_on_an_old_layout`, `test_changelog_drops_a_stacked_bases_released_entries`, `test_decisions_halts_once_after_every_ambiguous_file`, `test_decisions_renumbers_a_colliding_decision_and_its_citations`, `test_decisions_skips_a_conflicted_file_and_goes_on`, `test_delta_reports_a_requirement_main_changed`, `test_pin_n_unready_reads_the_findings_files`

### tests/test_viewer.py

`test_a_project_read_past_its_bound_is_killed`, `test_a_stale_claim_shows_no_running_gate`, `test_a_version_shows_its_phases_with_the_trees_ticks`, `test_converge_shows_its_round_cap_blockers_and_each_role`, `test_the_fingerprint_changes_when_a_cut_is_queued`, `test_the_only_options_print_liveness_and_the_fingerprint`, `test_the_projector_writes_nothing`

### tests/test_cut_context.py

`test_a_fact_is_listed_with_its_state_and_lines`, `test_a_pack_that_cannot_be_written_exits_2`, `test_the_pack_and_the_notes_are_written_and_exit_by_the_facts`, `test_the_scaffold_refuses_a_file_that_exists`, `test_the_script_runs_as_a_program`, `test_the_tasks_scaffold_lists_each_phase`

### tests/test_pin.py

`test_a_bare_install_links_the_newest_tag_origin_holds`, `test_a_planted_replace_ref_does_not_reach_the_export`, `test_a_repo_planted_above_the_scratch_supplies_no_config`, `test_a_tag_or_live_holds_the_links`, `test_an_install_names_what_stops_it`, `test_the_quiet_move_follows_origin`

### tests/test_modelsfile.py

`test_a_build_model_that_is_no_token_halts_its_version`, `test_case_m_a_take_reads_every_planned_station_again`, `test_pin_text_that_is_not_toml`, `test_pin_the_queued_text_against_the_file`, `test_status_names_a_broken_models_file`

### tests/test_queue_pins.py

`test_a_failed_entry_write_in_cut_stops_it_and_removes_the_reservation`, `test_cut_refuses_an_after_that_names_no_open_version_or_queued_cut`, `test_cut_reserves_the_id_then_writes_its_entry_under_the_lock`, `test_next_id_is_one_above_every_number_the_repo_its_branches_and_the_queue_hold`, `test_wait_cut_writes_its_reason_last_under_the_lock_and_skips_what_it_must`

### tests/test_metric_scripts.py

`test_run_metrics_halt_on_each_old_entry_alone`, `test_run_metrics_read_the_run_logs`, `test_run_reads_a_log_with_the_new_fields`, `test_the_code_script_runs_as_the_collector_runs_it`

### tests/test_sandboxed.py

`test_a_child_that_leaves_the_group_holding_the_pipe_returns_after_the_deadline`, `test_a_host_socket_is_out_of_reach`, `test_a_network_connect_is_denied`

### tests/test_brief_check.py

`test_models_prints_the_items_toml`, `test_write_writes_the_items_models_file`

### tests/test_next_tag.py

`test_a_stray_local_tag_is_no_base`, `test_next_tag_follows_the_bump`

### The single marks

| file | function |
|---|---|
| `tests/test_awake.py` | `test_a_cut_holds_the_machine_awake_by_change_id` |
| `tests/test_corpus.py` | `test_the_corpus_runs_each_case` |
| `tests/test_cut_pre.py` | `test_every_precondition_holds_by_hand` |
| `tests/test_facts.py` | `test_what_cannot_be_read_exits_2` |
| `tests/test_metrics.py` | `test_a_failing_metric_is_unavailable_with_its_reason` |

## Tests

The change adds no test, deletes none and merges none, so the `I16` table is empty. It adds no end-to-end run. Each count below is the output of the command beside it.

| what | count | command |
|---|---|---|
| tests added, by layer | 0 | `git diff --stat <base>..HEAD -- tests` shows only `@pytest.mark.slow` lines |
| tests deleted or merged | 0 | the same diff holds no removed line |
| end-to-end runs added | 0 | none: no test is new |
| `slow` marks after, in one file | its `after` value in [the marks](#the-marks) | `grep -c -e "^@pytest.mark.slow" tests/<file>` |

The files that gain marks are `tests/test_release.py`, `tests/test_conduct.py`, `tests/test_converge.py`,
`tests/test_mark_pins.py`, `tests/test_cut_check.py`, `tests/test_plan_check.py`, `tests/test_gate_run.py`,
`tests/test_gate_check.py`, `tests/test_integrate.py`, `tests/test_viewer.py`, `tests/test_cut_context.py`,
`tests/test_pin.py`, `tests/test_modelsfile.py`, `tests/test_queue_pins.py`, `tests/test_metric_scripts.py`,
`tests/test_sandboxed.py`, `tests/test_brief_check.py`, `tests/test_next_tag.py`, `tests/test_awake.py`,
`tests/test_corpus.py`, `tests/test_cut_pre.py`, `tests/test_facts.py` and `tests/test_metrics.py`. Phase 1 runs
`tests/test_next_tag.py` unchanged, under `-n 2`.

`make check` after the change runs the tests under 1 s and the scanners, about 35 to 49 s in the measure's runs, and the gate runs every test.

## Dependencies

None.

## Risks / Trade-offs

- **A break in a slow test shows at the end gate.** `make check` no longer runs the marked tests between phases ([D6](#d6)). The person accepted it; the gate still runs every test.
- **A mark on a test that runs under 1 s on a quiet machine.** It costs `make check` one test of coverage between phases, and nothing in the gate.
- **A test that crosses 1 s later is unmarked.** T1 says 5 s for every target, so the rule is not held by a check ([D4](#d4)); a later version may add one.
- **`gate_integrity.py` prints the `addopts` line.** It halts nothing; [D1](#d1) plans it.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the default of [D1](#d1), then the marks and words of [D2](#d2). Each ends on a green `make check`; the build ends on a green gate.
