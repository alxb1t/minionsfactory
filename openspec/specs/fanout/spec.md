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
