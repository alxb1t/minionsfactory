# Rubric — Feasibility & design

The definition of "done" for the **feasibility spike + design proposition** (`planning/vX.Y/vX.Y_design.md`): can
this PRD actually be built in *this* codebase, and how? **`mf-blueprint`** produces the design proposition +
verdict by reading the PRD against the real code; **`mf-inspect`** independently re-checks the design's soundness
later. See [README](README.md) for the (M)/(J) split.

Unlike the other rubrics, feasibility is **not pass/fail** — it emits a 4-way verdict (below), because "can we
build this here" is a judgment with degrees.

## Criteria (the design proposition must satisfy these)

1. **(J) Concrete approach.** The proposition names the **actual modules/files touched** and any new components —
   not a hand-wavy sketch. A reader can see where the code will land.
2. **(J) Architecture impact bounded.** It states whether the feature fits the current architecture as-is, or
   requires a refactor — and if so, **names the refactor** and whether it should be a **precursor version** first.
3. **(M+J) Effort proportionate.** (M): a rough **phase count** is stated. (J): the effort is proportionate to the
   feature's value and within the ≤ ~10-phase one-context bound; if it blows the bound, the proposition says
   **split or rescope**.
4. **(J) Blockers & prerequisites surfaced.** New dependencies (flagged as approval-gated), missing infra,
   external systems, and genuine unknowns needing a spike are all named — not discovered mid-build.
5. **(J) Alternatives considered.** At least one simpler approach is weighed, with why it was / wasn't chosen — the
   anti-over-engineering check (the planning-side echo of the `simplify` lens).
6. **(J) Risks named.** What could make the build fail or balloon (a shaky assumption, a fragile seam, an
   uncertain external contract) is called out.
7. **(M) Verdict present with rationale.** The proposition ends with exactly one verdict and a short why.

## The feasibility verdict

- **`feasible`** — clear approach, fits the architecture, proportionate effort → proceed to `mf-forge`.
- **`feasible-with-caveats`** — buildable, but with named caveats/risks recorded → proceed; caveats carried into
  the change's `design.md`.
- **`needs-precursor`** — not buildable until a prerequisite refactor/feature ships first → **HALT**; author the
  precursor as its own earlier version, then return.
- **`infeasible-as-specified`** — cannot be built as the PRD describes (too large, architecturally incompatible,
  blocked by an unresolved unknown) → **HALT**; rescope the PRD (back to `mf-order`).

Only `feasible` / `feasible-with-caveats` proceed to rendering. The verdict is a **human go/no-go gate**: the
person reads the proposition + verdict and decides go · rescope · precursor.

## Independent re-check (mf-inspect)

`mf-inspect`, reading the codebase fresh, sanity-checks the blueprint's feasibility claim against reality as part
of conformance — a design that reads sound on paper but doesn't hold against the code is a `blocking` finding.
