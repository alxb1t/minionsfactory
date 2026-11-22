# Verify forms — design

One reading of a `Verify:`'s words for the cut, the build and the close, a form for each count, and a limit a repository sets. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`plan_check.py` judges a ticked `Verify:` at the build's close and after each fix. `verify_check.py` loads its parser for the cut, which passes forms the close refuses. The build runs a `Verify:` in the worker's own shell.

```
cut      verify_check.py   reads the form          D4 D5 D6
build    worker's shell    runs it, per task       D7 D8          → plan_check.py --only
close    plan_check.py     judges it at HEAD       D1 D2 D3 D9 D10 D11
freeze   converge.py       copies the output       D12
```

Probe 7 of an earlier run halted a build on "`uv run … -L pyproject.toml` prints one integer, a space and `pyproject.toml`": the span after `and` ran as a command, exit 127.

## Goals / Non-Goals

- Goals: a form the close refuses fails at the cut or at its phase; a limit and a load the repository can live with; one parser.
- Non-Goals: a new kind of `Verify:`; a bound on the whole check; mutation tooling; a `**Verify timeout:**` line in this repository's `AGENTS.md`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Output opens at the first output verb after a command and holds every later span to `then`, `;` or the sentence's end | a verb with words before the span left the span a command | keeping the last-word rule; ending output at a comma |
| [D2](#d2) | The compared output is stdout alone; stderr is kept apart and shown on a failure | a tool's warning on stderr broke an exact match | merging both streams; dropping stderr |
| [D3](#d3) | A command starts only while the 1-minute load is under the core count, and always when none runs | side-by-side runs overloaded the machine; a load that never falls must not starve the check | a fixed pause; half the cores |
| [D4](#d4) | A count is stated only on `grep -c` or `--count` over one file | `git grep -c` prints `path:N`, and a multi-file count prints a line a file | accepting `path:N` lines |
| [D5](#d5) | Absence is `git grep -c` printing nothing; `-L` and `--files-without-match` are refused | `grep -L` exits 1 under one grep and 0 under another | a second absence form |
| [D6](#d6) | A plain `Verify:` holds no line number, no prose phrase and no `<default>..HEAD`; a `**HALT CHECK**` sub-task is exempt | a merge moves lines, simplify rewraps a phrase, a stacked range holds its dependency's commits | refusing them in a HALT CHECK too |
| [D7](#d7) | A phase's `**HALT CHECK**` sub-tasks run first; `--only` judges one it names; the close and converge skip every one | a check of the state before the edits ran after them; `--only` ran nothing for one it was named for | a new kind of `Verify:` |
| [D8](#d8) | The build runs each sub-task's `Verify:` through `plan_check.py --only`, not in its shell | a form the close refuses fails at the phase that wrote it | keeping the shell |
| [D9](#d9) | While `stacked-on` stands, the close's plan check takes its base from it | a stacked range holds its dependency's removed tests | the default branch's merge base |
| [D10](#d10) | A command's limit is the repository's `**Verify timeout:**` in seconds, 600 where none | one limit fits no repository | a limit per `Verify:` |
| [D11](#d11) | The build runs the plan check as one background command and waits on it once; "ends within 600 s" goes | the host ends a foreground call at ten minutes, and a queue outlasts any one limit | a foreground call |
| [D12](#d12) | Converge's freeze reads a command past its limit as timed out, and raises no card on it alone | `build.done` is a worker's file, the freeze's run is under the sandbox, and a timeout under load is no defect | skipping the freeze's run |
| [D13](#d13) | The records follow: D72, D74 and D79 are edited where they live | a decision page says what holds | a new decision |

### D1

`commands` in `plan_check.py` sets output when a word of the text before a span is an output verb and a command stands before it. Output ends at `then`, `;` or a sentence end. A `, and` or `, or` before a span that a verb follows opens a new command; before one with no verb it ends a list.

```
`a` exits `0`, and `b` prints nothing.   → a, b     (a verb follows b)
`a` prints one integer, a space and `b`. → a        (b is output)
`a` prints `1`, then `b` exits `0`.      → a, b
```

A count is still set only for `prints` or `reports` right before an all-digit span, and `exits` right before one sets the exit. A comma alone ends nothing.

### D2

`Result` gains `stderr`, last and empty by default. `run` pipes stderr apart. `passed` reads stdout; `report` shows the first lines of stdout, then of stderr, when a command fails. A kept result stores `stderr`; one kept without it is read as none kept, so no merged output is compared again. `collecting` reads stdout.

### D3

`schedule` waits until the command's slots are free, no other `make` runs when it is one, and either no command runs or the 1-minute load, read through `os.getloadavg`, is under `CPUS`. It re-reads the load each second while it waits. A load that cannot be read is no load.

### D4

`verify_check.py` refuses a stated count on a `git grep`, on a `grep` with no `-c` or `--count`, and on a `grep -c` over more than one file operand or with `-r` or `-R`. It prints `<sub-task>: I19 — a count on <form>: <command>`. A `git grep -c` with no stated count passes.

### D5

`L` leaves the options a search runs, and `--files-without-match` the long names; each is then refused as any option the search does not run. The absence form is `git grep -c "<pattern>" -- <file>` printing nothing.

### D6

- A **line number** is a word of a command shaped `<path>:<digits>` or `<path>:<digits>-<digits>`.
- A **prose phrase** is a search pattern of three or more words, each a run of letters, joined by single spaces, once quotes, a leading `^` and a trailing `$` are removed.
- A **range** is a word shaped `<default>..HEAD` or `<default>...HEAD`, `origin/` allowed before the default branch, which `cut_pre.default_branch` names.

A `**HALT CHECK**` sub-task is exempt from these three: it checks the state before the edits. Counts and `-L` stay refused there.

### D7

- The build runs a phase's HALT CHECK sub-tasks through `plan_check.py --only` before the phase's other tasks.
- A red-first check states the exit its command really gives before the edit, as `exits <N>`.
- In `jobs`, a HALT CHECK sub-task is skipped only when no `--only` is given; a `**HUMAN` phase's sub-task is skipped always.
- A command is skipped as naming the script only when one of its words has the file name `plan_check.py`, whatever its directory, so `tests/test_plan_check.py` is run.
- `converge.py`'s `added` leaves each HALT CHECK sub-task out of the lines it hands to `--only`.

### D8

Step 2's second item runs the phase's sub-tasks but a HALT CHECK through `plan_check.py --only`, once the tasks are done, and shows its lines. A **HUMAN** phase keeps its checks run as written: the plan check skips them. A `**CORPUS**` sub-task keeps `make corpus` after its check.

### D9

Step 3.6 passes `--base <base>`, where `<base>` is Step 3.5's: the sha `stacked-on` names while it stands, else the merge base of the default branch and `HEAD`. The spec's and D72's lists of what takes `stacked-on` gain the plan check.

### D10

`plan_check.py` reads the first integer after `**Verify timeout:**` in the root `AGENTS.md`. A missing file, a missing line, text with no integer or an integer below one gives `TIMEOUT_SECONDS`, 600, read at call time. `run` and `schedule` take the limit as an optional argument that falls back to it, so a test that patches `TIMEOUT_SECONDS` stands; a git call keeps it.

### D11

Step 2's `--only` run and Step 3.6's close each start as one background command, and the worker waits on it once and reads its exit and output. The fixer's reference keeps its foreground call and drops the claim of 600 s.

### D12

- `converge.py`'s `planned` splits the lines of `plan_check.py` into those ending `timed out` and the rest, and sends back the rest.
- A run with timeouts alone returns, and logs `plan check — timed out: <subjects>`.
- The freeze's `evidence.md` keeps each line as printed. The fixer's and the checkers' references say a `timed out` line is no failure.

### D13

`docs/decisions.md`, where a decision in force lives: D74 gains the build's run at each phase; D72 gains the plan check among the bases; D79 says a timeout in the plan check's lines is no finding. `docs/modules.md` lists the load `verify_check.py` makes of `cut_pre.py`.

## Tests

The tests added are unit tests, and no end-to-end run is added: the repository has no browser or engine to run on. Counts at the cut:

| file | tests at the cut | command |
|---|---|---|
| `tests/test_plan_check.py` | 20 | `git grep -c '^def test_' HEAD -- tests/test_plan_check.py` |
| `tests/test_verify_check.py` | 6 | `git grep -c '^def test_' HEAD -- tests/test_verify_check.py` |
| `tests/test_converge.py` | 76 | `git grep -c '^def test_' HEAD -- tests/test_converge.py` |

| test | layer | what it holds |
|---|---|---|
| `test_a_span_after_an_output_verb_is_output` | unit, extended | the probe's line is one command; a `, and` clause before a verb opens a command |
| `test_stderr_is_shown_and_never_compared` | unit, new | a warning on stderr beside an exact stdout passes; a failure shows both |
| `test_a_command_starts_under_the_load_or_when_none_runs` | unit, new | the load read is patched: over the cores with a command running waits, with none starts |
| `test_a_form_the_close_refuses_breaks_at_the_cut` | unit, new | each refused count, `-L`, a line number, a phrase and a range; the HALT CHECK exemption |
| `test_only_runs_the_named_sub_tasks` | unit, extended | a HALT CHECK named is judged; a command holding `test_plan_check.py` runs |
| `test_a_verify_timeout_line_sets_the_limit` | unit, new | the limit from `AGENTS.md`, 600 with no line |
| `test_a_catch_up_runs_the_changed_verifies_in_one_plan_check` | unit, extended | a HALT CHECK line the range adds is left out |
| `test_a_timeout_alone_sends_nothing_back` | unit, new | `planned` sends back a failure and not a timeout |

Tests that stay green unedited: `tests/test_skills.py`, which keeps the ids of `I3`, `I15` and `I19` equal in both skills, and `tests/test_structure.py`, which holds the module map.

Tests that turn and are edited, none deleted or merged:

| test | turns because | carries |
|---|---|---|
| `test_every_pytest_runs_without_the_cache_provider` | `run`'s result holds `stderr` | its assertions, the result's fourth field added |
| `test_a_command_runs_without_virtual_env` | the same | the same |
| the `plan_check.py` row of `tests/test_staged_writes.py` | a kept result stores `stderr` | its assertions, the stored text holding `"stderr": ""` |
| `test_a_search_prints_the_lines_it_matches_at_head` | `git grep -c` and a multi-file `grep -c` are refused | its assertions, the refused forms moved to the refusal test |
| `test_a_span_after_an_output_verb_is_no_command` | the wider rule | its assertions, the probe's line added |
| `test_a_check_out_of_shape_breaks_and_is_not_run` | `-L` joins the refused options | its assertions, one sub-task added |
| `test_commands_run_side_by_side_and_print_in_task_order` | the load read joins the start | its assertions, the load patched |

## Dependencies

None.

## Risks / Trade-offs

- A comma alone ends no output, so "`a` prints `1`, `b` prints `2`" stays one command. The price of D1; `then` and `, and` are the ways to write two.
- D6's phrase rule refuses a search of plain words that no rewrap could break, such as `class Foo Bar`. The cut names the rule and the fix: a pattern anchored on a symbol.
- A load that is high but not busy delays a command a second at a time; it never starves it, since a command starts when none runs.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the judge, the cut, the build, then time. Each phase is green on its own, and the build's own step runs through the plan check only from the phase that writes it.
