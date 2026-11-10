## MODIFIED Requirements

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. One `stamp.py` call MAY write several events, each its
own line, inserted so the last given is on top; the conductor SHALL write in one call the events it has with no command
between them. `stamp.py` SHALL exit 2, writing nothing, on a call that gives `done` or `halt` before another event, and on any
event for a run whose top line is `done`, or `halt` naming neither `.minions/debt.lock` nor `.minions/backlog.lock`: an event after
one needs a new `## Run` heading. A `halt` naming a lock takes the events of the converge that resumes it. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `shadow`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor, model and effort a mailbox checker's answer names, else the executor the conductor runs
on and the model and effort its worker was given, `default` where none, and `tokens` the worker's figure or `unavailable`. A
`shadow` line SHALL hold `overlap.py`'s line, or a shadow checker's failure. An adversarial head written by rule SHALL write one
`by rule` line, `no surface`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: Several events in one call
- **WHEN** `stamp.py` is given the events `round 1 · verdicts — conformance …` and `round 1 · verdicts — adversarial …`
- **THEN** the log holds both lines under the latest heading, adversarial's on top, each with the clock's time

#### Scenario: A round's verdicts
- **WHEN** a round's conformance and adversarial files are read, each written by its worker
- **THEN** the log holds one `verdicts` line for each role, each naming the executor, and the model and effort that role's
  worker was given

#### Scenario: A mailbox checker's verdicts
- **WHEN** conformance ran through the mailbox and its answer reads `exit 0 · executor codex · model gpt-6.1-sol · effort high`
- **THEN** its `verdicts` line ends `executor codex · model gpt-6.1-sol · effort high · tokens unavailable`

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A debt and a done in one call
- **WHEN** `stamp.py` is given the events `round 1 · debt — …` and then `round 1 · done — …`
- **THEN** the log holds both lines under the latest heading, `done` on top

#### Scenario: A done given before another event
- **WHEN** `stamp.py` is given the events `round 1 · done — …` and then `round 1 · debt — …`
- **THEN** it exits 2 with `stamp: cannot stamp — done goes last in a call`, and the log is unchanged

#### Scenario: An event after a run's end
- **WHEN** the latest run's top line is a `done`, or a `halt` naming no lock, and `stamp.py` is given an event
- **THEN** it exits 2 with `stamp: cannot stamp — the run ends on <event>: open a ## Run for a new event`, and the log is unchanged

#### Scenario: An event under a lock halt
- **WHEN** the latest run's top line is a `halt` naming `.minions/debt.lock`, and `stamp.py` is given the event `round 2 · debt — …`
- **THEN** the log holds the line under the latest heading, above the `halt`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** `surfaces.py` exits 0 in a verify round
- **THEN** the log holds one `by rule` line, `no surface`, the round's `fan-out` names conformance alone, and its one
  `verdicts` line is conformance's

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when the worker exits 0 and its check on disk passes — never on the worker's report. The converge
check SHALL need `done` as the newest run's latest status-log event. A newest run whose top line is no `halt` and holds a `done`
below it SHALL pass the check when both findings files are clean at `HEAD` and the tree is clean, after the check stamps `done`
again, `re-stamped by the run`, and logs it. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt, save a usage
limit, which halts only what runs on its executor. The scratch
gate's recipe SHALL try a write to a file `conduct.py` made outside the worker's reach, and SHALL pass only when that write is
refused; `conduct.py` SHALL halt the run when the file changed, and SHALL remove it. The recipe SHALL also pass only
when the shell's `uname -m` is the host's native architecture, so a worker whose shell runs translated halts the run, naming
its executor. A Codex probe worker SHALL also run `git write-tree` in a linked worktree of its scratch repo, and SHALL pass only
when it wrote the tree that command prints there. A Codex probe that passes SHALL then run one conformance checker over a
fixture change in a second scratch
repo, and SHALL pass only when the checker leaves `.minions/changes/0001-probe/conformance.md`, a file and no link, whose
frontmatter holds every key of the findings file contract, `type: conformance` and `plan: 0001-probe`, and when its log holds
a usage event; the checker's verdict SHALL be logged and never judged.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

#### Scenario: A worker dies after clean findings
- **WHEN** a converge worker exits 1 with both findings files clean at `HEAD` and no `done` in its status log
- **THEN** the version halts, naming the exit, and nothing is released

#### Scenario: A done under the top line
- **WHEN** the newest run's top line is a `debt` with a `done` below it, both findings files are clean at `HEAD` and the tree is clean
- **THEN** the converge check stamps `done` again, `re-stamped by the run`, logs it and passes, and the version goes on to release
- **AND WHEN** a findings file is not clean at `HEAD`
- **THEN** the check fails on that file and stamps nothing

#### Scenario: A probe worker runs unsandboxed
- **WHEN** the probe worker's write outside its reach lands
- **THEN** the run halts naming the probe's executor, no version starts a worker, and the file is gone

#### Scenario: A worker's shell runs translated
- **WHEN** the probe worker's shell reports `x86_64` on an `arm64` host
- **THEN** the run halts, naming the executor and both architectures, and no version starts a worker

#### Scenario: A Codex checker probe writes no findings file
- **WHEN** a Codex probe passes its scratch edit, and its checker exits 0 leaving no `conformance.md`
- **THEN** the probe fails, naming the missing file, and no station runs on Codex
- **AND WHEN** the checker leaves a findings file with every contract key and `verdict: clean` over the fixture's defect
- **THEN** the probe passes, and its check line names the verdict

#### Scenario: A Codex probe cannot write a linked worktree's index
- **WHEN** a Codex probe worker edits, commits and gates its scratch repo, and leaves no tree written in the linked worktree
- **THEN** the probe fails, naming `git write-tree`, and no station runs on Codex

### Requirement: A test is deleted or merged only as the design's table names it

`skills/mf-build/SKILL.md` SHALL treat a test deleted or merged as the change's `design.md` `## Tests` table names it
— each removed test mapped to the remaining test that carries its assertions and scenario ids, to a decision
in force at the base that retires it, or, when its proofs cover only a requirement the change's delta removes, to that
requirement removed with the code under test — as consolidation, not as weakening the gate, and SHALL halt on a deletion outside that table.
`skills/mf-cut-change/SKILL.md` SHALL write that table for every test a change deletes or merges. The fix station
in `skills/mf-converge/SKILL.md` SHALL never delete or merge a test.

#### Scenario: The build names the table, and the fix station never deletes
- **WHEN** a phase deletes a test that `design.md`'s `## Tests` table maps to a decision in force at the base that retires it
- **THEN** `mf-build` treats the deletion as consolidation and does not halt

#### Scenario: A deletion with its requirement
- **WHEN** a phase deletes a test whose proofs cover only a requirement the change's delta removes, with the code under test, and the table names that requirement
- **THEN** `mf-build` treats the deletion as consolidation and does not halt

#### Scenario: A deletion outside the table
- **WHEN** a phase deletes a test the table does not name
- **THEN** `mf-build` halts: the gate would be weakened

#### Scenario: A fix pass meets a test
- **WHEN** the fix station clears a finding
- **THEN** it deletes and merges no test

### Requirement: Conformance judges test cost and traced coverage

The conformance station SHALL run a **test-cost pass** after its sections, carding each new end-to-end test that a lower layer
proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When the freeze
removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to the test that runs it
now, to the decision, in force at the base, that the design's `## Tests` table names as retiring it, or to the requirement the
change's delta removes, with the code under test, that the table names. A proof carried by
none SHALL be `blocking`. Each round SHALL run both passes over that round's freeze. The station SHALL say in its Summary
that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** a conformance findings file's Summary does not say the test-cost pass ran, or the coverage-trace pass ran or the
  freeze removed no test
- **THEN** `mf-converge` treats it as a scope failure and halts

#### Scenario: The freeze removes a test the table retires
- **WHEN** the freeze removes a test that the `## Tests` table maps to a decision in force at the base
- **THEN** the coverage-trace pass accepts the removal and cards nothing for it

#### Scenario: The freeze removes a test with its requirement
- **WHEN** the freeze removes a test whose proofs cover only a requirement the change's delta removes, and the `## Tests` table names that requirement
- **THEN** the coverage-trace pass accepts the removal and cards nothing for it

#### Scenario: A proof carried by neither
- **WHEN** a removed assertion maps to no remaining test, no retiring decision and no removed requirement
- **THEN** conformance cards it `blocking`
