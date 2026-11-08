## ADDED Requirements

### Requirement: The release reads the findings files' frontmatter and card lines

`skills/mf-release/SKILL.md` SHALL read, of each findings file, its frontmatter, to the closing `---`, and, by one `grep`,
its cards' title, **Priority** and **Status** lines and each line naming `inconclusive`; it SHALL read no other part of the
file. Its preconditions on the findings files — each file's `verdict`, every blocking card `verified`, and `head:` at
`HEAD` — SHALL be judged from those lines alone, and its report's `inconclusive` sections named from them.

#### Scenario: A clean converge
- **WHEN** both findings files say `verdict: clean` with `head:` at `HEAD`, and each blocking card's Status reads `verified`
- **THEN** the release passes those preconditions, having read each file's frontmatter and the `grep`'s lines alone

#### Scenario: A blocking card not verified
- **WHEN** the adversarial file says `verdict: clean`, and a card whose Priority reads `high · adversarial · stability` has
  the Status `fixed`
- **THEN** the release halts, naming that card

## MODIFIED Requirements

### Requirement: A fresh worker reviews the plan before the cut commits

After its self-check, `skills/mf-cut-change/SKILL.md` SHALL hand a fresh read-only worker the **review packet**: the change
directory, `HEAD`, the cut's notes file and one question — whether each task can be built as written, each `Verify:` pass
after it, and each the search script did not run fail before it, save a `**HALT CHECK**`, which should hold. The reviewer
SHALL start from the packet, opening another file only at a `path:line` the change or the notes cite. Its prompt SHALL give
it a budget of 40 turns; a review that reaches it SHALL return its doubts so far under a first line `budget reached`, and the
cut SHALL take each of them as a doubt still standing after the second review. The cut SHALL fix a
simple doubt itself — a check that cannot pass or breaks `I19`, a reader a deletion missed, a task two readings would build
differently — re-running the search script; a doubt that changes a settled decision, or one still standing after a second
review, SHALL go to the person. A second review SHALL run only when a fix after the first — the cut's, the person's or the
switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `decided by the cutter` row included, or adds or
removes a task; a simple fix SHALL NOT be reviewed again. Before the first review, the cut SHALL stage the change directory
and record its tree; a second review SHALL be given the packet and the change directory's diff since that tree, and SHALL
judge that diff and the tasks it touches alone. Every plan review SHALL be a new worker given its packet; a message to an
earlier reviewer SHALL NOT be a review. An unattended cut SHALL instead take such a doubt's recommended option when the brief says
`decide: recommended`, adding a `decided by the cutter` row to the brief, and else SHALL halt in `cut.halt`, committing
nothing. Before writing, the cut SHALL re-check each fact of the brief whose cited path changed in `<sha>..HEAD`,
`<sha>` the brief's `At` line, and each fact citing no path, letting a fact on an unmoved path stand, and re-check every fact of a
brief with no `At` line, or one whose `<sha>` `git rev-parse --verify` does not resolve to a commit; where the host starts fresh
workers, up to four read-only helpers SHALL do that reading in parallel, each on Sonnet 5.5 at `medium` effort where the host
offers it, one per area of moved facts and one per design question, a helper not back in five minutes having its facts read by
the cut. No helper SHALL write a file: the cut SHALL write each helper's answer, and each fact it reads for the design, to
`.minions/changes/<change-id>/cut-notes.md`, and SHALL read that file in place of a file a helper already read. Before
writing, the cut SHALL also `git grep` every symbol, key or file the change deletes or renames and name each reader in a task, and
SHALL read the target's `CODING_STANDARDS.md` and `CONTRIBUTING.md`, planning to a target's own test rule over `T1`–`T6`.

#### Scenario: A deletion with a reader
- **WHEN** a change deletes a symbol a test still reads
- **THEN** the cut names that test in a task before it commits

#### Scenario: A design premise the code rules out
- **WHEN** the review finds a task the code cannot satisfy as the decision states it
- **THEN** the cut shows the doubt to the person with its `path:line`, and waits
- **AND WHEN** the cut is unattended and the brief does not say `decide: recommended`
- **THEN** it writes the doubt and its `path:line` to `cut.halt`, and commits nothing

#### Scenario: A brief at the cut's own commit
- **WHEN** the brief's `At` line names `HEAD`
- **THEN** the cut re-checks only the facts citing no path, and the deleted names

#### Scenario: A fact whose file moved
- **WHEN** a brief's fact cites a path that changed since its `At` line
- **THEN** the cut, or its helper, re-checks that fact at `HEAD` before writing

#### Scenario: The helpers' answers
- **WHEN** a helper answers a fact `moved to skills/x/SKILL.md:40`
- **THEN** the cut writes that answer to `cut-notes.md`, and the helper writes no file
- **AND** the review packet names `cut-notes.md`

#### Scenario: A simple fix
- **WHEN** the first review's only doubts are a check that cannot pass and a task two readings would build differently,
  and the cut's fixes change no decision and add or remove no task
- **THEN** the cut re-runs the search script and goes on to Step 9 with no second review

#### Scenario: A fix that adds a task
- **WHEN** the cut's fix after the first review adds a task, or changes a `design.md` decision
- **THEN** a second review runs, by a new worker given the packet and the change directory's diff since the first review
- **AND** no message goes to the first reviewer

#### Scenario: A review reaches its budget
- **WHEN** a plan review reaches its 40th turn with one doubt found
- **THEN** it returns that doubt under a first line `budget reached`
- **AND** the cut takes the doubt as one still standing after the second review: the person's, or under the switch the
  recommended option

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change — save an amend card that halts, as *The
converge fixer leaves the plan to the person* says; an amend card whose id an answered `amend needed` halt logged
since the newest `round 1 · start` line named, or whose qualified id already stands in the debt, SHALL go on as every
other card. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, and fix them. One fresh worker, the **pickup
check**, SHALL verify that fix at `medium` effort, given both findings files' open cards and the fix's own diff: on
adversarial's model when a picked card is adversarial's or `skills/mf-converge/scripts/surfaces.py` exits 1 over the fix's
range — the fix touching a `## Surfaces` path of `THREAT_MODEL.md`, or an adversarial card not `verified` or `accepted` — else
on conformance's. When the role whose model it needs is a mailbox role, converge SHALL instead verify the fix in a normal round,
counted. The pickup check SHALL be no round: it SHALL set both findings files' `head:` and leave their
`round:` as it stands, and a blocking card it leaves open SHALL go to a fix and a verify round counted against the cap. It
SHALL NOT name a per-version debt file. It SHALL delete a debt card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one debt file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and checks the fix by one pickup check

#### Scenario: A pickup check
- **WHEN** round 2 reads both files clean, and pickup picks a conformance `drift` card and an adversarial `medium` card
- **THEN** one fresh worker, on adversarial's model at `medium` effort, judges both cards against the pickup's diff
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

#### Scenario: An amend card after its amend
- **WHEN** Step 9 finds an amend card whose **Still true?** check still shows the defect, and an answered `amend needed` halt
  logged since the newest `round 1 · start` line named its id, or its qualified id already stands in the debt
- **THEN** converge writes it to the debt unless its id is there already, and halts nothing
- **AND WHEN** a catch-up run's Step 9 finds an amend card still true that no answered halt logged since the newest
  `round 1 · start` line named and the debt does not hold
- **THEN** it halts `amend needed — <its id>`

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
Step 7's verify round, and the pickup check, SHALL run `gate_check.py` as Step 1.6 does, after the gate.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, and the round halts `amend needed`

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup's fixer sets a `drift` card `wontfix`, naming an amend of the change's `design.md`
- **THEN** the pickup check keeps it `wontfix`, and Step 9 halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** Step 9 halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** check shows the defect gone at Step 9
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

### Requirement: Converge hands each worker a bundle of what the change cites

At each freeze, converge SHALL run `skills/mf-converge/scripts/bundle.py`, which writes
`.minions/changes/<change-id>/bundle.md`: each repo decision the change's proposal, design, tasks or spec delta cites — by a
`decisions.md#d<n>` link, or by `D<n> · ` and that decision's title — in full; an index, each `### D` heading of
`docs/decisions.md`; and each requirement the delta modifies or removes as a unified diff from its living text to the delta's,
a removed requirement's diff removing every line. A decisions file with no `### D`
heading SHALL go into the bundle whole. A design's own decision ids SHALL cite no repo decision. Conformance SHALL read the
bundle in place of the decisions file and the living spec, opening a decision the index names only to trace its architecture
section; adversarial SHALL read no bundle. `bundle.py` SHALL refuse to write through a link, and SHALL exit
2, writing nothing, on a file it cannot read.

#### Scenario: A change cites a decision
- **WHEN** a change's design links `docs/decisions.md#d48--…` and names a `D3` of its own
- **THEN** `bundle.md` holds D48 in full and every decision's heading in its index
- **AND** it holds no other decision's body

#### Scenario: A delta modifies a requirement
- **WHEN** a change's delta modifies a living requirement
- **THEN** `bundle.md` holds that requirement as a diff: each living line the delta drops marked `-`, each line it adds `+`
- **AND WHEN** the delta removes a requirement
- **THEN** its diff marks every living line `-`

#### Scenario: A decisions file with no headings
- **WHEN** a target's `docs/decisions.md` holds no `### D` heading
- **THEN** `bundle.md` holds the whole file

### Requirement: Converge bundles the debt cards on the diff's files

At each freeze, after `bundle.py`, converge SHALL run `skills/mf-converge/scripts/debt_match.py`, which writes
`.minions/changes/<change-id>/debt-cards.md` whole: a `# Debt cards on the diff's files` title, then each card of
`.minions/debt.md`, in full, whose **What it affects** field names in backticks a path the frozen patch changes, a `:<line>`
suffix dropped; `None.` when no card matches, or no debt file stands. No worker SHALL read `.minions/debt.md`; the repeat
rule SHALL match the cards `debt-cards.md` holds. `debt_match.py` SHALL refuse to write through a link, and SHALL exit 2,
writing nothing, when the debt file or the patch cannot be read.

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

### Requirement: Converge's checkers are conformance and adversarial

Converge SHALL run two checkers. **Conformance** SHALL judge the code against the change's own spec delta, design, tasks and
the decisions it cites, write `.minions/changes/<change-id>/conformance.md`, and grade `blocking` · `drift` · `nit`, its card
ids `R<n>`. **Adversarial** SHALL try to break the change — races, edge cases, exploits, security — write
`.minions/changes/<change-id>/adversarial.md`, and grade `critical` · `high` · `medium` · `low`, `high` a bug that would block,
its card ids `S<n>`. Each SHALL load its reference, `skills/mf-converge/references/generic-conformance.md` or
`skills/mf-converge/references/generic-adversarial.md`, whose `## The packet` table SHALL name what the conductor gives it:
conformance the range, `diff.patch`, the simplify commit's body, the change's `proposal.md`, `design.md`, `tasks.md` and spec
delta, its `bundle.md` and `debt-cards.md`, root `AGENTS.md` and the root standards files; adversarial the range,
`diff.patch`, the source and tests around the diff's hunks, `THREAT_MODEL.md`, root `AGENTS.md` and `debt-cards.md`.
Conformance SHALL read no code beyond the diff's hunks, save its stale-claim search. Each SHALL read `diff.patch` once, top to
bottom in slices, never a slice again, finding a hunk it needs again with `grep -n` on the patch, and run `git diff` or
`git show` only for a file's context the patch does not hold. A **security card** SHALL be an adversarial card whose
Priority's category is `security`.

#### Scenario: A converge round
- **WHEN** converge dispatches a round's checkers
- **THEN** conformance writes `conformance.md` and adversarial writes `adversarial.md`, and the release reads both

#### Scenario: The packets
- **WHEN** the packet tables of the conformance and adversarial references are read
- **THEN** conformance's names the change's artifacts, `bundle.md`, `debt-cards.md` and `diff.patch`, and no source beyond
  the diff's hunks
- **AND** adversarial's names `THREAT_MODEL.md` and `debt-cards.md`, and no `bundle.md`

#### Scenario: A security card
- **WHEN** an adversarial card's Priority reads `high · adversarial · security`
- **THEN** it is a security card
- **AND WHEN** it reads `high · adversarial · stability`
- **THEN** it blocks, and is no security card

### Requirement: A repeated finding escalates

Each station SHALL read the debt cards on the diff's files, `.minions/changes/<change-id>/debt-cards.md`. A finding that
repeats a debt card SHALL name that card's id in its **Related** field as `repeat of <id>`, and SHALL go up one level:
adversarial by one step, a conformance `nit` or `drift` to `blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** a station's finding describes a defect a card in `debt-cards.md` already holds
- **THEN** its **Related** field names `repeat of <id>`
- **AND** it goes up one level: adversarial by one step, a conformance `nit` or `drift` to `blocking`
