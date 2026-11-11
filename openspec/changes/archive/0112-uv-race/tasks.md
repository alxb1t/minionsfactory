# uv race — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `K` is
`skills/mf-converge/scripts/converge.py`, `C` is `skills/mf-ship/scripts/conduct.py`. Inside a phase a sub-task's `Verify:` is
its own; only the phase's end is green.

## Progress

- [x] 1 — Converge starts its scripts by the conductor's Python · moderate
- [x] 2 — A run builds each pinned script's environment once · hard
- [x] 3 — The corpus lock and the stress test · hard

## 1 — Converge starts its scripts by the conductor's Python

- [x] 1.1 **HALT CHECK** The base starts converge's scripts by `uv`, as the design's [Context](design.md#context) reads it (F1).
  Verify: `git grep -n -F '"uv", "run", "--script"' -- skills/mf-converge/scripts/converge.py` prints a line.
- [x] 1.2 Add `test_a_converge_script_runs_by_the_conductors_python` and `test_each_script_converge_starts_declares_no_dependencies`
  to `tests/test_converge.py` ([Tests](design.md#tests)); the second reads each name `K` passes to `script()` from `K`'s source.
  Verify: `git grep -n -e 'def test_a_converge_script_runs_by_the_conductors_python' -e 'def test_each_script_converge_starts_declares_no_dependencies' -- tests/test_converge.py` prints a line for each.
- [x] 1.3 Add `test_two_converges_start_gate_check_at_once` to `tests/test_converge.py`: parallel threads released by one `threading.Barrier`
  run `script("gate_check.py", "--help")` with an empty `UV_CACHE_DIR` under `tmp_path`; both exit 0, and `environments-v2` is absent from it.
  Verify: `git grep -n 'def test_two_converges_start_gate_check_at_once' -- tests/test_converge.py` prints a line.
- [x] 1.4 In `K` change `script()` to [D1](design.md#d1): it returns `[sys.executable, str(HERE / name), *args]`, and its docstring says it runs a converge script by the conductor's Python.
  Verify: `uv run pytest -q tests/test_converge.py -k "conductors_python or declares_no_dependencies or two_converges"` exits 0.
- [x] 1.5 In `tests/test_converge.py` change the fake host's `sandboxed` and the helpers that list the commands it ran, each reading a script's name as
  `Path(argv[3]).name if argv[0] == "uv" else argv[0]`, to read it as `Path(argv[1]).name if argv[0] == sys.executable else argv[0]` (F11).
  Verify: `uv run pytest -q -m "not slow" tests/test_converge.py` exits 0.

## 2 — A run builds each pinned script's environment once

- [x] 2.1 **HALT CHECK** The base holds the seams of [D2](design.md#d2): the pin helper, the temp-folder step and the run's finish (F8, F9).
  Verify: `git grep -n -e '^def _pin(' -e '^def _fresh_tmp(' -e '^def run(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.2 **HALT CHECK** The installed uv builds a script's environment by `uv sync --script` (F6).
  Verify: `uv sync --script skills/mf-converge/scripts/gate_check.py` exits 0.
- [x] 2.3 Add the autouse fixture `_uv_sync` to `tests/test_conduct.py` ([Tests](design.md#tests)): a fake `uv` first on `PATH` records each `sync --script` argv with its start and end time and the size of the `FAKE_CALLS` file,
  exits as `FAKE_UV_EXIT` says, prints `FAKE_UV_STDERR` to stderr, and runs the real `uv`, found by `shutil.which` when the fixture runs, for any other argument.
  Verify: `git grep -n 'def _uv_sync' -- tests/test_conduct.py` prints a line.
- [x] 2.4 Add `test_a_run_builds_each_pinned_scripts_environment_before_its_first_thread`, `test_a_failed_environment_build_halts_the_run` and `test_a_re_pin_builds_the_new_releases_environments`
  to `tests/test_conduct.py` as [the Tests table](design.md#tests) says.
  Verify: `git grep -n -e 'def test_a_run_builds_each_pinned_scripts_environment_before_its_first_thread' -e 'def test_a_failed_environment_build_halts_the_run' -e 'def test_a_re_pin_builds_the_new_releases_environments' -- tests/test_conduct.py` prints a line for each.
- [x] 2.5 In `C` add `SKILLS_DIR = Path(__file__).resolve().parents[2]`, beside the existing `SKILLS` table of host folders, which stays, `SYNC_SECONDS = 600`, `_pinned_scripts(skills)` and `_sync_scripts(primary, roots)` to [D2](design.md#d2); the run of `uv` takes `timeout=SYNC_SECONDS`.
  Verify: `git grep -n -e '^SYNC_SECONDS = ' -e '^def _pinned_scripts(' -e '^def _sync_scripts(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.6 In `Run.ship()` of `C` call `_sync_scripts` right after the `_fresh_tmp` step, its roots `SKILLS_DIR` and each key of `_pin()["trees"]()`, and halt on a reason as the `_fresh_tmp` step does.
  Verify: `uv run pytest -q tests/test_conduct.py -k "builds_each_pinned or failed_environment_build"` exits 0.
- [x] 2.7 In `run()` of `C`, in its `finally`, call `_sync_scripts` when `pin["move"](mark)` returns a line that starts `pin: moved to`, its roots each key of `pin["trees"]()`; print `run: <why>` on a reason and change no exit.
  Verify: `uv run pytest -q tests/test_conduct.py -k re_pin_builds` exits 0.

## 3 — The corpus lock and the stress test

- [x] 3.1 **HALT CHECK** The base holds the corpus runner's `run()` and its per-case delete the lock guards (F10).
  Verify: `git grep -n -e '^def run(' -e 'shutil.rmtree(out' -- scripts/corpus.py` prints a line for each.
- [x] 3.2 **HALT CHECK** Each guard the audit's held rows name stands at the base ([the audit](design.md#the-shared-state-audit)).
  Verify: `git grep -c -e 'debt.lock' -e 'with self.merging:' -e 'fcntl.flock' -- skills/mf-converge/scripts/converge.py skills/mf-ship/scripts/conduct.py` prints a count for each file.
- [x] 3.3 Add `test_a_corpus_run_holds_its_lock` to `tests/test_corpus.py` ([Tests](design.md#tests)): a case whose command tries a non-blocking exclusive `flock` on `{minions}/corpus.lock` and exits 0 only when it is refused; a link at that name is exit 2.
  Verify: `git grep -n 'def test_a_corpus_run_holds_its_lock' -- tests/test_corpus.py` prints a line.
- [x] 3.4 In `scripts/corpus.py` add a context manager `_locked(minions)` to [D4](design.md#d4) and take it in `run()` after the link check and the creation of the `minions` folder, around every case.
  Verify: `uv run pytest -q tests/test_corpus.py` exits 0.
- [x] 3.5 Add `test_three_versions_cut_built_converged_and_closed_at_once` to `tests/test_conduct.py` as [D5](design.md#d5) says, `@pytest.mark.slow`, parametrized over `range(10)`; each round builds its repository under its own `tmp_path`.
  Verify: `uv run pytest -q --collect-only tests/test_conduct.py -k three_versions` exits 0.
- [x] 3.6 Run the stress test. A round that halts names a resource the audit lacks: add its row to [the audit](design.md#the-shared-state-audit), and fix it by a lock or a name, or defer it with its trigger as [D3](design.md#d3) says.
  Verify: `uv run pytest -q -n auto tests/test_conduct.py -k three_versions` exits 0.
- [x] 3.7 Run the flaky test in a row: its node id repeated on one command line, with `--keep-duplicates`.
  Verify: `uv run pytest -q --keep-duplicates tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back tests/test_conduct.py::test_a_rejoined_dependency_brings_its_chain_back` exits 0.
- [x] 3.8 Check the audit names its table for the acceptance search.
  Verify: `git grep -n 'shared' -- openspec/changes/0112-uv-race/design.md` prints a line.
