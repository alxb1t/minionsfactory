## MODIFIED Requirements

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md`, `README.md`,
`CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and `docs/decisions.md`. A template's target path SHALL
be its path under `templates/` without the `.tmpl` suffix. The `Makefile` template's `gate` recipe SHALL run
`openspec validate --all --strict --no-interactive`.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and
  `docs/decisions.md` have templates

#### Scenario: The gate template validates the specs
- **WHEN** the `Makefile` template is read
- **THEN** it names `openspec validate --all --strict --no-interactive`

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards. The template SHALL
link `CODING_STANDARDS.md` and `CONTRIBUTING.md` as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`
as context for designing, building and reviewing; bootstrap SHALL halt when a `CODING_STANDARDS.md`,
`CODE_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md`, `ARCHITECTURE.md` or `docs/decisions.md` already exists.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
Build, and converge for every worker it dispatches, SHALL also read a root `CODING_STANDARDS.md`,
`CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name. A contradiction between those files SHALL
go to the person: review cards it as drift, and the build halts on one that decides its phase's code. No filename
SHALL take precedence over another.
Cut, build, and converge for every worker it dispatches, SHALL read the architecture decisions and the threat model —
the documents `AGENTS.md` names, else `docs/decisions.md`, `ARCHITECTURE.md`, `docs/adr/*.md` and `THREAT_MODEL.md`
when present. The build SHALL halt on a phase that contradicts a decision in force, unless a task of the change
amends that decision.
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
- **THEN** it creates `AGENTS.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and
  `docs/decisions.md`, and retains the template's test policy
- **AND** `AGENTS.md` links both standards files as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`

#### Scenario: A standards file already exists
- **WHEN** bootstrap starts in a directory holding `CODE_STANDARDS.md` or `THREAT_MODEL.md`
- **THEN** it halts, naming that file, and writes nothing

#### Scenario: An existing repo has standards its AGENTS.md does not name
- **WHEN** the build starts on a repo whose root holds `CODE_STANDARDS.md` and whose `AGENTS.md` does not name it
- **THEN** the build reads it, and converge hands it to every worker

#### Scenario: A phase contradicts a decision in force
- **WHEN** a phase's tasks would break a decision in the repo's `docs/decisions.md`, and no task amends it
- **THEN** the build halts, naming the decision and the task
- **AND WHEN** a task of the change amends that decision
- **THEN** the build proceeds
