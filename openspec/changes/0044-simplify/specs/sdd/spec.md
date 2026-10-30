## MODIFIED Requirements

### Requirement: Engine selection follows the executor

The build SHALL identify and report the executing agent from runtime evidence, not from its model, provider or
editor, and SHALL choose no engine by it: every station runs MF's own method on every executor. The build SHALL run
`mf-simplify` and no native `/simplify`; review and security SHALL run MF's method from the bundled references, and
converge SHALL invoke no native `/code-review` or `/security-review`.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code runs the build's simplify pass and native `/simplify` is invocable
- **THEN** the build runs `mf-simplify`, not the native command

#### Scenario: A native command is unavailable
- **WHEN** native `/simplify` is not invocable
- **THEN** the build runs `mf-simplify` as on any host, and nothing halts for it

#### Scenario: Claude Code converges
- **WHEN** converge runs on Claude Code
- **THEN** every review and security worker loads MF's references, and no native review command runs

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the build reports that executor and runs `mf-simplify`

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the build reports `unidentified` without guessing from the model name, and runs `mf-simplify`

### Requirement: Generic passes preserve the station boundaries

`mf-simplify` SHALL edit only the change's own lines, by its angles and closed edit kinds, inside the oracles its
skill names, before independent checking. The build SHALL retain its gate and separate simplify-commit ordering. Review SHALL check correctness, spec, standards, architecture and gate integrity in separate sections,
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

## ADDED Requirements

### Requirement: mf-simplify simplifies a change inside its oracles

`skills/mf-simplify/SKILL.md` SHALL take the active change's `<merge-base>..HEAD` and edit only its lines, one angle
at a time — reuse, simplification, efficiency, altitude, conventions — each edit one of `delete`, `stdlib`, `native`,
`speculative` or `shrink`. It SHALL run `make gate` after each angle and revert that angle's edits when the gate is
red or the angle adds net lines. It SHALL never edit a test, and SHALL never apply an edit that touches a spec
requirement or scenario, a public interface, a seam the design names, a control the threat model names, a decision in
force, or that exceeds 20 lines; such edits SHALL be noted for review instead. It SHALL commit what it applied as one
`refactor(<change-id>): simplify` commit whose body names the edits applied and skipped, the mode, and `net: -N lines`,
or report `lean already` and commit nothing. It SHALL write no findings file and hold no verdict.

#### Scenario: A trap is left alone
- **WHEN** the change holds a validation the threat model names, which looks redundant
- **THEN** `mf-simplify` leaves it, and its commit body notes it as skipped with the reason

#### Scenario: An angle turns the gate red
- **WHEN** an angle's edits fail `make gate`
- **THEN** `mf-simplify` reverts that angle's edits, keeps the angles that passed, and notes the reverted ones

#### Scenario: Nothing to simplify
- **WHEN** no angle finds an edit inside the oracles
- **THEN** `mf-simplify` reports `lean already` and makes no commit
