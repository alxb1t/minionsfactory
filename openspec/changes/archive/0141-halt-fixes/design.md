# Halt fixes — design

Each fix below is a few lines of a script or a sentence of a skill, and none changes a decision in force. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The line halts on defects it already has the words for. [D1](#d1) to [D4](#d4) are the plan check, which the build's close, converge and the cut all run. [D5](#d5) to [D7](#d7) are the conductor, [D8](#d8) and [D9](#d9) its queue, [D10](#d10) and [D11](#d11) integrate and converge, and [D12](#d12) the rule a rescue and a supervisor follow.

```
plan_check.py ──loaded by──▶ cut_check.py, verify_check.py   (D1)
   commands()  the span rule (D2), exits (D3)
   run()       no VIRTUAL_ENV (D4)
conduct.py     _decisions (D5) · advance (D6, D7) · cutting, rejoin (D8, D9)
integrate.py   decisions (D10)          converge.py  rounds (D11)
```

## Goals / Non-Goals

- Goals: a run stops on a plan's fault, not on a reading of the plan the scripts get wrong; each fix has a case that fails without it.
- Non-Goals: `_settle_kept` and the supervisor's settle paths (D61); the stack's reset (D72); a mutation tool's ranges; the debt.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `verify_check.py` loads the plan check's parser | the cut's copy and the build's read a `Verify:` differently, so a check passes the cut and fails the build | a second copy kept in step by a test |
| [D2](#d2) | after an output verb, every span is output until `then`, `;` or the sentence's end | a span is output today only right after its verb, so a quoted text and a list's later names run as commands | a comma as the end of output |
| [D3](#d3) | `` exits `<N>` `` means the command exits `<N>` | a line that says `exits 2` passes only on exit 0 today | reading every non-zero exit as a pass |
| [D4](#d4) | the plan check drops `VIRTUAL_ENV` from each command's environment | the close runs under `uv run --script`, whose variable makes each `uv run` warn into the compared output | filtering the warning from the output |
| [D5](#d5) | `_decisions` reads each run of whitespace as one space | a dedent in a decision's code block ended a run as a decision | stripping each line's indent alone |
| [D6](#d6) | the conductor removes `build.halt` when it spawns a build | the viewer reads it before a running worker, so a rejoined build shows a halt | the viewer testing the file's age |
| [D7](#d7) | a failed read of `origin` after the run's own push is tried once more | one failed read sent the run offline and logged the tag as released locally | no read after the push |
| [D8](#d8) | a released `after` is met | the cap counts it met, while the cutter was handed it and `cut_pre.py` halted on it | halting the cut |
| [D9](#d9) | `rejoin` of a cut clears and requests each dependent halted on it, down the chain | a dependent's halt is old text in its own entry, which a run skips unless a request names it | a rejoin per dependent |
| [D10](#d10) | `decisions` renumbers the changelog first, skips a conflicted path, and halts once after every path | one ambiguous path ended the loop before the plan's citations and the changelog | opening the supervisor's settle paths |
| [D11](#d11) | a verdict is read against its cards | `changes-requested` with nits alone halted the run, and with no card passed in silence | judging the word alone |
| [D12](#d12) | a `Verify:` that cannot pass is retargeted or split, never replaced by one that proves less | rescues weakened checks, and the gate's check takes any amend as the plan | a comparison in a script |

### D1

`verify_check.py` loads `plan_check.py` with `runpy`, as `cut_check.py` does, and takes from it the names it used from its own copy: `SPAN`, `Unparsed`, `commands` and `tokens`. Its own parser, its table of output verbs and its `Command` are deleted, and `check_command` types its `command` as `Any`. `brief_check.py` reads those names through `verify_check.py`'s namespace, so they stay there under the same names. The load crosses skill folders, so `tests/test_structure.py` lists the pair in `LOADS_OUTSIDE` and `docs/modules.md` names it in the row of `verify_check.py`.

### D2

`commands` resets `output` when the words between two spans hold `then`, a `;` or a sentence end (`.`, `!` or `?` before a space or the end), and sets it when the words before a span end in an output verb. Once set, it stays for every later span. The clause for a bare `and` or `or` goes: the rule holds it already.

```
`a` prints `1`, then `b` prints `2`     a cmd · 1 out · then → b cmd · 2 out
`a` exits `1` with `text`               a cmd · 1 out · text out
`a` lists `x`, `y` and `z`              a cmd · x y z out
```

A comma is no end: ``` `a` prints `1`, `b` prints `2` ``` reads `b` as output. That is the price of the rule, and the cut's checks name `then`.

Fix note (2026-11-21, S2): `commands` also ends output at a `, and` or `, or` before a span an output verb follows, so a second command after it is kept.

### D3

`Command` gains `exits: int | None = None`, set when the span right after the word `exits` is all digits. `passed` then holds `code == exits` and the output rule; with `exits` unset it is as it was, so a search that finds nothing still passes on exit 1. `report` says `exited <code>` whenever the code is not the exit the command is held to. `bare_pytest` stays true for `exits` unset or `0`, and false for any other, so a pytest that says it exits `1` runs.

### D4

`run` builds the child's environment from `os.environ` without `VIRTUAL_ENV`, then sets `PYTEST_ADDOPTS` as before. stderr stays merged into the compared output.

### D5

`_decisions` returns its text with each run of whitespace read as one space, headings and section alike. Fix notes are dropped first, as now. A reworded sentence is still a change, a dedent or a re-wrap is none. `_replanned` calls the same function, so the stack's re-plan test reads the same way.

Fix note (2026-11-21, S3): a line's first `#` or `|` is kept as a mark before the whitespace is read as one space, so a heading never joins the line before it.

### D6

`Run.advance` removes `.minions/changes/<change-id>/build.halt` through `_remove_in`, as `Run.cutting` removes `cut.halt`, just before it spawns a worker at stage `build`. `rescue.md` stays: the conductor reads it by its time alone.

### D7

In `Run.advance`, the first `Unreachable` from the release check is logged with `self.waited` and the check runs again with the same arguments. A second `Unreachable` takes the branch that was there: it is logged, `self.offline` is set and the check runs offline, so each failed read is a wait.

### D8

`Run.cutting` hands the cutter the entry's `after` ids that `_shipped` says have not shipped, so a released id leaves its `after=`. `cut_pre.after_problem` passes a name that is no open version when the default branch holds `openspec/changes/archive/<name>/`, the test `_shipped` makes; the lower-number check stays for both. Its message for a name that is neither reads `<name> is not an open or released version`.

### D9

`rejoin` of a queued cut finds, under the queue lock, each entry whose `halt` is `after <name> is cut-halted` for `<name>` the cut or a dependent it found, to a fixed point. It writes `halt: None` into each readable entry, leaves an unreadable one alone, and requests each from a live run, or starts a run when none is live. The line names the cut and each dependent: `rejoin: requested 0001-a, 0002-b`.

### D10

`decisions` calls `_renumber_changelog` right after it writes the decisions page. Then, for each changed path but the page and the changelog, a path in `_unmerged` is skipped and kept with the renumber, and any other goes to `_recite`, which returns `False` for an ambiguous path instead of raising and `True` on every other return, an early one included. After the loop the rule appends, after its `decisions: renumbered` line, one `decisions: conflicted — <path>: <moves>` line for each skipped path, `<moves>` as in the renumbered line, and, when a path was ambiguous, raises one `Stop` naming each. `skills/mf-integrate/SKILL.md` says so in its `decisions` row.

Fix note (2026-11-21, S4): the `decisions: renumbered` line reads `citations with them but in the conflicted` when a path was skipped.

### D11

`read_findings` in `converge.py` makes a file that is no stub malformed, as `verdict is changes-requested with no open card`, when its verdict is `changes-requested` and no card is open. A card is open until its status is `verified` or `accepted`, as `blockers` reads it, so a file whose cards are all cleared is malformed too.

`held` then writes `verdict: clean` and `open_blocking: 0` into the frontmatter of a role whose verdict is `changes-requested` while no open card blocks, once its `unclean` check has passed. It builds the text with `mflib.findings.keyed` and writes it through `BUNDLE["write"]`, as `ruled` does, and returns the verdict as `clean`.

A rewrite that leaves the file malformed by this fault alone gets the same write, so the file reads what converge counted. The `verdicts —` log line keeps the word the checker wrote.

Every later reader — `converged`, `unlocked`, `behind`, `conduct.py`'s `_unjudged` and `mf-release` — reads a clean file, and the pickup takes its open cards. The halt `changes requested with no blocking card open` is then unreachable and goes.

Fix note (2026-11-21, S1): `read_findings` judges the files, commits and passes first, so a file with no open card is malformed only once its scope held.

### D12

`skills/mf-rescue/SKILL.md` and `skills/mf-supervise/SKILL.md` each state the rule: a `Verify:` that cannot pass is retargeted or split, never replaced by one that proves less; an exact count stays exact; where none of that fits, the halt is a diagnosis. Prose alone: no script compares a replaced check with the old.

## Tests

This change adds unit cases and no end-to-end test ([T1](../../../skills/mf-build/SKILL.md)): each case reaches a function or the conductor's fake host, and none boots a browser. A new case is a new test next to the one it twins, so it fails before its fix.

| layer | what is added | where | the count, by |
|---|---|---|---|
| unit | the span rule, `exits`, the environment | `tests/test_plan_check.py` | `uv run pytest tests/test_plan_check.py --collect-only -q` |
| unit | the one parser, as the cut reads it | `tests/test_verify_check.py` | `uv run pytest tests/test_verify_check.py --collect-only -q` |
| unit | the listed load | `tests/test_structure.py` | `uv run pytest tests/test_structure.py --collect-only -q` |
| unit | a released `after` at the cut | `tests/test_cut_pre.py` | `uv run pytest tests/test_cut_pre.py --collect-only -q` |
| unit | the decisions compare, the build halt, the second read, the released `after` at the queue, the cascade | `tests/test_conduct.py` | `uv run pytest tests/test_conduct.py --collect-only -q` |
| unit | a conflicted, an ambiguous and an unreadable path | `tests/test_integrate.py` | `uv run pytest tests/test_integrate.py --collect-only -q` |
| unit | nits alone, a verdict with no card | `tests/test_converge.py` | `uv run pytest tests/test_converge.py --collect-only -q` |

End-to-end runs added: none.

Tests removed or merged: none, so the I16 table is empty.

Existing cases turn and keep their tests. The `no card` case of `test_a_blocker_is_fixed_verified_and_cleared` leaves its loop of halts for a test of its own, since a file with no card is malformed and is rewritten. The rejoin of each dependent in `test_a_cut_halt_is_shown_and_rejoin_cuts_again` becomes the rejoin of the head.

## Dependencies

None.

## Risks / Trade-offs

- The sticky span rule changes how every `Verify:` already written is read. A ticked check whose second command followed a comma now reads that command as output and runs it no more. `plan_check.py` and `verify_check.py` now agree, which is the point; a plan that wrote the comma form says `then`.
- `verify_check.py` fails at load when `plan_check.py` is missing, as `cut_check.py` does. The pinned release exports every skill together, so the two stand side by side.
- `decisions` prints more than one line when a path is skipped. The conductor logs what it prints; its tests run in the same phase as the change.
- The whitespace rule lets a rescue re-wrap a decision with no `Decided-by:` trailer. A re-wrap carries no meaning; a reworded sentence still needs one.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the plan check, the conductor, the queue, integrate and converge, then the rule.
