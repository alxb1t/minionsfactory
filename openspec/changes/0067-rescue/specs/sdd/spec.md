## ADDED Requirements

### Requirement: A halted version is rescued in its run

When a version halts on its build check, its converge cap, or integrate's red gate or note, `conduct.py` SHALL spawn the
`mf-rescue` station in that version's thread, unless its models file's `[rescue]` table says `skip = true`; the station SHALL run on
the `[rescue]` table's executor and model, the `[build]` table's when there is none. `skills/mf-build/SKILL.md` SHALL write
`.minions/build/<id>.halt` on every halt — the sub-task, the stop condition, one line of evidence. `skills/mf-rescue/SKILL.md` SHALL
fix a build halt on a `Verify:` that cannot pass, a reader a deletion missed, a task two readings would build differently, or an
`I19` break, with one `docs(<id>): amend the change directory` commit touching only `openspec/changes/<id>/tasks.md` and `design.md`,
never `design.md`'s decisions table, carrying a `Rescue:` trailer; every other halt it SHALL diagnose in `.minions/rescue/<id>.md`.
`conduct.py` SHALL halt the version when the commit touches any other path, and otherwise clear its halt and go on. A version SHALL
get at most `RESCUES = 3` rescues in a run, and none for a sub-task it rescued before; a timeout, a usage limit and D47's halts that
need the person SHALL get none. The run SHALL log `rescue — <id>: fixed · <sub-task> · <commit>` or `rescue — <id>: diagnosed ·
<file>`, and `report` SHALL print each. The rejoin folder and the grants folder SHALL be read and emptied through a directory file
descriptor opened without following a link.

#### Scenario: A check that cannot pass
- **WHEN** a build halts on a `Verify:` whose search matches a line no task touches
- **THEN** the rescue amends `tasks.md`, the run logs `rescue — fixed`, and the version builds on and releases in the same run

#### Scenario: A decision halt
- **WHEN** a build halts on a design premise the code rules out
- **THEN** the rescue writes `.minions/rescue/<id>.md`, and the version stays halted, its halt naming the file

#### Scenario: A rescue outside the plan
- **WHEN** a rescue's commit touches a file outside `tasks.md` and `design.md`
- **THEN** the version halts, naming the file

#### Scenario: The same sub-task again
- **WHEN** a version halts again on a sub-task it was rescued from
- **THEN** no rescue runs, and the halt names both

#### Scenario: A link at the rejoin folder
- **WHEN** a worker swaps the rejoin folder for a link to another directory after the run lists it
- **THEN** nothing in that directory is deleted

## MODIFIED Requirements

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the offline base, the release ledger and a person's gate approval
in the home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, or a
default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset time named.

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
