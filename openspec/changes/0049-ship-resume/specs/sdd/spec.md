## MODIFIED Requirements

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when the worker exits 0 and its check on disk passes — never on the worker's report. The converge
check SHALL need `done` as the newest run's latest status-log event. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

#### Scenario: A worker dies after clean findings
- **WHEN** a converge worker exits 1 with both findings files clean at `HEAD` and no `done` in its status log
- **THEN** the version halts, naming the exit, and nothing is released

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
outside git and the run directory, except the claim: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted, or a release whose
base moved. A worker stopped by a usage limit SHALL be halted with its reset time named.

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

## ADDED Requirements

### Requirement: Converge continues an unfinished run

When the newest run of a status log ends on neither `halt` nor `done`, `conduct.py`'s stage SHALL be `converge`, whatever
the findings files say, and `skills/mf-converge/SKILL.md` SHALL continue that run from its latest event: no new `## Run`
heading, the round unchanged, and a pickup whose fix was never committed sent again.

#### Scenario: A usage limit stops converge mid-pickup
- **WHEN** a run's latest event is `pickup` and its findings files are clean at `HEAD`
- **THEN** a re-run of `mf-ship` spawns converge, not the release
- **AND** the same run sends the pickup, verifies, writes the backlog and ends on `done`, repeating no judged round

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. `skills/mf-release/SKILL.md` SHALL restore a tree dirty with only its own fold and archive to `HEAD`, then
start over, and SHALL re-enter at its merge when `HEAD` is its release commit and the default branch has not moved.
`conduct.py` SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of a run, push the default branch and each merged
tag `origin` lacks, never forcing, a rejected push halting the run; `status` SHALL report that work, so a run starts for
it. The claim `.minions/runs/active` SHALL hold the conductor's pid and each worker's process group: a dead pid is a
stale claim, whose groups a run kills before it clears the claim and starts, and `status` SHALL name it.

#### Scenario: A release dies before its commit
- **WHEN** a release worker dies with its fold staged and the change's folder moved
- **THEN** a re-run reads the stage as `release`, restores the tree, and releases with one tag

#### Scenario: A release dies after its tag
- **WHEN** a release worker dies after its commit and tag, and the default branch has not moved
- **THEN** a re-run merges and pushes
- **AND WHEN** the default branch has moved
- **THEN** the stage is `released`, a halt naming the person's recovery

#### Scenario: A release dies before its push
- **WHEN** the default branch is ahead of `origin` and no version is open
- **THEN** `status` names the unpushed work, and a run pushes it and ends on `done`

#### Scenario: The conductor is killed
- **WHEN** `.minions/runs/active` holds a dead pid and a live worker group
- **THEN** `status` reads `stale`, and a run kills the group, clears the claim and starts
