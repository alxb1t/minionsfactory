---
bump: patch
version: 0.47.2
backlog: [0054·S3, 0054·R4]
---

# Loopback removal

`Ship loopback:` goes: no repo uses it, and while it exists a worker can turn it on for every later run. The parts of
`0054-loopback` that are not about the line stay.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

v0.47.0 added `- **Ship loopback:** yes` for isekai, whose gate served on `127.0.0.1`. isekai then took those tests out of its
gate, so no repo declares it. On macOS `allowLocalBinding` reaches every local service, and a worker can write the line into
`AGENTS.md` (`0054·S3`). A gate that needs loopback needs a Linux container, where loopback is private.

## What Changes

- **No worker binds loopback**, in any repo: `allowLocalBinding` and the `Ship loopback:` reader go.
- **A repo that still declares the line halts the run**, naming it as removed.
- **The Codex refusal under it and the `loopback` log events go.**
- **The drill's loopback row goes**; its refused bind, `_codex_held` and `env -u VIRTUAL_ENV` stay.
- **The record**: D51, `THREAT_MODEL.md` and `mf-ship` Step 3 say no loopback, and a gate that needs it needs the container.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A worker runs in an OS sandbox* — MODIFIED: no worker's sandbox has `allowLocalBinding`.
  - *A run's plan is read once* — MODIFIED: a declared `Ship loopback:` halts the run; no Codex refusal, no `loopback` events.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`, `THREAT_MODEL.md`,
`tests/test_conduct.py`, `tests/escape_drill.py` and `tests/test_escape_drill.py`. Amends D51.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The container; the `VIRTUAL_ENV` fix, `_codex_held`, the refused-bind row and D15's line, which stay;
`metrics/changes/0054-loopback.json`, which is history.
