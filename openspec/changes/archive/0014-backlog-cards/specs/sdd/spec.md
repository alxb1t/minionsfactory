## ADDED Requirements

### Requirement: Converge and the export share one card shape

`skills/mf-converge/SKILL.md` SHALL own the card: a `## The card` section whose table rows are the card's
fields, one per row, the first cell holding the field's label in bold (`**Why it's a problem**`).
`skills/mf-backlog-export/SKILL.md` SHALL carry a `## The card` section with a row for the same labels. Both
label sets SHALL be equal and non-empty.

#### Scenario: Both skills carry the same card fields
- **Key:** `sdd:backlog-cards:fields-agree`
- **Layers:** unit
- **WHEN** the labels are read from the first cell of each table row in the `## The card` section of both skills
- **THEN** both sets are equal and non-empty
