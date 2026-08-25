# MinionsFactory — Planning rubrics

The **definition of "done"** for each planning artifact — the planning-side analog of the execution machine gate.
Each rubric is a shared contract: a **producer** skill drives an artifact toward it; an **independent checker**
skill (a fresh subagent, blind to the producer) gates the artifact against it. Same discipline as the execution
loop's coder + fresh reviewer.

## The (M) / (J) split — the enforcement design

Every criterion is tagged:

- **(M) machine-checkable** — mechanical, un-gameable: a grep, a section-present check, a count, an id match. A
  checker asserts these directly; they cannot be argued away.
- **(J) judgment** — needs an independent agent's reading (is the acceptance really testable? is the design really
  sound?). These are exactly what a fresh, blind checker is for.

A criterion tagged **(M+J)** has a mechanical floor *and* a judgment layer (e.g. "no `TBD` marker" is (M); "no
requirement secretly defers a decision" is (J)).

## Verdict + severity conventions

- **prd-readiness** and **conformance** checkers emit `verdict: clean | changes-requested`. A finding is
  `blocking` (must fix — the artifact is not ready) or `nit` (advisory → note, never blocks). Any failed (M)
  criterion or any open `blocking` (J) finding → `changes-requested`. The loop is `produce → check → fix →
  re-check` until `clean`.
- **feasibility** emits a 4-way verdict — `feasible` · `feasible-with-caveats` · `needs-precursor` ·
  `infeasible-as-specified` (see [feasibility](feasibility.md)) — because "can we build this here" is not
  pass/fail.
- **compliance** emits `verdict: compliant | gaps-found` over **three** severities — `blocking` (the orchestrator
  cannot run here at all) · `required` (below standard; the loop runs) · `advisory` (a nit) — rather than the
  `blocking | nit` pair the other three share. `compliant` iff zero `blocking` **and** zero `required` gaps are
  open; open advisories are listed and counted but never withhold the verdict (see
  [compliance](compliance.md)). Its subject is a **repo** rather than a planning artifact, and its gaps carry the
  same `open → fixed → verified` status machine across rounds.

Checkers write a findings file with machine-readable frontmatter (the same `open → fixed → verified` status
machine the execution reviewer uses); every finding cites the exact PRD requirement / change artifact it fails —
**no citation, no finding.** Never invent findings to look thorough; a genuinely ready artifact passes.

## Which skill uses which rubric

| Rubric | Producer (drives toward it) | Checker (gates it, fresh + blind) |
|---|---|---|
| [prd-readiness](prd-readiness.md) | `mf-order` | `mf-gauge` |
| [feasibility](feasibility.md) | `mf-blueprint` | `mf-inspect` (re-checks) |
| [conformance](conformance.md) | `mf-forge` | `mf-inspect` |
| [compliance](compliance.md) | `mf-retrofit` (v0.7) · `mf-stamp` (v0.8) — forthcoming | `mf-teardown` |
