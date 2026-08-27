# Capability: `fanout` (end-of-plan review ‖ security ‖ simplify)

At plan end the orchestrator fans out the three read-only roles over the **frozen** diff, each as a
fresh instance that can only write its own findings file, then reads each verdict back from disk (the
trust boundary — never the role's word). A missing findings file counts as not-clean, so a
not-yet-run role can never let the loop converge falsely. This spec captures the behavior shipped in
`orchestrator/fanout.py` and `orchestrator/findings.py`; each scenario declares `Layers: unit` and is
bound to its proving test.

## Requirements

### Requirement: Run the read-only roles over the frozen diff

`run_fanout` SHALL run each read-only role over the supplied diff, prepending the orchestrator-owned
Inputs block (the role has no shell to resolve paths itself), scoping each role's write to its
findings file, emitting a spawn and a returned event per role, and collecting each verdict from disk.

#### Scenario: Each read-only role runs over the frozen diff
- **Key:** `fanout:read-only-roles:runs-each-over-frozen-diff`
- **Layers:** unit
- **WHEN** `run_fanout` runs a set of roles over a diff
- **THEN** each role is spawned read-only (Bash disallowed), the diff is written to the shared patch
  file, and each role's findings verdict is read back from disk

#### Scenario: The orchestrator Inputs block is prepended
- **Key:** `fanout:read-only-roles:prepends-inputs-block`
- **Layers:** unit
- **WHEN** a role is spawned
- **THEN** its prompt leads with the Inputs block (mode, head SHA, findings path) followed by the
  role's own prompt body

#### Scenario: A spawn and a returned event fire per role
- **Key:** `fanout:read-only-roles:emits-spawn-and-returned`
- **Layers:** unit
- **WHEN** the fan-out runs several roles
- **THEN** it emits a role-spawn then a role-returned event for each, in order

### Requirement: Read the findings verdict from disk

`read_findings_state` SHALL read a role's findings file frontmatter into a validated `FindingsState`,
return `None` for a missing file (which counts as not-clean upstream), and reject an unknown verdict
value.

#### Scenario: The findings frontmatter parses into a verdict
- **Key:** `fanout:findings:parses-frontmatter-verdict`
- **Layers:** unit
- **WHEN** a findings file with valid frontmatter is read
- **THEN** its verdict, open-blocking count, round, and head parse into a validated state

#### Scenario: A missing findings file reads as None
- **Key:** `fanout:findings:missing-file-is-none`
- **Layers:** unit
- **WHEN** the findings file does not exist
- **THEN** the read returns `None`

#### Scenario: An unknown verdict is rejected
- **Key:** `fanout:findings:rejects-unknown-verdict`
- **Layers:** unit
- **WHEN** a findings file carries a verdict outside the allowed values
- **THEN** validation raises rather than accepting the bad verdict

### Requirement: Findings location and key

A role's findings file SHALL live at `<repo>/.minions/findings/<change-id>_<role>.md` — inside the repository
being built, keyed to the change id, the same identifier as the change directory and the `Change:` commit trailer.
The path SHALL be resolved in exactly one place in code, used by the fan-out, the converge loop and the release
stage alike, and SHALL resolve from the **repo root** — no argument naming a directory outside the repository. The
orchestrator SHALL create the `.minions/findings/` directory before spawning any read-only role, which is granted
write access to its own findings file only and has no shell with which to create a directory.

#### Scenario: The findings path is keyed to the change id
- **Key:** `fanout:findings-path:change-id-keyed-path`
- **Layers:** unit
- **WHEN** the findings path is resolved for a change id and a role name
- **THEN** it is `<repo>/.minions/findings/<change-id>_<role>.md`, and the fan-out, converge and release stages
  resolve the identical path for the same inputs

#### Scenario: The fan-out writes through the single resolution site
- **Key:** `fanout:findings-path:fanout-writes-through-helper`
- **Layers:** unit
- **WHEN** `run_fanout` runs the three read-only roles for a change id
- **THEN** each role's write is scoped to `<repo>/.minions/findings/<change-id>_<role>.md` and each verdict is read
  back from that same path

#### Scenario: The findings directory is created before the first spawn
- **Key:** `fanout:findings-path:creates-findings-dir`
- **Layers:** unit
- **WHEN** the fan-out runs against a repo that has no `.minions/findings/` directory
- **THEN** the directory is created before the first role is spawned (the read-only role could not create it itself,
  and a missing file would otherwise read as not-clean)

#### Scenario: No resolution site takes a directory outside the repository
- **Key:** `fanout:findings-path:no-external-root-argument`
- **Layers:** unit
- **WHEN** the orchestrator's function signatures are scanned
- **THEN** none takes a parameter naming a directory outside the repository — the findings root derives from the
  repo the run was invoked against

### Requirement: Orchestrator-owned role inputs

The orchestrator SHALL build the Inputs block for **every** role — the three read-only fan-out roles and the coder,
fixer and release roles — carrying the change directory, the findings paths, the git head and the declared version,
**and nothing resolving outside the repository**. A spawned role's prompt SHALL lead with that block followed by
the role's own body; the release role, which the orchestrator does not spawn, SHALL receive the same block emitted
with its handoff. No role prompt SHALL derive a path by shell: path resolution lives in code, in one place, where
it can be typed, tested and gated.

#### Scenario: The Inputs block carries the change and its findings
- **Key:** `fanout:role-inputs:block-carries-change-and-findings`
- **Layers:** unit
- **WHEN** the Inputs block is built for a role
- **THEN** it names the change directory, each findings path, the git head and the declared version

#### Scenario: The Inputs block names no path outside the repository
- **Key:** `fanout:role-inputs:block-is-repo-only`
- **Layers:** unit
- **WHEN** the Inputs block is built for any role
- **THEN** every path it names resolves under the repository — it carries no context line naming an external
  narrative or overview document

#### Scenario: A role prompt leads with the Inputs block
- **Key:** `fanout:role-inputs:prompt-leads-with-inputs`
- **Layers:** unit
- **WHEN** a prompt is assembled for the coder, the fixer or the release role
- **THEN** the assembled prompt begins with the Inputs block and is followed by that role's own prompt body,
  which itself contains no shell path derivation
