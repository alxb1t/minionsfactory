---
bump: minor
---

# Context cost

The run logs' cost, turns and tokens per station per version join the review metrics page; a Claude worker starts with no MCP
server; converge's review and security workers load a worker reference, not the whole converge skill.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Measured over 230 run logs on 2026-11-05: $20.1 a version at list price, converge 63% of it. Every worker starts at ~26k tokens
before it reads anything, the operator's MCP servers among them — mail, drive, a billing cloud account. Review and security load
`skills/mf-converge/SKILL.md` whole, 6,631 words, 220 times over the logs, of which the worker's own sections are about a third.

## What Changes

- **The cost reader** — `review_metrics.py` reads each station's run log: cost, turns, tokens and duration, a table per repo.
- **No MCP server at a worker's start** — `--strict-mcp-config` in the Claude worker's command line.
- **The worker reference** — `skills/mf-converge/references/worker.md` holds what a review, security or fix worker needs: the
  card, the rules for tests, the review and security method, the verify pass; `skills/mf-converge/SKILL.md` keeps the conductor's.
- **The metric** — `converge-worker-reading-set`, the words a review worker reads.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The card is defined in converge alone* — MODIFIED: the card lives in converge's worker reference.
  - *The build owns the rules for tests, and the cut and converge carry them* — MODIFIED: converge carries them in its worker
    reference.
  - *Anchored harms block, and drift has its own tier* — MODIFIED: the worker reference names the anchors.
  - *Bundled generic role references resolve* — MODIFIED: converge's worker reference is a role resource; a link may name a
    section.
  - *A worker runs in an OS sandbox* — MODIFIED: a Claude worker starts no MCP server of the operator's config.
  - *Converge runs one depth* — MODIFIED: the worker reference holds the passes and the frontmatter.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: it reads the run logs' cost too.

## Impact

Changes `skills/mf-review-metrics/SKILL.md`, `skills/mf-review-metrics/scripts/review_metrics.py`, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-converge/SKILL.md`, `skills/mf-converge/references/` (`worker.md` added, `generic-review.md`, `generic-security.md`),
`skills/mf-build/SKILL.md`, `scripts/metrics/reading_set.py`, `metrics/catalogue.toml`, `docs/decisions.md` (D50, D51),
`THREAT_MODEL.md`, `tests/test_review_metrics.py`, `tests/test_conduct.py`, `tests/test_skills.py` and
`tests/test_metric_scripts.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Codex's MCP servers and token counts; effort per role; the cache TTL; build's fresh context per phase; the probe's model;
trimming `conduct.py` or the findings files' re-reads.
