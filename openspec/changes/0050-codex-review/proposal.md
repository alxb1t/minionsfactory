---
bump: minor
backlog: [0040·S2, 0040·S4, 0048·S2, 0048·S3]
---

# Codex as reviewer

Each station's executor is chosen per version, and a converge on Codex is proven to work.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

`conduct.py run --executor` sets one executor for a whole run, and Codex has never run a station. A second vendor's review
beside a Claude build is the cross-model check the line wants, and the Codex worker row has never been proven. Scratch
probes show it can: `conduct.py agent --executor codex` edited, committed and gated, and `codex exec` started a subagent.
Before a Codex worker runs a real version, its reach must be right.

## What Changes

- **`executor` in the models file** — per station, absent meaning the run's. No flag.
- **Validation** — an unknown executor, or `codex` with a `claude-*` model, halts that version before a worker starts.
- **One probe per executor** — any failure stops the run.
- **A worker's reach is the primary and the open worktrees**, on Codex and Claude alike, never the directory holding them.
- **`integrate.py` is loaded once**, before the first worker, and a change to the local git config halts a dependent's merge.
- **Proof** — the review calibration on Codex, and a cross-host run: a Claude build, a Codex converge, a Claude release.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station takes cut versions to the default branch* — MODIFIED: the station's executor, and the reach.
  - *A station's executor comes from the models file* — ADDED.
  - *A worker's reach stops at the repository* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `docs/decisions.md`
and `tests/test_conduct.py`. Adds this change's `evidence/calibration.md`. Amends D47.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Codex as the builder or the releaser, allowed but unproven; different models inside one converge run; parsing Codex
`--json`; a Codex usage limit's wording; `tier=high` on Codex; refusing a changed `Ship tools:` line.
