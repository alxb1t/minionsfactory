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
`/mf-ship approve-gate <change-id> <hash>` as the way out, `<hash>` the hash of what that run read. With no planning task, the
halt SHALL list each line the branch's dry run adds, and SHALL list the dry run itself when nothing else is listed. A person's
approval recorded in the home folder for the change, whose hash equals the hash of each gate makefile's unified diff, line
numbers included, and the dry runs' diff the script reads, SHALL pass the script without a planning task. An export that lacks a path of its tree, or a dry run that fails on either export, SHALL halt, naming the
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
- **THEN** the halt lists each added and removed line, says the dry run is unchanged, and names `approve-gate` with the hash

#### Scenario: A dry run gains a line with no plan
- **WHEN** no cut task names `` `gate` ``, no gate makefile changes, and the branch's dry run prints a line the base's does not
- **THEN** the script halts, naming the added line

#### Scenario: A person approves a gate change
- **WHEN** a person's approval recorded in the home folder holds the hash of the branch's gate makefile diffs and dry-run diff
- **THEN** the script passes, naming the approval
- **AND WHEN** the branch changes or moves a gate makefile line after the approval
- **THEN** the hashes differ, and the script halts as with no approval

#### Scenario: A branch writes its own approval
- **WHEN** a file in the repository, the run directory or the version's tree claims an approval
- **THEN** the script reads none of it, and halts as with no approval

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the release ledger and a person's gate approval in the
home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, or a default-branch commit no ledger entry stands behind. A worker
stopped by a usage limit SHALL be halted with its reset time named.

#### Scenario: A HUMAN phase halts its version
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** that version halts, naming the phase, and every other version goes on

#### Scenario: A later version halts, and the earlier ships
- **WHEN** two versions run and the later one's build check fails
- **THEN** the earlier is released, merged and pushed
- **AND** the run closes naming the later as halted and the earlier's tag as released, and exits 1

#### Scenario: A later version ships past a halted one
- **WHEN** two versions run and the earlier one's build check fails
- **THEN** the later is released, merged and pushed
- **AND** the run closes naming the earlier as halted and the later's tag as released, and exits 1

#### Scenario: A halted dependency blocks a chain
- **WHEN** a version halts, a second has it in `after:`, and a third has the second in `after:`
- **THEN** neither starts a worker, each logs `blocked — by <id>`, and the closing line names both as blocked

#### Scenario: No open version can start
- **WHEN** one version sits at a `**HUMAN` phase, and every other is `waiting`
- **THEN** the run starts no worker, and closes naming the first as halted and the others as blocked

#### Scenario: A failed probe stops the run
- **WHEN** the probe's check fails
- **THEN** no version starts a worker, and the run closes naming `run` as halted

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again

#### Scenario: The person resolves a semantic conflict
- **WHEN** integrate halted on a semantic conflict or a red gate, with the merge open and its note under
  `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

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

`skills/mf-build/SKILL.md` SHALL, before ticking each phase's box, run
`gate_check.py --change <change-id> --base <merge-base> --head <the staged tree>`, and SHALL halt on its exit 1, ticking and
committing nothing.

#### Scenario: A phase adds a line the cut did not quote
- **WHEN** a phase's staged diff adds a gate makefile line its cut task does not quote — in `Makefile`, a `*.mk` file, a
  `GNUmakefile` or any file make includes
- **THEN** the build halts before the phase's tick and commit, naming the line, and the next build continues the phase

#### Scenario: A phase adds a quoted line
- **WHEN** every gate makefile line the phase adds or removes is quoted by its cut task
- **THEN** the build commits the phase

### Requirement: A person can approve a gate change

`/mf-ship approve-gate <change-id> <hash>`, the person's command, SHALL be the person's yes to the gate check halt that named
`<hash>` beside the version's gate makefile edits and the dry runs' diff, and SHALL record the hash in the home folder beside
the kept URLs and the release ledger. It SHALL run none of the branch's makefiles, since it runs outside the sandbox, and SHALL
refuse a `<hash>` that is not a sha256. A worker, whose sandbox writes nothing in the home folder, SHALL be unable to record one.

#### Scenario: A person approves a planned change the task quoted badly
- **WHEN** converge halted on an unquoted gate line, and the person runs `/mf-ship approve-gate <change-id> <hash>` with the
  hash the halt named
- **THEN** the hash is recorded, and the next converge's gate check passes, naming the approval

#### Scenario: A person approves a phase's halt
- **WHEN** the build halted on its staged tree, and the person approves the hash that halt named
- **THEN** the next build's check on the same staged tree passes, naming the approval

#### Scenario: The approval runs no worker's code
- **WHEN** a branch's makefile runs a `$(shell …)` as make reads it, and the person runs `approve-gate`
- **THEN** the hash is recorded, and the `$(shell …)` does not run
