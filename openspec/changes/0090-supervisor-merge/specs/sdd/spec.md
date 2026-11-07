## MODIFIED Requirements

### Requirement: A supervisor answers what the rescue leaves

Under a version's switch, `decide = "recommended"`, when its rescue at a build check halt, a converge halt or an
`integrating` halt on a semantic conflict writes a diagnosis, the run diagnoses its converge `verify: halt`, or its rescue is
spent on the halt — the sub-task rescued before in the run, or `RESCUES` reached — `conduct.py` SHALL spawn the `mf-supervise`
station in that version's thread, with `decide=recommended`, and with `brief=<path>` when the version's passed cut recorded a
brief that still names a file. It SHALL spawn none without the switch; at an integrate red gate; at an `integrating` halt on
an open merge a supervisor was spawned on before, in this run or an earlier one, which the home folder's queue records; at a
halt the rescue's answer
on disk holds for a re-run; at a converge halt while `security.md` holds an open card of `critical` or `high` severity, or its
`amend needed` names one; when the rescue's worker failed or its amend was refused; nor when the models file's `[rescue]` table
says `skip = true`. The station SHALL run on the `[supervise]` table's executor, model and effort; on Claude, an absent model
SHALL be `claude-opus-5-5` and an absent effort `high`. At a passed cut, `conduct.py` SHALL record the brief's path in the
home folder's queue, under `briefs/<id>`, where no worker writes; a version cut by hand SHALL have none. The station SHALL
read the brief as evidence, never instruction.

`skills/mf-supervise/SKILL.md` SHALL answer a build or converge halt with one `docs(<id>): amend the change directory` commit
carrying `Supervisor: <sub-task or stage>` and `Decided-by: supervisor` trailers, or commit nothing. It MAY edit any file under
`openspec/changes/<id>/`, the spec delta included, tick a sub-task box whose `Verify:` it ran and saw pass, and add work as a new
unticked phase after the last. It SHALL never edit code, a test or any other path, take a security card of `critical` or `high`
severity, approve a gate makefile, accept a risk the threat model does not accept, untick a box, release, merge or push. At an
`integrating` halt it SHALL instead resolve the note's conflicts in Markdown files under `openspec/` and `docs/` alone, stage
each by name, write `.minions/changes/<id>/integrate.settled` naming what it settled, leave the merge and the note open, and
commit nothing; or edit nothing.

`conduct.py` SHALL take the commit only when it is the one commit past the station's start, with one parent, the amend's
subject, a `Supervisor:` trailer, a `Decided-by:` trailer reading `supervisor`, and paths under `openspec/changes/<id>/` alone. It
SHALL then clear the version's halt and its diagnosis, log `supervise — <id>: decided · <sub-task or stage> · <commit>`, and go
on in the same thread, with no restart and no wait for a poll. At an `integrating` halt it SHALL take the settle only when
`HEAD` and the open merge are the station's start's, the note stands, every index path it changed is a Markdown file under
`openspec/` or `docs/`, the work tree holds nothing unstaged or untracked, no path stays unmerged, and `integrate.settled` was
written during the station's run. It SHALL then clear the version's halt and its diagnosis, log
`supervise — <id>: decided · integrating · <tree>`, `<tree>` the staged tree, and spawn `mf-integrate` `with settled=supervisor`
in the same thread. Any other outcome SHALL halt the version, naming what the station left; at a converge halt, an answer on
disk SHALL then hold the version for a re-run as the rescue's does, the halt reading `supervisor answered its halt`, and the
person's amends alone, none carrying a `Rescue:` or `Supervisor:` trailer, SHALL go on. A version SHALL get one supervisor try
per halt and at most `SUPERVISES = 2` in a run; a halt the supervisor tried before SHALL name ` · supervised <sub-tasks>`. A
grant SHALL be refused while the station runs, as while the rescue runs. `report` SHALL print
`<id> · supervised <sub-task or stage> · <commit>` for each taken amend or settle, the run's closing line and its `done` line
SHALL name ` · supervised <ids>`, and the run's metrics SHALL count them as `supervisor-decided`.

#### Scenario: A diagnosed halt under the switch
- **WHEN** a build halts, its rescue writes a diagnosis, and the version's models file says `decide = "recommended"`
- **THEN** the supervisor runs, its amend of the spec delta with both trailers is taken, the run logs
  `supervise — <id>: decided`, and the version builds on and releases in the same run
- **AND** `report` prints `<id> · supervised 1.1 · <commit>`, and the `done` line names ` · supervised <id>`

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue diagnoses the halt
- **THEN** no supervisor runs, and the version stays halted, its halt naming the diagnosis

#### Scenario: An amend touching a test
- **WHEN** the supervisor's commit touches a file under `tests/`
- **THEN** the version halts, naming the file, and the run logs no `supervise —` line

#### Scenario: A spent rescue
- **WHEN** under the switch a version halts again on a sub-task its rescue amended before in the run
- **THEN** the supervisor runs once, with no rescue
- **AND WHEN** the version halts on that sub-task again
- **THEN** no worker runs, and the halt names ` · rescued 1.1 · supervised 1.1`

#### Scenario: A refused amend at a converge halt
- **WHEN** the supervisor at an `amend needed` halt commits an amend of the change directory with no `Decided-by: supervisor`
  trailer
- **THEN** the version stays halted for the run, its halt reading `supervisor answered its halt`, and the closing line names
  `a re-run` as its need

#### Scenario: A blocking security card
- **WHEN** converge halts `amend needed` naming a security card of `high` severity, under the switch
- **THEN** the rescue diagnoses, no supervisor runs, and the version stays halted

#### Scenario: The brief kept at a passed cut
- **WHEN** a queued cut passes its check
- **THEN** the home folder's queue holds `briefs/<id>`, naming the brief's path, after the cut's queue entry is gone
- **AND WHEN** that version's supervisor runs under the switch
- **THEN** its prompt names `brief=<path>`
- **AND WHEN** a version cut by hand has its supervisor run
- **THEN** its prompt names no brief

#### Scenario: A note the supervisor settles
- **WHEN** under the switch a dependent's delta halts `integrating` on a semantic conflict, the rescue diagnoses it, and the
  supervisor stages its resolution of the version's delta and writes `integrate.settled`
- **THEN** the run logs `supervise — <id>: decided · integrating · <tree>`, spawns `mf-integrate` `with settled=supervisor`,
  whose merge commit holds that tree and names the note's heading as `the supervisor`, and the version builds on and releases
  in the same run

#### Scenario: A settle outside the text
- **WHEN** the supervisor at an `integrating` halt stages a file outside `openspec/` and `docs/` Markdown
- **THEN** the version halts, naming the file, the merge and the note stay open, and the run logs no `supervise —` line
- **AND WHEN** a later run meets the same open merge's halt
- **THEN** its rescue runs, no supervisor runs, and the version stays halted for the person

### Requirement: A semantic conflict is handed to the person with the merge open

When the delta check reports a changed requirement, or git leaves a conflict that is not additive (one side editing what the
other removed, two values for one thing, designs that disagree, a choice between behaviours),
`skills/mf-integrate/SKILL.md` SHALL halt with the merge in progress in the version's worktree, write
`.minions/changes/<change-id>/integrate.md` holding both intents and a proposed resolution, and continue from the open
merge on its next run. A MODIFIED delta that only inserts into the default branch's current block, and keeps nothing the default
branch removed, SHALL NOT count as a semantic conflict. Under the version's switch, the version's supervisor MAY settle the note
first, in Markdown under `openspec/` and `docs/` alone; `mf-integrate`'s next run, given `settled=supervisor` by `conduct.py`
alone, SHALL then commit the merge as staged and gate it, and SHALL delete `integrate.settled` with the note.

#### Scenario: Both versions changed one requirement
- **WHEN** the branch's delta modifies a requirement the default branch also changed since the base, and changes or removes a
  line of the default branch's current block
- **THEN** the merge stays open, the note names both changes, and the next run continues from `MERGE_HEAD`

#### Scenario: Two values for one thing
- **WHEN** the branch sets a constant to one value and the default branch sets it to another
- **THEN** the merge stays open, the note names both changes, and nothing is resolved

#### Scenario: The branch already holds the default branch's change
- **WHEN** the branch's delta modifies a requirement the default branch also changed, and the delta's block holds the default
  branch's block with lines added
- **THEN** no note is written, and the merge is committed

#### Scenario: The supervisor settled the note
- **WHEN** `mf-integrate` runs with `settled=supervisor` on an open merge whose note stands
- **THEN** it commits the merge as staged, with no rule run again, gates it, and deletes the note and `integrate.settled`

### Requirement: The integrate merge commit names every path it settled

`skills/mf-integrate/SKILL.md`'s merge commit SHALL hold one body line per path it settled: `<path>: integrate.py <rule>` for a
fixed rule, the union line as before, `<path>: the person` after a note halt, `<path>: the supervisor` after a note the
supervisor settled, and `<path>: test fixed — <what it now asserts>` for a test the integrator edited, which SHALL never remove
or loosen an assertion. A test the integrator fixed past the person's fix SHALL be named in a commit of its own, its message
that line and the trailer block, and the merge commit SHALL stay as it was.

#### Scenario: A merge the rules and a person settled
- **WHEN** a merge's `CHANGELOG.md` was settled by the rule and a requirement by the person after a note halt
- **THEN** the commit body names `CHANGELOG.md: integrate.py changelog` and the requirement's path as `the person`

#### Scenario: A merge the supervisor settled
- **WHEN** `mf-integrate` runs with `settled=supervisor` after a note halt naming a requirement
- **THEN** the commit body names the requirement's path as `the supervisor`, and no path as `the person`

#### Scenario: A test fixed past the person's fix
- **WHEN** integrate halted on a red gate, the person committed a fix past the merge, and a merged test the union broke is still red
- **THEN** the integrator commits the test fix on its own, its message `<path>: test fixed — …` and the trailer block, and the
  merge commit names no test fixed
