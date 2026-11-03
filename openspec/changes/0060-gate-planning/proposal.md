---
bump: minor
backlog: [0055·R3]
---

# Gate planning

A planned change to a gate makefile is caught at the cut, not after the whole build; a person's approval passes it without a
history rewrite; and a branch still cannot certify its own gate.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

In two days three planned `Makefile` changes halted converge after the whole build: isekai's `0088-mf-readiness`, gpunit's
`0017-mf-readiness` and isekai's `0093-the-tests-revisited`. Each was planned and approved at the cut, in prose; `gate_check.py`
reads only a cut task that names `` `gate` `` and quotes each changed line, and nothing before converge runs it. Each recovery
rewrote every commit from the cut. The sandbox made such edits common: every target moves tests in or out of its gate.

## What Changes

- **The halt lists every unquoted line in one run**, states the rule, says the cut commit is what counts, and names the way out.
- **`I18`**: a cut task that names a gate makefile names `` `gate` `` and quotes its lines in a `diff` block; the cut runs the
  check's own parser and refuses the bare form.
- **The build checks a gate change at its phase**, before the phase's commit.
- **`/mf-ship approve-gate <change-id>`**: the person's yes, bound to the hash of the exact diff, kept in the home folder,
  passes the check with no rewrite.
- **Ride-along**: `mf-release`'s `Next:` names `/mf-plan`; the station diagrams say `plan`; `0055·R3`'s start-row fix.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge and the release halt on a gate the cut did not plan* — MODIFIED: the halt lists every line; a person's approval
    passes it.
  - *The cut plans a gate change in the form the check reads* — ADDED.
  - *The build checks a gate change at its phase* — ADDED.
  - *A person can approve a gate change* — ADDED.

## Impact

Changes `skills/mf-converge/scripts/gate_check.py`, `skills/mf-converge/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-build/SKILL.md`, `skills/mf-release/SKILL.md`, `skills/mf-ship/SKILL.md`, `skills/mf-ship/scripts/conduct.py`,
`README.md`, `docs/README.md`, `docs/decisions.md`, `tests/test_gate_check.py` and `tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

`0034·R9`, the recording `SHELL`; a cut that runs a `Verify:`'s `grep` pattern; a `setup` target in the bootstrap template.
