## ADDED Requirements

### Requirement: An answered converge halt gets one amend round

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an
older backlog lock's, SHALL be **answered** when `HEAD` is past its head, a descendant that is not it, and either both findings
files' `head:` is that head, or a commit past it is an **amend**: one parent, the subject `docs(<id>): amend the change
directory`, and paths under `openspec/changes/<id>/` alone — the person's, the rescue's or the supervisor's. `conduct.py`'s stage
SHALL then be `converge`, with no grant, and its converge check SHALL not read the old halt. A **halt before round 1** — a halt
other than a `verify: halt` in a run with no `start` line, not marked `· grant` — SHALL be void when `HEAD` is past its head, by
any commit, and SHALL be re-run when `HEAD` is its head: `conduct.py`'s stage SHALL be `converge` in both, and it SHALL start no
rescue for it. A run SHALL re-run a version once at the same head: one that halts before round 1 again SHALL stay out for the
rest of that run, a rejoin logging it still halted. Any other halt, and one whose head is no ancestor of `HEAD`, SHALL stand.

`skills/mf-converge/SKILL.md`, finding an answered halt, SHALL open a catch-up run marked `· amend` and run its catch-up round over
`<judged head>..HEAD`, the judged head being both findings files' `head:`, whatever their verdicts: the amend, the build's code
for a phase it added, and converge's own unverified fix. It SHALL open no new round 1 for it. Before the run's `start` line it
SHALL run each `Verify:` line the range adds to `tasks.md`, a ticked task's included, and halt `verify failed — <sub-task ids>`
when one fails. The run SHALL count its own rounds: one judge round and at most one fix round, `round:` carrying on past three;
a blocking finding open at its end SHALL halt `cap reached`. Review SHALL keep the full plan in its reading set, and its
stale-claim pass SHALL search the whole tree for each claim the amend changes. Finding a halt before round 1, it SHALL open a
plain new run, with no mark, as a fresh invocation does, save after a catch-up run, where a new run of the same mark runs the
catch-up round again. A run marked `· grant` that resumes SHALL stay a granted round.

#### Scenario: A gate red before round 1
- **WHEN** converge halts on a red gate before round 1 at head H, writing no `start` line, and the person asks a live run to take
  it back with no new commit
- **THEN** the run takes it back, and converge runs again in a plain new run
- **AND WHEN** it halts before round 1 again in that run
- **THEN** it stays out for the rest of the run, and a rejoin logs it still halted
- **AND WHEN** a commit past H follows
- **THEN** its stage is `converge`

#### Scenario: A two-line amend after a halt
- **WHEN** converge halted `amend needed`, and the person commits a two-line amend of the change directory
- **THEN** a run converges it in a catch-up run marked `· amend`, with no grant, judging `<judged head>..HEAD` in one round
- **AND** no run restarts at `round: 1`, and the version releases in the same run

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a catch-up run marked `· amend` over `<judged head>..HEAD`, with no grant and no new round 1

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the cap is a granted round's, in a run with no `start` line, and `HEAD` is its head
- **THEN** its stage stays `converge-halted`, and it is no halt before round 1

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, so its head is not the findings files' `head:`, and an amend follows
- **THEN** its stage is `converge`, and the amend round's range starts at the files' `head:`, the fix in it
- **AND WHEN** only a commit other than an amend follows
- **THEN** its stage stays `converge-halted`

#### Scenario: An amend adding a phase
- **WHEN** an amend answering a converge halt adds an unticked phase after the last
- **THEN** the version builds that phase, and the amend round's range holds the build's commits

#### Scenario: An amended Verify that fails
- **WHEN** the range adds a `Verify:` line to a ticked task, and the command fails
- **THEN** converge halts `verify failed — <sub-task id>` before its `start` line, and any commit past that head answers it

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

## MODIFIED Requirements

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, or after an answered halt, it runs one verify round over `head..HEAD`, with no pickup,
unless the selection is merges only, every merge replays by the fixed rules and no answered halt opened the run, when the round
is by rule and runs no worker.
**Merges and amends** are merges, and the person's, the rescue's or the supervisor's `docs(<id>): amend the change directory`
commits touching only `openspec/changes/<id>/`. When the selection is merges and amends only, or the run follows an answered
halt, the run SHALL count its own rounds: one judge round and at most one fix round, then a halt, with `round:` carrying on past
three. Any other selection SHALL count against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup
- **AND WHEN** the selection is merges only, and every merge replays by the fixed rules
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
- **THEN** `mf-converge` judges it in one Step 7 round as round 4, with no halt at the cap and no round by rule

#### Scenario: A rescue's amend at round 3 has its own count
- **WHEN** the last judged round is 3, Step 9 halted `amend needed`, and the selection is the rescue's amend of the change
  directory, carrying its `Rescue:` trailer
- **THEN** `mf-converge` judges it in one Step 7 round as round 4, with no halt at the cap and no round by rule

#### Scenario: A supervisor's amend has its own count
- **WHEN** the last judged round is 3, Step 9 halted `amend needed`, and the selection is the supervisor's amend of the change
  directory, carrying its `Supervisor:` trailer
- **THEN** `mf-converge` judges it in one Step 7 round as round 4, with no halt at the cap and no round by rule

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3, no answered halt opened the run, and the selection holds a commit that is neither a merge
  nor an amend
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
a conflicted `CHANGELOG.md` with the `changelog` rule, run the `decisions` rule on every merge, conflicted or clean, run the
`delta` rule, and exit 0 when `delta` names no requirement and the rebuilt tree equals the merge's tree, else 1. Its line SHALL
name each path a rule settled: one git left unmerged, and `docs/decisions.md` when the `decisions` rule renumbered. Its git SHALL
run no hook and fetch no missing object.
It SHALL exit 2, rebuilding nothing, for a commit without two parents or whose second parent the default branch does not hold.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL first run *Catch-up scope*'s ancestry and parent checks, halting when one
fails, then run `replay` for each merge in its selection; when every merge replays and the selection holds nothing else, it SHALL
write both findings files `head: HEAD` and `verdict: clean` with a `## By rule` section naming each merge's paths, log
`round N · by rule — clean, <paths>`, dispatch no worker, and count the round within the merges-and-amends count. A selection
holding an amend — the person's, the rescue's or the supervisor's — and a run after an answered halt SHALL take the catch-up round
as before.

#### Scenario: A changelog the rule settled
- **WHEN** the integrate merge conflicted in `CHANGELOG.md` alone, settled by `integrate.py changelog`
- **THEN** the catch-up replays it, writes both findings files clean with `## By rule`, dispatches no worker, and the release
  passes its preconditions

#### Scenario: A decision renumbered in a cleanly merged file
- **WHEN** git merged `docs/decisions.md` with no conflict, and the integrate merge's `decisions` rule renumbered the branch's id
- **THEN** replay prints `replay: by rule — docs/decisions.md` and exits 0

#### Scenario: A merge and the person's amend
- **WHEN** the selection is a merge that replays and the person's amend of the change directory, and Step 1 passes
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches review and security over the selection

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
`amend needed` halt to its amend round, a catch-up run marked `· amend` whose one Step 7 round judges the rescue's amend. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer and wait for a re-run — save the person's
`docs(<id>): amend the change directory` commits, none carrying a `Rescue:` or `Supervisor:` trailer, which answer an
`amend needed`, `verify: halt` or clean catch-up or amend-run halt
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
- **WHEN** a build halts on a design premise the code rules out
- **THEN** the rescue writes `.minions/changes/<id>/rescue.md`, and the version stays halted, its halt naming the file

#### Scenario: A rescue outside the plan
- **WHEN** a rescue's commit touches a file outside `tasks.md` and `design.md`
- **THEN** the version halts, naming the file

#### Scenario: A rescue at amend needed
- **WHEN** converge halts `amend needed` on a review card whose fix names a `design.md` prose amend, in the run or before it
- **THEN** the rescue commits that amend, and the version converges again in the same run, in a catch-up run marked `· amend`,
  with no new round 1
- **AND WHEN** the card is a security card of `high` severity
- **THEN** the rescue diagnoses, and the version stays halted

#### Scenario: A rescue at a drift halt
- **WHEN** converge's Step 9 halts `amend needed` on an `open` `drift` card whose **Fix** names a `design.md` amend, both findings
  files clean, and the version's models file says `decide = "recommended"`
- **THEN** the rescue commits that amend with its `Rescue:` trailer, and the version goes on in the same run through its amend
  round, whose one Step 7 round reads the amend, with no new round 1, and releases

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

### Requirement: The converge fixer leaves the plan to the person

`skills/mf-converge/SKILL.md`'s fix pass SHALL NOT edit the change's `tasks.md` or `design.md`. A card whose fix needs either SHALL be
set `wontfix`, naming the amend the person commits by the file's path: an **amend card**, as is any card whose **Fix** names the
change's `tasks.md` or `design.md` by path. A blocking amend card SHALL halt the round `amend needed — <card ids>` after the fix
pass. The verify pass SHALL keep an amend card's `wontfix` whose justification holds, and SHALL NOT turn it `accepted`; in an amend
round, it SHALL turn an amend card the amend settled, its **Still true?** check showing the defect gone, `verified`, its note
naming the amend. At Step 9,
before the debt lock, every non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?** check still shows
the defect, SHALL halt the run `amend needed — <card ids>`, writing nothing to the debt, save one *Converge keeps deferred work
in one repository debt file* lets go on. The person's amend answers either halt.
Step 7's verify round SHALL run `gate_check.py` as Step 1.6 does, after the gate.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, and the round halts `amend needed`

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup round's fixer sets a `drift` card `wontfix`, naming an amend of the change's `design.md`
- **THEN** the verify pass keeps it `wontfix`, and Step 9 halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** Step 9 halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** check shows the defect gone at Step 9
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — and the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role, the confirmed and refuted cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. The cut's `diff-lines` and `diff-files` SHALL be the collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and review's yield

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

## REMOVED Requirements

### Requirement: A converge halt answered by the person converges afresh

**Reason**: An answered halt gets one amend round over its own range, never a reopen of converge from round 1 over the whole
change, per this change's D63.

**Migration**: Read *An answered converge halt gets one amend round*: its answer rule, its `· amend` run and its own count
replace the `· amended` run, and a halt before round 1 is answered and re-run as before.
