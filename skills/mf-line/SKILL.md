---
name: mf-line
description: Run the whole planning line end-to-end — Order → Gauge → Blueprint → Forge → Inspect — so the human only answers questions and reads docs. Use to take a feature idea all the way to an execution-ready openspec change in one guided flow. The PM-side conductor; pauses at the human go/no-go gates.
---

# mf-line — the planning-line conductor

You conduct the full planning line so the human doesn't invoke each stage by hand: **Order → Gauge → Blueprint →
Forge → Inspect → (Run)**. The human's only job is to **answer the interview, read the docs, and make the go/no-go
calls**; you sequence the stages, delegate the checks to fresh subagents, and pause at each human gate.

> **Note (design):** this is an **LLM conductor** — a supervised, soft version of the framework's "no LLM in the
> orchestration layer" invariant, acceptable because planning is human-in-the-loop. The on-thesis successor is a
> deterministic `minions author` CLI (backlogged). Independence still holds: each **check** stage runs as a fresh,
> blind subagent (enforced inside `mf-gauge` / `mf-inspect`), regardless of you conducting.

## The sequence

Run each stage by following its skill, with **cwd = the vault project dir** throughout — the repo-touching stages
resolve their target from `overview.md` → `repo:`. Interactive stages run here in the **main session**; checks are
delegated.

1. **`mf-order`** (main session) — interview the human → `planning/vX.Y/vX.Y_<name>.md`.
   → Pause: let the human read the PRD.
2. **`mf-gauge`** (fresh subagent) — gate the PRD.
   → `changes-requested`? relay findings, **loop back to `mf-order`** to fix, re-gauge. `clean`? continue.
3. **`mf-blueprint`** (main session; cwd = the vault project dir) — feasibility + design proposition →
   `planning/vX.Y/vX.Y_design.md` + a verdict.
   → **Human go/no-go gate.** `feasible` / `feasible-with-caveats`: continue on the human's go. `needs-precursor` /
   `infeasible-as-specified`: **HALT** — the human rescopes (back to `mf-order`) or authors a precursor version.
4. **`mf-forge`** (main session; cwd = the vault project dir) — render PRD + design →
   `<repo>/openspec/changes/NNNN-<name>/`.
5. **`mf-inspect`** (fresh subagent) — verify PRD ↔ change conformance + executability.
   → `changes-requested`? relay findings, fix the **change** (re-run `mf-forge` for the fix), **re-inspect**; loop
   until `clean`. `clean`? the change is execution-ready → hand off to `minions run`.

## Human gates (where you stop and wait)

- After **Order** — the human reviews the PRD.
- After **Blueprint** — the **go/no-go** on the feasibility verdict (the key gate).
- After **Inspect** — the human reviews conformance findings before the change is called done.

Between gates, keep moving; don't ask permission for each mechanical step. But **never** proceed past a
`needs-precursor` / `infeasible` blueprint verdict, or ship a change that `mf-inspect` left `changes-requested`.

## Never

- Do a **check** yourself in this session — always route `mf-gauge` / `mf-inspect` through their fresh, blind
  subagents (independence is the point).
- Skip a stage, or collapse the two producer→checker pairs into one pass.
- Grow scope, cut tasks, or write the change outside `mf-forge`.
