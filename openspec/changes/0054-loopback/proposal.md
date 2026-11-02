---
bump: minor
backlog: [0053·R1, 0053·R2]
---

# Loopback

A repo that opts in lets its Claude workers bind loopback, so a gate that serves on `127.0.0.1` passes under the sandbox; the
exposure that brings is stated, and shown in each run's log.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

isekai's readiness proof ran `make gate` under a Claude worker, and 33 of its tests failed with `PermissionError` binding
`127.0.0.1`: its browser tests and a few unit tests serve on loopback. The sandbox refuses every bind, so every phase's gate is
red under a worker, and isekai cannot run `/mf-ship`. On macOS the only switch, `allowLocalBinding`, also reaches every service
on the Mac's loopback, so it is a person's choice per repo, not a default.

## What Changes

- **`- **Ship loopback:** yes`** in `AGENTS.md` turns on `allowLocalBinding` for that repo's Claude workers; any other value
  halts the run.
- **A Codex station is refused** in such a repo: Codex cannot bind with its network off.
- **Each run's log names what the operator's own processes listen on loopback** at its start, in such a repo.
- **No worker inherits the conductor's `VIRTUAL_ENV`.**
- **The record states the exposure**: D51, `THREAT_MODEL.md`, `mf-ship` Step 3; D15 states the anchor exception (`0053·R1`).
- **The drill** proves a loopback bind, and fails when Codex writes a trust entry (`0053·R2`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A worker runs in an OS sandbox* — MODIFIED: `Ship loopback:` turns on loopback for Claude workers; no worker inherits
    `VIRTUAL_ENV`.
  - *A run's plan is read once* — MODIFIED: the plan reads `Ship loopback:`, refuses a Codex station under it, and the run logs
    the loopback listeners.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`, `THREAT_MODEL.md`,
`tests/test_conduct.py` and `tests/escape_drill.py`. Adds `tests/test_escape_drill.py` and this change's `evidence/`. Amends D15
and D51.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A Linux container for workers; a port allowlist, or a halt on listening services; loopback for Codex; any other leaked
environment variable.
