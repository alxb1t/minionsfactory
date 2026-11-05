## ADDED Requirements

### Requirement: A run grants one round at a small cap, and halts a large one for a re-plan

When a version's converge halts with `cap reached` in a run, `conduct.py` SHALL read the open blocking findings in its review and
security findings files — review's `blocking`, security's `critical` and `high`, each `Status: open` — and, when every one's fix is
sized `one line`, `a test` or `one line and a test`, no granted round reached the cap — its converge run is not marked `· grant`,
and the run has not granted the version already — and its models
file's `[converge]` table does not say `auto_grant = false`, SHALL spawn converge with `grant=yes` itself, writing no grant file and
starting no rescue, log `grant — <id>: automatic · <ids>`, and check the round as it checks a person's grant's. Otherwise — a blocker sized `a design change`, no open blocking card read, a granted
round's cap, automatic or a person's, in this run or an earlier one, a second cap in the run, or `auto_grant = false` — the run SHALL write the version a last halt line, `re-plan: <ids>`, and the version's rescue SHALL
diagnose it, naming `/mf-plan` with the version's brief as the way back. A person's grant SHALL still spend a round on a re-plan
halt. `mf-converge` run by hand grants nothing on its own.

#### Scenario: A small cap
- **WHEN** a version caps with open blockers sized `one line` and `a test`
- **THEN** the run logs `grant — <id>: automatic`, converges one more round, writes no `.minions/grants/<id>`, and releases the
  version in the same run when that round is clean

#### Scenario: A design change at the cap
- **WHEN** an open blocker at the cap is sized `a design change`
- **THEN** no grant is spent, and the version halts as `re-plan`, its rescue naming `/mf-plan`

#### Scenario: The granted round blocks again
- **WHEN** the automatically granted round ends with a blocker open
- **THEN** the version halts as `re-plan`, and no second automatic grant is spent
- **AND WHEN** a later run reads that cap
- **THEN** it halts the version as `re-plan` and spawns no converge

#### Scenario: The granted round ends unfinished
- **WHEN** the automatically granted round's converge exits 0 with its status log not on `done`
- **THEN** the run logs the converge check's failure and halts the version, spawning no other converge

#### Scenario: Turned off
- **WHEN** the version's models file says `[converge] auto_grant = false`
- **THEN** its cap halts as `re-plan` with no automatic grant

## MODIFIED Requirements

### Requirement: A halted version is rescued in its run

When a version halts on its build check, its converge cap the run does not grant, or integrate's red gate or note, `conduct.py` SHALL spawn the
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
