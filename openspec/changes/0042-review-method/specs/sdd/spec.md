## MODIFIED Requirements

### Requirement: Engine selection follows the executor

Build and converge SHALL identify and report the executing agent from runtime evidence, not from its model,
provider or editor. Positively identified Claude Code SHALL retain native `/simplify` and its restrictions. Review
and security SHALL run MF's method from the bundled references on every executor, Claude Code included; converge
SHALL invoke no native `/code-review` or `/security-review`. Other and unidentified executors SHALL use the bundled
generic simplify through the host's instruction-loading facilities.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code runs the build's simplify pass and native `/simplify` is invocable
- **THEN** the build uses it without replacing its engine with generic instructions

#### Scenario: A native command is unavailable
- **WHEN** Claude Code cannot invoke native `/simplify`
- **THEN** the build halts naming that command
- **AND** generic simplify requires an explicit user instruction to switch that run

#### Scenario: Claude Code converges
- **WHEN** converge runs on Claude Code
- **THEN** every review and security worker loads MF's references, and no native review command runs

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the build uses the generic simplify path

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the station reports and uses the generic path without guessing from the model name

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins. At `high` it SHALL dispatch each finder, verifier, gap
sweep and role writer itself, none dispatching another, and record `mode: parallel` or `mode: sequential`. The
station SHALL halt before work requiring an unavailable worker capability, naming that capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

#### Scenario: A host runs one worker at a time at high
- **WHEN** converge runs at `high` on a host that cannot run workers in parallel
- **THEN** it runs the same finders, verifiers, gap sweep and role writer in sequence, and the findings files record
  `mode: sequential`

### Requirement: Generic passes preserve the station boundaries

Generic simplify SHALL inspect the change for unnecessary complexity and duplication, preserve behavior and
apply improvements before independent checking. The build SHALL retain its gate and separate simplify-commit
ordering. Review SHALL check correctness, spec, standards, architecture and gate integrity in separate sections,
each citing its source document, including the existing stale-claim, test-cost and coverage-trace passes.

Security SHALL read the target's threat model first, then inspect changed behavior and relevant surrounding
context for concrete vulnerabilities, secrets exposure, unsafe permissions and trust-boundary failures, including
prompt, tool and model-output trust where relevant. A finding SHALL be introduced by the change, carry a concrete
scenario and the offending line quoted, and SHALL NOT be one the reference's do-not-flag list names unless the
target's threat model overrides it. A section whose source document is missing SHALL be marked `inconclusive`, never
read as a pass. Findings SHALL use the existing cards, severity, verdict, verification and release contracts. Review
and security SHALL edit their own findings files, leave code changes to the fix station, and keep findings local
rather than publish external comments.

#### Scenario: A generic pass receives a frozen change
- **WHEN** the station receives the explicit base and head, patch and change artifacts
- **THEN** it reads relevant source context and judges that range without requiring a GitHub remote or review plugin
- **AND** it reports the scope it actually inspected rather than declaring an uninspected change clean

#### Scenario: A generic worker verifies a fix
- **WHEN** fresh review and security workers receive their findings and the fix range
- **THEN** each promotes verified findings or reopens them under the existing contract
- **AND** review receives the design's test table and runs the required review passes

#### Scenario: A section lacks its source document
- **WHEN** the target has no threat model, or one whose sections read `Not written yet:`
- **THEN** the security file's threat-model section is `inconclusive`, its generic classes are still checked, and
  the verdict may still be `clean`

## ADDED Requirements

### Requirement: Converge runs at a tier

`skills/mf-converge/SKILL.md` SHALL take `tier=standard|high`, `standard` when absent. At `standard` each role's one
fresh worker SHALL judge the change from a packet given up front, reading beyond the diff only to trace a named
angle. At `high` each role SHALL run finders per angle, a fresh verifier per candidate, a gap sweep and a fresh role
writer, per `skills/mf-converge/references/high-tier.md`. Both tiers SHALL write the same review and security files,
whose frontmatter SHALL record `tier`, `mode`, `workers`, `model` and `packet`. The cut SHALL suggest the tier in
`.minions/models/<change-id>.toml`, `mf-ship` SHALL pass it, and the release SHALL report it.

#### Scenario: No tier is given
- **WHEN** converge runs without `tier=`
- **THEN** it runs at `standard`, one fresh worker per role, and the findings files record `tier: standard`

#### Scenario: The cut suggests high
- **WHEN** the models file's `[converge]` table holds `tier = "high"` and `mf-ship` runs converge
- **THEN** the prompt carries `tier=high`, and the findings files record `tier: high`

#### Scenario: A standard diff is large
- **WHEN** a standard-tier change exceeds 1,500 changed lines
- **THEN** it is reviewed anyway, and each file's limitations say it is over the standard cap

### Requirement: A finding carries its evidence and verdict

Every card SHALL hold an `Evidence:` field — the offending line quoted, the rule or spec line it breaks, and whether
it was read, traced or ran — and a `Verdict:` field, `confirmed` or `plausible`, a plausible one saying what would
confirm it. Its Priority SHALL name a category. A candidate refuted by evidence SHALL be listed under `## Refuted` in
the findings file with its counter-evidence, never as a card.

#### Scenario: A candidate is refuted
- **WHEN** a checker finds the guard that defeats a candidate
- **THEN** the candidate appears under `## Refuted` with that guard quoted, and no card is written for it
