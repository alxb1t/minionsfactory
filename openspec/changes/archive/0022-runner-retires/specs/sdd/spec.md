## MODIFIED Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **WHEN** every `skills/*/SKILL.md` is scanned
- **THEN** no file names `minions.toml`
- **AND** `mf-build`, `mf-converge` and `mf-release` each name both `make gate` and `make -n gate`

### Requirement: The cut and the build share one input contract

`skills/mf-build/SKILL.md` SHALL own the input contract: a `## Input contract` section whose table rows are
the items a change must meet, one per row, the first cell holding the item's id in bold (`**I1**`).
`skills/mf-cut-change/SKILL.md` SHALL carry a `## Input contract` section with a row for the same ids. The two
id sets SHALL be equal, non-empty, and numbered from `I1` with no gap.

#### Scenario: The two skills carry the same contract ids
- **WHEN** the ids are read from the first cell of each table row in the `## Input contract` section of both
  skills
- **THEN** the two sets are equal and non-empty
- **AND** they run from `I1` upward with no number missing

### Requirement: A release may skip the check loop, and says so

`skills/mf-release/SKILL.md` SHALL release a change for which no findings file exists, and SHALL state the skip
as the line `converge: skipped — no findings files`. It SHALL NOT carry the rule that a missing findings file is
not clean; that rule SHALL stay in `skills/mf-converge/SKILL.md`, which judges its own stations by it.

#### Scenario: The release names the skip, and the missing-file rule lives in converge only
- **WHEN** `mf-release` and `mf-converge` are scanned
- **THEN** `mf-release` names `converge: skipped — no findings files`
- **AND** `mf-release` does not name `A missing findings file is not clean`
- **AND** `mf-converge` names `A missing findings file is not clean`

### Requirement: The build and the cut share one list of prose rules

`skills/mf-build/SKILL.md` SHALL own the prose rules: a `## Prose rules` section whose table rows are the rules,
one per row, the first cell holding the rule's id in bold (`**P1**`). `skills/mf-cut-change/SKILL.md` SHALL
carry a `## Prose rules` section with a row for the same ids. The two id sets SHALL be equal, non-empty, and
numbered from `P1` with no gap.

#### Scenario: The two skills carry the same prose-rule ids
- **WHEN** the ids are read from the first cell of each table row in the `## Prose rules` section of both
  skills
- **THEN** the two sets are equal and non-empty
- **AND** they run from `P1` upward with no number missing

### Requirement: Converge keeps deferred work in one repository backlog

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix to one file, `.minions/backlog.md`,
under a heading for its change. After both verdicts are clean, and only while a round remains under the cap, it
SHALL pick up this run's non-blocking cards whose fix is sized `one line` or `a test`, and every `drift` card, fix
them, and verify them in a normal round. It SHALL NOT name a per-version backlog file. It SHALL delete a backlog card
only when a verified repeat of it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `.minions/backlog.md`
- **AND** it names both pickup sizes, `one line` and `a test`
- **AND** it does not name `_backlog.md`

### Requirement: The release does not read the backlog

`skills/mf-release/SKILL.md` SHALL NOT hold a release on deferred work. It SHALL name no per-version backlog file.
A paydown change lists the card ids it closes under the `backlog:` key of its `proposal.md` frontmatter:
`skills/mf-cut-change/SKILL.md` SHALL write that key, and `mf-release` SHALL delete exactly those cards from
`.minions/backlog.md` after the fold.

#### Scenario: The release names no per-version backlog, and the paydown key is shared
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-cut-change/SKILL.md` are scanned
- **THEN** `mf-release` does not name `_backlog.md`
- **AND** `mf-release` names `.minions/backlog.md`
- **AND** `mf-release` and `mf-cut-change` each name `backlog:`

### Requirement: The card is defined in converge alone

`skills/mf-converge/SKILL.md` SHALL own the card: a `## The card` section whose table rows are the card's fields,
one per row, the first cell holding the field's label in bold (`**Why it's a problem**`). No other shipped skill
SHALL carry a `## The card` section.

#### Scenario: Only converge carries the card
- **WHEN** every `skills/*/SKILL.md` is scanned for a `## The card` section
- **THEN** `mf-converge` carries one, with at least one label
- **AND** no other skill carries one

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, counted against the cap, with no
pickup.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-converge/SKILL.md` are scanned
- **THEN** `mf-release` names the check `HEAD equals the head:`
- **AND** `mf-converge` names `catch-up round`

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/SKILL.md` SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `blocking | drift | nit`
- **AND** it names each anchor: `data loss`, `spend`, `exposure`, `silent wrong output`

### Requirement: A repeated finding escalates

Each station SHALL read `.minions/backlog.md`. A finding that repeats a backlog card SHALL name that card's id in its
**Related** field as `repeat of <id>`, and SHALL go up one level: security by one step, a review `nit` or `drift` to
`blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `repeat of`
- **AND** it names `up one level`

### Requirement: Review searches for stale claims

The review station SHALL run a **stale-claim pass** after its engine: every path, symbol, verb, route or count the
diff renames, deletes or changes is searched across the rest of the tree, and each mention the change made false is
carded as `drift`. The station SHALL say in its Summary that the pass ran, and `skills/mf-converge/SKILL.md` SHALL
check that it did.

#### Scenario: Converge names the stale-claim pass
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `stale-claim pass` at least twice: where the station runs it and where the conductor checks it

### Requirement: A fix's test fails without the fix

For a card whose fix size includes `a test`, the fix station SHALL paste the new test's failing run from before the
fix into the card's **Status** note. The verify pass SHALL reopen the card when that run is missing, or when the test
does not exercise the card's **When you'd hit it** scenario. Fixes to docs only are exempt.

#### Scenario: Converge names the red run and the verifier's check
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `failing run from before the fix`
- **AND** it names `When you'd hit it` in the verify step

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `backlog`, `halt` and `done`, and a
run SHALL end on `halt` or `done`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `_status_log.md`
- **AND** it names `newest on top`
- **AND** it names each event: `start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`,
  `backlog`, `halt`, `done`

### Requirement: A skill infers the one active change

`skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL take `change-id`
from their parameter when one is given. When none is given, each SHALL take the candidates from
`git ls-files openspec/changes/`, without `archive/`: no candidate SHALL halt with `no active change`, several SHALL
halt listing them, and exactly one SHALL be used only if the current branch equals `v<version>_<slug>` built from
that change's `proposal.md` `version:` and its id, else halt naming both. The skill SHALL echo the id with
`(inferred:` before any other work, and SHALL NOT forbid inference.

#### Scenario: Build, converge and release each name the inference and its halts
- **WHEN** `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` are scanned
- **THEN** each names `git ls-files openspec/changes/`
- **AND** each names `no active change`
- **AND** each names `(inferred:`
- **AND** none names `Never infer it`

## REMOVED Requirements

### Requirement: Enforced binding

**Reason**: the spec↔test binding is deleted; specs are bound by review, not by a checker (D36).

**Migration**: none. A scenario's test is named in the change's `tasks.md` and judged by review.

### Requirement: Reviewer conformance

**Reason**: the runner's reviewer role is deleted; `mf-converge` review judges whether a delta is implemented and tested.

**Migration**: none. Run `mf-converge`.

### Requirement: Release fold

**Reason**: the runner's release station is deleted; `mf-release` folds the delta.

**Migration**: none. Run `mf-release`.

### Requirement: Change structure

**Reason**: the runner's change reader is deleted; `mf-build`'s input contract `I1`…`I15`, written by `mf-cut-change`, states a change's shape.

**Migration**: none. Cut with `mf-cut-change`.

### Requirement: Repository is the source of truth for change progress

**Reason**: the runner's driver and its retired-vocabulary scans are deleted; `mf-build` reads progress from `tasks.md`, and no test asserts an absence (D37).

**Migration**: none.

### Requirement: Full backfill traceability

**Reason**: the spec↔test binding is deleted, and the `spec` and `spec_exempt` markers with it (D36).

**Migration**: none. Tests carry no marker.

### Requirement: Commit-to-change traceability

**Reason**: the runner's release gate, the one check of the trailer, is deleted; D21 keeps the trailer as a convention `mf-build` writes.

**Migration**: none. Commits keep the `Change:` trailer.

### Requirement: The retired gate config is named nowhere

**Reason**: no test asserts an absence (D37); a retired name leaves the tree in the commit that retires it.

**Migration**: none.

### Requirement: The backlog export is named nowhere

**Reason**: no test asserts an absence (D37); a retired name leaves the tree in the commit that retires it.

**Migration**: none.
