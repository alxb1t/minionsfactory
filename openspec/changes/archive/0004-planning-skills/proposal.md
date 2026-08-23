# Proposal — 0004-planning-skills

**Change:** `0004-planning-skills` · **Version:** v0.4 · **PRD:** vault `prd/v0.4_planning_skills.md` (R1–R10)
**Build mode:** hand-authored (Claude Code + human; no orchestrator automation). **Doc-only change** — ships prose
(skills, rubrics, a template, make targets), not test-backed Python, so its **spec delta is N-A** (see
`specs/README.md`).

## Why

The framework has a proven **execution** side but no tooled, enforced **planning** side. Producing a PRD is ad-hoc
(no interview discipline, no shared "well-defined" bar); the PRD → repo-change translation is unverified (no
independent check that the change faithfully renders intent — the "garbage plan → confidently-wrong autonomy" risk,
one layer upstream); and **feasibility is never assessed against the codebase** (a clean PRD + a faithful change + a
green gate can still be building a 3-week refactor). Planning is the leverage point — "execution is only as good as
the plan it's given" — and it currently has none of the producer→checker enforcement the execution loop rests on.

## What (scope)

A six-skill **planning line** — the PM-side mirror of `minions run` (Order → Gauge → Blueprint → Forge → Inspect →
Run) — plus its shared rubrics, a template, and install tooling:

1. **Three rubrics (R7)** — `skills/rubrics/{prd-readiness,feasibility,conformance}.md`: the shared definitions of
   "done," each criterion tagged (M) machine / (J) judgment. The planning-side analog of the machine gate.
2. **`mf-order` + `mf-gauge` (R1, R2)** — interview → PRD (`prd/vX.Y_<name>.md`); a fresh, blind readiness gate.
3. **`mf-blueprint` (R3)** — feasibility verdict + design proposition (`prd/vX.Y_design.md`) against the codebase;
   HALTs on infeasible/needs-precursor. Closes the feasibility gap.
4. **`mf-forge` (R4)** — render the PRD + design → `openspec/changes/<id>/` (four artifacts; `Change:` trailer).
5. **`mf-inspect` (R5)** — fresh, blind PRD↔change conformance + executability; loops to clean.
6. **`mf-line` (R6)** — an LLM conductor sequencing the line, delegating checks to fresh subagents, pausing at the
   human gates.
7. **`template/vault-pm/` (R8) + `make install-skills`/`uninstall-skills` (R9)** — a worked example of the vault PM
   layout; symlink install/uninstall to `~/.claude/skills/`.

## Approach

- **Skills are prose**, authored by hand (no loop) — self-hosting resumes at v0.5, the first clean *code* feature.
- **Independence is enforced inside the check-skills** (`mf-gauge`, `mf-inspect` spawn a fresh subagent given only
  the artifact + rubric), so it holds whether a stage is run manually or by `mf-line`.
- **Private/public split** — the PRD + design proposition stay in the vault; only the sanitized change crosses to
  the repo (that crossing is `mf-forge`).
- **Tracked as a doc-only change (PRD Option 1)** — full `Change: 0004-planning-skills` traceability on every
  commit, but an **N-A spec delta** (nothing test-backed to bind); the reusable precedent for future prose
  deliverables. `specs check` passes trivially (no scenarios added; test markers unaffected).

## Out of scope (deferred)

Deterministic `minions author` CLI (the no-LLM successor to `mf-line`) → backlog. Secure `mf-research` → backlog.
`/audit` → v0.5 (paired with the remediation loop). `minions bootstrap` full stamping → v0.8. Cross-model checks →
backlog. Notion/Confluence/Linear backends. No new runtime dependency; no edit to the vault-wide `CLAUDE.md` schema.

## Success criteria

All six `mf-` skills exist under `skills/` with their three rubrics; `make install-skills` symlinks them to
`~/.claude/skills/` and `make uninstall-skills` removes them cleanly (both documented); `template/vault-pm/` is a
filled worked example; the repo gate stays green (markdown-only; `specs check` unaffected); every commit carries a
`Change: 0004-planning-skills` trailer; and the change archives cleanly. The real proof is **v0.5 is authored with
this line.**
