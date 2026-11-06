## MODIFIED Requirements

### Requirement: A halted version is rescued in its run

When a version halts on its build check, a converge halt — its cap the run does not grant, or `amend needed` among them — or integrate's red gate or note, `conduct.py` SHALL spawn the
`mf-rescue` station in that version's thread, unless its models file's `[rescue]` table says `skip = true`; the station SHALL run on
the `[rescue]` table's executor and model, the `[build]` table's when there is none. `skills/mf-build/SKILL.md` SHALL write
`.minions/changes/<id>/build.halt` on every halt — the sub-task, the stop condition, one line of evidence. `skills/mf-rescue/SKILL.md` SHALL
fix a build halt on a `Verify:` that cannot pass, a reader a deletion missed, a task two readings would build differently, or an
`Verify:` that is not one plain command — a `$(…)`, a shell variable, a loop or a `cd` — and a converge `amend needed` halt with the
amend its `wontfix` cards name, with one `docs(<id>): amend the change directory` commit touching only `openspec/changes/<id>/tasks.md` and `design.md`,
never `design.md`'s decisions table without the version's switch, carrying a `Rescue:` trailer; every other halt it SHALL diagnose in `.minions/changes/<id>/rescue.md`.
An `amend needed` halt naming a security card of `critical` or `high` severity SHALL get a diagnosis alone, whatever the
switch. The rescue SHALL be offered its amend whether the version halted in this run or before it, at the run's start.
`conduct.py` SHALL halt the version when the commit touches any other path, and otherwise clear its halt and go on in the same run, an
`amend needed` halt to a converge run marked `· amended`. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer and wait for a re-run — save the person's
`docs(<id>): amend the change directory` commits, which answer an `amend needed`, `verify: halt` or clean catch-up halt
by amends alone: the version SHALL go on in the run, logged `rescue — <id>: amended · <commit>`. A version SHALL
get at most `RESCUES = 3` rescues in a run, and none for a sub-task it rescued before; a timeout, a usage limit and D47's halts that
need the person SHALL get none. The run SHALL log `rescue — <id>: fixed · <sub-task> · <commit>`, `rescue — <id>: decided ·
<sub-task> · <commit>` or `rescue — <id>: diagnosed · <file>`, and `report` SHALL print each. The rejoin folder and the grants folder SHALL be read and emptied through a directory file
descriptor opened without following a link.

#### Scenario: A check that cannot pass
- **WHEN** a build halts on a `Verify:` whose search matches a line no task touches
- **THEN** the rescue amends `tasks.md`, the run logs `rescue — fixed`, and the version builds on and releases in the same run

#### Scenario: A decision halt
- **WHEN** a build halts on a design premise the code rules out
- **THEN** the rescue writes `.minions/changes/<id>/rescue.md`, and the version stays halted, its halt naming the file

#### Scenario: A rescue outside the plan
- **WHEN** a rescue's commit touches a file outside `tasks.md` and `design.md`
- **THEN** the version halts, naming the file

#### Scenario: A rescue at amend needed
- **WHEN** converge halts `amend needed` on a review card whose fix names a `design.md` prose amend, in the run or before it
- **THEN** the rescue commits that amend, and the version converges again in the same run, in a run marked `· amended`
- **AND WHEN** the card is a security card of `high` severity
- **THEN** the rescue diagnoses, and the version stays halted

#### Scenario: An amend lands during a rescue
- **WHEN** the person commits `docs(<id>): amend the change directory` while the rescue of its `amend needed` halt runs
- **THEN** the version goes on in the same run, and the run logs `rescue — <id>: amended`

#### Scenario: A rescue that answers its cap
- **WHEN** a rescue at a converge cap writes a grant and a rejoin request
- **THEN** the run starts no further converge round, and logs the version still halted

#### Scenario: The same sub-task again
- **WHEN** a version halts again on a sub-task it was rescued from
- **THEN** no rescue runs, and the halt names both

#### Scenario: A link at the rejoin folder
- **WHEN** a worker swaps the rejoin folder for a link to another directory after the run lists it
- **THEN** nothing in that directory is deleted

### Requirement: A halted version rejoins a live run

`conduct.py rejoin [<change-id>]` SHALL write a request in the repository's queue in the home folder, where no worker writes,
under the queue lock, and `/mf-ship` SHALL send it when a run is live. The live run SHALL check that folder at most every 10
seconds and before its close, and SHALL take into the run every
open version the request names — every one for a request with no id — whose stage on disk is no longer a halt: a halted one,
a blocked one, and one cut after the run started. A version still at a halt SHALL stay out, logged with why. The poll SHALL
not end the run's loop while a version's thread runs: an entry it cannot delete SHALL be no request, and a version it fails
to take SHALL halt alone. A request folder that is a link SHALL hold no request, and the poll SHALL delete nothing through
it. A version the run's plan already holds SHALL stay out, logged, while its models file differs from what the run read, and
a version whose rescue answered its converge or integrate halt on disk SHALL stay out, logged, for the rest of the run, both
waiting for a re-run. Anything that answers that halt on disk while its rescue runs, or before the run reads the rescue's
outcome, SHALL count as the rescue's answer: the person's own commit past the halted head, settled merge or removed note, and
a grant landing after the rescue's `finish`, included. The person's `docs(<id>): amend the change directory` commits that
answer a halt by amends alone SHALL not: that version goes on in its run. Any other taken version
SHALL have its models file read as it joins, then go through the run's base check, its dependencies, its stations and the
merge lock, as at a run's start, with its halts and blocks cleared. Its executor's probe SHALL run once in the run, before
the first worker on it; a failed probe SHALL halt only the versions on that executor, each later one with that probe's
reason and no second probe. The run SHALL log a `rejoin` event per
version taken, delete the requests it read, and a run's start SHALL delete every request it finds. A run-level halt SHALL
end the run, as before. A request that lands after a run's last poll and before it removes its claim SHALL start the next
run, which deletes it at its start and takes every open version.

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

- **AND WHEN** only the person's amends answered an `amend needed` halt while its rescue ran
- **THEN** the version goes on in the run, with no request

#### Scenario: A version cut during the run
- **WHEN** a version is cut while a run is live, and `/mf-ship` runs
- **THEN** the live run takes it, and builds it beside the others
- **AND WHEN** a folder stands in the queue's request folder beside the request
- **THEN** the poll skips it, and the run goes on
- **AND WHEN** the request folder is a link to another folder
- **THEN** the poll reads no request there, and deletes nothing in it

#### Scenario: A worker writes a request
- **WHEN** a worker writes a file in `.minions/runs/rejoin/`
- **THEN** no run reads it as a request

#### Scenario: A new executor
- **WHEN** a taken version's models file names an executor the run has not probed
- **THEN** the run probes it before that version's first worker, and the version goes on
- **AND WHEN** that probe fails
- **THEN** only the versions on that executor halt, the probe run once for them all, and the others release

#### Scenario: A request at the close
- **WHEN** a request lands after the last version's thread ends
- **THEN** the run reads it before its close
- **AND WHEN** a request lands after the run's last poll and before it removes its claim
- **THEN** the run's close starts the next run, whose start deletes it and takes every open version

## ADDED Requirements

### Requirement: A rescue decides by the version's switch

A version's models file MAY say `decide = "recommended"` at its top, before its tables: the **switch**, which the cut writes
from the brief. `conduct.py` SHALL read it once a run, with the version's plan, and pass it to the rescue as `decide=recommended`.
Under the switch, `skills/mf-rescue/SKILL.md` SHALL take the fix a card or the plan itself proposes as its own decision, at a build
halt and an `amend needed` halt: it MAY edit `proposal.md` and `design.md`'s `## Decisions` besides `tasks.md` and
`design.md`'s prose, and its commit SHALL carry a `Decided-by: rescue` trailer. It SHALL never edit the spec delta, code or a
test, take a security card of `critical` or `high` severity, approve a gate makefile, settle an integrate conflict, release,
merge or push, or answer a run-wide halt. `conduct.py` SHALL take an amend that touches `proposal.md` or changes `design.md`'s
`## Decisions` section only under the switch and with that trailer, logging `rescue — <id>: decided · <sub-task> · <commit>`;
without the switch it SHALL refuse it, naming the decision. The run's closing line, and its `done` line, SHALL name
` · decided <ids>` when a rescue decided, `report` SHALL print a line for each decision, and the run's metrics SHALL count them as `rescues-decided`.

#### Scenario: A decided amend
- **WHEN** a version's models file says `decide = "recommended"`, and its rescue at `amend needed` commits an edit to a row of
  `design.md`'s `## Decisions` with `Decided-by: rescue`
- **THEN** the run takes it, logs `rescue — <id>: decided`, the version converges again, and `report` and the closing line name it

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue commits the same amend
- **THEN** the run refuses it, naming the decision, and the version stays halted

#### Scenario: A worker writes the switch
- **WHEN** a worker adds `decide = "recommended"` to the models file during the run
- **THEN** no rescue of that run decides for that version

### Requirement: A run goes on while anything can move

At each poll, at most `REJOIN_POLL` seconds apart whatever the number of live threads, so within one poll of each rescue's end, `conduct.py` SHALL take back, with no request, every halted version with no live
thread that is neither blocked nor held for its rescue's answer, when its stage on disk is no halt and its stage or `HEAD` differs
from what the run read when the version halted, the same at two polls in a row. A version that halts again with nothing changed on
disk SHALL not be taken again; `RESCUES = 3` stands. The run SHALL end only when no version thread is live, and neither a request,
a queued cut nor this re-check starts one. Its closing line SHALL name, after `released <tags>`, the one action each halted version
needs: ` · needs <id> <action>`, joined by `, `.

#### Scenario: A fix while the run waits
- **WHEN** a version halts while another builds, and the person commits a fix on its branch
- **THEN** the run takes it back at its next poll, with no request, and it releases in the same run

#### Scenario: Nothing changed
- **WHEN** a version halts on a timeout, and nothing on disk changes
- **THEN** the run does not take it back, and its closing line names the version and what it needs

#### Scenario: The run ends when nothing can move
- **WHEN** every version thread has ended, and no halted version's stage or `HEAD` changed since its halt
- **THEN** the run closes, naming each halted version's action
