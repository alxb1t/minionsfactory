---
version: v0.30.1
---

# Metrics baseline

Record MF's first metrics data point: v0.30.0's values, measured on its release tree.

Read [design](design.md) for the decisions and [tasks](tasks.md) for the phase. No requirement changes.

## Why

v0.30.0 shipped the metrics collector, but its release ran the v0.29.0 stations, which have no metrics step. So
`metrics/changes/` is empty, and no page can compare one release with another. A first tracked data file gives the
next release a previous release to compare with.

## What Changes

- `metrics/changes/0030-change-impact.json`: v0.30.0's values, collected on the `v0.30.0` tree by that tree's own
  collector.
- This change's release, run by the v0.30 `mf-release`, records `metrics/changes/0031-metrics-baseline.json` by
  its step 2b. The `0031-metrics-baseline` page then charts both releases.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs: true`. A data file changes no behaviour.

## Impact

Adds `metrics/changes/0030-change-impact.json`. No code, skill or doc changes.

Dependencies: none.

## Not in this change

No data file for any release before v0.30, per the 0030 proposal's exclusion of backfilled history. No collector,
catalogue or skill edit.
