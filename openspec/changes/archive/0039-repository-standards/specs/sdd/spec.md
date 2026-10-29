## MODIFIED Requirements

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md`, `README.md`,
`CODING_STANDARDS.md` and `CONTRIBUTING.md`. A template's target path SHALL be its path under `templates/` without
the `.tmpl` suffix. The `Makefile` template's `gate` recipe SHALL run `openspec validate --all --strict
--no-interactive`.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md` and `CONTRIBUTING.md` have templates

#### Scenario: The gate template validates the specs
- **WHEN** the `Makefile` template is read
- **THEN** it names `openspec validate --all --strict --no-interactive`

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards. The template SHALL
link `CODING_STANDARDS.md` and `CONTRIBUTING.md` as mandatory context, and bootstrap SHALL halt when a
`CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` already exists.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
Build, and converge for every worker it dispatches, SHALL also read a root `CODING_STANDARDS.md`,
`CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name. A contradiction between those files SHALL
go to the person: review cards it as drift, and the build halts on one that decides its phase's code. No filename
SHALL take precedence over another.
The root context SHALL explicitly direct reading of the shared principles and decisions rather than rely on
host-specific import syntax.

#### Scenario: A target has the agreed context
- **WHEN** a station starts on a target containing `AGENTS.md`
- **THEN** it reads that context and its mandatory linked context regardless of the host's automatic loader

#### Scenario: A target lacks the agreed context
- **WHEN** cut, build, converge or release starts without root `AGENTS.md`
- **THEN** it halts naming that missing file without substituting another context filename

#### Scenario: A new target is bootstrapped
- **WHEN** bootstrap writes a target with no collisions
- **THEN** it creates `AGENTS.md`, `CODING_STANDARDS.md` and `CONTRIBUTING.md`, and retains the template's test
  policy
- **AND** `AGENTS.md` links both standards files as mandatory context

#### Scenario: A standards file already exists
- **WHEN** bootstrap starts in a directory holding `CODE_STANDARDS.md`
- **THEN** it halts, naming that file, and writes nothing

#### Scenario: An existing repo has standards its AGENTS.md does not name
- **WHEN** the build starts on a repo whose root holds `CODE_STANDARDS.md` and whose `AGENTS.md` does not name it
- **THEN** the build reads it, and converge hands it to every worker

## ADDED Requirements

### Requirement: The build's comment rules default to no explanatory comment

`skills/mf-build/SKILL.md` `C1` SHALL forbid an explanatory comment: names, types, structure and tests carry what
code does. `C2` SHALL name the exceptions: a short why or pointer for a constraint code cannot express, a contract
or required docstring, and a tool directive or header. A rule in the repo's coding standards that names a `C` rule
SHALL replace it. The rules SHALL apply to the comments a phase writes or changes and the comments next to them,
never to a whole file unasked.

#### Scenario: A phase writes an explanatory comment
- **WHEN** a phase adds a comment restating what the next line does
- **THEN** `C1` forbids it, and review may card it

#### Scenario: A project refines a comment rule
- **WHEN** the repo's `CODING_STANDARDS.md` holds a rule naming `C2`
- **THEN** that rule replaces `C2` for the repo, and the other `C` rules still apply
