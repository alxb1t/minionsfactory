## ADDED Requirements

### Requirement: A supervisor answers what the rescue leaves

Under a version's switch, `decide = "recommended"`, when its rescue at a build check halt or a converge halt writes a
diagnosis, the run diagnoses its converge `verify: halt`, or its rescue is spent on the halt — the sub-task rescued before in
the run, or `RESCUES` reached — `conduct.py` SHALL spawn the `mf-supervise` station in that version's thread, with
`decide=recommended`. It SHALL spawn none without the switch; at an integrate halt; at a halt the rescue's answer on disk holds
for a re-run; at a converge halt while `security.md` holds an open card of `critical` or `high` severity, or its `amend needed`
names one; when the rescue's worker failed or its amend was refused; nor when the models file's `[rescue]` table says
`skip = true`. The station SHALL run on the `[supervise]` table's executor, model and effort; on Claude, an absent model SHALL be
`claude-opus-5-5` and an absent effort `high`.

`skills/mf-supervise/SKILL.md` SHALL answer the halt with one `docs(<id>): amend the change directory` commit carrying
`Supervisor: <sub-task or stage>` and `Decided-by: supervisor` trailers, or commit nothing. It MAY edit any file under
`openspec/changes/<id>/`, the spec delta included, tick a sub-task box whose `Verify:` it ran and saw pass, and add work as a new
unticked phase after the last. It SHALL never edit code, a test or any other path, take a security card of `critical` or `high`
severity, approve a gate makefile, accept a risk the threat model does not accept, untick a box, release, merge or push.

`conduct.py` SHALL take the commit only when it is the one commit past the station's start, with one parent, the amend's
subject, a `Supervisor:` trailer, a `Decided-by:` trailer reading `supervisor`, and paths under `openspec/changes/<id>/` alone. It
SHALL then clear the version's halt and its diagnosis, log `supervise — <id>: decided · <sub-task or stage> · <commit>`, and go
on in the same thread, with no restart and no wait for a poll. Any other outcome SHALL halt the version, naming what the station
left; at a converge halt, an answer on disk SHALL then hold the version for a re-run as the rescue's does, the halt reading
`supervisor answered its halt`, and the person's amends alone, none carrying a `Rescue:` or `Supervisor:` trailer, SHALL go on. A
version SHALL get one supervisor try per halt and at most `SUPERVISES = 2` in a run; a halt the supervisor tried before SHALL
name ` · supervised <sub-tasks>`. A grant SHALL be refused while the station runs, as while the rescue runs. `report` SHALL
print `<id> · supervised <sub-task or stage> · <commit>` for each taken amend, the run's closing line and its `done` line SHALL
name ` · supervised <ids>`, and the run's metrics SHALL count them as `supervisor-decided`.

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

## MODIFIED Requirements

### Requirement: A halted version is rescued in its run

When a version halts on its build check, a converge halt — its cap the run does not grant, or `amend needed` among them — or integrate's red gate or note, `conduct.py` SHALL spawn the
`mf-rescue` station in that version's thread, unless its models file's `[rescue]` table says `skip = true`; the station SHALL run on
the `[rescue]` table's executor and model, the `[build]` table's when there is none. `skills/mf-build/SKILL.md` SHALL write
`.minions/changes/<id>/build.halt` on every halt — the sub-task, the stop condition, one line of evidence. `skills/mf-rescue/SKILL.md` SHALL
fix a build halt on a `Verify:` that cannot pass, a reader a deletion missed, a task two readings would build differently, or an
`Verify:` that is not one plain command — a `$(…)`, a shell variable, a loop or a `cd` — and a converge `amend needed` halt with the
amend its cards name — each `wontfix` card's, and each `open` `drift` card's **Fix** — with one `docs(<id>): amend the change directory` commit touching only `openspec/changes/<id>/tasks.md` and `design.md`,
never `design.md`'s decisions table without the version's switch, carrying a `Rescue:` trailer; every other halt it SHALL diagnose in `.minions/changes/<id>/rescue.md`.
An `amend needed` halt naming a security card of `critical` or `high` severity SHALL get a diagnosis alone, whatever the
switch. The rescue SHALL be offered its amend whether the version halted in this run or before it, at the run's start.
`conduct.py` SHALL halt the version when the commit touches any other path, and otherwise clear its halt and go on in the same run, an
`amend needed` halt to a converge run marked `· amended`, or to its catch-up round when both findings files are still clean, where one
Step 7 round judges the rescue's amend. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer and wait for a re-run — save the person's
`docs(<id>): amend the change directory` commits, none carrying a `Rescue:` or `Supervisor:` trailer, which answer an
`amend needed`, `verify: halt` or clean catch-up halt
by amends alone: the version SHALL go on in the run, logged `rescue — <id>: amended · <commit>`. A version SHALL
get at most `RESCUES = 3` rescues in a run, and none for a sub-task it rescued before; a timeout, a usage limit and D47's halts that
need the person SHALL get none. The run SHALL log `rescue — <id>: fixed · <sub-task> · <commit>`, `rescue — <id>: decided ·
<sub-task> · <commit>` or `rescue — <id>: diagnosed · <file>`, and `report` SHALL print each. The rejoin folder and the grants folder SHALL be read and emptied through a directory file
descriptor opened without following a link. A sub-task an amend adds — the rescue's, the supervisor's or the person's — SHALL go
in a new unticked phase after the last, with its `## Progress` line, never under a ticked phase, whose sub-tasks no build reads.

#### Scenario: A check that cannot pass
- **WHEN** a build halts on a `Verify:` whose search matches a line no task touches
- **THEN** the rescue amends `tasks.md`, the run logs `rescue — fixed`, and the version builds on and releases in the same run

#### Scenario: A decision halt
- **WHEN** a build halts on a design premise the code rules out, with no switch
- **THEN** the rescue writes `.minions/changes/<id>/rescue.md`, and the version stays halted, its halt naming the file

#### Scenario: A rescue outside the plan
- **WHEN** a rescue's commit touches a file outside `tasks.md` and `design.md`
- **THEN** the version halts, naming the file

#### Scenario: A rescue at amend needed
- **WHEN** converge halts `amend needed` on a review card whose fix names a `design.md` prose amend, in the run or before it
- **THEN** the rescue commits that amend, and the version converges again in the same run, in a run marked `· amended`
- **AND WHEN** the card is a security card of `high` severity
- **THEN** the rescue diagnoses, and the version stays halted

#### Scenario: A rescue at a drift halt
- **WHEN** converge's Step 9 halts `amend needed` on an `open` `drift` card whose **Fix** names a `design.md` amend, both findings
  files clean, and the version's models file says `decide = "recommended"`
- **THEN** the rescue commits that amend with its `Rescue:` trailer, and the version goes on in the same run through a catch-up
  round whose one Step 7 round reads the amend, with no new round 1, and releases

#### Scenario: An amend lands during a rescue
- **WHEN** the person commits `docs(<id>): amend the change directory` while the rescue of its `amend needed` halt runs
- **THEN** the version goes on in the same run, and the run logs `rescue — <id>: amended`

#### Scenario: A worker's amend is no person's
- **WHEN** an amend of the change directory carrying a `Supervisor:` trailer follows a converge halt's head, and the supervisor's
  check refused it
- **THEN** the version stays halted for the run, as when the rescue answered it

#### Scenario: A rescue that answers its cap
- **WHEN** a rescue at a converge cap writes a grant and a rejoin request
- **THEN** the run starts no further converge round, and logs the version still halted

#### Scenario: The same sub-task again
- **WHEN** a version halts again on a sub-task it was rescued from
- **THEN** no rescue runs, and the halt names both

#### Scenario: A sub-task added after its phase is ticked
- **WHEN** an amend at a converge halt adds a sub-task the build must make, and every phase of `## Progress` is ticked
- **THEN** the amend adds it in a new unticked phase after the last, and the version builds that phase before it converges

#### Scenario: A link at the rejoin folder
- **WHEN** a worker swaps the rejoin folder for a link to another directory after the run lists it
- **THEN** nothing in that directory is deleted

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, with no pickup, unless the
selection is merges and amends only, every merge replays by the fixed rules and no amend carries a `Rescue:` or `Supervisor:`
trailer, when the round is by rule and runs no worker.
**Merges and amends** are merges, and the person's, the rescue's or the supervisor's `docs(<id>): amend the change directory`
commits touching only `openspec/changes/<id>/`. When the selection is merges and amends only, the run SHALL count its own rounds:
one judge round and at most one fix round, then a halt, with `round:` carrying on past three. Any other selection SHALL count
against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup
- **AND WHEN** the selection is merges and amends only, every merge replays by the fixed rules and no amend carries a
  `Rescue:` or `Supervisor:` trailer
- **THEN** the round is by rule: no freeze, no worker, no verify round, and no pickup

#### Scenario: The catch-up round judges a merge-in by what the merge decided
- **WHEN** the range `head..HEAD` holds a merge of the default branch whose conflicts were resolved by hand
- **THEN** the round's patch holds that merge's remerge-diff, not the default branch's changes
- **AND** a merge with no conflicts adds nothing to read, and the gate judges the combined tree

#### Scenario: A catch-up over merges only has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge alone
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap
- **AND WHEN** a blocking finding is still open after its one fix round
- **THEN** it halts with `cap reached`, and the stage reads `converge-halted`

#### Scenario: A catch-up over a merge and the person's amend has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge and the person's amend of the change directory
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap

#### Scenario: A rescue's amend at round 3 has its own count
- **WHEN** the last judged round is 3, Step 9 halted `amend needed`, and the selection is the rescue's amend of the change
  directory, carrying its `Rescue:` trailer
- **THEN** `mf-converge` judges it in one Step 7 round as round 4, with no halt at the cap and no round by rule

#### Scenario: A supervisor's amend has its own count
- **WHEN** the last judged round is 3, Step 9 halted `amend needed`, and the selection is the supervisor's amend of the change
  directory, carrying its `Supervisor:` trailer
- **THEN** `mf-converge` judges it in one Step 7 round as round 4, with no halt at the cap and no round by rule

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3 and the selection holds a commit that is neither a merge nor the person's, the rescue's
  or the supervisor's amend
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: A converge halt answered by the person converges afresh

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an older backlog lock's,
SHALL be void when its head is both findings files' `head:` and `HEAD` is past it, a descendant that is not it: `conduct.py`'s
stage SHALL be `converge`, and its converge check SHALL not read the old halt. A halt in a catch-up run whose findings files are
both still clean, a Step 1.6 `verify: halt`, and a fix pass's or Step 9's `amend needed` halt SHALL also be void when `HEAD` is past its head and every commit since is the person's `docs(<id>): amend the
change directory`, one parent each, touching only `openspec/changes/<id>/`. A **halt before round 1** — a halt other than a
`verify: halt` in a run with no `start` line, not marked `· grant` — SHALL be void when `HEAD` is past its head, by any commit, and SHALL be re-run when
`HEAD` is its head: `conduct.py`'s stage SHALL be `converge` in both, and it SHALL start no rescue for it. A run SHALL re-run a
version once at the same head: one that halts before round 1 again SHALL stay out for the rest of that run, a rejoin logging it
still halted. Any other halt naming no head, one past the judged head,
and one whose head is no ancestor of `HEAD` SHALL stand. `skills/mf-converge/SKILL.md`, finding its newest run's top line a halt
before round 1, SHALL open a plain new run, with no mark, as a fresh invocation does; finding a void
catch-up halt, or a void `amend needed` halt, with both files clean, it SHALL run the catch-up round again, opening no new round 1,
and SHALL judge an amend there carrying a `Rescue:` or `Supervisor:` trailer in one Step 7 round over its diff, passing only a
trailer-less amend by rule;
finding any other void halt, it SHALL open a run marked `· amended`, and
converge from round 1 over the whole change, the findings files restarting at `round: 1`. A run marked `· grant` that resumes
SHALL stay a granted round.

#### Scenario: A gate red before round 1
- **WHEN** converge halts on a red gate before round 1 at head H, writing no `start` line, and the person asks a live run to take
  it back with no new commit
- **THEN** the run takes it back, and converge runs again in a plain new run
- **AND WHEN** it halts before round 1 again in that run
- **THEN** it stays out for the rest of the run, and a rejoin logs it still halted
- **AND WHEN** a commit past H follows
- **THEN** its stage is `converge`

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a new run marked `· amended`, from round 1, with no grant

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the cap is a granted round's, in a run with no `start` line, and `HEAD` is its head
- **THEN** its stage stays `converge-halted`, and it is no halt before round 1

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, or in a catch-up run past its `start` line, so its head is not the findings
  files' `head:`, and a commit other than the person's amend follows
- **THEN** its stage stays `converge-halted`, and no `· amended` run opens

#### Scenario: The person's amend answers a catch-up halt
- **WHEN** a catch-up round halts at Step 1.6 on a `Verify:` changed since the cut, and the person commits `docs(<id>): amend the
  change directory`
- **THEN** its stage is `converge`, and the next run's catch-up round counts the merge and the amend as its own

#### Scenario: The person's amend answers a drift halt
- **WHEN** Step 9 halts `amend needed` with both findings files clean, and the person commits `docs(<id>): amend the change
  directory`
- **THEN** its stage is `converge`, and the next run is a catch-up round that passes the person's trailer-less amend by rule,
  with no new round 1

#### Scenario: The supervisor's amend answers a drift halt
- **WHEN** Step 9 halts `amend needed` with both findings files clean, and the supervisor's amend, carrying its `Supervisor:`
  trailer, is taken
- **THEN** the next run is a catch-up round whose one Step 7 round reads the amend, with no new round 1 and no round by rule

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
a conflicted `CHANGELOG.md` with the `changelog` rule, run the `decisions` rule on every merge, conflicted or clean, run the
`delta` rule, and exit 0 when `delta` names no requirement and the rebuilt tree equals the merge's tree, else 1. Its line SHALL
name each path a rule settled: one git left unmerged, and `docs/decisions.md` when the `decisions` rule renumbered. Its git SHALL
run no hook and fetch no missing object.
It SHALL exit 2, rebuilding nothing, for a commit without two parents or whose second parent the default branch does not hold.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL first run *Catch-up scope*'s ancestry and parent checks, halting when one
fails, then run `replay` for each merge in its selection; when every merge replays and the selection holds nothing else but the
person's amends, none carrying a `Rescue:` or `Supervisor:` trailer, which Step 1's gate and `gate_check.py` judge, it SHALL
write both findings files `head: HEAD` and `verdict: clean` with a `## By rule` section naming each merge's paths and each amend,
log `round N · by rule — clean, <paths>`, dispatch no worker, and count the round within the merges-and-amends count. Any other
selection, one holding the rescue's or the supervisor's amend among them, SHALL take the catch-up round as before.

#### Scenario: A changelog the rule settled
- **WHEN** the integrate merge conflicted in `CHANGELOG.md` alone, settled by `integrate.py changelog`
- **THEN** the catch-up replays it, writes both findings files clean with `## By rule`, dispatches no worker, and the release
  passes its preconditions

#### Scenario: A decision renumbered in a cleanly merged file
- **WHEN** git merged `docs/decisions.md` with no conflict, and the integrate merge's `decisions` rule renumbered the branch's id
- **THEN** replay prints `replay: by rule — docs/decisions.md` and exits 0

#### Scenario: A merge and the person's amend
- **WHEN** the selection is a merge that replays and the person's amend of the change directory, and Step 1 passes
- **THEN** the catch-up writes both findings files clean with `## By rule`, naming the merge and the amend, and dispatches no worker

#### Scenario: A merge and the rescue's amend
- **WHEN** the selection is a merge that replays and the rescue's amend of the change directory, carrying its `Rescue:` trailer
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches review and security over the selection

#### Scenario: A merge and the supervisor's amend
- **WHEN** the selection is a merge that replays and the supervisor's amend of the change directory, carrying its `Supervisor:`
  trailer
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches review and security over the selection

#### Scenario: A merge someone judged
- **WHEN** the merge holds a hunk the integrator resolved as a union, a person's resolution, a test edited, or a requirement
  the delta edits that the default branch changed, the delta changing or removing a line of the default branch's block
- **THEN** replay exits 1, and the catch-up round dispatches review and security as before

#### Scenario: A merge of a commit the default branch does not hold
- **WHEN** the merge's second parent is not an ancestor of the default branch, though git merged it with no conflict
- **THEN** replay exits 2, and the catch-up halts, naming the merge, with no findings file written clean

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue and, under its switch, its
supervisor, and every other version SHALL go on
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
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, an old
`.minions/backlog.md` beside `.minions/debt.md` or a file at `.minions/backlog.lock` or `.minions/debt.lock`, or one that is a
link, or a default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset
time named.

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
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/changes/<change-id>/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/changes/<change-id>/integrate.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: A verify halt is diagnosed by the run

When a version's converge halt is Step 1.6's `verify: halt`, `conduct.py` SHALL write its diagnosis to `.minions/changes/<id>/rescue.md`
itself, from the halt line, through a file opened without following a link, start no rescue worker, and log `rescue — <id>: diagnosed
· <file>`. The diagnosis, and every rescue proposal `skills/mf-rescue/SKILL.md` writes, SHALL name the command the run takes back:
`conduct.py rejoin <id>` while a run is live, else `/mf-ship`. A version whose models file says `[rescue] skip = true` SHALL get no
diagnosis.

#### Scenario: A `Verify:` changed since the cut
- **WHEN** converge halts at Step 1.6 with `verify: halt`
- **THEN** the run writes the diagnosis with no worker, naming the person's amend commit and the command, and the version stays
  halted with no switch
