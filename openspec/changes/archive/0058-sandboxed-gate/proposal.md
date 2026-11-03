---
bump: patch
version: v0.47.1
---

# Sandboxed gate

MF's own `make gate` passes inside a worker's sandbox, so MF can ship itself with `/mf-ship`.

Read [design](design.md) for the decisions and [tasks](tasks.md) for the phases. No requirement changes: the tests change,
and the conductor does not.

## Why

MF's `/mf-ship` of `0055`, `0056` and `0057` halted all three builds in phase 1: 26 tests in `tests/test_conduct.py` start
`conduct.py run`, which reads its own start time with `ps -o lstart=` for the claim, and a Claude worker's sandbox refuses
`ps`. A real run's conductor is outside the sandbox, so only the tests meet it; since v0.46.0, MF has been built by hand.

## What Changes

- **A fake `ps` first on `PATH`** for every test in `tests/test_conduct.py`, through an autouse fixture: a fixed start time for
  a live pid, nothing for a dead one, and a name and start time a test registers for a process it starts.
- **`_no_ps` stays** for the tests that need `ps` to fail.
- **A real sandboxed worker runs `make gate`** as the proof.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: `skip_specs: true`. The tests change, no behaviour does.

## Impact

Changes `tests/test_conduct.py`. Adds this change's `evidence/`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

How the conductor reads start times; `mf-bootstrap`'s templates. The vault's readiness checklist is the person's.
