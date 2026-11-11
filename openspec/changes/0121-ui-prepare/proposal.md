---
bump: minor
beside: [0118-debt-paydown-3a, 0119-debt-paydown-3b, 0120-ui-state]
---

# ui · prepare

A brief's approved npm packages are fetched once at the queue, and every worker installs them offline with scripts off.

Reading map: [design](design.md) holds the row grammar, the fetch, the workers' settings and the halt, [tasks](tasks.md) holds the phases that build them.

## Why

No worker may reach the npm registry: a worker with it in reach installs anything, through `make` if not by typing `npm`.
MF treats Python packages this way: the conductor fetches the approved wheels at the queue, and workers read them offline.

The next version puts a Node build in a target's gate, and needs the packages there, approved and offline.
A direct package no row approves must stop the version, held by a check, not by the cache alone.

## What Changes

- A `## Dependencies` row `npm:<name>` at an exact version is read at the queue; a range, a tag, a URL, a path, a git reference or an alias is refused, exit 2, nothing reserved. Python rows are unchanged.
- `conduct.py cut` and each run's start fetch the lock's tree and the approved rows into `.minions/npm-cache`, under the OS sandbox with the network open, install scripts off, the registry fixed, nothing published in the last 7 days.
- The queue prints each new package of the tree, its version and its install-script flag.
- A Claude worker, a Codex worker and `sandboxed()` run npm from that cache, offline, with install scripts off.
- A version whose tracked `package.json` holds a direct package no row approves halts before converge, naming it.
- The record: the requirements, decision D81, the principle, the threat model and the skills' prose say so.
- Requirement `A queued cut prefetches the packages it approves` (MODIFIED): its rows are Python rows, and an `npm:` row has its own.
- Requirement `A plain command runs in an OS sandbox` (MODIFIED): the command starts with npm offline, scripts off, and the cache in the run directory.
- Requirement `A queued cut fetches the npm packages it approves` (ADDED).
- Requirement `A worker's npm runs offline from the run directory's cache` (ADDED).
- Requirement `A build halts on a direct npm package no row approves` (ADDED).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

- `skills/mf-ship/scripts/conduct.py`: the row grammar, `_prefetch`, a new npm fetch, a profile with the network open, the worker settings at the Claude worker, the Codex worker and `sandboxed()`, and the build check.
- `skills/mf-plan/scripts/brief_check.py`: the plan refuses an npm row out of shape.
- `tests/test_conduct.py`, `tests/test_sandboxed.py`, `tests/test_brief_check.py`, `tests/test_cut_check.py`: the tests of [design](design.md#d6).
- `skills/mf-cut-change/scripts/cut_check.py`: read, and pinned by a test.
- `docs/decisions.md`, `docs/principles.md` and `THREAT_MODEL.md`.
- `skills/mf-ship/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md` and `skills/mf-build/SKILL.md`: the prose.
- The spec delta folds into the living spec at the release.
- The machine's pin: the fetch and the worker settings are `conduct.py`'s, so they act only once the pin moves to this release, on the person's word ([D55](../../../docs/decisions.md#d55--one-pinned-mf-release-per-machine)).

## Not in this change

- `ui/`, `package.json`, the lock, `make setup`, the npm cache's place in a target, the gate and CI steps, and the edit of [D4](../../../docs/decisions.md#d4--this-repos-own-gate-is-python-on-uv): the scaffold, a version of its own.
- Any `Ship` line, and a worker with the registry in reach.
- pnpm.
- A halt on a `Ship network:` line naming the npm registry; the fetch at `rejoin`; publish dates in the print.
- A manifest check for Python packages.
