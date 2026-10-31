---
version: v0.39
---

# Review metrics

An operator skill, `mf-review-metrics`, reads the `.minions/findings/` of the repos the operator names and writes one
HTML page of charts and tables, per tier and model, so review tiers are chosen on data.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirement.

## Why

Every converge leaves its findings files and status log on disk, and since v0.37 they record the tier, the model, the
workers, the verdict states and the tokens. Nothing reads them across changes or repos: whether `standard` is good
enough, and what `high` costs, is guessed. The data is there; a reader and a page are not.

## What Changes

- **`skills/mf-review-metrics/`** — a skill and a stdlib `uv` script: the repos from
  `~/.config/minionsfactory/review-metrics.toml`, read leniently across every era of the files, one page written to
  the path the config names.
- **The page** — a table per repo and per tier × model, and charts over changes through `mf-build`'s `chart()`; a
  missing field is a gap, listed per repo, never a zero.
- **The principle** *The repo reaches nothing outside itself* gains the station's exception; **D50** records it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The review-metrics station charts past findings, read-only* — ADDED.

## Impact

Adds `skills/mf-review-metrics/SKILL.md`, `skills/mf-review-metrics/scripts/review_metrics.py` and
`tests/test_review_metrics.py`; changes `docs/principles.md`, `docs/decisions.md` and `README.md`. After release the
person runs `make install-skills` once: a new skill directory is not linked until then.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Advice or a recommended tier — numbers only (D43); a station of the line — `mf-ship` never calls it; `AGENTS.md`'s
skill list, which simplify edits in the same run; any write into a repo.
