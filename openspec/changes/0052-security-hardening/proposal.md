---
bump: minor
backlog: [0050·S2, 0050·R6, 0050·S3, 0051·S4, 0051·S9]
---

# Security hardening

A confused or prompt-injected worker, on Claude or Codex, cannot do lasting harm outside its version.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

A Claude worker runs under an allowlist that reads a command's text, and `make`, `uv` and `python3` run any code. Measured: a
script a worker ran deleted a file in `~` under the allowlist and under auto mode, and Claude Code's OS sandbox refused it.
Codex has a sandbox, with its network on and no deny list. Every worker can push.

## What Changes

- **Every Claude worker runs in Claude Code's sandbox**: writes to the repo alone, listed domains, no credential reads by a
  script or the `Read` tool, and no project settings or `.mcp.json` at its start.
- **`Ship network:`** in `AGENTS.md` adds domains.
- **A Codex worker's network is off.**
- **No worker pushes**: under `merge=yes` the release stops at its merge, and `conduct.py` pushes, from a scratch repo that reads
  no repo's config, to the URLs a run kept in the home folder before its first worker. A repointed `origin` halts every remote
  call until a person clears it.
- **A run's plan is read once**, and a person's commit during a run halts before integrate.
- **The record states the boundary**: D47, a new decision, and `THREAT_MODEL.md`.
- **An escape test** runs on a real worker and a real subagent, and the drill runs under the sandbox.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The release merges and pushes on the person's yes* — MODIFIED: under `merge=yes`, the conductor pushes.
  - *The ship station takes cut versions to the default branch* — MODIFIED: an OS sandbox on both executors.
  - *A worker runs in an OS sandbox* — ADDED.
  - *No worker pushes* — ADDED.
  - *A run's plan is read once* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, the `mf-ship` and `mf-release` skills, `docs/decisions.md`, `docs/principles.md`,
`THREAT_MODEL.md`, `tests/test_conduct.py` and `tests/fake_worker.py`. Adds `tests/escape_drill.py` and this change's `evidence/`. Amends D17 and D47, adds
D51.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A hostile repo, and a container for it; Codex's reads of `~`; auto mode, which blocked nothing; `0034·R9`.
