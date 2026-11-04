## ADDED Requirements

### Requirement: The build runs a quick check between phases

`skills/mf-build/SKILL.md` SHALL end each phase but its last on a green `make check` when `make -n check` exits 0, and on a green
gate otherwise; its last phase SHALL end on a green gate. The input contract's `I8` SHALL read "each phase ends on a green
`make check`, the last on a green gate".

#### Scenario: A repo with a check target
- **WHEN** a target's `Makefile` has a `check` target, and a change has three phases
- **THEN** the build runs `make check` after phases 1 and 2, and the gate after phase 3

#### Scenario: A repo without one
- **WHEN** `make -n check` exits non-zero
- **THEN** the build runs the gate after every phase, as before

### Requirement: The conductor scans a push for secrets

Before it pushes, `conduct.py` SHALL scan each pushed range with `betterleaks git`, from a scratch repo that borrows the primary's
objects and reads no repo config or attributes, and SHALL halt the run on a hit, naming the rule, the file and the commit, the
secret redacted, pushing nothing. A run SHALL stop at its start when `betterleaks` is not on `PATH`, naming its install.

#### Scenario: A secret in the push range
- **WHEN** a release's commits hold a string a Betterleaks rule matches
- **THEN** the run halts before any push, naming the rule, the file and the commit, and the secret is not in the log

#### Scenario: No Betterleaks
- **WHEN** `betterleaks` is not on `PATH`
- **THEN** `conduct.py run` exits 2, naming its install, and starts no worker

## MODIFIED Requirements

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md`, `README.md`,
`CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and `docs/decisions.md`. A template's target path SHALL
be its path under `templates/` without the `.tmpl` suffix. The `Makefile` template's `gate` recipe SHALL run
`openspec validate --all --strict --no-interactive` and `betterleaks dir . --no-banner --redact`, and its `check` recipe the
same lines but the scan.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and
  `docs/decisions.md` have templates

#### Scenario: The gate template validates the specs
- **WHEN** the `Makefile` template is read
- **THEN** it names `openspec validate --all --strict --no-interactive` and `betterleaks dir . --no-banner --redact`
- **AND** it holds a `check` target
