# Plan review diet — design

The cut's plan reviews move to Sonnet 5.5 · high, and scripts settle the doubts a script can find before the reviewer reads. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The plan review is a fresh read-only worker, on Opus 5.5 · high whatever the cut runs on. [D71](../../../docs/decisions.md#d71--the-cut-and-converge-read-what-changed) rejected Sonnet for it, and [D74](../../../docs/decisions.md#d74--converges-rounds-are-cut-at-their-causes) held Opus.

Across the reviews of 0103–0109, the doubts every cutter fixed were judgment, or mechanical in classes: unplanned readers, `Verify:` sequencing, record consistency.

Cache writes were the largest part of a review's cost, and Sonnet 5.5 costs half of Opus 5.5 on every rate. The reviewer counted its own 40 turns, overran them, and rarely said so.

The code, read at `HEAD`:

```
cut_check.py   ROWS, JUDGED, blocks(), row_*(change[, plan]), check() -> failures, matches, judge
facts.py       reader_lines(name), run_readers(names, notes), main()  [readers <name>... [--notes]]
SKILL.md       Step 3 readers · Step 8 self-check · Step 8.5 review (40 turns, Opus 5.5 · high)
```

## Goals / Non-Goals

**Goals:** a reviewer on Sonnet that reads what a script cannot find; each mechanical class held by a script with a case in the tests; an overrun the ledger can see.

**Non-Goals:** a Codex review (it needs `conduct.py` to start it between the cutter's staging and its commit); a change to the 1-hour cache; a ledger in this repository.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the first and second plan reviews run on Sonnet 5.5 · high | half the price; converge's checkers stand behind it | Opus 5.5 for the first only |
| [D2](#d2) | `cut_check.py` settles `Verify:` sequencing, rows `V1`–`V4` | a class of 0103–0109's doubts, found by reading text | a reviewer reading each check |
| [D3](#d3) | `cut_check.py` settles record consistency, rows `K1`–`K6` | a class of 0103–0109's doubts, found by comparing text | a reviewer comparing the artifacts |
| [D4](#d4) | `facts.py readers` takes `--signature`, `--file` and `--string` | unplanned readers were the third class | a helper per changed name |
| [D5](#d5) | the packet marks each settled row and readers line; the reviewer skips them | a settled class re-read costs tokens and finds nothing | a packet of rows alone |
| [D6](#d6) | a 25-turn budget; the cut counts the tool calls from the transcript and records an overrun | reviews overran their 40, and one said so | a hard cap the host does not have |
| [D7](#d7) | the cut keeps the 1-hour cache | a lapse while the cut waits re-writes its whole context | the 5-minute cache |
| [D8](#d8) | hypotheses guard the move | the first review goes back to Opus when they fail | no measure |
| [D9](#d9) | the reading step names the decision headings as the conversation's index | `bundle.py --decisions` takes no empty list (debt `0100·R4`) | a bare `--decisions` that prints the index |
| [D10](#d10) | an amend is not held to `V1`–`V4` in this version | decided by the cutter, below | a check in `mf-rescue` and `mf-supervise` |

### D1

A new decision in [docs](../../../docs/decisions.md), **The plan reviews run on Sonnet**, takes the next id after D79 and states D1's choice. It overturns D71's rejection and D74's "Plan reviews run on Opus 5.5 · high", and edits [D65](../../../docs/decisions.md#d65--a-lighter-plan-review-and-build) where it names the model. A first review still runs always and a second only after a fix that changes a decision or a task, as before.

Its text, for the `Planning` group after D77:

```
### D80 · The plan reviews run on Sonnet

**The cut's plan reviews run on Sonnet 5.5 · high, the first always and a second only after a fix that changes a decision
or a task. `cut_check.py` settles what a script finds in the plan — `Verify:` sequencing and the record's consistency — and
`facts.py readers` the stand-ins, monkeypatches and readers of a changed name; the packet marks each as settled, and the
reviewer judges the rest. The reviewer's budget is 25 turns, its tool calls counted by the cut from its transcript, an
overrun recorded in `cut-notes.md`. The cut keeps the 1-hour cache.**

- **Why:** the reviews were the cut's dearest worker beside its own context, Sonnet 5.5 is half Opus 5.5's price on every
  rate, and a class of what they raised a script finds; converge's Codex checkers stand behind the plan review.
- **Accepts:** a first review that finds less than Opus 5.5 did · a measure that can put it back: a cut's reviews at most
  $1.40 together, converge's plan-side blockers at most one a version, failing over three versions.
- **Rejected:** plan reviews on Opus 5.5 · a Codex plan review, which needs the conductor to start it between the cutter's
  staging and its commit · the 5-minute cache — a lapse while the cut waits re-writes its context.
- **Amends:** D65, D71 and D74, each edited where it lives.
```

### D2

Rows of `cut_check.py`, each a halt line `cut_check: halt — <row> — <sub-task>: <why>`. A **needle** is each pattern of a `grep` or `git grep` `Verify:` — every `-e` value, else the first operand — read as a literal: after its backslashes are removed it holds none of `^ $ . * + ? ( ) [ ] { } |`, or the search has `-F`. A pattern that is no literal is left to the reviewer. `search_parts` takes the words from `plan_check.py`'s `tokens`, and the file operands are the words after the patterns, a `HEAD` among them dropped.

| row | halts when |
|---|---|
| `V1` | a needle of a sub-task's search is quoted in an earlier sub-task whose text names the searched file: the check holds before its own task |
| `V2` | a `pytest` `Verify:` selects by `-k` a word that a later sub-task's `test_` name holds, and that sub-task's text adds, removes, merges or renames |
| `V3` | a `git grep` names a file that `git ls-tree -r --name-only HEAD` lacks, and the first sub-task naming it is in the same phase: the build checks before the phase commits |
| `V4` | a needle is named neither in its sub-task's text outside the `Verify:` clause, fenced lines included, nor in the section of a decision the sub-task links |

`V1` and `V4` skip a **HALT CHECK** sub-task, which checks a premise. `V3` is computed first: on a hit `check` returns that failure alone, with no search matches and no other row, so the run exits 1 and ends `cut_check: halt — 1 rows failed`. A row is a text match over `tasks.md` and the tree of `HEAD`, and runs no command of the plan.

### D3

Rows of `cut_check.py`, in the same halt form. A **path span** is a backtick span with no space, holding a `/` or ending `.py`, `.md`, `.toml`, `.yaml`, `.yml` or `.mk`, or `Makefile`; paths under `openspec/changes/` and `.minions/` are left out. A path is the same as another when they are equal or one ends with `/` and the other.

| row | halts when |
|---|---|
| `K1` | a path span of `proposal.md`'s `## Impact` is held as text by no sub-task, `Verify:` included, or a path span of a sub-task's first line that `git ls-tree -r --name-only HEAD` lists, outside `openspec/changes/`, is absent from `## Impact` |
| `K2` | a `tests/` path of `design.md`'s `## Tests` is held as text by no sub-task, or a `tests/` path of a sub-task's first line is absent from `## Tests` |
| `K3` | the ids of the `## Decisions` table and the `### D` headings of `design.md` differ, or sit in another order |
| `K4` | a `design.md#d<n>` link of `tasks.md` or `proposal.md` has no `### D<n>` heading |
| `K5` | a sub-task with exactly one path span, its text holding none of the words `add`, `new`, `create`, names a `Step <n>` and that file has no `## Step <n>` heading at `HEAD`, or names a constant — a span of capitals, digits and `_`, three characters or more, `HEAD` apart — and `git grep -w` finds it nowhere in that file at `HEAD` |
| `K6` | one `path:line` or `path:first-last` cite stands in two sub-tasks |

### D4

`facts.py readers` keeps its names, and `--notes`. Each flag repeats, names are optional, a call with no name and no flag exits 2, and a value that is no identifier for `--signature` exits 2. Each kind prints `<kind> of <value> — <text> · <path>:<line>` per hit at `HEAD`, or `<kind> of <value> — none · HEAD`, and appends the lines to the notes.

| flag | kind | a hit is |
|---|---|---|
| `--signature <name>` | `stand-in` | a line defining `def <name>`, `class <name>` or `<name> = lambda`: every definition of the name, the real one too |
| `--signature <name>` | `monkeypatch` | a line holding the name in quotes or after a dot, inside a `setattr` or `patch` call that may span lines |
| `--file <path>` | `runpy reader` | a line holding the file's basename in quotes: how `runpy.run_path`, `spec_from_file_location` and a `uv run --script` argv name a script |
| `--file <path>` | `import reader` | a line `import <stem>`, `from <pkg> import <stem>` or `from . import <stem>`, `<stem>` the file's name without its suffix |
| `--string <text>` | `string reader` | a line holding the text as written, searched with `git grep -F` and no word bound |

### D5

Step 8.5's packet names the settled classes: each met row of `cut_check.py`, `V` and `K` rows among them, and each readers line of `cut-notes.md`. The reviewer judges `Verify:` and record questions no script settles: a pattern that is no literal, a sequence across phases, a stand-in the readers lines do not name.

### D6

The prompt gives 25 turns, counted as tool calls; at the 25th the reviewer stops and returns its doubts under `budget reached`. After each review the cut counts that worker's tool calls from its transcript, and when they pass the budget appends `plan review <n> over budget: <calls> tool calls` to `cut-notes.md`, `<n>` the review's number. A host that keeps no transcript gives no line.

### D7

Nothing changes: [`conduct.py`](../../../skills/mf-ship/scripts/conduct.py) asks for the 1-hour cache because the cut waits on background reviews. A 5-minute cache that lapses re-writes the cut's context of 100–275k tokens at the dearer rate, so its saving is lost on the first lapse.

### D8

The person's ledger measures both hypotheses; no task, as the ledger is outside this repository.

- **H18:** a cut's reviews cost at most $1.40 together, against $2.83 for 0109.
- **H19:** converge's plan-side blockers stay at or under one a version.

H19 failing over three versions puts the first review back on Opus 5.5, as a new decision.

### D9

`skills/mf-cut-change/SKILL.md`'s reading step says: from the conversation, read the `### D` headings of `docs/decisions.md` as the index, and in full each decision the conversation settles against. A brief source keeps `bundle.py --decisions`.

### D10

The cutter's decision `C1`, under `decide: recommended`: rows `V1`–`V4` run at the cut and not on an amend. After a build starts, `HEAD` holds earlier phases, so "a needle an earlier task adds" is true by design; and the halts that raised it were a backtick span read as a command, which no row here finds. The trigger to hold an amend: a `Verify:` an amend wrote again fails to run as written.

## Tests

All new tests are unit tests; no end-to-end run is added, and none is deleted or merged. [T1](../../../skills/mf-cut-change/SKILL.md#rules-for-tests) puts each at the lowest layer: a scratch repository and a fake `openspec`, as `tests/test_cut_check.py` and `tests/test_facts.py` already do.

| file | added | by |
|---|---|---|
| `tests/test_cut_check.py` | a defect for each of `V1`–`V4` and `K1`–`K6`, added to `test_each_mechanical_row_fails_by_name`, each tripping its row alone | [D2](#d2), [D3](#d3) |
| `tests/test_cut_check.py` | `test_a_search_names_its_literal_needle`, for the needle reader | [D2](#d2) |
| `tests/test_facts.py` | one test for each of `--signature`, `--file` and `--string`, and one for a call with no name and no flag and a `--signature` value that is no identifier | [D4](#d4) |

The rows turn existing tests red, and the tasks mend them first:

- `V4` halts the `_TASKS` fixture, whose 1.1 names no needle: `_DESIGN`'s decision gains a line naming it, and `test_a_fenced_block_does_not_count_toward_the_limit` keeps the decision link in its replaced text.
- `K1` halts the fixture whose `## Impact` names no `a.py`: `_PROPOSAL` names it. A `Makefile` in sub-task 1.1 is no file of the scratch repository's `HEAD`, so it asks nothing of `## Impact`, and `a.py` stays held by the `Verify:` text.
- `V4` and `K1` also meet `test_each_mechanical_row_fails_by_name[P9]`: its defect keeps a decision link beside the bare id.
- A defect that names a new path adds it to `## Impact` or `## Tests`, so it trips its row alone.

The scan of the review table's opening words in the skills tests holds as it is.

## Dependencies

None.

## Risks / Trade-offs

- A Sonnet first review may miss what Opus found. Converge's checkers stand behind it, and [D8](#d8) puts the review back on Opus on evidence.
- A text-match row can flag a sound task: the way out is always a rewrite of the `Verify:` or the task, never a skip. A pattern that is no literal escapes `V1` and `V4`, and the reviewer reads it.
- `K1` flags a path a task only reads: the cut adds it to `## Impact`, which is harmless.

## Verdict

Ready: every file the phases edit exists at `HEAD`, every row is a text match, and no decision of the brief is left open. The cutter's `C1` and the new decision's id are the items a person may want to read.
