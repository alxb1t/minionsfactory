---
bump: patch
version: 0.68.1
---

# Ship fixes 2

Three gaps the optimization batch's runs hit, fixed so a run needs no person for them: a converge halt before round 1 that nothing
could answer, tests bound by the machine's load, and a worker's scratch files with no place inside its sandbox.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`0077-run-metrics`' converge halted on a red gate before round 1, a flake: no commit could answer it, a rescue only diagnosed it,
and `rejoin` logged `still converge-halted`. The flake was the stale-lock test, which must reach `_clear_stale_lock` within 1 s.
`0075-test-speed`'s timing check failed inside a parallel build at a load of 135. `0080-minions-layout`'s release fold had no
scratch path: `mktemp` writes outside a worker's sandbox.

## What Changes

- **A halt before round 1** — a converge halt in a run with no `start` line, not marked `· grant`, save a `verify: halt`, is
  answered by any commit past its head, or re-run once per run at the same head; converge opens a plain new run for it; it gets no rescue.
- **The load-bound tests** — the stale-lock test's young lock is 60 s inside `LOCK_STALE`; `tests/test_metrics.py`'s limit is 5 s;
  `_when_logged` polls the halted version's thread instead of sleeping 0.5 s.
- **A scratch place** — every worker's environment holds `TMPDIR=<primary>/.minions/tmp`, beside `UV_CACHE_DIR`, emptied at a
  run's start; `skills/mf-release/SKILL.md` Step 2 names `mktemp` for the fold's scratch file.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A converge halt answered by the person converges afresh* — MODIFIED: a halt before round 1 is answered by a commit past its
    head, or re-run once per run at it.
  - *A worker runs in an OS sandbox* — MODIFIED: its temporary files are kept in the run directory, as `uv`'s cache is.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`,
`tests/test_conduct.py`, `tests/fake_worker.py` and `tests/test_metrics.py`.

No debt card closes. Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- An amend landing while a rescue runs, and a rescue's own amend at `amend needed` — they overturn D47 and D53, which a patch
  cannot.
- A build rule placing a timing `Verify:` — it would add a decision.
- `test_run_halts_on_a_timeout`'s `< 20` s check — kept as it is.
