---
bump: minor
version: 0.45
backlog: [0049·S4, 0049·S8, 0049·S10, 0049·R6, 0049·R7, 0049·R8, 0049·R9, 0049·R10, 0049·R11, 0049·R13, 0049·R16, 0047·S3, 0048·R8, 0038·N2, 0044·R12, 0050·R1, 0050·R2, 0050·R3, 0050·R4, 0050·R9, 0050·S4]
---

# Reliability paydown

A Claude run is safe on a real project: what it may push, a stop that survives a death, a real-death drill, and the controls
a person needs.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The person wants MF safe and reliable before real projects. The backlog stands at 31 cards, and a few of them matter on a
real repository: a run would push a person's own commit on `main`, a death erases a stop, and resume has met only fake workers.
Stopping a run takes hand commands, and each extra round has taken a hand-written prompt.

## What Changes

- **A run pushes only merges of tagged releases**, and halts naming anything else.
- **A stop survives a death** — a resumed release re-reads its flag, and a person's refusal leaves a mark.
- **No hook runs in a run**, and `make gate` is the only check.
- **`core.hookspath` is allowed**, `lfs.repositoryformatversion` still halts, and `mf-ship.localorigin` goes.
- **`/mf-ship stop`** ends a live run, killing only a conductor that keeps its start time, and
  **`/mf-ship grant <change-id>`** gives a capped version one more round.
- **A run stops at its start on a skill with no link.**
- **Converge dispatches in the foreground.**
- **The fake worker moves out of the test file**, for the gate's speed.
- **A drill** kills real workers in a scratch repository.
- **`THREAT_MODEL.md` lists its open gaps**, and the one-line drift cards are paid.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A re-run recovers what a dead station left* — MODIFIED: what a run may push, a stop, no `localorigin`.
  - *A person can stop a run* — ADDED.
  - *A person can grant one more round* — ADDED.
  - *A run needs its skills linked* — ADDED.
  - *No hook runs in a run* — ADDED.
  - *Converge never ends a turn with a worker running* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, the `mf-ship`, `mf-converge`, `mf-release` and `mf-cut-change` skills,
`THREAT_MODEL.md`, `AGENTS.md`, `docs/decisions.md`, `docs/principles.md`, `CHANGELOG.md` and `tests/test_conduct.py`. Adds
`tests/fake_worker.py`, `tests/drill_resume.py` and this change's `evidence/`. Amends D11 and D47.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The hostile-worker cards left for Codex hardening, `0049·S5`'s hostile route among them; an LFS repo, whose objects a run
cannot upload, which is what stays of `0049·R15`; `0034·R9`; a run that waits out a usage limit; conflict resolve.
