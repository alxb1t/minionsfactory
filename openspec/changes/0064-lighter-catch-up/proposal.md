---
bump: minor
backlog: [0061·R3, 0061·S1]
---

# Lighter catch-up

The catch-up after integrate costs only what the merge needs: a green gate is recorded by its tree and never run twice on the
same tree, and a merge the fixed rules reproduce is clean by recomputation, with no review.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

MF's run `20261103-192106`, `0060-gate-planning`: the catch-up worker ran 873 s and 167,167 tokens to gate the head integrate had
just gated and to review one `CHANGELOG.md` the rule had settled. On one head after converge the gate runs five times — integrate,
converge's start and verify, the release's precondition and its post-fold run — at 4–6 minutes each; only the last is on a
changed tree.

## What Changes

- **`gate_run.py`** — runs `make gate`, records a green run by its tree, and reuses the record on the same clean tree with the
  same dry run; every station gates through it; the release's post-fold gate runs fresh.
- **`integrate.py replay <merge>`** — rebuilds a merge with the fixed rules alone and compares trees.
- **A by-rule catch-up** — every merge replays → both findings files clean with `## By rule`, no worker.
- **The integrate commit names every settled path** — the rule, the union, the person, a test fixed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — ADDED: replay, its ancestry check,
    `## By rule`, the count.
  - *The integrate merge commit names every path it settled* — ADDED: the four body-line kinds.
  - *The skills run the repository's `make gate`* — MODIFIED: through `gate_run.py`, its record and its reuse.
  - *The release ships only a reviewed head* — MODIFIED: a by-rule catch-up runs no verify round.
  - *Converge keeps a status log* — MODIFIED: the `by rule` event.
  - *The release records the gate's time* — MODIFIED: the time from a run or a reused record.
  - *Independent workers have fresh contexts* — MODIFIED: `mode: by-rule`, `workers: 0`.

## Impact

Changes `skills/mf-converge/scripts/gate_run.py` (new), `skills/mf-integrate/scripts/integrate.py`, the `mf-build`,
`mf-converge`, `mf-integrate` and `mf-release` skills, `README.md`, `docs/principles.md`, `docs/decisions.md` (D45),
`THREAT_MODEL.md`, `tests/test_gate_run.py` (new), `tests/test_integrate.py`, `tests/test_skills.py`, `tests/test_conduct.py` and
`tests/fake_worker.py`. `conduct.py` is unchanged.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A conductor change; reusing a record across a changed tree, or a red one; a by-rule catch-up over a commit that is not a merge.
