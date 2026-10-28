---
version: v0.31.1
backlog: [0023·R7, 0028·R3, 0028·S1, 0030·R12, 0030·S2, 0032·N1]
---

# Release patches

`mf-release` ships a `vX.Y.Z` patch as itself, the line says what a patch may hold, and the backlog's small cards
are paid down.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the corrected requirements.

## Why

`mf-release` writes `<version>.0` for every tag, heading and commit, so a patch `v0.30.1` would ship as
`v0.30.1.0`; v0.30.1 shipped right only because its agent departed from the text. A6 sends a patch to the human
because `AGENTS.md` says nothing about patches. Six cards — a branch retiring its own tests, a `script` read as a
`uv` option, a path scrub with gaps, a template rule out of date, an unnamed default branch, and a moot design
quote — wait on small fixes.

## What Changes

- **The patch form:** `mf-release` names `<tag>` — `vX.Y` → `vX.Y.0`, `vX.Y.Z` as itself — for the tag, the
  CHANGELOG heading, the commit, precondition 5, the push and the close-out. D19's line gains the patch form.
- **What a patch may hold**, stated in `AGENTS.md`: fixes, never a new station, parameter, decision or
  requirement.
- **Who may retire a test (`0028·S1`):** only a decision in force at the base, in `I16`, `T5`, the coverage-trace
  pass, D39, the principle and the bootstrap's `AGENTS.md` template (`0028·R3`).
- **The collector:** a `script` starting with `-` is a broken catalogue (`0030·S2`); the path scrub blocks a match
  only on a name character (`0030·R12`).
- **Small text:** `mf-plan` names how it finds the default branch (`0032·N1`); `README.md` links the archived 0027
  design; `0023·R7` is closed as moot, its design archived.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, each a MODIFIED requirement, corrected:
  - *A test is deleted or merged only as the design's table names it* — the retiring decision is in force at the
    base.
  - *Review judges test cost and traced coverage* — the coverage-trace pass accepts only such a decision.
  - *A metric is a Python script the collector runs without a shell* — a `script` outside the repository, or
    starting with `-`, is a broken catalogue.

## Impact

Changes `skills/mf-release/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-converge/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-bootstrap/templates/AGENTS.md.tmpl`,
`skills/mf-build/scripts/metrics.py`, `tests/test_metrics.py`, `docs/decisions.md`, `docs/principles.md`,
`AGENTS.md` and `README.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The gate-recipe hardening — `0023·S1`, `S5`, `R8` — is its own version. No new station, parameter, decision or
requirement: this is a patch. No archived change is edited; `0023·R7` is closed, not fixed.
