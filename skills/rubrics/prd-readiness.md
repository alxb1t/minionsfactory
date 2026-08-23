# Rubric — PRD readiness

The definition of "done" for a **PRD** (`prd/vX.Y_<name>.md`): is it well-defined enough to hand downstream
(blueprint → forge → execution)? **`mf-order`** drives the interview toward every criterion; **`mf-gauge`** gates
the finished PRD as a fresh, blind instance. See [README](README.md) for the (M)/(J) split + verdict conventions.

A PRD is **ready** when every (M) criterion passes and no (J) criterion has an open `blocking` finding.

## Criteria

1. **(J) One small feature — blocking.** The PRD delivers a single, cohesive, self-contained feature, not a
   bundle. A multi-feature ask is **split** into separate versioned PRDs (the excess parked in the backlog's
   future section), never grown into this one. *The scope guard — the interview's main job.*
2. **(J) Real problem stated — blocking.** The Problem section says who it's for, why now, and what breaks without
   it — a concrete motivation, not a vague "would be nice."
3. **(J) Observable outcome — blocking.** The Outcome is an end state you can **see or verify**, not a subjective
   aspiration ("cleaner", "better UX") with no observable signal.
4. **(M+J) Every requirement has testable acceptance — blocking.** Each requirement carries acceptance a test
   could express (a WHEN/THEN, an observable behavior). (M): every requirement has a non-empty acceptance clause.
   (J): the acceptance is genuinely falsifiable, not a restatement of the requirement. *The core criterion — this
   is what lets the downstream machine gate express "done".*
5. **(M+J) No unresolved research / no TBD — blocking.** The PRD holds **decisions, not investigations**. (M): no
   `TBD` / `???` / "decide later" / "figure out" / "investigate" / "research needed" markers in requirements or
   constraints. (J): no requirement quietly defers a design/technical question into execution — research is done
   on the planning side and its conclusion stated. *Research belongs before the PRD, not inside it.*
6. **(J) Right-sized — blocking.** The feature plausibly decomposes into ≤ ~10 self-contained, independently
   committable phases — small enough to fit one execution context. If it can't, it's too big → rescope or split.
7. **(M+J) Non-goals present + meaningful.** (M): a Non-goals section exists. (J): it draws a real boundary (names
   what is deliberately excluded / deferred), not filler.
8. **(J) Constraints stated.** Constraints are explicit where they apply: new dependencies (approval-gated
   downstream), security posture, "no new runtime dependency", compatibility limits.
9. **(J) Prerequisites & ordering identified.** What must exist first is named; the version is consistent with the
   roadmap's sequence (no depending on an unbuilt later version).
10. **(M) Version declared.** The PRD frontmatter/header declares its `vX.Y`, matching the intended roadmap slot +
    the eventual change id.

## Findings

`mf-gauge` writes a findings file (`verdict: clean | changes-requested`), one finding per failed criterion, each
citing the PRD section/requirement it fails and a one-line fix pointer. No open blocking finding and all (M)
passing ⇒ `clean`.
