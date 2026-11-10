# Sandbox tmp — design

How a sandboxed command and a Codex worker get a `TMPDIR` outside every repository, and how the tests stop depending on where
their temporary folder lies. Verdict: the tests' layer first, then the runner's, so the version's own gate is green on the pinned `sandboxed()`.

Read [proposal](proposal.md) for why, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the requirements.

## Context

Facts at `8c2ea64`, `HEAD` at the cut. `C` is `skills/mf-ship/scripts/conduct.py`, `K` is `tests/conftest.py`. Lines are `HEAD`'s,
from the cut's notes.

| id | fact | where |
|---|---|---|
| F1 | `sandboxed()` makes `<primary>/.minions/tmp` and sets `TMPDIR` to it: inside the primary's git repository, and the only temp folder the profile can write | `C:3305-3320` |
| F2 | with `TMPDIR` there, the corpus, facts, plan check, skip stub and verify check "cannot read or write exits 2" cases, next tag, pin and the planted-key tests fail; with a normal `TMPDIR` they pass; `GIT_CEILING_DIRECTORIES` at that `TMPDIR` makes every one pass but the planted-key test, whose scan still scans nothing under the primary's ignored `.minions/` | `K:20-31`, `tests/test_guardrails.py:73-115` |
| F3 | a worker's `TMPDIR` is also `.minions/tmp`; a Codex worker runs with `exclude_tmpdir_env_var` and `exclude_slash_tmp`, so it has no writable temp folder: 0099's checker halted `not clean` on `zsh: can't create temp file for here document`; zsh makes those files under `TMPPREFIX`, default `/tmp/zsh`, which `exclude_slash_tmp` leaves unwritable | `C:3468-3472`, `C:3528-3533` |
| F4 | `argv()` appends `SHELL_RULES` to every prompt, checkers' included, and the rules forbid `$(…)`, shell variables, loops and `cd`, not a here-document | `C:270-276`, `C:3459` |
| F5 | a Codex worker's roots are the common directory, each gitdir, the trees and a cutter's brief folder; `_unswapped` halts on a root that is a link or moved | `C:3505-3512`, `C:3394-3410` |
| F6 | `Run.worker` and `agent` call `argv()` then `work()`; no caller of `argv()` removes anything it made | `C:4733-4795`, `C:7541-7552` |
| F7 | this version's own converge runs the pinned `sandboxed()`, whose `TMPDIR` lies in the primary: a fix there cannot help its own gate, a fix in the tests' setup, read from the version's own tree, can | `C:3320`, `K:21` |
| F8 | the tests that read a `TMPDIR` this change moves | `tests/test_sandboxed.py:112-117`, `tests/test_sandboxed.py:253`, `tests/test_conduct.py:5240-5242`, `tests/test_conduct.py:9929-9937`, `tests/test_conduct.py:10662-10666`, `tests/test_conduct.py:10745-10764`, `tests/test_conduct.py:10793-10796` |
| F9 | the gate's CI job runs on `ubuntu-latest`, where `fake_sandbox_exec` stands in for Seatbelt | `.github/workflows/ci.yml:12` |

## Goals / Non-Goals

**Goals:** a gate run under `sandboxed()` and a gate run bare agree on every test, whichever folder `TMPDIR` names; a Codex worker
has a temporary folder that no repository holds and no worker can link away.

**Non-Goals:** a Claude worker's `TMPDIR` ([proposal](proposal.md#not-in-this-change)); a Codex fixer; any new station, parameter
or decision ([AGENTS.md](../../../AGENTS.md)'s patch line).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | the tests' layer: `K`'s `isolated_home` sets `GIT_CEILING_DIRECTORIES` at pytest's base temp for every test, and `test_betterleaks_finds_a_planted_key` runs `git init -q` in the folder it scans | F2: the ceiling alone makes every test pass but the planted-key test, which scans a folder the enclosing repository's `.gitignore` empties, so that folder is its own repository. Brief's Q1, Q2 | the ceiling alone: the planted-key scan stays empty · `--no-git` on the scan: the gate's own call differs from the test's |
| <a id="d2"></a>**D2** | `C` gains `_temp_folder(prefix)`: a fresh folder made by `tempfile.mkdtemp(prefix=prefix, dir=os.environ.get("TMPDIR") or "/tmp")`, resolved, never by a call that reads `tempfile.gettempdir()`, which Python caches; it stops with 2 and `conduct: cannot run — TMPDIR <parent> lies inside a git repository` when `git -C <parent> rev-parse --git-dir` exits 0, and with `conduct: cannot run — TMPDIR <parent>: <error>` when the folder cannot be made | the operator's shell sets `TMPDIR` to the system temp, and a gate run under `sandboxed()` has the fresh folder alone to write, so a nested call cannot make one under a system temp of its own (F7, F9); the check makes "outside every repository" a fact, not a hope; `_scratch` already names the home-folder scratch of a remote git call, so the new one is `_temp_folder` | the system temp by `os.confstr`: a nested call is refused, and Linux has none · no check: a `TMPDIR` in a repository reopens F2 silently |
| <a id="d3"></a>**D3** | `sandboxed()` makes `_temp_folder("mf-sandbox-")` after the `sandbox-exec` check and the `.minions` guard, adds it to the profile's write list, sets `TMPDIR` to it and removes it in a `finally` that covers the spawn; it keeps the `.minions` link guard through `_folder_fd(trees[0], ".minions")`, which no longer makes `tmp` | F1: the profile's real path of the folder is what Seatbelt matches; the folder is the command's own, so one command cannot read another's; the link guard stays because `uv`'s cache is still in `.minions` | a folder kept in `.minions/tmp` and a ceiling in the env: a command's `git` still finds the primary's repository when it stays |
| <a id="d4"></a>**D4** | `K`'s `isolated_home` also sets `TMPDIR` to a fresh `tmp_path_factory.mktemp("tmp")`, a sibling of `tmp_path` | the folders `_temp_folder` makes in a test then lie under the ceiling of D1, and in no repository a test makes at `tmp_path`; a run with `TMPDIR` inside the primary stays green | `tmp_path / "tmp"`: a test that makes a repository at `tmp_path` holds it · a monkeypatch of `_temp_folder` in each test: dozens of edits |
| <a id="d5"></a>**D5** | `argv()` makes `_temp_folder("mf-codex-")` for a Codex worker, after `_unswapped`, appends it as the last writable root, sets `TMPDIR` to it in place of `.minions/tmp` and `TMPPREFIX` to `<folder>/zsh`, both after `cache` and before `PATH` in the env prefix, and keeps `exclude_tmpdir_env_var` and `exclude_slash_tmp`; the `.minions/tmp` folder is made for a Claude worker alone | Brief's Q6 and its `C1` row: the folder is a root only by name, so Codex's own `TMPDIR` root stays off; zsh takes here-document files from `TMPPREFIX`, not `TMPDIR` (F3), so `TMPDIR` alone would leave the 0099 failure; no repository becomes writable ([D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes) holds); a worker cannot link a folder it cannot rename | `exclude_tmpdir_env_var=false`: Codex takes `TMPDIR` as a root by resolving links · a folder under `.minions`: a repository holds it |
| <a id="d6"></a>**D6** | `C` gains `_temp_of(command)`, the folder of a command's `TMPDIR=` element whose name starts `mf-codex-`, else None, and `_temp_gone(command)`, which removes it, never a link; `Run.worker` and `agent` call it in a `finally` around `work()` | F6: `argv()` returns a command, so the folder's name is in the command and nowhere else; the name prefix keeps the removal to folders `_temp_folder` made | an argument to `argv()` that the caller removes: dozens of callers and tests change · removal at the run's end: a long run piles folders |
| <a id="d7"></a>**D7** | `SHELL_RULES` gains `no here-document (<<): write a file with your editing tool;` before `use git -C <dir>`; its last words stay | Brief's Q6, the second guard: a shell that does not take `TMPPREFIX`, or a folder that is full, still cannot make a here-document's file; the last words are the test's `endswith` | a rule in each checker's `## Prompt`: the converge references say nothing of shells, and `argv()` already carries the rules to every prompt |
| <a id="d8"></a>**D8** | `skills/mf-release/SKILL.md` says where a worker's scratch folder is: `.minions/tmp/` on Claude, a fresh folder outside every repository on Codex | its sentence at lines 175-176 is false for Codex once D5 lands | none: a rule that misstates the behaviour is patch material |

## Tests

The change adds `test_a_command_gets_a_fresh_tmpdir_outside_every_repository`, `test_a_tmpdir_in_a_repository_runs_nothing`,
`test_a_codex_worker_gets_its_own_temporary_folder` and `test_a_codex_temp_folder_is_removed`, and extends the tests below; it
removes none. At the base `tests/test_sandboxed.py` holds 11 tests, `tests/test_guardrails.py` 5 and `tests/test_conduct.py` 162
(`git grep -c '^def test_' -- <file>`).

| layer | file | test | does | why here |
|---|---|---|---|---|
| unit | `tests/test_guardrails.py` | `test_the_isolation_fixture_holds_home_under_tmp_path`, extended | `GIT_CEILING_DIRECTORIES` names `tmp_path`'s parent, and `TMPDIR` names a folder under that parent and not under `tmp_path` | the test of the fixture's other variables (`T2`) |
| unit | `tests/test_guardrails.py` | `test_betterleaks_finds_a_planted_key`, extended | the scanned folder is its own repository before the keys are written | the proof of the eighth test (`T1`) |
| unit | `tests/test_sandboxed.py` | `test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment`, extended | `TMPDIR` is no `.minions/tmp`, the profile writes it, the folder is gone after, and a linked `.minions` still stops with 2 | a step in the test that reads the command's environment (`T2`) |
| unit | `tests/test_sandboxed.py` | `test_the_command_runs_a_command_in_the_cwd`, extended | the profile is `_profile` of the repository and the command's `TMPDIR` | its profile assertion moves with D3 |
| unit | `tests/test_conduct.py` | `test_the_run_hands_converge_its_trees_and_sandbox`, extended | its command prints `TMPDIR` after the cwd, and the profile is `_profile` of the trees and that folder | its profile assertion moves with D3 |
| unit | `tests/test_sandboxed.py` | `test_a_command_gets_a_fresh_tmpdir_outside_every_repository`, new | on the fake `sandbox-exec`: `git rev-parse` in `$TMPDIR` exits non-zero, a file is written there, the folder is gone after, and a second command gets another | Brief's Q3; the fake runs unconfined and the question is where the folder lies (`T1`) |
| unit | `tests/test_sandboxed.py` | `test_a_tmpdir_in_a_repository_runs_nothing`, new | `TMPDIR` inside a repository, and `TMPDIR` naming a missing folder: each stops with 2, naming `TMPDIR`, and the command does not run | the guard of [D2](#d2) and its write failure (`T1`) |
| unit | `tests/test_sandboxed.py` | `test_a_write_outside_the_trees_is_denied`, extended | a write into the command's `TMPDIR` succeeds, one beside it is denied; skipped where Seatbelt cannot nest | the real profile (`T2`) |
| unit | `tests/test_conduct.py` | `test_a_codex_worker_gets_its_own_temporary_folder`, new | `argv("codex", …)` sets `TMPDIR` to a folder where `git rev-parse` fails and `TMPPREFIX` to `<folder>/zsh`, the folder is the last writable root, `exclude_tmpdir_env_var` stays, a `TMPDIR` in a repository stops with 2, and a Claude command keeps `.minions/tmp` | Brief's Q3 case for Codex; `argv()` is the seam (`T1`) |
| unit | `tests/test_conduct.py` | `test_a_codex_temp_folder_is_removed`, new | `_temp_gone` removes the folder `_temp_of` names, leaves a folder it did not make and a link, and `agent` removes it when the worker ends | the removal of [D6](#d6) (`T1`) |
| unit | `tests/test_conduct.py` | the codex loop at `:9929`, the argv blocks at `:10662` and `:10745`, the cutter block at `:10793`, the root lists at `:10856` and `:10903`, and `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, extended | each reads the Codex `TMPDIR` and its last root as D5 sets them, the lists compared up to that root; the rules hold `here-document` | the assertions that named `.minions/tmp` or the exact roots for Codex |

End-to-end runs added: none. `I16` table: none removed.

## Dependencies

None.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| a conductor started with `TMPDIR` inside a repository now stops | the stop names `TMPDIR`; the bug it prevents was a red gate with no cause named |
| a Codex folder leaks when the conductor dies between `argv()` and `work()` | the folder is empty, under the system temp, and the OS clears it; the name prefix lets a later `_temp_gone` find none |
| the planted-key test's own repository is what the scan needs, a premise the brief measured only for the ceiling | the acceptance run of 1.6 holds it in phase 1, before any code moves |
| the escape drill calls `argv()` for Codex and removes nothing | its folder is empty, outside the gate, and the OS clears it |
| a test's `TMPDIR` under the base temp hides a test that relied on the system one | `tests/test_guardrails.py` holds the fixture's variables, and the acceptance run puts pytest's base temp (`--basetemp`) inside the primary |
| this version's own converge runs the pinned `sandboxed()` | phase 1 alone makes its gate green; phases 2 and 3 are green there through D4 ([F7](#context)) |
| 0110-gate-hardening meets the new rule when it integrates | its tests run under the same fixture; its round-1 fixes stand (the brief's Q5) |

## Verdict

Build in phases, each green on its own: the tests' layer; `sandboxed()` and the fixture's `TMPDIR`; the Codex worker, the shell
rules and the release text.
