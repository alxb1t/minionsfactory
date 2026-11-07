---
bump: minor
version: v0.69
after: [0082-cut-station]
---

# Plan queues

A hard `mf-plan` close checks its brief with `brief_check.py`, names each change's models and switch, asks once
"confirm, and queue it?", and on yes queues the cut with `conduct.py cut`: the person plans the next version in the same
chat.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`0082-cut-station` gives the run a cut station, but a plan still ends on `Next: /mf-cut-change …` and the person, or the
main thread, cuts. The person wants the plan to dispatch the cut and return to the chat. A cutter's doubt should be rare
(P2): a brief that is light, has no `At` line, no `## For the cut`, or a check out of shape is the cutter's doubt made at the
plan, so it is caught there.

## What Changes

- **`skills/mf-plan/scripts/brief_check.py <brief>`** — exit 1 on a title that is not `hard`, no `At <sha>, <date>.` line,
  an empty `## For the cut`, an Acceptance or `Verify:` command that breaks `verify_check.py`'s shell rules, or an item whose
  slug, bump, `after` or models line is out of shape.
- **`mf-plan`'s close** — `## For the cut` names per change its slug, bump, `after`, `debt`, `decide: recommended` and the
  models of the build, converge, release and the cut station; `brief_check.py` must pass; the close shows the items and
  `conduct.py status`, then asks "confirm, and queue it?" — yes, or `then=ship` given up front, runs `conduct.py cut` per
  change in order and reaches every merge and push in the run; no ends on one `Next: /mf-cut-change` line per change.
- **Its role and *Never*** — the plan queues a cut on the person's yes; it still never cuts.
- **The record** — a new decision for the plan's close.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A hard brief is checked before it is queued* — ADDED: `brief_check.py`, its checks and exits.
  - *The plan's close queues the cut on the person's yes* — ADDED: the question, `then=ship`, `conduct.py cut` per change,
    the yes it is.
  - *The plan station writes the brief after every round* — MODIFIED: `## For the cut`'s fields, the models and the switch.

## Impact

Adds `skills/mf-plan/scripts/brief_check.py` and `tests/test_brief_check.py`. Changes `skills/mf-plan/SKILL.md`,
`tests/test_skills.py` and `docs/decisions.md`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The cut station itself (`0082-cut-station`); the roadmap row, which stays the operator's; notifications; a light close
queuing anything; a brief check inside the cut.
