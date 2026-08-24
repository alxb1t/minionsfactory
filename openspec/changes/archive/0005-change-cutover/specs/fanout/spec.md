# Spec delta — capability: `fanout` (end-of-plan review ‖ security ‖ simplify)

v0.5 moves the findings home out of the retired `implementation_plans/` and keys it to the **change id** (R5), and
generalizes the orchestrator-owned Inputs block — already this capability's concern — so the coder, fixer and
release roles receive their paths from the orchestrator instead of shelling for them (R6).

Both requirements are **ADDED**; the existing read-only-roles and findings-verdict requirements are unchanged.

On release this delta folds into top-level `specs/fanout/spec.md`.

## ADDED Requirements

### Requirement: Findings location and key

A role's findings file SHALL live at `<vault>/findings/<change-id>_<role>.md` — keyed to the change id, the same
identifier as the change directory and the `Change:` commit trailer. The path SHALL be resolved in exactly one place
in code, used by the fan-out, the converge loop and the release stage alike. The orchestrator SHALL create the
`findings/` directory before spawning any read-only role, which is granted write access to its own findings file
only and has no shell with which to create a directory.

#### Scenario: The findings path is keyed to the change id
- **Key:** `fanout:findings-path:change-id-keyed-path`
- **Layers:** unit
- **WHEN** the findings path is resolved for a change id and a role name
- **THEN** it is `<vault>/findings/<change-id>_<role>.md`, and the fan-out, converge and release stages resolve the
  identical path for the same inputs

#### Scenario: The fan-out writes through the single resolution site
- **Key:** `fanout:findings-path:fanout-writes-through-helper`
- **Layers:** unit
- **WHEN** `run_fanout` runs the three read-only roles for a change id
- **THEN** each role's write is scoped to `<vault>/findings/<change-id>_<role>.md` and each verdict is read back from
  that same path

#### Scenario: The findings directory is created before the first spawn
- **Key:** `fanout:findings-path:creates-findings-dir`
- **Layers:** unit
- **WHEN** the fan-out runs against a vault that has no `findings/` directory
- **THEN** the directory is created before the first role is spawned (the read-only role could not create it itself,
  and a missing file would otherwise read as not-clean)

### Requirement: Orchestrator-owned role inputs

The orchestrator SHALL build the Inputs block for **every** role — the three read-only fan-out roles and the coder,
fixer and release roles — carrying the change directory, the findings paths, the git head and the declared version.
A spawned role's prompt SHALL lead with that block followed by the role's own body; the release role, which the
orchestrator does not spawn, SHALL receive the same block emitted with its handoff. No role prompt SHALL derive a
path by shell: path resolution lives in code, in one place, where it can be typed, tested and gated.

#### Scenario: The Inputs block carries the change and its findings
- **Key:** `fanout:role-inputs:block-carries-change-and-findings`
- **Layers:** unit
- **WHEN** the Inputs block is built for a role
- **THEN** it names the change directory, each findings path, the git head and the declared version

#### Scenario: A role prompt leads with the Inputs block
- **Key:** `fanout:role-inputs:prompt-leads-with-inputs`
- **Layers:** unit
- **WHEN** a prompt is assembled for the coder, the fixer or the release role
- **THEN** the assembled prompt begins with the Inputs block and is followed by that role's own prompt body,
  which itself contains no shell path derivation
