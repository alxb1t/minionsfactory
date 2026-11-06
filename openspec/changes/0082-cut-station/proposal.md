---
bump: minor
debt: [0063·S3, 0074·S2]
---

# Cut station

A settled brief is queued with `conduct.py cut`, and the run cuts it in a sandboxed worker of its own, then builds it: the
person's chat stays free while the cut runs.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

On 2026-11-05/06 the main thread cut most versions itself, its plan reviews in the foreground, and each helper's finish
notice landed in the chat. The person: "I see the chat is blocked … I kind of am affraid to talk with Claude to not
interrupt the work." A cut also waits on the person at Step 9, and two parallel cutters race for one id at Step 1
(`0073` on 2026-11-05). The rejoin mailbox is worker-writable (`0063·S3`), and the cut pastes the brief's `At` value into a
command unchecked (`0074·S2`).

## What Changes

- **`conduct.py cut <slug> <bump> brief=<path> [after=<ids>] --executor <executor>`** — takes the next free number under
  one lock, reserves it in `.minions/cuts/<id>`, keeps its parameters in the home folder's queue, and hands it to the live
  run, or starts one, detached, and waits for its claim.
- **The queue lock** — `cut`, `rejoin`, `grant` and a run's close share it, so two cuts never both start a run, and a cut
  or request that lands as a run ends starts the next one.
- **The mailbox moves home** — rejoin requests stand in the home folder's queue, where no worker writes (`0063·S3`).
- **The cut station** — the run makes the branch and worktree, spawns `mf-cut-change … unattended=yes` sandboxed to its
  worktree, the run directory and the brief, checks the cut on disk, then builds it as any version.
- **`cut-halted`** — a stage with no rescue; `status` and `report` show its one line; `rejoin <id>` drops the half-done
  branch and cuts again.
- **`mf-cut-change unattended=yes`** — no wait: under the brief's `decide: recommended` it takes the recommended option
  and logs a `decided by the cutter` row in the brief; the rest halt in `cut.halt`. It writes `models.toml` from the
  brief and the brief's `Cut` line. Both modes check the `At` sha's shape first (`0074·S2`).
- **The record** — a new decision; D20, D38, D41, D44, D47 and D51 amended; the threat model, the principles, `mf-ship`'s
  skill and the README.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A settled brief is queued for a cut* — ADDED: `conduct.py cut`, its lock, its number, its reservation and queue entry,
    the person's yes, start-or-join.
  - *A run cuts each queued brief in a station of its own* — ADDED: the branch and worktree by the conductor, the cutter,
    its check, then the build.
  - *The cutter reaches its worktree, the run directory and its brief* — ADDED: the cut station's sandbox.
  - *A cut halt is the plan's, answered by a re-plan and a rejoin* — ADDED: `cut-halted`, no rescue, the re-cut.
  - *An unattended cut decides by the brief's switch* — ADDED: `unattended=yes`, `decide: recommended`, the halts, the
    brief's rows and `Cut` line.
  - *The cut checks the brief's `At` value before any command takes it* — ADDED: the hex shape, the full sha.
  - *A halted version rejoins a live run* — MODIFIED: the mailbox in the home folder's queue; a request at a run's close
    starts the next run.
  - *A cut reserves its id against every open version branch* — MODIFIED: a reservation in `.minions/cuts/` is taken too.
  - *The cut commits without waiting, unless it adds a dependency* — MODIFIED: an unattended cut halts where a cut by hand
    waits.
  - *Model suggestions use exposed capabilities* — MODIFIED: models the brief names are written, not suggested.
  - *Every worktree shares the primary's run directory* — MODIFIED: `cuts/` generic, `cut.halt` the change's.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `tests/test_conduct.py`, `tests/fake_worker.py`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`
and `README.md`.

Dependencies: none — `fcntl` is the standard library's. The gate recipe stays unchanged.

## Not in this change

`mf-plan`'s close queuing the cut (`0083-plan-queues`) and `brief_check.py`; the roadmap row, which stays the operator's;
notifications, which are the UI's; a rescue that takes a decision; the cut station's cost in the run and review metrics;
`run --detach` waiting for its claim; a Linux lock other than `fcntl.flock`.
