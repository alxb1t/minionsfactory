# Test speed — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The fakes start bare
- [x] 2 — The deletions and the merge
- [x] 3 — The longest tests split
- [x] 4 — The rest split

## 1 — The fakes start bare

- [x] 1.1 Start the fake worker and the fake `ps` under `python -S`, and add `"-S"` to the argv assertion, in
  `tests/test_conduct.py`, per [D1](design.md#d1).
  Verify: `grep -n 'sys.executable, "-S"' tests/test_conduct.py` prints a line, `grep -n 'sys.executable} -S' tests/test_conduct.py`
  prints a line, and `uv run pytest -q tests/test_conduct.py -k "probe_halts_on_a_write_out or a_ready_version_ships_past_a_slow_one or worker_carries_the_allowlist"` reports `3 passed`.

## 2 — The deletions and the merge

- [x] 2.1 Delete the forged release's `move`, `delete`, `replace`, `graft`, `shallow` and hand-release cases, folding `delete` into
  the `("resume", *views)` case, and delete `test_a_good_read_keeps_the_offline_base`, in `tests/test_conduct.py`,
  per [D2](design.md#d2) and the design's `## Tests` table.
  Verify: `grep -L 'def test_a_good_read_keeps_the_offline_base' tests/test_conduct.py` prints `tests/test_conduct.py`, and
  `uv run pytest -q tests/test_conduct.py -k "forged_release_is_not_pushed or after_waits_for_its_dependency"` reports `2 passed`.
- [x] 2.2 Merge `test_a_version_cut_during_a_run_joins` into `test_a_new_executor_is_probed_mid_run`, its assertions moved per
  [D2](design.md#d2), in `tests/test_conduct.py`.
  Verify: `grep -L 'def test_a_version_cut_during_a_run_joins' tests/test_conduct.py` prints `tests/test_conduct.py`, and
  `uv run pytest -q tests/test_conduct.py -k new_executor_is_probed_mid_run` reports `1 passed`.
- [x] 2.3 Cut `tests/test_gate_check.py`'s topology grid to the six topologies with `unplanned` and the two plan variants on
  `parent-after-link`, and
  delete `test_mf_integrate_runs_its_script`, `test_the_release_gates_its_fold_fresh` and its helpers from `tests/test_skills.py`,
  per the design's `## Tests` table.
  Verify: `grep -L -e 'def test_mf_integrate_runs_its_script' -e 'def test_the_release_gates_its_fold_fresh' tests/test_skills.py`
  prints `tests/test_skills.py`, and `uv run pytest -q tests/test_gate_check.py -k include_changed_on_the_branch_halts` reports `1 passed`.

## 3 — The longest tests split

- [x] 3.1 Split `test_a_forged_release_is_not_pushed` into the tests [D3](design.md#d3) names, in `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "forged_release or pushed_release_retires or resumed_push_retires or person_landed_refuses or local_history_records"` reports `6 passed`.
- [x] 3.2 Split `test_after_waits_for_its_dependency` into the tests [D3](design.md#d3) names, in `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "after_waits_for_its_dependency or dependents_delta_halts or crashed_integrate_script or refuses_a_planted_hook or integrate_script_is_loaded_once or merges_in_before_its_first_worker or merged_in_once_merges_again or clean_merge_in_builds_on_the_merge or changelog_conflict_is_settled or conflict_halts_naming_the_merge or behind_an_unchanged_gate or ticked_version_goes_to_integrate or open_merge_with_no_note or open_merge_with_its_note or open_merge_is_merge_ins"` reports `15 passed`.
- [x] 3.3 Split `test_a_rerun_recovers_a_dead_release` and `test_a_halted_dependency_blocks_a_chain` into the tests
  [D3](design.md#d3) names, in `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "rerun_recovers_a_dead_release or release_cut_short_is_recovered or dead_integrate_is_resumed or halted_dependency_blocks_a_chain or lone_dependent_is_blocked or free_version_ships_past or waits_while_its_dependency_works or rejoined_dependency_brings"` reports `8 passed`.

## 4 — The rest split

- [x] 4.1 Split `test_no_worker_pushes` and `test_a_run_pushes_only_tagged_merges` into the tests [D3](design.md#d3) names, in
  `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "no_worker_pushes or repointing_origin_reaches or redirected_git_dir or inside_a_worktree_reads or kept_urls_stand or refused_home_folder or planted_promisor or plain_commit_on_main or tagged_side_merge or no_run_made_is_not or bare_version_tag or the_persons_to_push or stray_tag_on_a_run_release"` reports `13 passed`.
- [x] 4.2 Split `test_a_rerun_pushes_what_a_release_left`, `test_a_local_release_is_pushed_when_origin_returns` and
  `test_a_run_goes_on_while_origin_is_down` into the tests [D3](design.md#d3) names, in `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "rerun_pushes_what_a_release_left or planted_remote_key_refuses or key_set_after_the_refusal or scratch_stands_outside or local_origin_url_is_refused or tag_alone_starts_one_run or pushed_when_origin_returns or lands_before_origin_flaps or goes_on_while_origin_is_down or no_offline_base_halts or past_the_offline_base_halts"` reports `11 passed`.
- [x] 4.3 Measure each test's own cost: the suite run serially, without coverage, so the load of a version building beside it
  skews no test; no test's call over 20 s; a test over halts the build, naming it. The suite's wall time is the release's
  `gate-seconds`.
  Verify: `uv run pytest -q -p no:cacheprovider --durations=0 --durations-min=20` prints no `<secs>s call` line under its
  `slowest durations` header.
