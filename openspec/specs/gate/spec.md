# Capability: `gate` (the quality-gate runner)

The orchestrator runs the target repo's own quality gate itself — so the agent it drives cannot game
it. The command list is **read from the target** (`.minions/minions.toml`), not hardcoded, and the
runner executes each command in order (no shell), stopping at the first failure. This spec captures
the behavior shipped in `orchestrator/gate.py`; each scenario declares `Layers: unit` and is bound to
its proving test.

## Requirements

### Requirement: Read the target's gate command list

`read_gate_commands` SHALL read the ordered gate command list from the target's
`.minions/minions.toml`, and SHALL error clearly when that config is absent (rather than run an
empty, falsely-green gate).

#### Scenario: The ordered command list parses
- **Key:** `gate:command-list:parses-ordered-list`
- **Layers:** unit
- **WHEN** the target ships a `.minions/minions.toml` with a `gate` array
- **THEN** the commands parse out in order

#### Scenario: A missing config errors clearly
- **Key:** `gate:command-list:missing-config-errors`
- **Layers:** unit
- **WHEN** the target has no `.minions/minions.toml`
- **THEN** a `FileNotFoundError` naming `minions.toml` is raised

### Requirement: Run the gate, stop at the first failure

`SubprocessGate` SHALL run each gate command in order and pass only when every command exits zero;
on the first non-zero command it SHALL stop and report a red verdict with the steps run so far.

#### Scenario: All-green commands pass
- **Key:** `gate:run:all-green-passes`
- **Layers:** unit
- **WHEN** every gate command exits zero
- **THEN** the verdict is green and every command's step is recorded in order

#### Scenario: The first red command stops the gate
- **Key:** `gate:run:stops-at-first-red`
- **Layers:** unit
- **WHEN** a gate command exits non-zero
- **THEN** the verdict is red, later commands do not run, and the last step carries the failure
