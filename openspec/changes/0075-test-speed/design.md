# Test speed — design

The fakes start bare, the tests that repeat another's assertions go, and the multi-case tests split, so the gate's test step is
bound by the cores. Verdict at the end: ready to build.

## Context

Read at `6647909` (v0.61.0); the test files moved since the brief's `1df4e7a`, so every fact was re-read. `C` is
`tests/test_conduct.py`.

- **F1. The run:** 164 tests. `uv run coverage run -m pytest -q -n auto`, as the gate: 124.5 s wall, 569 CPU-s; without coverage
  115.2 s (a `/tmp` export, 10 cores). The slowest, under coverage: `test_a_forged_release_is_not_pushed` (`C:2918`) 91.9 s ·
  `test_after_waits_for_its_dependency` (`C:778`) 73.4 · `test_a_rerun_recovers_a_dead_release` (`C:2264`) 44.5 ·
  `test_a_run_pushes_only_tagged_merges` (`C:2652`) 29.8 · `test_a_local_release_is_pushed_when_origin_returns` (`C:3555`) 24.9 ·
  `test_an_include_changed_on_the_branch_halts` (`tests/test_gate_check.py:96`) 22.8 · `test_a_run_goes_on_while_origin_is_down`
  (`C:3472`) 21.7 · `test_a_halted_dependency_blocks_a_chain` (`C:1103`) 21.2 · `test_no_worker_pushes` (`C:3150`) 20.9 ·
  `test_a_rerun_pushes_what_a_release_left` (`C:2442`) 20.3.
- **F2. Coverage in the fakes:** `[tool.coverage.run] patch = ["subprocess"]` (`pyproject.toml:24-27`) sets
  `COVERAGE_PROCESS_CONFIG`; the wheel's `a1_coverage.pth` starts coverage in any child that runs `site`. The fake worker is
  `MF_SHIP_AGENT = shlex.join([sys.executable, str(_WORKER)])` (`C:168`); the fake `ps` is a `#!{sys.executable}` script
  (`C:118`). `tests/fake_worker.py` imports the standard library alone; a `python -S` child loads no coverage, and its own children
  — `integrate.py replay` (`tests/fake_worker.py:126-127`) — still inherit the variable. The one assertion on the worker's argv is
  `C:5338-5342`.
- **F3. The forged release's cases:** `push()` closes the releases after the heads push (`skills/mf-ship/scripts/conduct.py:3310`),
  before a tag push, and the mutation hooks fire after a tag push (`C:2998-3013`), so `_ledger_heads` is empty when `move`,
  `delete`, `replace`, `graft` and `shallow` fire; `("resume", *views)` (`C:2969`) keeps the views. The hand-release case
  (`C:2944-2948`) is `test_a_run_pushes_only_tagged_merges`' `C:2718-2722` with its `status` check.
- **F4. The split targets:** each is `slow`; their independent cases and the state they share are named in [D3](#d3).

## Goals / Non-Goals

**Goals:** the test step under 70 s on 10 cores; no test over 20 s; every assertion and spec title kept.

**Non-Goals:** the conductor's own git cost; product code.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The fake worker and the fake `ps` run under `python -S` | Q3 | `env -u` in `MF_SHIP_AGENT`, which drops `integrate.py replay`'s coverage |
| [D2](#d2) | The deletions and the merge, each in the `## Tests` table | Q8, `0062·R6`, `0063·R8` | the low-confidence set |
| [D3](#d3) | One test per independent case or primary; chained steps stay together | Q2, Q6 | a session template repo |

### D1

`C:168` reads `shlex.join([sys.executable, "-S", str(_WORKER)])`; the fake `ps` shebang `#!{sys.executable} -S`; `C:5338-5342`'s
argv gains `"-S"`.

### D2

The table under `## Tests` is the list; a merged test's assertions move whole into the test that carries it.
`test_a_version_cut_during_a_run_joins`' assertions — the `rejoin — 0002-marks: build` line, the planted folder the poll skips, a
stale `all` request cleared at the next start, a linked rejoin folder — move into `test_a_new_executor_is_probed_mid_run`. The
forged release's remaining cases keep fewer than twenty tags, so `C:3060`'s `v9.20` stays clear.

### D3

Split as follows, each new test carrying `slow`, its setup through the file's helpers (`_primary`, `_version`, `_released`,
`_with_origin`); a step that reads an earlier step's state stays in that step's test, or seeds its state itself.

| test today | after |
|---|---|
| `test_a_forged_release_is_not_pushed` | itself (the prelude: the moved remote ref, `C:2950-2954`), `test_a_pushed_release_retires_its_head`, `test_a_resumed_push_retires_at_the_next_read`, `test_a_release_a_person_landed_refuses_a_forged_one`, `test_local_history_records_no_forged_release` (seeding a landed release merge), `test_a_forged_release_on_an_older_default_is_not_pushed` (`C:3096-3146`: the older default, and origin's HEAD leaving the kept name, which reads its pushed `maintenance`) |
| `test_after_waits_for_its_dependency` | itself (the hook on no integrate merge), `test_a_dependents_delta_halts_as_integrating`, `test_a_crashed_integrate_script_halts_and_a_rerun_merges`, `test_a_merge_in_refuses_a_planted_hook`, `test_the_integrate_script_is_loaded_once`, `test_a_cut_only_version_merges_in_before_its_first_worker`, `test_a_cut_only_version_merged_in_once_merges_again`, `test_a_clean_merge_in_builds_on_the_merge` (the `gated` case, kept: the one clean merge before a build), `test_a_changelog_conflict_is_settled_by_rule`, `test_a_merge_in_conflict_halts_naming_the_merge`, `test_a_started_version_behind_an_unchanged_gate_builds`, `test_a_ticked_version_goes_to_integrate`, `test_an_open_merge_with_no_note_halts`, `test_an_open_merge_with_its_note_halts_as_integrating`, `test_a_started_dependents_open_merge_is_merge_ins`; `behind` becomes a module helper `_behind`, the `INTEGRATE` swap a `monkeypatch.setitem` |
| `test_a_rerun_recovers_a_dead_release` | itself (fold, then tag and held), `test_a_release_cut_short_is_recovered` (the `0003` moved-main case as its prelude, then the `0004` dies-at-the-commit, `0005` stops-at-the-tag and `0006` forged-subject cases, seeding `v0.1.0` and `v0.2.0` so the fake worker's tag numbers hold, `tests/fake_worker.py:375`), `test_a_dead_integrate_is_resumed_by_a_rerun` |
| `test_a_halted_dependency_blocks_a_chain` | itself (the blocked chain, `root`), `test_a_lone_dependent_is_blocked_by_its_halt` (`only`), `test_a_free_version_ships_past_a_blocked_chain` (`edited`), `test_a_dependent_waits_while_its_dependency_works` (`worked`), `test_a_rejoined_dependency_brings_its_chain_back` (the rejoin `0071` added) |
| `test_no_worker_pushes` | itself (main, then the tag), `test_a_worker_repointing_origin_reaches_nothing`, `test_a_redirected_git_dir_reaches_nothing`, `test_a_repo_inside_a_worktree_reads_only_local` (with the linked worktree's commondir, `C:3275-3283`), `test_the_kept_urls_stand_past_a_repoint` (the last three seeding one clean run, and the kept-URLs test a `0002-marks` worktree), `test_a_refused_home_folder_still_pushes`, `test_a_planted_promisor_halts` |
| `test_a_run_pushes_only_tagged_merges` | `test_a_plain_commit_on_main_is_not_pushed`, `test_a_tagged_side_merge_is_not_pushed`, `test_a_release_merge_no_run_made_is_not_pushed`, `test_a_bare_version_tag_is_not_pushed`, `test_a_hand_release_is_the_persons_to_push`, `test_a_stray_tag_on_a_run_release_halts_until_removed` |
| `test_a_rerun_pushes_what_a_release_left` | itself (the kept URLs, then origin moves), `test_a_planted_remote_key_refuses_status_and_run` (the uploadpack, filter, config-key loop `C:2575-2601`, pushurl `C:2602-2604` and no-origin hook refusals), `test_a_key_set_after_the_refusal_reaches_nothing` (also seeding origin's `main` moved ahead and fetched, so the push is refused, `C:2493-2505`), `test_the_scratch_stands_outside_the_worktree`, `test_a_local_origin_url_is_refused`, `test_a_tag_alone_starts_one_run`; each split test seeds one clean run, then `_released` `v0.2.0` unpushed, as the first part leaves it |
| `test_a_local_release_is_pushed_when_origin_returns` | itself (offline, refused, pushed), `test_a_push_that_lands_before_origin_flaps_passes` (seeding `v0.1.0` pushed and a kept base) |
| `test_a_run_goes_on_while_origin_is_down` | itself (seeding `_keep_base` at `main`), `test_a_run_with_no_offline_base_halts_when_origin_is_down`, `test_a_commit_past_the_offline_base_halts`; `RETRIES` set by `monkeypatch.setitem` |

## Tests

`git grep -c '^def test_' 6647909 -- tests/` counts the suite at the cut: 164 collected. The splits add tests and remove none of
their assertions; renamed tests keep the scenario titles they carry. Removed or merged, per `T5` and `I16`:

| removed or merged | carried by | scenario title it held |
|---|---|---|
| forged release's `move`, `delete`, `replace`, `graft`, `shallow` cases (`C:2963-2972`) | `test_a_resumed_push_retires_at_the_next_read`: `delete` folded into `("resume", *views)`; `("resume",)` stays | *A worker rewrites local history* |
| forged release's hand-release case (`C:2944-2948`) | `test_a_hand_release_is_the_persons_to_push`, which gains `ls-remote --tags origin` empty, as the case checked all of origin | *A worker forges a release* |
| `test_a_good_read_keeps_the_offline_base` (`C:3384`) — `0062·R6` | `test_a_local_release_is_pushed_when_origin_returns` (`C:3588`, `:3599`), `test_anchor_seeds_the_offline_base` (`C:3459`, `:3464`) | *A good read keeps the offline base*, to `test_a_local_release_is_pushed_when_origin_returns` |
| `test_a_version_cut_during_a_run_joins` (`C:1788`) — `0063·R8` | `test_a_new_executor_is_probed_mid_run`, its assertions moved per [D2](#d2) | *A version cut during the run*, to `test_a_new_executor_is_probed_mid_run` |
| `tests/test_gate_check.py`'s six topologies × three plans (`:238-271`) → the six with `unplanned`, the two plan variants on `parent-after-link` | `tests/test_gate_check.py:339`, `:386` | — |
| `test_mf_integrate_runs_its_script` (`tests/test_skills.py:531`) | `test_the_stations_run_the_bundled_metrics_script` (`tests/test_skills.py:479`, `_METRICS_SCRIPTS`) | — |
| `test_the_release_gates_its_fold_fresh` (`tests/test_skills.py:553`), and its helpers `_FRESH`, `_RELEASE_CUT`, `_fresh_problems` (`:540-550`) | retired by D42 | — |

## Dependencies

None.

## Risks / Trade-offs

- **A split that leans on state:** each chained step stays in one test, or seeds what it reads; [D3](#d3) names them.

## Verdict

Ready to build.
