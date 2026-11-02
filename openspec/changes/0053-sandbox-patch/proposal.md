---
bump: patch
backlog: [0052·S7, 0052·S8, 0052·S9, 0052·R18, 0052·R6, 0052·R7, 0052·R8, 0052·R10, 0052·R13, 0052·R14, 0052·S12, 0051·R11, 0051·R14, 0051·R13, 0051·S8]
---

# Sandbox patch

A Claude worker runs sandboxed or not at all, a forged merge is refused, and the threat model claims only what a run holds.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

`0052` put every worker in an OS sandbox and gave the push to `conduct.py`, and its converge carded where that falls short. A
Claude sandbox that cannot start runs commands unsandboxed, and the run does not notice (`0052·S7`). A worker can write the
shape of a tagged release, and `conduct.py` pushes it with no gate or converge behind it (`0052·S8`). A usage limit that killed
converge inside the backlog lock left a halt with no way out but a whole new round. MF runs on a real project next.

## What Changes

- **A Claude worker's sandbox fails closed**, and the probe proves a write outside the worker's reach is refused, on each
  executor.
- **`conduct.py` pushes only a release a run took to its release**, recorded in the home folder, judged against `origin`'s real
  head, pushing the sha it checked.
- **A stale `backlog.lock` is cleared** at a run's start, and a converge halted on it resumes at Step 9 with no new round.
- **The record states the boundary**: `THREAT_MODEL.md`, D47, D51, and the anchor rule's exception for the accepted class.
- **A Codex worker starts with its trees untrusted**, so a worker-written `.codex/` starts nothing: a planted
  `.codex/config.toml` in `tests/escape_drill.py` showed its MCP server running (`0052·S12`).
- **The cards** `0052·R6`, `R7`, `R8`, `R10`, `R13`, `R14` and `0051·R14` are paid; `0051·R13` and `0051·S8` close as moot.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A worker runs in an OS sandbox* — MODIFIED: a sandbox that cannot start ends the worker; a Codex worker's trees are
    untrusted.
  - *The ship station judges every station from disk* — MODIFIED: the probe's gate needs a write out refused.
  - *No worker pushes* — MODIFIED: only a release a run took to its release is pushed.
  - *A re-run recovers what a dead station left* — MODIFIED: the push rule reads the release ledger and `origin`'s real head.
  - *Every worktree shares the primary's run directory* — MODIFIED: a run clears a stale backlog lock.
  - *Converge continues an unfinished run* — MODIFIED: a halt on the backlog lock resumes at Step 9.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: the lock's halt needs no person.
  - *Anchored harms block, and drift has its own tier* — MODIFIED: a route in the threat model's accepted class does not block.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, the `mf-ship`, `mf-converge` and `mf-release` skills,
`skills/mf-converge/references/generic-security.md`, `docs/decisions.md`, `THREAT_MODEL.md`, `tests/test_conduct.py`,
`tests/fake_worker.py` and `tests/escape_drill.py`. Adds this change's `evidence/`. Amends D47 and D51.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Linux, stated as unproven; a paydown of the other cards; a way out of any non-cap converge halt but the lock's; a pid in
`backlog.lock`; a guard against a release forged inside its own release window; `0052·S15` and the accepted class.
