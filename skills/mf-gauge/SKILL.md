---
name: mf-gauge
description: Independently gate a PRD for readiness (small, testable, no unresolved research) before it goes downstream. Use after mf-order, or on any PRD — stage 2 of the planning line. Spawns a fresh, blind subagent and writes a readiness findings file with a clean|changes-requested verdict.
---

# mf-gauge — PRD readiness gate (independent)

You gate a **PRD** against the PRD-readiness rubric and write a **findings file**. Your value is **independence**:
the check must be blind to whatever conversation produced the PRD, or it is theatre.

## The mechanism: a fresh, blind subagent

**Do not judge the PRD in this session** — you may be carrying the authoring context. Instead, **launch a fresh
subagent** (the Task tool) and give it **only**:

1. the **PRD path** to check,
2. the **rubric path** — `~/.claude/skills/rubrics/prd-readiness.md` (installed) or
   `skills/rubrics/prd-readiness.md` (source repo),
3. the **findings path** to write (below),
4. the instruction block below.

Pass **no** interview history and no prior reasoning — only those paths. When the subagent returns, relay its
verdict + headline findings to the human.

### Instruction for the subagent

> You are an independent PRD readiness checker with no stake in this PRD passing. Read the PRD and the rubric. For
> each rubric criterion decide pass/fail:
> - **(M) criteria — check mechanically:** no `TBD` / `???` / "decide later" / "figure out" / "investigate" /
>   "research needed" markers; a **Non-goals** section exists; a **version `vX.Y`** is declared; every requirement
>   has a non-empty acceptance clause.
> - **(J) criteria — judge:** one small feature (not a bundle); a real problem; an observable outcome; acceptance
>   genuinely falsifiable; no requirement secretly defers a decision to execution; ≤ ~10 self-contained phases;
>   Non-goals meaningful; constraints stated; prerequisites/ordering identified.
> Write the findings file (shape below): one finding per failed criterion, each citing the PRD section it fails and
> a one-line fix. Set `verdict: clean` only if every (M) passes and no (J) has an open blocking finding. Do not
> invent findings to look thorough — a genuinely ready PRD passes.

## Findings file

Written by the subagent to `planning/vX.Y/vX.Y_gauge.md` (in the vault, beside the PRD):

```markdown
---
type: gauge
plan: vX.Y
verdict: clean | changes-requested
open_blocking: N
checked: YYYY-MM-DD
---

# <Project> vX.Y — PRD readiness (mf-gauge)

## Summary
2–3 sentences: is the PRD ready, and the headline gaps.

## Findings
### G1 blocking — <short title>
- **Criterion:** the rubric item it fails
- **Where:** the PRD section
- **What / why / fix:** the gap, its consequence, and a one-line fix pointer.
```

## Outcome

- `clean` → the PRD is ready; hand off to **`mf-blueprint`** (feasibility + design).
- `changes-requested` → relay the findings; the human loops back to **`mf-order`** to fix, then re-gauge.

## Never

- Judge the PRD inline — spawn the blind subagent; independence is the whole point.
- Edit the PRD — you gate; `mf-order` fixes.
- Invent findings, or pad. Blocking first; concision over volume.
