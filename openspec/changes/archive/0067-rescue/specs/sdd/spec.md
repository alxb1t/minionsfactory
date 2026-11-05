## ADDED Requirements

### Requirement: A halted version is rescued in its run

When a version halts on its build check, its converge cap, or integrate's red gate or note, `conduct.py` SHALL spawn the
`mf-rescue` station in that version's thread, unless its models file's `[rescue]` table says `skip = true`; the station SHALL run on
the `[rescue]` table's executor and model, the `[build]` table's when there is none. `skills/mf-build/SKILL.md` SHALL write
`.minions/build/<id>.halt` on every halt — the sub-task, the stop condition, one line of evidence. `skills/mf-rescue/SKILL.md` SHALL
fix a build halt on a `Verify:` that cannot pass, a reader a deletion missed, a task two readings would build differently, or an
`Verify:` that is not one plain command — a `$(…)`, a shell variable, a loop or a `cd` — with one `docs(<id>): amend the change directory` commit touching only `openspec/changes/<id>/tasks.md` and `design.md`,
never `design.md`'s decisions table, carrying a `Rescue:` trailer; every other halt it SHALL diagnose in `.minions/rescue/<id>.md`.
`conduct.py` SHALL halt the version when the commit touches any other path, and otherwise clear its halt and go on. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer, the person's own fix included, and wait for a re-run. A version SHALL
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

#### Scenario: A rescue that answers its cap
- **WHEN** a rescue at a converge cap writes a grant and a rejoin request
- **THEN** the run starts no further converge round, and logs the version still halted

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

### Requirement: A person can grant one more round

`/mf-ship grant <change-id>` SHALL work only on a version whose status log halted at the cap. It SHALL record the grant and
start a run, or, with a run live, write that version's rejoin request. A refusal SHALL name the stage and the command to
run instead: `/mf-ship`. With a run live, it SHALL refuse while the newest run log holds that version's rescue spawned and not
finished, naming the stage and the rescue, and write nothing: a grant written then is the rescue's answer. A grant landing
after the rescue's `finish` and before the run reads its outcome SHALL count as the rescue's answer too, held for the run and
left on disk for a re-run. `conduct.py` SHALL
spend the grant when it spawns converge, with `grant=yes`. `skills/mf-converge/SKILL.md`
SHALL open a run marked as the grant, send the open blockers to a fixer, verify one round, and on clean write the rest to
the backlog with no pickup; a blocker left SHALL halt. The cap SHALL stay three.

#### Scenario: A grant on a version not at the cap
- **WHEN** a person grants a version at any other stage, a grant already waiting included
- **THEN** it refuses, naming the stage and `/mf-ship`, and no run starts

#### Scenario: A grant during a live run
- **WHEN** a person grants a version at the cap while a run is live
- **THEN** the live run takes it back and spends the grant in its converge, and the run log holds a `grant` event

#### Scenario: A grant during the version's rescue
- **WHEN** a person grants a version at the cap while the live run's rescue of it runs
- **THEN** it exits 2, naming the rescue, and writes no grant and no rejoin request
- **AND WHEN** that rescue has finished and the run has read its outcome, leaving the cap halt
- **THEN** the grant goes to the live run, as in *A grant during a live run*
- **AND WHEN** the grant lands after the rescue's `finish` and before the run reads its outcome
- **THEN** the run holds the version as the rescue answered it, and the grant stays on disk for a re-run

#### Scenario: A grant is spent once
- **WHEN** a granted round ends on a blocker
- **THEN** the stage is `converge-halted`, and a run spends no second round

### Requirement: A halted version rejoins a live run

`conduct.py rejoin [<change-id>]` SHALL write a request in `.minions/runs/rejoin/`, and `/mf-ship` SHALL send it when a run is
live. The live run SHALL check that folder at most every 10 seconds and before its close, and SHALL take into the run every
open version the request names — every one for a request with no id — whose stage on disk is no longer a halt: a halted one,
a blocked one, and one cut after the run started. A version still at a halt SHALL stay out, logged with why. The poll SHALL
not end the run's loop while a version's thread runs: an entry it cannot delete SHALL be no request, and a version it fails
to take SHALL halt alone. A request folder that is a link SHALL hold no request, and the poll SHALL delete nothing through
it. A version the run's plan already holds SHALL stay out, logged, while its models file differs from what the run read, and
a version whose rescue answered its converge or integrate halt on disk SHALL stay out, logged, for the rest of the run, both
waiting for a re-run. Anything that answers that halt on disk while its rescue runs, or before the run reads the rescue's
outcome, SHALL count as the rescue's answer: the person's own commit past the halted head, settled merge or removed note, and
a grant landing after the rescue's `finish`, included. Any other taken version
SHALL have its models file read as it joins, then go through the run's base check, its dependencies, its stations and the
merge lock, as at a run's start, with its halts and blocks cleared. Its executor's probe SHALL run once in the run, before
the first worker on it; a failed probe SHALL halt only the versions on that executor, each later one with that probe's
reason and no second probe. The run SHALL log a `rejoin` event per
version taken, delete the requests it read, and a run's start SHALL delete every request it finds. A run-level halt SHALL
end the run, as before; a request reaches no ended run.

#### Scenario: A fixed version rejoins
- **WHEN** a version halts while another builds, the person fixes it on disk once any rescue of it has ended, and runs
  `/mf-ship`
- **THEN** the live run logs `rejoin` for it, and it releases in the same run, the other version's stations untouched

#### Scenario: A version still halted
- **WHEN** a request names a version whose stage is still a halt
- **THEN** it stays out, and the run logs why

#### Scenario: A version its rescue answered
- **WHEN** a version's rescue answered its converge or integrate halt on disk, and a request names it
- **THEN** it stays out for the rest of the run, and the run logs it still halted, naming the answer
- **AND WHEN** the person's own commit, settled merge or removed note answered that halt while the rescue ran
- **THEN** it counts as the rescue's answer: the version stays out, logged the same, and a re-run goes on from it

#### Scenario: A version cut during the run
- **WHEN** a version is cut while a run is live, and `/mf-ship` runs
- **THEN** the live run takes it, and builds it beside the others
- **AND WHEN** a folder stands in `.minions/runs/rejoin/` beside the request
- **THEN** the poll skips it, and the run goes on
- **AND WHEN** `.minions/runs/rejoin` is a link to another folder
- **THEN** the poll reads no request there, and deletes nothing in it

#### Scenario: A new executor
- **WHEN** a taken version's models file names an executor the run has not probed
- **THEN** the run probes it before that version's first worker, and the version goes on
- **AND WHEN** that probe fails
- **THEN** only the versions on that executor halt, the probe run once for them all, and the others release

#### Scenario: A request at the close
- **WHEN** a request lands after the last version's thread ends
- **THEN** the run reads it before its close
- **AND WHEN** a request outlives its run
- **THEN** the next run's start deletes it, and takes every open version anyway
