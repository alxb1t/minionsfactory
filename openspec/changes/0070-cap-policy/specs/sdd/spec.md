## ADDED Requirements

### Requirement: A run grants one round at a small cap, and halts a large one for a re-plan

When a version's converge halts with `cap reached` in a run, `conduct.py` SHALL read the open blocking findings in its review and
security findings files — review's `blocking`, security's `critical` and `high`, each `Status: open` — and, when every one's fix is
sized `one line`, `a test` or `one line and a test`, no granted round reached the cap — its converge run is not marked `· grant`,
and the run has not granted the version already — and its models
file's `[converge]` table does not say `auto_grant = false`, SHALL spawn converge with `grant=yes` itself, writing no grant file and
starting no rescue, log `grant — <id>: automatic · <ids>`, and check the round as it checks a person's grant's. Otherwise — a blocker sized `a design change`, no open blocking card read, a granted
round's cap, automatic or a person's, in this run or an earlier one, a second cap in the run, or `auto_grant = false` — the run SHALL write the version a last halt line, `re-plan: <ids>`, and the version's rescue SHALL
diagnose it, naming `/mf-plan` with the version's brief as the way back. A person's grant SHALL still spend a round on a re-plan
halt. `mf-converge` run by hand grants nothing on its own.

#### Scenario: A small cap
- **WHEN** a version caps with open blockers sized `one line` and `a test`
- **THEN** the run logs `grant — <id>: automatic`, converges one more round, writes no `.minions/grants/<id>`, and releases the
  version in the same run when that round is clean

#### Scenario: A design change at the cap
- **WHEN** an open blocker at the cap is sized `a design change`
- **THEN** no grant is spent, and the version halts as `re-plan`, its rescue naming `/mf-plan`

#### Scenario: The granted round blocks again
- **WHEN** the automatically granted round ends with a blocker open
- **THEN** the version halts as `re-plan`, and no second automatic grant is spent
- **AND WHEN** a later run reads that cap
- **THEN** it halts the version as `re-plan` and spawns no converge

#### Scenario: The granted round ends unfinished
- **WHEN** the automatically granted round's converge exits 0 with its status log not on `done`
- **THEN** the run logs the converge check's failure and halts the version, spawning no other converge

#### Scenario: Turned off
- **WHEN** the version's models file says `[converge] auto_grant = false`
- **THEN** its cap halts as `re-plan` with no automatic grant
