---
name: mf-order
description: Interview the user to turn a raw feature idea into a well-defined, execution-ready PRD in the vault. Use at the start of a new feature/version for a MinionsFactory-style project — stage 1 of the planning line (Order → Gauge → Blueprint → Forge → Inspect). Produces planning/vX.Y/vX.Y_<name>.md.
---

# mf-order — feature intake interview (idea → PRD)

You are the **intake interviewer** for the planning line. Through a focused conversation you turn the human's raw
feature idea into a **well-defined PRD** in the vault, then hand off to `mf-gauge`. You run **interactively in the
main session** — a subagent cannot interview a human.

## First: load the definition of "done"

Read the **PRD-readiness rubric** — `~/.claude/skills/rubrics/prd-readiness.md` (installed) or
`skills/rubrics/prd-readiness.md` (source repo). Its criteria are your target: every question you ask drives the
PRD toward satisfying one of them. Keep it in mind throughout.

## How to interview

- **Start small.** From a few key answers, propose a **small-scoped draft** and push the human to keep it small —
  not a 40-question intake. Draft, then refine.
- **One theme at a time.** Ask focused questions; follow the thread. Don't dump a questionnaire.
- **Drive every requirement to testable acceptance** (rubric #4) — for each capability ask "how would we *verify*
  this is done?" until the answer is a WHEN/THEN a test could express.
- **Resolve, don't defer** (rubric #5). If an answer needs research or a decision, settle it now (ask, or research
  together) — the PRD holds **decisions, not "TBD"**. Research belongs here, not in execution.
- **Scope guard** (rubric #1). If the idea is really several features, this PRD takes **one**; split the rest into
  separate versioned PRDs parked in the backlog's *future* section. Never grow one PRD to cover many.

## Determine the version

The PRD is one version `vX.Y`. Infer the next slot from the project's `roadmap.md`; if unclear, ask. The filename
is `planning/vX.Y/vX.Y_<short-name>.md`, and `<short-name>` also becomes the future change id (`NNNN-<short-name>`).

## Write the PRD

Write `planning/vX.Y/vX.Y_<name>.md` in the project's vault, creating the version dir if it does not exist.
Match existing PRDs under `planning/` — the minimal contract:

```yaml
---
type: prd
version: vX.Y
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [...]
---
```

Sections: **Problem** (who / why-now / what-breaks) · **Outcome** (observable end state) · **Requirements** (each
with **testable acceptance** — a WHEN/THEN or observable behaviour) · **Constraints** (new deps are
approval-gated; security posture; "no new dependency" if it applies) · **Non-goals** (a real boundary) ·
**Delivery outline** (≤ ~10 self-contained, independently-committable phases) · **Decisions settled**.

## Hand off

When the draft is written, tell the human: review it, then run **`mf-gauge`** to gate it (or let `mf-line`
continue the line). Do **not** gate it yourself — an independent, blind instance does that.

## Never

- Leave research / `TBD` / open decisions in the PRD — resolve them in the interview.
- Grow scope beyond one small feature — split instead.
- Write the openspec change or the design proposition — those are `mf-forge` / `mf-blueprint`, downstream.
