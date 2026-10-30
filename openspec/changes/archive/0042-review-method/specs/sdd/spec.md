## MODIFIED Requirements

### Requirement: Engine selection follows the executor

The build SHALL identify and report the executing agent from runtime evidence, not from its model,
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
- **THEN** the build reports and uses the generic path without guessing from the model name

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins. At `high` it SHALL dispatch each finder, pass worker,
verifier, gap sweep and role writer itself, none dispatching another, and record `mode: parallel` or
`mode: sequential`. The station SHALL halt before work requiring an unavailable worker capability, naming that
capability.

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
prompt, tool and model-output trust where relevant. A finding SHALL be introduced by the change, unless the
contract's passes or repeat rule name it or it is a contradiction between standards files, carry a concrete scenario
and the offending line quoted, and SHALL NOT be one the reference's do-not-flag list names unless the target's threat
model overrides it. A section whose source document is missing SHALL be marked `inconclusive`, never
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

### Requirement: Review searches for stale claims

The review station SHALL run a **stale-claim pass** after its sections: every path, symbol, verb, route or count the
diff renames, deletes or changes is searched across the rest of the tree, and each mention the change made false is
carded as `drift`. The station SHALL say in its Summary that the pass ran, and `skills/mf-converge/SKILL.md` SHALL
check that it did.

#### Scenario: Converge names the stale-claim pass
- **WHEN** the frozen diff renames a path that a file outside the diff still names
- **THEN** review cards that mention as `drift`, and its Summary says the stale-claim pass ran

#### Scenario: A review without the pass
- **WHEN** a review findings file's Summary does not say the stale-claim pass ran
- **THEN** `mf-converge` treats it as a scope failure and halts

### Requirement: Review judges test cost and traced coverage

The review station SHALL run a **test-cost pass** after its sections, carding each new end-to-end test that a lower
layer proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When
the freeze removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to
the test that runs it now, or to the decision, in force at the base, that the design's `## Tests` table names as retiring it. A
proof carried by neither SHALL be `blocking`. Each round SHALL run both passes over that round's freeze. The
station SHALL say in its Summary that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** a review findings file's Summary does not say the test-cost pass ran, or the coverage-trace pass ran or
  the freeze removed no test
- **THEN** `mf-converge` treats it as a scope failure and halts

#### Scenario: The freeze removes a test the table retires
- **WHEN** the freeze removes a test that the `## Tests` table maps to a decision in force at the base
- **THEN** the coverage-trace pass accepts the removal and cards nothing for it

#### Scenario: A proof carried by neither
- **WHEN** a removed assertion maps to no remaining test and to no retiring decision
- **THEN** review cards it `blocking`

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their role resources: converge's review and security references on every
executor, and the build's generic simplify when that path runs.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package.
Missing, empty and escaping targets SHALL fail the gate's resource-integrity check.

#### Scenario: The generic instruction package is incomplete
- **WHEN** a referenced role resource is missing, empty or resolves outside its skill package
- **THEN** the resource-integrity check reports the referring skill and the invalid target

#### Scenario: The package contains valid role resources
- **WHEN** the shipped resource references resolve within their packages to nonempty files
- **THEN** the resource-integrity check passes without treating illustrative change-document links as resources

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time in change-id order, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor running
`mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL act under `conduct.py`'s allowlist on Claude Code — extended by
`AGENTS.md`'s `Ship tools:` line, with forced pushes, hard resets and cleans denied, its shell reaching the directory
`Worktrees:` names and nothing outside it, its prompt carrying the shell rules — or the workspace-write sandbox on Codex, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt the run by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run.

#### Scenario: Two cut versions ship
- **WHEN** two versions are cut, each in its own worktree, and `mf-ship` runs to the end
- **THEN** both are released, merged and pushed in change-id order, the later one integrated and judged by a
  catch-up round first, and only the primary is left

#### Scenario: A worker runs a command off the list
- **WHEN** a build worker's command is denied by the allowlist and the build's check still passes
- **THEN** the run goes on, and the report lists the denial
- **AND WHEN** the build's check fails
- **THEN** the run halts, and its `halt` line names the denial

#### Scenario: No worktrees are declared
- **WHEN** `mf-ship` starts in a repo whose `AGENTS.md` declares no `Worktrees:`
- **THEN** it halts, naming the missing declaration, and starts no worker

## ADDED Requirements

### Requirement: Converge runs at a tier

`skills/mf-converge/SKILL.md` SHALL take `tier=standard|high`, `standard` when absent. At `standard` each role's one
fresh worker SHALL judge the change from a packet given up front, reading beyond the diff only to trace a named
angle. At `high` each role SHALL run finders per angle, a fresh verifier per candidate, a gap sweep and a fresh role
writer, per `skills/mf-converge/references/high-tier.md`. At `high` a named pass worker SHALL run review's
stale-claim, test-cost and coverage-trace passes, the role writer SHALL report them and apply the repeat rule, and a
verify round SHALL give a fresh verifier to each card marked `fixed` or `wontfix`. Converge SHALL halt, naming the
role and the count, before a role passes 40 verifiers in a round, and SHALL NOT verify only some of its candidates.
Both tiers SHALL write the same review and security files, whose frontmatter SHALL record `tier`, `mode`, `workers`,
`model` and `packet`. The cut SHALL suggest the tier in `.minions/models/<change-id>.toml`, `mf-ship` SHALL pass it
and halt on any value but `standard` or `high`, and the release SHALL report it.

#### Scenario: No tier is given
- **WHEN** converge runs without `tier=`
- **THEN** it runs at `standard`, one fresh worker per role, and the findings files record `tier: standard`

#### Scenario: The cut suggests high
- **WHEN** the models file's `[converge]` table holds `tier = "high"` and `mf-ship` runs converge
- **THEN** the prompt carries `tier=high`, and the findings files record `tier: high`

#### Scenario: The models file holds an unknown tier
- **WHEN** the models file's `[converge]` table holds a `tier` other than `standard` or `high`
- **THEN** `mf-ship` halts, naming the value, and starts no converge worker

#### Scenario: A standard diff is large
- **WHEN** a standard-tier change exceeds 1,500 changed lines
- **THEN** it is reviewed anyway, and each file's Summary says it is over the standard cap

#### Scenario: Review runs its passes at high
- **WHEN** review runs at `high`
- **THEN** the pass worker writes `pass-review.md`, and the role writer's Summary reports each pass from it

#### Scenario: A verify round at high meets a wontfix
- **WHEN** the fixer marks a card `wontfix` and commits nothing
- **THEN** a fresh verifier judges it against the unchanged head and the previous freeze's patch
- **AND** the role writer records `accepted` or reopens the card

#### Scenario: Candidates pass the ceiling at high
- **WHEN** a role's next verifiers would take it past 40 in a round
- **THEN** converge halts, naming the role, the count and the ceiling, and starts none of that batch

### Requirement: A finding carries its evidence and verdict

Every card SHALL hold an `Evidence:` field — the offending line quoted, the rule or spec line it breaks, and whether
it was read, traced or ran — and a `Verdict:` field, `confirmed` or `plausible`, a plausible one saying what would
confirm it. Its Priority SHALL name a category. A candidate refuted by evidence SHALL be listed under `## Refuted` in
the findings file with its counter-evidence, never as a card.

#### Scenario: A candidate is refuted
- **WHEN** a checker finds the guard that defeats a candidate
- **THEN** the candidate appears under `## Refuted` with that guard quoted, and no card is written for it
