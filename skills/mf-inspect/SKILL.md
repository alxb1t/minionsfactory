---
name: mf-inspect
description: Independently verify that an openspec change faithfully renders its PRD and is execution-ready. Use after mf-forge — stage 5 of the planning line, the last gate before execution. Spawns a fresh, blind subagent, writes a conformance findings file, and loops fix→re-inspect until clean.
---

# mf-inspect — PRD ↔ change conformance gate (independent)

You are the **final gate before execution**: does the openspec change **faithfully render the PRD** and is it
**execution-ready**? Like `mf-gauge`, your value is **independence** — the check must be blind to whoever produced
the change (`mf-forge`) and the design (`mf-blueprint`), or it is theatre. This is the planning-side mirror of the
execution loop's fresh reviewer.

## Setup

Run with **cwd = the target repo**. Resolve the vault from `.env` → `VAULT_PROJECT_DIR`. Inputs are the PRD
(`$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_<name>.md`) and the change dir (`openspec/changes/NNNN-<name>/`).

## The mechanism: a fresh, blind subagent

**Do not judge inline** — you may be carrying the authoring/render context. **Launch a fresh subagent** (the Task
tool) and give it **only**:

1. the **PRD path**,
2. the **change dir path**,
3. the **conformance rubric** — `~/.claude/skills/rubrics/conformance.md` (installed) or
   `skills/rubrics/conformance.md`, and the **feasibility rubric** (for criterion 7's design re-check),
4. the **findings path** (below),
5. the instruction block below.

Pass **no** render history and no prior reasoning — only those paths. Relay the subagent's verdict + headline
findings to the human.

### Instruction for the subagent

> You are an independent conformance checker with no stake in this change passing. Read the PRD, the change
> (`proposal.md` · `design.md` · `tasks.md` · `specs/` delta), and the rubrics. Check each conformance criterion:
> - **completeness** — every PRD requirement maps to a task/scenario (nothing dropped);
> - **no scope creep** — nothing in the change is untraceable to a PRD requirement;
> - **bidirectional trace** — every spec-delta `#### Scenario:` ↔ a PRD acceptance clause (each scenario has a
>   `Key:`; each genuinely expresses its requirement);
> - **design.md is real** — actual decisions, no open questions, consistent with `planning/vX.Y/vX.Y_design.md`;
> - **phases execution-ready** — every `tasks.md` phase is machine-checkable, self-contained, right-sized, and
>   **code+commit only** (a research/design-lock phase is blocking);
> - **contract complete (M)** — all four artifacts present; change id/version matches the PRD;
> - **design soundness** — sanity-check the design still holds against the real codebase (read it); a proposition
>   that doesn't survive contact with the code is blocking.
> Write the findings file (shape below): one finding per failed criterion, each citing the exact PRD requirement +
> change artifact/line and a one-line fix. Set `verdict: clean` only if every (M) passes and no blocking finding
> is open. A doc-only change with an N-A `specs/` delta satisfies the contract/trace criteria accordingly. Do not
> invent findings.

## Findings file

Written by the subagent to `$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_inspect.md`:

```markdown
---
type: inspect
plan: vX.Y
change: NNNN-<name>
verdict: clean | changes-requested
round: 1
open_blocking: N
checked: YYYY-MM-DD
---

# <Project> vX.Y — change conformance (mf-inspect, round N)

## Summary
2–3 sentences: does the change faithfully render the PRD and is it execution-ready?

## Findings
### I1 blocking open — <short title>
- **Criterion:** the conformance rubric item it fails
- **Where:** PRD requirement ↔ change artifact/line
- **What / why / fix:** the gap, its consequence, a one-line fix pointer.
```

## The loop

- `clean` → the change is execution-ready. Hand off: `minions run` can build it.
- `changes-requested` → relay the findings; the human (or `mf-forge` in a fix pass) fixes the **change** →
  **re-inspect** with a fresh subagent (bump `round`, scope to the fix, flip findings `open → fixed → verified`)
  → repeat until `clean`.

## Never

- Judge the change inline — spawn the blind subagent; independence is the point.
- Edit the change or the PRD — you gate; `mf-forge` / the human fixes.
- Re-litigate the PRD's scope (a genuine PRD-vs-change contradiction is itself a finding). Invent findings, or pad.
