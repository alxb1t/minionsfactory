## ADDED Requirements

### Requirement: A plan check holds the plan to the built tree

`skills/mf-converge/scripts/plan_check.py --change <id> --base <rev>` SHALL exit 1, printing one `plan: ` line per problem,
when: the command of a ticked sub-task's `Verify:`, run again as argv with no shell from the repository root, exits non-zero,
save a search whose `Verify:` says `prints nothing` or `` prints `0` ``, which passes on exit 1 with no other output; a
`- [ ] N.M` box stands unticked under a ticked `## Progress` phase; a name the diff from the merge base of `<rev>` and `HEAD`
removes — a Python `def` or `class` name, or an upper-case module-level name, that nothing outside `openspec/` names at
`HEAD`, or the base name of a file the diff deletes — is still named, as a word, on a line of `openspec/specs/` or of the
change directory outside `tasks.md` and `design.md`'s `## Tests` section, that line holding no word of removal; a `def test_`
name under `tests/` at the merge base is gone at `HEAD` and `design.md`'s `## Tests` section does not name it; or a sub-task
marked `**CORPUS**` names a case `scripts/corpus.toml` does not hold. It SHALL NOT run again a `**HALT CHECK**` sub-task's
command, a command of a `**HUMAN` phase, or a command naming `plan_check.py`, and SHALL run no command with a shell. It SHALL
exit 0 printing `plan: clean` when none holds, and 2 when it cannot read `tasks.md`, the base or git.
`skills/mf-build/SKILL.md` SHALL run it at the build's close, after the metrics and before `build.done`, and SHALL halt on any
other exit than 0, writing no `build.done`. Converge's fixer SHALL run it after its gate and before its commit, clearing each
problem as a blocking card of the same pass, or setting it `wontfix` naming the amend; converge's Step 7 SHALL run it after
`gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any verify worker, counting no round; a line
the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the run `amend needed — plan check:
<subjects>`, naming each line's sub-task, `path:line` or test name and never the command it quotes. `skills/mf-rescue/SKILL.md`
SHALL take that halt as a fix of the lines `plan_check.py` prints, in `tasks.md` and `design.md`'s prose.

#### Scenario: A ticked check that no longer holds
- **WHEN** at the build's close a ticked sub-task's `Verify:` command exits 1
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command, and the build halts with no `build.done`

#### Scenario: An unticked box under a finished phase
- **WHEN** `## Progress` ticks phase 2 and sub-task `2.3` stands unticked
- **THEN** `plan_check.py` exits 1, naming `2.3`

#### Scenario: A removed name still in the plan
- **WHEN** the diff removes `def _fence`, nothing outside `openspec/` names `_fence` at `HEAD`, and a `design.md` line names it
  with no word of removal
- **THEN** `plan_check.py` exits 1, naming that line
- **AND WHEN** the line says the change deletes `_fence`
- **THEN** that line halts nothing

#### Scenario: A test the base had
- **WHEN** `def test_old` stands under `tests/` at the merge base and nowhere at `HEAD`
- **THEN** `plan_check.py` exits 1, naming `test_old`
- **AND WHEN** `design.md`'s `## Tests` section names `test_old`
- **THEN** it halts nothing

#### Scenario: A clean plan
- **WHEN** every ticked `Verify:` passes, every box under a ticked phase is ticked, and no removed name or base test is missing
- **THEN** `plan_check.py` exits 0 and prints `plan: clean`

#### Scenario: A fix that breaks a ticked check
- **WHEN** converge's fixer commits a fix and Step 7's `plan_check.py` exits 1
- **THEN** the conductor sends its lines to the fix station before any verify worker, and the round count stays
- **AND WHEN** the next Step 7's `plan_check.py` prints a line that fix pass was sent, naming sub-task `3.2`
- **THEN** converge halts `amend needed — plan check: 3.2`, and the rescue amends `tasks.md` or `design.md` to clear it

### Requirement: A reader of run data has a corpus case

`make corpus` SHALL run `scripts/corpus.py`, which SHALL run each `[[case]]` of `scripts/corpus.toml` — a reader's argv, run
with no shell from the repository root — once per file its `each` globs match under the run directory, or once when it has
none, writing only under the run directory's `corpus/`. It SHALL exit 1 naming each run that exits non-zero, 2 when the cases
file cannot be read or the run directory is a link, and 0 otherwise. `make gate` and `make check` SHALL NOT run it.
`skills/mf-cut-change/SKILL.md` SHALL mark each sub-task that adds or alters code reading the run directory, run logs or Codex
sessions `` **CORPUS** `<case>` `` in a repository whose root `Makefile` has a `corpus` target, and SHALL plan the case in
`scripts/corpus.toml`. `skills/mf-build/SKILL.md` SHALL run `make corpus` after such a sub-task's `Verify:` passes and before
its tick, halting on any other exit than 0. `plan_check.py` SHALL fail a marked sub-task whose case `scripts/corpus.toml` does
not hold.

#### Scenario: The corpus over this repository
- **WHEN** `make corpus` runs in this repository
- **THEN** each case runs over the run directory's own findings files, status logs, run logs and Codex sessions, and it exits 0

#### Scenario: A reader that fails on real data
- **WHEN** a case's reader exits 1 on one change's findings file
- **THEN** `make corpus` exits 1, naming the case and that file

#### Scenario: A marked sub-task with no case
- **WHEN** a ticked sub-task is marked `` **CORPUS** `review-metrics` `` and `scripts/corpus.toml` holds no case of that name
- **THEN** `plan_check.py` exits 1, naming the sub-task and the case

## MODIFIED Requirements

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change — save an amend card that halts, as *The
converge fixer leaves the plan to the person* says; an amend card whose id an answered `amend needed` halt logged
since the newest `round 1 · start` line named, or whose qualified id already stands in the debt, SHALL go on as every
other card. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, and fix them. When round 1 of a run that is no
catch-up run leaves a blocking card open, its fix pass SHALL take those same cards with the blocking ones — the **round-1
pickup** — and round 2's verify round SHALL judge them all; pickup SHALL then not run again in that run. One fresh worker, the
**pickup check**, SHALL verify a pickup's fix at `medium` effort, given both findings files' open cards and the fix's own diff: on
adversarial's model when a picked card is adversarial's or `skills/mf-converge/scripts/surfaces.py` exits 1 over the fix's
range — the fix touching a `## Surfaces` path of `THREAT_MODEL.md`, or an adversarial card not `verified` or `accepted` — else
on conformance's. When the role whose model it needs is a mailbox role, converge SHALL instead verify the fix in a normal round,
counted. A pickup whose fixer commits nothing SHALL get no pickup check. The pickup check SHALL be no round: it SHALL set both
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

#### Scenario: A round-1 pickup
- **WHEN** round 1 leaves one blocking card open and two non-blocking cards sized `one line`
- **THEN** one fix pass takes all three, and round 2's verify round judges all three
- **AND WHEN** round 2 reads both files clean
- **THEN** no pickup runs, and converge goes on to the debt

#### Scenario: A pickup that commits nothing
- **WHEN** the pickup's fixer sets every picked card `wontfix` and commits nothing
- **THEN** no pickup check runs, and converge goes on to the debt

### Requirement: A repeated finding escalates

Each station SHALL read the debt cards on the diff's files, `.minions/changes/<change-id>/debt-cards.md`. A finding that
repeats a debt card SHALL name that card's id in its **Related** field as `repeat of <id>`, and SHALL go up one level:
adversarial by one step, a conformance `nit` or `drift` to `blocking`. A finding whose mechanism a debt card holds in another
form — the same code misreading the same kind of input — SHALL also name `repeat of <id>` in its **Related** field, and SHALL
keep its grade, its **Priority** saying it is a repeat of that card's mechanism.

#### Scenario: Converge names the repeat rule
- **WHEN** a station's finding describes a defect a card in `debt-cards.md` already holds
- **THEN** its **Related** field names `repeat of <id>`
- **AND** it goes up one level: adversarial by one step, a conformance `nit` or `drift` to `blocking`

#### Scenario: A repeat of a card's mechanism
- **WHEN** a station finds that `_rows` misreads a new Markdown form, and `debt-cards.md` holds a card on `_rows` misreading
  another form
- **THEN** its **Related** field names `repeat of <that card's id>`, and its grade stays the one its harm earns

### Requirement: The converge fixer leaves the plan to the person

`skills/mf-converge/SKILL.md`'s fix pass SHALL NOT edit the change's `tasks.md`, nor its `design.md` save the prose a `drift` card
names outside the `## Decisions` section, which it SHALL correct; it SHALL NOT edit that section, a row of its table, a decision's
D-id or a `## ` heading, save one line it MAY append as the last line of a `### D<n>` entry of that section,
`Fix note (<YYYY-MM-DD>, <card id>): <one line>`, recording how the code now implements that decision, the entry's other lines
untouched. A card whose fix that line records SHALL be no amend card, and converge's close-out SHALL name each fix note the run
appended, by its D-id and card. A card whose fix needs any other edit of those SHALL be set `wontfix`, naming the amend the
person commits by the file's path: an **amend card**, as is any card whose **Fix** names the change's `tasks.md` or `design.md`
by path, save a `drift` card's naming that prose or a fix note. A blocking amend card SHALL halt the round
`amend needed — <card ids>` after the fix pass. The verify pass SHALL keep an amend card's `wontfix` whose justification holds,
and SHALL NOT turn it `accepted`; in an amend
round, it SHALL turn an amend card the amend settled, its **Still true?** check showing the defect gone, `verified`, its note
naming the amend. At Step 9,
before the debt lock, every non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?** check still shows
the defect, SHALL halt the run `amend needed — <card ids>`, writing nothing to the debt, save one *Converge keeps deferred work
in one repository debt file* lets go on. The person's amend answers either halt.
The fixer SHALL run `plan_check.py` after its gate, as *A plan check holds the plan to the built tree* says.
Step 7's verify round, and the pickup check, SHALL run `gate_check.py` as Step 1.6 does, after the gate; Step 7 SHALL then run
`plan_check.py`.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, and the round halts `amend needed`

#### Scenario: Drift in the design's prose
- **WHEN** the pickup picks a `drift` card whose **Fix** names a line of the change's `design.md` outside its `## Decisions`
  section
- **THEN** the fixer corrects that line and sets the card `fixed`; it is no amend card, and Step 9 halts on nothing for it

#### Scenario: A fix that changes how a decision is built
- **WHEN** a card's fix changes how the code implements the change's D3, and D3's own words still hold
- **THEN** the fixer appends `Fix note (<date>, <card id>): <how the code now does it>` as the last line of D3's entry, edits no
  other line of it, and sets the card `fixed`
- **AND** converge's close-out names D3 and the card

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup's fixer sets a `drift` card `wontfix`, naming an amend of a decision in the change's `design.md`
- **THEN** the pickup check keeps it `wontfix`, and Step 9 halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** Step 9 halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** check shows the defect gone at Step 9
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

### Requirement: A rescue decides by the version's switch

A version's models file MAY say `decide = "recommended"` at its top, before its tables: the **switch**, which the cut writes
from the brief. `conduct.py` SHALL read it once a run, with the version's plan, and pass it to the rescue as `decide=recommended`.
Under the switch, `skills/mf-rescue/SKILL.md` SHALL take the fix a card or the plan itself proposes as its own decision, at a build
halt and an `amend needed` halt: it MAY edit `proposal.md` and `design.md`'s `## Decisions` besides `tasks.md` and
`design.md`'s prose, and its commit SHALL carry a `Decided-by: rescue` trailer. It SHALL never edit the spec delta, code or a
test, take a security card of `critical` or `high` severity, approve a gate makefile, settle an integrate conflict, release,
merge or push, or answer a run-wide halt. `conduct.py` SHALL take an amend that touches `proposal.md` or changes `design.md`'s
`## Decisions` section only under the switch and with that trailer, logging `rescue — <id>: decided · <sub-task> · <commit>`;
without the switch it SHALL refuse it, naming the decision. Lines of the form `Fix note (<YYYY-MM-DD>, <card id>): <text>` that
end a `### D<n>` entry, added or edited, SHALL be no change to that section; any other edit of the entry SHALL be one. The
run's closing line, and its `done` line, SHALL name
` · decided <ids>` when a rescue decided, `report` SHALL print a line for each decision, and the run's metrics SHALL count them as `rescues-decided`.

#### Scenario: A decided amend
- **WHEN** a version's models file says `decide = "recommended"`, and its rescue at `amend needed` commits an edit to a row of
  `design.md`'s `## Decisions` with `Decided-by: rescue`
- **THEN** the run takes it, logs `rescue — <id>: decided`, the version converges again, and `report` and the closing line name it

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue commits the same amend
- **THEN** the run refuses it, naming the decision, and the version stays halted

#### Scenario: An amend that appends a fix note
- **WHEN** the models file has no `decide`, and the rescue's amend appends a `Fix note (…)` line as the last line of D2's entry
- **THEN** the run takes it as an amend that decided nothing
- **AND WHEN** the amend also edits a line of D2's own words
- **THEN** the run refuses it, naming the decision

#### Scenario: A worker writes the switch
- **WHEN** a worker adds `decide = "recommended"` to the models file during the run
- **THEN** no rescue of that run decides for that version

### Requirement: A run cuts each queued brief in a station of its own

A run SHALL read the queue at its start and at every poll, and take each queued cut with no halt that it has not read
before, or that a request names. For each, `conduct.py` SHALL make the branch named by its id and its linked worktree from the
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
- **THEN** the run takes it at its next poll, beside the versions it is running

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

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one.
It SHALL read the brief as CommonMark does: a section opens at the ATX heading written `## Decisions`, `## Dependencies` or
`## For the cut`, and runs to the next heading of level one or two, in any form, or HTML heading of those levels; a section's
lines split at a newline. A carriage return not before a newline SHALL exit 1, naming its line. It SHALL also exit 1 when a
line of `## For the cut` is none of: a blank line; a head, opening
`<n>. ` and one space at the line's start; under a head, a `- models: ` or `- **Acceptance:** ` line indented three spaces or
as far as its head's text; a line indented at least two spaces past its Acceptance line, after that line or its
continuation; or the cut's `Cut <YYYY-MM-DD> as <id> at <sha>.` line. It SHALL also exit 1 when a head names a slug, an
`after` entry or a `beside` entry that `conduct.py`'s `SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or
more than one, or more than one `beside:`, or when an item has no `models:` line, more
than one, or one not naming the build, converge, release and cut station in order, then any of the build-moderate,
conformance, adversarial and fix parts in that order, each with a model and effort of `[A-Za-z0-9._-]` alone, then at most a
last `shadow`. A head MAY
omit `beside:`. A build,
converge, release, conformance or adversarial model MAY open with a host, `claude/` or `codex/`; a host it does not know, or a
host on the cut, fix or build-moderate model, SHALL exit 1, naming it. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or
`## For the cut` holds a character for which `str.isprintable()` is false, printing `brief: halt — <section> line <n>: a
character isprintable() refuses`; when a heading of any form, a line of an HTML block, or a line holding an inline `<h1>`…`<h6>`
tag, that is not `## Decisions`, `## Dependencies` or `## For the cut` as written, reads as one of them once its `<h1>`…`<h6>`
tags and every character but a letter or a digit are dropped and case is folded,
a letter or digit outside ASCII standing for any one, and at least one ASCII letter left, or a second heading is
one of them as written; a line inside a fenced or indented code block SHALL be none of these; when the brief has no
`## Dependencies`; and when that section is neither `None.` nor a table of item,
package, constraint and why whose every row names a `## For the cut` item's slug, a package and a constraint.
It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot
be parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`, or an
  item's slug or cut effort holds `$(…)` or `;`
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** a `## For the cut` line opens `- ` where `<n>. ` is due, a `| ` line sits under a head, an unindented line
  follows a head, or a head holds a second `after:`, or an item has a second models line
- **THEN** `brief_check.py` exits 1, naming the line or the item
- **AND WHEN** a head holds a second `beside:`, or a `beside` entry holding `;`
- **THEN** `brief_check.py` exits 1, naming the item

#### Scenario: A models or Acceptance line with no head
- **WHEN** a brief's `## For the cut` holds a `- models: ` or `- **Acceptance:** ` line three spaces in before any head
- **THEN** `brief_check.py` exits 1, naming the line as outside the item grammar

#### Scenario: A models line naming hosts
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · conformance codex/gpt-6.1-sol high · adversarial codex/gpt-6.1-sol
  high · fix claude-opus-5-5 high · shadow`
- **THEN** that line halts nothing
- **AND WHEN** a part names `gemini/x`, or the fix or cut model opens with a host
- **THEN** `brief_check.py` exits 1, naming the item and the word

#### Scenario: A models line naming a moderate build
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · build-moderate claude-sonnet-5-5 high`
- **THEN** that line halts nothing
- **AND WHEN** the `build-moderate` part comes after `conformance`, or its model opens with `claude/`
- **THEN** `brief_check.py` exits 1, naming the item

#### Scenario: A checked line holds other whitespace
- **WHEN** a line of a brief's `## For the cut`, `## Dependencies` or `## Decisions` holds a no-break space, an ideographic
  space, a tab, a vertical tab, a form feed, U+200B or U+2060
- **THEN** `brief_check.py` exits 1, printing `brief: halt — <section> line <n>: a character isprintable() refuses` for that line

#### Scenario: A For the cut heading in another form
- **WHEN** a brief holds ` ## For the cut`, `##<tab>For the cut`, `## For the cut ##`, `## For the cut` followed by U+200B,
  `For the cut` underlined `---`, `<h2>For the cut</h2>`, or `## For the cut` with a Cyrillic `о` for its `o`, besides its
  `## For the cut`, or that heading twice
- **THEN** `brief_check.py` exits 1, naming each such line

#### Scenario: A For the cut heading in a fenced block
- **WHEN** a brief holds `## For the cut` inside a fenced code block, besides its own `## For the cut`
- **THEN** that line halts nothing and opens no section, as CommonMark reads it

#### Scenario: A lone carriage return
- **WHEN** a brief's line holds a carriage return not before a newline
- **THEN** `brief_check.py` exits 1, naming that line

#### Scenario: A brief's packages
- **WHEN** a hard brief has no `## Dependencies`, or one that is prose, or a row naming no `## For the cut` item
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** it reads `None.`, or each row names an item, a package and a constraint
- **THEN** that section halts nothing

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, its `## Dependencies`, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`
- **AND WHEN** a head also carries `· beside: 0097-cross-model`
- **THEN** that head halts nothing

### Requirement: A fresh worker reviews the plan before the cut commits

After its self-check, `skills/mf-cut-change/SKILL.md` SHALL hand a fresh read-only worker the **review packet**: the change
directory, `HEAD`, the cut's notes file and one question — whether each task can be built as written, each `Verify:` pass
after it, and each the search script did not run fail before it, save a `**HALT CHECK**`, which should hold. Every plan
reviewer SHALL run on Opus 5.5 at `high` effort where the host offers it, whatever model the cut runs on. The reviewer
SHALL start from the packet, opening another file only at a `path:line` the change or the notes cite. Its prompt SHALL give
it a budget of 40 turns; a review that reaches it SHALL return its doubts so far under a first line `budget reached`, and the
cut SHALL take each of them as a doubt still standing after the second review. The cut SHALL fix a
simple doubt itself — a check that cannot pass or breaks `I19`, a reader a deletion missed, a task two readings would build
differently — re-running the search script; a doubt that changes a settled decision, or one still standing after a second
review, SHALL go to the person. A second review SHALL run only when a fix after the first — the cut's, the person's or the
switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `decided by the cutter` row included, or adds or
removes a task; a simple fix SHALL NOT be reviewed again. Before the first review, the cut SHALL stage the change directory
and record its tree; a second review SHALL be given the packet and the change directory's diff since that tree, and SHALL
judge that diff, and each task that cites a decision or a path the diff changes. Every plan review SHALL be a new worker given its packet; a message to an
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

#### Scenario: A cut on another model
- **WHEN** the cut runs on Sonnet 5.5 and the host offers Opus 5.5
- **THEN** each plan review runs on Opus 5.5 at `high` effort
