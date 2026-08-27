# Spec delta — `build-loop`

## MODIFIED Requirements

### Requirement: Deterministic per-phase decision

`decide` SHALL advance a phase only when the gate is green, the coder left no HALT report, a new commit landed,
and the current phase moved — otherwise it SHALL halt with a reason. The HALT report SHALL be resolved **inside
the repository**, at `.minions/HALT.md`. `decide` SHALL take the before and after `ChangeState` and delegate the
advance signal to `change_advanced`, so a moved `tasks.md` checkbox is trusted only when a real commit proves it.
The advance is **detected** from disk state (commit + phase index), never trusted from the agent, so it cannot be
gamed.

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

#### Scenario: The HALT report is resolved inside the repository
- **Key:** `build-loop:phase-decision:halt-report-in-repo`
- **Layers:** unit
- **WHEN** the HALT report's existence is tested for a repo
- **THEN** the path checked is `<repo>/.minions/HALT.md`, and no path outside the repository is resolved

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
