---
bump: minor
version: v0.63
---

# Code metrics

Each release records its codebase's shape and its tests' health in its tracked data file: the largest module, the modules over a
thousand lines, the complex functions, coverage, suppressions, size, dependencies, and the test step's time, slowest test and slow
tests, from a junit report the gate now writes.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

`metrics/changes/<id>.json` records words of instruction and a test count, nothing of the code's structure or the suite's time; the
gate keeps no per-test duration. The UI will chart these as a trend, release over release.

## What Changes

- **`scripts/metrics/codebase.py`** — the codebase's metrics, read from the tree, Ruff's `C901` for complexity.
- **The gate's junit report** — `make gate`'s pytest step writes `.minions/test-report.xml`; the test metrics read it, and
  `coverage.xml` gives total coverage.
- **The catalogue** — the `code` group's entries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Each release records its codebase* — ADDED: the code and test metrics, their sources, and a gap for a missing or stale report.

## Impact

Changes `Makefile` (the gate's pytest line), `scripts/metrics/codebase.py` (new), `metrics/catalogue.toml`, `AGENTS.md` (the gate's
account) and `tests/test_metric_scripts.py`.

Dependencies: none. The gate recipe gains one flag, quoted in its task.

## Not in this change

The run's metrics — `0077-run-metrics`; a page — the UI's; Ruff's complexity in the gate itself.
