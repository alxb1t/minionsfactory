## REMOVED Requirements

### Requirement: The bootstrap's `CLAUDE.md` states the rules for tests

**Reason:** The target-context contract moves to `AGENTS.md` without a legacy fallback.

**Migration:** Rename the template to `skills/mf-bootstrap/templates/AGENTS.md.tmpl` and retain its test policy.

## MODIFIED Requirements

### Requirement: A test is deleted or merged only as the design's table names it

`skills/mf-build/SKILL.md` SHALL treat a test deleted or merged as the change's `design.md` `## Tests` table names it
as consolidation, not as weakening the gate, and SHALL halt on a deletion outside that table. The fix station in
`skills/mf-converge/SKILL.md` SHALL never delete or merge a test.

#### Scenario: The build names the table, and the fix station never deletes
- **WHEN** `mf-build` and `mf-converge` are scanned
- **THEN** `mf-build`'s `## Step 2 — The per-phase ritual` names `` `## Tests` table ``
- **AND** `mf-converge`'s `## Step 6 — The fix station (a fresh worker, inside this loop)` names
  `never deletes or merges a test`

## ADDED Requirements

### Requirement: The bootstrap's `AGENTS.md` states the rules for tests

`skills/mf-bootstrap/templates/AGENTS.md.tmpl` SHALL hold a `## Tests` section stating where a test goes, that a
step in an existing test comes before a new one, which engines a test runs on, and that a test is deleted or merged
only as a change's `## Tests` table names it.

#### Scenario: The template has the section
- **WHEN** `skills/mf-bootstrap/templates/AGENTS.md.tmpl` is read
- **THEN** one of its lines is `## Tests`

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
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
- **THEN** it creates `AGENTS.md` and retains the template's test policy

### Requirement: Skills install into the shared user directory by default

The installer SHALL default to `~/.agents/skills`, preserve the `SKILLS_DIR` override and retain its existing
symlink, collision-refusal and checkout-specific uninstall behavior. It SHALL leave previous installations alone.

#### Scenario: The operator uses the default destination
- **WHEN** `make install-skills` runs without a destination override
- **THEN** it targets the shared user skills directory

#### Scenario: The operator supplies a destination
- **WHEN** `SKILLS_DIR` names a different destination
- **THEN** installation and uninstallation use that destination with their existing safeguards

### Requirement: Engine selection follows the executor

Build and converge SHALL identify and report the executing agent from runtime evidence, not from its model,
provider or editor. Positively identified Claude Code SHALL retain native `/simplify`, `/code-review` and
`/security-review` invocation and the existing native engine restrictions. Other and unidentified executors
SHALL use the bundled generic instructions through the host's instruction-loading facilities.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code executes a pass and its required native command is invocable
- **THEN** the station uses that native command without replacing its engine with generic instructions

#### Scenario: A native command is unavailable
- **WHEN** Claude Code cannot invoke the required native command
- **THEN** the station halts naming that command
- **AND** generic execution requires an explicit user instruction to switch that run

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the station uses the generic path

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the station reports and uses the generic path without guessing from the model name

### Requirement: Generic passes preserve the station boundaries

Generic simplify SHALL inspect the change for unnecessary complexity and duplication, preserve behavior and
apply improvements before independent checking. The build SHALL retain its gate and separate simplify-commit
ordering. Generic review SHALL check correctness, spec compliance, target standards and tests, including the
existing stale-claim, test-cost and coverage-trace passes.

Generic security SHALL inspect changed behavior and relevant surrounding context for concrete vulnerabilities,
secrets exposure, unsafe permissions and trust-boundary failures, including prompt and tool instructions where
relevant. Findings SHALL cite evidence and use the existing cards, severity, verdict, verification and release
contracts. Review and security SHALL edit their own findings files, leave code changes to the fix station, and
keep findings local rather than publish external comments.

#### Scenario: A generic pass receives a frozen change
- **WHEN** the station receives the explicit base and head, patch and change artifacts
- **THEN** it reads relevant source context and judges that range without requiring a GitHub remote or review plugin
- **AND** it reports the scope it actually inspected rather than declaring an uninspected change clean

#### Scenario: A generic worker verifies a fix
- **WHEN** fresh review and security workers receive their findings and the fix range
- **THEN** each promotes verified findings or reopens them under the existing contract
- **AND** review receives the design's test table and runs the required review passes

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Claude Code SHALL retain parallel review and security dispatch. The generic path SHALL prefer parallel dispatch
and permit sequential independent workers over the same frozen head, completing both before a fix begins.
The station SHALL halt before work requiring an unavailable worker capability, naming that capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their generic role resources when the generic branch executes.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package.
Missing, empty and escaping targets SHALL fail the gate's resource-integrity check.

#### Scenario: The generic instruction package is incomplete
- **WHEN** a referenced role resource is missing, empty or resolves outside its skill package
- **THEN** the resource-integrity check reports the referring skill and the invalid target

#### Scenario: The package contains valid role resources
- **WHEN** the shipped resource references resolve within their packages to nonempty files
- **THEN** the resource-integrity check passes without treating illustrative change-document links as resources

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
Authentication and provider configuration SHALL remain the operator's responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

### Requirement: Compatibility claims identify their evidence

This migration SHALL include a live Codex smoke of the generic passes with findings on disk and fresh verification
after a fix, plus a hand review of Claude Code's native dispatch. Model calls SHALL stay outside CI.
A host SHALL be described as tested only when an actual run supplies that evidence; other hosts SHALL be
described by the capabilities they require, without a universal model-quality claim.

#### Scenario: A host is documented without a live run
- **WHEN** documentation describes a supported host's capabilities but has no run evidence
- **THEN** it does not label that host tested

#### Scenario: The generic smoke finishes
- **WHEN** the Codex smoke and native dispatch review meet the design's acceptance criteria
- **THEN** the migration records their actual outcomes and retains links to the evidence
