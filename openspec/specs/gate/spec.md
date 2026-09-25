# Capability: `gate` (the quality-gate runner)

## Purpose

The orchestrator runs the target repo's own quality gate itself — so the agent it drives cannot game
it. The command list is **read from the target** (`.minions/minions.toml`), not hardcoded, and the
runner executes each command in order (no shell), stopping at the first failure. This spec captures
the behavior shipped in `orchestrator/gate.py`; each scenario declares `Layers: unit` and is bound to
its proving test.

## Requirements

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

### Requirement: Run the target's `make gate`

`SubprocessGate` SHALL resolve the target's gate to the one command `make gate`, after checking it with
`make -n gate`. It SHALL raise a `FileNotFoundError` naming the `Makefile` — rather than run an empty,
falsely-green gate — when the target has no root `Makefile`, when `make -n gate` exits non-zero, or when
`make -n gate` prints no command: nothing, or only a line saying `is up to date` or `Nothing to be done`.

#### Scenario: A gate target resolves to make gate
- **Key:** `gate:make-gate:resolves-to-make-gate`
- **Layers:** unit
- **WHEN** the target has a root `Makefile` whose `make -n gate` exits zero and prints a command
- **THEN** the gate runs exactly one command, `make gate`

#### Scenario: A missing Makefile errors clearly
- **Key:** `gate:make-gate:missing-makefile-errors`
- **Layers:** unit
- **WHEN** the target has no root `Makefile`
- **THEN** a `FileNotFoundError` naming `Makefile` is raised, and no command is run

#### Scenario: A missing gate target errors clearly
- **Key:** `gate:make-gate:missing-target-errors`
- **Layers:** unit
- **WHEN** `make -n gate` exits non-zero
- **THEN** a `FileNotFoundError` naming `Makefile` is raised, and `make gate` is not run

#### Scenario: A gate target that runs nothing errors clearly
- **Key:** `gate:make-gate:empty-target-errors`
- **Layers:** unit
- **WHEN** `make -n gate` prints nothing, or only a line saying `is up to date` or `Nothing to be done`
- **THEN** a `FileNotFoundError` naming `Makefile` is raised, and `make gate` is not run
