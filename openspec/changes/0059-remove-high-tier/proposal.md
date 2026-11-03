---
bump: minor
---

# Remove the high tier

Converge keeps one depth: `tier=high`, its finders, verifiers and reference go, and D49 says so.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

v0.37's calibration found 5 of 5 at both depths: the high tier with 89 workers and 55.6 M tokens, the standard one with 2 and
4.2 M. The person, 2026-10-31 and 2026-11-03: very expensive for what it adds. gpunit's `0017` and isekai's `0093` still named
`tier = "high"` this week, at that cost.

## What Changes

- **Converge runs one depth**, one fresh worker per role; `references/high-tier.md` goes, and a `tier=` given by hand halts.
- **The run passes no tier**: `TIERS`, `_tier` and the prompt's tier clause go; a granted round keeps its `and grant=yes`.
- **The cut writes no `tier`** into a models file, and an old one's is ignored.
- **The findings files and the status log record no tier.** `mf-review-metrics` drops the tier dimension and dates a file's
  `inconclusive` count by its `## Refuted` section.
- **The record**: D49 becomes one depth; D47, D50, `README.md` and `mf-release`'s close-out lose their tier text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge runs one depth* — ADDED: one worker per role, no `tier=`, no tier recorded.
  - *Converge runs at a tier* — REMOVED.
  - *Independent workers have fresh contexts* — MODIFIED: no high-tier dispatch.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: a table per model; `## Refuted` marks the era.

## Impact

Changes `skills/mf-converge/SKILL.md`, its `generic-review.md` and `generic-security.md`, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-ship/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-release/SKILL.md`, `skills/mf-review-metrics/`,
`docs/decisions.md`, `README.md`, `tests/test_conduct.py`, `tests/fake_worker.py`, `tests/drill_resume.py` and
`tests/test_review_metrics.py`. Deletes `skills/mf-converge/references/high-tier.md`. Amends D49, D47 and D50.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The large-diff split, on *Later*; old findings files and models files, left as they are.
