## MODIFIED Requirements

### Requirement: A fresh worker reviews the plan before the cut commits

After its self-check, `skills/mf-cut-change/SKILL.md` SHALL hand a fresh read-only worker the **review packet**: the change
directory, `HEAD`, the cut's notes file, the output of `cut_check.py` and one question — whether each task can be built as
written, each `Verify:` pass after it, and each the search script did not run fail before it, save a `**HALT CHECK**`, which
should hold. The reviewer SHALL take each row `cut_check.py` printed as met, and each `facts.py readers` line of the notes, as
settled, and judge the rows it printed to judge. Every plan reviewer SHALL run on Sonnet 5.5 at `high` effort where the host
offers it, whatever model the cut runs on. The reviewer SHALL start from the packet, opening another file only at a `path:line`
the change or the notes cite. Its prompt SHALL give it a budget of 25 turns; a review that reaches it SHALL return its doubts so
far under a first line `budget reached`, and the cut SHALL take each of them as a doubt still standing after the second review.
The cut SHALL count each reviewer's tool calls from its transcript and, when they pass the budget, append a line naming the
review and its calls to `.minions/changes/<change-id>/cut-notes.md`. The cut SHALL fix a
simple doubt itself — a check that cannot pass or breaks `I19`, a reader a deletion missed, a task two readings would build
differently — re-running the search script; a doubt that changes a settled decision, or one still standing after a second
review, SHALL go to the person. A second review SHALL run only when a fix after the first — the cut's, the person's or the
switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `decided by the cutter` row included, or adds or
removes a task; a simple fix SHALL NOT be reviewed again. Before the first review, the cut SHALL stage the change directory
and record its tree; a second review SHALL be given the packet and the change directory's diff since that tree, and SHALL
judge that diff, and each task that cites a decision or a path the diff changes. Every plan review SHALL be a new worker given its packet; a message to an
earlier reviewer SHALL NOT be a review. An unattended cut SHALL instead take such a doubt's recommended option when the brief says
`decide: recommended`, adding a `decided by the cutter` row to the brief, and else SHALL halt in `cut.halt`, committing
nothing. Before writing, the cut SHALL place each fact of the brief with `facts.py`, which reads a fact on an unmoved path as
standing and a fact whose lines moved as moved to its new range, and leaves each other fact unplaced; the cut SHALL re-read
no fact the script placed. Where the host starts fresh workers, up to four read-only helpers SHALL read the unplaced
facts in parallel, each on Sonnet 5.5 at `medium` effort where the host offers it, a helper not back in five minutes having
its facts read by the cut; with no unplaced fact no helper SHALL start. No helper SHALL write a file: the cut SHALL write each
answer, and each fact it reads for the design, to `.minions/changes/<change-id>/cut-notes.md`, and SHALL read that file in
place of a file already read. Before writing, the cut SHALL also name each symbol, key or file the change deletes or renames
to `facts.py readers`, which `git grep`s it at `HEAD`, a changed signature, file or string by its own flag, and name each
reader in a task, and SHALL read the target's `CODING_STANDARDS.md` and `CONTRIBUTING.md`, planning to a target's own test rule
over `T1`–`T6`.

#### Scenario: A deletion with a reader
- **WHEN** a change deletes a symbol a test still reads
- **THEN** the cut names that test in a task before it commits

#### Scenario: A design premise the code rules out
- **WHEN** the review finds a task the code cannot satisfy as the decision states it
- **THEN** the cut shows the doubt to the person with its `path:line`, and waits
- **AND WHEN** the cut is unattended and the brief does not say `decide: recommended`
- **THEN** it writes the doubt and its `path:line` to `cut.halt`, and commits nothing

#### Scenario: A brief at the cut's own commit
- **WHEN** every fact's file is untouched since its sha
- **THEN** `facts.py` places each as standing, and no helper starts

#### Scenario: A fact whose file moved
- **WHEN** a brief's fact cites lines of a file that changed since its sha, and every cited line's text is unchanged
- **THEN** `facts.py` places it as moved to the new range, and the cut writes that to `cut-notes.md`

#### Scenario: An unplaced fact
- **WHEN** a brief's fact cites a changed line, a deleted file, or a sha that names no commit
- **THEN** `facts.py` leaves it unplaced, and a helper, or the cut, reads that fact at `HEAD`

#### Scenario: The helpers' answers
- **WHEN** a helper answers a fact `moved to skills/x/SKILL.md:40`
- **THEN** the cut writes that answer to `cut-notes.md`, and the helper writes no file
- **AND** the review packet names `cut-notes.md`

#### Scenario: A simple fix
- **WHEN** the first review's only doubts are a check that cannot pass and a task two readings would build differently,
  and the cut's fixes change no decision and add or remove no task
- **THEN** the cut re-runs the search script and goes on to Step 9 with no second review

#### Scenario: A fix that adds a task
- **WHEN** the cut's fix after the first review adds a task, or changes a `design.md` decision
- **THEN** a second review runs, by a new worker given the packet and the change directory's diff since the first review
- **AND** no message goes to the first reviewer

#### Scenario: A review reaches its budget
- **WHEN** a plan review reaches its 25th turn with one doubt found
- **THEN** it returns that doubt under a first line `budget reached`
- **AND** the cut takes the doubt as one still standing after the second review: the person's, or under the switch the
  recommended option

#### Scenario: A review passes its budget
- **WHEN** a reviewer's transcript holds more tool calls than its budget
- **THEN** the cut appends a line naming that review and its calls to `cut-notes.md`

#### Scenario: A cut on another model
- **WHEN** the cut runs on Opus 5.5 and the host offers Sonnet 5.5
- **THEN** each plan review runs on Sonnet 5.5 at `high` effort

#### Scenario: A packet with a mechanical row
- **WHEN** `cut_check.py` prints a row as met
- **THEN** the reviewer's packet holds that output, and the reviewer re-checks no such row

#### Scenario: A packet with a readers line
- **WHEN** `facts.py readers` wrote a line to `cut-notes.md` for a changed signature
- **THEN** the reviewer takes that line as settled and searches for no stand-in of that name

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL also decide the `Verify:` sequencing rows `V1` to `V4` — a needle an earlier
task already adds, a `-k` that selects tests a later task adds or deletes, a `git grep` of a file not committed before its
phase ends, a needle its task never names — and the record's consistency rows `K1` to `K6` — the proposal's `## Impact` against
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

#### Scenario: A record that disagrees with itself
- **WHEN** a task links `design.md#d9` and `design.md` has no `### D9` heading
- **THEN** `cut_check.py` prints the failed row `K4` naming the task, and exits 1

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts
