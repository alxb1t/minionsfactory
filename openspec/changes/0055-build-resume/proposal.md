---
bump: patch
---

# Build resume

A build that dies after its last phase resumes at simplify, so simplify and the metrics run again, and a run can tell from
disk whether the build's closing steps are done.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

isekai's `0091-the-sixth-walkthrough` hit a usage limit mid-simplify, after every phase was ticked and committed, with an
edit left uncommitted. `conduct.py` reads every phase ticked as a finished build, so a re-run goes to converge, which halts on
the dirty tree or converges with simplify unfinished; a hand `/mf-build` reports the change built and stops. Nothing on disk
tells a finished simplify from one that never ran.

## What Changes

- **`mf-build` writes `.minions/build/<change-id>.done`** after its closing steps, naming `HEAD` and simplify's outcome.
- **`conduct.py` reads every phase ticked, no converge run, and no `.done` at `HEAD`** as stage `build`, closing steps left;
  its build check fails while no `.done` names `HEAD`.
- **`mf-build` resumes at simplify** when every phase is ticked and no `.done` names `HEAD`. It restores a dirty tree's paths
  in the change's range first, saved to a patch, only while its `.closing` mark names `HEAD` and no earlier patch is there,
  and halts otherwise.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A re-run recovers what a dead station left* — MODIFIED: a build with its closing steps left is stage `build`, and
    resumes at simplify.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-build/SKILL.md`, `skills/mf-ship/SKILL.md`, `tests/test_conduct.py`
and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

`mf-simplify` writing the marker; a resume in the middle of a simplify angle; one folder per change under `.minions/`.
