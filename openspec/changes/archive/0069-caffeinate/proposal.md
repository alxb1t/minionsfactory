---
bump: minor
version: v0.58
after: [0068-pinned-release]
---

# Caffeinate

While an `mf-ship` run is live, the Mac does not go to sleep.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phase, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

A sleeping Mac stops every worker mid-station, and the run resumes only on a re-run, at a cost. Through the night of 2026-11-04
the person's session started `caffeinate -is -w <pid>` by hand for each run.

## What Changes

- **The hold** — the conductor starts `caffeinate -is -w <its pid>` at its start, ending with it; none under fake workers.
- **The record** — the `start` line says whether the machine is held; `mf-ship`'s Step 3 names the lid.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A live run holds the machine awake* — ADDED: the hold, its absence, the `start` line, the lid.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md` and `tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Keeping a closed lid awake; `-d`; watching the hold itself.
