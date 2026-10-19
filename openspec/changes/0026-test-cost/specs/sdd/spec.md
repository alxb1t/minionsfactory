## ADDED Requirements

### Requirement: The build owns the rules for tests, and the cut and converge carry them

`skills/mf-build/SKILL.md` SHALL own the rules for tests: a `## Rules for tests` section whose table rows are the
rules, one per row, the first cell holding the rule's id in bold (`**T1**`). `skills/mf-cut-change/SKILL.md` and
`skills/mf-converge/SKILL.md` SHALL each carry a `## Rules for tests` section with a row for the same ids. The id
sets SHALL be equal, non-empty, and numbered from `T1` with no gap.

#### Scenario: The three skills carry the same test-rule ids
- **WHEN** the ids are read from the first cell of each table row in the `## Rules for tests` section of
  `mf-build`, `mf-cut-change` and `mf-converge`
- **THEN** each carrier's set equals `mf-build`'s, and none is empty
- **AND** each runs from `T1` upward with no number missing

### Requirement: A test is deleted or merged only as the design's table names it

`skills/mf-build/SKILL.md` SHALL treat a test deleted or merged as the change's `design.md` `## Tests` table names it
as consolidation, not as weakening the gate, and SHALL halt on a deletion outside that table. The fix station in
`skills/mf-converge/SKILL.md` SHALL never delete or merge a test.

#### Scenario: The build names the table, and the fix station never deletes
- **WHEN** `mf-build` and `mf-converge` are scanned
- **THEN** `mf-build`'s `## Step 2 — The per-phase ritual` names `` `## Tests` table ``
- **AND** `mf-converge`'s `## Step 6 — The fix station (one subagent, inside this loop)` names
  `never deletes or merges a test`

### Requirement: Review judges test cost and traced coverage

The review station SHALL run a **test-cost pass** after its engine, carding each new end-to-end test that a lower
layer proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When
the freeze removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to
the test that runs it now against the design's `## Tests` table. Each round SHALL run both passes over that round's
freeze. The station SHALL say in its Summary that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that
it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `test-cost pass` at least twice
- **AND** it names `coverage-trace pass` at least twice

### Requirement: The release records the gate's time

`skills/mf-release/SKILL.md` SHALL time precondition 1's gate run and SHALL write one `Gate:` line under the new
release heading in `CHANGELOG.md`: that time, CI's latest green run on the default branch read with `gh run list`
or `none`, and the previous release's `Gate:` line's times.

#### Scenario: The release names the line and the CI read
- **WHEN** `skills/mf-release/SKILL.md` is scanned
- **THEN** it names `Gate: local`
- **AND** it names `gh run list`

### Requirement: The bootstrap's `CLAUDE.md` states the rules for tests

`skills/mf-bootstrap/templates/CLAUDE.md.tmpl` SHALL hold a `## Tests` section stating where a test goes, that a
step in an existing test comes before a new one, which engines a test runs on, and that a test is deleted or merged
only as a change's `## Tests` table names it.

#### Scenario: The template has the section
- **WHEN** `skills/mf-bootstrap/templates/CLAUDE.md.tmpl` is read
- **THEN** one of its lines is `## Tests`

## MODIFIED Requirements

### Requirement: A fix's test fails without the fix

For a card whose fix size includes `a test`, the fix station SHALL paste the new or extended test's failing run from
before the fix into the card's **Status** note; an extended test's run is the existing test with the new step added.
The verify pass SHALL reopen the card when that run is missing, or when the test does not exercise the card's
**When you'd hit it** scenario. Fixes to docs only are exempt.

#### Scenario: Converge names the red run and the verifier's check
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `failing run from before the fix`
- **AND** it names `When you'd hit it` in the verify step
