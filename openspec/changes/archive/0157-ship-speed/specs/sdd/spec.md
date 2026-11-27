## ADDED Requirements

### Requirement: The conductor runs a quick plan check after each phase

After a build phase's worker passes its check, `conduct.py` SHALL, for each phase of `## Progress` but the last, run `plan_check.py --change <change-id> --base <base> --quick` in the version's worktree, under the sandbox runner, its `<base>` the one the close's plan check takes. It SHALL run it beside the gate it runs after the last phase, once the phase is ticked at `HEAD` and the tree is clean, over every ticked sub-task, those of earlier phases included. A failure SHALL fail the build check as `plan check: plan_check.py --quick exit <code> · <the last line it printed>`, and SHALL write `build.halt` with `sub-task: phase <N>`, `stop: plan check`, the evidence and `head:`, so the version halts as a failed build check does and the rescue's amend of `tasks.md` answers it. A phase worker's own check SHALL stay a read of the boxes and the tree. The last phase SHALL run no quick check: the close's whole plan check follows it.

#### Scenario: A later phase breaks an earlier search
- **WHEN** phase 3 of four removes a line that a ticked `git grep` `Verify:` of phase 1 finds, and phase 3's worker passes its own check
- **THEN** the conductor's quick plan check prints a line for that sub-task and exits 1, the build check fails as `plan check: …`, and `build.halt` names `phase 3`
- **AND** no `pytest` runs for it

#### Scenario: The last phase
- **WHEN** the last phase's worker passes its check
- **THEN** the conductor runs no quick plan check, and the gate and the close follow as before

#### Scenario: A phase whose checks hold
- **WHEN** every ticked `Verify:` command that runs no `pytest` test and no `make` passes, and each ticked `pytest` `Verify:` that says it exits 0 collects a test
- **THEN** the quick plan check exits 0 and the next phase is spawned

## MODIFIED Requirements

### Requirement: A plan check holds the plan to the built tree

`skills/mf-converge/scripts/plan_check.py --change <id> --base <rev>` SHALL exit 1, printing one `plan: ` line per problem,
when: the command of a ticked sub-task's `Verify:`, run again as argv with no shell from the repository root, exits non-zero,
save a search whose `Verify:` says `prints nothing` or `` prints `0` ``, which passes on exit 1 printing nothing, or `0` alone
for `` prints `0` ``; that command exits 0 printing anything where its `Verify:` says it `prints nothing`, or printing other
than the number alone where it says it `` prints `<N>` `` or `` reports `<N>` ``; a
`- [ ] N.M` box stands unticked under a ticked `## Progress` phase; a name the diff from the merge base of `<rev>` and `HEAD`
removes — a Python `def` or `class` name, or an upper-case module-level name, that nothing outside `openspec/` names at
`HEAD`, or the base name of a file the diff deletes — is still named, as a word, on a line of `openspec/specs/` or of the
change directory outside `tasks.md` and `design.md`'s `## Tests` section, that line holding no word of removal and, in
`openspec/specs/<capability>/spec.md`, standing in no requirement the change's `specs/<capability>/spec.md` lists under
`## REMOVED Requirements`; a `def test_`
name under `tests/` at the merge base is gone at `HEAD` and `design.md`'s `## Tests` section does not name it; or a sub-task
marked `**CORPUS**` names a case `scripts/corpus.toml` does not hold. Without `--only` it SHALL NOT run again a `**HALT CHECK**`
sub-task's command; with or without it, it SHALL NOT run again a command of a `**HUMAN` phase, or a command one of whose words has
the file name `plan_check.py`, and SHALL run no command with a shell. It SHALL exit 0 printing `plan: clean` when none holds, and
2 when it cannot read `tasks.md`, the base or git, or when `--only` names a sub-task outside a `**HUMAN` phase whose `Verify:`
holds no command.

It SHALL read a `Verify:`'s spans as follows: a span whose word right before it is an output verb — `prints`, `exits` and the
like — is output, never a command, and so is each later span until a `then`, a `;`, the sentence's end or a `Verify:` label; a
`, and` or `, or` before a span that a verb follows opens a new command. No other word SHALL open output: a span with words
between an output verb and it, and no span between them, is a command. A command whose `Verify:` says it
`` exits `<N>` `` SHALL pass only on exit `<N>`, and on the output the `Verify:` says; the search that passes on exit 1 is the one
whose `Verify:` names no exit. It SHALL run each command without `VIRTUAL_ENV` in its environment, SHALL compare a command's stdout
alone with what the `Verify:` says, keeping its stderr apart, and SHALL show the first lines of both on a failure.
`skills/mf-cut-change/scripts/verify_check.py` SHALL read a `Verify:`'s commands through this script's parser, loaded
from it, and keep no parser of its own.

It SHALL judge in groups, and a group that fails SHALL print its lines and end the check before the next group starts, a group
whose only lines say `timed out` ending nothing, as such a line is no finding. The
**reads** group comes first: the unticked boxes, the removed names, the base's tests and the corpus cases, which run no command. The
**quick** group follows: every `Verify:` command that is no `pytest` run and no `make`, a `pytest` with `--collect-only` included, and the collection —
the command with `--collect-only -q` appended — of each `pytest` `Verify:` that says it exits 0 and no more, a collection that timed out printing
`timed out`, one that exits non-zero or finds no test printing `plan: <sub-task> — `<command>` collected no test`, and one that
exits 2 with its first lines of output. The **long** group is last: the `pytest` and `make`
commands, each a `pytest` the gate's green record vouches for left unrun. The commands of the quick group start before its
collections, and none of them waits behind a command of the long group. With `--only` the reads group is empty.

`--quick` SHALL judge the quick group alone, over the ticked sub-tasks as a plain check reads them, a `**HALT CHECK**` sub-task,
a `**HUMAN` phase and a command naming `plan_check.py` left out as there. It SHALL run no `pytest` test and no `make`, check no
box, name, test or corpus case, print `plan: clean` and exit 0 when no line is printed, and exit 2, naming both options, when
`--only` is given with it.

It SHALL run each distinct command once a check, whatever the number of sub-tasks that name it, and hold the one result to each
sub-task's own words. It SHALL run the commands of a group side by side, one slot for each core the machine has, and print the lines in
task order, then command order, whatever order they finish in: a `pytest` with `-n` takes every slot and runs alone, a `make`
runs one at a time, and every `pytest` starts with `-p no:cacheprovider` in its `PYTEST_ADDOPTS`. It SHALL start a command only
while the machine's 1-minute load is under its core count, and SHALL start one whatever the load when no command runs. A command
past its limit — the integer after `**Verify timeout:**` in the root `AGENTS.md`, in seconds and at most a day, else 600 — SHALL lose its whole
process group and print `plan: <sub-task> — `<command>` timed out`; ended by SIGTERM, the check SHALL end the
process group of each command then running. A `pytest` command — one whose argv starts `pytest`, `uv run pytest` or `python -m pytest` — whose `Verify:` says nothing of its
output beyond that it exits 0, and whose words after its pytest prefix are only quiet flags — `-q`, `-qq`, `-v`, `-vv`, `-x` or `-s` — `-n` or
`--numprocesses` with its value, `-k` with its value, and test paths and `::` nodes that exist, SHALL pass unrun when `gate_run.py` holds a
green record for the same tree and the same dry run of `make -n gate` and the command's own collection finds a test; one that says what it
prints, says it exits another code, names a `[` node or a path outside the repo's `testpaths`, or carries `-m`, `-c`, `--deselect` or any
other option still runs. On a settled tree the check SHALL keep each finished result — its exit, stdout and stderr — in
`.minions/plan-check/<tree>/`, named by the command, `HEAD` and every ref, and SHALL read it again on the same tree while
`HEAD` and every ref stand, whatever the command's words; a timed-out command SHALL be kept by no one, a result kept without its
stderr SHALL be read as none kept, and an unsettled tree
SHALL keep and read none. With
`--only <sub-task ids>` it SHALL run the `Verify:` commands of those sub-tasks alone, ticked or not, a `**HALT CHECK**` sub-task
it names included, with the other skips, print only their lines and check nothing else.

`conduct.py close` SHALL run it at the build's close, after the metrics and before `build.done`, its `--base` the sha `stacked-on` names while it stands and else the merge base of the default branch
and `HEAD`, and SHALL halt on any other exit than 0, writing no `build.done`. Converge's fixer SHALL run `--quick` in the foreground after
its check and before its commit, clearing each problem as a blocking card of the same pass, or setting it `wontfix` naming the
amend; converge's Step 7 SHALL run the whole check after `gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any
verify worker, counting no round, save a line that says a command timed out, which it SHALL send back to no one; a line the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the
run `amend needed — plan check: <subjects>`, naming each line's sub-task, `path:line` or test name and never the
command it quotes. `skills/mf-rescue/SKILL.md` SHALL take that halt as a fix of the lines `plan_check.py` prints, in `tasks.md` and
`design.md`'s prose.

#### Scenario: A ticked check that no longer holds
- **WHEN** at the build's close a ticked sub-task's `Verify:` command exits 1
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command, and the build halts with no `build.done`

#### Scenario: A ticked check that exits 0 with other output
- **WHEN** a ticked sub-task's `Verify:` says a search prints nothing and the search finds a match, or says `printf 1` prints
  `2`
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command
- **AND WHEN** its `Verify:` says `printf 1` prints `1`, or says a `grep -c` that finds nothing prints `0`
- **THEN** that check halts nothing

#### Scenario: An exit the Verify: names
- **WHEN** a ticked `Verify:` says that `false` exits `1`
- **THEN** `plan_check.py` prints no line for it
- **AND WHEN** a ticked `Verify:` says that `true` exits `1`, or says that `false` exits nothing
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command

#### Scenario: Spans after an output verb
- **WHEN** a ticked `Verify:` says that `printf 1` prints `1`, then `printf 2` prints `2`
- **THEN** both commands run
- **AND WHEN** it says that a search lists `a.py`, `b.py` and `c.py`
- **THEN** the search is the one command, and no file name is run

#### Scenario: Words between the verb and the span
- **WHEN** a ticked `Verify:` says that `printf 1` prints one integer, a space and `pyproject.toml`
- **THEN** `printf 1` and `pyproject.toml` are both commands, and `plan_check.py` reports the second
- **AND WHEN** it says that `printf 1` exits `0`, and `printf 2` prints `2`
- **THEN** both commands run
- **AND WHEN** it says that `printf 1` exits `0`, then the test that holds the guard, `printf 2`, exits `0`
- **THEN** both commands run

#### Scenario: A warning on stderr
- **WHEN** a ticked `Verify:` says a command prints `1`, and the command prints `1` on stdout and a warning on stderr
- **THEN** `plan_check.py` prints no line for it
- **AND WHEN** that command exits 1
- **THEN** the line shows its stdout and its stderr

#### Scenario: A command under a set VIRTUAL_ENV
- **WHEN** `VIRTUAL_ENV` is set in the environment of `plan_check.py`, and a ticked `Verify:` runs `printenv VIRTUAL_ENV`
- **THEN** the command prints nothing: it never saw the variable

#### Scenario: An unticked box under a finished phase
- **WHEN** `## Progress` ticks phase 2 and sub-task `2.3` stands unticked
- **THEN** `plan_check.py` exits 1, naming `2.3`

#### Scenario: A removed name still in the plan
- **WHEN** the diff removes `def _fence`, nothing outside `openspec/` names `_fence` at `HEAD`, and a `design.md` line names it
  with no word of removal
- **THEN** `plan_check.py` exits 1, naming that line
- **AND WHEN** the line says the change deletes `_fence`
- **THEN** that line halts nothing

#### Scenario: A removed name in a requirement the delta removes
- **WHEN** the diff removes `LIMIT`, and a line of `openspec/specs/cap/spec.md` names it with no word of removal
- **THEN** `plan_check.py` exits 1, naming that line
- **AND WHEN** the line stands in a requirement the change's `specs/cap/spec.md` lists under `## REMOVED Requirements`
- **THEN** that line halts nothing, and the same name in the next requirement, which the delta keeps, still exits 1

#### Scenario: A test the base had
- **WHEN** `def test_old` stands under `tests/` at the merge base and nowhere at `HEAD`
- **THEN** `plan_check.py` exits 1, naming `test_old`
- **AND WHEN** `design.md`'s `## Tests` section names `test_old`
- **THEN** it halts nothing

#### Scenario: A clean plan
- **WHEN** every ticked `Verify:` passes, every box under a ticked phase is ticked, and no removed name or base test is missing
- **THEN** `plan_check.py` exits 0 and prints `plan: clean`

#### Scenario: A fix that breaks a ticked check
- **WHEN** converge's fixer commits a fix and Step 7's `plan_check.py` exits 1
- **THEN** the conductor sends its lines to the fix station before any verify worker, and the round count stays
- **AND WHEN** the next Step 7's `plan_check.py` prints a line that fix pass was sent, naming sub-task `3.2`
- **THEN** converge halts `amend needed — plan check: 3.2`, and the rescue amends `tasks.md` or `design.md` to clear it

#### Scenario: A command named twice runs once
- **WHEN** sub-tasks `1.1` and `1.2` name the same command, `1.1` saying it prints `1` and `1.2` saying it prints nothing, and it prints `1`
- **THEN** the command runs once, and `plan_check.py` prints a line for `1.2` alone

#### Scenario: A bare pytest on a green gate
- **WHEN** a ticked `Verify:` says a `pytest` command exits 0, `gate_run.py` holds a green record for the same tree and the same dry run, and the command's collection finds a test
- **THEN** the command does not run, and `plan_check.py` prints no line for it
- **AND WHEN** the `Verify:` says the command prints `3`, or the tree or the dry run differs from the record's, or a test path lies outside the repo's `testpaths`
- **THEN** the command runs

#### Scenario: A collection that finds no test
- **WHEN** a ticked `Verify:` says a `pytest` command exits 0 and names a test file or node that does not exist, or selects no test with `-k`, whether or not a green record stands
- **THEN** its collection fails, `plan_check.py` prints `collected no test` for it, exits 1, and runs no `pytest`

#### Scenario: An option the green gate vouches
- **WHEN** a ticked `Verify:` says `uv run pytest tests/test_a.py tests/test_b.py -n auto -q -k test_one` exits 0, the record stands, and the collection finds a test
- **THEN** the command does not run, and `plan_check.py` prints no line for it
- **AND WHEN** the command carries `-m slow`, `-c other.ini`, `--deselect` or a `[` node
- **THEN** the command runs

#### Scenario: A cheap failure ends the check
- **WHEN** a ticked `git grep` `Verify:` exits 1 and a ticked `pytest` `Verify:` would run for minutes
- **THEN** `plan_check.py` prints the search's line, exits 1, and starts no `pytest`
- **AND WHEN** a box stands unticked under a ticked phase and a command also fails
- **THEN** only the box's line prints

#### Scenario: A quick check
- **WHEN** `plan_check.py --quick` runs over a ticked `git grep` that exits 1 and a ticked `pytest` `Verify:` that says it exits 0
- **THEN** it prints the search's line and exits 1, collects the `pytest` command and runs no test, and checks no box
- **AND WHEN** every command passes
- **THEN** it prints `plan: clean` and exits 0
- **AND WHEN** `--only` is given with `--quick`
- **THEN** it exits 2, naming both

#### Scenario: A result kept by tree
- **WHEN** `plan_check.py` runs a command on a settled tree and runs again on the same tree
- **THEN** the second check reads the kept result and does not run the command
- **AND WHEN** the tree is unsettled, or the command is another, or `HEAD` is another commit
- **THEN** the command runs
- **AND WHEN** another branch moves while `HEAD` and the tree stand, and the command reads it through a shell or a script it
  names, as `sh -c 'git diff --quiet other HEAD'` does
- **THEN** the command runs, and its new exit is judged

#### Scenario: Commands run side by side
- **WHEN** two commands each wait for a file the other writes, and a third fails after the first
- **THEN** both finish, and the failure lines print in task order, whatever order the commands finished in
- **AND** a `pytest` with `-n` starts only when no other command runs, and a `make` starts only when no other `make` runs

#### Scenario: A load over the cores
- **WHEN** the 1-minute load is over the core count and a command runs
- **THEN** the next command waits
- **AND WHEN** the load is over the core count and no command runs
- **THEN** the next command starts

#### Scenario: A limit the repository sets
- **WHEN** the root `AGENTS.md` holds `**Verify timeout:** 1800`
- **THEN** a command is ended at 1800 s
- **AND WHEN** no such line stands, or it holds `-30`
- **THEN** a command is ended at 600 s
- **AND WHEN** it holds `3000000`
- **THEN** a command is ended at a day

#### Scenario: A timed-out command's group
- **WHEN** a command starts a child, outlives its limit, and `plan_check.py` kills it
- **THEN** the child is gone too, and the line says the command timed out

#### Scenario: Only the named sub-tasks
- **WHEN** `plan_check.py --only 1.1 2.3` runs and `1.1` is unticked and `2.3` is a `**HALT CHECK**`
- **THEN** it runs the commands of `1.1` and of `2.3`, and prints a `plan: ` line for each only if it fails
- **AND WHEN** a plain check names `2.3` in no `--only`
- **THEN** the command of `2.3` does not run
- **AND WHEN** `--only 1.6` names a sub-task whose `Verify:` holds no backticked command
- **THEN** it exits 2, naming `1.6`

#### Scenario: A test file named for the script
- **WHEN** a ticked `Verify:` runs `pytest tests/test_plan_check.py`
- **THEN** the command runs, as only a command with a word of the file name `plan_check.py` is skipped

#### Scenario: A stacked close
- **WHEN** the build's close runs while `stacked-on` names a commit
- **THEN** the plan check's `--base` is that sha, and a test the dependency deleted is no test gone since the base

### Requirement: The converge fixer leaves the plan to the person

The converge fixer, whose rules `skills/mf-converge/references/fix.md` holds, SHALL NOT edit the change's `tasks.md` or `proposal.md`, nor its
`design.md` save the prose a `drift` card names outside the `## Decisions`, `## Tests` and `## Dependencies` sections, which it
SHALL correct; it SHALL NOT edit those sections, a row of their tables, a decision's D-id or a `## ` heading, save one line it MAY
append as the last line of a `### D<n>` entry of the decisions section,
`Fix note (<YYYY-MM-DD>, <card id>): <one line>`, recording how the code now implements that decision, the entry's other lines
untouched. A card whose fix that line records SHALL be no amend card, and converge's close-out SHALL name each fix note the run
appended, by its D-id and card.

The fixer MAY also edit the change's spec delta, the files under `openspec/changes/<id>/specs/`, and the body of a `### D<n>` entry of
`design.md`'s decisions section, to say what its own fix does. It SHALL do so in the commit of the fix, which SHALL carry a `Plan-text:`
trailer naming the card ids the fix clears; it SHALL NOT change the decisions table, add or remove a decision, a `### D<n>` heading
or a `## ` heading, and SHALL NOT clear so a card of the security category whose severity is `critical` or `high`. `converge.py` SHALL
read each commit of a fix pass, after the pass and before the gate, and again over the commits a resumed run finds since its freeze,
and halt `plan edit refused — <why>` when a commit is a merge, or
changes a path under `openspec/changes/<id>/` other than `design.md` and `specs/`, changes a file under `specs/` or a line of a
decision's body other than a fix note with no `Plan-text:` trailer, changes the decisions table or a heading, or names a card of that
security class in its trailer. A commit that touches nothing under the change's folder, or only the prose of `design.md` outside its
decisions section or a fix note, SHALL need no trailer. The verify pass SHALL read a plan-text edit in the fix's diff, and keep a card
`fixed` only when the wording holds of the code.

A card whose fix needs any other edit of those SHALL be set `wontfix`, naming the amend the
person commits by the file's path: an **amend card**, which a checker marks `Amend: yes` and any other card `Amend: no`. A
checker SHALL mark `Amend: yes` a card whose **Fix** names the change's `tasks.md`, `proposal.md` or `design.md` by path, save a `drift` card's
naming that prose, a fix note, or the delta or a decision's body as words the fixer may write, and a security card of `critical` or `high` severity
whatever it names. A blocking amend card SHALL halt the round `amend needed — <card ids>` after the fix pass. The
verify pass SHALL keep an amend card's `wontfix` whose justification holds, and SHALL NOT turn it `accepted`; in an amend
round, it SHALL turn an amend card the amend settled, its **Still true?** check showing the defect gone, `verified`, its note
naming the amend. At the debt write,
before the debt lock, every non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?** command still shows
the defect, SHALL halt the run `amend needed — <card ids>`, writing nothing to the debt, save one *Converge keeps deferred work
in one repository debt file* lets go on; a card whose **Still true?** holds no command SHALL go to the debt unchecked. The person's
amend answers either halt.
The fixer SHALL run `plan_check.py --quick` after its check and before its commit, as *A plan check holds the plan to the built tree*
says, and SHALL write `.minions/changes/<change-id>/fix.md` with a last line `plan check left: <subjects>` or
`plan check left: none`, which `converge.py` reads in place of the fixer's report. The whole plan check SHALL run for a fix after
its gate, at the freeze. A verify round and the pickup check SHALL run `gate_check.py` after the gate, and a verify round SHALL then
run `plan_check.py`, which reads a kept result while one stands.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, the card reads `Amend: yes`, and the round halts
  `amend needed`

#### Scenario: Drift in the design's prose
- **WHEN** the pickup picks a `drift` card whose **Fix** names a line of the change's `design.md` outside its `## Decisions`,
  `## Tests` and `## Dependencies` sections
- **THEN** the fixer corrects that line and sets the card `fixed`; it reads `Amend: no`, and the debt write halts on nothing for it

#### Scenario: Drift in the design's tests section
- **WHEN** a `drift` card's **Fix** names a row of the change's `design.md` `## Tests` table
- **THEN** the fixer edits no row of it, sets the card `wontfix` naming the amend, and the card reads `Amend: yes`

#### Scenario: A fix that changes how a decision is built
- **WHEN** a card's fix changes how the code implements the change's D3, and D3's own words still hold
- **THEN** the fixer appends `Fix note (<date>, <card id>): <how the code now does it>` as the last line of D3's entry, edits no
  other line of it, and sets the card `fixed`
- **AND** converge's close-out names D3 and the card

#### Scenario: A fix that says what it does in the delta
- **WHEN** a card's fix changes a rule the change's spec delta states and the delta's words lag
- **THEN** the fixer edits the delta in the commit of the fix, which carries `Plan-text: <card id>`, `converge.py` takes the commit, and the verify pass judges the wording in the round that follows

#### Scenario: A decision's body, with the trailer
- **WHEN** a fix commit edits the body of the change's D3 and carries `Plan-text: <card id>`
- **THEN** `converge.py` takes it, and the commit reads as a re-plan to a stacked dependent

#### Scenario: The delta with no trailer
- **WHEN** a fix commit edits a file under the change's `specs/` and carries no `Plan-text:` trailer
- **THEN** the round halts `plan edit refused`, naming the file

#### Scenario: A plan file the fixer may not touch
- **WHEN** a fix commit edits the change's `tasks.md`, or its `proposal.md`, with or without the trailer
- **THEN** the round halts `plan edit refused`, naming the file

#### Scenario: The decisions table
- **WHEN** a fix commit edits a row of `design.md`'s decisions table, adds a `### D<n>` heading or removes one, with the trailer
- **THEN** the round halts `plan edit refused`

#### Scenario: A security card of high severity
- **WHEN** a fix commit's `Plan-text:` trailer names a card of the security category whose severity is `high`
- **THEN** the round halts `plan edit refused`, and the card is left to the halt `amend needed`

#### Scenario: Drift in the prose and a fix note need no trailer
- **WHEN** a fix commit edits `design.md` outside its decisions section, or appends a fix note, and touches nothing else under the change's folder
- **THEN** `converge.py` takes it with no trailer

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup's fixer sets a `drift` card `wontfix`, naming an amend of a decision in the change's `design.md`
- **THEN** the pickup check keeps it `wontfix`, and the debt write halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** the debt write halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** command shows the defect gone at the debt write
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

#### Scenario: The fixer's check and the script's
- **WHEN** a fixer clears its cards and commits
- **THEN** it has run `plan_check.py --quick` and `make check`, and converge runs the gate, then the whole plan check at the freeze
- **AND** the verify round runs the whole check again, answered from the kept result while one stands, and a line it prints that the fixer's `plan check left:` line did not name is sent back as before

### Requirement: Converge's conductor is a script

`skills/mf-converge/scripts/converge.py` SHALL conduct converge: its preconditions, the freeze, the dispatch of each checker, the
fixer and each verify worker, the read of each findings file's frontmatter and cards, the loop to its cap of three rounds, the
pickup, a granted round, a catch-up round with its by-rule write, the resume from the status log, the debt write and the report.
`conduct.py` SHALL load it in-process, as it loads `integrate.py`, and call it in the version's thread; `conduct.py converge
<change-id> [conformance=<model>/<effort>] [adversarial=<model>/<effort>] [fix=<model>/<effort>] [grant=yes]` SHALL run it by hand.
No converge worker that conducts SHALL start: the workers are the checkers, the fixer and the verify workers, each a fresh agent
process the run starts through its own worker and checker calls, with a prompt the script fills from the `## Prompt` section of the
role's reference. The script SHALL run the gate, `gate_check.py`, `plan_check.py` and each `Verify:` and **Still true?** command
under `conduct.py`'s sandbox runner, never bare. It SHALL stamp each findings file's `head`, `round`, `files` and `commits` after its
checker returns, as *Converge stamps a findings file's counts* says, and SHALL read a findings file's frontmatter keys `passes` and
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them or with no
frontmatter, or with a card whose id is outside `R<n>` and `S<n>`, or whose verdict is `changes-requested` with no open card, or whose
verdict is `clean` with `open_blocking` 0 while a blocking card's Status word is neither `verified` nor `accepted`, SHALL be malformed. A card is
open until its status is `verified` or `accepted`; a role whose verdict is `changes-requested` while no open card blocks SHALL
count as clean, its file's verdict written `clean` and its open cards left to the pickup and the debt. `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py`
and `skip_stub.py` SHALL read a findings file's cards and frontmatter through `skills/mflib/findings.py`, a card's title a line that
starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word, as `- **stale-claim** — ran.`,
is no card; `skills/mflib/debtfile.py` SHALL read a debt card's title, a line that starts `- **<digits>·<id> — ` with an id holding no `*`, and `debt_match.py` and `cut_context.py` SHALL read it through the module. The status log's events and their text
SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `replay` exiting 2 SHALL send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red, a security card and a debt the freeze may not read SHALL still halt. A file whose verdict is `clean` while a blocking card is
not closed SHALL get its one rewrite worker, the role's own, told the card and its Status word, in place of the debt card and the go-on; the
mismatch itself SHALL send no card to a fixer and count no round, and the file the worker leaves SHALL be read as any file. A file malformed after that rewrite, for any
reason, SHALL halt the version, naming the role, the card and the word of the first read, and the halt SHALL not be `cap reached`.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: Changes requested with nits alone
- **WHEN** a checker's findings file says `changes-requested` and holds open cards, none of a blocking grade
- **THEN** the role counts as clean, its file reads `verdict: clean`, the pickup takes its small and drift cards, and the version converges with no halt

#### Scenario: Changes requested with no card
- **WHEN** a checker's findings file says `changes-requested` and holds no open card
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`, and the file reads `verdict: clean` after, the
  rewrite having fixed it or not

#### Scenario: A clean file with a blocking card not closed
- **WHEN** a verify worker's file says `verdict: clean` and `open_blocking: 0` while blocking card R1's Status reads `fixed`
- **THEN** one rewrite worker of that role is started, told R1 and `fixed`, no fixer is sent R1, and the round count stays
- **AND WHEN** the file then reads R1 `verified`, or `changes-requested` with `open_blocking: 1`
- **THEN** converge goes on from that file

#### Scenario: A clean file still mismatched
- **WHEN** the file still says `verdict: clean` while R1's Status reads `fixed` after the rewrite worker, or the worker leaves the file with no `Amend:` line on a card
- **THEN** the version halts, the halt naming the role, R1 and `fixed`, and it is no `cap reached`

#### Scenario: A card titled outside the contract's ids
- **WHEN** a checker's findings file holds a card titled `- **S-1 — a title**`
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`

#### Scenario: A bold-led bullet that is no card
- **WHEN** a findings file holds `- **stale-claim** — ran.` under a `## Passes` heading and `- **Spec** — none.` in its Summary, beside cards that carry their `Amend:` fields
- **THEN** the file is read with those cards alone, and no rewrite worker is started for it
- **AND** `open_cards.py` writes those cards alone

#### Scenario: A worker exits 1
- **WHEN** a checker exits 1 or leaves no findings file
- **THEN** one fresh worker is started for that role, and a second failure halts the version, naming the role

#### Scenario: A prose check
- **WHEN** a non-blocking card's **Still true?** holds no command in backticks
- **THEN** the card goes to the debt unchecked, and no command runs for it

#### Scenario: A check command writes outside the trees
- **WHEN** a card's **Still true?** command tries to write a file outside the worktrees
- **THEN** the sandbox denies it, the card goes to the debt unchecked, and nothing is written outside

#### Scenario: A debt the freeze may not read
- **WHEN** `.minions/debt.md` is a link at a freeze
- **THEN** converge halts naming `debt_match.py`, and writes no empty `debt-cards.md`

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check
