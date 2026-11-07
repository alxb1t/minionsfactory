---
bump: minor
after: [0088-paydown-2, 0090-supervisor-merge]
debt: [0082·S5, 0083·S3]
---

# Cut halts

A queued cut no longer stops on what the plan could have settled: the brief approves each package, the queue holds that
approval, a cut halt names its answer, and a hand cut never takes a queued version.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

A fresh repo's first queued cut halted on its `## Dependencies` after 57 s; the halt sat unseen for 19 minutes, its closing
line saying only `needs <id> a fix`; the packages were approved in chat, where no station reads them, and the planning thread
then cut the queued id by hand. Each stop was one the plan could have settled. The brief check also still passes
`## For the cut` forms it does not parse (`0083·S3`; 0088's review R10, security S7 and S8).

## What Changes

- **The brief** — a hard brief holds a `## Dependencies` section, `None.` or a row per package: item, package, constraint,
  why. The plan lists each package as a fact and asks the person to approve it.
- **The brief check** — requires that section, and reads `## For the cut` by a strict line grammar: every line a head, a
  models or Acceptance line, its continuation, a blank or the cut's line; every checked line printable; one heading form
  per checked section.
- **The queue** — `conduct.py cut` copies the item's `## Dependencies` rows into its home-queue entry, and a `rejoin` of a
  queued cut keeps them, taking a row they lack only with the person's `--yes <hash>`; the station halts a cut whose
  `design.md` lists a package or constraint outside them.
- **The cut** — unattended, a package the brief's rows list is committed without a halt; a hand cut halts on an id the
  queue holds.
- **The answers** — a cut halt the plan answers ends `needs <id> its brief answered (/mf-plan …), then conduct.py rejoin
  <id>`, in the log, `status`, `report` and the closing line.
- **The plan in the background** — `mf-plan`'s fact-finding and checks run in background helpers, and the chat stays free.
- **The record** — D62; D38 and D58 amended; the principle *A new dependency halts for a person*; `mf-ship`'s
  `cut-halted` row; `THREAT_MODEL.md` (`0082·S5`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The build approves a dependency only as the cut committed it* — MODIFIED: an unattended cut commits the rows the brief
    approves for its item, and halts on any other.
  - *The cut commits without waiting, unless it adds a dependency* — MODIFIED: unattended, a dependency the brief approves
    is no halt.
  - *The plan station checks the line's rules before its first round* — MODIFIED: the facts and checks run in background
    helpers; a package the version adds is a fact and a question.
  - *The plan station writes the brief after every round* — MODIFIED: the `## Dependencies` section.
  - *A cut reserves its id against every open version branch* — MODIFIED: a hand cut of an id the queue holds halts,
    naming the answer.
  - *A settled brief is queued for a cut* — MODIFIED: `cut` copies the item's `## Dependencies` rows into its entry.
  - *A run cuts each queued brief in a station of its own* — MODIFIED: a cut passes only with its `design.md`'s packages
    inside those rows.
  - *A cut halt is the plan's, answered by a re-plan and a rejoin* — MODIFIED: the halt names its answer; a rejoin keeps
    the queued rows and takes a new one only with the person's `--yes <hash>`.
  - *An unattended cut decides by the brief's switch* — MODIFIED: a `## Dependencies` is no longer always a halt.
  - *A hard brief is checked before it is queued* — MODIFIED: the `## Dependencies` section, the line grammar, the
    printable rule and the heading rule.
  - *The plan's close queues the cut on the person's yes* — MODIFIED: the close shows the `## Dependencies` rows.

## Impact

Changes `skills/mf-plan/SKILL.md`, `skills/mf-plan/scripts/brief_check.py`, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-ship/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`,
`tests/test_brief_check.py`, `tests/test_conduct.py` and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Notifications of a halt — `ui · control`.
- Judging whether one constraint is looser than another — a constraint is approved as written
  ([D4](design.md#d4)).
- The rest of `0082·S5`'s reach — a switch or a decision row a cutter plants — stays with the re-plan's close, which shows
  each item before the yes ([D8](design.md#d8)).
