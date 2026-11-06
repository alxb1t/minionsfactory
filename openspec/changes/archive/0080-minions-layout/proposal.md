---
bump: minor
version: v0.66
---

# Minions layout

Everything about one change lives in one folder, `.minions/changes/<change-id>/`: its findings, status log, patch, models file,
integrate notes, build marks, rescue diagnosis, release mark, gate-check export and worker logs. A run moves an old layout at its
start; the review metrics read both.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`.minions/` spreads a change across seven folders by kind, and worker logs by run stamp; a person or the coming viewer reading one
version opens all of them. The person settled the layout on 2026-11-01: `.minions/` is hard to navigate.

## What Changes

- **One folder per change** — `.minions/changes/<change-id>/` holds `review.md`, `security.md`, `status_log.md`, `diff.patch`,
  `models.toml`, `integrate.{md,red,resolved}`, `build.{done,halt,closing,discarded.patch}`, `rescue.md`, `release.held`,
  `gate-check/` and `logs/<stamp>-<station>[-<n>].log`; `grants/`, `runs/`, `gate/`, `replay/`, `metrics/` and `debt.md` stay.
- **One helper** — `_change_dir(primary, id)` in `conduct.py` and in each standalone script.
- **The move** — `conduct.py run` moves an old layout at its start, under the claim, before any worker; a hand-run station or
  script on an old layout — integrate, release, converge, build, their scripts — halts, naming `/mf-ship`.
- **Both layouts read** — `review_metrics.py` reads a repo no run has moved.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Every worktree shares the primary's run directory* — MODIFIED: the per-change folder, the move, the hand-run halt.
  - *A station keeps a log per spawn* — MODIFIED: logs under the change's `logs/`, the probe's under `runs/`.
  - *No station deletes a findings file or the diff patch* — MODIFIED: the run's move is no station's act.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: both layouts read.
  - *Converge keeps a status log*, *Converge and the release halt on a gate the cut did not plan*, *Model suggestions use exposed
    capabilities*, *The integrate station merges the default branch into the next version*, *A semantic conflict is handed to the
    person with the merge open*, *The ship station takes cut versions to the default branch*, *A halt stops only its version, and a
    re-run resumes*, *A version declares what it builds on*, *A re-run recovers what a dead station left*, *A station's executor
    comes from the models file*, *Converge runs one depth*, *A halted version is rescued in its run*, *A verify halt is diagnosed by
    the run* — MODIFIED: the new paths.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`, `skills/mf-converge/scripts/gate_check.py`,
`skills/mf-build/scripts/metrics.py` (its `_change_dir` renamed `_spec_dir`), `skills/mf-review-metrics/scripts/review_metrics.py`,
`scripts/metrics/run.py`, the `SKILL.md` of mf-build, mf-converge (and `references/worker.md`), mf-integrate, mf-release, mf-rescue,
mf-cut-change, mf-ship and mf-review-metrics, `docs/decisions.md`, `docs/principles.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`THREAT_MODEL.md`, and `tests/test_conduct.py`, `tests/fake_worker.py`, `tests/test_review_metrics.py`, `tests/test_metric_scripts.py`,
`tests/test_integrate.py`, `tests/test_gate_check.py`, `tests/drill_resume.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The viewer; the debt in a tracker; moving `grants/`, `runs/`, `gate/`, `replay/` or `metrics/`; the bootstrap's own templates beyond
`CONTRIBUTING.md`'s.
