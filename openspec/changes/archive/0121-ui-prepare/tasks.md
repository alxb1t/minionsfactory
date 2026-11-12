# ui · prepare — tasks

The phases: the rows, the fetch, the workers, the halt, the record. Each ends on a green `make check`.

## Progress

- [x] 1 — The rows · moderate
- [x] 2 — The fetch · hard
- [x] 3 — The workers · moderate
- [x] 4 — The halt · hard
- [x] 5 — The record · moderate

## 1 — The rows

- [x] 1.1 **HALT CHECK** `PACKAGE`, `SPECIFIER` and `_prefetch` stand in `skills/mf-ship/scripts/conduct.py` where [D1](design.md#d1) reads them.
  Verify: `git grep -n -e '^PACKAGE = ' -e '^SPECIFIER = ' -e '^def _prefetch' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.2 Add `NPM_PREFIX`, `NPM_NAME`, `NPM_VERSION` and `_plain_row(package, constraint) -> bool` after `SPECIFIER` in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1): a Python row is plain when `PACKAGE` and `SPECIFIER` match it, as `_prefetch` reads it today. Test each row of its table in `test_an_npm_row_is_plain_only_at_an_exact_version`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k an_npm_row_is_plain_only_at_an_exact_version` exits 0.
- [x] 1.3 Make `_prefetch` check every row with `_plain_row` before any fetch, and fetch only the rows that do not start `npm:`. An npm row's refusal reads `not npm:<name> at an exact version`; a Python row's text is unchanged. Test each refusal of the spec's scenario in `test_a_cut_refuses_an_npm_row_that_is_no_exact_version`, `tests/test_conduct.py`, beside the wheel prefetch's test.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_cut_refuses_an_npm_row_that_is_no_exact_version` exits 0.
- [x] 1.4 In `packages` of `skills/mf-plan/scripts/brief_check.py`, add a halt `## Dependencies row <n> — not an npm package at an exact version: <package> <constraint>` for each `npm:` row `conduct["_plain_row"]` refuses; Python rows read as before. Test it in `test_an_npm_row_is_checked_at_the_plan`, `tests/test_brief_check.py`.
  Verify: `uv run pytest -q tests/test_brief_check.py -k an_npm_row_is_checked_at_the_plan` exits 0.
- [x] 1.5 Pin that `I11` of `skills/mf-cut-change/scripts/cut_check.py` holds a `| npm:vue | 3.5.43 | … |` table in `test_an_npm_row_in_the_dependencies_table_is_read`, `tests/test_cut_check.py`, beside `test_a_dependencies_table_is_read`.
  Verify: `uv run pytest -q tests/test_cut_check.py -k an_npm_row_in_the_dependencies_table_is_read` exits 0.

## 2 — The fetch

- [x] 2.1 Add `network=False` to `_profile` in `skills/mf-ship/scripts/conduct.py`: set, the profile holds no `(deny network*)` line; unset, it is today's string. Test both in `test_a_profile_may_open_the_network`, `tests/test_sandboxed.py`.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k a_profile_may_open_the_network` exits 0.
- [x] 2.2 Add `NPM_REGISTRY`, `NPM_QUIET_DAYS`, `_npm_env(scratch)` and `_fetch_run(argv, cwd, writes, env, timeout)` to `conduct.py`, per [D3](design.md#d3) and [D2](design.md#d2) step 4; no `sandbox-exec` stops with 2. Add `_FAKE_NPM` beside `_FAKE_UV` in `tests/test_conduct.py`.
  Verify: `git grep -n -e '^NPM_REGISTRY' -e '^def _npm_env' -e '^def _fetch_run' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.3 Add `_fetch_npm(primary, rows, command)` to `conduct.py`, [D2](design.md#d2) steps 1 to 5, and have `_prefetch` call it for the npm rows after its wheel loop, so a missing `uv` stops the cut as it does today. Test the argv, the environment, the profile, the cache, a failure, a timeout and a scratch folder left empty in `test_a_cut_fetches_the_npm_rows_it_approves`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_cut_fetches_the_npm_rows_it_approves` exits 0.
- [x] 2.4 Make `_fetch_npm` stop with 2 naming `npm` when no `npm` is on `PATH` and a row or a lock needs it, and run nothing when none does. Test both in `test_a_missing_npm_halts_by_name_only_where_it_is_needed`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_missing_npm_halts_by_name_only_where_it_is_needed` exits 0.
- [x] 2.5 Return from `_fetch_npm` the lines of [D2](design.md#d2) step 6, make `_prefetch` return them, and have `cut` print them before its own line. Test the lines and the flag in `test_a_cut_prints_the_new_packages_of_the_tree`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_cut_prints_the_new_packages_of_the_tree` exits 0.
- [x] 2.6 Add `_fetch_locks(primary)` to `conduct.py`, and call it in `Run.ship` after `_sync_scripts`, halting the run on its text; a default branch `git ls-tree` cannot list is no lock. Test a lock, no lock, an unlistable default and a failed fetch in `test_a_run_start_fetches_each_tracked_lock`, `tests/test_conduct.py`, driven by `_run_claude`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_run_start_fetches_each_tracked_lock` exits 0.

## 3 — The workers

- [x] 3.1 Add `NPM_SETTINGS` to `conduct.py` and build `npm_config_cache=<primary>/.minions/npm-cache` beside `cache` in `argv`, per [D4](design.md#d4): after `scratch` in a Claude worker's `env` prefix, after `path` in a Codex worker's. Test both lines in `test_a_worker_carries_the_npm_settings`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_worker_carries_the_npm_settings` exits 0.
- [x] 3.2 Make `test_a_worker_carries_the_allowlist_and_a_denial_is_named` in `tests/test_conduct.py` slice a Claude worker's prefix up to `claude`, not at `len(hooks_off) + 5`, and a Codex worker's up to `codex`, not at `len(hooks_off) + 6`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_worker_carries_the_allowlist_and_a_denial_is_named` exits 0.
- [x] 3.3 Set `npm_config_cache`, `npm_config_offline` and `npm_config_ignore_scripts` in `sandboxed()`'s environment beside `UV_CACHE_DIR`. Test them in `test_a_sandboxed_command_has_npm_offline_with_scripts_off`, `tests/test_sandboxed.py`.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k a_sandboxed_command_has_npm_offline_with_scripts_off` exits 0.

## 4 — The halt

- [x] 4.1 Add `UNAPPROVED_NPM` and `_npm_unapproved(tree, change, default)` to `conduct.py`, per [D5](design.md#d5): the npm rows of `design.md` at `_cut_commit`, each tracked `package.json`, the default branch's file at the same path. Test each scenario of the spec in `test_a_manifest_is_judged_by_the_rows_of_the_cut`, `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_manifest_is_judged_by_the_rows_of_the_cut` exits 0.
- [x] 4.2 Return `_npm_unapproved`'s text from `_check_build` after its existing checks, `default_branch(primary)` its third argument. Test that `check` halts a built version before converge, naming the file, the package and its specifier, and passes one whose packages are all approved, in `test_a_build_halts_on_a_direct_npm_package_no_row_approves`, `tests/test_conduct.py`, beside `test_each_check_passes_only_on_disk_evidence`.
  Verify: `uv run pytest -q tests/test_conduct.py -k a_build_halts_on_a_direct_npm_package_no_row_approves` exits 0.

## 5 — The record

- [x] 5.1 In `docs/decisions.md`, add `### D81 · An npm package is approved at an exact version and installed offline` after D62, with its id in the index lines at the head of the page; and in D62's *Rejected* line say an exact npm version needs no grammar. Decisions Q6, Q8, Q11 and Q15 of the brief state it.
  Verify: `git grep -n 'D81' -- docs/decisions.md` prints the heading and the index lines.
- [x] 5.2 In `docs/principles.md`, add to *A new dependency halts for a person* the build check of [D5](design.md#d5) under *Held by*, citing D81, and the npm row beside the Python one.
  Verify: `git grep -n 'D81' -- docs/principles.md` prints a line.
- [x] 5.3 In `THREAT_MODEL.md`, add that an npm row travels the approval's path of D62, that `.minions/npm-cache` is a run-directory folder a worker may write and read offline, and that the fetch runs under the OS sandbox with the network open, no credential read.
  Verify: `git grep -n 'npm-cache' -- THREAT_MODEL.md` prints a line.
- [x] 5.4 Say it in the skills' prose: `skills/mf-ship/SKILL.md`, the `cut` row's fetch and the `sandboxed` row's environment; `skills/mf-plan/SKILL.md`, the `## Dependencies` row form `npm:<name>` at an exact version; `skills/mf-cut-change/SKILL.md`, the `design.md` row form; `skills/mf-build/SKILL.md`, stop-condition 4's npm check.
  Verify: `git grep -l 'npm:' -- skills/mf-ship/SKILL.md skills/mf-plan/SKILL.md skills/mf-cut-change/SKILL.md skills/mf-build/SKILL.md` prints each path.
