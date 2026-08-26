---
name: mf-forge
description: Render an approved PRD + design proposition into an execution-ready openspec change (proposal, design, tasks, spec delta). Use after mf-blueprint returns feasible — stage 4 of the planning line. Runs in the repo, reads the vault PRD/design via .env, writes openspec/changes/NNNN-<name>/.
---

# mf-forge — render PRD + design → openspec change

You turn the approved **PRD** (the *what*) + **design proposition** (the *how*) into the repo's **openspec change**
— the execution-ready contract the loop consumes. This is the **private → public crossing**: the PRD and design
proposition hold the full thinking in the vault; you render only the **sanitized, execution-ready subset** into the
repo. You are a producer; `mf-inspect` verifies your output.

## Setup

Run with **cwd = the target repo**. Resolve the vault from `.env` → `VAULT_PROJECT_DIR`. Read both:
- `$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_<name>.md` (requirements + acceptance),
- `$VAULT_PROJECT_DIR/planning/vX.Y/vX.Y_design.md` (the blueprint — must be `feasible` /
  `feasible-with-caveats`; if it HALTed, stop and send the human back).

**Determine the change id.** `NNNN` = the next number after the highest existing dir under `openspec/changes/`
**including `archive/`**; `<name>` = the PRD's `<short-name>`. E.g. `0005-<name>`.

## Write the change — four artifacts, always

Create `openspec/changes/NNNN-<name>/`:

1. **`proposal.md`** — leading YAML frontmatter declaring the release version, then a header line
   (`**Change:** NNNN-<name> · **Version:** vX.Y · **PRD:** vault path`), then **Why** (from the PRD Problem),
   **What (scope)** (the requirements as a numbered list), **Approach** (from the design proposition, sanitized),
   **Out of scope**, **Success criteria**.

   ```markdown
   ---
   version: vX.Y
   ---

   # Proposal — NNNN-<name>
   ```

   The `version:` frontmatter is **required and machine-read**: the change is the unit of release, so the version
   travels with it, and the orchestrator's change-state reader takes the release version from here and nowhere else.
   It must match `vX.Y` exactly (no patch component). A change whose `proposal.md` carries no frontmatter, no
   `version` key, or a malformed value is **refused at preflight**, before any role is spawned.
2. **`design.md`** — the technical *how*, from the blueprint's design proposition: real decisions (modules touched,
   new components, key trade-offs). **No open design questions** — those were resolved at `mf-blueprint`. A small
   change still gets a brief one.
3. **`tasks.md`** — a `## Progress` checklist (`- [ ] N — <title>`, current = first unchecked) over ordered
   **code+commit** phases from the PRD delivery outline + design, plus a per-phase ritual (test-first → gate green
   → commit with a `Change: NNNN-<name>` trailer → CHANGELOG). **No research / design-lock phase** — all research
   and design were done on the planning side; a plan the loop receives opens at the first *code* phase.
4. **`specs/` delta** — for each PRD requirement, an `## ADDED Requirements` (or `MODIFIED`/`REMOVED`) block with a
   `### Requirement:` and keyed `#### Scenario:` entries translating the requirement's **testable acceptance** into
   WHEN/THEN:

   ```markdown
   ## ADDED Requirements
   ### Requirement: <name>
   The system SHALL <behaviour>.

   #### Scenario: <name>
   - **Key:** `<capability>:<requirement-slug>:<scenario-slug>`
   - **Layers:** unit
   - **WHEN** <trigger>
   - **THEN** <observable outcome>
   ```

   Each PRD acceptance clause → at least one scenario; internal logic declares `Layers: unit`, system-boundary
   declares `unit` + `e2e` (e2e reserved). **Doc-only change:** no behavioural capability → write `specs/README.md`
   marking the delta **N-A** instead (see `0004-planning-skills` as the precedent).

## Trailer convention

Tell the human (and record in `tasks.md`): every phase commit for this change carries `Change: NNNN-<name>`
**contiguous** with `Co-Authored-By:` (no blank line between — git parses the trailer block as the last paragraph).

## Hand off

When the change is written, hand off to **`mf-inspect`** to verify PRD ↔ change conformance + executability. Do
**not** verify it yourself (independence), and do **not** fold or archive (that's the release role, at ship time).

## Never

- Add a feature, task, or scenario the PRD did not authorize (no scope creep — `mf-inspect` flags it).
- Include a research / design-lock phase in `tasks.md` (execution plans are code+commit only).
- Leave an open design question in `design.md`, or copy the PRD's private reasoning verbatim (render the sanitized
  subset).
