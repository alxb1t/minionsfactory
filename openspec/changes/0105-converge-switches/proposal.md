---
bump: minor
debt: [0100·S5]
---

# Converge switches

A person can skip converge's conformance role, its adversarial role, or converge whole, per version, on the models line. A
repo's `AGENTS.md` default pre-fills that line.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

A proof of concept does not earn converge's tokens, and the person has no way to say so: `conduct.py` sends a built version
back to converge until both findings files are clean at `HEAD` ([evidence](design.md#context)). The hand skip lives in
`mf-release` alone, and `mf-cut-change` offers a `skip` the run never reads.

## What Changes

- **The word `skip`** — the models line takes `converge skip`, `conformance skip` and `adversarial skip`; `models.toml` takes
  `skip = true` under `[converge]` or `[converge.<role>]`. `brief_check.py` refuses a skip beside that role's models or
  `shadow`, and both roles skipped.
- **`converge skip`** — a built version goes straight to integrate and release; the run log says `converge skipped — plan`
  and the release `converge: skipped — by plan`.
- **A skipped role** — converge dispatches the other role alone; a script writes the skipped role's findings file as a stub at
  `HEAD`, each round and catch-up, so the run's readers stay unchanged; the release names `<role>: skipped`. A skipped
  Codex role is not probed and takes no prompt clause.
- **A repo default** — an `AGENTS.md` line `**Converge:** skip` (or `conformance skip`, `adversarial skip`) pre-fills each
  version's models line in `mf-plan` and the cut; `conduct.py` reads `models.toml` alone.
- **A surfaces warning** — the cut warns when a version with adversarial skipped touches `THREAT_MODEL.md`'s `## Surfaces`.
- **Debt `0100·S5`** — converge names each Agent call's description `<role> round <N>`; `review_metrics.py` anchors `WORKER`
  at the description's start.
- **The record** — a new decision; D14 edited; a requirement of the spec amended; the threat model names a planted skip.
- The dead `skip, read by hand` text leaves `mf-cut-change`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station takes cut versions to the default branch* — MODIFIED: converge runs unless the version's plan skips it.
  - *A release may skip the check loop, and says so* — MODIFIED: `converge: skipped — by plan`, and `<role>: skipped` for a stub.
  - *Converge's workers take their models from the models file* — MODIFIED: `skip` under `[converge]` and a checker table; the
    prompt clause `<role>=skip`; a skipped role is not probed.
  - *A hard brief is checked before it is queued* — MODIFIED: the `skip` forms and their refusals.
  - *Converge's checkers are conformance and adversarial* — MODIFIED: a plan may skip either.
  - *A converge conductor stubs a skipped checker* — ADDED: `skip_stub.py`, the stub file, when it is written.
  - *The plan and the cut take a repo's converge default* — ADDED: `**Converge:**` pre-fills the line; the surfaces warning.
  - *A converge worker's description names its role and round* — ADDED: the description forms and the anchored `WORKER`.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-plan/scripts/brief_check.py`, `skills/mf-plan/SKILL.md`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`,
`skills/mf-release/SKILL.md`, `skills/mf-ship/SKILL.md`, `skills/mf-review-metrics/scripts/review_metrics.py`, `docs/decisions.md`, `THREAT_MODEL.md`,
`tests/test_conduct.py`, `tests/fake_worker.py`, `tests/test_brief_check.py` and `tests/test_review_metrics.py`. Adds
`skills/mf-converge/scripts/skip_stub.py` and `tests/test_skip_stub.py`. No dependency; the gate recipe is unchanged.

## Not in this change

- Moving the switches out of `models.toml`: when a paydown of `0085·S2` lands.
- A hand read or a debt card for a skipped converge.
- An automatic floor under an adversarial skip.
- A skip of the fixer, or of the plan review.
