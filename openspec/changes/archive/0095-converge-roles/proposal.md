---
bump: minor
version: 0.78
after: [0094-lighter-converge]
---

# Converge roles

Converge's two checkers become specialists: **conformance** holds the code to the change's own plan, **adversarial** tries to
break it. Each reads only what its job needs, the diff once; a script picks the debt cards, and a verify reads only its open
cards.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Review and security overlap, and each reads far more than it judges with ([measured](design.md#context)). Of 0072–0089's
blockers, spec conformance as text caught 29% and adversarial correctness 60%; security and review found 11 issues twice. A
round-1 review spent 11.4% of its reads on `.minions/debt.md`, which no blocker cited, and read the diff a second time through
`git diff`. A verify round spent 40–50% re-reading its own file and the method. "Security" read as security only.

## What Changes

- **The roles** — `review`/`review.md` becomes **conformance**/`conformance.md`, grading `blocking` · `drift` · `nit`;
  `security`/`security.md` becomes **adversarial**/`adversarial.md`, grading `critical` · `high` · `medium` · `low`. The
  references become `generic-conformance.md` and `generic-adversarial.md`, each with its own packet. `conduct.py`'s blocking
  rule, paths and worker tables, the release's preconditions, the run metrics and the review metrics take the new names.
- **The move** — a run moves a change folder's `review.md` and `security.md` to the new names at its start; a hand-run station
  on the old names halts naming `/mf-ship`; `review_metrics.py` reads both.
- **The packets** — conformance reads the change's artifacts, its bundle and the diff, and no code beyond the diff's hunks;
  adversarial reads the diff, the source and tests around it, and `THREAT_MODEL.md`. Each reads `diff.patch` once.
- **The debt** — `skills/mf-converge/scripts/debt_match.py` puts into the bundle the debt cards whose files the diff touches;
  no worker reads `.minions/debt.md`.
- **Verify** — `skills/mf-converge/scripts/open_cards.py` extracts a findings file's open cards; a verify worker gets them, the
  fix diff and a short `references/verify.md`.
- **The defaults** — conformance on the mid tier · high, adversarial on the strongest tier · high.
- **The record** — D66; every live mention of the old names renamed, D12 rewritten, D48 amended; the reading set measured
  per role.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge's checkers are conformance and adversarial* — ADDED: the two roles, their files, grades, packets and card ids.
  - *A run moves the old findings files to the checkers' names* — ADDED: the move at a run's start; the old names halt a
    hand-run station.
  - *Converge bundles the debt cards on the diff's files* — ADDED: `debt_match.py`; no worker reads the debt file.
  - *A verify worker reads its open cards and the fix diff* — ADDED: `open_cards.py`, `references/verify.md`.
  - *Conformance searches for stale claims* — ADDED, renaming *Review searches for stale claims*, REMOVED.
  - *Conformance judges test cost and traced coverage* — ADDED, renaming *Review judges test cost and traced coverage*,
    REMOVED.
  - *A fix that reaches no surface takes its adversarial head by recomputation* — ADDED, renaming 0094's *… takes its security
    head by recomputation*, REMOVED.
  - *Anchored harms block, and drift has its own tier* — MODIFIED: conformance and adversarial grade.
  - *A repeated finding escalates* — MODIFIED: against the bundled debt cards.
  - *Converge keeps a status log* — MODIFIED: the roles named.
  - *The stations use AGENTS.md as target context* — MODIFIED: the bundle to conformance, the threat model to adversarial.
  - *Generic passes preserve the station boundaries* — MODIFIED: each role's sections.
  - *Independent workers have fresh contexts* — MODIFIED: the roles named.
  - *Bundled generic role references resolve* — MODIFIED: the conformance, adversarial, verify and worker references.
  - *Every worktree shares the primary's run directory* — MODIFIED: the change folder's files named.
  - *Every station runs MF's own method* — MODIFIED: the roles named.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: both names read.
  - *Converge runs one depth* — MODIFIED: the roles named.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: the roles named.
  - *A halted version is rescued in its run* — MODIFIED: a conformance card in the scenario.
  - *A run grants one round at a small cap, and halts a large one for a re-plan* — MODIFIED: the roles' blocking grades.
  - *Each release records its run* — MODIFIED: per role, by the new names.
  - *A supervisor answers what the rescue leaves* — MODIFIED: a security card read from `adversarial.md`.
  - *Converge's workers take their models from the models file* — MODIFIED: the worker tables renamed; the blocking fixer on
    adversarial's model; the new defaults.
  - *Converge hands each worker a bundle of what the change cites* — MODIFIED: the bundle is conformance's, and adversarial's
    for its debt cards.
  - *An answered converge halt gets one amend round* — MODIFIED, 0092's: conformance keeps the full plan.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`,
`skills/mf-converge/scripts/surfaces.py`, `skills/mf-converge/scripts/gate_check.py`,
`skills/mf-integrate/scripts/integrate.py`, `skills/mf-review-metrics/scripts/review_metrics.py`, `scripts/metrics/run.py`,
`scripts/metrics/reading_set.py`, `metrics/catalogue.toml`, the `SKILL.md` of `mf-build`, `mf-cut-change`, `mf-integrate`,
`mf-release`, `mf-rescue` and `mf-supervise`, `docs/decisions.md`, `docs/principles.md`, `docs/README.md`, `README.md`,
`AGENTS.md`, `THREAT_MODEL.md`, `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`, `tests/fake_worker.py`, `tests/test_conduct.py`, `tests/test_gate_check.py`,
`tests/test_integrate.py`, `tests/test_metric_scripts.py`, `tests/test_review_metrics.py`, `tests/test_skills.py` and
`tests/test_surfaces.py`. Renames `generic-review.md` and `generic-security.md`. Adds `skills/mf-converge/references/verify.md`,
`skills/mf-converge/scripts/debt_match.py`, `skills/mf-converge/scripts/open_cards.py`, `tests/test_debt_match.py` and
`tests/test_open_cards.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- More than two checkers: the measurement says two roles earn their cost.
- A checker judging the deterministic checks: the gate, `gate_check.py`, the `Verify:` lines and coverage stay scripts.
- New card ids: conformance keeps `R`, adversarial keeps `S` ([C3](design.md#goals--non-goals)).
- Renaming `mf-review-metrics` or `review-metrics.json`: "review" there is the activity.
