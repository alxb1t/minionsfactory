---
bump: patch
backlog: [0062·R6, 0063·R8]
---

# Test speed

The gate's test step falls from the slowest test to the cores: the multi-case tests split per case, coverage kept out of the
fake processes, and the tests that only repeat another's assertions deleted.

Read [design](design.md) for the decisions and [tasks](tasks.md) for the phases. No requirement changes: the same assertions,
regrouped.

## Why

At `6647909` the test step takes 124 s of wall under coverage on 10 cores, and one test, `test_a_forged_release_is_not_pushed`,
takes 92 s of it: a run cannot end before its longest test. Coverage starts in every fake worker and fake `ps`, though `tests/`
is no coverage source.

## What Changes

- **The fakes start bare** — the fake worker and the fake `ps` run under `python -S`, so coverage's `.pth` never loads in them.
- **Deletions** — five mutation cases and the hand-release case of the forged-release test, `test_a_good_read_keeps_the_offline_base`
  (`0062·R6`), most of `tests/test_gate_check.py`'s topology grid,
  `test_mf_integrate_runs_its_script` and `test_the_release_gates_its_fold_fresh`, each mapped to the test that carries it.
- **A merge** — `test_a_version_cut_during_a_run_joins` into `test_a_new_executor_is_probed_mid_run` (`0063·R8`).
- **Splits** — the forged-release, after-waits, rerun-recovers, dependency-chain, no-worker-pushes, pushes-only-tagged,
  rerun-pushes, local-release and origin-down tests, one test per independent case or primary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: `skip_specs`.

## Impact

Changes `tests/test_conduct.py`, `tests/test_gate_check.py` and `tests/test_skills.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The conductor's own git cost (`_outside`, `_unpushed`); a session template repo; the low-confidence deletions; re-marking the
borderline `slow` tests.
