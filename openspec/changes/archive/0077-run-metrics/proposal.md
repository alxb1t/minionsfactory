---
bump: minor
version: v0.64
---

# Run metrics

Each release records its run in its tracked data file — the minutes per stage, the person's waits, the rounds, the halts, the
cost and tokens per station, review's yield per role — and converge records each role's executor, model and effort.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`metrics/changes/<id>.json` holds twelve values of the tree and none of the run that made it: a release's lead time, its
bottleneck, its cost and its review's yield are read today from logs by hand, and the UI that will chart them needs one tracked
series. Converge records no executor or effort per role, and the page sums every role's tokens into one number.

## What Changes

- **Converge's record** — each `verdicts` line names its role's executor, model and effort; a card gains `**Round:**`; the spawn
  line names the effort; a station spawned twice in one stamp keeps both logs.
- **Run metrics** — `scripts/metrics/run.py`, catalogue scripts read at the release's collect: minutes per stage, the lead, the
  waits, rounds, halts, rescues, commits, cost and tokens per station, review's yield, escapes, the debt's flow.
- **The review metrics data** — the status log's tokens parsed per role in every form they were written; Codex workers' tokens
  read from the operator's Codex sessions; `review-metrics.json` beside the page.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Each release records its run* — ADDED: the run metrics, their sources, and a gap for what cannot be read.
  - *A station keeps a log per spawn* — ADDED: a second spawn in one stamp writes its own log.
  - *Converge keeps a status log* — MODIFIED: a `verdicts` line per role, naming its executor, model and effort.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: per-role tokens, Codex sessions, the data file.

## Impact

Changes `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-review-metrics/scripts/review_metrics.py`, `skills/mf-review-metrics/SKILL.md`, `skills/mf-rescue/SKILL.md`, `scripts/metrics/run.py` (new),
`metrics/catalogue.toml`, `docs/decisions.md` (D50), `tests/test_conduct.py`, `tests/test_metric_scripts.py` and
`tests/test_review_metrics.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A page — the UI's; the codebase's and the tests' metrics — `0078-code-metrics`; a same-freeze calibration bench; a cut's timing; a
per-role executor.
