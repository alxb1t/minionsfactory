## MODIFIED Requirements

### Requirement: Converge keeps deferred work in one repository backlog

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/backlog.md`, under a heading for its change. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, fix them, and verify them in a normal
round. It SHALL NOT name a per-version backlog file. It SHALL delete a backlog card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and verifies them in a normal round

#### Scenario: Converge writes the backlog
- **WHEN** the loop ends clean with non-blocking cards still not `verified`
- **THEN** converge writes each one whose **Still true?** check still shows the defect, and whose id is not yet in
  the backlog, to `.minions/backlog.md` under its change's heading, and to no per-version file
- **AND** it names each moot card, whose check shows the defect gone, in its report
- **AND** it deletes an older card only when a verified repeat of it fixed the defect and its **Still true?**
  check shows the defect gone
