# Faster plan check — design

The plan check runs its commands side by side, passes a bare `pytest` on the gate's green record, keeps results by tree and kills what it times out. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`plan_check.py` re-runs each ticked `Verify:` command in task order, one at a time, as argv with no shell, each under a 600 s timeout that kills only the direct child. See [proposal](proposal.md) for what that cost 0110.

Most of the time was the whole-suite `pytest` lines; the gate runs the same suite under `-n auto`, in far less. `gate_run.py` already records a green gate by the settled tree and the hash of `make -n gate`, in `.minions/gate/<tree>`.

Callers: the build's close and the fixer run the script through their own Bash tool, whose foreground limit is 600 s. Converge's Step 7, through `sandboxed()`, which has no deadline, runs it. `converge.py` and `cut_check.py` load `subtasks`, `verify_of`, `commands`, `tokens`, `passed`, `phases`, `check_corpus` and `Stop` from it by `runpy`.

The code, read at `HEAD`:

```
plan_check.py   TIMEOUT_SECONDS, Task, Command, subtasks, commands, tokens, verify_of,
                rerun(name, command, root) → replaced by run and report,
                passed(command, code, stdout),
                check_verifies(tasks, human, root), check(change, base), main()
gate_run.py     records(), settled_tree(), dry_run(), read_record(path)
converge.py     Host.sandboxed, sandboxed(context, argv, out), _captured, planned, added
conduct.py      sandboxed(argv, cwd, trees, out), Run.sandboxed
cut_check.py    ROWS, row_v1…row_v4, check()
```

The hazards of running side by side: every `pytest` writes `.pytest_cache`, `make corpus` rewrites `.minions/corpus/`, and a `pytest` with `-n auto` takes every core. No `Verify:` reads what another writes.

## Goals / Non-Goals

**Goals:** a plan check whose wall time is the longest command, not the sum; a command that runs once; a green gate that stands for the tests it ran; a hung command that ends with its group.

**Non-Goals:** a faster gate; a compiled rewrite; a per-test cache; a change to the output the requirement fixes, save that the lines come in task order whatever order the commands finish in.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | each distinct command runs once a check; each sub-task's own words judge its result | 0108 re-ran one `pytest` line at each sub-task that named it | a run per sub-task |
| [D2](#d2) | a `pytest` `Verify:` that wants only `exits 0`, and names only test paths and nodes that exist, with no option but `-q`, `-v`, `-x` or `-s`, passes unrun on the gate's green record for the same tree and dry run | the gate runs every test, slow ones too; a subset of a green suite passes, and named paths and nodes that exist prove the subset is not empty | running the subset again; vouching for a `-k` or `-m` selection the gate's run never proved selects a test |
| [D3](#d3) | a result is kept by command, `HEAD` and every ref in `.minions/plan-check/<tree>/`, on a settled tree only | re-run only what changed; no reading of a command's words proves it reads no ref | a record by sub-task; a record on an unsettled tree; the refs in the key only of a command whose words name a revision or `git` |
| [D4](#d4) | the rest run in parallel, one slot for each core; `-n` alone, `make` one at a time, `-p no:cacheprovider` for every `pytest` | the person: every core; the cache dir and `.minions/corpus/` are shared | a fixed slot count; one worker for every `pytest` |
| [D5](#d5) | a timeout kills the command's process group; SIGTERM ends the running groups; `sandboxed()` takes a deadline | orphans hold cores; closes debt `0108·S4` | killing the direct child only |
| [D6](#d6) | the fixer and the build's close run the plan check in the foreground, within 600 s | no more polling of a check that takes minutes | a background run with a poll |
| [D7](#d7) | `cut_check.py` row `V5` flags a `pytest` `Verify:` naming no test path | the whole suite is the gate's; caught at the plan | a runtime refusal in `plan_check.py` |
| [D8](#d8) | a catch-up's re-run of the added `Verify:` lines goes through `plan_check.py --only` | the re-run halted on a `**HALT CHECK**` the check skips, and ran serially | a second runner in `converge.py` |
| [D9](#d9) | `docs/decisions.md` edits D74's plan-check sentence | A7: a decision in force is edited where it lives | a new decision |
| [D10](#d10) | hypothesis **H20** guards the move | a measure, held by the person's ledger | none |

### D1

`jobs(tasks, human, only)` returns the `(sub-task name, Command)` pairs a check judges, in task order and then command order: a ticked sub-task, a `**HALT CHECK**` apart, a `**HUMAN` phase apart, a command naming `plan_check.py` apart. With `only` it takes the named sub-tasks, ticked or not. `check_verifies` runs each distinct command text once and judges that result against each pair's own `Command`, whose `nothing` and `count` differ between sub-tasks; a fail prints the lines the replaced `rerun` printed.

### D2

`gate_green()` loads `gate_run.py` by `runpy` from `plan_check.py`'s own folder, as `converge.py` loads its siblings, once a check and only when a bare pytest is among the jobs. It holds when `settled_tree()` is not `None` and `read_record(records() / tree)["dry"]` equals `dry_run()`; a `Stop` of `gate_run.py`, or a timeout there, makes it `False` and never a crash.

A **pytest command** is one whose argv starts `pytest`, `uv run pytest` or `python -m pytest`; `is_pytest(argv)` reads it for this decision, for [D4](#d4) and, through `plan_check.py`'s names, for `V5` of [D7](#d7). A word `pytest` elsewhere, as in `git grep -e pytest`, makes no pytest command.

A **bare pytest** is a pytest command whose `Command` has no `count` and no `nothing`: its `Verify:` says it exits 0 and no more. It passes unrun when `gate_green()` holds and every word after its pytest prefix is one of `-q`, `-qq`, `-v`, `-vv`, `-x` or `-s`, or an operand that is an existing test module, a file named `test_*.py` or `*_test.py` that the repo's `testpaths` reach, each of whose `::` nodes is a `test…` `def` or a `Test…` `class` of that file, a `[` parameter id never among them. Any other word runs it, a directory, a file that is no test module and a node that is no test among them: a `-k`, `-m` or `--deselect` selection, which the gate's run does not prove selects a test, and any other option, such as `-c` or `-p`, which can change what pytest collects. A `-k` that selects nothing exits 5 run alone, and so fails here: the plan check exists to catch a ticked `Verify:` that a later task broke, which the build's run before the tick cannot. Decided by the supervisor under the person's delegation, 2026-11-11, on adversarial card S1.

**Collection proves it, not the text.** A bare pytest passes unrun only when, besides the above, the same argv with
`--collect-only -q` appended exits 0 and prints at least one collected test; any other result runs the command. pytest
itself then settles a node's ancestry, a parameter id, a file whose tests moved and a selection: the textual checks
cannot, as rounds 1–5 found one case after another. The collection runs under the same deadline and group kill as any
command and takes seconds. Re-planned by the planner under the person's delegation, 2026-11-11: S1 returned
with a new case of one invariant, a re-plan and not a grant.

### D3

The store is `records().parent / "plan-check" / <tree>/`, beside `gate` in the primary's `.minions`. A file is named by the sha256 of the **key**: the command text, then after a newline `HEAD`'s sha and every ref's, as `git for-each-ref` prints them. Every command is keyed so, whatever its words: no reading of a command, a shell's body or a script it names decides whether it reads a ref, so another branch moving ends every reuse. It holds JSON, `{"exit": <code>, "output": <text>}`, which `passed()` reads again.

**The refs key every command, not the text's guess.** Rounds 1–4 of adversarial card S2 widened a textual reading of what reads git one wrapper at a time — a shell, a script file, a script that delegates, a shell's inline body — each round finding the next, the shape [D2](#d2) ended for S1; a closed list of tree-only programs kept by the text alone was rejected, as what it could keep, `grep`, `git grep` and `ruff`, takes milliseconds, while `pytest` and `make` run the tree's own code. Re-planned by the supervisor under the person's delegation, 2026-11-11, on the rescue's diagnosis and the card's Fix.

`check_verifies` reads `HEAD`'s sha and the refs once, reads results before a run, and writes them after the batch ends, only when `settled_tree()` still equals the tree the check began on; a timed-out command is never written. A store that is a link keeps nothing, as `write_record` does. An unsettled tree — the fixer's before its commit — reads and writes none.

### D4

`CPUS = os.cpu_count() or 1` is the slot count. `weight(argv)` is `CPUS` for a pytest command with a `-n`, `-n<N>`, `-nauto` or `--numprocesses` word, and 1 for the rest. The dispatcher starts the commands strictly in order: a command starts when enough slots are free, and a `make` also when no other `make` runs, and one that waits holds back every later command, so a `pytest` with `-n` runs alone.

Each command runs with `PYTEST_ADDOPTS` set to `-p no:cacheprovider` after any value the environment holds. Results are held by key, and the lines print in the order `jobs` gives, whatever order the commands finish in. The output the requirement fixes — `exited <n>`, `printed other than its Verify: says`, `timed out`, the first `  | ` output lines — does not change.

### D5

`run(command, root)` starts the command in a session of its own, `start_new_session=True`, so its group is its pid, and holds the process in `RUNNING` while it runs. On timeout `os.killpg(pid, SIGKILL)` ends the group, and the result is `timed out`. `main` installs a SIGTERM handler that kills the group of each process in `RUNNING` and exits 143, and restores the old handler when it returns, so a check that `sandboxed()` terminates leaves no orphan.

`sandboxed(argv, cwd, trees, out=None, timeout=None, grace=5.0)` in `conduct.py` starts its command in a session of its own and, when `timeout` is not `None`, watches it from a thread. Past the deadline, at once when it is 0 or less, the group gets SIGTERM and, after `grace` seconds, SIGKILL; the output gets `sandboxed: timed out — killed after <timeout> s`, the timeout as given, and the exit is 124. `Run.sandboxed` and `Host.sandboxed` take the same `timeout`, and `converge.sandboxed` passes `remaining(context)`, so a card's command or a gate holds converge no longer than its own deadline. A group gone, or one this process may not
signal — the release's sandbox refuses `os.killpg` — ends the watch: it has nothing left to end, and the thread never
dies on the refusal (`075d4a0`, after the release's sandboxed gate missed that line).

### D6

`skills/mf-converge/references/fix.md` and `skills/mf-build/SKILL.md` Step 3.6 say to run the plan check in the foreground, and that it ends within 600 s, the Bash tool's limit. The words about polling a background run, where a caller kept them, are dropped.

### D7

Row `V5` of `cut_check.py` halts a sub-task whose `Verify:` holds a pytest command, as [D2](#d2) reads it, with no test path: a word that ends `.py`, holds `::`, or is a path with a name after its last `/`. `-m "not slow"` alone, a bare `pytest` and `tests/` alone each name none. The halt line is `<sub-task>: <command> names no test file`, and the row runs at the cut only, the plan check itself refusing nothing.

### D8

`converge.added` keeps its detection — the sub-tasks whose `Verify:` the range adds or rewords — and, when any changed, runs `plan_check.py --change <id> --base <base> --only <ids>` through `_captured` in place of its loop. Exit 1: halt `verify failed — <sub-task ids>`, the distinct `N.M` subjects of the `plan: <id> —` lines, in order; any other exit but 0, a SIGTERM end among them, and an exit 1 that names no such subject: halt `plan check: <lines>`. `--only` takes ids of the form `N.M`, checks nothing but the `Verify:` commands, and shares the runner, the gate record and the store.

Unticked sub-tasks are run, as the loop ran them. A `**HALT CHECK**`, a `**HUMAN` phase and a command naming `plan_check.py` are skipped, which ends the halt 0110's amend round met on a `**HALT CHECK**` whose premise its own phase replaced. Decided by the planner under the person's delegation.

### D9

`docs/decisions.md` D74's sentence reads that `plan_check.py` re-runs each ticked `Verify:` in parallel, passing a bare `pytest` on the gate's green record and keeping results by tree. No new id is taken: the choice refines how D74's check runs, and the requirement in `openspec/specs/sdd/spec.md` carries the rest, folded at release. The release deletes debt card `0108·S4`.

### D10

The person's ledger measures **H20**: the plan check of a version of 0110's size, at the build's close and at Step 7, where the tree is settled, runs in at most 2 min on this machine's cores, against about 10 min at `HEAD`. A miss that repeats reopens [D4](#d4) and [D2](#d2) as a new decision. No task: the ledger is outside this repository.

## Tests

All new tests are unit tests at the lowest layer ([T1](../../../skills/mf-cut-change/SKILL.md#rules-for-tests)): a scratch repository under `tmp_path`, as `tests/test_plan_check.py` already builds, or the fake `sandbox-exec` of the shared fixtures. No end-to-end run is added, and none is deleted or merged.

| file | added | by |
|---|---|---|
| `tests/test_plan_check.py` | `test_a_command_named_twice_runs_once`, `test_a_green_gate_record_passes_a_bare_pytest`, `test_a_result_is_kept_by_tree_and_reused`, `test_a_command_naming_a_revision_is_keyed_by_head` | [D1](#d1), [D2](#d2), [D3](#d3) |
| `tests/test_plan_check.py` | `test_a_pytest_with_n_takes_every_slot`, `test_commands_run_side_by_side_and_print_in_task_order`, `test_every_pytest_runs_without_the_cache_provider` | [D4](#d4) |
| `tests/test_plan_check.py` | `test_a_timed_out_command_loses_its_process_group`, `test_sigterm_ends_the_commands_running`, `test_only_runs_the_named_sub_tasks` | [D5](#d5), [D8](#d8) |
| `tests/test_sandboxed.py` | `test_a_command_past_its_deadline_is_killed_with_its_group`, `test_a_command_that_ignores_sigterm_is_killed_after_the_grace` | [D5](#d5) |
| `tests/test_conduct.py` | `test_the_run_passes_a_deadline_to_the_sandbox` | [D5](#d5) |
| `tests/test_converge.py` | `test_a_sandboxed_command_gets_the_converge_deadline`, `test_a_catch_up_runs_the_changed_verifies_in_one_plan_check` | [D5](#d5), [D8](#d8) |
| `tests/test_cut_check.py` | a defect for `V5` in `test_each_mechanical_row_fails_by_name` | [D7](#d7) |
| `tests/test_plan_check.py` | in `test_a_green_gate_record_passes_a_bare_pytest`, a `-k` selection, a `-m` selection and a `-c` option that run on a green record | [D2](#d2) |
| `tests/test_plan_check.py` | `test_a_wrapped_git_command_is_not_reused_once_a_branch_moves` | [D3](#d3) |

The change turns existing tests red, and the tasks mend them with the code:

- `tests/test_converge.py`'s `Host.sandboxed` takes `timeout`, or every converge test calls a fake that refuses the new keyword.
- `test_a_catch_up_judges_the_new_commits` sets `host.exits["git"]` to fail an amended `Verify:`; it sets `host.exits["plan_check.py"]` and prints the failing line instead, and its later `[0, 1, 0]` list of plan-check exits gains the catch-up's own run.
- `V5` halts the fixture of `tests/test_cut_check.py` whose `Verify:` is `uv run pytest -q -k widget`: it names a test file.
- Each test of `tests/test_plan_check.py` that edits `tasks.md` leaves the tree unsettled, so no record is read or written: the existing cases hold as they are.
- `test_a_result_is_kept_by_tree_and_reused` expects an empty commit on the same tree to re-run the `git rev-parse` command alone; under [D3](#d3)'s key by every ref the counted `sh -c` command runs again too, and its counts of runs and kept files follow.
- `test_a_command_naming_a_revision_is_keyed_by_head` and `test_a_script_file_that_reads_git_is_keyed_by_head` expect `printf 1`, `ruff check .`, `git ls-files src`, `sh plain.sh` and `sh loop.sh` keyed by the text alone; under [D3](#d3) each is keyed by `HEAD` and the refs too.

## Dependencies

None.

## Risks / Trade-offs

- Any ref moving — another version's commit, a fetch — ends every kept result, so a check re-runs its unvouched commands: the `grep` lines in milliseconds, a `-k` pytest in seconds, side by side under [D4](#d4). A plan check that misses H20 on it reopens [D3](#d3), per [D10](#d10).
- A kept result can be stale when a `Verify:` reads an ignored file, a run folder among them. The key is the tree, which ignored files do not enter; a `Verify:` that reads run data is a defect of that plan.
- Most `pytest` `Verify:` lines name a `-k` selection, so [D2](#d2) runs them: each its own file's tests, side by side, seconds apiece against the whole-suite runs row `V5` keeps out of a plan. A plan check that misses H20 on them reopens [D2](#d2), per [D10](#d10).
- A plan whose commands together outlast the Bash tool's foreground limit is cut off at 600 s. Row `V5` and the record keep the usual plan far below it; the trigger to revisit is a plan check that halts on that limit.
- The fixer runs the check on an unsettled tree, so [D2](#d2) and [D3](#d3) do not fire there; its time falls to [D1](#d1), [D4](#d4) and row `V5`.
- A grandchild that starts its own session escapes the group kill. The plan's commands are `git`, `pytest`, `ruff`, `make` and `uv`, none of which do.

## Verdict

Ready: every file the phases edit exists at `HEAD`, every behaviour is a function with a seam in an existing test file, and no decision of the brief is left open. The decision [D8](#d8) is the planner's, under the person's delegation; the cutter's `C1`, which fixes what a pytest command is, and `C2`, which fixes the deadline's reading and the catch-up's exits, are the others to read.
