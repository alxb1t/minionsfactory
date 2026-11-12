# ui · prepare — design

How a brief's approved npm packages reach a worker with no registry in reach: read at the queue, fetched once, installed offline. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

MF fetches a brief's approved Python wheels at the queue into `.minions/uv-cache`, and every worker and `sandboxed()` reads them offline (`_prefetch`, `skills/mf-ship/scripts/conduct.py`). An npm package has no such path: a worker's npm reads the operator's home cache, or nothing.
`npm` and `node` are no command a Claude worker may type, but `make gate` spawns anything, and the OS sandbox alone holds it.
A worker with the registry in reach can install any package, and `Ship network:` is no answer: the registry takes a publish, and the proxy reads a hostname alone.
The flow this change builds:

```
brief ## Dependencies ──▶ conduct.py cut ──▶ _prefetch ──▶ .minions/npm-cache ◀── run start (each tracked lock)
   npm:vue | 3.5.43        refuse a bad row    sandbox, net open, scripts off
                                                          │
          Claude worker · Codex worker · sandboxed() ◀────┘  offline, scripts off, same cache
                                                          │
          build ends ──▶ _check_build ──▶ a direct package no row approves halts before converge
```

## Goals / Non-Goals

- Goals: only approved packages install; no worker reaches the registry; a lock's tree is warm before a worker needs it; the person reads each new package of the tree at the queue.
- Non-Goals: `ui/`, `package.json`, `make setup`, the gate and CI steps (the scaffold); pnpm; a `Ship` line; the fetch at `rejoin`; a manifest check for Python.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | An npm row is `npm:<name>` at an exact version; the grammar lives in `conduct.py`, and the pair travels as written | Q11: an exact version needs no ecosystem grammar, which D62 rejected; the queue entry and the `design.md` comparison need no new shape | a range or a tag (a grammar per ecosystem); a new column for the ecosystem |
| [D2](#d2) | The fetch runs at each cut and each run's start: the lock's tree, then the approved rows, into `.minions/npm-cache` | Q6, Q12: the wheel prefetch's shape; the lock first, so a cold cache never turns a worker's install red | a fetch in `rejoin`; a fetch by a worker |
| [D3](#d3) | The fetch runs under the OS sandbox with the network open | Q13: npm unpacks archives; `--no-build` has no npm equal | a fetch outside the sandbox, as the wheel fetch runs |
| [D4](#d4) | A worker's npm: the cache, offline, scripts off, at the Claude worker, the Codex worker and `sandboxed()` | Q14, Q10: no worker reaches the registry, and no `Ship` line is needed | a `Ship network:` line; `npm` on the allowlist |
| [D5](#d5) | The build ends on a check: a direct package the default branch lacks and no row approves halts the version before converge | Q15, C1: only approved packages at the approved versions, held by a check, not by the cache alone | the cache alone; reading the queue entry, which is gone |
| [D6](#d6) | The tests fake `npm` first on `PATH`; no test reaches a network | Q17: the wheel prefetch's tests | a live fetch |
| [D7](#d7) | The record: decision D81, the requirements, the principle, the threat model, the skills' prose | Q6, Q8, Q16: the approval is the direct packages at exact versions; the lock pins the rest | a record in the scaffold's version |

### D1

`conduct.py` gains the patterns of an npm row and `_plain_row(package, constraint)`, which says whether a row is plain. A row whose package starts `npm:` reads as `npm:` plus a lowercase name, scoped names (`@vitejs/plugin-vue`) allowed, and a constraint of one exact version: digits, dots and an optional pre-release. Any other row is plain when `PACKAGE` and `SPECIFIER` match it, as today.

| row | read |
|---|---|
| `npm:vue` · `3.5.43` | plain |
| `npm:@vitejs/plugin-vue` · `6.0.1` | plain |
| `npm:vue` · `^3.5.43`, `latest`, a URL, a path, a git reference | refused |
| `npm:vue@npm:other` · `1.0.0` (an alias) | refused |
| `left-pad` · `>=1.3,<2` | a Python row, as today |

`_prefetch` checks every row, Python and npm, before any fetch, and refuses with exit 2 and the row named; a Python row's text is as it is today. [D62](../../../docs/decisions.md#d62--a-queued-cuts-packages-are-approved-at-the-plan) rejected *each ecosystem's version grammar*: an exact version needs none, so the decision is narrowed, not overturned. `brief_check.py`'s `packages` calls the same function through `conduct`, so a plan names the refusal before the person's yes. `cut_check.py`'s `I11` reads the table's shape alone and holds an npm row already; a test pins it.

### D2

`_prefetch` returns the printed lines and `cut` prints them before its own; it fetches the wheels first and calls `_fetch_npm` after, so a missing `uv` stops a cut as it does today. A new `_fetch_npm(primary, rows, command)` does the npm part: `command` is `cut` or `run`, the word that starts its halts.

1. The locks are the `package-lock.json` files tracked at the default branch (`git ls-tree -r --name-only`); a default branch git cannot list has none. With no lock and no row it returns, and `npm` is not looked for. Else `npm` missing stops with 2 naming `npm`.
2. For each lock, a scratch folder under `.minions/tmp` holds the manifest and the lock copied from the default branch. For a cut that approves rows in a repository with no lock, the scratch folder holds an empty manifest.
3. `npm ci` installs the lock's tree. Then `npm install --no-save <name>@<version>` installs each approved row.
4. Each command takes `--ignore-scripts`, `--no-audit`, `--no-fund`, `--registry` set to npm's own, `--userconfig` and `--globalconfig` set to `/dev/null`, `--cache` set to `.minions/npm-cache`, and `--before` set to seven days ago. The environment is the conductor's with each `npm_config_*` and `NPM_*` name and each name of `TOKENS` removed, and `HOME` and `TMPDIR` naming the scratch folder.
5. Each command has `PREFETCH_SECONDS`. A failure or a timeout stops with 2 naming the package, or the lock; the scratch folder is removed either way.
6. The scratch folder's `node_modules/.package-lock.json` lists the tree after step 3 and after step 4. The packages in the second and not the first are the new ones, and the function returns one line each, `npm: new <name> <version>`, ending ` · install script` when the entry says `hasInstallScript`. Each line is printed once, for several locks.

At a run's start, `_fetch_locks(primary)` calls `_fetch_npm` with no rows and returns the stop's text, as `_sync_scripts` returns its own; `Run.ship` halts the run on it, after `_sync_scripts`. `rejoin` runs no fetch. The lock's own tree is trusted as the person committed it to the default branch; `--before` bounds what the cut's rows resolve.

### D3

`_profile(trees, home)` gains `network=False`; with it set, the profile has no `(deny network*)` line. The default is today's string, so `sandboxed()` and the tests that compare it stay as they are.

A new `_fetch_run(argv, cwd, writes, env, timeout)` starts `sandbox-exec -p <profile> <argv>`, the profile's writable trees being the scratch folder and `.minions/npm-cache` alone, and returns the finished process.

No `sandbox-exec` on `PATH` stops with 2 and runs nothing, as `sandboxed()` does. The profile still denies every `SECRETS` path, `~/.npmrc` included.

### D4

`NPM_SETTINGS` holds `npm_config_offline=true` and `npm_config_ignore_scripts=true`. A worker's `argv` builds `npm_config_cache=<primary>/.minions/npm-cache` beside `cache` and adds both. A Claude worker's settings follow its `scratch`; a Codex worker's follow its `path`, so the slice of `test_a_codex_worker_gets_its_own_temporary_folder` keeps its place and the slices of `test_a_worker_carries_the_allowlist_and_a_denial_is_named` move. `sandboxed()` sets the same keys in its environment beside `UV_CACHE_DIR`. [D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes) accepts no new domain: `NETWORK` is unchanged.

### D5

The queue entry is deleted when the cut passes (`Run.cutting`, `_remove_in(..., "cuts", ...)`), so the build cannot read the queued rows. `design.md`'s `## Dependencies` at the cut commit is the copy that stays, and the cut station already halted a row of it outside the queue's rows (`_unapproved`). So `_npm_unapproved(tree, change, default)` reads that file at `_cut_commit`, takes its `npm:` rows, and compares. No cut commit means no row.

For each `package.json` tracked at `HEAD` outside `node_modules`, a direct package is one under `dependencies`, `devDependencies`, `optionalDependencies` or `peerDependencies`. It passes when the default branch's file at the same path holds the same name at the same specifier, or a row names `npm:<name>` at exactly that specifier. A range fails: `^3.5.43` is no row's `3.5.43`.

The first failure is returned as `UNAPPROVED_NPM: <path> <name> <specifier>`. `_check_build` returns it after its existing checks, so the build stage fails and the version halts before converge.

That choice is the cutter's, recorded as `C1` in the brief's decisions: the brief says "the queue's rows", and the committed `design.md` is the queue's rows once the cut has passed.

### D6

New tests go to the lowest layer that can fail ([T1](../../../skills/mf-build/SKILL.md)). They reuse `_conduct`, `_primary`, `_claimed`, `_swap_runner`, `_version`, `_commit` and `_done` of `tests/test_conduct.py`, and the autouse fake `sandbox-exec`.

A `_FAKE_NPM` beside `_FAKE_UV` records its argv, its environment and its working directory to `FAKE_NPM_RECORD`, copies `FAKE_NPM_LOCK` to `node_modules/.package-lock.json` of its working directory when set, sleeps `FAKE_NPM_SLEEP` and exits `FAKE_NPM_EXIT`.

The `T2` check: no existing test reaches the fetch or the halt, so each has a test of its own.

### D7

The record is [D81](../../../docs/decisions.md) in `docs/decisions.md`, which narrows D62's rejected grammar and cites Q6, Q8, Q11 and Q15 of the brief; the principle *A new dependency halts for a person*; the threat model; and the skills' prose. The spec delta folds into the living spec at the release, not here.

## Tests

Added tests and the layer of each; no end-to-end test is added, the repo has no browser layer.

| layer | test | file | shows |
|---|---|---|---|
| unit | `test_an_npm_row_is_plain_only_at_an_exact_version` | `tests/test_conduct.py` | [D1](#d1)'s table, each row |
| unit | `test_a_profile_may_open_the_network` | `tests/test_sandboxed.py` | `network=True` drops the deny line, the default is unchanged |
| unit | `test_a_sandboxed_command_has_npm_offline_with_scripts_off` | `tests/test_sandboxed.py` | the npm keys and the cache path |
| unit | `test_a_worker_carries_the_npm_settings` | `tests/test_conduct.py` | the Claude and the Codex command line |
| unit | `test_an_npm_row_is_checked_at_the_plan` | `tests/test_brief_check.py` | the plan names a bad row |
| unit | `test_an_npm_row_in_the_dependencies_table_is_read` | `tests/test_cut_check.py` | `I11` holds the row |
| unit | `test_a_manifest_is_judged_by_the_rows_of_the_cut` | `tests/test_conduct.py` | each scenario of the halt, on the helper |
| integration | `test_a_cut_refuses_an_npm_row_that_is_no_exact_version` | `tests/test_conduct.py` | each refusal exits 2, no fetch, nothing reserved |
| integration | `test_a_cut_fetches_the_npm_rows_it_approves` | `tests/test_conduct.py` | argv, environment, profile, cache, failure, timeout |
| integration | `test_a_missing_npm_halts_by_name_only_where_it_is_needed` | `tests/test_conduct.py` | a row or a lock needs `npm`, or none does |
| integration | `test_a_cut_prints_the_new_packages_of_the_tree` | `tests/test_conduct.py` | each new package, its version and its flag |
| integration | `test_a_run_start_fetches_each_tracked_lock` | `tests/test_conduct.py` | a lock, no lock, a failed fetch halts the run |
| integration | `test_a_build_halts_on_a_direct_npm_package_no_row_approves` | `tests/test_conduct.py` | the halt and the pass, through `check` |

The count of tests at the base of each file comes from `git grep -c '^def test_' -- tests/test_conduct.py tests/test_sandboxed.py tests/test_brief_check.py tests/test_cut_check.py`; the build adds the tests of the table to it. No test is deleted or merged, so the `I16` table is empty.

An existing test reads each worker's environment prefix by position and changes with [D4](#d4): `test_a_worker_carries_the_allowlist_and_a_denial_is_named` slices a Claude worker's command line at `len(hooks_off) + 5` and a Codex worker's at `len(hooks_off) + 6`, and expects the executor next. `test_a_codex_worker_gets_its_own_temporary_folder` reads up to `path`, and the `npm` settings follow it, so it stays as it is. The escape drill needs no change: it runs in a scratch repo with no `Ship` lines and expects no worker to reach npm.

## Dependencies

None.

## Risks / Trade-offs

- The lock's tree installs without the 7-day bound: `--before` reads the registry's time for what npm resolves, and a lock names its versions. The person's commit to the default branch is the review. The 7 days hold what the cut's rows resolve.
- A package with an install script gets none: `--ignore-scripts` is set at the fetch and at every worker. A package that needs its script, a native build, fails red at the gate; the printed flag tells the person before the yes.
- The fetch needs the network at each run's start where a lock is tracked. A run offline halts at its start, as a failed `uv sync --script` does. A warm cache serves every worker offline after it.
- The fetch acts only once the machine's pin moves to this release ([D55](../../../docs/decisions.md#d55--one-pinned-mf-release-per-machine)): the person's word.
- A direct package in a manifest the version moves is read at its new path: a moved file with the same package reads as new and halts. The halt names the file; the person approves or re-plans.

## Migration Plan

None. A repository with no tracked lock and no `npm:` row runs no `npm`.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the rows, the fetch, the workers, the halt, the record.
