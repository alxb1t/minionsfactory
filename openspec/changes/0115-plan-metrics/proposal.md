---
bump: minor
---

# Plan metrics

`mf-review-metrics` books the person's planning and hand work from their session transcripts, as a `plan` and an `operator` station per change, beside the stations the run spawns.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the requirement.

## Why

The metrics book only what a run spawns: build, converge, cut and the rest, from their logs. The person's own planning and hand work in an interactive session is a real cost of each version, as the plan and as operator work, and none of it is on the page. A version's cost is understated by what no log holds.

## What Changes

- **The sessions key** — `review-metrics.toml` may hold `sessions = [...]`, the transcript folders to read; none listed, none read ([D1](design.md#d1)).
- **The reader** — a transcript is reduced to numbers, ids and times; only a session holding an `mf-*` marker is read, and a session a station log's `init` names is skipped ([D2](design.md#d2), [D3](design.md#d3), [D4](design.md#d4)).
- **The plan** — a span opens at an `mf-plan` call carrying `brief=` and closes at the last write of the brief; it is bound to the ids a matched `conduct.py cut` queued, split equally, joined across `from=`, and `unbooked` when never queued ([D5](design.md#d5), [D6](design.md#d6)).
- **The operator** — every other message of a listed session, booked to the open version the nearest earlier mark names, else `unbooked`; a subagent at its launching call's time ([D7](design.md#d7)).
- **The output** — `plan` and `operator` rows in `review-metrics.json`'s `stations` and as columns of the page's cost table ([D8](design.md#d8)).
- **The record** — D50's text, the skill's text, the requirement ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The review-metrics station books the person's planning and operator work from session transcripts* — ADDED: the `sessions` key, the reader's read list, the plan span and its binding, the operator booking, the skipped station sessions, the `plan` and `operator` rows.

## Impact

Changes `skills/mf-review-metrics/scripts/review_metrics.py`, `skills/mf-review-metrics/SKILL.md`, `docs/decisions.md`, `docs/principles.md` and `tests/test_review_metrics.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Codex sessions of the person: no plan runs there today. Build it when a plan runs on Codex.
- A target project's own sessions as a separate source: read when a `sessions` entry names their folder, booked the same way.
- The person's ledger of cost per version: it lives outside this repository ([D10](design.md#d10)).
