# Release script — tasks

The phases build `release.py`: `pre`, `finish`, a release run again, `merge` with the conductor, then the skill and the record. Each decision is in [design](design.md).

## Progress

- [ ] 1 — release.py pre · moderate
- [ ] 2 — release.py finish · hard
- [ ] 3 — a release run again · hard
- [ ] 4 — release.py merge and the conductor · hard
- [ ] 5 — the skill and the record · moderate

## 1 — release.py pre

- [ ] 1.1 **HALT CHECK** The premise of [D1](design.md#d1): the tag `release.py` prints comes from the tags merged into the default branch.
  Verify: `git grep -q -F -e '--merged' -- skills/mf-release/scripts/next_tag.py` exits `0`.
- [ ] 1.2 Add the corpus case `release-findings` to `scripts/corpus.toml`: `each` the `conformance.md` and `adversarial.md` of every change, `argv` `release.py findings {input}`, per [D14](design.md#d14).
  Verify: `grep -n -F -e 'release-findings' scripts/corpus.toml` prints the case's name line.
- [ ] 1.3 Create `skills/mf-release/scripts/release.py` with its `uv` header, `Stop`, a `main(argv)` that parses the subcommands the phases add, a git helper that adds the options of [D7](design.md#d7) under `--run`, and `findings <file>` per [D2](design.md#d2) and [D14](design.md#d14). Create `tests/test_release.py` with a `repo` fixture (a temporary git repository on `main` holding a version branch, a change folder and a `CHANGELOG.md`) and the tests `test_findings_prints_a_files_verdict`, `test_main_exits_0_1_and_2_by_line` and `test_the_git_helper_adds_the_run_options`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_findings_prints_a_files_verdict or test_main_exits_0_1_and_2_by_line or test_the_git_helper_adds_the_run_options"` exits `0`.
- [ ] 1.4 Add `pre` to `release.py` with its first checks, one line each, in the order of [D2](design.md#d2): the old layout, then under `--run` the restore of [D8](design.md#d8) (a dirty tree whose paths are all in the derived set goes back to `HEAD`, a stale `release.flag` and `release.pre` removed), then the tree clean. Tests: `test_pre_halts_on_an_old_layout`, `test_pre_restores_a_dead_releases_derived_work`, `test_pre_restore_removes_a_stale_flag_and_an_untracked_spec`, `test_a_hand_pre_keeps_the_clean_tree_halt`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_halts_on_an_old_layout or test_pre_restores_a_dead_releases_derived_work or test_pre_restore_removes_a_stale_flag_and_an_untracked_spec or test_a_hand_pre_keeps_the_clean_tree_halt"` exits `0`.
- [ ] 1.5 Add to `pre` the checks that read the run directory, one line each: the gate green through `gate_run.py` with its seconds, conformance and adversarial clean, converge ran or skipped, `HEAD` equal to each findings file's `head:`. Tests: `test_pre_halts_on_each_failed_precondition_of_the_findings`, `test_pre_reads_a_skipped_converge`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_halts_on_each_failed_precondition_of_the_findings or test_pre_reads_a_skipped_converge"` exits `0`.
- [ ] 1.6 Add the tag to `pre`: read `bump:` from `proposal.md` (any value but `minor` and `patch` halts), run `next_tag.py`, halt on a tag that already exists, write `release.pre` with `tag:`, `version:`, `gate:` and `head:` ([D4](design.md#d4)), print `release: tag — <tag>`. Tests: `test_pre_prints_the_tag_and_writes_the_mark`, `test_pre_halts_on_a_bad_bump`, `test_pre_halts_on_an_existing_tag`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_prints_the_tag_and_writes_the_mark or test_pre_halts_on_a_bad_bump or test_pre_halts_on_an_existing_tag"` exits `0`.
- [ ] 1.7 Add the remaining checks to `pre`, one line each: `## [Unreleased]` holding entries, `gate_check.py --change --base` exiting 0, the default branch an ancestor of `HEAD` (halt naming `/mf-integrate`), each `after:` id archived at `HEAD`. Test: `test_pre_halts_on_each_failed_precondition_of_the_tree`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_halts_on_each_failed_precondition_of_the_tree"` exits `0`.
- [ ] 1.8 Add the row of `release.py` to `docs/modules.md`: layer `station`, the base names its string constants end in and its imports load, in order.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 2 — release.py finish

- [ ] 2.1 Add `finish` to `release.py`: it reads `release.pre` (missing, or its `head:` stale, halts) and takes the worker's paths, those under `openspec/specs/` and the Markdown files; any other path halts naming it ([D5](design.md#d5)). Tests: `test_finish_takes_the_workers_paths`, `test_finish_halts_on_a_python_file`, `test_finish_halts_without_the_mark`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_takes_the_workers_paths or test_finish_halts_on_a_python_file or test_finish_halts_without_the_mark"` exits `0`.
- [ ] 2.2 In `finish`, write `version: <version>` below `bump:` in `proposal.md`, then move `openspec/changes/<change-id>/` to `openspec/changes/archive/<change-id>/` with `git mv`. Test: `test_finish_archives_the_change_and_writes_its_version`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_archives_the_change_and_writes_its_version"` exits `0`.
- [ ] 2.3 In `finish`, rename `## [Unreleased]` in `CHANGELOG.md` to `## [<tag without v>] - <today>` and seed an empty `## [Unreleased]` above it. Test: `test_finish_cuts_the_changelog_heading`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_cuts_the_changelog_heading"` exits `0`.
- [ ] 2.4 In `finish`, write the `Gate:` line under the renamed heading in the form of [D7](design.md#d7): the mark's gate time, the CI time, the previous version's times. Tests: `test_finish_writes_the_gate_line`, `test_finish_writes_ci_none_when_gh_fails`, `test_finish_writes_ci_not_read_under_a_run`, `test_finish_copies_the_previous_gate_line`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_writes_the_gate_line or test_finish_writes_ci_none_when_gh_fails or test_finish_writes_ci_not_read_under_a_run or test_finish_copies_the_previous_gate_line"` exits `0`.
- [ ] 2.5 In `finish`, bump `pyproject.toml`'s `version` to the tag without `v` and run `uv lock --offline`, per [D6](design.md#d6); the test project holds no dependency, so the lock resolves offline, and a failing `uv lock` halts naming its last line. Tests: `test_finish_bumps_the_version_file_and_its_lock`, `test_finish_halts_when_uv_lock_fails`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_bumps_the_version_file_and_its_lock or test_finish_halts_when_uv_lock_fails"` exits `0`.
- [ ] 2.6 In `finish`, bump `package.json` and `package-lock.json` by the edit of [D6](design.md#d6), halt on a lock of the shapes [D6](design.md#d6) names, and record `version file: none` in a repository with neither file. Tests: `test_finish_bumps_package_json_and_its_lock`, `test_finish_records_none_for_no_version_file`, `test_finish_halts_on_a_lock_of_another_shape`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_bumps_package_json_and_its_lock or test_finish_records_none_for_no_version_file or test_finish_halts_on_a_lock_of_another_shape"` exits `0`.
- [ ] 2.7 In `finish`, collect the metrics with `metrics.py collect --change --base --out metrics/changes/<change-id>.json --value gate-seconds=<the mark's gate> --model unidentified`; no `metrics/catalogue.toml` records `metrics: none — no catalogue`; a data file whose `version` is not the release's halts. Tests: `test_finish_collects_the_metrics`, `test_finish_records_none_for_no_catalogue`, `test_finish_halts_on_a_stale_metrics_version`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_collects_the_metrics or test_finish_records_none_for_no_catalogue or test_finish_halts_on_a_stale_metrics_version"` exits `0`.
- [ ] 2.8 In `finish`, stage the worker's paths and its own writes by name, run `gate_run.py --fresh`, then halt naming any unstaged change and any untracked file ([D7](design.md#d7)); a red gate halts with nothing committed. Tests: `test_finish_halts_on_a_red_gate`, `test_finish_halts_on_an_unstaged_change_after_the_gate`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_halts_on_a_red_gate or test_finish_halts_on_an_unstaged_change_after_the_gate"` exits `0`.
- [ ] 2.9 In `finish`, make the one commit `chore(release): <tag>` with the skip lines in its body and `Change: <change-id>` alone as trailer, check `git status --porcelain` prints nothing, then make the annotated local tag; under `--run` every git call carries the options of [D7](design.md#d7). Tests: `test_finish_commits_once_and_tags`, `test_finish_states_a_skipped_converge_in_the_body`, `test_finish_under_run_signs_nothing_and_runs_no_hook`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_commits_once_and_tags or test_finish_states_a_skipped_converge_in_the_body or test_finish_under_run_signs_nothing_and_runs_no_hook"` exits `0`.
- [ ] 2.10 In `finish`, clear the paid cards named by `debt:` (else `backlog:`) in the archived proposal through `mflib.debtfile`'s `lock`, `clear` and `write`; an id not found is reported, neither key records `debt: none`, an old `.minions/backlog.md` halts naming it. Tests: `test_finish_clears_the_paid_cards`, `test_finish_reports_an_unknown_card`, `test_finish_records_debt_none`, `test_finish_halts_on_an_old_backlog_file`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_clears_the_paid_cards or test_finish_reports_an_unknown_card or test_finish_records_debt_none or test_finish_halts_on_an_old_backlog_file"` exits `0`.
- [ ] 2.11 In `finish`, halt after the tag and the debt while `release.flag` stands, naming the file ([D4](design.md#d4)). Test: `test_finish_stops_on_the_flag`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_finish_stops_on_the_flag"` exits `0`.
- [ ] 2.12 Update the row of `release.py` in `docs/modules.md` to the base names its string constants now end in and its imports load.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 3 — a release run again

- [ ] 3.1 **HALT CHECK** The premise of [D8](design.md#d8): `finish` exists to resume.
  Verify: `git grep -q -F -e 'def finish' -- skills/mf-release/scripts/release.py` exits `0`.
- [ ] 3.2 Add `--origin held` and `--origin free` to `pre` and `finish`; without it the script reads `git ls-remote --tags origin <tag>` and `refs/remotes/origin/<default>` itself, and no `origin` is `free`; an `origin` it cannot read exits 2 ([D3](design.md#d3)). Tests: `test_a_hand_run_reads_origin_itself`, `test_an_unreadable_origin_cannot_run`, `test_no_origin_is_free`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_a_hand_run_reads_origin_itself or test_an_unreadable_origin_cannot_run or test_no_origin_is_free"` exits `0`.
- [ ] 3.3 Make `finish` resume from git per [D8](design.md#d8): at a release commit it skips every step before the tag, runs `gate_run.py` on the tree, tags a missing tag, clears the debt again and reads the flag; a commit without `release.pre`, one whose parent is not the mark's `head:` and one with a path outside the derived set halt naming it, through the function `pre` shares. Tests: `test_a_second_finish_after_a_death_at_each_step_ends_the_same`, `test_finish_at_a_release_commit_tags_a_missing_tag`, `test_finish_at_a_release_commit_runs_the_gate_before_tagging`, `test_a_release_commit_with_a_code_path_halts`, `test_a_release_commit_whose_parent_is_not_the_marks_head_halts`, `test_a_release_commit_without_the_mark_halts`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_a_second_finish_after_a_death_at_each_step_ends_the_same or test_finish_at_a_release_commit_tags_a_missing_tag or test_finish_at_a_release_commit_runs_the_gate_before_tagging or test_a_release_commit_with_a_code_path_halts or test_a_release_commit_whose_parent_is_not_the_marks_head_halts or test_a_release_commit_without_the_mark_halts"` exits `0`.
- [ ] 3.4 Under the bound of [D9](design.md#d9) make `pre` pass a tag of this release that is own, and `finish` move it to the release commit; a tag the default branch holds and a tag `origin` holds each halt naming which. Tests: `test_pre_passes_an_own_tag`, `test_a_tag_on_an_orphan_commit_is_moved`, `test_a_tag_origin_holds_halts`, `test_a_tag_the_default_branch_holds_halts`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_passes_an_own_tag or test_a_tag_on_an_orphan_commit_is_moved or test_a_tag_origin_holds_halts or test_a_tag_the_default_branch_holds_halts"` exits `0`.
- [ ] 3.5 Make `pre` undo a stranded release under the bound of [D10](design.md#d10), before its restore and in the order of [D2](design.md#d2), printing `release: drop — <tag> and its commit` and exiting 0. Tests: `test_a_stranded_release_is_dropped`, `test_a_release_the_default_branch_holds_is_not_dropped`, `test_a_release_origin_holds_is_not_dropped`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_a_stranded_release_is_dropped or test_a_release_the_default_branch_holds_is_not_dropped or test_a_release_origin_holds_is_not_dropped"` exits `0`.
- [ ] 3.6 Make `pre` at a release commit with a clean tree print `release: resume — <tag>` after the shared validity check and the findings check at `HEAD~1`, and none of the fold's checks, before its restore ([D8](design.md#d8)). Tests: `test_pre_reads_a_release_commit_as_a_resume`, `test_pre_halts_on_a_forged_release_commit`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_pre_reads_a_release_commit_as_a_resume or test_pre_halts_on_a_forged_release_commit"` exits `0`.
- [ ] 3.7 Update the row of `release.py` in `docs/modules.md` to the base names its string constants now end in and its imports load.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 4 — release.py merge and the conductor

- [ ] 4.1 Add `merge` to `release.py` per [D11](design.md#d11): `HEAD` the tagged release commit, the flag absent, the default branch an ancestor of `HEAD`, the primary clean, `--no-ff` with `Change:` alone as trailer, the trees equal. Tests: `test_merge_merges_with_its_trailer_and_the_trees_are_equal`, `test_merge_halts_on_an_untagged_branch`, `test_merge_halts_when_the_default_branch_moved`, `test_merge_halts_on_a_dirty_primary`, `test_merge_halts_while_the_flag_stands`, `test_merge_switches_a_primary_that_is_this_checkout`.
  Verify: `uv run pytest tests/test_release.py -q -k "test_merge_merges_with_its_trailer_and_the_trees_are_equal or test_merge_halts_on_an_untagged_branch or test_merge_halts_when_the_default_branch_moved or test_merge_halts_on_a_dirty_primary or test_merge_halts_while_the_flag_stands or test_merge_switches_a_primary_that_is_this_checkout"` exits `0`.
- [ ] 4.2 In `skills/mf-ship/scripts/conduct.py` add the constant `RELEASE` for `release.py`'s path, and a function that runs one subcommand under `_boxed` with `--run` and `--origin` read through the kept URLs, logs it as a `release · script` spawn and a finish with its exit, and returns its exit and its line ([D3](design.md#d3), [D12](design.md#d12)). In `skills/mflib/runlog.py` make `release_died` read those lines as [D12](design.md#d12) says. Tests: `test_the_release_script_runs_boxed_with_run_and_origin`, `test_a_script_run_is_logged_as_a_release_spawn_and_finish`, `test_release_died_reads_the_scripts_lines`.
  Verify: `uv run pytest tests/test_conduct.py tests/test_runlog.py -q -k "test_the_release_script_runs_boxed_with_run_and_origin or test_a_script_run_is_logged_as_a_release_spawn_and_finish or test_release_died_reads_the_scripts_lines"` exits `0`.
- [ ] 4.3 Create `tests/fake_release.py`, a stand-in for `release.py` with `pre`, `finish` and `merge` that makes the commit, the tag and the merge the fake worker made, with the modes `dies-release-fold`, `dies-release-commit`, `dies-release-tag` and `stops-release-tag` copied from `tests/fake_worker.py`. Make `_conduct()` of `tests/test_conduct.py` point `RELEASE` at it. Test: `test_the_release_stand_in_makes_the_commit_tag_and_merge`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_the_release_stand_in_makes_the_commit_tag_and_merge"` exits `0`.
- [ ] 4.4 In the release stage of `advance` run `pre`, the worker, the guards of [D12](design.md#d12), `finish` and `merge` in that order; a script's exit 1 is the version's halt with its line as the reason, exit 2 a halt `release cannot run`, a `drop` line reads the stage again and `resume` starts no worker; the same holds for `finish` and `merge`. Make the release branch of `tests/fake_worker.py` fold alone and delete its modes the stand-in now holds, keeping its `plant-*` modes, which plant after the fold. Tests: `test_a_script_halt_is_the_versions_halt`, `test_a_script_that_cannot_run_halts_the_version`, `test_a_drop_line_reads_the_stage_again`, `test_a_resume_starts_no_worker`, `test_a_key_planted_by_the_release_worker_halts_before_finish`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_script_halt_is_the_versions_halt or test_a_script_that_cannot_run_halts_the_version or test_a_drop_line_reads_the_stage_again or test_a_resume_starts_no_worker or test_a_key_planted_by_the_release_worker_halts_before_finish"` exits `0`.
- [ ] 4.5 In `_release_tip` read a stranded release that `pre` can undo as stage `release`, a tip whose `release.flag` stands as `released` naming the file, and the rest of the moved-branch cases as `released` with the reason they have ([D10](design.md#d10)). Tests: `test_a_droppable_tip_reads_release`, `test_a_flagged_tip_reads_released`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_droppable_tip_reads_release or test_a_flagged_tip_reads_released"` exits `0`.
- [ ] 4.6 Rewrite `test_a_rerun_recovers_a_dead_release` and `test_a_release_cut_short_is_recovered` of `tests/test_conduct.py` to the stand-in's deaths and the undoing of a stranded release, keeping their names ([D8](design.md#d8), [D10](design.md#d10)), and adjust `test_a_changed_git_config_halts_a_merge_in` and `test_a_worker_repointing_origin_reaches_nothing` to the guard that now runs before `finish`. The flow tests `test_a_ready_version_ships_past_a_slow_one`, `test_no_worker_pushes` and `test_a_rerun_pushes_what_a_release_left` keep passing.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_rerun_recovers_a_dead_release or test_a_release_cut_short_is_recovered or test_a_changed_git_config_halts_a_merge_in or test_a_worker_repointing_origin_reaches_nothing or test_a_ready_version_ships_past_a_slow_one or test_no_worker_pushes or test_a_rerun_pushes_what_a_release_left"` exits `0`.
- [ ] 4.7 Update `docs/modules.md`: the row of `release.py` and the `names` cell of `conduct.py`, which now holds `release.py`.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 5 — the skill and the record

- [ ] 5.1 In `skills/mf-release/SKILL.md` replace Step 1's preconditions and *A resumed release* with `scripts/release.py pre`, naming its lines, its `resume` and `drop` and its `--run`.
  Verify: `git grep -c -F -e 'scripts/release.py' -- skills/mf-release/SKILL.md` prints a count.
- [ ] 5.2 In `skills/mf-release/SKILL.md` keep Step 2's fold, the preamble and the prose that states the version, add that a flag is written to `.minions/changes/<change-id>/release.flag`, and say that under `merge=yes` the worker stops there.
  Verify: `git grep -c -F -e 'release.flag' -- skills/mf-release/SKILL.md` prints a count.
- [ ] 5.3 In `skills/mf-release/SKILL.md` replace Steps 3 and 4 with `release.py finish` and Step 5's merge with `release.py merge`, keeping the ask, the attended push and the worktree's removal; no `git tag -a` stays.
  Verify: `git grep -c -F -e 'git tag -a' -- skills/mf-release/SKILL.md` prints nothing.
- [ ] 5.4 In `tests/test_skills.py` replace the `mf-release` rows of `_METRICS_SCRIPTS` that name the scripts `release.py` now runs with the row `("mf-release", "scripts/release.py")`, and edit the expected lists of the tests that print those rows.
  Verify: `uv run pytest tests/test_skills.py -q` exits `0`.
- [ ] 5.5 In `docs/decisions.md` reword D17 so the commit, the tag and the merge are `release.py`'s under a run, unsigned, D19 so `release.py pre` computes the tag, and D21 so a commit a script makes carries `Change:` alone, and add `release.flag` and `release.pre` to the marks of D57.
  Verify: `git grep -n -F -e 'release.flag' -- docs/decisions.md` prints the line of D57.
