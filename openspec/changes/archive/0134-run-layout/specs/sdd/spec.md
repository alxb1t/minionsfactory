## MODIFIED Requirements

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository, the parent taken by `primary_of` and the join by `run_dir` of the shared home, `skills/mflib/layout.py`. Each script SHALL keep its own git call, its guard and its error text. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after ten minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming them when both files stand, or when beside the old file the old lock is a file or younger than
ten minutes; with no old file, no old lock halts. An old file that is a link SHALL halt, naming it, and the move SHALL NOT
follow it. The move SHALL hold `.minions/debt.lock`, created with `mkdir`, halting naming it when it is held, and naming it a
file, not a lock, when a file or a link stands there; it SHALL NOT replace a `debt.md`. Everything about one change SHALL live in `.minions/changes/<change-id>/` — its conformance, adversarial and status
log files, its diff patch, its models file, the cutter's `cut.halt`, integrate's notes, build's marks, rescue's diagnosis, release's `held`, its gate-check
export and its worker logs — each script finding it through `change_dir(primary, id)` of the shared home; `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/`, `cuts/` and `debt.md` stay generic, and the shared home SHALL name each of those a second script spells. A run SHALL move an old layout's files into it at its start, under its claim,
before any worker, idempotently, leaving every file it does not name; a link at `changes/`, `changes/<change-id>/` or an old file
SHALL halt, naming it, and so SHALL an old file beside its new one. The old layout SHALL be one table of the shared home, holding a change folder's old `review.md` and `security.md` and an old worker log among its entries. `integrate.py`, `gate_check.py`, `run.py`, `conduct.py grant`, and a
hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`, finding a file of its change at one of the table's old paths, SHALL halt, naming `/mf-ship` to move it and the first of the change's old paths in sorted order, before writing a file at a new path;
`conduct.py status` and `report` SHALL name such a change `old layout`, reading no stage; `review_metrics.py` SHALL read both
layouts.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: A worktree and the primary give one run directory
- **WHEN** a script that asks git for the common directory runs from a linked worktree and from the primary
- **THEN** both give the primary's `.minions/`, and the change folder is `.minions/changes/<change-id>/` under it

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/debt.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

#### Scenario: A release waits for the lock
- **WHEN** the release reaches the debt write while another holds `.minions/debt.lock` for less than ten minutes
- **THEN** it waits, writes once the lock is free, and halts naming the lock only after ten minutes of waiting

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
- **AND WHEN** beside the old file `.minions/debt.lock` is a plain file
- **THEN** the run halts, naming `.minions/debt.lock` a file, not a lock, and starts no worker
- **AND WHEN** no old file stands beside a young `backlog.lock`, or a file there
- **THEN** the run goes on

#### Scenario: A run moves an old layout
- **WHEN** a run starts beside `.minions/findings/<id>_review.md`, `models/<id>.toml`, `build/<id>.done` and a stray `findings/notes.txt`
- **THEN** each moves into `.minions/changes/<id>/`, the findings file as `conformance.md`, the stray stays, the version's stage
  reads as before, and a second start moves nothing

#### Scenario: A hand-run release on an old layout
- **WHEN** `mf-release` runs by hand for a change whose findings sit in `.minions/findings/`
- **THEN** it halts, naming `/mf-ship`, and releases nothing

#### Scenario: Every station halts on one table
- **WHEN** a change's old worker log or old `review.md` stands, and `gate_check.py`, `integrate.py`, converge or `run.py` runs by hand
- **THEN** each halts, naming the same file, the first of the change's old paths in sorted order, and `/mf-ship`

### Requirement: A run moves the old findings files to the checkers' names

At its start, under its claim, before any worker, `conduct.py run` SHALL move each `.minions/changes/<change-id>/review.md` to
`conformance.md` and each `security.md` to `adversarial.md`, and an old layout's `.minions/findings/<change-id>_review.md`  and
`_security.md` straight to the new names, by the old-layout move's rules: a link at an old file or its folder, an old file
beside its new one, or two old files naming one new path SHALL halt with nothing moved, and a second start SHALL move nothing.
`gate_check.py`, `integrate.py`, `run.py`, `conduct.py grant`, and a hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`,
finding a change's `review.md` or `security.md` in its folder, SHALL halt naming `/mf-ship`; `conduct.py status` and `report`
SHALL name such a change `old layout`. A models file's `[converge.review]` and `[converge.security]` SHALL be read
as `[converge.conformance]` and `[converge.adversarial]` when the new table is absent.

#### Scenario: A run moves the old names
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `security.md`
- **THEN** they move to `conformance.md` and `adversarial.md`, the version's stage reads as before, and a second start moves
  nothing

#### Scenario: Both names stand
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `conformance.md`
- **THEN** the run halts, naming both, and moves nothing

#### Scenario: A hand-run converge on the old names
- **WHEN** `mf-converge` runs by hand for a change whose folder holds `review.md`
- **THEN** it halts, naming the file and `/mf-ship`, and writes no status log

#### Scenario: A metrics read on the old names
- **WHEN** `scripts/metrics/run.py` reads a change whose folder holds `review.md` or `security.md`
- **THEN** it halts, naming the file and `/mf-ship`, as every station does

#### Scenario: An old worker table
- **WHEN** a version's models file holds `[converge.review]` and no `[converge.conformance]`
- **THEN** conformance's worker takes `[converge.review]`'s model and effort

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or `.mf-ship-origin`, or start with `.minions/`, unless the test lists the file and the name. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands and state paths SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

#### Scenario: A load the map does not declare
- **WHEN** a script names a file of another station that its row in `docs/modules.md` does not list
- **THEN** `tests/test_structure.py` fails naming both files, and the gate is red

#### Scenario: A station loads a station
- **WHEN** a station's script names a script of another station and the pair is on no exception list
- **THEN** the loads rule fails naming the pair

#### Scenario: A private name crosses a file
- **WHEN** a script reads `_name` from a file it names and the pair is on no exception list
- **THEN** the names rule fails naming the file and the name

#### Scenario: A cycle
- **WHEN** two scripts name each other and the cycle is on no exception list
- **THEN** the cycles rule fails naming the files of the cycle

#### Scenario: An OS command outside its files
- **WHEN** a script outside the listed files and the port names `caffeinate` or `bwrap`
- **THEN** the OS-command rule fails naming the file and the command
- **AND WHEN** the port names it
- **THEN** the rule passes

#### Scenario: A state path joined outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant equal to `.minions`, or one that starts with `.minions/`, and the file is on no exception list
- **THEN** the state-path rule fails naming the file and the name
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: A load of the home with no seed
- **WHEN** a script under `skills/` imports `mflib` and the statement before that import is not the seed line
- **THEN** the seed rule fails naming the script

#### Scenario: A load of the home from scripts with no seed
- **WHEN** a script under `scripts/` imports `mflib` and no seed line of its depth stands before the import
- **THEN** the seed rule fails naming the script

#### Scenario: A file on no surface
- **WHEN** a Python file under `skills/` matches no glob of the threat model's surfaces
- **THEN** the surfaces rule fails naming the file

#### Scenario: A file with no row
- **WHEN** a Python file under `skills/` has no row in `docs/modules.md`
- **THEN** the map rule fails naming the file
- **AND WHEN** a row names a file that is gone
- **THEN** the map rule fails naming the row

#### Scenario: A stale exception
- **WHEN** a listed exception no longer exists in the tree
- **THEN** the rule that lists it fails naming the exception, so a list only shrinks
