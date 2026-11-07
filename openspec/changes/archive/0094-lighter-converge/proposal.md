---
bump: minor
version: v0.75
after: [0092-amend-round]
---

# Lighter converge

Converge spends where judgment is: the conductor on the mid tier, the checkers on the strongest tier with a reading set cut
to what the change cites, the fixer on the mid tier below blocking, and a security verify only where security can be reached.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Converge is most of a run's spend, and most of that buys no judgment ([measured](design.md#context)). The conductor judges
nothing, yet its model is every worker's. Each worker reads the whole decisions file and the whole living spec before it
judges. The fixer runs on the strongest model for a nit. Security re-verifies a fix that touches no surface it guards.

## What Changes

- **Worker models** — the models file gains `[converge.review]`, `[converge.security]` and `[converge.fix]`, each a `model` and
  an `effort`. `conduct.py` reads them once with the plan and passes them in the converge prompt; converge puts each on its
  worker's call. On Codex every worker stays on the conductor's model.
- **The defaults** — the cut writes the conductor on the mid tier · medium, review and security on the strongest tier · high,
  and the fixer on the mid tier · high.
- **The fixer by grade** — a fixer sent any blocking card runs on review's model; otherwise on the fixer's.
- **The bundle** — `skills/mf-converge/scripts/bundle.py` writes `.minions/changes/<change-id>/bundle.md` at each freeze: the
  repo decisions the change cites, in full, an index of every decision, and the living requirements the delta modifies or
  removes. Workers read it in place of `docs/decisions.md` and the living spec.
- **Security by recomputation** — `THREAT_MODEL.md` gains `## Surfaces`, a list of path globs, and so does the bootstrap's
  template. `skills/mf-converge/scripts/surfaces.py` reads a fix's paths and the security file's cards; a fix that reaches no
  surface, with no security card awaiting its checker, takes its security head by rule, and review alone verifies it.
- **The record** — D64; D11, D41, D48 and D49 amended; `AGENTS.md`, the principles and `README.md` say what holds; the worker
  reading set is measured with the decisions index, watched at 10,500 words.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge's workers take their models from the models file* — ADDED: the worker tables, read once, passed in the prompt;
    the fixer by grade; the cut's defaults.
  - *Converge hands each worker a bundle of what the change cites* — ADDED: `bundle.py` at each freeze, read in place of the
    decisions file and the living spec.
  - *A fix that reaches no surface takes its security head by recomputation* — ADDED: `## Surfaces`, `surfaces.py`, review
    alone verifies.
  - *Converge keeps a status log* — MODIFIED: a `verdicts` line names the model and effort its worker was given; a security
    head by rule writes a `by rule` line.
  - *The stations use AGENTS.md as target context* — MODIFIED: converge's workers read the bundle's decisions in place of the
    decisions file.
  - *Converge runs one depth* — MODIFIED: the packet holds the bundle; the converge prompt carries the worker models before
    any grant.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/generic-review.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`, `THREAT_MODEL.md`, `AGENTS.md`, `docs/decisions.md`,
`docs/principles.md`, `README.md`, `scripts/metrics/reading_set.py`, `metrics/catalogue.toml`, `tests/test_conduct.py`,
`tests/fake_worker.py`, `tests/test_metric_scripts.py` and `tests/test_skills.py`. Adds
`skills/mf-converge/scripts/bundle.py`, `skills/mf-converge/scripts/surfaces.py`, `tests/test_bundle.py` and
`tests/test_surfaces.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The amend round — `0092-amend-round`.
- A build or cut change — `0093-lighter-build-cut`; the build keeps one model a change.
- A security skip in a catch-up run, its fix round included ([C9](design.md#goals--non-goals)).
- The conductor's own reading set: `converge-reading-set` stays past its watch until a change trims the skill.
