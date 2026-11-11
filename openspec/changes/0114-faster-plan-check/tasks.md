# Faster plan check — tasks

The phases: what `plan_check.py` runs and keeps, the parallel runner and the group kill, then the deadline, the catch-up, the whole-suite flag and the docs. Each phase ends green.

## Progress

- [ ] 1 — plan_check.py: distinct commands, the gate's green record, the record by tree · hard
- [ ] 2 — The parallel runner and the group kill · hard
- [ ] 3 — The deadline, the catch-up, the whole-suite flag and the foreground · hard

## 1 — plan_check.py: distinct commands, the gate's green record, the record by tree

- [ ] 1.1 **HALT CHECK** `plan_check.py` holds the seams this phase changes ([D1](design.md#d1)).
  Verify: `git grep -n -e '^def check_verifies(' -e '^def passed(' -e '^TIMEOUT_SECONDS = ' -- skills/mf-converge/scripts/plan_check.py` prints a line for each.
- [ ] 1.2 In `skills/mf-converge/scripts/plan_check.py` add `Result` (exit, output, timed out), `run(command, root)`, which returns one, and `report(name, command, result)`, which returns the lines `rerun` returned; delete `rerun`, make `check_verifies` call `run` and `report` in its place, one command at a time, and make `passed`'s docstring name `report`'s rule ([D1](design.md#d1)).
  Verify: `git grep -n -w rerun -- skills/mf-converge/scripts/plan_check.py` prints nothing.
- [ ] 1.3 In `skills/mf-converge/scripts/plan_check.py` add `jobs(tasks, human, only)`, and make `check_verifies` take `only=None` and run each distinct command text once, judging its one result by each sub-task's own words ([D1](design.md#d1)); add `test_a_command_named_twice_runs_once` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k named_twice` exits 0.
- [ ] 1.4 In `plan_check.py` add `gate()`, which loads `gate_run.py` once by `runpy`, `gate_green()`, `is_pytest(argv)` and `bare_pytest(command)` as [D2](design.md#d2) says, and pass a bare `pytest` unrun when `gate_green()` holds; add `test_a_green_gate_record_passes_a_bare_pytest` to `tests/test_plan_check.py`: a stub `pytest` on `PATH` that exits 3 passes unrun on the record, and runs when its `Verify:` says it prints `1` or the dry run of `make -n gate` differs from the record's.
  Verify: `uv run pytest -q tests/test_plan_check.py -k green_gate_record` exits 0.
- [ ] 1.5 In `plan_check.py` add `names_revision(argv)` and `keyed(text, head)`, the key of [D3](design.md#d3): the command text, and `HEAD`'s sha too when `names_revision` holds; add `test_a_command_naming_a_revision_is_keyed_by_head` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k keyed_by_head` exits 0.
- [ ] 1.6 In `plan_check.py` add `store(tree)`, `keep(tree, key, result)` and `load(tree, key)`, and make `check_verifies` read `HEAD`'s sha once, read a kept result before a run and write the new ones after the batch, on a settled tree and never a timeout ([D3](design.md#d3)); add `test_a_result_is_kept_by_tree_and_reused` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k kept_by_tree` exits 0.

## 2 — The parallel runner and the group kill

- [ ] 2.1 In `skills/mf-converge/scripts/plan_check.py` add `CPUS` as `os.cpu_count() or 1` and `weight(argv)`: `CPUS` for a pytest command with a `-n`, `-n<N>`, `-nauto` or `--numprocesses` word, else 1 ([D4](design.md#d4)); add `test_a_pytest_with_n_takes_every_slot` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k takes_every_slot` exits 0, and `git grep -n -F cpu_count -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [ ] 2.2 In `plan_check.py` add `RUNNING`, the processes now running, and make `run` start its command through `Popen` in a session of its own, `start_new_session=True`, join `RUNNING` while it runs, and on a timeout kill the command's process group ([D5](design.md#d5)); add `test_a_timed_out_command_loses_its_process_group` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k loses_its_process_group` exits 0.
- [ ] 2.3 In `plan_check.py` make `run` start every command with `PYTEST_ADDOPTS` holding `-p no:cacheprovider` after the environment's own value ([D4](design.md#d4)); add `test_every_pytest_runs_without_the_cache_provider` to `tests/test_plan_check.py`.
  Verify: `uv run pytest -q tests/test_plan_check.py -k without_the_cache_provider` exits 0.
- [ ] 2.4 In `plan_check.py` add `schedule(work, root)`: it starts the commands in order, each when `weight` slots are free and a `make` also when no other `make` runs, and returns each result by key; `check_verifies` calls it for what no record answers and prints in `jobs` order ([D4](design.md#d4)); add `test_commands_run_side_by_side_and_print_in_task_order` to `tests/test_plan_check.py`, per the scenario *Commands run side by side*, with `CPUS` patched to 4.
  Verify: `uv run pytest -q tests/test_plan_check.py -k side_by_side` exits 0.
- [ ] 2.5 In `plan_check.py` make `main` install a SIGTERM handler that kills the process group of each process in `RUNNING` and exits 143, and restore the old handler when it returns ([D5](design.md#d5)); add `test_sigterm_ends_the_commands_running` to `tests/test_plan_check.py`, which runs the script as a subprocess.
  Verify: `uv run pytest -q tests/test_plan_check.py -k sigterm_ends` exits 0.

## 3 — The deadline, the catch-up, the whole-suite flag and the foreground

- [ ] 3.1 **HALT CHECK** `skills/mf-converge/scripts/converge.py` and `skills/mf-ship/scripts/conduct.py` hold the seams this phase changes ([D5](design.md#d5), [D8](design.md#d8)).
  Verify: `git grep -n -e '^def added(' -e '^def sandboxed(' -- skills/mf-converge/scripts/converge.py skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py` give `sandboxed` the parameter `timeout=None`: when it is not `None` the command starts in a session of its own, a thread watches it, and past the deadline, at once when it is 0 or less, the group gets SIGTERM, the output gets `sandboxed: timed out — killed after <timeout> s` and the exit is 124 ([D5](design.md#d5)); add `test_a_command_past_its_deadline_is_killed_with_its_group` to `tests/test_sandboxed.py`.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k past_its_deadline` exits 0.
- [ ] 3.3 In `conduct.py` give `sandboxed` the parameter `grace=5.0`, after which the group gets SIGKILL ([D5](design.md#d5)); add `test_a_command_that_ignores_sigterm_is_killed_after_the_grace` to `tests/test_sandboxed.py`.
  Verify: `uv run pytest -q tests/test_sandboxed.py -k ignores_sigterm` exits 0.
- [ ] 3.4 In `conduct.py` make `Run.sandboxed` pass `timeout` on ([D5](design.md#d5)); add `test_the_run_passes_a_deadline_to_the_sandbox` to `tests/test_conduct.py`, a command past its deadline exiting 124.
  Verify: `uv run pytest -q tests/test_conduct.py -k passes_a_deadline` exits 0.
- [ ] 3.5 In `skills/mf-converge/scripts/converge.py` give `Host.sandboxed` a `timeout` and make `sandboxed(context, argv, out)` pass `remaining(context)` ([D5](design.md#d5)); in `tests/test_converge.py` make `Host.sandboxed` take and record it, and add `test_a_sandboxed_command_gets_the_converge_deadline`.
  Verify: `uv run pytest -q tests/test_converge.py -k converge_deadline` exits 0.
- [ ] 3.6 In `skills/mf-converge/scripts/plan_check.py` make `main` take `--only <ids>`, each of the form `N.M` and anything else exiting 2, and `check` then pass `only` to `check_verifies`, over those sub-tasks whatever their boxes, and print its lines only ([D8](design.md#d8)); add `test_only_runs_the_named_sub_tasks` to `tests/test_plan_check.py`, per the scenario *Only the named sub-tasks*.
  Verify: `uv run pytest -q tests/test_plan_check.py -k only_runs_the_named` exits 0.
- [ ] 3.7 In `converge.py` make `added` keep its detection and, when a `Verify:` changed, run `plan_check.py --only` for those sub-tasks through `_captured`, exit 1 halting `verify failed — <ids>`, the distinct `N.M` subjects of its lines, and any other exit but 0, or an exit 1 naming none, halting `plan check: <lines>` ([D8](design.md#d8)); in `tests/test_converge.py` make `test_a_catch_up_judges_the_new_commits` set `host.exits["plan_check.py"]` and `host.printed["plan_check.py"]` where it set `host.exits["git"]`, drop that `git` reset, put the catch-up's own run first in its list of plan-check exits, and add `test_a_catch_up_runs_the_changed_verifies_in_one_plan_check`.
  Verify: `uv run pytest -q tests/test_converge.py -k one_plan_check` exits 0.
- [ ] 3.8 In `skills/mf-cut-change/scripts/cut_check.py` add `row_v5(change, plan)`, with `V5` in `ROWS` and in `check`'s `rows` ([D7](design.md#d7)); in `tests/test_cut_check.py` add its defect to `test_each_mechanical_row_fails_by_name`, and make the fixture whose `Verify:` is `uv run pytest -q -k widget` name `test_widget.py`, so it halts no row but `V2`.
  Verify: `uv run pytest -q tests/test_cut_check.py -k V5` exits 0.
- [ ] 3.9 In `skills/mf-cut-change/SKILL.md` Step 8 read `V1`–`V5` in the list of rows the script decides, and in the `Verify:` bullet `V1`–`V5` settle a search's sequence, its needles and a `pytest`'s test files ([D7](design.md#d7)).
  Verify: `grep -c -F V5 skills/mf-cut-change/SKILL.md` prints `2`.
- [ ] 3.10 In `skills/mf-converge/references/fix.md` the plan-check bullet says to run it `in the foreground`, and that it ends within 600 s ([D6](design.md#d6)).
  Verify: `git grep -n 'in the foreground' -- skills/mf-converge/references/fix.md` prints a line.
- [ ] 3.11 In `skills/mf-build/SKILL.md` Step 3.6 say to run the plan check `in the foreground`, within 600 s ([D6](design.md#d6)).
  Verify: `git grep -n 'in the foreground' -- skills/mf-build/SKILL.md` prints a line.
- [ ] 3.12 In `docs/decisions.md` D74's plan-check sentence reads `re-runs each ticked Verify: in parallel, passes a bare pytest on the gate's green record and keeps results by tree` in place of `re-runs each ticked Verify:` ([D9](design.md#d9)).
  Verify: `git grep -n 'keeps results by tree' -- docs/decisions.md` prints a line.
