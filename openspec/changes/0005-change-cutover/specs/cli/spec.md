# Spec delta — capability: `cli` (the run-from-source entry point)

v0.5 moves the zero-token preflight from the vault-plan read to the in-tree change read (R7). The requirement is
restated; its single scenario keeps its key and its `Layers: e2e` (reserved — `__main__.py` is wiring, proven at the
v0.7 dogfood tier, so no unit test is owed).

The requirement reproduces its scenario in full because the fold replaces the whole requirement block, matched by
title. On release this delta folds into top-level `specs/cli/spec.md`.

## MODIFIED Requirements

### Requirement: Zero-token preflight before spend

Before spawning any role the entry point SHALL run the **change-state** read and the vault-write preflight,
refusing a malformed or misconfigured target with a diagnostic naming the specific problem — no active change under
`changes/` outside `archive/`, a change missing one of its four artifacts, a `tasks.md` with no `## Progress`
checklist, a `proposal.md` with no declared `version`, or an ungranted vault — rather than spending tokens mid-run.
Every refusal SHALL surface as a preflight diagnostic and a non-zero exit; no unhandled exception class SHALL be
reachable from a misconfigured target.

#### Scenario: A misconfigured target is refused before spend
- **Key:** `cli:preflight:refuses-misconfigured-target`
- **Layers:** e2e
- **WHEN** the target's change is malformed, declares no version, or its vault access is not granted
- **THEN** the entry point prints a preflight failure naming the specific problem and exits non-zero without
  spawning a role
