---
name: mf-blueprint
description: Assess whether a PRD is technically feasible in this codebase and produce a design proposition before any tasks are cut. Use after mf-gauge passes — stage 3 of the planning line. Reads the PRD + the repo, writes planning/vX.Y/vX.Y_design.md, and emits a feasible|feasible-with-caveats|needs-precursor|infeasible-as-specified verdict (a human go/no-go gate).
---

# mf-blueprint — feasibility spike + design proposition

You answer the question the earlier stages can't: **can this PRD actually be built in *this* codebase, and how?**
A clean, testable PRD can still describe a 3-week refactor or something infeasible — you catch that **now**, at
planning time, not mid-execution. You are a **producer with a gate**: you write the design proposition and emit a
feasibility verdict; the human reads it and decides go / no-go. (`mf-inspect` re-checks your design independently
later, so you run in the main session — no fresh-subagent requirement here.)

## Setup

Run with **cwd = the target repo** (you must read its code). Resolve the vault from the repo's `.env` →
`VAULT_PROJECT_DIR`; the PRD is `$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_<name>.md`. First read the **feasibility
rubric** — `~/.claude/skills/rubrics/feasibility.md` (installed) or `skills/rubrics/feasibility.md` (source repo).

## Do the spike

Read the PRD, then explore the **real codebase** against it:

- Identify the **actual modules/files** the feature touches and any new components — where the code will land.
- Judge **architecture fit** — does it slot into the current design, or need a refactor first?
- Estimate **effort** — a rough phase count; is it proportionate and within the ≤ ~10-phase, one-context bound?
- Surface **blockers/prerequisites** — new dependencies (approval-gated), missing infra, external systems,
  genuine unknowns needing a spike.
- Weigh at least one **simpler alternative** (the anti-over-engineering check).
- Name the **risks** — what could make the build fail or balloon.

Use `Grep` / `Glob` / `Read` freely; delegate broad codebase searches to an `Explore` subagent if it helps. Cite
real paths — a proposition that doesn't reference the actual code isn't feasibility, it's a guess.

## Write the design proposition

Write `$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_design.md` (private thinking stays in the vault; `mf-forge` later
renders the sanitized subset into the change's `design.md`):

```markdown
---
type: design
version: vX.Y
verdict: feasible | feasible-with-caveats | needs-precursor | infeasible-as-specified
created: YYYY-MM-DD
---

# <Project> vX.Y — Design proposition (mf-blueprint)

## Approach
Modules/files touched, new components — where the code lands (cite real paths).

## Architecture impact
Fits as-is, or the refactor required (→ precursor version?).

## Effort
Rough phase count; proportionate? within ≤ ~10 self-contained phases?

## Blockers & prerequisites
New deps (approval-gated), missing infra, external systems, unknowns needing a spike.

## Alternatives considered
At least one simpler approach + why chosen / rejected.

## Risks
What could make the build fail or balloon.

## Verdict
<one of the four> — a short rationale.
```

## The verdict is a human go/no-go gate

- **`feasible`** / **`feasible-with-caveats`** → proceed to **`mf-forge`** (caveats carried into the change's
  `design.md`).
- **`needs-precursor`** → **HALT**. Recommend authoring the prerequisite refactor/feature as its own earlier
  version (a new `mf-order` run), then returning.
- **`infeasible-as-specified`** → **HALT**. Recommend rescoping the PRD (back to `mf-order`).

Present the verdict + the headline reasons to the human and let them make the call — don't proceed past a HALT on
your own.

## Never

- Cut tasks or write the openspec change — that's `mf-forge`, downstream.
- Hand-wave the approach, or hide an effort blow-up to keep the feature alive — an honest `needs-precursor` /
  `infeasible` verdict is the whole point of this stage.
