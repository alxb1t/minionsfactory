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
marked `**CORPUS**` names a case `scripts/corpus.toml` does not hold. It SHALL NOT run again a `**HALT CHECK**` sub-task's
command, a command of a `**HUMAN` phase, or a command naming `plan_check.py`, and SHALL run no command with a shell. It SHALL
exit 0 printing `plan: clean` when none holds, and 2 when it cannot read `tasks.md`, the base or git.

It SHALL run each distinct command once a check, whatever the number of sub-tasks that name it, and hold the one result to each
sub-task's own words. It SHALL run the commands side by side, one slot for each core the machine has, and print the lines in
task order, then command order, whatever order they finish in: a `pytest` with `-n` takes every slot and runs alone, a `make`
runs one at a time, and every `pytest` starts with `-p no:cacheprovider` in its `PYTEST_ADDOPTS`. A command past 600 s SHALL
lose its whole process group and print `plan: <sub-task> — `<command>` timed out`; ended by SIGTERM, the check SHALL end the
process group of each command then running. A `pytest` command — one whose argv starts `pytest`, `uv run pytest` or `python -m pytest` — whose `Verify:` says nothing of its
output beyond that it exits 0 SHALL pass unrun when `gate_run.py` holds a green record for the same tree and the same dry run of `make -n gate`; one that
says what it prints still runs. On a settled tree the check SHALL keep each finished result — its exit and output — in
`.minions/plan-check/<tree>/`, named by the command, and SHALL read it again on the same tree; a command naming a revision
SHALL be kept by `HEAD` too, a timed-out command SHALL be kept by no one, and an unsettled tree SHALL keep and read none. With
`--only <sub-task ids>` it SHALL run the `Verify:` commands of those sub-tasks alone, ticked or not, with the same skips, print
only their lines and check nothing else.

`skills/mf-build/SKILL.md` SHALL run it at the build's close, after the metrics and before `build.done`, in the foreground within
600 s, and SHALL halt on any other exit than 0, writing no `build.done`. Converge's fixer SHALL run it in the foreground after
its gate and before its commit, clearing each problem as a blocking card of the same pass, or setting it `wontfix` naming the
amend; converge's Step 7 SHALL run it after `gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any
verify worker, counting no round; a line the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the
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
- **AND WHEN** the `Verify:` says the command prints `3`, or the tree or the dry run differs from the record's
- **THEN** the command runs

#### Scenario: A result kept by tree
- **WHEN** `plan_check.py` runs a command on a settled tree and runs again on the same tree
- **THEN** the second check reads the kept result and does not run the command
- **AND WHEN** the tree is unsettled, or the command is another, or it names `HEAD` and `HEAD` is another commit
- **THEN** the command runs

#### Scenario: Commands run side by side
- **WHEN** two commands each wait for a file the other writes, and a third fails after the first
- **THEN** both finish, and the failure lines print in task order, whatever order the commands finished in
- **AND** a `pytest` with `-n` starts only when no other command runs, and a `make` starts only when no other `make` runs

#### Scenario: A timed-out command's group
- **WHEN** a command starts a child, outlives the 600 s limit, and `plan_check.py` kills it
- **THEN** the child is gone too, and the line says the command timed out

#### Scenario: Only the named sub-tasks
- **WHEN** `plan_check.py --only 1.1 2.3` runs and `1.1` is unticked and `2.3` is a `**HALT CHECK**`
- **THEN** it runs the command of `1.1` alone and prints a `plan: ` line for it only if it fails

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under macOS Seatbelt, through `conduct.py sandboxed -- <cmd>`.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — to its
own fresh temporary folder, and to `/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied
(`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`,
`~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and
SHALL have no network of any kind, loopback included. It SHALL start with the credential variables of a Claude worker unset, with
`VIRTUAL_ENV` unset, with git's hooks off, with `UV_OFFLINE=1`, with `uv`'s cache in the run directory, and with `TMPDIR` naming that
temporary folder: one made for the command alone, outside every repository, under the conductor's own `TMPDIR`, and removed by
`conduct.py` when the command ends. A conductor whose own `TMPDIR` lies inside a git repository SHALL run nothing, print a line
naming `TMPDIR` and exit 2. Its exit code SHALL be the
command's own, a signal's exit shifted to `128` plus its number. When a failed command's output holds the OS's refusal,
`Operation not permitted`, `conduct.py` SHALL print one `sandboxed: denied —` line after it, so a refused write or call reads as
a refusal. Where `sandbox-exec` is not on `PATH`, `conduct.py` SHALL run nothing, print a line holding `no OS sandbox` and exit 2: it SHALL
never run the command bare.

A command the conductor starts with a deadline SHALL run in a process group of its own. Past its deadline the group SHALL be
sent SIGTERM and, after a short grace, SIGKILL; `conduct.py` SHALL then print one `sandboxed: timed out —` line and exit 124.
Converge SHALL give each command it runs the seconds left to its own deadline.

#### Scenario: A command writes outside the trees
- **WHEN** a command run through `conduct.py sandboxed` writes a file in a folder outside every tree
- **THEN** the write fails with `Operation not permitted`, the command's exit is non-zero, and one `sandboxed: denied —` line
  follows its output
- **AND** a write inside a tree succeeds

#### Scenario: A command reads a credential
- **WHEN** a command run through `conduct.py sandboxed` reads a file under `~/.ssh`
- **THEN** the read fails with `Operation not permitted`

#### Scenario: A command calls the network
- **WHEN** a command run through `conduct.py sandboxed` connects to a loopback port that a listener holds open
- **THEN** the connect fails, and the listener sees none

#### Scenario: The command's exit passes through
- **WHEN** a command run through `conduct.py sandboxed` exits with 3
- **THEN** `conduct.py` exits with 3, and a command a signal ended exits with `128` plus the signal's number

#### Scenario: A worker's credentials stay unset
- **WHEN** `GITHUB_TOKEN` and `VIRTUAL_ENV` are set where `conduct.py sandboxed` starts
- **THEN** the command sees neither, and sees `UV_OFFLINE=1`

#### Scenario: A command's own temporary folder
- **WHEN** a command run through `conduct.py sandboxed` runs `git rev-parse` in its `TMPDIR`, and writes a file there
- **THEN** the `git rev-parse` fails, the write succeeds, and the folder is gone after the command ends

#### Scenario: The conductor's temporary folder lies in a repository
- **WHEN** `conduct.py sandboxed -- true` runs with `TMPDIR` naming a folder inside a git repository
- **THEN** `true` does not run, the output names `TMPDIR`, and the exit is 2

#### Scenario: No OS sandbox stands
- **WHEN** `sandbox-exec` is not on `PATH` and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox`, and the exit is 2

#### Scenario: A command past its deadline
- **WHEN** a command that starts a child runs under a deadline and outlives it
- **THEN** the command and its child are gone, the output holds a `sandboxed: timed out —` line, and the exit is 124
- **AND WHEN** the command ignores SIGTERM
- **THEN** SIGKILL ends it after the grace

### Requirement: An answered converge halt gets one amend round

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an
older backlog lock's, SHALL be **answered** when `HEAD` is past its head, a descendant that is not it, and either both findings
files' `head:` is that head, or a commit past it is an **amend**: one parent, the subject `docs(<id>): amend the change
directory`, and paths under `openspec/changes/<id>/` alone — the person's, the rescue's or the supervisor's. `conduct.py`'s stage
SHALL then be `converge`, with no grant, and its converge check SHALL not read the old halt. A **halt before round 1** — a halt
other than a `verify: halt` in a run with no `start` line, not marked `· grant` — SHALL be void when `HEAD` is past its head, by
any commit, and SHALL be re-run when `HEAD` is its head: `conduct.py`'s stage SHALL be `converge` in both, and it SHALL start no
rescue for it. A run SHALL re-run a version once at the same head: one that halts before round 1 again SHALL stay out for the
rest of that run, a rejoin logging it still halted. Any other halt, and one whose head is no ancestor of `HEAD`, SHALL stand.

`skills/mf-converge/SKILL.md`, finding an answered halt, SHALL open a catch-up run marked `· amend` and run its catch-up round over
`<judged head>..HEAD`, the judged head being both findings files' `head:`, whatever their verdicts: the amend, the build's code
for a phase it added, and converge's own unverified fix. It SHALL open no new round 1 for it. Before the run's `start` line it
SHALL run each `Verify:` line the range adds to `tasks.md`, a ticked task's included, through `plan_check.py --only` under the
sandbox, and halt `verify failed — <sub-task ids>` when one fails, or `plan check: <lines>` when the plan check cannot run to its end; the run SHALL skip what a plan check skips — a `**HALT
CHECK**` sub-task's command, a command of a `**HUMAN` phase and a command naming `plan_check.py` — and SHALL run the rest
through the plan check's own runner. The run SHALL count its own rounds: one judge round and at most one fix round, `round:`
carrying on past three;
a blocking finding open at its end SHALL halt `cap reached`. Conformance SHALL keep the full plan in its reading set, and its
stale-claim pass SHALL search the whole tree for each claim the amend changes. Finding a halt before round 1, it SHALL open a
plain new run, with no mark, as a fresh invocation does, save after a catch-up run, where a new run of the same mark runs the
catch-up round again. A run marked `· grant` that resumes SHALL stay a granted round.

#### Scenario: A gate red before round 1
- **WHEN** converge halts on a red gate before round 1 at head H, writing no `start` line, and the person asks a live run to take
  it back with no new commit
- **THEN** the run takes it back, and converge runs again in a plain new run
- **AND WHEN** it halts before round 1 again in that run
- **THEN** it stays out for the rest of the run, and a rejoin logs it still halted
- **AND WHEN** a commit past H follows
- **THEN** its stage is `converge`

#### Scenario: A two-line amend after a halt
- **WHEN** converge halted `amend needed`, and the person commits a two-line amend of the change directory
- **THEN** a run converges it in a catch-up run marked `· amend`, with no grant, judging `<judged head>..HEAD` in one round
- **AND** no run restarts at `round: 1`, and the version releases in the same run

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a catch-up run marked `· amend` over `<judged head>..HEAD`, with no grant and no new round 1

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the cap is a granted round's, in a run with no `start` line, and `HEAD` is its head
- **THEN** its stage stays `converge-halted`, and it is no halt before round 1

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, so its head is not the findings files' `head:`, and an amend follows
- **THEN** its stage is `converge`, and the amend round's range starts at the files' `head:`, the fix in it
- **AND WHEN** only a commit other than an amend follows
- **THEN** its stage stays `converge-halted`

#### Scenario: An amend adding a phase
- **WHEN** an amend answering a converge halt adds an unticked phase after the last
- **THEN** the version builds that phase, and the amend round's range holds the build's commits

#### Scenario: An amended Verify that fails
- **WHEN** the range adds a `Verify:` line to a ticked task, and the command fails
- **THEN** converge halts `verify failed — <sub-task id>` before its `start` line, and any commit past that head answers it

#### Scenario: An amended Verify the plan check skips
- **WHEN** the range adds a `Verify:` line to a `**HALT CHECK**` sub-task whose command would fail
- **THEN** the command does not run, and converge halts nothing for it

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL also decide the `Verify:` sequencing rows `V1` to `V5` — a needle an earlier
task already adds, a `-k` that selects tests a later task adds or deletes, a `git grep` of a file not committed before its
phase ends, a needle its task never names, a `pytest` command that names no test path — and the record's consistency rows `K1` to `K6` — the proposal's `## Impact` against
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

#### Scenario: A record that disagrees with itself
- **WHEN** a task links `design.md#d9` and `design.md` has no `### D9` heading
- **THEN** `cut_check.py` prints the failed row `K4` naming the task, and exits 1

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts
