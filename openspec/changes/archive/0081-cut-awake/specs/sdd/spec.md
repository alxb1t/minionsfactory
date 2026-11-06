## ADDED Requirements

### Requirement: A cut run by hand holds the machine awake

The cut SHALL run `skills/mf-cut-change/scripts/awake.py start <change-id>` at the head of its Step 1, and `awake.py stop
<change-id>` at every halt from Step 1 on and at Step 11's close-out. `start` SHALL start `caffeinate -is -t 7200 -w <host pid>`,
detached, the host being its nearest ancestor process that is neither a shell nor `uv`, so the hold ends at the stop, the host's
exit or two hours, whichever comes first. It SHALL record the hold's pid in `.minions/awake/<change-id>`, a generic folder of the run directory, and print
`awake: held (2 h at most)`; a hold already recorded for that id is stopped first, and a hold for another id is left alone.
`stop` SHALL kill the recorded pid only while `ps` names it `caffeinate`, and remove the record. With no `caffeinate` on `PATH`,
`start` SHALL print `awake: not held — caffeinate not on PATH`, start nothing and exit 0; the cut SHALL go on whatever `awake.py` prints.
`skills/mf-cut-change/SKILL.md` SHALL say that a closed lid sleeps the Mac whatever the cut holds, unless it is in clamshell mode.

#### Scenario: A cut on a Mac
- **WHEN** the cut starts with `caffeinate` on `PATH`
- **THEN** `awake.py start <change-id>` starts `caffeinate -is -t 7200 -w <host pid>` once, records its pid in
  `.minions/awake/<change-id>`, and prints `awake: held (2 h at most)`

#### Scenario: Two cuts at once
- **WHEN** holds stand for two change ids and one is stopped
- **THEN** its `caffeinate` is killed and its record removed, and the other's stands

#### Scenario: No caffeinate
- **WHEN** no `caffeinate` is on `PATH`
- **THEN** `awake.py start` prints `awake: not held — caffeinate not on PATH`, records nothing and exits 0

## MODIFIED Requirements

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
log files, its diff patch, its models file, integrate's notes, build's marks, rescue's diagnosis, release's `held`, its gate-check
export and its worker logs — each script finding it through one `_change_dir(primary, id)`; `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/` and `debt.md` stay generic. A run SHALL move an old layout's files into it at its start, under its claim,
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
