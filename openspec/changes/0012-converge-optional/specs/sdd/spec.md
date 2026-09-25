## ADDED Requirements

### Requirement: A release may skip the check loop, and says so

`skills/mf-release/SKILL.md` SHALL release a change for which no findings file exists, and SHALL state the skip
as the line `converge: skipped — no findings files`. It SHALL NOT carry the rule that a missing findings file is
not clean; that rule SHALL stay in `skills/mf-converge/SKILL.md`, which judges its own stations by it.

#### Scenario: The release names the skip, and the missing-file rule lives in converge only
- **Key:** `sdd:converge-optional:skip-is-stated`
- **Layers:** unit
- **WHEN** `mf-release` and `mf-converge` are scanned
- **THEN** `mf-release` names `converge: skipped — no findings files`
- **AND** `mf-release` does not name `A missing findings file is not clean`
- **AND** `mf-converge` names `A missing findings file is not clean`
