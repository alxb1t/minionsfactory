# Capability: `build-loop` (the deterministic build spine)

The driver that advances the active **in-tree change** phase by phase or halts — **no LLM in the
loop**. It reads where the work stands from the repo alone (`openspec/changes/<id>/tasks.md` plus
git head), spawns the coder, runs the gate itself, and **detects** the advance (a new commit landed
**and** the current-phase index moved) rather than trusting the agent's word; at change-complete it
fans out, runs the converge loop, and prepares the release, halting cleanly at the first blocker so
the next run resumes from disk. This spec captures the behavior shipped in `orchestrator/driver.py`;
each scenario declares `Layers: unit` and is bound to its proving test.

> Two requirement **titles** below still say "plan" — kept verbatim on purpose. The release fold
> matches a requirement by title and replaces the whole block, so retitling one would append a
> duplicate and orphan the original. Their bodies speak of the change, which is what ships.

## Requirements

### Requirement: Deterministic per-phase decision

`decide` SHALL advance a phase only when the gate is green, the coder left no HALT report, a new
commit landed, and the current phase moved — otherwise it SHALL halt with a reason. The advance is
**detected** from disk state (commit + phase pointer), never trusted from the agent, so it cannot
be gamed.

#### Scenario: A green gate with a new commit and a moved phase advances
- **Key:** `build-loop:phase-decision:advances-on-commit-and-moved-phase`
- **Layers:** unit
- **WHEN** the gate is green, no HALT report exists, and both the git head and the current phase
  changed between the before and after states
- **THEN** the decision is to advance

#### Scenario: A red gate halts the phase
- **Key:** `build-loop:phase-decision:red-gate-halts`
- **Layers:** unit
- **WHEN** the gate result is red
- **THEN** the decision is not to advance and the reason names the gate

#### Scenario: A coder HALT report halts the phase
- **Key:** `build-loop:phase-decision:coder-halt-report-halts`
- **Layers:** unit
- **WHEN** the coder wrote a HALT report
- **THEN** the decision is not to advance and the reason names the halt

#### Scenario: An unchanged commit or phase halts the phase
- **Key:** `build-loop:phase-decision:no-advance-halts`
- **Layers:** unit
- **WHEN** the gate is green but neither the git head nor the current phase moved
- **THEN** the decision is not to advance (the coder did not really finish the phase)

### Requirement: Drive the plan phase by phase

`run` SHALL loop spawn-coder → gate → decide, advancing through each phase until the plan is
complete, resuming from the current phase on disk, and halting cleanly — with a halt event and a
halted run-summary — on a red gate, a coder HALT report, or a provider error.

#### Scenario: The run advances through every phase to completion
- **Key:** `build-loop:run:advances-until-complete`
- **Layers:** unit
- **WHEN** each phase gates green with a new commit and a moved phase pointer
- **THEN** the run ends COMPLETE having advanced once per phase

#### Scenario: The run resumes from the current phase on disk
- **Key:** `build-loop:run:resumes-from-disk`
- **Layers:** unit
- **WHEN** an earlier phase is already done on disk
- **THEN** the run picks up at the first unfinished phase and advances only the remaining phases

#### Scenario: A red gate halts the run
- **Key:** `build-loop:run:red-gate-halts`
- **Layers:** unit
- **WHEN** the gate is red on a phase
- **THEN** the run ends HALTED, its reason names the gate, and no phase advanced

#### Scenario: A coder HALT report halts the run
- **Key:** `build-loop:run:coder-halt-report-halts`
- **Layers:** unit
- **WHEN** the coder writes a HALT report
- **THEN** the run ends HALTED with a halt reason

#### Scenario: A provider error halts the run cleanly
- **Key:** `build-loop:run:provider-error-halts-cleanly`
- **Layers:** unit
- **WHEN** the provider raises a `ProviderError` spawning the coder
- **THEN** the run ends HALTED, emits a halt event (not a traceback), and names the provider error

#### Scenario: An advancing phase emits the full event stream
- **Key:** `build-loop:run:emits-advancing-event-stream`
- **Layers:** unit
- **WHEN** a phase advances
- **THEN** the events emitted are phase-start, role-spawn, role-returned, advance, run-summary

#### Scenario: An already-complete plan emits only a complete summary
- **Key:** `build-loop:run:already-complete-summary`
- **Layers:** unit
- **WHEN** every phase is already done on disk
- **THEN** the only event is a run-summary whose status is complete

### Requirement: End-of-plan fan-out, converge, and release sequencing

At plan-complete `run` SHALL run the fan-out, then the converge loop, then the release, in that
order — but only when the build did not halt first — halting the run if converge halts or the
release is refused, and never reaching release when converge halts.

#### Scenario: Fan-out runs when the plan completes
- **Key:** `build-loop:end-of-plan:fanout-on-complete`
- **Layers:** unit
- **WHEN** the plan reaches complete
- **THEN** the fan-out stage is invoked

#### Scenario: No fan-out when the build halts
- **Key:** `build-loop:end-of-plan:no-fanout-on-halt`
- **Layers:** unit
- **WHEN** the build halts before the plan completes
- **THEN** the fan-out stage is not invoked

#### Scenario: Converge runs after the fan-out
- **Key:** `build-loop:end-of-plan:converge-after-fanout`
- **Layers:** unit
- **WHEN** the plan completes
- **THEN** the converge stage runs after the fan-out, in that order

#### Scenario: A converge halt halts the run
- **Key:** `build-loop:end-of-plan:converge-halt-halts-run`
- **Layers:** unit
- **WHEN** the converge loop halts (e.g. round cap exceeded)
- **THEN** the run ends HALTED carrying the converge reason

#### Scenario: Release is prepared after converge
- **Key:** `build-loop:end-of-plan:release-after-converge`
- **Layers:** unit
- **WHEN** the plan completes and converge converges
- **THEN** the release stage runs after fan-out and converge, in that order

#### Scenario: A refused release halts the run
- **Key:** `build-loop:end-of-plan:release-refused-halts`
- **Layers:** unit
- **WHEN** the release is refused
- **THEN** the run ends HALTED carrying the refusal reason

#### Scenario: A converge halt reaches neither release
- **Key:** `build-loop:end-of-plan:no-release-when-converge-halts`
- **Layers:** unit
- **WHEN** converge halts
- **THEN** the release stage is never invoked
