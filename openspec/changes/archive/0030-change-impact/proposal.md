---
version: v0.30
---

# Change impact

A repository that declares its health metrics gets them measured at every change, kept as history, and charted.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The line ships many versions, and the gate proves each one works; nothing shows where a project is heading. A
person wants the measurable things that matter — speed, size, complexity, clarity, debt — tracked from change to
change, with the change that moved each one named, before the review spends its rounds.

## What Changes

- **A catalogue opts a repository in:** `metrics/catalogue.toml` declares each metric — its unit, which way is
  better, an optional watch threshold and noise, and the Python script that prints its value. No catalogue, no
  metrics, and the station says so.
- **A bundled collector**, `skills/mf-build/scripts/metrics.py`, run as a `uv` script with its Python pinned. It
  runs each metric script without a shell, writes one data file, and renders a self-contained HTML page: what
  moved since the previous release, then a chart per metric.
- **The build collects a draft** after its simplify pass, into `.minions/metrics/`, and names the page in its
  close-out; it never halts on a watch.
- **The release records the shipped values** on its final tree, `metrics/changes/<change-id>.json`, inside the
  release commit.
- **MF adopts itself:** its catalogue measures reading load, the contract's growth, tests, gate time, prose
  clarity, line conformance, cut amends and open backlog cards, with its metric scripts under `scripts/metrics/`.
- **Decisions:** D43 records the design; D2 lets a skill bundle a stdlib-only script; D18 names `metrics/` as
  optional.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, each an ADDED requirement:
  - *A repository opts into metrics with a catalogue* — no catalogue, no collection, stated.
  - *A metric is a Python script the collector runs without a shell* — the output contract, `unavailable`, a
    broken catalogue halting.
  - *The build collects a draft of the metrics after simplify* — into `.minions/metrics/`, the page named, no halt
    on a watch.
  - *The release records the shipped metrics in its commit* — on the final tree, before the gate.
  - *The page classifies each metric against the previous release* — the states, their order, gaps never zero.
  - *A data file records where its values came from* — revisions, `mf_version`, executor, model.

## Impact

Adds `skills/mf-build/scripts/metrics.py`, `metrics/catalogue.toml`, `scripts/metrics/` and their tests. Changes
`skills/mf-build/SKILL.md`, `skills/mf-release/SKILL.md`, `docs/decisions.md`, `AGENTS.md`, `README.md` and
`docs/README.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none — the collector and the metric scripts use the standard library; `uv` runs them, as it runs the
gate. The gate recipe stays unchanged.

## Not in this change

No fix loop on a breach, no reason recorded for an accepted breach, no narrative report, no hotspot scatter or
layer matrix, no history backfilled, no run records and no cross-repository learning. No catalogue is written for
another repository; each adopts in a version of its own. The bootstrap, converge and the cut are unchanged. This
change's own build and release run the installed v0.29.0 skills, so MF's first tracked data file comes with the
release after the skill links are reinstalled.
