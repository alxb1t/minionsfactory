# Spec delta — capability: `build-loop` (the deterministic build spine)

v0.5 switches the loop's state from the vault plan to the in-tree change (R1, R2). The decision and the drive
requirements are restated over `ChangeState` — ordered phases from `changes/<id>/tasks.md` plus git head — and the
advance test is delegated to `change_advanced` rather than re-implemented in the driver.

Both requirements below reproduce **all** of their scenarios — surviving ones verbatim — because the fold replaces
the whole requirement block. Titles are kept **verbatim** (`_apply_fold` matches by title; a retitle would append a
duplicate and orphan the original), so "plan" survives in the second title while its body speaks of the change; the
capability preamble is hand-edited in phase 6, where the fold cannot reach.

On release this delta folds into top-level `specs/build-loop/spec.md`.

## MODIFIED Requirements

### Requirement: Deterministic per-phase decision

`decide` SHALL advance a phase only when the gate is green, the coder left no HALT report, a new commit landed,
and the current phase moved — otherwise it SHALL halt with a reason. It SHALL take the before and after
`ChangeState` and delegate the advance signal to `change_advanced`, so a moved `tasks.md` checkbox is trusted only
when a real commit proves it. The advance is **detected** from disk state (commit + phase index), never trusted
from the agent, so it cannot be gamed.

#### Scenario: A green gate with a new commit and a moved phase advances
- **Key:** `build-loop:phase-decision:advances-on-commit-and-moved-phase`
- **Layers:** unit
- **WHEN** the gate is green, no HALT report exists, and both the git head and the current phase index
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
- **WHEN** the gate is green and a new commit landed but the current phase index did not move
- **THEN** the decision is not to advance (the coder did not really finish the phase)

#### Scenario: A moved checkbox with no new commit halts the phase
- **Key:** `build-loop:phase-decision:moved-checkbox-without-commit-halts`
- **Layers:** unit
- **WHEN** the gate is green and the `tasks.md` checkbox moved but the git head did not change
- **THEN** the decision is not to advance — the checkbox alone is not evidence the phase was built

### Requirement: Drive the plan phase by phase

`run` SHALL loop spawn-coder → gate → decide, advancing through each phase of the active in-tree change until the
change is complete (`ChangeState.is_complete`), resuming from the current phase on disk, and halting cleanly — with
a halt event and a halted run-summary — on a red gate, a coder HALT report, or a provider error. It SHALL read its
state through an injected reader that consults the **repository only**.

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

#### Scenario: The run drives a target whose vault holds no plan
- **Key:** `build-loop:run:drives-with-no-vault-plan`
- **Layers:** unit
- **WHEN** `run` drives a target whose `changes/<id>/tasks.md` is well-formed and whose vault contains no plan file
  and no `implementation_plans/` directory
- **THEN** the run advances through every phase to COMPLETE, reading phase state from the repo alone

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
- **THEN** the events emitted are phase-start, role-spawn, role-returned, advance, run-summary, each phase
  rendered as its index and title

#### Scenario: An already-complete plan emits only a complete summary
- **Key:** `build-loop:run:already-complete-summary`
- **Layers:** unit
- **WHEN** every phase is already checked off on disk
- **THEN** the only event is a run-summary whose status is complete
