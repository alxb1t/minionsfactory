---
bump: minor
after: [0091-cut-halts]
---

# Lighter build and cut

The cut reviews its plan once, and again only when a fix after the first changes a decision or a task, each time by a fresh
worker; a build whose highest phase is moderate runs whole on Sonnet 5.5 · high.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Every cut from 0086 to 0091 ran a first and a second plan review, 18–52% of a cut's cost, and 0086, 0088 and 0090
continued the first reviewer by a message, which D40 rejects. A plan the cut gets wrong is now repaired in the run — rescue, the supervisor, the amend
round — at about $3 a time. A build on the strongest model costs about twice a Sonnet build per line, for phases a Sonnet
build handles with no visible loss.

## What Changes

- **The plan review** — Step 8.5 of `mf-cut-change` runs a first review always, and a second only when a fix after the first
  changes a `design.md` decision or a brief's `## Decisions` row, a `C` row included, or adds or removes a task. A simple fix
  is not reviewed again. Reverses 0074 D4.
- **Fresh reviewers** — every plan review is a new worker; a message to an earlier reviewer is no review.
- **The moderate build** — *Suggesting models*' moderate row names Sonnet 5.5 · high, where the session offers it; a
  build whose highest row is the moderate one runs whole on it. `mf-plan`'s models line follows it.
- **The record** — D65; D7, D40 and D41 noted; D42 names the skills test this change adds as the one scan it accepts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Model suggestions use exposed capabilities* — MODIFIED: a build whose highest row is the moderate one is suggested
    Sonnet 5.5 · high, where the session offers it.
  - *A fresh worker reviews the plan before the cut commits* — MODIFIED: the second review is conditional, and every
    review is a new worker.
  - *An unattended cut decides by the brief's switch* — MODIFIED: a `decided by the cutter` row calls the second review.

## Impact

Changes `skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md`, `docs/decisions.md` and `tests/test_skills.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- A fresh build session per phase — about $1 a build, and it needs a guard against re-spawning without end.
- A model per phase — one model a change.
- A second review after a simple fix — the run's repairs catch what it would.
