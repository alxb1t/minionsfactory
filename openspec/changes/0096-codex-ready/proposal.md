---
bump: minor
debt: [0050·S7]
---

# Codex ready

A Codex worker under `mf-ship` starts on MF's settings alone, logs JSON events the run reads as it reads Claude's, halts on
a writable root swapped for a link, and is proved at a run's start by one real checker on a fixture.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

No `mf-ship` station has ever run on Codex ([measured](design.md#context)). A Codex worker loads the operator's
`~/.codex/config.toml` — its model, MCP servers whose binary may be missing, plugins — and logs plain text, so its denials,
usage limit, cost and tokens read as nothing. Debt card `0050·S7`'s trigger, "before the first unattended Codex run of two
versions", is the next version's first run.

## What Changes

- **Config isolation** — a Codex worker starts with `--ignore-user-config`: no operator MCP server, plugin, profile or
  notify; its model and effort come from the models file, else Codex's own defaults. D51's accepted MCP gap closes.
- **JSON events** — a Codex worker starts with `--json`. `conduct.py` reads a denial, a usage limit and an MCP tool call from
  its events; each Codex worker log opens with a spawn line naming its model. The run metrics and the review metrics read a
  Codex log's tokens, and price them by a new `skills/mf-review-metrics/prices.toml`.
- **The swap window** — before each Codex spawn, every writable root and the working directory must be a folder that resolves
  to itself, else the version halts; `/tmp` leaves a Codex worker's roots. Pays `0050·S7`.
- **The probe** — a run's Codex probe, after its scratch edit, runs one conformance checker on a fixture and passes only on a
  findings file to the contract and a log with a usage event. The gate tests the argv, the readers and the probe with a fake
  `codex` on `PATH`.
- **The record** — D67; D47 and D51 amended; `THREAT_MODEL.md` names the host crossing and the closed swap window.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station judges every station from disk* — MODIFIED: the Codex probe also runs a checker on a fixture.
  - *A station's executor comes from the models file* — MODIFIED: a Codex station's denials, usage limit, tokens and priced
    cost read from its JSON log; converge's per-role tokens stay unavailable on Codex.
  - *A worker's reach stops at the repository* — MODIFIED: a writable root swapped for a link halts the next Codex spawn.
  - *A worker runs in an OS sandbox* — MODIFIED: a Codex worker loads no user config, logs JSON, and has no `/tmp` root; the
    probe fails on a Codex MCP tool call.
  - *Each release records its run* — MODIFIED: a Codex log's tokens, priced by the price table, a model with no price a gap.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: the same for a Codex station's cost cell.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `scripts/metrics/run.py`,
`skills/mf-review-metrics/scripts/review_metrics.py`, `docs/decisions.md`, `THREAT_MODEL.md`, `tests/fake_worker.py`,
`tests/test_conduct.py`, `tests/test_metric_scripts.py` and `tests/test_review_metrics.py`. Adds
`skills/mf-review-metrics/prices.toml` and `tests/fake_codex.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The models line's hosts per role, the checker mailbox, the shadow round and the cross-model metrics: the version after
  this one, `cross-model`.
- The calibration bench: a one-off run of the 0042 fixture per model, by hand, once Codex runs reliably.
- Codex as builder or releaser.
- List prices: `prices.toml` lands with no rows; a person adds one when a model is used ([C1](design.md#goals--non-goals)).
- Judging the probe checker's verdict: the probe proves the runtime, never a model's judgment ([D9](design.md#d9)).
