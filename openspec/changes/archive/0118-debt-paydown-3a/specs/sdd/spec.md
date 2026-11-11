## MODIFIED Requirements

### Requirement: A reader of run data has a corpus case

`make corpus` SHALL run `scripts/corpus.py`, which SHALL run each `[[case]]` of `scripts/corpus.toml` — a reader's argv, run
with no shell from the repository root — once per file its `each` globs match under the run directory, or once when it has
none, writing only under the run directory's `corpus/`. A case MAY hold a `shape`, a regular expression: `corpus.py` SHALL run
the case only over the inputs whose text it matches, in multiline mode, SHALL print how many it skipped, and SHALL exit 2 for a
`shape` that is no regular expression. It SHALL exit 2 when `corpus/<case>` is a link, before it deletes or writes anything
under it. It SHALL exit 1 naming each run that exits non-zero, 2 when the cases
file cannot be read or the run directory is a link, and 0 otherwise. `make gate` and `make check` SHALL NOT run it.
`skills/mf-cut-change/SKILL.md` SHALL mark each sub-task that adds or alters code reading the run directory, run logs or Codex
sessions `` **CORPUS** `<case>` `` in a repository whose root `Makefile` has a `corpus` target, and SHALL plan the case in
`scripts/corpus.toml`. `skills/mf-build/SKILL.md` SHALL run `make corpus` after such a sub-task's `Verify:` passes and before
its tick, halting on any other exit than 0. `plan_check.py` SHALL fail a marked sub-task whose case `scripts/corpus.toml` does
not hold.

#### Scenario: The corpus over this repository
- **WHEN** `make corpus` runs in this repository
- **THEN** each case runs over the run directory's own findings files, status logs, run logs and Codex sessions, and it exits 0

#### Scenario: A reader that fails on real data
- **WHEN** a case's reader exits 1 on one change's findings file
- **THEN** `make corpus` exits 1, naming the case and that file

#### Scenario: A marked sub-task with no case
- **WHEN** a ticked sub-task is marked `` **CORPUS** `review-metrics` `` and `scripts/corpus.toml` holds no case of that name
- **THEN** `plan_check.py` exits 1, naming the sub-task and the case

#### Scenario: An input older than the card shape
- **WHEN** a case holds `shape = '^ok'` and one of its inputs does not open with `ok`
- **THEN** the reader runs over the others, and the case's line reads `1 skipped`

#### Scenario: A linked case folder
- **WHEN** `corpus/<case>` is a link to a folder holding files
- **THEN** `make corpus` exits 2 naming the case, and the folder keeps its files

### Requirement: The review-metrics station books the person's planning and operator work from session transcripts

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read an interactive session's transcripts only from the folders
the config's `sessions` key lists, each a list of strings, none listed and none read, and SHALL book their cost as two
stations of a change, `plan` and `operator`, beside the stations a run spawns, in the `stations` of `review-metrics.json` and
as columns of the page's cost table. It SHALL read from a transcript only the line's `type`, `timestamp` and `cwd`, an assistant
message's `id`, `model` and `usage`, a tool call's name and id, the `brief=` and `from=` tokens of an `mf-plan` call, the path
of a `Write` or `Edit` call, whether a `Bash` call runs `conduct.py cut`, and the ids of a `cut: queued <id>` line, and SHALL
write numbers, change ids and times, never text or a path. It SHALL read a session only when it holds a call of a skill named
`mf-*` or of `conduct.py`. A `brief=$NAME` or `brief=${NAME}` token of a command SHALL be read as the value of an earlier
`NAME=<value>` word of the same command, and as written when no word assigns the name.

A message SHALL be priced once by its `id`, its tokens priced by `prices.toml` under its model, a gap with no row; a message
with no token is no turn. A session whose id a station log's `init` event names SHALL be skipped, with its subagents: the run's
own spawn, booked under its station. A subagent's messages SHALL be booked at the time of the call its `meta.json`'s
`toolUseId` names.

A **plan span** SHALL open at a `Skill` call of `mf-plan` carrying `brief=<path>` and close at the last `Write` or `Edit` in the session of that
path or of a brief it continues with `from=` or is continued by; every later message SHALL be operator work. A span SHALL be bound
to the ids of the `cut: queued <id>` lines in the results of a `conduct.py cut` call naming the same `brief=`, a line counting
only when `<id>` has a change folder in a repo read and a cut log of that change written after the call; a span that queued
several ids SHALL be split equally among them, a span that queued none booked `unbooked`, and a `from=` continuation in a later
session SHALL join the span of the brief it continues. Every message outside a span SHALL be `operator`, booked to the open
version the nearest earlier mark names — a valid `cut: queued` line, or a run-log line naming a change — else `unbooked`. A
session whose first `cwd` names a repo read, as that folder, one under it, or a worktree of it, SHALL take the marks of that
repo alone.

#### Scenario: No sessions key
- **WHEN** the config holds no `sessions` key
- **THEN** no transcript is read and `review-metrics.json` holds no `plan` or `operator` row

#### Scenario: A plan span, operator work and an unbooked plan
- **WHEN** a listed session holds an `mf-plan` call with `brief=<path>`, a write of that path, a `conduct.py cut` naming it whose result says `cut: queued <id>` for a change with a folder and a later cut log, then more messages, and a second plan whose brief no cut names
- **THEN** the first span's messages are `plan` rows of `<id>`, the later messages `operator` rows booked by the nearest earlier mark, and the second span a `plan` row with no repo and no change, `unbooked`

#### Scenario: A span that queued two versions
- **WHEN** one `conduct.py cut` naming a span's brief queued two valid ids
- **THEN** each id holds half of the span's dollars, turns, tokens and seconds

#### Scenario: A continuation joins its plan
- **WHEN** a later session holds an `mf-plan` call with `from=` naming the earlier brief
- **THEN** its span is booked with the earlier span's, to the same ids

#### Scenario: A station's own session
- **WHEN** a transcript's session id is the one a station log's `init` event names
- **THEN** no row is booked from it

#### Scenario: A forged queue line
- **WHEN** a line `cut: queued <id>` appears in a result of a call that is no `conduct.py cut`, or `<id>` has no change folder or no cut log after the call
- **THEN** it binds nothing, and the span is `unbooked`

#### Scenario: A secret in a message
- **WHEN** a transcript's message text, command and results hold a planted secret string and the brief's path
- **THEN** neither the page, `review-metrics.json` nor the printed summary holds any byte of either

#### Scenario: One usage per message
- **WHEN** a transcript holds several lines of one message `id`
- **THEN** its usage is priced once

#### Scenario: A brief named by a variable
- **WHEN** a `conduct.py cut` command reads `B=<brief>; … brief=$B`
- **THEN** the span of that brief is bound to the ids the call queued

#### Scenario: A session in one repo, a mark in another
- **WHEN** two repos each hold a mark, a session's first `cwd` is the second repo, and the first repo's mark is the nearer
- **THEN** the session's operator messages book to the second repo's mark

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL also decide the `Verify:` sequencing rows `V1` to `V6` — a needle an earlier
task already adds, a `-k` that selects tests a later task adds or deletes, a `git grep` of a file not committed before its
phase ends, a needle its task never names, a `pytest` command that names no test path, a needle a later task removes — and the record's consistency rows `K1` to `K6` — the proposal's `## Impact` against
the tasks' files, the design's `## Tests` against the tasks' test files, the decision index against the decision headings, each
decision a task cites, each cited Step and constant, and two tasks on one line. It SHALL print each row it leaves to judgment —
`I5` to `I10`, `I15`, `I16`, `P12` and `P13`'s paragraphs — and a summary line, and exit 1 on a mechanical failure, which the
cut SHALL fix and run again. The self-check SHALL write that summary line and the judgment rows only. `gate_check.py --tasks`
SHALL be called the gate-edit check in the cut's prose. `facts.py readers` SHALL also take `--signature <name>`, printing the
stand-ins and the monkeypatches of that name; `--file <path>`, printing the lines that name the file by its quoted basename and
the imports of its module; and `--string <text>`, printing each line holding the text as written; each kind SHALL print `none`
when it finds nothing. `mf-plan`'s re-measure of a continued brief SHALL run `facts.py` and re-read only the facts it leaves
unplaced.

#### Scenario: A precondition fails
- **WHEN** the tree is dirty, the id is taken, or `make -n gate` lists no command
- **THEN** `cut_pre.py` prints a line naming that check, exits 1, and the cut halts

#### Scenario: Every precondition holds
- **WHEN** each check holds
- **THEN** `cut_pre.py` prints one line per check and exits 0

#### Scenario: The readers of a deleted name
- **WHEN** a task deletes `_old_name`
- **THEN** `facts.py readers _old_name` prints each `git grep -nw` hit at `HEAD` with its `path:line`, or `none`, and the cut
  names each reader in a task

#### Scenario: The stand-ins of a changed signature
- **WHEN** a task changes the signature of `_run`, and a test holds `monkeypatch.setattr(mod, "_run", fake)`
- **THEN** `facts.py readers --signature _run` prints that line as a `monkeypatch of _run`, with its `path:line`, and the cut
  names that test in a task

#### Scenario: The readers of a changed file
- **WHEN** a task renames `scripts/tool.py`, a test loads it by `"tool.py"` and another holds `import tool`
- **THEN** `facts.py readers --file scripts/tool.py` prints the first as a `runpy reader` and the second as an `import reader`

#### Scenario: The readers of a changed string
- **WHEN** a task changes the text `Opus 5.5 · high`
- **THEN** `facts.py readers --string "Opus 5.5 · high"` prints each line holding it, `git grep -F` at `HEAD`

#### Scenario: A mechanical failure
- **WHEN** a sub-task of `tasks.md` has no `Verify:`, or the design has no `## Tests` section
- **THEN** `cut_check.py` prints the failed row, exits 1, and the cut fixes the file and runs it again

#### Scenario: A needle an earlier task adds
- **WHEN** a sub-task's `Verify:` greps a needle in a file that an earlier sub-task names and quotes the needle of
- **THEN** `cut_check.py` prints the failed row `V1` naming both sub-tasks, and exits 1

#### Scenario: A whole-suite pytest
- **WHEN** a sub-task's `Verify:` runs `pytest` with no test path, or with `-m "not slow"` alone
- **THEN** `cut_check.py` prints the failed row `V5` naming the sub-task and asking for the test files, and exits 1

#### Scenario: A needle a later task removes
- **WHEN** a sub-task's `Verify:` greps a needle in a file, and a later sub-task naming that file holds a fenced `diff` block with the needle in a removed line
- **THEN** `cut_check.py` prints the failed row `V6` naming both sub-tasks, and exits 1

#### Scenario: A record that disagrees with itself
- **WHEN** a task links `design.md#d9` and `design.md` has no `### D9` heading
- **THEN** `cut_check.py` prints the failed row `K4` naming the task, and exits 1

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts
