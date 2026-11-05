---
bump: minor
---

# Debt rename

`.minions/backlog.md` becomes `.minions/debt.md`, its lock `debt.lock`, the proposal key `debt:`, and the word "backlog" leaves the
line's record; a run moves an old file to its new name at its start.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Every card is a deferred check-loop finding with `path:line`, priority, fix and trigger — technical debt a paydown drains, not a list
of work to come, which the vault's roadmap holds. The person settled the word on 2026-11-03.

## What Changes

- **The file and the lock** — `.minions/debt.md` and `.minions/debt.lock` in `conduct.py`, converge's Step 9, the release, the run
  metrics, the review metrics and their tests; the status-log event `debt`; the release reads `debt:` or an older `backlog:`.
- **The word** — D16, D15, the principles, `mf-plan`, the cut, the review references, `AGENTS.md`, `CONTRIBUTING.md`,
  `THREAT_MODEL.md`; `scripts/metrics/backlog.py` becomes `debt.py`, the metric id `open-backlog-cards` kept.
- **The move** — `conduct.py run` moves `backlog.md` and a stale `backlog.lock` at its start, under the claim; both files standing, or
  a young old lock, halts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge keeps deferred work in one repository backlog* — REMOVED, as *Converge keeps deferred work in one repository debt
    file* — ADDED.
  - *The release does not read the backlog* — REMOVED, as *The release does not read the debt* — ADDED: `debt:` or `backlog:`.
  - *A repeated finding escalates*, *Converge keeps a status log*, *The plan station reads the target without moving it*, *The plan
    station checks the line's rules before its first round*, *A halt stops only its version, and a re-run resumes*, *Converge
    continues an unfinished run*, *A person can grant one more round*, *A converge halt answered by the person converges afresh* —
    MODIFIED: the file, the lock and the word.
  - *Every worktree shares the primary's run directory* — MODIFIED: the file, the lock, and the move at a run's start.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`,
`skills/mf-converge/references/generic-review.md`, `skills/mf-release/SKILL.md`, `skills/mf-plan/SKILL.md`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-review-metrics/scripts/review_metrics.py`, `scripts/metrics/run.py`,
`scripts/metrics/backlog.py` (to `debt.py`), `metrics/catalogue.toml`, `docs/decisions.md` (D15, D16), `docs/principles.md`,
`AGENTS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md`, `tests/test_conduct.py`, `tests/test_metric_scripts.py` and
`tests/test_review_metrics.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The per-change layout — `minions layout`; the debt in a tracker; the metric id `open-backlog-cards`, the archived proposals'
`backlog:` keys, the `metrics/changes/*.json` history and the `Why: 00NN-backlog-…` citations, which stay as written.
