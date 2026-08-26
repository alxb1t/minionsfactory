# Rubric — PRD readiness

The definition of "done" for a **PRD** (`planning/vX.Y/vX.Y_<name>.md`): is it well-defined enough to hand downstream
(blueprint → forge → execution)? **`mf-order`** drives the interview toward every criterion; **`mf-gauge`** gates
the finished PRD as a fresh, blind instance. See [README](README.md) for the (M)/(J) split + verdict conventions.

A PRD is **ready** when every (M) criterion passes and no (J) criterion has an open `blocking` finding.

## Criteria

1. **(J) One small feature — blocking.** The PRD delivers a single, cohesive, self-contained feature, not a
   bundle. A multi-feature ask is **split** into separate versioned PRDs (the excess parked in the backlog's
   future section), never grown into this one. *The scope guard — the interview's main job.*
   **Exception — a declared migration** (see below). A migration may carry several steps in one PRD, but only if
   it declares itself one and earns it.
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
   **A declared migration may exceed the bound at the version level, but not at the stage level:** it decomposes
   into named **stages**, and each stage is itself ≤ ~10 phases and ends on a green gate. The bound moves; it does
   not disappear.
7. **(M+J) Non-goals present + meaningful.** (M): a Non-goals section exists. (J): it draws a real boundary (names
   what is deliberately excluded / deferred), not filler.
8. **(J) Constraints stated.** Constraints are explicit where they apply: new dependencies (approval-gated
   downstream), security posture, "no new runtime dependency", compatibility limits.
9. **(J) Prerequisites & ordering identified.** What must exist first is named; the version is consistent with the
   roadmap's sequence (no depending on an unbuilt later version).
10. **(M) Version declared.** The PRD frontmatter/header declares its `vX.Y`, matching the intended roadmap slot +
    the eventual change id.

## The migration exception (criteria 1 and 6)

Some work is **one migration in several steps**: each step is coherent, but shipping any alone leaves a state
nobody should run. The steps are coupled by **breakage**, not by theme. Splitting them means releasing a known
break; merging them silently means a bundle passing as a feature. This class lets the shape be stated instead.

**Claiming it is cheap and explicit** — `class: migration` in the frontmatter plus a **Stages** section. A checker
never infers it, and it is never the default. Three things are required, and only the second is a real gate:

1. **One sentence on why splitting would ship a break.** Not an essay. *"They are related"* or *"it is one
   refactor"* does not qualify; if a step could ship alone and leave a working system, it is a separate version.
2. **Stages, each ≤ ~10 phases, each ending on a green gate.** This is the part that matters — it keeps execution
   tractable, which is what the bound was ever for. The bound moves from the version to the stage; it does not
   disappear.
3. **One version, one tag.** If the steps want separate tags they are separate versions and this does not apply.

**What does not relax, ever.** Criteria **4** (testable, falsifiable acceptance), **5** (no decision deferred to
execution) and **9** (prerequisites and ordering) apply unchanged, and a migration makes them *more* load-bearing,
not less — a longer PRD has more places for two clauses to contradict each other, and that is the defect class
this rubric actually catches. Size was never the guard that found bugs. **Relax scope; never relax acceptance.**

## Findings

`mf-gauge` writes a findings file (`verdict: clean | changes-requested`), one finding per failed criterion, each
citing the PRD section/requirement it fails and a one-line fix pointer. No open blocking finding and all (M)
passing ⇒ `clean`.
