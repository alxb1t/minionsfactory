## ADDED Requirements

### Requirement: A run checks each cut with the cut's checker

After the cut commit, the station's `check` for a queued cut SHALL run `skills/mf-cut-change/scripts/cut_check.py <id> --bump <bump>` in the cut's worktree, under the sandbox runner, on the conductor's own Python, once `_check_cut` and the dependency check pass. Each run of the checker, and of each declared check, SHALL end after 1800 s, keep the last 2000 lines of its output, and write to the cut's worktree and the run directory alone. Exit 0 SHALL pass the cut; exit 1 with a `cut_check: halt — ` line in its output SHALL write its failing lines to `.minions/changes/<id>/cut.red`; exit 2, an exit 1 with no such line, or a run that cannot start, SHALL halt the cut as `the cut check cannot run`, naming the last line of the run's output, or the first line of the error that kept it from starting. A first failure of a branch the call cut SHALL reset the worktree to the default branch, remove `cut.halt`, and start the cutter once more, its prompt naming `cut.red`; the checks SHALL then run again, and a second failure SHALL reset the worktree to the default branch again, so the branch holds no change, and halt the cut, naming the first failing line. A branch the run found already holding the change and failing SHALL halt the cut at once, and nothing SHALL be reset. `skills/mf-cut-change/SKILL.md` SHALL have an unattended cut that finds `cut.red` read it with the brief.

#### Scenario: A cut whose checker passes
- **WHEN** the cutter commits a change directory and `cut_check.py` exits 0
- **THEN** the cut passes, and the version goes on as before

#### Scenario: A cut that fails once
- **WHEN** `cut_check.py` exits 1 printing a `cut_check: halt — ` line on the first cut
- **THEN** the lines go to `cut.red`, the worktree is reset to the default branch, and a second cutter starts with a prompt naming `cut.red`
- **AND WHEN** the second cut passes the checks
- **THEN** the cut passes

#### Scenario: A cut that fails twice
- **WHEN** the second cut's check exits 1 too
- **THEN** the worktree is reset to the default branch, so the branch holds no change, the cut halts as `the cut check failed twice`, naming the first failing line, and no third cutter starts

#### Scenario: A checker that cannot run
- **WHEN** `cut_check.py` exits 2, or exits 1 on a traceback with no `cut_check: halt — ` line, or the sandbox cannot start it
- **THEN** the cut halts as `the cut check cannot run`, naming the last line of the checker's output, and starts no second cutter

#### Scenario: A rejoin's branch fails
- **WHEN** a person amends a halted cut's branch and a rejoin finds the check still failing
- **THEN** the cut halts at once, and the person's amend stays on the branch

### Requirement: A repository declares the checks a cut passes

A repository MAY declare `**Cut checks:**` in its root `AGENTS.md`: a line of backticked commands. After `cut_check.py` passes, the station SHALL read the line from the primary checkout's `AGENTS.md`, never the cut's, and run each command, split into words and with no shell, in the cut's worktree under the sandbox runner. A command that exits non-zero, or cannot start, SHALL fail the cut check, its command and the last 20 lines of its output going to `cut.red`, on the route of *A run checks each cut with the cut's checker*. A file the checker or a declared command leaves in the cut's worktree SHALL fail the cut check too, `cut.red` naming the files, on the same route. A repository that declares no line SHALL run none. `skills/mf-cut-change/SKILL.md` SHALL say that the conductor runs these commands and the cut runs none; `skills/mf-bootstrap/templates/AGENTS.md.tmpl` SHALL name the line; MF's own `AGENTS.md` SHALL declare none. The cut SHALL still run no gate.

#### Scenario: A declared command passes
- **WHEN** `AGENTS.md` declares `**Cut checks:** `true`` and the checker passes
- **THEN** the cut passes

#### Scenario: A declared command fails
- **WHEN** a declared command exits 1 printing a line
- **THEN** the cut check fails, `cut.red` holds the command and the line, and the route of a failed check runs

#### Scenario: A declared command leaves a file
- **WHEN** a declared command exits 0 and writes `junk.txt` in the cut's worktree
- **THEN** the cut check fails, `cut.red` names `junk.txt`, and the route of a failed check runs

#### Scenario: A repository declares none
- **WHEN** root `AGENTS.md` holds no `**Cut checks:**`
- **THEN** the station runs no command beyond the checker

### Requirement: A plan holds no phase a person does

`cut_check.py`'s `I14` SHALL fail each phase line of `tasks.md`, under `## Progress` or not, that holds `**HUMAN`, saying a person's step comes after the release; no other row SHALL exempt such a phase, and `verify_check.py` SHALL read its `Verify:` as any other's. `brief_check.py` SHALL exit 1, naming the line, when a line of the brief's `## Phases` holds `**HUMAN`. The `I14` row of `skills/mf-cut-change/SKILL.md` and `skills/mf-build/SKILL.md` SHALL state the refusal, and the ids of both tables SHALL stay equal and run unbroken. For a version cut before, `conduct.py` SHALL still halt it at a phase marked `**HUMAN` with no rescue, `plan_check.py` SHALL still skip such a phase's `Verify:`, and `skills/mf-build/SKILL.md` SHALL still halt on an unworked one with the person's checklist: one line per step, each command in an `sh` block, secrets by env-var name, the closing checks, and `Next: /mf-build`.

#### Scenario: The cut refuses a person's phase
- **WHEN** a `tasks.md` lists `- [ ] 2 — Tag the release **HUMAN`
- **THEN** `cut_check.py` prints the failed row `I14` naming phase 2, with any other row the line fails, and exits 1

#### Scenario: A brief marks a person's phase
- **WHEN** a line of the brief's `## Phases` holds `**HUMAN`
- **THEN** `brief_check.py` exits 1, naming the line

#### Scenario: A version cut before is read as it was
- **WHEN** a version cut before holds a phase marked `**HUMAN`
- **THEN** the conductor halts it at that phase with no rescue, and the plan check skips its `Verify:`

#### Scenario: The build meets an unworked phase of a version cut before
- **WHEN** `mf-build` runs that phase's `Verify:` checks and one fails
- **THEN** it halts with the person's checklist: one line per step, each command in an `sh` block, secrets by env-var name, the closing checks, and `Next: /mf-build`

### Requirement: The build edits a file no task names when its check needs it

`skills/mf-build/SKILL.md` SHALL have a worker whose `make check` is red, with an output naming a file no task of the phase names, edit that file when the edit turns the check green, and list it in the commit body, one `Unplanned: <path>` line a file before the trailer block. `skills/mf-converge/references/worker.md` SHALL give conformance an `unplanned-file` pass: each file of the freeze's diff that no task names, save `CHANGELOG.md` and the change's own `openspec/changes/<change-id>/` folder, which the build writes every phase, and save a file changed only by a commit the change's converge status log names as a fix's, whose files stand on its cards, SHALL stand on an `Unplanned:` line of a commit in range; a file so listed and needed by a red check SHALL be a `nit`, and one changed with no such line, or past what the check needed, SHALL be `blocking`. The `I6` and `I7` rows of both skills SHALL still ask a task to name its files, and SHALL say the build answers a file a task misses.

#### Scenario: A red check needs an unnamed file
- **WHEN** a phase's `make check` is red on a fixture no task names, and editing it turns the check green
- **THEN** the worker edits it, and the commit body holds `Unplanned: tests/fixtures/a.json` before the trailer block

#### Scenario: Conformance judges the unplanned file
- **WHEN** the freeze's diff changes a file no task names, other than `CHANGELOG.md` and the change's own folder
- **THEN** conformance opens a `nit` when an `Unplanned:` line lists it and a red check needed it, and a `blocking` card when no line lists it
- **AND WHEN** the file is changed only by a commit the status log names as a fix's
- **THEN** the pass leaves it out
- **AND WHEN** the file is `CHANGELOG.md`, or under `openspec/changes/<change-id>/`
- **THEN** the pass opens no card for it

## MODIFIED Requirements

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL also decide the `Verify:` sequencing rows `V1` to `V8` — a needle an earlier
task already adds, a `-k` that selects tests a later task adds or deletes, a `git grep` of a file not committed before its
phase ends, a needle its task never names, a `pytest` command that names no test path, a needle a later task removes, a command
whose first word is no program on `PATH`, no path of the tree and no path a task names, and a `-k` that selects no test of the files it
names at `HEAD` and none a task names — and the record's consistency rows `K1` to `K7` — the proposal's `## Impact` against
the tasks' files, the design's `## Tests` against the tasks' test files, the decision index against the decision headings, each
decision a task cites, each cited Step and constant, two tasks on one line, and a line of `design.md` outside `## Tests`, or of
`proposal.md`, that names a backticked identifier a task removes with no removal word. It SHALL print each row it leaves to
judgment — `I5` to `I10`, `I15`, `I16`, `P12` and `P13`'s paragraphs — and a summary line, and exit 1 on a mechanical failure,
which the cut SHALL fix and run again. The self-check SHALL write that summary line and the judgment rows only.
`gate_check.py --tasks` SHALL be called the gate-edit check in the cut's prose. `facts.py readers` SHALL also take
`--signature <name>`, printing the stand-ins and the monkeypatches of that name; `--file <path>`, printing the lines that name
the file by its quoted basename and the imports of its module; and `--string <text>`, printing each line holding the text as
written; each kind SHALL print `none` when it finds nothing. `mf-plan`'s re-measure of a continued brief SHALL run `facts.py`
and re-read only the facts it leaves unplaced.

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

#### Scenario: A first word that names nothing
- **WHEN** a sub-task's `Verify:` runs `nosuchtool --check`, and no sub-task names a path `nosuchtool`
- **THEN** `cut_check.py` prints the failed row `V7` naming the sub-task, and exits 1
- **AND WHEN** the first word is `git`, a file of `HEAD`'s tree, or a path a sub-task names
- **THEN** the row holds

#### Scenario: A -k that selects nothing
- **WHEN** a sub-task's `Verify:` runs `pytest tests/test_a.py -k typo`, and neither `tests/test_a.py` at `HEAD` nor any sub-task names a test that `typo` selects
- **THEN** `cut_check.py` prints the failed row `V8` naming the sub-task, and exits 1
- **AND WHEN** the expression selects a test of that file at `HEAD`, or a `test_` name a sub-task names
- **THEN** the row holds

#### Scenario: A design line that names a removed name
- **WHEN** a sub-task says it deletes `_old_name`, and `design.md` outside `## Tests` has a line naming `_old_name` with no removal word
- **THEN** `cut_check.py` prints the failed row `K7` naming the line, and exits 1
- **AND WHEN** that line says the name is removed or renamed
- **THEN** the row holds

#### Scenario: A record that disagrees with itself
- **WHEN** a task links `design.md#d9` and `design.md` has no `### D9` heading
- **THEN** `cut_check.py` prints the failed row `K4` naming the task, and exits 1

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts

### Requirement: A Verify: is one plain command and counts honestly

The input contract SHALL hold `I19`: a `Verify:` is one plain command — no `$(…)`, no shell variable, no loop, no `cd` — and an
exact count only when the count is the point. `skills/mf-cut-change/scripts/verify_check.py` SHALL exit 1 on a check that breaks
the shape or passes a search an option outside its fixed list or a path outside the repository, 0 printing each search's matches
as `path:line`, and 2 on a
`Verify:` it cannot parse, a `git grep` git refuses, or a `grep` whose paths it cannot judge because `HEAD`'s tree holds a link out of
it, naming the sub-task. A `git grep`'s paths SHALL be judged without exporting the tree.

It SHALL also refuse, naming the sub-task, a count stated on any search but `grep -c` or `grep --count` over one file operand with
no `-r` or `-R`, `-L` and `--files-without-match` among the options, and, in a sub-task that is no `**HALT CHECK**`, a word
other than a search pattern shaped `<path>:<digits>` or `<path>:<digits>-<digits>`, a search pattern of three or more plain
words, and a range `<default>..HEAD` or `<default>...HEAD`, `origin/` allowed before the default branch and `HEAD` left out, a
search pattern being no range. The one absence form is a `git grep -c`
printing nothing.

It SHALL refuse too, naming the sub-task and the span, a `Verify:` in which two commands of the plan
check's parse stand in one clause with an output verb between them — no `then`, `;`, sentence end or `Verify:` label, and no
`, and` or `, or` before a span an output verb follows, between the earlier command and the later one; an `e.g.` or an `i.e.`
SHALL end no output. It SHALL read a `**HUMAN` phase's `Verify:` as any other's.

#### Scenario: A loop in a check
- **WHEN** a `Verify:` reads `for i in $(seq 20); do … done`
- **THEN** `verify_check.py` exits 1, naming the sub-task

#### Scenario: A search with a stray match
- **WHEN** a `Verify:` greps a pattern a line the design never names already matches
- **THEN** `verify_check.py` prints that line as `path:line`, and the cut accounts for it before its commit

#### Scenario: A tree that tracks a link out of it
- **WHEN** the repository tracks `link -> /usr/share`, and one `Verify:` is a `git grep` with a path and another a `grep`
- **THEN** the `git grep` check exits 0 printing its match, and the `grep` check exits 2 naming its sub-task and the link

#### Scenario: A count off its one form
- **WHEN** a `Verify:` says `git grep -c x -- a.md` prints `1`, or `grep -c x a.md b.md` prints `1`, or `grep -n x a.md` prints `1`
- **THEN** `verify_check.py` exits 1, naming the sub-task
- **AND WHEN** a `Verify:` says `grep -c x a.md` or `grep --count x a.md` prints `1`, or `git grep -c x -- a.md` prints nothing
- **THEN** it halts nothing

#### Scenario: A command after an output verb
- **WHEN** a `Verify:` says that `printf 1` prints one integer, a space and `pyproject.toml`, or prints a line of `a.md`
- **THEN** `verify_check.py` exits 1, naming the sub-task and the span
- **AND WHEN** a `Verify:` says that `printf 1` exits `0`, and `printf 2` prints `2`, or that `printf 1` prints `1`, then
  `printf 2` exits `0`, or that `printf 1` and `printf 2` exit 0
- **THEN** it halts nothing

#### Scenario: An Oxford comma or an e.g. before a command
- **WHEN** a `Verify:` says that `printf 1` prints one integer, a space, and `pyproject.toml`, or prints one integer, e.g. `3`
- **THEN** `verify_check.py` exits 1, naming the sub-task and the span

#### Scenario: A search for a range's text
- **WHEN** a `Verify:` runs `git grep -n origin/main... -- docs/`
- **THEN** `verify_check.py` halts nothing for a range: the pattern is no range

#### Scenario: An option that hides the path
- **WHEN** a `Verify:` runs `grep -L x a.md` or `git grep --files-without-match x`
- **THEN** `verify_check.py` exits 1, naming the sub-task

#### Scenario: A form of a plain check
- **WHEN** a plain `Verify:` runs `git diff main..HEAD -- a.md`, or names `a.py:12-20`, or greps `three plain words`
- **THEN** `verify_check.py` exits 1, naming the sub-task
- **AND WHEN** the sub-task is a `**HALT CHECK**`
- **THEN** it halts nothing for these forms

### Requirement: A moderate phase builds on its own model

`skills/mf-cut-change/SKILL.md` SHALL end each `## Progress` line with ` · moderate` or ` · hard`: `hard`
when the phase matches the strongest-tier row of its *Suggesting models* table, `moderate` otherwise. `conduct.py` SHALL run a
phase whose line ends ` · moderate` on the models file's `[build.moderate]` model and effort, on `[build]`'s executor, when
that table names a model or an effort; every other phase, and a phase with no rating among them, SHALL run on
`[build]`'s. The close SHALL run on the models file's `[build.close]` model and effort, else `[build.moderate]`'s, else `[build]`'s, each key from the first table that names it, on `[build]`'s executor; the brief's models line SHALL take the part `build-close <model> <effort>` after `build-moderate`, with no host. A `[build.moderate]` or `[build.close]` naming an `executor`, a model or effort outside `[A-Za-z0-9._-]`, or a `claude-*` model on a
Codex build SHALL halt the version before its worker starts. The run SHALL read `[build.moderate]` and `[build.close]` once with its plan.

#### Scenario: A moderate and a hard phase
- **WHEN** a version's models file holds `[build]` with `claude-opus-5-5` and `[build.moderate]` with `claude-sonnet-5-5` at
  `high`, phase 1 ends ` · moderate` and phase 2 ` · hard`
- **THEN** phase 1's worker runs on `claude-sonnet-5-5` at `high`, and phase 2's on `claude-opus-5-5`

#### Scenario: No moderate table
- **WHEN** the models file holds no `[build.moderate]`
- **THEN** every build worker but the close runs on `[build]`'s model

#### Scenario: A moderate table names a host
- **WHEN** `[build.moderate]` names `executor = "codex"`
- **THEN** the version halts naming the table, and no worker starts for it

#### Scenario: A close table
- **WHEN** the models file holds `[build]` with `claude-opus-5-5`, `[build.moderate]` with `claude-sonnet-5-5` at `medium`, and `[build.close]` with `claude-sonnet-5-5` at `high`
- **THEN** the close's worker runs on `claude-sonnet-5-5` at `high`, and without `[build.close]` at `medium`, and with neither on `claude-opus-5-5`

#### Scenario: A close table names a host
- **WHEN** `[build.close]` names `executor = "codex"`, or the brief's models line writes `build-close codex/m high`
- **THEN** the version halts naming the table, or the brief check fails, and no worker starts for it

## REMOVED Requirements

### Requirement: A HUMAN phase is handed over as a checklist of commands

**Reason:** the cut refuses a phase a person must do, so it writes no such phase and no sub-task of one needs commands with real values.

**Migration:** *A plan holds no phase a person does* states the refusal and keeps the build's checklist for a version cut before.
