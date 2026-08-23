# Rubric — PRD ↔ change conformance

The definition of "done" for the **openspec change** (`openspec/changes/<id>/`): does it faithfully render the PRD
**and** is it execution-ready? **`mf-inspect`** checks it as a fresh, blind instance, given only the PRD + the
change. See [README](README.md) for the (M)/(J) split + verdict conventions.

The change is **conformant** when every (M) criterion passes and no (J) criterion has an open `blocking` finding.

## Criteria

1. **(J) Completeness — blocking.** Every PRD requirement maps to one or more tasks/scenarios in the change.
   Nothing the PRD asks for is dropped.
2. **(J) No scope creep — blocking.** Nothing in the change is untraceable to a PRD requirement. The renderer
   added no feature, task, or scenario the PRD never authorized.
3. **(M+J) Bidirectional trace — blocking.** Every spec-delta `#### Scenario:` traces to a PRD requirement's
   acceptance, and vice-versa. (M): each scenario carries a stable `Key:` and (once bound) a resolving marker;
   (J): the scenario genuinely expresses that requirement's acceptance, not an adjacent claim.
4. **(J) design.md is real — blocking.** `design.md` makes actual technical decisions (the *how*), leaves **no
   open design question**, is not a restatement of the *what*, and is **consistent with the blueprint**
   (`prd/vX.Y_design.md`).
5. **(J) Phases execution-ready — blocking.** Each phase in `tasks.md` is machine-checkable, self-contained, and
   right-sized, and every phase is **code+commit** — **no research/design-lock phase** (all research/design was
   resolved on the planning side). A non-code phase is a blocking finding.
6. **(M) Contract complete.** All four artifacts are present — `proposal.md` · `design.md` · `tasks.md` · `specs/`
   delta — and the change id/version matches the PRD's `vX.Y`. (Overlaps the repo's execution-side contract guard
   by design — belt and suspenders.)
7. **(J) Design soundness / feasibility re-check.** An independent sanity-check that the design still holds against
   the real codebase (per the [feasibility](feasibility.md) rubric) — a proposition that looked sound but doesn't
   survive contact with the code is blocking.

## Findings

`mf-inspect` writes a findings file (`verdict: clean | changes-requested`, `open → fixed → verified` status
machine), one finding per failed criterion citing the exact PRD requirement + change artifact/line it fails. The
loop is `inspect → fix the change → re-inspect (fresh, scoped to the fix)` until `clean`.

**Doc-only changes.** A change with an N-A spec delta (e.g. v0.4 itself) satisfies criterion 6 with the delta
explicitly marked N-A, and criteria 3 / 7 scoped accordingly (no scenarios to trace; feasibility is trivial for a
prose deliverable).
