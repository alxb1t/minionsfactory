# Test cost — design

How the suite stops repeating work: which tests go, what carries their proofs, and how the marks are found. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The tests audit finds these costs in the suite. Each is in a test file; none is in a script.

```
D1  test_three_versions_…[0..9]     ten identical rounds; the autouse `_uv_sync` fixture
                                    (tests/test_conduct.py) fakes the build they were made to race
D3  _conduct() = runpy.run_path     the conductor compiled on every call
D4  slow tests with no `slow` mark  `make check` runs what `T1` says it leaves to the gate
C4  duplicates                      a test whose proof another test holds
B5  waits that assert nothing       a loop and a helper that go on when the line never came
```

`pyproject.toml` declares the marker (`slow: over 5 s; make check leaves it to the gate`) and `Makefile`'s `check` runs `-m "not slow"`. `gate` runs every test. The `isolated_home` fixture of `tests/conftest.py` stays as it is.

## Goals / Non-Goals

**Goals**

- Each test that proves something keeps proving it; each proof that goes is carried, in the `## Tests` table.
- `make check` skips every test over 5 s.
- A wait that misses its line fails there, not in a later test.

**Non-Goals**

- A script edited. No decision, requirement or behaviour changes.
- The other costs of the audit: full flows run for one assert, the converge `run()` reload, the viewer and integrate scenarios. They ride with the region's version ([proposal](proposal.md#not-in-this-change)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The three-versions test runs a single round | the fixture fakes the build, so a second round repeats the first; one round is still the only test of three versions at once (brief Q35) | the repeated rounds behind an opt-in marker: a draw nobody runs |
| [D2](#d2) | `tests/conduct_load.py` compiles the conductor once; each call runs the code into a fresh module and returns a copy of its names | isolation needs a fresh dict, not a fresh compile | a cached dict: tests share state · a copy of the helper in each test file |
| [D3](#d3) | The `slow` marks come from a durations run of the build, at the 5 s of `T1`, and only the tests it lists are marked | the audit's figures are estimates on a loaded machine; the build's own run is the evidence (brief Q35) | cutting each test under 5 s first: that is the audit's D2, left out |
| [D4](#d4) | A duplicate is deleted or merged as the `## Tests` table says; a merge moves into the survivor each line it lacks | no proof goes (`T5`) | deleting on the audit's word alone: a survivor may lack a line |
| [D5](#d5) | `_when_logged` takes `seconds` (60 by default) and raises `TimeoutError` when its line is still missing; the 30 s loop asserts after it | a missed line then fails at its own test | a longer wait: it hides the miss |
| [D6](#d6) | The D5 of the archived `0112-uv-race` design is corrected in place | the record says what held; it says the rounds make a draw a test, and the fixture shows they do not | a note in this change alone: the archive stays wrong |

### D1

`test_three_versions_cut_built_converged_and_closed_at_once` is `@pytest.mark.slow` and parametrized over `range(10)`. `attempt` is read once more, in an assert's message. The change drops the parametrization and the parameter, and the message reads `call`. `slow` stays: one round is still over 5 s.

The `_uv_sync` fixture replaces each `uv sync --script` with a fake that exits 0, so no round builds an environment, and the race that the rounds sampled never runs. The race's fix stays held by its own tests, `test_a_run_builds_each_pinned_scripts_environment_before_its_first_thread` and its neighbours.

### D2

`tests/conduct_load.py` holds `_SCRIPT`, the path of `skills/mf-ship/scripts/conduct.py`, and `_CODE`, its compiled source. `conduct()` does what `runpy.run_path` does, but compiles nothing:

```
module = types.ModuleType("<run_path>")          name and __file__ as run_path sets them
module.__file__ = str(_SCRIPT)
sys.modules["<run_path>"] = module               a frozen dataclass reads it; the old entry comes back
exec(_CODE, module.__dict__)
return dict(module.__dict__)                     a copy, as run_path returns
```

`conduct.py` defines `@dataclass(frozen=True)` classes, and a dataclass looks its module up in `sys.modules`, so the entry stands for the call, as `runpy` leaves it. `conduct.py` reads no `sys.argv`, so `runpy`'s change to `sys.argv[0]` is not carried. `tests/test_conduct.py` and `tests/test_sandboxed.py` import it as `_conduct`, so no call site changes.

A test, `test_each_conduct_load_is_a_fresh_module`, holds the property the sharing rests on: two loads return different `Run` classes, and `"<run_path>"` is not left in `sys.modules`. Its twin, per `T6`: the red run with `conduct()` returning one cached dict goes in the phase's commit body.

### D3

The build runs `uv run pytest -q -n auto -m "not slow" --durations=0 --durations-min=5 tests/test_*.py`. It prints, under `slowest durations`, one line per setup, call or teardown of 5 s or more.

Each test named there gets `@pytest.mark.slow` above its `def`, the other decorators kept. A second run lists none.

A marked test is not changed: the gate runs it. `make check` stops running it, which is the point of `T1`.

### D4

Each row of the `## Tests` table is one removal. A test the table deletes is mapped to the test that keeps its assertions. Where the survivor lacks a line of the deleted test, the line moves into the survivor, as the row says; no deleted assertion is dropped.

A test that holds a guard keeps its twin (`W5`): the survivors are the guards' tests already. A survivor that comes out over 5 s after the merge carries `slow`, found by the same durations run (phase 4's last task).

### D5

`_when_logged(root, said, act, hold)` waits 60 s for each of `said` in the run log, then runs `act`, whether the line came or not. After the change it is `_when_logged(root, said, act, hold, seconds=60.0)`.

At the deadline, a line still missing leaves `act` unrun and makes `hold` as before, so the run is not left waiting. `join()` then raises `TimeoutError` naming `said`.

The loop in `test_a_dependent_waits_while_its_dependency_works` polls `waiting()` for 30 s and goes on. `assert waiting()` follows it. With the log line dropped, the audit saw the test pass; the phase's commit body names that red run (`T6`).

A test that goes red once `_when_logged` raises named a line that never came, which is a fault of its own: phase 5's check halts the build on it.

### D6

The fifth decision of `openspec/changes/archive/0112-uv-race/design.md` and the `## Tests` row that cites it say ten rounds. After the change they say one round, and name the fixture as the reason the rounds repeated.

The archived `tasks.md` stays: it records what was built.

## Tests

This change removes tests and adds two. Counts come from `uv run pytest --collect-only -q tests/test_*.py`, its last line.

`tests/conduct_load.py` is a helper, no test: `tests/test_conduct.py` and `tests/test_sandboxed.py` load the conductor through it.

| layer | added | removed |
|---|---|---|
| unit | `test_each_conduct_load_is_a_fresh_module`, `test_a_log_line_that_never_comes_fails_the_wait` | the duplicates of the table below |
| end-to-end | none | nine of the ten rounds; the full run of each of the lone-dependent and later-version tests |

Before: 709 tests collected. After: 694: nine rounds and eight deleted tests removed, two added. `uv run pytest tests/test_conduct.py -q -k three_versions --collect-only` collects one test, not ten.

No new end-to-end run: `T1` puts each added test at the unit layer, `T2` extends the tests that already reach the state, and `T3` holds because no merged step leans on an earlier one.

**The `I16` table.** Removed or merged, per `T5`:

| removed or merged | carried by | what it held |
|---|---|---|
| `test_a_lone_dependent_is_blocked_by_its_halt` (`tests/test_conduct.py`) | `test_run_halts_on_a_human_phase`, whose `lone` case gains the dependents `0002-marks`, `0003-more` and the log lines the deleted test asserted; `test_a_halted_dependency_blocks_a_chain` holds the blocked lines and report | a human-phase halt blocks its chain, and no worker starts |
| `test_a_later_version_ships_past_a_halted_one` (`tests/test_conduct.py`) | `test_a_later_version_halts_and_the_earlier_ships`, and the first case of `test_run_halts_on_a_human_phase` | a halted version leaves an independent version to release, and the closing line says `needs … a fix` |
| `test_a_forged_release_is_not_pushed` (`tests/test_conduct.py`) | `test_a_plain_commit_on_main_is_not_pushed`, which gains a second `halts_on` after moving `refs/remotes/origin/main` to `main` | a plain commit, and the same with the remote-tracking ref moved, halt and push nothing |
| `test_another_branch_moving_ends_the_reuse_of_a_result` (`tests/test_plan_check.py`) | `test_a_wrapped_git_command_is_not_reused_once_a_branch_moves`, whose `commands` gain `git diff --quiet other HEAD` | a result kept for a command is not reused once another branch it reads moves |
| `test_a_git_grep_of_another_branch_is_not_reused_once_it_moves` (`tests/test_plan_check.py`) | the same survivor, whose `commands` gain `git grep -q LEGACY other -- src/legacy.py` and whose `other` moves onto the commit of the empty tree | the same, for a `git grep` of another branch |
| `test_a_dash_prefix_halts` (`tests/test_gate_check.py`) | `test_a_planned_dash_the_task_does_not_quote_halts`, whose first step adds `-echo b` the task does not quote | an added `-` recipe line halts |
| `test_an_ignore_target_halts`, `test_makeflags_ignore_halts` (`tests/test_gate_check.py`) | the same test, whose `lines` gain `.IGNORE:` and `MAKEFLAGS += -i` | an added `.IGNORE:` line and an added `MAKEFLAGS += -i` line each halt |
| the step "a link swapped in after any check by name" of `test_a_log_out_of_shape_is_not_stamped` (`tests/test_stamp.py`) | the step before it, "no stamp is written through a link": `stamp.py` reads through one `O_NOFOLLOW` open and never calls `Path.is_symlink`, which the removed step patches | a stamp through a link is refused |
| the Codex run of `test_a_codex_fixers_prompt_names_its_attribution` (`tests/test_converge.py`) | `test_a_codex_fixer_runs_through_host_fix_and_halts_at_a_limit`, whose first run gains the prompt assertion `Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>`; the test stays, renamed `test_a_claude_fixers_prompt_names_its_attribution`, for the Claude fixer | a Codex fixer's prompt names its attribution line |

## Dependencies

None.

## Risks / Trade-offs

- **A merge that loses a line.** [D4](#d4) moves each line the survivor lacks; the build's first check of phase 4 halts when a test the table names is not at `HEAD` by that name.
- **A test over 5 s after a merge, or after the compile of [D2](#d2) moved it under 5 s.** The first stays unmarked until phase 4's last task finds it. The second stays marked: a marker the gate ignores costs nothing.
- **`_when_logged` raising turns a latent miss red.** Phase 5's first check runs the whole file; a red there is a line that never came, and the plan halts for the person.
- **`tests/test_converge.py` and `tests/test_gate_check.py` are shared with `0126-station-guards`.** They add cases beside the tests deleted or edited here; a textual conflict is the integrate station's.
- **Editing an archive.** [D6](#d6) corrects one decision's text and one table row; no task of the archive changes.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). No script is edited.
