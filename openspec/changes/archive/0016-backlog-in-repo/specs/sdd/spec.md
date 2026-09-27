## ADDED Requirements

### Requirement: Converge keeps deferred work in one repository backlog

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix to one file, `.minions/backlog.md`,
under a heading for its change. After both verdicts are clean, and only while a round remains under the cap, it
SHALL pick up this run's non-blocking cards whose fix is sized `one line` or `a test`, fix them, and verify them in
a normal round. It SHALL NOT name a per-version backlog file.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **Key:** `sdd:repo-backlog:converge-writes-one-file`
- **Layers:** unit
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
- **Key:** `sdd:repo-backlog:release-does-not-read`
- **Layers:** unit
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-cut-change/SKILL.md` are scanned
- **THEN** `mf-release` does not name `_backlog.md`
- **AND** `mf-release` names `.minions/backlog.md`
- **AND** `mf-release` and `mf-cut-change` each name `backlog:`

### Requirement: The card is defined in converge alone

`skills/mf-converge/SKILL.md` SHALL own the card: a `## The card` section whose table rows are the card's fields,
one per row, the first cell holding the field's label in bold (`**Why it's a problem**`). No other shipped skill
SHALL carry a `## The card` section.

#### Scenario: Only converge carries the card
- **Key:** `sdd:backlog-cards:fields-agree`
- **Layers:** unit
- **WHEN** every `skills/*/SKILL.md` is scanned for a `## The card` section
- **THEN** `mf-converge` carries one, with at least one label
- **AND** no other skill carries one

### Requirement: The backlog export is named nowhere

No shipped code, role prompt, skill or doc SHALL name `mf-backlog-export`. The scan SHALL cover the same root set
as the retired-vocabulary scans, and exclude the specs, `tests/`, and the historical record (`CHANGELOG.md`,
`openspec/changes/archive/`).

#### Scenario: The retired export is named nowhere in code, prompts, skills or docs
- **Key:** `sdd:retired-export:named-nowhere`
- **Layers:** unit
- **WHEN** the shared root set is scanned for `mf-backlog-export`
- **THEN** no file names it
- **AND** a mention planted in each root is reported

## REMOVED Requirements

### Requirement: Converge and the export share one card shape

**Reason**: `mf-backlog-export` is deleted, so only one skill carries the card. Its scenario key moves to *The card
is defined in converge alone*.
**Migration**: none. The card stays in `skills/mf-converge/SKILL.md`, unchanged.
