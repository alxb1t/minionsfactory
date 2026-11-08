---
bump: minor
version: 0.82
debt: [0097·R2, 0097·R3, 0097·R4]
---

# Worker diet

Every worker the run spawns starts with less: its station's tools alone, no operator plugins, output style or auto-memory,
a cache lifetime fit to its waits, and reach only into live worktrees. Build and cut read the decisions they cite and an
index; the converge conductor reads no mandatory context and runs on Sonnet; tool output shrinks; and the review metrics
show where the tokens go.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

A version costs $43.7 on average (0096, 0097), and most of it is context re-read every turn: a worker's first turn is
~28.6k tokens before any work, build carries all 55 decisions for 206 turns, a green gate prints ~4.5k chars, and the
converge conductor runs Opus to orchestrate ([measured](design.md#context)). The metrics cannot show cost per worker, nor
the cut's and the supervisor's spend. This version trims what every worker carries; the cut, converge and build-per-phase
diets follow it.

## What Changes

- **The spawn** — each Claude worker gets `--tools` from a station table, `--settings` turning off plugins, the output
  style and auto-memory, and `--exclude-dynamic-system-prompt-sections`; the cut and the converge conductor ask for the
  1-hour cache, every other station the 5-minute one; `--add-dir` names only the worktrees of open versions and queued
  cuts. A worker that calls a tool its station lacks halts its version, naming the tool. The probe reports its first
  turn's context.
- **The context** — build and cut read the decisions they cite, in full, and an index, which `bundle.py --decisions`
  prints; the principles and the threat model only when a task names them. The converge conductor reads no mandatory
  context, runs on Sonnet 5.5 · high when the models file names none, and runs its fixer and verify workers at `medium`.
  One `stamp.py` call writes several events.
- **Tool output** — pytest prints short tracebacks; `gate_run.py` runs the gate without `VIRTUAL_ENV`, and a green gate
  prints its summary line alone.
- **The metrics** — `review-metrics.json` carries each converge worker's role, round, run and first-turn context, a
  mailbox checker's tokens and dollars — a subagent's a gap, as no event holds its totals — each round and role's dollars
  from its own run's workers, each station's cost with the cut and the supervisor among them; the page reads every repo
  a run started in; the role table gets back its median duration and tokens (`0097·R4`).
- **The record** — D70; D48, D50 and D64 amended (`0097·R2`); the threat model and the principles; the README line
  (`0097·R3`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The skills run the repository's `make gate`* — MODIFIED: the gate runs without `VIRTUAL_ENV`; a green gate prints its
    summary line alone.
  - *Converge keeps a status log* — MODIFIED: one `stamp.py` call may write several events.
  - *The stations use AGENTS.md as target context* — MODIFIED: build and cut read the decisions they cite and an index;
    the principles and the threat model when a task names them; the converge conductor reads no mandatory context.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: the cut and supervise stations, workers,
    dollars per run, round and role where its workers hold them, first-turn context, the run's repo list, the role
    table's medians.
  - *A worker's reach stops at the repository* — MODIFIED: an open worktree is an open version's or a queued cut's.
  - *Converge's workers take their models from the models file* — MODIFIED: the conductor's default is Sonnet 5.5 ·
    high; the fixer and verify workers run at `medium`.
  - *A Claude worker starts with its station's tools and nothing of the operator's* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/stamp.py`, `skills/mf-converge/scripts/gate_run.py`,
`skills/mf-converge/scripts/bundle.py`, `skills/mf-review-metrics/scripts/review_metrics.py`,
`skills/mf-review-metrics/prices.toml`, `scripts/metrics/reading_set.py`, `pyproject.toml`, `AGENTS.md`,
`skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/SKILL.md`,
`skills/mf-review-metrics/SKILL.md`, `skills/mf-bootstrap/templates/AGENTS.md.tmpl`,
`skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl`, `docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`,
`README.md`, `tests/fake_worker.py`, `tests/test_conduct.py`, `tests/test_stamp.py`, `tests/test_gate_run.py`,
`tests/test_bundle.py`, `tests/test_review_metrics.py` and `tests/test_metric_scripts.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The plan reviews' packet and budget, the cut's helpers on Sonnet, a pickup-only verify, the bundle as diffs and release
  reading frontmatter alone: the cut and converge diet, after this version.
- One build worker per phase: the build-per-phase version.
- Dropping the skills listing, a scripted spec fold, splitting `conduct.py`, the Codex usage-limit fallback, local models.
- Judging the savings: the ledger over the three versions after each ships, against $43.7 a version.
