---
bump: minor
---

# Cut awake

A cut run by hand holds the Mac awake while it works, as `conduct.py run` does for a run.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

A cut can take more than 20 minutes, and the Mac sleeps under it. On 2026-11-06 the person: "while it is cutting the change, I
don't want the laptop to go to sleep". `0069-caffeinate` held the Mac for a live run alone; its Non-Goals named "a hold for a
station run by hand".

## What Changes

- **The hold** — `skills/mf-cut-change/scripts/awake.py start <change-id>` starts `caffeinate -is -t 7200 -w <the session's
  host pid>`, detached, and records the hold's pid in `.minions/awake/<change-id>`; `stop <change-id>` kills it.
- **The cut** — Step 1 starts the hold and prints its line; every halt from Step 1 on, and Step 11's close-out, stop it; the
  skill names the lid.
- **The record** — D57 and the run directory's requirement name `awake/` among its generic folders.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A cut run by hand holds the machine awake* — ADDED: the cut's hold, its 2 h bound, its record by change id, its stop,
    no `caffeinate`, the lid.
  - *Every worktree shares the primary's run directory* — MODIFIED: `awake/` among the generic folders.

## Impact

Adds `skills/mf-cut-change/scripts/awake.py` and `tests/test_awake.py`. Changes `skills/mf-cut-change/SKILL.md`,
`tests/test_skills.py` and `docs/decisions.md` (D57).

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A hold for the plan, the build, converge or the release run by hand; Linux, where `caffeinate` is absent; the unattended
background cut; keeping a closed lid awake.
