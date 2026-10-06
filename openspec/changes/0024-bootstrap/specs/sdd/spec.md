## ADDED Requirements

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md` and
`README.md`. A template's target path SHALL be its path under `templates/` without the `.tmpl` suffix. The
`Makefile` template's `gate` recipe SHALL run `openspec validate --all --strict --no-interactive`.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md` and `README.md` have templates

#### Scenario: The gate template validates the specs
- **WHEN** the `Makefile` template is read
- **THEN** it names `openspec validate --all --strict --no-interactive`
