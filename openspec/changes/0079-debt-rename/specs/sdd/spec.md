## ADDED Requirements

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, fix them, and verify them in a normal
round. It SHALL NOT name a per-version debt file. It SHALL delete a debt card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one debt file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and verifies them in a normal round

#### Scenario: Converge writes the debt
- **WHEN** the loop ends clean with non-blocking cards still not `verified`
- **THEN** converge writes each one whose **Still true?** check still shows the defect, and whose id is not yet in
  the debt, to `.minions/debt.md` under its change's heading, and to no per-version file
- **AND** it names each moot card, whose check shows the defect gone, in its report
- **AND** it deletes an older card only when a verified repeat of it fixed the defect and its **Still true?**
  check shows the defect gone

### Requirement: The release does not read the debt

`skills/mf-release/SKILL.md` SHALL NOT hold a release on deferred work. It SHALL name no per-version debt file.
A paydown change lists the card ids it closes under the `debt:` key of its `proposal.md` frontmatter, an older proposal's `backlog:` read the same:
`skills/mf-cut-change/SKILL.md` SHALL write that key, and `mf-release` SHALL delete exactly those cards from
`.minions/debt.md` after the fold.

#### Scenario: The release names no per-version debt, and the paydown key is shared
- **WHEN** `mf-release` runs while `.minions/debt.md` holds open cards the change does not list
- **THEN** it releases without reading or holding on them

#### Scenario: A paydown change is released
- **WHEN** the change's `proposal.md` lists card ids under `debt:`, or an older one's `backlog:`
- **THEN** `mf-release` deletes exactly those cards from `.minions/debt.md` after the fold

## MODIFIED Requirements

### Requirement: A repeated finding escalates

Each station SHALL read `.minions/debt.md`. A finding that repeats a debt card SHALL name that card's id in its
**Related** field as `repeat of <id>`, and SHALL go up one level: security by one step, a review `nit` or `drift` to
`blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** a station's finding describes a defect already carded in `.minions/debt.md`
- **THEN** its **Related** field names `repeat of <id>`
- **AND** it goes up one level: security by one step, a review `nit` or `drift` to `blocking`

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`, the executor, model and effort from the version's models file, else the run's, and `tokens` the
worker's figure or `unavailable`. The log SHALL NOT be a findings file: no station writes it and no
release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, its time taken from `date`
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's review and security files are read
- **THEN** the log holds one `verdicts` line for each role, each naming that role's executor, model and effort

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

### Requirement: The plan station reads the target without moving it

`skills/mf-plan/SKILL.md` SHALL read the target repository only at a named commit of its default branch, through
`git show`, `git grep`, `git log`, `git ls-tree` and `git diff`, and SHALL read the working tree only for the
gitignored `.minions/debt.md`, or an old `.minions/backlog.md` a run has not moved. It SHALL NOT switch, check out, stash, reset, commit, branch or edit in the target,
nor run its gate or a metric collection. A helper it dispatches for facts SHALL be held to the same rule, and SHALL
return conclusions citing `path:line` at that commit.

#### Scenario: A build runs in the same checkout
- **WHEN** `mf-plan` gathers facts while another session builds a change on its version branch in that checkout
- **THEN** the checkout's branch, index and working tree are as they were before
- **AND** every fact cites `path:line` at the named commit of the default branch

### Requirement: The plan station checks the line's rules before its first round

Before its first round, `mf-plan` SHALL report as facts: the debt cards whose trigger the version fires, proposed
for `debt:`; a recommendation to pay down first when the debt holds more than ten open cards; whether
the version's bump fits the repository's rule for a patch; the decisions in force the version touches, naming any overturn; a split
when one diff would be too large for review; re-measured facts when continuing a brief written against an older
commit; and, when the target holds `metrics/catalogue.toml`, the metrics past their watch in the latest tracked data
file.

#### Scenario: A version planned in a repo with metrics
- **WHEN** the target has a catalogue and a tracked data file with a metric past its watch
- **THEN** the first round lists that metric as a fact, read from the data file, with no collection run

#### Scenario: A brief continued against a newer commit
- **WHEN** `from=` names a brief whose facts cite an older commit than the default branch's
- **THEN** the station re-measures those facts before its first round

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming both when both files stand or the old lock is younger than ten minutes. The move SHALL hold
`.minions/debt.lock`, created with `mkdir`, halting naming it when it is held, and SHALL NOT replace a `debt.md`.

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
- **AND WHEN** both files stand, or a `backlog.lock` or `debt.lock` younger than ten minutes
- **THEN** the run halts, naming them, and starts no worker

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
`.minions/debt.lock`, or an older `.minions/backlog.lock`, a release whose
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
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/integrate/<change-id>.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: Converge continues an unfinished run

When the newest run of a status log ends on neither `halt` nor `done`, `conduct.py`'s stage SHALL be `converge`, whatever
the findings files say, and `skills/mf-converge/SKILL.md` SHALL continue that run from its latest event: no new `## Run`
heading, the round unchanged, and a pickup whose fix was never committed sent again. A run whose top line is a `halt` naming
`.minions/debt.lock`, or an older `.minions/backlog.lock`, SHALL be continued the same way, at Step 9, when both findings files are clean at `HEAD`.

#### Scenario: A usage limit stops converge mid-pickup
- **WHEN** a run's latest event is `pickup` and its findings files are clean at `HEAD`
- **THEN** a re-run of `mf-ship` spawns converge, not the release
- **AND** the same run sends the pickup, verifies, writes the debt and ends on `done`, repeating no judged round

#### Scenario: A converge halted on the backlog lock
- **WHEN** a run's top line is a `halt` naming `.minions/debt.lock`, and both findings files are clean at `HEAD`
- **THEN** a re-run of `mf-ship` spawns converge, which writes the debt and ends on `done` in the same run, with no new round
- **AND WHEN** either findings file is not clean at `HEAD`
- **THEN** converge halts, naming it

### Requirement: A person can grant one more round

`/mf-ship grant <change-id>` SHALL work only on a version whose status log halted at the cap. It SHALL record the grant and
start a run, or, with a run live, write that version's rejoin request. A refusal SHALL name the stage and the command to
run instead: `/mf-ship`. With a run live, it SHALL refuse while the newest run log holds that version's rescue spawned and not
finished, naming the stage and the rescue, and write nothing: a grant written then is the rescue's answer. A grant landing
after the rescue's `finish` and before the run reads its outcome SHALL count as the rescue's answer too, held for the run and
left on disk for a re-run. `conduct.py` SHALL
spend the grant when it spawns converge, with `grant=yes`. `skills/mf-converge/SKILL.md`
SHALL open a run marked as the grant, send the open blockers to a fixer, verify one round, and on clean write the rest to
the debt with no pickup; a blocker left SHALL halt. The cap SHALL stay three.

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

### Requirement: A converge halt answered by the person converges afresh

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an older backlog lock's,
SHALL be void when its head is both findings files' `head:` and `HEAD` is past it, a descendant that is not it: `conduct.py`'s
stage SHALL be `converge`, and its converge check SHALL not read the old halt. A halt in a catch-up run whose findings files are
both still clean, a Step 1.6 `verify: halt`, and a fix pass's `amend needed` halt SHALL also be void when `HEAD` is past its head and every commit since is the person's `docs(<id>): amend the
change directory`, one parent each, touching only `openspec/changes/<id>/`. Any other halt naming no head, one past the judged head,
and one whose head is no ancestor of `HEAD` SHALL stand. `skills/mf-converge/SKILL.md`, finding its newest run's top line a void
catch-up halt with both files clean, SHALL run the catch-up round again; finding any other void halt, it SHALL open a run marked `· amended`, and
converge from round 1 over the whole change, the findings files restarting at `round: 1`. A run marked `· grant` that resumes
SHALL stay a granted round.

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a new run marked `· amended`, from round 1, with no grant

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, or in a catch-up run, so its head is not the findings files' `head:`, and a
  commit other than the person's amend follows
- **THEN** its stage stays `converge-halted`, and no `· amended` run opens

#### Scenario: The person's amend answers a catch-up halt
- **WHEN** a catch-up round halts at Step 1.6 on a `Verify:` changed since the cut, and the person commits `docs(<id>): amend the
  change directory`
- **THEN** its stage is `converge`, and the next run's catch-up round counts the merge and the amend as its own

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

## REMOVED Requirements

### Requirement: Converge keeps deferred work in one repository backlog

**Reason**: the word leaves the record — every card is a deferred check-loop finding, technical debt.
**Migration**: *Converge keeps deferred work in one repository debt file* holds the same rule, in `.minions/debt.md`.

### Requirement: The release does not read the backlog

**Reason**: the word leaves the record.
**Migration**: *The release does not read the debt* holds the same rule; the `debt:` key, or an older proposal's `backlog:`.
