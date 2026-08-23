# Tasks — 0004-planning-skills

Ordered phases for v0.4. **Build mode: by hand** (Claude Code + human; no orchestrator automation). **Doc-only
change** — ships prose (skills, rubrics, template, make targets); the per-phase "gate" is: the repo gate stays green
(markdown-only — ruff/ty/pytest/`specs check` unaffected) and the phase's deliverable exists as specified in the
PRD. Read `proposal.md` + `design.md` (this dir) and the vault PRD (`prd/v0.4_planning_skills.md`, R1–R10) first.

**Per-phase ritual.** Author the phase's deliverable → confirm the repo gate stays green → **commit** with a
`Change: 0004-planning-skills` trailer (contiguous with `Co-Authored-By:` — see `design.md` §8) → append to
`CHANGELOG.md [Unreleased]` → prepend the vault `log.md` + update `overview.md`. One phase, then stop for review.

## Progress

- [ ] 1 — Rubrics (`prd-readiness` · `feasibility` · `conformance`) + `skills/rubrics/README.md`
- [ ] 2 — `mf-order` (interview → PRD) + `mf-gauge` (PRD readiness gate, fresh + blind)
- [ ] 3 — `mf-blueprint` (feasibility verdict + design proposition vs the codebase)
- [ ] 4 — `mf-forge` (render PRD + design → `openspec/changes/<id>/`)
- [ ] 5 — `mf-inspect` (PRD↔change conformance + executability, fresh + blind; loops)
- [ ] 6 — `mf-line` (LLM conductor over phases 2–5)
- [ ] 7 — `template/vault-pm/` + `make install-skills`/`uninstall-skills` + README

---

## Phase 1 — Rubrics
The shared definitions of "done," authored first (every later skill references them). `skills/rubrics/`:
`prd-readiness.md` (drives `mf-order`, gates `mf-gauge`), `feasibility.md` (produced by `mf-blueprint`, re-checked
by `mf-inspect`), `conformance.md` (gates `mf-inspect`) + `README.md` (the shared (M)/(J) split, verdict
conventions, skill→rubric map). **Acceptance:** three rubric files + README exist; each criterion tagged (M) or
(J); verdict conventions stated; repo gate green.

## Phase 2 — `mf-order` + `mf-gauge`
`skills/mf-order/` (interactive interview driven by `prd-readiness`, writes `prd/vX.Y_<name>.md`, splits
multi-feature asks) + `skills/mf-gauge/` (spawns a fresh subagent given only the PRD + `prd-readiness`; emits
`verdict: clean | changes-requested` + findings). **Acceptance:** both skills exist; `mf-gauge` spawns a fresh
subagent (independence); flags an unready PRD, passes a clean one; repo gate green.

## Phase 3 — `mf-blueprint`
`skills/mf-blueprint/` — reads the PRD + target codebase, writes `prd/vX.Y_design.md` per `feasibility`, emits the
4-way verdict, HALTs on `needs-precursor`/`infeasible`. **Acceptance:** skill exists; design proposition cites real
modules; verdict + rationale present; HALT path documented; repo gate green.

## Phase 4 — `mf-forge`
`skills/mf-forge/` — cwd = repo, reads the PRD + design from the vault via `.env`, writes `openspec/changes/<id>/`
(four artifacts; `Change:` trailer convention). tasks = code+commit only (no research phase). **Acceptance:** skill
exists; produces all four artifacts; `design.md` ← the blueprint; repo gate green.

## Phase 5 — `mf-inspect`
`skills/mf-inspect/` — spawns a fresh subagent given the PRD + change; checks `conformance`; emits verdict +
findings; loops (fix → re-inspect). **Acceptance:** skill exists; fresh subagent; flags a dropped/added requirement
+ a research phase; passes a faithful change; repo gate green.

## Phase 6 — `mf-line`
`skills/mf-line/` — sequences order → gauge → blueprint → forge → inspect; interactive stages in the main session,
checks delegated to fresh subagents, pauses at the human gates. **Acceptance:** skill exists; walks the full line;
pauses at the interview + blueprint + inspect gates; checks run fresh; repo gate green.

## Phase 7 — Template + install/uninstall
`template/vault-pm/` (filled worked example: overview · roadmap · prd/ · backlog · log · decisions) + `make
install-skills` (symlink `skills/mf-*` + `skills/rubrics` → `~/.claude/skills/`) + `make uninstall-skills` + README
docs. **Acceptance:** template is a worked example (not placeholders); install links all six skills + the rubrics;
uninstall removes them; both documented; repo gate green.

---

## Release (end of build)
Doc-only change: **no spec fold** (N-A delta). Cut `## [0.4.0]` in `CHANGELOG.md`, bump `pyproject`, verify every
`base..HEAD` commit carries a `Change: 0004-planning-skills` trailer, tag `v0.4.0`, move the change to
`openspec/changes/archive/0004-planning-skills/`.
