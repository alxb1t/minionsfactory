# uv race — design

How the versions of one run stop racing on what they share: converge builds no helper environment, a run builds each pinned
script's environment once and in sequence, and every shared resource has a named guard. Verdict: each layer has its own
phase — the cause, the prevention, the audit and its stress test.

Read [proposal](proposal.md) for why and [tasks](tasks.md) for the phases. There is no spec delta ([D7](#d7)).

## Context

Facts at `3ddeffd`, re-read at `e3051e5`, `HEAD` at the cut. `K` is `skills/mf-converge/scripts/converge.py`, `C` is
`skills/mf-ship/scripts/conduct.py`. Lines are `HEAD`'s, from the cut's notes.

| id | fact | where |
|---|---|---|
| F1 | `script(name, *args)` returns `["uv", "run", "--script", <script>, *args]`; each call runs it under `sandboxed()` | `K:367-369` |
| F2 | `script()` starts `gate_run.py` at `K:416`, `K:1077` and `K:1219`, `gate_check.py` at `K:418` and `plan_check.py` at `K:457` and `K:1116` | `K:416-457`, `K:1077`, `K:1116`, `K:1219` |
| F3 | `K` also loads other scripts in-process by `runpy`, `plan_check.py` among them | `K:29-38` |
| F4 | `gate_run.py`, `gate_check.py` and `plan_check.py` declare `requires-python = ">=3.12"` and `dependencies = []`, as `C` does | `skills/mf-converge/scripts/gate_check.py:1-4`, `C:1-4` |
| F5 | every version's converge thread shares the primary's `.minions/uv-cache`: the sandboxed env sets `UV_CACHE_DIR` and `UV_OFFLINE=1`, a worker's argv sets the same cache | `C:3214-3215`, `C:3356` |
| F6 | `uv sync --script <file>` builds `environments-v2/<stem>-<hash>` under the cache and writes no `.lock` file beside the script; a later `uv run --script <file>` reuses the environment | a probe on a scratch copy, at the cut |
| F7 | `C` loads `converge` in-process; the one `uv run --script` it starts itself is `brief_check.py` in the cut | `C:4260`, `C:6980` |
| F8 | the skills folder of `C` is `Path(__file__).resolve().parents[2]`; the pinned release's folders are the keys of `pin.py`'s `trees()`, and `move()` returns `pin: moved to <tag>` or `pin: cannot move — …` | `C:63-68`, `skills/mf-ship/scripts/pin.py:252-263`, `skills/mf-ship/scripts/pin.py:312-341` |
| F9 | `run()` re-pins once, in its `finally`; `Run.ship()` empties `.minions/tmp` before a version thread starts | `C:6554`, `C:6414` |
| F10 | `scripts/corpus.py` deletes and recreates `.minions/corpus/<case>/<n>` with no lock; its `.minions` is the primary's from every worktree | `scripts/corpus.py:126-129`, `scripts/corpus.py:165-171` |
| F11 | `tests/test_converge.py` reads a `uv` argv as `Path(argv[3]).name` when `argv[0] == "uv"` | `tests/test_converge.py:158`, `tests/test_converge.py:724`, `tests/test_converge.py:791` |
| F12 | the sandbox profile allows every read, so a sandboxed command reads the conductor's interpreter | `C:3153-3184` |

## Goals / Non-Goals

**Goals:** no helper environment is built while versions run at once; each shared resource of a run has a named guard and a
reason; the race becomes a test, not a chance.

**Non-Goals:** a target's own `uv run --script` in its gate ([Not in this change](proposal.md#not-in-this-change)); a uv cache
for each version; a new station, parameter, decision or requirement.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `script()` of `K` returns `[sys.executable, str(HERE / name), *args]`, the conductor's own Python 3.12 or later, and its docstring says so. Each call still runs under `sandboxed()`. A test reads each name `K` passes to `script()` and asserts the file's PEP 723 header declares `dependencies = []`: a script with a dependency cannot run by a bare interpreter | no per-call uv environment, so nothing to race on (F1, F5); the scripts `script()` starts have no dependency (F4); a sandboxed command reads the interpreter (F12) | a lock around `uv run` in `K`: the workers' own `uv run` of the same scripts stay racy · a cache for each thread: it builds every environment again |
| <a id="d2"></a>**D2** | `C` builds each pinned script's environment before any thread uses it. `_pinned_scripts(skills)` returns the sorted `<skills>/*/scripts/*.py` whose first line is `# /// script`. `_sync_scripts(primary, roots)` runs, for each distinct root and each such script in order, one `uv sync --script <script>` with `timeout=SYNC_SECONDS` (600), `UV_CACHE_DIR` the primary's `.minions/uv-cache`, and no `UV_*`, `PIP_*` or `VIRTUAL_ENV` name of the person's environment; it returns `None`, or `uv sync --script <name> failed: <first non-blank stderr line>` (`timed out` for a timeout). `Run.ship()` calls it right after `_fresh_tmp`, its roots the skills folder of `C` and each key of `pin["trees"]()`, and a failure halts the run as `_fresh_tmp`'s does. `run()` calls it again in its `finally` when `pin["move"](mark)` returns a line that starts `pin: moved to`, its roots each key of `pin["trees"]()`; a failure there prints `run: <why>` and changes no exit | one writer, in sequence, before the threads exist: a worker or a thread then only reuses (F6); the run starts unsandboxed and online, so a script with a dependency is cached before the offline sandbox needs it; the run halts at its start, never in a worker | a sync inside each worker: it is the race · a sync at the first `uv run` of a thread: a thread cannot know it is first |
| <a id="d3"></a>**D3** | [The shared-state audit](#the-shared-state-audit) names each resource the versions of a run share, who shares it, its guard, and a verdict: held, fixed here, or deferred with its trigger. A gap is fixed in this change when the fix is a lock or a name, and deferred when it needs a metric to prove it | the person asked to prevent the races of parallel versions in any project, not one race | a fix for each row: a held row needs none |
| <a id="d4"></a>**D4** | `scripts/corpus.py` `run()` creates the `minions` folder with `mkdir(parents=True, exist_ok=True)` after its link check, then takes `fcntl.flock(LOCK_EX)` on `<minions>/corpus.lock`, opened `O_CREAT \| O_RDWR \| O_NOFOLLOW`, and holds it across every case. A link at that name, or an open that fails, is a `Stop` naming `corpus.lock` | the corpus runs from each worktree into the primary's shared `.minions/corpus/` (F10), so parallel builds delete each other's output; the kernel drops a flock when its process ends, so no stale lock stays | a folder per worktree: the output path is part of what a reader of the corpus knows · a `mkdir` lock: it goes stale on a kill |
| <a id="d5"></a>**D5** | One test, `test_three_versions_cut_built_converged_and_closed_at_once`, is parametrized over ten rounds, each in its own `tmp_path`. A round queues three cuts with `_queued`, runs one `_run_claude`, and asserts exit 0, no halt event in the run log, and each version released. It is marked `slow` | the race is a draw: ten rounds make it a test, and the three versions share every resource of [the audit](#the-shared-state-audit) at once | a loop in one test: one failure hides the rest · a real sandbox: a Seatbelt cannot nest |
| <a id="d6"></a>**D6** | The converge change acts from the next version: a run uses the pinned release's converge and conduct, so this version's own run still starts converge's scripts by `uv`, and the sync of D2 does not run for it | self-hosting, as 0110's D9: a pinned release cannot read what the branch adds | holding the version until it can run itself: no version could ever land |
| <a id="d7"></a>**D7** | The change sets `skip_specs: true`. The spec names no converge script as run by `uv`; it names `uv run --script` for the metric collector and the cut's prefetch only, and neither changes | a patch adds no requirement and no decision ([AGENTS.md](../../../AGENTS.md)); `docs/decisions.md` is untouched | a modified requirement: there is no title to modify |

## The shared-state audit

Each row is a resource the versions of one run share. Lines are `HEAD`'s, from the cut's notes.

| id | resource | shared by | guard | verdict |
|---|---|---|---|---|
| U1 | the uv cache's script environments, `environments-v2/<stem>-<hash>` | each thread's and worker's `uv run --script` of a pinned script | none: the race (F5) | **fixed** — [D1](#d1) starts converge's by `sys.executable`; [D2](#d2) builds the rest before any thread |
| U2 | the uv cache's wheels, and each version's project environment | the sandboxed gate's `uv sync --locked` in each worktree | each worktree's own `.venv`; uv's own lock on the cache | **held** — no MF code shares a `.venv` |
| U3 | `.minions/debt.md` | converge threads writing cards | the `.minions/debt.lock` folder, taken by `mkdir`, waited for, then a halt (`K:1258-1275`, `C:52-53`) | **held** |
| U4 | `.minions/tmp` | every Claude worker's `TMPDIR` | emptied once by `_fresh_tmp` before a thread starts (`C:6414`); `mktemp` names are unique; one run at a time by `.minions/runs/active` | **held** |
| U5 | `.minions/corpus/<case>/<n>` | each build's `make corpus` | none (F10) | **fixed** — [D4](#d4) |
| U6 | the git common directory's refs: branches, tags, the default branch | each version's commits, the integrate merge, each release | each version commits to its own branch; the integrate merge runs under `merging` (`C:5626`); any other writer of one ref meets git's own ref lock files | **held** — [D5](#d5) closes the versions at once |
| U7 | the home queue and `.minions/cuts/` | `conduct.py cut` and the run | `fcntl.flock` on the queue's `lock` (`C:6703-6723`) | **held** |
| U8 | the run log `.minions/runs/<stamp>.md` | every thread's events | a `<stamp>.lock` folder taken by `mkdir` around each append (`C:2479-2506`) | **held** |
| U9 | the Codex window, read from the rollouts | each Codex worker's `mf.quota` line | none: `_quota` subtracts the shares a window moved while parallel workers also used it (`C:3957-3978`) | **deferred** — trigger: when a metric compares per-change Codex quota across versions that ran at once |

## Tests

The change adds the tests below, edits the expectations of those named after the table, and removes none.

| layer | file | test | does | why here |
|---|---|---|---|---|
| unit | `tests/test_converge.py` | `test_a_converge_script_runs_by_the_conductors_python` | `script("gate_check.py", "--change", "x")` equals `[sys.executable, <the script's path>, "--change", "x"]` and names no `uv` | the lowest layer that can fail for the argv (`T1`) |
| unit | `tests/test_converge.py` | `test_each_script_converge_starts_declares_no_dependencies` | each name `K` passes to `script()` has `dependencies = []` in its PEP 723 header, and the names include `gate_run.py`, `gate_check.py` and `plan_check.py` | the guard of [D1](#d1), read from source (`T1`) |
| integration | `tests/test_converge.py` | `test_two_converges_start_gate_check_at_once` | parallel threads, released by one barrier, run `script("gate_check.py", "--help")` with an empty `UV_CACHE_DIR`; both exit 0 and the cache holds no `environments-v2` | the race made a test; it proves no uv environment is built |
| integration | `tests/test_conduct.py` | `test_a_run_builds_each_pinned_scripts_environment_before_its_first_thread` | a fake `uv` on `PATH` records each `sync --script` with its time and the size of the worker-calls file: one record for each pinned script, in order, none overlapping, each before the first worker call | no lower layer reaches `Run.ship()`'s order (`T1`) |
| integration | `tests/test_conduct.py` | `test_a_failed_environment_build_halts_the_run` | the fake `uv` exits 1 with a stderr line: the log's `run` halt names the script and the line, and no worker starts | the halt of [D2](#d2) |
| integration | `tests/test_conduct.py` | `test_a_re_pin_builds_the_new_releases_environments` | `run()` with `_pin` swapped for a stub whose `move` says `pin: moved to v9.9.9` and whose `trees` names a temp skills folder only after `move` has been called: the fake `uv` records that folder's scripts, each after the `move` call | the seam of the re-pin |
| integration | `tests/test_corpus.py` | `test_a_corpus_run_holds_its_lock` | a case whose command tries `flock(LOCK_EX \| LOCK_NB)` on `{minions}/corpus.lock` exits 0 only when the lock is held; a link at that name is exit 2 | the lowest layer that reaches `run()` (`T1`) |
| end-to-end | `tests/test_conduct.py` | `test_three_versions_cut_built_converged_and_closed_at_once` | [D5](#d5), ten rounds | no lower layer runs versions at once (`T1`); no existing test queues three cuts and runs them together, and `test_a_queued_cut_is_cut_then_built` runs one (`T2`) |

Edited expectations: the fake host's `sandboxed` and the helpers that list the commands it ran, in `tests/test_converge.py`,
read a script's name as `Path(argv[1]).name` when `argv[0]` is `sys.executable` (F11). An autouse fixture `_uv_sync` of
`tests/test_conduct.py` puts a fake `uv` first on `PATH`: it records `sync --script` and exits 0, and runs the real `uv` for
every other argument, so no other test builds an environment.

End-to-end runs added: the ids `uv run pytest --collect-only -q tests/test_conduct.py -k three_versions` prints, one boot of
`_run_claude` each, on one executor. `I16` table: none removed.

## Dependencies

None.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| a uv without `uv sync --script` halts every run at its start | the halt names the script and uv's own stderr line, so the cause reads at once; the run never starts a worker on a broken cache |
| a cold cache and no network halts the run at its start for a script with a dependency | the run starts unsandboxed and online; the halt is at the start, never in a worker |
| a later edit gives a converge script a dependency | the guard test of [D1](#d1) goes red |
| this version's own converge can still draw the race ([D6](#d6)) | a halt on `Directory not empty` is rejoined; the next version runs the fix |
| a flock on `corpus.lock` blocks a second `make corpus` until the first ends | each case has `TIMEOUT_SECONDS`, so the wait is bounded |
| the audit's held rows rest on a read at the cut | the stress test of [D5](#d5) runs the shared resources at once, and each held row's lines are re-checked in the build ([tasks](tasks.md)) |

## Verdict

Build in phases, each green on its own: converge's scripts by `sys.executable` and the guard test; the environments built once
at a run's start and after a re-pin; the corpus lock and the stress test.
