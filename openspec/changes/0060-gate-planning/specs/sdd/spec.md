## MODIFIED Requirements

### Requirement: Converge and the release halt on a gate the cut did not plan

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each run
`skills/mf-converge/scripts/gate_check.py` before judging or releasing, and SHALL halt on its verdict. The script
SHALL export the base and `HEAD` with `git archive` into fresh directories under `.minions/gate-check/`, run make
there with `MAKEFLAGS` and `MFLAGS` cleared, and remove them when it ends. A **gate makefile** SHALL be any file in
the `MAKEFILE_LIST` or a `Reading makefile` line of `make -pn -r -w -d gate` on either export. When no sub-task in
`tasks.md` as the cut commit holds it names both `Makefile` and `` `gate` ``, a branch that changes a gate makefile,
or the `make -n gate` output, SHALL halt. When such a task exists, the script SHALL show the two exports'
`make -n gate` diff, and SHALL halt on a command line the base prints and the branch does not, and on every
non-blank gate makefile line the branch adds or removes, unless that task quotes the line. Its verdict SHALL
name what it read — the gate makefiles and the dry runs — and SHALL NOT state that the gate is the base's. A halt SHALL
list every unquoted line in one run, the halt with no planning task among them; SHALL say that `` `gate` `` must be in
backticks and that the cut commit is what counts; SHALL say whether the dry run changed or the file alone; and SHALL name
`/mf-ship approve-gate <change-id>` as the way out. A person's approval recorded in the home folder for the change, whose
hash equals the hash of the edits and the dry runs' diff the script reads, SHALL pass the script without a planning task. An export that lacks a path of its tree, or a dry run that fails on either export, SHALL halt, naming the
side. The cut commit SHALL be the one commit that adds the change's `design.md`; more than one SHALL be a
halt.

#### Scenario: Both stations name the dry-run check
- **WHEN** a branch changes a gate makefile — an included makefile, a sub-make's makefile, a recipe line given a
  `-` prefix, a `.IGNORE` target, or `-i` in `MAKEFLAGS` — or a file that changes the gate's dry run, and no cut task
  names the gate recipe
- **THEN** `mf-converge` halts before judging, and `mf-release` before releasing

#### Scenario: A planned gate change drops a command
- **WHEN** a cut task names the gate recipe, and the base's dry run prints a command line the branch's does not
- **THEN** each station shows the two dry runs' diff and halts, unless that task quotes the line

#### Scenario: A planned change adds a line the task does not quote
- **WHEN** a cut task names the gate recipe, and the branch adds or removes a gate makefile line the task does not
  quote — a removed `SHELL := /bin/bash -o pipefail`; an added `-` recipe prefix, a `.IGNORE` target, a `SHELL` assignment or `-i` in `MAKEFLAGS`, in any form: a continued rule
  line, `define`, a computed name, `$(eval)`
- **THEN** each station halts, naming the line

#### Scenario: The base's gate reads a file the export lacks
- **WHEN** either export lacks a path of its tree — an `export-ignore` path — or `make -pn -r -w -d gate` or
  `make -n gate` fails in it — an included `.env`
- **THEN** each station halts, naming the side and the failure, and compares nothing in the working tree

#### Scenario: The halt lists every unquoted line
- **WHEN** a branch adds a `setup` target and edits `.PHONY`, and no cut task names `` `gate` ``
- **THEN** the halt lists each added and removed line, says the dry run is unchanged, and names `approve-gate`

#### Scenario: A person approves a gate change
- **WHEN** a person's approval recorded in the home folder holds the hash of the branch's gate edits and dry-run diff
- **THEN** the script passes, naming the approval
- **AND WHEN** the branch changes a gate makefile line after the approval
- **THEN** the hashes differ, and the script halts as with no approval

#### Scenario: A branch writes its own approval
- **WHEN** a file in the repository, the run directory or the version's tree claims an approval
- **THEN** the script reads none of it, and halts as with no approval

## ADDED Requirements

### Requirement: The cut plans a gate change in the form the check reads

`skills/mf-cut-change/SKILL.md` SHALL hold input-contract item `I18`, which `skills/mf-build/SKILL.md` owns: a sub-task that
names `Makefile`, or a gate makefile ending `.mk`, SHALL name `` `gate` `` and hold a fenced `diff` block quoting each line it adds
or removes, with no blank line inside the block. The cut SHALL run `gate_check.py --tasks <tasks.md>` before its commit, and
SHALL halt, naming the sub-task, on one that names a gate makefile without that form.

#### Scenario: A cut task describes a Makefile edit in prose
- **WHEN** a sub-task says "the gate's `pytest` line takes `-m "not e2e"`" in `Makefile`, and holds no `diff` block
- **THEN** the cut halts, naming the sub-task and `I18`, and commits nothing

#### Scenario: A cut task quotes its lines
- **WHEN** a sub-task names `Makefile` and `` `gate` `` and holds a `diff` block of its lines
- **THEN** the cut's check passes

### Requirement: The build checks a gate change at its phase

`skills/mf-build/SKILL.md` SHALL, before committing a phase whose staged diff touches a gate makefile, run
`gate_check.py --change <change-id> --base <merge-base> --head <the staged tree>`, and SHALL halt on its exit 1, committing
nothing.

#### Scenario: A phase adds a line the cut did not quote
- **WHEN** a phase's staged diff adds a gate makefile line its cut task does not quote
- **THEN** the build halts before the phase's commit, naming the line

#### Scenario: A phase adds a quoted line
- **WHEN** every gate makefile line the phase adds or removes is quoted by its cut task
- **THEN** the build commits the phase

### Requirement: A person can approve a gate change

`/mf-ship approve-gate <change-id>`, the person's command, SHALL show the version's gate makefile edits and the dry runs' diff,
as `gate_check.py` reads them, with their hash, and on the person's yes SHALL record the hash in the home folder beside the kept
URLs and the release ledger. A worker, whose sandbox writes nothing in the home folder, SHALL be unable to record one.

#### Scenario: A person approves a planned change the task quoted badly
- **WHEN** converge halted on an unquoted gate line, and the person runs `/mf-ship approve-gate <change-id>` and says yes
- **THEN** the hash is recorded, and the next converge's gate check passes, naming the approval
