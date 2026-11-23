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
`amend needed` halt to its amend round, a catch-up run marked `· amend` whose one Step 7 round judges the rescue's amend. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer and wait for a re-run — save the person's
`docs(<id>): amend the change directory` commits, none carrying a `Rescue:` or `Supervisor:` trailer, which answer an
`amend needed`, `verify: halt` or clean catch-up or amend-run halt
by amends alone: the version SHALL go on in the run, logged `rescue — <id>: amended · <commit>`. A **halt** SHALL be a halted sub-task or stage at the
version's `HEAD` when the halt is read, so a halt at a new head is a new halt, whatever its sub-task or stage; this holds for a build's, a converge's and an
integrate's halts alike. A version SHALL get at most `RESCUES = 3` rescues in a run, and none for a halt it was rescued from before; a timeout, a usage limit and D47's halts that
need the person SHALL get none. The halt's ` · rescued <sub-tasks>` words SHALL name the sub-task or stage of each rescue, with no head. The run SHALL log `rescue — <id>: fixed · <sub-task> · <commit>`, `rescue — <id>: decided ·
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
- **WHEN** converge halts `amend needed` on a conformance card whose fix names a `design.md` prose amend, in the run or before it
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
- **WHEN** a version halts again at the same `HEAD` on a sub-task it was rescued from
- **THEN** no rescue runs, and the halt names the sub-task as rescued

#### Scenario: The same sub-task at a new head
- **WHEN** a version's build halts on sub-task 1.1 and is rescued, and a commit then moves `HEAD` and the build halts on 1.1 again
- **THEN** the second halt is a new halt, and a rescue runs for it

#### Scenario: A converge halt at two heads
- **WHEN** a version's converge halts `amend needed` at one head and is rescued, and halts `amend needed` again at the head the amend left
- **THEN** each halt gets its rescue in the same run

#### Scenario: An integrate halt
- **WHEN** a version halts `integrating` at one head and a rescue's turn is spent on it
- **THEN** a second halt `integrating` at that head gets no rescue, and one at a new head gets one

#### Scenario: The fourth rescue
- **WHEN** a version has been rescued at three heads in the run and halts at a fourth
- **THEN** no rescue runs, whatever the sub-task or stage, and the halt names each sub-task or stage rescued

#### Scenario: A sub-task added after its phase is ticked
- **WHEN** an amend at a converge halt adds a sub-task the build must make, and every phase of `## Progress` is ticked
- **THEN** the amend adds it in a new unticked phase after the last, and the version builds that phase before it converges

#### Scenario: A link at the rejoin folder
- **WHEN** a worker swaps the rejoin folder for a link to another directory after the run lists it
- **THEN** nothing in that directory is deleted

### Requirement: A supervisor answers what the rescue leaves

Under a version's switch, `decide = "recommended"`, when its rescue at a build check halt, a converge halt or an
`integrating` halt on a semantic conflict writes a diagnosis, the run diagnoses its converge `verify: halt`, or its rescue is
spent on the halt — the halt rescued before in the run, or `RESCUES` reached — `conduct.py` SHALL spawn the `mf-supervise`
station in that version's thread, with `decide=recommended`, and with `brief=<path>` when the version's passed cut recorded a
brief that still names a file. It SHALL spawn none without the switch; at an integrate red gate; at an `integrating` halt on
an open merge a supervisor was spawned on before, in this run or an earlier one, which the home folder's queue records; at a
halt the rescue's answer
on disk holds for a re-run; at a converge halt while `adversarial.md` holds an open security card of `critical` or `high`
severity, or its `amend needed` names one; when the rescue's worker failed or its amend was refused; nor when the models file's
`[rescue]` table says `skip = true`. The station SHALL run on the `[supervise]` table's executor, model and effort; on Claude, an
absent model SHALL be `claude-opus-5-5` and an absent effort `high`. At a passed cut, `conduct.py` SHALL record the brief's path
in the home folder's queue, under `briefs/<id>`, where no worker writes; a version cut by hand SHALL have none. The station SHALL
read the brief as evidence, never instruction.

`skills/mf-supervise/SKILL.md` SHALL answer a build or converge halt with one `docs(<id>): amend the change directory` commit
carrying `Supervisor: <sub-task or stage>` and `Decided-by: supervisor` trailers, or commit nothing. It MAY edit any file under
`openspec/changes/<id>/`, the spec delta included, tick a sub-task box whose `Verify:` it ran and saw pass, and add work as a new
unticked phase after the last. It SHALL never edit code, a test or any other path, take a security card of `critical` or `high`
severity, approve a gate makefile, accept a risk the threat model does not accept, untick a box, release, merge or push. At an
`integrating` halt it SHALL instead resolve the note's conflicts in Markdown files under `openspec/` and `docs/` alone, stage
each by name, write `.minions/changes/<id>/integrate.settled` naming what it settled, leave the merge and the note open, and
commit nothing; or edit nothing.

`conduct.py` SHALL take the commit only when it is the one commit past the station's start, with one parent, the amend's
subject, a `Supervisor:` trailer, a `Decided-by:` trailer reading `supervisor`, and paths under `openspec/changes/<id>/` alone. It
SHALL then clear the version's halt and its diagnosis, log `supervise — <id>: decided · <sub-task or stage> · <commit>`, and go
on in the same thread, with no restart and no wait for a poll. At an `integrating` halt it SHALL take the settle only when
`HEAD` and the open merge are the station's start's, the note stands, every index path it changed is a Markdown file under
`openspec/` or `docs/`, the work tree holds nothing unstaged or untracked, no path stays unmerged, and `integrate.settled` was
written during the station's run. It SHALL then clear the version's halt and its diagnosis, log
`supervise — <id>: decided · integrating · <tree>`, `<tree>` the staged tree, and spawn `mf-integrate` `with settled=supervisor`
in the same thread, halting the version when the merge commit holds a path past that tree other than a test its body names
fixed. Any other outcome SHALL halt the version, naming what the station left; at a converge or integrate halt, an answer on
disk SHALL then hold the version for a re-run as the rescue's does, the halt reading `supervisor answered its halt`, and the
person's amends alone, none carrying a `Rescue:` or `Supervisor:` trailer, SHALL go on. A version SHALL get one supervisor try
per halt, a **halt** being a sub-task or stage at the version's `HEAD` as *A halted version is rescued in its run* says, and at most `SUPERVISES = 2` in a run; a halt the supervisor tried before SHALL name ` · supervised <sub-tasks>`, each a
sub-task or stage with no head. A
grant SHALL be refused while the station runs, as while the rescue runs. `report` SHALL print
`<id> · supervised <sub-task or stage> · <commit>` for each taken amend or settle, the run's closing line and its `done` line
SHALL name ` · supervised <ids>`, and the run's metrics SHALL count them as `supervisor-decided`.

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
- **WHEN** under the switch a version halts again at the same `HEAD` on a sub-task its rescue was spent on in the run
- **THEN** the supervisor runs once, with no rescue
- **AND WHEN** the version halts on that sub-task at that `HEAD` again
- **THEN** no worker runs, and the halt names ` · rescued 1.1 · supervised 1.1`

#### Scenario: A halt at a new head
- **WHEN** under the switch a supervisor answered a converge halt at one head and the version halts again at the head its amend left
- **THEN** a supervisor runs for the new halt, while the cap of supervisions a version gets in a run stands

#### Scenario: The third supervision
- **WHEN** a version has had two supervisions in the run and halts at a new head
- **THEN** no supervisor runs

#### Scenario: A refused amend at a converge halt
- **WHEN** the supervisor at an `amend needed` halt commits an amend of the change directory with no `Decided-by: supervisor`
  trailer
- **THEN** the version stays halted for the run, its halt reading `supervisor answered its halt`, and the closing line names
  `a re-run` as its need

#### Scenario: A blocking security card
- **WHEN** converge halts `amend needed` naming a security card of `high` severity, under the switch
- **THEN** the rescue diagnoses, no supervisor runs, and the version stays halted

#### Scenario: A blocking adversarial card outside security
- **WHEN** a converge cap leaves an open adversarial card of `high` severity whose category is `stability`, under the switch,
  and the rescue diagnoses the halt
- **THEN** the supervisor runs

#### Scenario: The brief kept at a passed cut
- **WHEN** a queued cut passes its check
- **THEN** the home folder's queue holds `briefs/<id>`, naming the brief's path, after the cut's queue entry is gone
- **AND WHEN** that version's supervisor runs under the switch
- **THEN** its prompt names `brief=<path>`
- **AND WHEN** a version cut by hand has its supervisor run
- **THEN** its prompt names no brief

#### Scenario: A note the supervisor settles
- **WHEN** under the switch a dependent's delta halts `integrating` on a semantic conflict, the rescue diagnoses it, and the
  supervisor stages its resolution of the version's delta and writes `integrate.settled`
- **THEN** the run logs `supervise — <id>: decided · integrating · <tree>`, spawns `mf-integrate` `with settled=supervisor`,
  whose merge commit holds that tree and names the note's heading as `the supervisor`, and the version builds on and releases
  in the same run

#### Scenario: A settle outside the text
- **WHEN** the supervisor at an `integrating` halt stages a file outside `openspec/` and `docs/` Markdown
- **THEN** the version halts, naming the file, the merge and the note stay open, and the run logs no `supervise —` line
- **AND WHEN** a later run meets the same open merge's halt
- **THEN** its rescue runs, no supervisor runs, and the version stays halted for the person

### Requirement: The converge fixer leaves the plan to the person

The converge fixer, whose rules `skills/mf-converge/references/fix.md` holds, SHALL NOT edit the change's `tasks.md` or `proposal.md`, nor its
`design.md` save the prose a `drift` card names outside the `## Decisions`, `## Tests` and `## Dependencies` sections, which it
SHALL correct; it SHALL NOT edit those sections, a row of their tables, a decision's D-id or a `## ` heading, save one line it MAY
append as the last line of a `### D<n>` entry of the decisions section,
`Fix note (<YYYY-MM-DD>, <card id>): <one line>`, recording how the code now implements that decision, the entry's other lines
untouched. A card whose fix that line records SHALL be no amend card, and converge's close-out SHALL name each fix note the run
appended, by its D-id and card.

The fixer MAY also edit the change's spec delta, the files under `openspec/changes/<id>/specs/`, and the body of a `### D<n>` entry of
`design.md`'s decisions section, to say what its own fix does. It SHALL do so in the commit of the fix, which SHALL carry a `Plan-text:`
trailer naming the card ids the fix clears; it SHALL NOT change the decisions table, add or remove a decision, a `### D<n>` heading
or a `## ` heading, and SHALL NOT clear so a card of the security category whose severity is `critical` or `high`. `converge.py` SHALL
read each non-merge commit of a fix pass, after the pass and before the gate, and halt `plan edit refused — <why>` when a commit
changes a path under `openspec/changes/<id>/` other than `design.md` and `specs/`, changes a file under `specs/` or a line of a
decision's body other than a fix note with no `Plan-text:` trailer, changes the decisions table or a heading, or names a card of that
security class in its trailer. A commit that touches nothing under the change's folder, or only the prose of `design.md` outside its
decisions section or a fix note, SHALL need no trailer. The verify pass SHALL read a plan-text edit in the fix's diff, and keep a card
`fixed` only when the wording holds of the code.

A card whose fix needs any other edit of those SHALL be set `wontfix`, naming the amend the
person commits by the file's path: an **amend card**, which a checker marks `Amend: yes` and any other card `Amend: no`. A
checker SHALL mark `Amend: yes` a card whose **Fix** names the change's `tasks.md`, `proposal.md` or `design.md` by path, save a `drift` card's
naming that prose, a fix note, or the delta or a decision's body as words the fixer may write, and a security card of `critical` or `high` severity
whatever it names. A blocking amend card SHALL halt the round `amend needed — <card ids>` after the fix pass. The
verify pass SHALL keep an amend card's `wontfix` whose justification holds, and SHALL NOT turn it `accepted`; in an amend
round, it SHALL turn an amend card the amend settled, its **Still true?** check showing the defect gone, `verified`, its note
naming the amend. At the debt write,
before the debt lock, every non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?** command still shows
the defect, SHALL halt the run `amend needed — <card ids>`, writing nothing to the debt, save one *Converge keeps deferred work
in one repository debt file* lets go on; a card whose **Still true?** holds no command SHALL go to the debt unchecked. The person's
amend answers either halt.
The fixer SHALL run `plan_check.py` after its gate, as *A plan check holds the plan to the built tree* says, and SHALL write
`.minions/changes/<change-id>/fix.md` with a last line `plan check left: <subjects>` or `plan check left: none`, which
`converge.py` reads in place of the fixer's report. A verify round and the pickup check SHALL run `gate_check.py` after the gate,
and a verify round SHALL then run `plan_check.py`.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, the card reads `Amend: yes`, and the round halts
  `amend needed`

#### Scenario: Drift in the design's prose
- **WHEN** the pickup picks a `drift` card whose **Fix** names a line of the change's `design.md` outside its `## Decisions`,
  `## Tests` and `## Dependencies` sections
- **THEN** the fixer corrects that line and sets the card `fixed`; it reads `Amend: no`, and the debt write halts on nothing for it

#### Scenario: Drift in the design's tests section
- **WHEN** a `drift` card's **Fix** names a row of the change's `design.md` `## Tests` table
- **THEN** the fixer edits no row of it, sets the card `wontfix` naming the amend, and the card reads `Amend: yes`

#### Scenario: A fix that changes how a decision is built
- **WHEN** a card's fix changes how the code implements the change's D3, and D3's own words still hold
- **THEN** the fixer appends `Fix note (<date>, <card id>): <how the code now does it>` as the last line of D3's entry, edits no
  other line of it, and sets the card `fixed`
- **AND** converge's close-out names D3 and the card

#### Scenario: A fix that says what it does in the delta
- **WHEN** a card's fix changes a rule the change's spec delta states and the delta's words lag
- **THEN** the fixer edits the delta in the commit of the fix, which carries `Plan-text: <card id>`, `converge.py` takes the commit, and the verify pass judges the wording in the round that follows

#### Scenario: A decision's body, with the trailer
- **WHEN** a fix commit edits the body of the change's D3 and carries `Plan-text: <card id>`
- **THEN** `converge.py` takes it, and the commit reads as a re-plan to a stacked dependent

#### Scenario: The delta with no trailer
- **WHEN** a fix commit edits a file under the change's `specs/` and carries no `Plan-text:` trailer
- **THEN** the round halts `plan edit refused`, naming the file

#### Scenario: A plan file the fixer may not touch
- **WHEN** a fix commit edits the change's `tasks.md`, or its `proposal.md`, with or without the trailer
- **THEN** the round halts `plan edit refused`, naming the file

#### Scenario: The decisions table
- **WHEN** a fix commit edits a row of `design.md`'s decisions table, adds a `### D<n>` heading or removes one, with the trailer
- **THEN** the round halts `plan edit refused`

#### Scenario: A security card of high severity
- **WHEN** a fix commit's `Plan-text:` trailer names a card of the security category whose severity is `high`
- **THEN** the round halts `plan edit refused`, and the card is left to the halt `amend needed`

#### Scenario: Drift in the prose and a fix note need no trailer
- **WHEN** a fix commit edits `design.md` outside its decisions section, or appends a fix note, and touches nothing else under the change's folder
- **THEN** `converge.py` takes it with no trailer

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup's fixer sets a `drift` card `wontfix`, naming an amend of a decision in the change's `design.md`
- **THEN** the pickup check keeps it `wontfix`, and the debt write halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** the debt write halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** command shows the defect gone at the debt write
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

### Requirement: One module writes and parses the models file

`skills/mflib/modelsfile.py` SHALL be the one writer and parser of `.minions/changes/<change-id>/models.toml`: the map of its tables and keys, the text `brief_check.py --models` prints, the parser, each key's reader, the token rule, the hash and the write. `brief_check.py` and `conduct.py` SHALL go through it; `conduct.py` SHALL keep each station's executor, model and effort defaults, the comparison with the plan and its child run of `brief_check.py`. The module SHALL find the file through `skills/mflib/layout.py`. The models line's grammar SHALL stay `brief_check.py`'s, and its `cut` part SHALL write no table: the cut's model goes on `conduct.py cut`'s own arguments.

The module's one map SHALL name `rescue` and `supervise`, each a model and an effort with no host, among the parts a models line writes, after `fix`, as the `[rescue]` and `[supervise]` tables; it SHALL name `auto_grant` as the person's key, which a tool reads and never writes. A key the map does not name SHALL be ignored, `tier` among them, and `[converge.review]` and `[converge.security]` SHALL be read no more. Every `model` and `effort` of every table of the map SHALL be letters, digits, `.`, `_` and `-` alone, and a table that holds another word SHALL halt its version, naming the table and the word. `brief_check.py` SHALL take `rescue` and `supervise` as optional parts, after `fix` and before an optional last `shadow`, each of three words and with no host, and SHALL halt a part out of that order or with a host.

The module's read SHALL follow no link, not block, take a regular file alone, read at most `65,536` bytes and decode them strictly. A missing file SHALL be no file, and a version with none SHALL run on the defaults; a link, a dangling link, a pipe, a folder, a file over the bound, a byte that is not UTF-8 and text that is not TOML SHALL each be a broken file. A broken file SHALL halt its version alone, wherever the run plans or takes it, naming the file and why, and SHALL fail the cut's check naming it. `conduct.py status` SHALL name it after the version's line and go on, and the viewer SHALL read no skip from it. The hash the cut's check compares SHALL be taken over the bytes of that read.

The module's write SHALL go through the staged write under the change folder's descriptor and refuse a link; a failed write SHALL stop `conduct.py cut` with exit 2. `brief_check.py --models <brief> <slug> --write <change-id>` SHALL run the parse `--models` runs, then write its text through the module in the current directory's repository, and print `brief: wrote .minions/changes/<change-id>/models.toml`; its exits SHALL be `--models`', and 2 for a failed write.

#### Scenario: A bad byte in a models file
- **WHEN** a version's models file holds a byte that is not UTF-8 and another version is open
- **THEN** the run halts the first version, naming the file, and the other version goes on

#### Scenario: Text that is not TOML
- **WHEN** a version's models file holds `[converge`
- **THEN** the run halts that version at its take, and the plan reads no skip from it

#### Scenario: A link, a pipe or a folder at the file
- **WHEN** a link, a pipe or a folder stands at `.minions/changes/<id>/models.toml`
- **THEN** the version halts naming the file, no read blocks, and a cut's check fails naming it

#### Scenario: A file over the bound
- **WHEN** a version's models file is `65,537` bytes
- **THEN** the version halts naming the file, and the file is not parsed

#### Scenario: No models file
- **WHEN** a change's folder holds no `models.toml`
- **THEN** each station of the version runs on the defaults, and the cut's check fails as no models file

#### Scenario: A word that is no token
- **WHEN** a version's `[build]` table holds `model = "TMPDIR=/tmp/mf-codex-x"`
- **THEN** the version halts naming `build` and the word, and no worker starts on it

#### Scenario: An old checker table
- **WHEN** a version's models file holds `[converge.review]` and no `[converge.conformance]`
- **THEN** conformance runs on the checkers' defaults, and `[converge.review]` is read for nothing

#### Scenario: A key the map does not name
- **WHEN** a version's `[converge]` table holds `tier = "high"`
- **THEN** the key is ignored, and no table of the file is refused for it

#### Scenario: A rescue and a supervise part
- **WHEN** a brief's models line ends `… · fix claude-sonnet-5-5 medium · rescue claude-sonnet-5-5 high · supervise claude-opus-5-5 high`
- **THEN** `brief_check.py --models` prints `[rescue]` and `[supervise]` tables, each with `model` and `effort` and no `executor`, after `[converge.fix]`

#### Scenario: A rescue part before fix
- **WHEN** a models line names `rescue` before `fix`
- **THEN** `brief_check.py` halts the line out of shape

#### Scenario: A supervise part with a host
- **WHEN** a models line names `supervise codex/gpt-6.1-sol high`
- **THEN** `brief_check.py` halts, naming that `supervise` takes no host

#### Scenario: A line with neither part
- **WHEN** a models line names no `rescue` and no `supervise`
- **THEN** the file holds neither table, and the rescue runs on `[build]`'s models and the supervisor on its defaults, as before

#### Scenario: A status read of a broken file
- **WHEN** `conduct.py status` runs and a version's models file is not UTF-8
- **THEN** that version's line keeps its stage and gains ` — changes/<id>/models.toml: it is not UTF-8`, and the command exits 0

#### Scenario: A link where the write lands
- **WHEN** a link stands at `.minions/changes/<id>/models.toml` and the run writes the entry's text
- **THEN** the cut stops with exit 2 naming the file, and the link's target is unchanged

#### Scenario: A hard link at the file
- **WHEN** the file has a second name and the run writes the entry's text
- **THEN** the name holds the new text and the other name keeps its old bytes

#### Scenario: The attended cut's writer
- **WHEN** `brief_check.py --models <brief> a --write 0001-a` runs on a brief whose item `a` names its models
- **THEN** `.minions/changes/0001-a/models.toml` holds what `--models` prints, and the command prints `brief: wrote .minions/changes/0001-a/models.toml`

#### Scenario: The writer's flag beside no `--models`
- **WHEN** `brief_check.py <brief> --write 0001-a` runs
- **THEN** it exits 2 and writes nothing

## ADDED Requirements

### Requirement: A plan review asks what else produces a rule's subject

The question of the cut's plan review, which `skills/mf-cut-change/SKILL.md` gives the reviewer in its packet, SHALL cover, beside whether each task can be built as written, each requirement the change's delta adds or changes and each rule a decision of `design.md` states: what else produces the thing the rule judges — the build's commits, a fix commit, an amend, the release's edits and a generated file — and what the plan exempts. A doubt it finds SHALL return to the cutter as every doubt does. A plan that adds or changes no such requirement and states no such rule SHALL be passed over by this part of the question.

#### Scenario: A plan with a new requirement
- **WHEN** the cut's delta adds a requirement that judges a file the build, a fix or the release also writes
- **THEN** the packet's question asks what else produces that file and what the plan exempts, and a doubt the reviewer finds goes back to the cutter

#### Scenario: A plan with no such rule
- **WHEN** the cut's delta adds or changes no requirement and no decision states a rule
- **THEN** the reviewer passes over that part of the question, and the packet's other part stands

### Requirement: A fixer's plan-text commit re-plans a stacked dependent

The stack's re-plan test of `conduct.py`, which resets a stacked version whose dependency re-planned past it, SHALL read a fix commit that carries a `Plan-text:` trailer and changes the body of a decision of the dependency's `design.md` as it reads an amend of the change directory: as a re-plan. A fix commit that changes no decision's body, with or without the trailer, SHALL be no re-plan.

#### Scenario: A dependency whose fix edited a decision's body
- **WHEN** a version stacked on a dependency's built head and the dependency's fix commit, carrying `Plan-text:`, edits the body of a decision
- **THEN** the stacked version is reset, and the run says the dependency re-planned past its head

#### Scenario: A dependency whose fix edited the delta alone
- **WHEN** the dependency's fix commit carries `Plan-text:` and edits a file under the change's `specs/` alone
- **THEN** the stacked version is not reset for it

### Requirement: Row V7 passes over a command row I19 refuses

The cut's check, `cut_check.py`, SHALL pass over, in its row `V7`, a `Verify:` command whose first word is `cd`, a loop keyword or a shell assignment, the words `verify_check.py` refuses at the start of a command under `I19`. Row `V7` SHALL halt any other first word that is no program on `PATH`, no file of the tree and no path a sub-task names, and `I19` SHALL halt each command it refuses. The two rows SHALL read the same on every host, whether `PATH` holds a program of that name or not.

#### Scenario: A command that starts with cd
- **WHEN** a `Verify:` command is `cd x` and `PATH` holds a `cd` program
- **THEN** `cut_check.py` halts `I19` alone

#### Scenario: A command that starts with cd on a host with no such program
- **WHEN** a `Verify:` command is `cd x` and `PATH` holds no `cd` program
- **THEN** `cut_check.py` halts `I19` alone, as on the other host

#### Scenario: A first word that names nothing
- **WHEN** a `Verify:` command's first word is `nothing-here`
- **THEN** `cut_check.py` halts `V7`, naming the word
