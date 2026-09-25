## REMOVED Requirements

### Requirement: Read the target's gate command list

**Reason**: the gate is the target's `make gate`; nothing reads a command list any more.
**Migration**: declare the gate as a `gate` target in the target's root `Makefile`, and delete
`.minions/minions.toml`.

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

## ADDED Requirements

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
