## ADDED Requirements

### Requirement: A settled brief is queued for a cut

`conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] --executor claude|codex [--model <m>] [--effort <e>]`, run
in the primary, SHALL take the next free change number under the repository's queue lock: one above every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch, every branch named by a change id and its committed
change directories, every reservation in `.minions/cuts/` and every queued cut. It SHALL write the reservation
`.minions/cuts/<id>` and keep the cut's bump, brief path, `after` ids, executor, model and effort in the queue in the home
folder, where no worker writes, then hand the cut to the live run, or, with none live, start a run detached and wait, under
the lock, until that run holds its claim or has ended. A slug that is not lowercase words joined by `-`, a bump other than
`minor` or `patch`, a brief that is no file, or an `after` id that names no open version or queued cut SHALL exit 2 and
reserve nothing; so SHALL a run that cannot start, its precondition named. Queuing a cut SHALL be the person's yes to cut,
run, merge and push that version. A run SHALL take the queue lock before it removes its claim, and then start the next run
when a rejoin request or a queued cut it never read stands.

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

### Requirement: A run cuts each queued brief in a station of its own

A run SHALL read the queue at its start and at every poll, and take each queued cut with no halt that it has not read
before, or that a request names. For each, `conduct.py` SHALL make the branch named by its id and its linked worktree from the
default branch, as code, then run `mf-cut-change` with `unattended=yes` as a fresh sandboxed worker in that worktree, logged
as the station `cut`. The cut SHALL pass when the branch's tip is the change's `docs(<id>): land the change directory` commit,
the branch holds `openspec/changes/<id>/`, its tree is clean and `.minions/changes/<id>/models.toml` stands; the run SHALL then
delete its queue entry and reservation, read its models file and probe a new executor, and take the version through its
stations as any open version. A branch that already holds the change SHALL be checked, not cut again. A cut whose
`after` names a queued cut SHALL wait until that cut passes, and halt when it halts. The cutter's executor SHALL be probed
before its first worker, as a version's is.

#### Scenario: A queued cut is built
- **WHEN** a run takes a queued cut and the cutter commits its change directory and models file
- **THEN** the cut passes, its reservation goes, and the version goes into `build` in the same run

#### Scenario: A cut queued during a run
- **WHEN** a cut is queued while a run is live
- **THEN** the run takes it at its next poll, beside the versions it is running

### Requirement: The cutter reaches its worktree, the run directory and its brief

The cut station's worker SHALL run in its executor's OS sandbox, as every worker does, writing only its own worktree, the run
directory and the common git directory, and the one brief file its queue entry names: a Claude cutter SHALL be given that
worktree and the run directory alone as its directories, and an edit rule for the brief alone; a Codex cutter SHALL take the
brief's folder as a writable root. No other version's worktree SHALL be in its reach.

#### Scenario: A Claude cutter's reach
- **WHEN** the run spawns a Claude cutter for a brief outside the repository
- **THEN** its directories are its worktree and the run directory, its sandbox writes those, the common directory and the
  brief, and its allowed rules edit the brief and no other file outside them

### Requirement: A cut halt is the plan's, answered by a re-plan and a rejoin

A cut that does not pass SHALL put its queued cut at the stage `cut-halted`, with one line: the line the cutter wrote in
`.minions/changes/<id>/cut.halt`, else the failed check or worker exit, kept in its queue entry. No rescue SHALL run. `status`
SHALL print `<id> · cut` for a queued cut and `<id> · cut-halted — <line>` for a halted one, and `report` SHALL print its halt
line. A run's start SHALL log each halted cut as a halt and take it into no thread. `conduct.py rejoin <id>` naming a queued cut
SHALL clear its halt under the queue lock, then request it from the live run, or start a run when none is live; the run SHALL
then drop the cut's branch and worktree, when its branch holds no change, and cut again from the brief.

#### Scenario: A cutter halts
- **WHEN** the cutter writes `cut.halt` and commits nothing
- **THEN** the run logs `<id> · halt — cut-halted — <its line>`, runs no rescue, and `status` prints `<id> · cut-halted — <its line>`

#### Scenario: A re-plan and a rejoin
- **WHEN** the person re-plans the brief and runs `conduct.py rejoin <id>`
- **THEN** the cut's half-done branch is dropped, the brief is cut again, and a cut that passes goes into `build`

### Requirement: An unattended cut decides by the brief's switch

`skills/mf-cut-change/SKILL.md` SHALL take `unattended=yes`, set by the cut station alone. Unattended, the cut SHALL hold no
awake hold, start in the worktree the conductor made with its own reservation standing, and never wait for the person. Where
the brief's `## For the cut` item for the change says `decide: recommended`, a moved fact that fails and a plan-review doubt
that changes a settled decision or survives the second review SHALL take the recommended option, and the cut SHALL add a row
`| C<n> | decided by the cutter: … | <reason> |` to the brief's `## Decisions`. A `## Dependencies` that is not `None.`, a
self-check item the cut cannot meet, a doubt with no clear recommendation and a `debt:` id not found SHALL always halt, and
without the switch every doubt SHALL halt. A halt SHALL write one line to `.minions/changes/<id>/cut.halt` and commit nothing.
After its commit, the cut SHALL write `.minions/changes/<id>/models.toml` from the brief's models, with
`decide = "recommended"` when the brief says so, and add `Cut <YYYY-MM-DD> as <id> at <sha>.` after the brief's `## For the cut`
list; it SHALL write nothing else outside the change and the run directory.

#### Scenario: A doubt with a recommendation under the switch
- **WHEN** an unattended cut's plan review raises a doubt that changes a settled decision, with a clear recommendation, and
  the brief says `decide: recommended`
- **THEN** the cut takes it, adds a `decided by the cutter` row to the brief, and commits

#### Scenario: A dependency
- **WHEN** an unattended cut's `## Dependencies` is not `None.`
- **THEN** it writes `cut.halt` and commits nothing, whatever the switch

### Requirement: The cut checks the brief's `At` value before any command takes it

The cut SHALL read every fact as a moved fact when the brief's `At` value is not 7 to 40 lowercase hex digits, running no
command with it. Else it SHALL run `git rev-parse --verify --quiet '<sha>^{commit}'`, and diff from the full sha that prints.

#### Scenario: A value that is not a sha
- **WHEN** a brief reads `At --output=x, 2026-11-05.`
- **THEN** the cut runs no git command with the value, and reads every fact as moved

## MODIFIED Requirements

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
a grant landing after the rescue's `finish`, included. Any other taken version
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

### Requirement: A cut reserves its id against every open version branch

`skills/mf-cut-change/SKILL.md` SHALL take a change id only when its number is higher than every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch and on every branch named by a change id and not merged
into it, and than every reservation in `.minions/cuts/`; an unattended cut SHALL instead find its own reservation there. It
SHALL take `bump=minor|patch`, write `bump:` into `proposal.md`'s frontmatter, and assign no number.

#### Scenario: Two cuts while one change is open
- **WHEN** a version branch holding change `0040-x` is not yet merged, and a second cut is asked for id `0040-y`
- **THEN** the cut halts: the id is taken by an open branch

#### Scenario: A cut by hand beside a queued cut
- **WHEN** `.minions/cuts/0041-q` stands, and a cut by hand is asked for id `0041-y`
- **THEN** the cut halts: the id is reserved

### Requirement: The cut commits without waiting, unless it adds a dependency

`skills/mf-cut-change/SKILL.md` SHALL commit the change once its self-check passes, without waiting for the human.
It SHALL wait for the human's OK before the commit only when `## Dependencies` is not `None.`, when a
self-check item cannot be met, or when the plan review leaves a doubt to the person; an unattended cut SHALL halt there
instead, committing nothing. An edit after the commit SHALL be a further commit on the branch.

#### Scenario: The cut's show step commits without waiting
- **WHEN** the self-check passes, `## Dependencies` is `None.`, and the plan review leaves no doubt to the person
- **THEN** `mf-cut-change` shows the change and commits without waiting

#### Scenario: A dependency, or an unmet item
- **WHEN** `## Dependencies` is not `None.`, or a self-check item cannot be met
- **THEN** the cut waits for the human's OK before committing
- **AND WHEN** the cut is unattended
- **THEN** it halts in `cut.halt` and commits nothing

#### Scenario: A plan-review doubt left to the person
- **WHEN** the plan review leaves a doubt to the person
- **THEN** the cut waits for the human's OK before committing

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
It SHALL write the suggestion to `.minions/changes/<change-id>/models.toml`, a table per station, as well as show it, and
SHALL never write it into the change. When the brief's `## For the cut` item names models for the change, the cut SHALL write
those instead, as the person's choice made at the plan's close. Authentication and provider configuration SHALL remain the
operator's responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

#### Scenario: The cut records its suggestion
- **WHEN** the cut commits a change
- **THEN** `.minions/changes/<change-id>/models.toml` holds a `build`, a `converge` and a `release` table, each with its
  `model`, and nothing under `openspec/changes/<change-id>/` names a model

#### Scenario: The brief names the models
- **WHEN** the brief's `## For the cut` item for the change names a model and effort per station
- **THEN** `.minions/changes/<change-id>/models.toml` holds exactly those

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming them when both files stand, or when beside the old file the old lock is a file or younger than
ten minutes; with no old file, no old lock halts. An old file that is a link SHALL halt, naming it, and the move SHALL NOT
follow it. The move SHALL hold `.minions/debt.lock`, created with `mkdir`, halting naming it when it is held, and SHALL NOT
replace a `debt.md`. Everything about one change SHALL live in `.minions/changes/<change-id>/` — its review, security and status
log files, its diff patch, its models file, the cutter's `cut.halt`, integrate's notes, build's marks, rescue's diagnosis, release's `held`, its gate-check
export and its worker logs — each script finding it through one `_change_dir(primary, id)`; `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/`, `cuts/` and `debt.md` stay generic. A run SHALL move an old layout's files into it at its start, under its claim,
before any worker, idempotently, leaving every file it does not name; a link at `changes/`, `changes/<change-id>/` or an old file
SHALL halt, naming it, and so SHALL an old file beside its new one. `integrate.py`, `gate_check.py`, `run.py`, `conduct.py grant`, and a
hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`, finding a file of its change at its old path, SHALL halt, naming
`/mf-ship` to move it, before writing a file at a new path;
`conduct.py status` and `report` SHALL name such a change `old layout`, reading no stage; `review_metrics.py` SHALL read both
layouts.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/debt.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

#### Scenario: A dead worker left the lock
- **WHEN** a run starts and `.minions/debt.lock` is older than ten minutes
- **THEN** the run removes it and logs the removal before its first worker
- **AND WHEN** the lock is younger
- **THEN** the run leaves it

#### Scenario: A run moves an old backlog
- **WHEN** a run starts beside a `.minions/backlog.md` and no `.minions/debt.md`
- **THEN** it moves the file, removes any stale `backlog.lock`, logs both, and a second start moves nothing
- **AND WHEN** both files stand, the old file is a link, or beside it a `backlog.lock` that is a file or younger than ten
  minutes, or a `debt.lock` younger than ten minutes
- **THEN** the run halts, naming them, and starts no worker
- **AND WHEN** no old file stands beside a young `backlog.lock`, or a file there
- **THEN** the run goes on

#### Scenario: A run moves an old layout
- **WHEN** a run starts beside `.minions/findings/<id>_review.md`, `models/<id>.toml`, `build/<id>.done` and a stray `findings/notes.txt`
- **THEN** each moves into `.minions/changes/<id>/`, the stray stays, the version's stage reads as before, and a second start moves nothing

#### Scenario: A hand-run release on an old layout
- **WHEN** `mf-release` runs by hand for a change whose findings sit in `.minions/findings/`
- **THEN** it halts, naming `/mf-ship`, and releases nothing
