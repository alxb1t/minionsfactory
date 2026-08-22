# Capability: `status` (the event stream)

A typed event schema with an append-only history, a current-state snapshot, and a stdout renderer —
so a run's progress lives on disk (round-tripping through its typed variants) and renders as
human-readable lines. This spec captures the behavior shipped in `orchestrator/status.py`; each
scenario declares `Layers: unit` and is bound to its proving test.

## Requirements

### Requirement: The event stream round-trips through disk

Events SHALL append to the history and read back as their typed variants, the snapshot SHALL reflect
the latest event, and the snapshot SHALL report in-progress after a role spawn and done once the
result lands.

#### Scenario: An appended event reads back as its typed variant
- **Key:** `status:stream:append-reads-back-typed`
- **Layers:** unit
- **WHEN** an event is appended to the stream and read back
- **THEN** it round-trips as the same typed event variant

#### Scenario: The snapshot reflects the latest event
- **Key:** `status:stream:snapshot-reflects-latest`
- **Layers:** unit
- **WHEN** several events are emitted
- **THEN** the snapshot reads back the most recent one

#### Scenario: The snapshot reads in-progress after a spawn
- **Key:** `status:stream:in-progress-after-spawn`
- **Layers:** unit
- **WHEN** a role-spawn is the latest event
- **THEN** the snapshot reports the run in progress

#### Scenario: The snapshot reads done after the result lands
- **Key:** `status:stream:done-after-result`
- **Layers:** unit
- **WHEN** a role-returned event follows the spawn
- **THEN** the snapshot no longer reports in progress

### Requirement: Render events as human-readable lines

`render` SHALL format each event variant as a human-readable stdout line — trimming a verbose phase
label to one line and surfacing a role's summary when present.

#### Scenario: Each event variant renders as a line
- **Key:** `status:render:formats-each-event`
- **Layers:** unit
- **WHEN** an event of any variant (phase-start, role-spawn, role-returned, gate-step, advance, halt,
  run-summary) is rendered
- **THEN** it produces the variant's human-readable line

#### Scenario: A verbose phase is trimmed for the CLI
- **Key:** `status:render:trims-verbose-phase`
- **Layers:** unit
- **WHEN** a very long `current_phase` label is rendered
- **THEN** the line is trimmed to a short one-line label

#### Scenario: A role's summary is surfaced when present
- **Key:** `status:render:surfaces-role-summary`
- **Layers:** unit
- **WHEN** a role-returned event carries a summary
- **THEN** the rendered line surfaces the summary (the reason is not hidden)
