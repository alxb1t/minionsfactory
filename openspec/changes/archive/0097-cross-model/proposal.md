---
bump: minor
version: 0.80
after: [0096-codex-ready]
---

# Cross-model converge

Converge's checkers run on the host the models file names — Codex while the conductor and fixer stay on Claude — through a
mailbox `conduct.py` serves; a shadow round 1 runs the other host's checkers on the same freeze; the review metrics show, per
role and executor, whether the cross-model review earns its cost.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The person wants Codex to review and Claude to fix, and the numbers before trusting it. Today a checker always runs on
converge's host: a worker table naming an `executor` halts, a sandboxed Claude conductor cannot start `codex exec`, and the
review metrics hold one model per change ([measured](design.md#context)). `0096-codex-ready` makes a Codex worker reliable;
this version puts it in the check loop.

## What Changes

- **The models line** — a part may name its host, `codex/gpt-6.1-sol`, and the line may add `conformance`, `adversarial`
  and `fix` parts and a last `shadow`. `brief_check.py` holds the grammar; the cut writes the worker tables with `executor`
  and `[converge] shadow = true`.
- **Checker tables name an executor** — a conformance or adversarial table may name one; the fixer's still halts. The run
  probes each checker's executor at its start.
- **The checker mailbox** — a converge conductor sends a checker on another host to `conduct.py checker`; `conduct.py`,
  unsandboxed, spawns it with its table's model and effort, and answers. The conductor reads the findings from disk. The
  findings frontmatter gains `executor:`.
- **Shadow round 1** — under `[converge] shadow = true`, round 1 also runs the other host's two checkers on the same freeze,
  into `shadow-conformance.md` and `shadow-adversarial.md`, which drive no fix. `overlap.py` counts shared and unique catches.
- **The metrics** — the review metrics read per role and executor, a checker's own log as its cost, escapes traced to the
  round 1 that missed them and the shadow overlap, and show four headline numbers on the page and in `review-metrics.json`.
  The run metrics count a checker's log in converge's cost and its role's tokens.
- **The record** — D68; D11, D40, D41, D47, D49, D50 and D64 amended; `THREAT_MODEL.md` names the mailbox.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A hard brief is checked before it is queued* — MODIFIED: a models part may carry a host, and the line may add checker
    and fixer parts and `shadow`.
  - *Converge's workers take their models from the models file* — MODIFIED: a checker table may name an executor; a checker
    on another host than converge's is named `<role>=mailbox`.
  - *A station's executor comes from the models file* — MODIFIED: each checker's executor and a shadow's are probed.
  - *Converge keeps a status log* — MODIFIED: the `shadow` event; a `verdicts` line names its checker's executor.
  - *The review-metrics station charts past findings, read-only* — MODIFIED: per role and executor, checker logs, escapes,
    the shadow overlap and the headline numbers.
  - *Each release records its run* — MODIFIED: a checker's log counts in converge's cost and its role's tokens.
  - *A converge checker on another host runs through the mailbox* — ADDED.
  - *A shadow round 1 runs the other host's checkers* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-plan/scripts/brief_check.py`,
`skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/SKILL.md`,
`skills/mf-converge/references/worker.md`, `skills/mf-converge/references/verify.md`,
`skills/mf-review-metrics/scripts/review_metrics.py`, `skills/mf-review-metrics/SKILL.md`, `scripts/metrics/run.py`,
`docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`, `tests/fake_codex.py`, `tests/fake_worker.py`, `tests/test_conduct.py`, `tests/test_brief_check.py`,
`tests/test_review_metrics.py`, `tests/test_metric_scripts.py` and `tests/test_skills.py`. Adds
`skills/mf-converge/scripts/overlap.py`, `tests/fake_claude.py` and `tests/test_overlap.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The calibration bench: a one-off run of the 0042 fixture per model, by hand, once Codex runs reliably.
- Codex as builder or releaser, and a fixer on another host than converge's ([C3](design.md#goals--non-goals)).
- Counting the next five versions' shadow rounds: the person sets `shadow` at each plan's close
  ([C4](design.md#goals--non-goals)).
- A recommendation on the page: it gives numbers ([D50](../../../docs/decisions.md#d50--review-metrics-are-read-across-repos-and-drawn-on-one-page)).
