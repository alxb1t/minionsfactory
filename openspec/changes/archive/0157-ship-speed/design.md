# Ship speed — design

The plan check trusts the gate's green run for more of the pytest `Verify:` lines, judges in groups so a cheap failure ends it early, runs a quick mode after each phase and in the fixer, and a verify file that says clean beside a blocking card not closed goes to a rewrite worker, then halts. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`plan_check.py` re-runs each ticked `Verify:` as argv. A `pytest` with `-n` takes every slot, so each runs alone, in task order, and a cheap `git grep` listed after one waits for it. Every command runs to the end: a failure that shows at once still waits for every long run.

The gate's green record vouches only for a bare `pytest`: quiet options and test modules. The plans of the refactoring series write `-n auto` and `-k <test>`, so the record vouches for almost none of them, and each such command runs for real at the close and after each fix. A rescue's amend of `tasks.md` gives a new tree, so the whole check runs again.

The conductor's phase check reads the boxes and the tree and runs no `Verify:`. The first full run of every ticked `Verify:` is the close's, so a later phase that breaks an earlier search is found at the close. The fixer runs the whole check on a tree the gate has not judged, so nothing is vouched and nothing is kept.

Converge counts a blocking card `fixed` as open. The conductor counts only `open`. A verify file that says clean with `open_blocking: 0` beside a card left `fixed` therefore sends the card to a fixer with nothing to fix, burns a round, and meets the cap, where the conductor reads no open card and refuses the grant.

## Goals / Non-Goals

**Goals**

- The gate's green run stands in for a pytest `Verify:` that expects exit 0, with `-n` and `-k`.
- A failure a cheap check finds ends the check before a long run, and is found at its phase.
- The fixer's order and the script's agree: quick before the commit, whole once after the gate.
- A slip of one word in a verify file costs one rewrite worker and no round.

**Non-Goals**

- The gate's own run time, the fixer's view of coverage, a lighter gate at the release, the cache's expiry, and a gate skipped on an amend. See [proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | With the gate green at the tree, a pytest `Verify:` that expects exit 0 passes unrun also with `-n` or `--numprocesses` and `-k`, with their values, over the test files it names, once its collection finds a test | `-n` and `-k` are what the plans write; the gate's run proved the whole suite | vouching a count, `prints nothing` or another exit; vouching `-m`, `-c` or `--deselect` |
| [D2](#d2) | The check judges in the groups **reads**, **quick** and **long**, in that order, and a failed group ends the check | a failure known in a second is not held behind pytest | fail-fast inside the long group; one schedule reordered |
| [D3](#d3) | `plan_check.py --quick` judges the quick group alone, and is refused beside `--only` | one mode serves the phase check and the fixer | a flag on `--only`; a second script |
| [D4](#d4) | The conductor runs `--quick` after each phase but the last, beside `gate_built`, over every ticked sub-task; a failure is the phase's check failing | a later phase that breaks an earlier search is found at its phase | a run inside `_check_phase`, which `check` calls read-only and more than once; collecting at the close alone; a worker that runs it |
| [D5](#d5) | The fixer runs `--quick` before its commit, and the script runs the whole check after the fix's gate, at the freeze | the fixer's tree is unsettled, so nothing is vouched and nothing is kept | telling the fixer to run the gate |
| [D6](#d6) | A findings file that says clean with `open_blocking: 0` while a blocking card's Status word is neither `verified` nor `accepted` is malformed: one rewrite worker of the role, then a halt when the rewritten file is malformed for any reason | the role's own worker sets the word, so no fixer's and no conductor's word verifies a fix | a fixer pass for the card; reading the frontmatter alone; the conductor reading `fixed` as open |
| [D7](#d7) | This change's tasks name at most one distinct `Verify:` command with `tests/test_conduct.py` and at most one with `tests/test_converge.py`, reused by each task that needs it | the change is built under the old plan check, where each distinct such command runs whole at the close | one command a task |

### D1

`bare_pytest` keeps its rule that the `Verify:` expects exit 0 and no more: no count, no `prints nothing`, no other exit. The words after the pytest prefix are vouched when each is one of:

- a quiet option or a test module the gate discovers, as today;
- `-n` or `--numprocesses` with its value, glued as `-n4`, `-nauto` or `--numprocesses=4`, or apart as `-n auto`;
- `-k` with the next word as its value.

Any other option, `-m`, `-c`, `--deselect`, a node with `[` and a path the gate does not discover run as today. Case vouched: `uv run pytest tests/test_conduct.py tests/test_structure.py -n auto -q`. Case run: `uv run pytest tests/test_x.py -m slow -q`.

### D2

```
check
 ├─ reads   boxes · names · tests · corpus        no command runs
 ├─ quick   commands that are no pytest run, no make · a collection per pytest `Verify:` that expects exit 0
 └─ long    pytest runs and make, those the green record vouches for left unrun
 a failed group prints its lines and ends the check
```

A command is a **pytest run** when its argv starts `pytest`, `uv run pytest` or `python -m pytest` and it holds no `--collect-only`. A **collection** is that command with ` --collect-only -q` appended, as `collecting` makes it, for each pytest `Verify:` that says it exits 0 and no more. A collection that exits non-zero or finds no test is the line `plan: <sub-task> — `<command>` collected no test`, and it no longer waits for a green record.

The quick group starts its commands before its collections, so a collection that takes every slot holds no search behind it, and no command of it waits behind a pytest of the long group. Results are kept by tree as today; collections are not. With `--only`, the reads group is empty.

### D3

`--quick` runs the quick group over the ticked sub-tasks, as a plain check reads them: a `**HALT CHECK**`, a `**HUMAN` phase and a command naming `plan_check.py` stay out. It runs no pytest test and no `make`, checks no box, name, test or corpus case, and prints `plan: clean` and exits 0 when no line is printed. `--quick` beside `--only` exits 2, naming both.

### D4

`Run.advance` calls `Run.quick_built` once a numbered phase's check has passed and a later phase stays unticked, beside `gate_built`, which it calls after the last phase. `quick_built` runs `_quick_plan`, which runs `plan_check.py --quick` under `_boxed`, its `--base` the close's. A failure is `plan check: plan_check.py --quick exit <code> · <the last line>`, with `build.halt` written as `sub-task: phase <N>`, `stop: plan check`, so the version halts as a failed build check does and its cause reads `plan-text`.

`_check_phase` stays a read: `check` calls it more than once, and a run in it would write `build.halt` on each call. A failure before a `**HUMAN` phase halts with no rescue, as any build check does there.

The rescue's amend of `tasks.md` answers a failure: the phase is ticked, so the next spawn is the following phase, whose quick check runs again over every ticked sub-task. A person's amend that unticks the phase builds it again, and the last phase runs none, as the close's whole check follows.

### D5

`skills/mf-converge/references/fix.md` tells the fixer to run `plan_check.py --change <change-id> --base <base> --quick` in place of the whole check, and to name what it leaves on its `plan check left:` line as before. Converge already runs the gate after the fix and the whole check at the freeze, and the verify round runs it again from the kept result while one stands, so no script change is needed: the freeze finds the gate's record and vouches under [D1](#d1). `fix.md` says the whole check follows the gate.

### D6

`read_findings` reads a file whose `verdict` is `clean`, whose `open_blocking` is `0` and which holds a blocking card whose Status word is neither `verified` nor `accepted` as malformed, with the card's id and word in the reason. It judges it after the passes of conformance, as it judges the file with no open card. `held` sends it to `rewrite`, whose prompt for this reason lets the worker set the card's Status or the file's verdict, in place of the contract's "keep each Status".

A file malformed after the rewrite, for any reason, raises `Halt` naming the role, the card and the word of the first read: a rewrite that breaks the file another way must not drop the blocker through the debt card. The mismatch itself sends no card to a fixer and counts no round; a worker that sets the verdict `changes-requested` or the card `open` leaves a file read as any file. The rounds loop, `blockers`, the debt write and the conductor's `_open_blockers` stand as they are.

### D7

The commands of `tasks.md` that name `tests/test_conduct.py` or `tests/test_converge.py` are one text each, the same in every task that needs it. A `uv run pytest` command over more than one test file, or over either of those files, carries `-n auto`. A `--collect-only` command, `make check` and `make gate` are exempt.

## Tests

The change adds unit and in-process tests and no end-to-end test, and deletes or merges none. The pins of `test_a_green_gate_record_passes_a_bare_pytest` turn in the first phase and again in the second.

| layer | added or changed | command | reason |
|---|---|---|---|
| unit | the vouched options, the groups, `--quick` and the collection line, in `tests/test_plan_check.py` | `uv run pytest tests/test_plan_check.py --collect-only -q` | the lowest layer that can fail for the check's rule (`T1`) |
| unit | the clean file with a blocking card not closed, its rewrite and its halt, in `tests/test_converge.py` | `uv run pytest tests/test_converge.py --collect-only -q` | `read_findings` and `held` are read in process |
| in-process | the phase's quick run and its `build.halt`, in `tests/test_conduct.py` | `uv run pytest tests/test_conduct.py --collect-only -q` | `Run.quick_built` reads a fixture repository |
| end-to-end | none | none | no browser or engine runs |

`test_a_green_gate_record_passes_a_bare_pytest` and the tests of `tests/test_conduct.py` that run a build of more than one phase over a fixture meet the new runs. A test the new rule turns red is fixed in the phase that turns it, and the commit body lists it as `Unplanned:`.

## Dependencies

None.

## Risks / Trade-offs

- **A test green in the whole suite and red alone** is not seen: the gate's run vouches for it. The gate runs the whole suite, so a test that fails alone fails there first only when order matters.
- **A group that fails hides the later groups.** A plan with a failed box line and a failed long command shows the box line first, and the next check shows the rest. Each round is cheap.
- **A collection of `-n auto` takes every slot.** A pytest `Verify:` collected in the quick group collects again before it runs in the long group, unless the record vouches for it. The cost is an import of the test files, not a run.
- **A slow command that is no pytest run and no `make`**, such as `ty check`, lands in the quick group and runs at each phase end and in the fixer, and a slow quick run shows nothing in the run log while it runs. A plan keeps such a command out of a `Verify:`.
- **`--only` collects too.** The build worker's run of its phase's `Verify:` lines through `--only` pays a collection for each pytest line that expects exit 0, then runs it, where no record stands mid-build.
- **A quick failure is the plan's.** A `Verify:` of an earlier phase that a later phase breaks on purpose halts at that phase, where it halted at the close before; the rescue's amend answers it as it answered the close's.
- **The clean mismatch has one more halt.** A role whose worker still leaves the word wrong halts the version, where the debt card went on; the halt names what is wrong.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the green gate vouches more, cheap first and `--quick`, the phase check collects, the fixer's check and the clean file, the words.
