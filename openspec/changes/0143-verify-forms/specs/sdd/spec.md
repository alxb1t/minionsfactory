## ADDED Requirements

### Requirement: The build judges each Verify: with the plan check

`skills/mf-build/SKILL.md` SHALL run, before a phase's other tasks, the phase's `**HALT CHECK**` sub-tasks through
`plan_check.py --only <sub-task ids>`, and halt on a line it prints. After the phase's tasks it SHALL run each other sub-task's
`Verify:` the same way, and tick a box only once its command passed there, never judging a `Verify:` in the worker's own shell.
A `**HUMAN` phase's `Verify:` SHALL stay run as written, the plan check skipping it. The plan check SHALL run as one background
command the worker waits on once.

#### Scenario: A form the close refuses
- **WHEN** a phase's sub-task says `` `printf 1` prints `2` `` and the build runs it through `plan_check.py --only`
- **THEN** the plan check exits 1 at that phase, and the build ticks no box

#### Scenario: A premise checked first
- **WHEN** a phase holds a `**HALT CHECK**` sub-task and tasks that change the state it checks
- **THEN** the build runs the HALT CHECK through `--only` before those tasks, and halts on a failure with `stop: HALT CHECK`

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

It SHALL read a `Verify:`'s spans as follows: once an output verb — `prints`, `exits` and the like — follows a command, each later
span is output, never a command, whatever words stand between the verb and the span, until a `then`, a `;`, the sentence's end
or a `Verify:` label; a verb right after `that`, `which` or `who` opens no output, and a `, and` or `, or` before a span that a
verb follows opens a new command. A command whose `Verify:` says it
`` exits `<N>` `` SHALL pass only on exit `<N>`, and on the output the `Verify:` says; the search that passes on exit 1 is the one
whose `Verify:` names no exit. It SHALL run each command without `VIRTUAL_ENV` in its environment, SHALL compare a command's stdout
alone with what the `Verify:` says, keeping its stderr apart, and SHALL show the first lines of both on a failure.
`skills/mf-cut-change/scripts/verify_check.py` SHALL read a `Verify:`'s commands through this script's parser, loaded
from it, and keep no parser of its own.

It SHALL run each distinct command once a check, whatever the number of sub-tasks that name it, and hold the one result to each
sub-task's own words. It SHALL run the commands side by side, one slot for each core the machine has, and print the lines in
task order, then command order, whatever order they finish in: a `pytest` with `-n` takes every slot and runs alone, a `make`
runs one at a time, and every `pytest` starts with `-p no:cacheprovider` in its `PYTEST_ADDOPTS`. It SHALL start a command only
while the machine's 1-minute load is under its core count, and SHALL start one whatever the load when no command runs. A command
past its limit — the integer after `**Verify timeout:**` in the root `AGENTS.md`, in seconds and at most a day, else 600 — SHALL lose its whole
process group and print `plan: <sub-task> — `<command>` timed out`; ended by SIGTERM, the check SHALL end the
process group of each command then running. A `pytest` command — one whose argv starts `pytest`, `uv run pytest` or `python -m pytest` — whose `Verify:` says nothing of its
output beyond that it exits 0, and whose words after its pytest prefix are only `-q`, `-v`, `-x` or `-s` flags and test paths
and `::` nodes that exist, SHALL pass unrun when `gate_run.py` holds a green record for the same tree and the same dry run of
`make -n gate` and the command's own collection finds a test; one that says what it prints, selects with `-k`, `-m` or `--deselect`, or carries another option still runs. On a settled tree the check SHALL keep each finished result — its exit, stdout and stderr — in
`.minions/plan-check/<tree>/`, named by the command, `HEAD` and every ref, and SHALL read it again on the same tree while
`HEAD` and every ref stand, whatever the command's words; a timed-out command SHALL be kept by no one, a result kept without its
stderr SHALL be read as none kept, and an unsettled tree
SHALL keep and read none. With
`--only <sub-task ids>` it SHALL run the `Verify:` commands of those sub-tasks alone, ticked or not, a `**HALT CHECK**` sub-task
it names included, with the other skips, print only their lines and check nothing else.

`skills/mf-build/SKILL.md` SHALL run it at the build's close, after the metrics and before `build.done`, as one background
command it waits on once, its `--base` the sha `stacked-on` names while it stands and else the merge base of the default branch
and `HEAD`, and SHALL halt on any other exit than 0, writing no `build.done`. Converge's fixer SHALL run it in the foreground after
its gate and before its commit, clearing each problem as a blocking card of the same pass, or setting it `wontfix` naming the
amend; converge's Step 7 SHALL run it after `gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any
verify worker, counting no round, save a line that says a command timed out, which it SHALL send back to no one; a line the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the
run `amend needed — plan check: <subjects>`, naming each line's sub-task, `path:line` or test name and never the command it
quotes. `skills/mf-rescue/SKILL.md` SHALL take that halt as a fix of the lines `plan_check.py` prints, in `tasks.md` and
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
- **THEN** `printf 1` is the one command, and `pyproject.toml` is output
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
- **WHEN** a ticked `Verify:` says a `pytest` command exits 0, and `gate_run.py` holds a green record for the same tree and the same dry run
- **THEN** the command does not run, and `plan_check.py` prints no line for it
- **AND WHEN** the `Verify:` says the command prints `3`, or the tree or the dry run differs from the record's, or the command's collection finds no test, or a test path lies outside the repo's `testpaths`
- **THEN** the command runs
- **AND WHEN** the command selects with `-k`, or names a test file or node that does not exist
- **THEN** the command runs, and a selection that collects no test fails the check

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
words, and a range `<default>..HEAD` or `<default>...HEAD`, `origin/` allowed before the default branch and `HEAD` left out. The one absence form is a `git grep -c`
printing nothing.

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

#### Scenario: An option that hides the path
- **WHEN** a `Verify:` runs `grep -L x a.md` or `git grep --files-without-match x`
- **THEN** `verify_check.py` exits 1, naming the sub-task

#### Scenario: A form of a plain check
- **WHEN** a plain `Verify:` runs `git diff main..HEAD -- a.md`, or names `a.py:12-20`, or greps `three plain words`
- **THEN** `verify_check.py` exits 1, naming the sub-task
- **AND WHEN** the sub-task is a `**HALT CHECK**`
- **THEN** it halts nothing for these forms

### Requirement: A dependent builds on its dependency's built head

`conduct.py` SHALL stack a dependent once its one unreleased `after:` dependency, lower than it, has a **built head** — the
commit its `.minions/changes/<id>/build.done` names, the tip of its branch or an ancestor of it, with every `## Progress` box
ticked — and the run records no halt for that dependency, and that head holds the dependent's merge-base with the default
branch. To stack, it SHALL write the head's full sha to `.minions/changes/<change-id>/stacked-on`, merge the built head into
the dependent's worktree with no agent, by `integrate.py`'s rules and with no `delta` check, commit it as
`chore(stack): merge <id> at <sha7> into <change-id>`, and log `stacked — on <id> at <sha7>`; the dependent then builds. A
dependency's thread that reads its stage past the build SHALL wake each dependent waiting on it. A dependent with two or more
unreleased dependencies, a halted one, or a built head that lacks its base SHALL wait as an unstacked dependent does. Until its
dependency's release is merged in, a stacked dependent whose build is done SHALL read as `stacked` in `conduct.py status` and
start no converge; while the dependency has not released, it SHALL wait for the dependency's thread to end, and a dependency
that ends unreleased SHALL block it. Once the dependency released — before or after the dependent's build ended — the run
SHALL merge the default branch into it, as for any dependent, remove `stacked-on` once that merge is committed, read the
build as closed past that merge, and run converge from round 1. `conduct.py` SHALL also remove a `stacked-on` that stands
before it spawns converge or the release. A stacked dependent re-run before its build ends SHALL build on, waiting on no
thread.

While `stacked-on` stands, `mf-build`'s gate check, metrics and plan check, `mf-simplify`'s range and the gate's diff coverage
SHALL take the sha it names as their base, in place of the merge-base with the default branch; the gate SHALL take only a line
of 40 hex digits from it, resolved through `git rev-parse --verify`, never as text in its recipe.

An amend of the dependency's change directory past the stacked-on head that touches its `proposal.md` or changes its
`design.md`'s `## Decisions` SHALL, while `stacked-on` stands — before the dependency's release or after it, until the merge
back — reset the dependent's branch to its cut commit, past the config refusals, remove `stacked-on`, and log `reset`
naming the head it left; so SHALL a stacked-on head that the branch of a dependency that has not released no longer holds.
A dependent reset while its dependency has not released SHALL wait for a built head past that amend; one whose dependency
released SHALL get the default branch merged in and build again. The reset SHALL be read before each of the dependent's
stages, at each poll of its wait and before the merge back, never during a station's run.

#### Scenario: A dependent builds while its dependency converges
- **WHEN** `0002` names `0001` in `after:`, and `0001`'s build check passes while its converge is held
- **THEN** `conduct.py` commits `chore(stack): merge 0001-todo at <sha7> into 0002-marks`, `stacked-on` holds `0001`'s built
  head, and `0002` builds
- **AND WHEN** `0002`'s build is done and `0001` has not released
- **THEN** `conduct.py status` prints `0002-marks · stacked`, and no converge of `0002` starts
- **AND WHEN** `0001` releases
- **THEN** the run merges the default branch into `0002`, `stacked-on` is gone, and `0002`'s converge runs, then its release

#### Scenario: A dependency re-plans
- **WHEN** `0002` is stacked on `0001`'s built head, and an amend of `0001`'s change directory past that head touches its
  `proposal.md`
- **THEN** `0002`'s branch is back at its cut commit, `stacked-on` is gone, and the run log names the head it left
- **AND WHEN** the amend touches `tasks.md` alone
- **THEN** `0002` stays stacked

#### Scenario: A dependency re-plans and releases during the dependent's build
- **WHEN** `0002` is stacked on `0001`'s built head, an amend of `0001`'s change directory past that head touches its
  `proposal.md`, and `0001` releases before `0002`'s merge back
- **THEN** before the merge back `0002`'s branch is back at its cut commit, `stacked-on` is gone, and the run log names the
  head it left
- **AND** the run merges the default branch into `0002`, and `0002` builds again

#### Scenario: Two unreleased dependencies
- **WHEN** a version names two unreleased versions in `after:`, each with a built head
- **THEN** it stacks on neither, and waits as before

#### Scenario: A stacked base for diff coverage
- **WHEN** `make -n gate` runs in a version's worktree while its `stacked-on` names a commit
- **THEN** it prints `--compare-branch=<that sha>`
- **AND WHEN** `stacked-on` holds text that is no commit, or a shell command
- **THEN** it prints `--compare-branch=main`, and runs nothing the text names

#### Scenario: A stacked build's plan check
- **WHEN** `0002` is stacked and the dependency's change deleted a test
- **THEN** the build's close runs the plan check from `stacked-on`'s sha, and that test is no test gone since the base

### Requirement: Converge writes the evidence of each freeze

At every freeze — round 1, each re-freeze after a fix, a catch-up — after `debt-cards.md` and before any dispatch, converge
SHALL write `.minions/changes/<change-id>/evidence.md` whole, from tools alone, and hand its path to every worker it starts
through the placeholder `{evidence}` of each reference's `## Prompt`. The file SHALL hold four sections, each a list of lines
or `None.`: **Gate integrity** — one line for each suppression, skip, removed test, removed assertion, edit to the gate's
configuration or swallowed error the frozen patch holds, by `skills/mf-converge/scripts/gate_integrity.py`; **Plan check** —
the whole output of `plan_check.py` for the freeze, a command past its limit shown as timed out, never as failed;
**Stale-claim candidates** — each name the patch renames or deletes with
its `git grep` mentions outside the patch; **Test cost** — each test the patch adds with its seconds from the gate's junit
report, each `slow` marker and end-to-end `run` boot it adds, and each test it removes against the design's `## Tests`
section. Each line SHALL name a file by its path as Git names it, unquoted, and SHALL time a test by its module, its class
and its name. Converge SHALL judge nothing in it, and SHALL run each command under the sandbox runner. A line that says a command
timed out SHALL raise no card by itself, from the fixer, a checker or Step 7.

#### Scenario: Round 1 writes the evidence
- **WHEN** converge freezes a range in round 1
- **THEN** `evidence.md` stands beside `diff.patch`, `bundle.md` and `debt-cards.md`, before the first checker starts

#### Scenario: A fix is re-frozen
- **WHEN** a fix commit is re-frozen
- **THEN** `evidence.md` is rewritten for the new range, and each worker of the next round is given it

#### Scenario: A new suppression
- **WHEN** the frozen patch adds a line holding `# noqa`, `# type: ignore`, `# ty: ignore` or `# pragma: no cover`
- **THEN** the Gate integrity section holds a line naming its path and line

#### Scenario: A removed test the design names
- **WHEN** the patch removes `def test_a` and the design's `## Tests` section names `test_a`
- **THEN** the Test cost section says the removed test is named in it

#### Scenario: A path Git spaces or quotes
- **WHEN** the frozen patch changes `tests/a b/x.py`, or `café.py`, which Git quotes
- **THEN** each line names the file by that path, whichever file comes before it in the patch

#### Scenario: One test name in two classes
- **WHEN** the patch adds `TestFast.test_main`, 0.1 s in the report, and the report holds `TestSlow.test_main` of the same module at 9.0 s
- **THEN** the Test cost section gives the added test 0.10 s

#### Scenario: Nothing found
- **WHEN** a tool finds nothing for a section
- **THEN** the section reads `None.`

#### Scenario: A command past its limit at the freeze
- **WHEN** the freeze's plan check prints `plan: 1.2 — `<command>` timed out` and no other line
- **THEN** the Plan check section holds that line, Step 7 sends nothing back and raises no card, and the run goes on
- **AND WHEN** the plan check prints a timed-out line and a failed one
- **THEN** only the failed line is sent back
