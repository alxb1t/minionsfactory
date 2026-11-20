## ADDED Requirements

### Requirement: One module writes and parses the debt file

`skills/mflib/debtfile.py` SHALL be the one writer and parser of `.minions/debt.md`: its read, a card's id, extent and count, the file and unfile of cards, the spoiled card's text, its lock, the patch's paths and the match of a card to them, the page of `debt-cards.md`, and the clear of a paid card. `converge.py`, `cut_context.py` and `conduct.py` SHALL read and write the debt through it, and `debt_match.py` SHALL be a command over it with its arguments, output and exits as they were. The module SHALL name no state path: its callers find the file and its lock through `skills/mflib/layout.py`.

A debt card SHALL be a title line `- **<4 digits>·<id> — <title>**` and the indented lines after it, a blank line not ending it, and a count SHALL be of the file or of the cards under one heading. A heading SHALL be `## <change>` as the writer writes it, trailing blanks forgiven on the read, and a section SHALL end at the next `## ` line alone; the writer's own lookup of a heading SHALL be a read. Every reader SHALL follow no link and replace a byte that is not UTF-8, a link SHALL halt it, and a missing file SHALL read as no card.

The lock SHALL be one function of the module: it SHALL make `.minions/debt.lock` by `mkdir`, wait the caller's seconds by five and raise when it is still held, write its holder's token into the lock, and renew the lock's time after each **Still true?** command. Its release SHALL remove only a lock that holds that token, and a lock gone or another's SHALL be no error. The break of a stale lock SHALL go through the module and remove the token before the folder.

#### Scenario: A heading with trailing blanks
- **WHEN** the debt holds `## 0139-debt` followed by trailing blanks and converge files a card under that change
- **THEN** the card goes under that heading, and no second heading is written

#### Scenario: A card runs through a blank line
- **WHEN** a debt card's **What it affects** follows a blank line after its title's field lines
- **THEN** every reader reads it as the card's own

#### Scenario: A title with no qualified id
- **WHEN** the debt holds a line `- **R1 — a title**`
- **THEN** no reader counts it as a card

#### Scenario: A debt that is a link
- **WHEN** `.minions/debt.md` is a link
- **THEN** each reader refuses it, and the debt write and the freeze halt naming it

#### Scenario: A lock another holder made
- **WHEN** a holder's lock was broken as stale and a second holder took it, and the first holder releases
- **THEN** the second holder's lock stands, and the first release raises no error

#### Scenario: A live hold past ten minutes
- **WHEN** a **Still true?** command runs past ten minutes and the holder renews the lock after it
- **THEN** a run's start finds the lock younger than ten minutes and leaves it

## MODIFIED Requirements

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository, the parent taken by `primary_of` and the join by `run_dir` of the shared home, `skills/mflib/layout.py`. Each script SHALL keep its own git call, its guard and its error text. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after ten minutes of waiting and naming the lock; converge SHALL take and release the lock through `skills/mflib/debtfile.py`, whose lock knows its holder. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming them when both files stand, or when beside the old file the old lock is a file or younger than
ten minutes; with no old file, no old lock halts. An old file that is a link, or is no regular file, SHALL halt, naming it, and the move SHALL NOT
follow it. The move SHALL hold `.minions/debt.lock`, created with `mkdir`, halting at once, naming it, when it is held, and naming it a
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

#### Scenario: An old backlog that is no file
- **WHEN** a run starts beside a `.minions/backlog.md` that is a dangling link or a folder
- **THEN** the run halts, naming `.minions/backlog.md`, and starts no worker

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

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/scripts/converge.py` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change, through `skills/mflib/debtfile.py` and the folder it opens from the primary — save an amend card that halts, as *The
converge fixer leaves the plan to the person* says; an amend card whose id an answered `amend needed` halt logged
since the newest `round 1 · start` line named, or whose qualified id already stands in the debt, SHALL go on as every
other card. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, and fix them. When round 1 of a run that is no
catch-up run leaves a blocking card open, its fix pass SHALL take those same cards with the blocking ones — the **round-1
pickup** — and round 2's verify round SHALL judge them all; pickup SHALL then not run again in that run. One fresh worker, the
**pickup check**, SHALL verify a pickup's fix at `medium` effort, given both findings files' open cards and the fix's own diff: on
adversarial's table when a picked card is adversarial's, else on conformance's. A pickup whose fixer commits nothing SHALL get
no pickup check. The pickup check SHALL be no round: it SHALL set both
findings files' `head:` and leave their
`round:` as it stands, and a blocking card it leaves open SHALL go to a fix and a verify round counted against the cap. It
SHALL NOT name a per-version debt file. It SHALL delete a debt card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one debt file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and checks the fix by one pickup check

#### Scenario: A pickup check
- **WHEN** round 2 reads both files clean, and pickup picks a conformance `drift` card and an adversarial `medium` card
- **THEN** one fresh worker, on adversarial's table at `medium` effort, judges both cards against the pickup's diff
- **AND** both files' `head:` is `HEAD`, their `round:` stays 2, and no round 3 runs
- **AND WHEN** the pickup check leaves a blocking card open
- **THEN** converge sends it to a fix, and verifies in round 3

#### Scenario: Converge writes the debt
- **WHEN** the loop ends clean with non-blocking cards still not `verified`
- **THEN** converge writes each one whose **Still true?** check still shows the defect, and whose id is not yet in
  the debt, to `.minions/debt.md` under its change's heading, and to no per-version file
- **AND** it names each moot card, whose check shows the defect gone, in its report
- **AND** it deletes an older card only when a verified repeat of it fixed the defect and its **Still true?**
  check shows the defect gone

#### Scenario: A change's heading with trailing blanks
- **WHEN** the debt holds the change's heading followed by trailing blanks and converge writes a card for that change
- **THEN** the card goes under that heading and no second heading is written

#### Scenario: An amend card after its amend
- **WHEN** Step 9 finds an amend card whose **Still true?** check still shows the defect, and an answered `amend needed` halt
  logged since the newest `round 1 · start` line named its id, or its qualified id already stands in the debt
- **THEN** converge writes it to the debt unless its id is there already, and halts nothing
- **AND WHEN** a catch-up run's Step 9 finds an amend card still true that no answered halt logged since the newest
  `round 1 · start` line named and the debt does not hold
- **THEN** it halts `amend needed — <its id>`

#### Scenario: A round-1 pickup
- **WHEN** round 1 leaves one blocking card open and two non-blocking cards sized `one line`
- **THEN** one fix pass takes all three, and round 2's verify round judges all three
- **AND WHEN** round 2 reads both files clean
- **THEN** no pickup runs, and converge goes on to the debt

#### Scenario: A pickup that commits nothing
- **WHEN** the pickup's fixer sets every picked card `wontfix` and commits nothing
- **THEN** no pickup check runs, and converge goes on to the debt

### Requirement: Converge bundles the debt cards on the diff's files

At each freeze, after `bundle.py`, converge SHALL run `skills/mf-converge/scripts/debt_match.py`, a command over `skills/mflib/debtfile.py`, which writes
`.minions/changes/<change-id>/debt-cards.md` whole: a `# Debt cards on the diff's files` title, then each card of
`.minions/debt.md`, in full, whose **What it affects** field names in backticks a path the frozen patch changes, a `:<line>`
suffix dropped; `None.` when no card matches, or no debt file stands. No worker SHALL read `.minions/debt.md`; the repeat
rule SHALL match the cards `debt-cards.md` holds. `debt_match.py` SHALL read the debt as the module reads it, following no link and replacing a byte that is not UTF-8, SHALL refuse to write through a link, and SHALL exit 2,
writing nothing, when the debt file is a link or cannot be opened, or the patch cannot be read; a freeze that gets a non-zero exit from it SHALL halt, naming `debt_match.py`, and SHALL NOT write an empty `debt-cards.md`.

#### Scenario: A card on a file the diff touches
- **WHEN** the debt holds a card whose **What it affects** names `` `src/a.py:12` `` and another naming `` `src/b.py` ``, and the
  patch changes `src/a.py` alone
- **THEN** `debt-cards.md` holds the first card in full and not the second

#### Scenario: No debt file
- **WHEN** no `.minions/debt.md` stands
- **THEN** `debt-cards.md` reads `None.` under its title

#### Scenario: A bundle that is a link
- **WHEN** `debt-cards.md`, the debt cards beside the bundle, is a link
- **THEN** `debt_match.py` exits 2 naming it, and the link's target is unchanged

#### Scenario: A debt that is a link
- **WHEN** `.minions/debt.md` is a link
- **THEN** `debt_match.py` exits 2 naming it, and the freeze halts naming `debt_match.py`, with no empty `debt-cards.md`

#### Scenario: A bad byte in the debt
- **WHEN** `.minions/debt.md` holds a byte that is not UTF-8
- **THEN** `debt_match.py` replaces it, matches the cards and exits 0

### Requirement: Converge's conductor is a script

`skills/mf-converge/scripts/converge.py` SHALL conduct converge: its preconditions, the freeze, the dispatch of each checker, the
fixer and each verify worker, the read of each findings file's frontmatter and cards, the loop to its cap of three rounds, the
pickup, a granted round, a catch-up round with its by-rule write, the resume from the status log, the debt write and the report.
`conduct.py` SHALL load it in-process, as it loads `integrate.py`, and call it in the version's thread; `conduct.py converge
<change-id> [conformance=<model>/<effort>] [adversarial=<model>/<effort>] [fix=<model>/<effort>] [grant=yes]` SHALL run it by hand.
No converge worker that conducts SHALL start: the workers are the checkers, the fixer and the verify workers, each a fresh agent
process the run starts through its own worker and checker calls, with a prompt the script fills from the `## Prompt` section of the
role's reference. The script SHALL run the gate, `gate_check.py`, `plan_check.py` and each `Verify:` and **Still true?** command
under `conduct.py`'s sandbox runner, never bare. It SHALL read a findings file's frontmatter keys `files`, `commits`, `passes` and
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them, or with a card
whose id is outside `R<n>` and `S<n>`, SHALL be malformed. `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py`
and `skip_stub.py` SHALL read a findings file's cards and frontmatter through `skills/mflib/findings.py`, a card's title a line that
starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word, as `- **stale-claim** — ran.`,
is no card; `skills/mflib/debtfile.py` SHALL read a debt card's title, a line that starts `- **<4 digits>·<id> — ` with an id holding no `*`, and `debt_match.py` and `cut_context.py` SHALL read it through the module. The status log's events and their text
SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `replay` exiting 2 SHALL send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red, a security card and a debt the freeze may not read SHALL still halt.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: A card titled outside the contract's ids
- **WHEN** a checker's findings file holds a card titled `- **S-1 — a title**`
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`

#### Scenario: A bold-led bullet that is no card
- **WHEN** a findings file holds `- **stale-claim** — ran.` under a `## Passes` heading and `- **Spec** — none.` in its Summary, beside cards that carry their `Amend:` fields
- **THEN** the file is read with those cards alone, and no rewrite worker is started for it
- **AND** `open_cards.py` writes those cards alone

#### Scenario: A worker exits 1
- **WHEN** a checker exits 1 or leaves no findings file
- **THEN** one fresh worker is started for that role, and a second failure halts the version, naming the role

#### Scenario: A prose check
- **WHEN** a non-blocking card's **Still true?** holds no command in backticks
- **THEN** the card goes to the debt unchecked, and no command runs for it

#### Scenario: A check command writes outside the trees
- **WHEN** a card's **Still true?** command tries to write a file outside the worktrees
- **THEN** the sandbox denies it, the card goes to the debt unchecked, and nothing is written outside

#### Scenario: A debt the freeze may not read
- **WHEN** `.minions/debt.md` is a link at a freeze
- **THEN** converge halts naming `debt_match.py`, and writes no empty `debt-cards.md`

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check
