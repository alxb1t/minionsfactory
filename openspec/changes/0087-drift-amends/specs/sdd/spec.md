## MODIFIED Requirements

### Requirement: The converge fixer leaves the plan to the person

`skills/mf-converge/SKILL.md`'s fix pass SHALL NOT edit the change's `tasks.md` or `design.md`. A card whose fix needs either SHALL be
set `wontfix`, naming the amend the person commits by the file's path: an **amend card**, as is any card whose **Fix** names the
change's `tasks.md` or `design.md` by path. A blocking amend card SHALL halt the round `amend needed — <card ids>` after the fix
pass. The verify pass SHALL keep an amend card's `wontfix` whose justification holds, and SHALL NOT turn it `accepted`. At Step 9,
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

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change — save an amend card that halts, as *The
converge fixer leaves the plan to the person* says; an amend card whose id an answered `amend needed` halt named, or whose
qualified id already stands in the debt, SHALL go on as every other card. After both verdicts are
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

#### Scenario: An amend card after its amend
- **WHEN** Step 9 finds an amend card whose **Still true?** check still shows the defect, and an answered `amend needed` halt
  named its id, or its qualified id already stands in the debt
- **THEN** converge writes it to the debt unless its id is there already, and halts nothing
- **AND WHEN** a catch-up run's Step 9 finds an amend card still true that no answered halt named and the debt does not hold
- **THEN** it halts `amend needed — <its id>`

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
and SHALL judge an amend there carrying a `Rescue:` trailer in one Step 7 round over its diff, passing only a trailer-less amend by rule;
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

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

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

#### Scenario: A rescue at a drift halt
- **WHEN** converge's Step 9 halts `amend needed` on an `open` `drift` card whose **Fix** names a `design.md` amend, both findings
  files clean, and the version's models file says `decide = "recommended"`
- **THEN** the rescue commits that amend with its `Rescue:` trailer, and the version goes on in the same run through a catch-up
  round whose one Step 7 round reads the amend, with no new round 1, and releases

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
