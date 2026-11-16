## ADDED Requirements

### Requirement: A queued cut waits while the line is at its cap

A run SHALL read `in_flight` under `[queue]` in `ship.toml`, found under `$XDG_CONFIG_HOME/minionsfactory/`, else
`~/.config/minionsfactory/`, once at its start; a missing file, a missing `[queue]` table or a missing key SHALL mean no cap, as
before. A file that cannot be read, or a value that is no whole number above 0, SHALL stop `conduct.py run` and `conduct.py cut`
with exit 2, naming the file. With a cap, the run SHALL take a queued cut, at its start and at each poll, in id order, only
while fewer versions are in flight than the cap, and SHALL count the versions of its own repository alone. A version SHALL be in
flight while its thread runs, no halt names it and every `after` id it names is shipped, its cut included; a halted version, and
a version or cut waiting on its `after`, SHALL not be. A rejoin request naming a cut, the take-back of a version by a rejoin or a
grant, and a version already cut at the run's start SHALL run whatever the cap.

A cut that waits SHALL not count as read: the run SHALL take it at the first poll after a slot frees, SHALL stay alive while it
waits and a version is in flight, and its close SHALL start no next run for a cut that only waits. A waiting cut SHALL carry its
reason, `<n> in flight, cap <N>`, in its queue entry, written under the queue lock and cleared when the run takes the cut, and
the run SHALL log one `wait` line when a cut starts to wait. `status` SHALL print the reason, the viewer SHALL show the state
`queued` with it, and `conduct.py cut` SHALL name the cap in its line.

#### Scenario: No file
- **WHEN** no `ship.toml` stands, or it holds no `in_flight` key, and cuts are queued for a run
- **THEN** the run takes every queued cut at its start, and each cut queued into the live run at the next poll

#### Scenario: A bad file
- **WHEN** `ship.toml` cannot be parsed, or `in_flight` is `0`, negative, a fraction, a string or a boolean
- **THEN** `conduct.py run` exits 2 naming the file, and starts no worker, and `conduct.py cut` exits 2 and reserves nothing

#### Scenario: A cap of 1
- **WHEN** `in_flight` is 1 and two cuts are queued
- **THEN** the run takes the lower id, logs one `wait` line for the other, and takes it only after the first's release

#### Scenario: A halted version does not hold the queue
- **WHEN** `in_flight` is 1 and the one version in flight halts
- **THEN** the run takes the next queued cut at its next poll, the halted version still open

#### Scenario: A version waiting on its after does not hold the queue
- **WHEN** `in_flight` is 1 and the one version at a station names an `after` id that is not shipped
- **THEN** the run takes the next queued cut at its next poll

#### Scenario: A cut queued into a live run
- **WHEN** `in_flight` is 1, a version is in flight and a cut is queued
- **THEN** the cut waits, its queue entry holds `1 in flight, cap 1`, and the run takes it at the poll after the version leaves the line

#### Scenario: A rejoin runs past the cap
- **WHEN** `in_flight` is 1, a version is in flight and `conduct.py rejoin <id>` names a halted cut
- **THEN** the live run takes that cut at its next poll

#### Scenario: A cap above 1
- **WHEN** `in_flight` is 2 and three cuts are queued
- **THEN** the run takes the two lowest ids and holds the third until one of them leaves the line

#### Scenario: The run stays alive for a waiting cut
- **WHEN** a cut waits and the only version in flight is still building
- **THEN** the run does not end, and takes the cut once the version releases

#### Scenario: The close starts no run for a waiting cut
- **WHEN** a run ends with a queued cut that only waited for room
- **THEN** its close starts no next run, and a cut queued after its last poll still starts one

#### Scenario: A waiting cut is shown
- **WHEN** a cut waits at `1 in flight, cap 1`
- **THEN** `status` prints `<id> · cut — waits: 1 in flight, cap 1`, the viewer's queue shows `<id>` in the state `queued` with that reason, and `conduct.py cut` prints the cap in its line

## MODIFIED Requirements

### Requirement: A run cuts each queued brief in a station of its own

A run SHALL read the queue at its start and at every poll, and take each queued cut with no halt that it has not read
before, or that a request names, while the line has room under its cap, a request-named cut excepted
(*A queued cut waits while the line is at its cap*). For each, `conduct.py` SHALL make the branch named by its id and its linked worktree from the
default branch, as code, then run `mf-cut-change` with `unattended=yes` as a fresh sandboxed worker in that worktree, logged
as the station `cut`. The cut SHALL pass when the branch's tip is the change's `docs(<id>): land the change directory` commit,
the branch holds `openspec/changes/<id>/`, its tree is clean, `.minions/changes/<id>/models.toml` stands, and each row of the
`## Dependencies` of the branch's `design.md` names a package and constraint the queue entry holds, as written. The station
SHALL read the branch's tip, its change directory and its `design.md` at `refs/heads/<id>`, never a tag of that name, and SHALL
read `design.md` as CommonMark with GFM tables
renders it: the section opens at the ATX heading written `## Dependencies` and runs to the next heading of level one or two, or
HTML heading of those levels, and its rows are the cells of the table rendered there. A section that is neither `None.` nor
one table of package, constraint and why SHALL fail the cut, as SHALL a heading or HTML heading that reads as `## Dependencies`
once every character but a letter or a digit is dropped and case is folded but is not written so, or a second
`## Dependencies`; a line inside a code block is no heading, and a missing section adds no package. The run SHALL then
delete its queue entry and reservation, read its models file and probe a new executor, and take the version through its
stations as any open version. A branch that already holds the change SHALL be checked, not cut again. A cut whose
`after` names a queued cut SHALL wait until that cut passes, and halt when it halts. The cutter's executor SHALL be probed
before its first worker, as a version's is. The run SHALL never read the brief for a package's approval.

#### Scenario: A queued cut is built
- **WHEN** a run takes a queued cut and the cutter commits its change directory and models file
- **THEN** the cut passes, its reservation goes, and the version goes into `build` in the same run

#### Scenario: A cut queued during a run
- **WHEN** a cut is queued while a run is live
- **THEN** the run takes it at its next poll, beside the versions it is running, while the line has room under its cap

#### Scenario: A cut that adds the approved packages
- **WHEN** the cutter commits a `design.md` whose `## Dependencies` lists only packages and constraints the queue entry holds
- **THEN** the cut passes, and the version goes into `build`

#### Scenario: A cut that adds another package
- **WHEN** the committed `design.md` lists a package the queue entry does not hold, or a constraint other than the one it holds
- **THEN** the cut halts at `cut-halted`, naming each such package and constraint

#### Scenario: A table a line splitter would miss
- **WHEN** the committed `design.md`'s `## Dependencies` table lists `evil 1` after a line `` ```x` `` above the section, or
  under lone carriage returns, or after a row `#- note`
- **THEN** the cut halts at `cut-halted`, naming `evil 1`

#### Scenario: A tag named after the change
- **WHEN** a tag named the change id points at a commit whose `design.md` lists no package, and the branch's `design.md` lists
  one the queue entry does not hold
- **THEN** the station reads the branch, and the cut halts naming that package

### Requirement: A settled brief is queued for a cut

`conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] [beside=<id>[,<id>]] --executor claude|codex [--model <m>]
[--effort <e>]`, run
in the primary, SHALL take the next free change number under the repository's queue lock: one above every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch, every branch named by a change id and its committed
change directories, every reservation in `.minions/cuts/` and every queued cut. It SHALL write the reservation
`.minions/cuts/<id>` and keep the cut's bump, brief path, `after` ids, any `beside` ids, executor, model and effort in the
queue in the home folder, where no worker writes, with the package and constraint of each row of the brief's
`## Dependencies` whose item is `<slug>`, then hand the cut to the live run, or, with none live, start a run detached and
wait, under the lock, until that run holds its claim or has ended. Its line SHALL name the cap when `ship.toml` sets one. A brief with no `## Dependencies` approves no package. A
queue entry with no `beside` SHALL read as one naming none. A slug that is not lowercase words joined by `-`, a bump other
than `minor` or `patch`, a brief that is no file, a brief whose `## Dependencies` is neither `None.` nor a table of item,
package, constraint and why, an `after` id that names no open version or queued cut, a `beside` id that is no change id, or
an argument after the brief that is neither `after=` nor `beside=`, or names either twice, SHALL exit 2 and reserve nothing;
so SHALL a run that cannot start, its precondition named. Queuing a cut SHALL be the person's yes to cut,
run, merge and push that version, and to the packages its rows name. A run SHALL take the queue lock before it removes its
claim, and then start the next run when a rejoin request or a queued cut it never read stands, a cut that only waits for room
under the cap excepted.

#### Scenario: Two cuts at once with no run live
- **WHEN** two `conduct.py cut` calls run at once and no run is live
- **THEN** they reserve two different numbers, and exactly one run starts

#### Scenario: A cut while a run is live
- **WHEN** `conduct.py cut` runs while a run is live
- **THEN** it reserves the next number, starts no run, and prints that the live run takes it

#### Scenario: A cut as a run ends
- **WHEN** a cut is queued after a run's last poll and before it removes its claim
- **THEN** the run's close starts the next run, which takes it
- **AND WHEN** the run read every queued cut and no request stands
- **THEN** its close starts no run

#### Scenario: A brief that is no file
- **WHEN** `brief=` names no file
- **THEN** `conduct.py cut` exits 2, naming it, and reserves nothing

#### Scenario: A brief's packages
- **WHEN** the brief's `## Dependencies` holds rows for the queued slug and for another item
- **THEN** the queue entry holds the package and constraint of the slug's rows alone
- **AND WHEN** the section is prose, neither `None.` nor a table
- **THEN** `conduct.py cut` exits 2, naming the section, and reserves nothing

#### Scenario: A cut beside another
- **WHEN** `conduct.py cut <slug> minor brief=<path> beside=<id>` runs, `<id>` a change id
- **THEN** the queue entry holds `<id>` as its `beside` ids
- **AND WHEN** a `beside` id is no change id, or the argument after the brief opens neither `after=` nor `beside=`
- **THEN** `conduct.py cut` exits 2, naming it, and reserves nothing

### Requirement: A cut halt is the plan's, answered by a re-plan and a rejoin

A cut that does not pass SHALL put its queued cut at the stage `cut-halted`, with one line: the line the cutter wrote in
`.minions/changes/<id>/cut.halt`, else the failed check or worker exit, kept in its queue entry. The cutter's own line, and a
package outside the queue entry's rows, SHALL end
` · needs <id> its brief answered (/mf-plan <id> depth=hard brief=<brief> from=<brief>), then conduct.py rejoin <id>`, `<brief>`
the path its queue entry holds; every other cut halt keeps its line. No rescue SHALL run. `status`
SHALL print `<id> · cut` for a queued cut, `<id> · cut — waits: <n> in flight, cap <N>` for one that waits for room under the
cap, and `<id> · cut-halted — <line>` for a halted one, `report` SHALL print its halt
line, and the run's closing line SHALL name ` · needs <id> its brief answered (…), then conduct.py rejoin <id>` for a cut
halted with that answer. A run's start SHALL log each halted cut as a halt and take it into no thread. `conduct.py rejoin <id>`
naming a queued cut SHALL clear its halt, under the queue lock, keeping the queue entry's already-queued package rows, then
request it from the live run, or start a run when none is live; a brief it cannot read, or whose `## Dependencies` is
neither `None.` nor a table, SHALL exit 2, naming it, and keep the halt. A row of the brief's `## Dependencies` for its slug
that the entry does not already hold SHALL be queued only when the rejoin is given `--yes <hash>`, `<hash>` the sha256 of
those new rows; without it, or with another hash, the rejoin SHALL exit 1, keep the entry and its halt, and name each new
row and the exact `conduct.py rejoin <id> --yes <hash>` command, the person's yes to those rows. `--yes` on a rejoin naming
no queued cut SHALL exit 2. The run SHALL then drop the cut's branch and worktree,
when its branch holds no change, and cut again from the brief.

#### Scenario: A cutter halts
- **WHEN** the cutter writes `cut.halt` and commits nothing
- **THEN** the run logs `<id> · halt — cut-halted — <its line> · needs <id> its brief answered (…), then conduct.py rejoin <id>`,
  runs no rescue, `status` prints `<id> · cut-halted — ` and the same line, and the closing line names the answer

#### Scenario: A re-plan and a rejoin
- **WHEN** the person re-plans the brief and runs `conduct.py rejoin <id>`
- **THEN** the cut's half-done branch is dropped, the brief is cut again, and a cut that passes goes into `build`

#### Scenario: A package approved at the re-plan
- **WHEN** a cut halted on a package outside its queued rows, and the person's re-plan adds that row to the brief's
  `## Dependencies` before `conduct.py rejoin <id>`
- **THEN** the rejoin exits 1 naming that row and `conduct.py rejoin <id> --yes <hash>`
- **AND WHEN** the person runs that command
- **THEN** the row is queued beside the queued rows, and the branch's cut is checked again and passes

#### Scenario: A rejoin whose brief adds a package row
- **WHEN** a queued cut's entry holds `left-pad 1.3.0`, its brief's `## Dependencies` also lists `right-pad ^2` for its slug,
  and `conduct.py rejoin <id>` runs with no `--yes`, after a fix on disk and no re-plan
- **THEN** it exits 1 naming `right-pad ^2` and `conduct.py rejoin <id> --yes <hash>`, the entry holds `left-pad 1.3.0`
  alone and keeps its halt, and no run is asked to take the cut
- **AND WHEN** `conduct.py rejoin <id> --yes <hash>` runs with that hash
- **THEN** the entry holds `left-pad 1.3.0` and `right-pad ^2`, its halt cleared, and the run takes the cut back

#### Scenario: A failed check on disk
- **WHEN** a cut halts on a dirty tree, a missing models file, a kept worktree or a worker's exit
- **THEN** its line names no brief, and the closing line names `a fix`
