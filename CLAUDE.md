# minions_factory — shared context for Claude Code

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**. Pointed
at a target repo, it drives a **vault-backed implementation plan** to completion: a fresh, per-phase **coder** builds the
plan one phase per spawn (the orchestrator **runs the quality gate itself** and detects the advance); at plan end it
fans out **review ‖ security ‖ simplify** as fresh read-only instances, runs a **converge loop** over their
blocking findings, and hands a **release** step the gated, tagged result. Every role is a **fresh, single-role
Claude Code instance**; the driver **advances or halts** on machine-checkable disk state. The project dogfoods
its own conventions — vault-backed planning, a strict quality gate, all state on disk.

Hard constraints that shape the code: **no LLM sits in the orchestration layer** (the driver is deterministic,
unit-testable control flow); **the orchestrator runs the objective checks itself** (the gate + git state — so
the agent it drives can't game them); **all state lives on disk** (a run resumes from the plan's `current_phase`
+ git + the ledger, never from memory); and **roles are fresh instances behind a provider seam** (harness-
agnostic — Claude Code is the default adapter, with no dependency on a harness's internals).

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (build a phase, review the branch diff,
> run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.** Read this
> for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## The plan lives in a private vault — read it first

The full, canonical implementation plan is **not in this repo** (this repo is public — it must never contain
the vault's absolute path). It lives in a private Obsidian vault whose location is stored in **`.env`**
(gitignored) as **`VAULT_PROJECT_DIR`**.

1. Read `.env` and load `VAULT_PROJECT_DIR` — the absolute path to the vault project folder. If it is missing,
   copy `.env.example` → `.env` and ask the human to fill it in. **Never hardcode or print the real path in
   committed files.**
2. Read the **latest implementation plan** in `$VAULT_PROJECT_DIR/implementation_plans/` — the
   `vX.Y_*implementation_plan.md` with the **highest version number** (**ignore `archive/`**). It is the source
   of truth for scope, decisions, architecture, repo layout, the engineering conventions, the per-phase steps,
   **and the phase workflow contract** — including whether the plan runs **autonomously** or in a **human-
   written / teacher mode**. Lower-versioned plans are completed predecessors — historical record only.
3. The plan tracks progress via its **`current_phase`** frontmatter + the **Progress ledger** (bottom of the
   plan); the newest entries sit at the **top** of `$VAULT_PROJECT_DIR/log.md` (this project's `log.md` is
   **prepend / newest-first**). Read these to see where the work stands. If the plan references a Phase-0
   research file, read it too.

Plans and their research/findings files live in `$VAULT_PROJECT_DIR/implementation_plans/` (version-prefixed,
e.g. `v0.1_loop_spine_implementation_plan.md`); the project's `overview.md`, `log.md`, `backlog.md`,
`release_log.md`, `decisions.md`, and `open_questions.md` sit at `$VAULT_PROJECT_DIR/`. Do not re-derive
decisions already settled in the plan. If something there conflicts with reality, raise it with the human rather
than silently diverging. Any vault writes stay **inside `$VAULT_PROJECT_DIR`** and follow the conventions already
visible in that folder (the `log.md` / `overview.md` / `backlog.md` shapes) — `VAULT_PROJECT_DIR` is the only
vault path this repo knows.

---

## The quality gate (a phase is done only when all are green)

- `pytest` — all tests pass. **Test-first (red → green)** for every unit of logic we control. The suite doubles
  as executable documentation — name tests as behavioural sentences.
- `ruff format --check` + `ruff check` — format + lint clean (`D` docstrings + `ANN` annotations enabled).
- `ty check` — strict type-check clean.

External effects are **faked** in tests behind their seams — the **provider** (`claude -p`) behind the
`Provider` Protocol (`FakeProvider`) and the **gate subprocess** behind the gate seam (`FakeGate`) — so **no
unit test spawns a real Claude Code instance or hits the network**; real `claude -p` is exercised only in an
end-to-end dogfood run. CI (`.github/workflows/ci.yml`) runs the gate on every push. Full conventions are in the
plan (§ Engineering conventions).

The repo keeps a **`CHANGELOG.md`** in [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format, aligned
to the version line (plan `vX.Y` = CHANGELOG release = `pyproject` version = git tag `vX.Y.0`): each phase
appends under `## [Unreleased]`; plan completion cuts `## [X.Y.0]`. Keeping it current is part of the phase
ritual — see the plan + the vault's `conventions.md`.

---

## Engineering conventions

The plan's **§ Non-negotiable principles / Engineering conventions** is authoritative — read it. In brief, the
load-bearing seams are:

- a **`Provider` Protocol** — a real `ClaudeCodeProvider` (`claude -p`, `--output-format json`) + a
  `FakeProvider`; the driver depends on the **seam**, never the CLI directly (harness-agnostic + unit-testable).
- **the orchestrator runs the gate itself** via a `run_gate(repo)` seam (real subprocess + `FakeGate`); the gate
  command list is **read from the target repo**, not hardcoded (so a non-Python target needs no code change).
- **plan state is read from disk** — `read_plan_state(...) -> PlanState`; plan-selection = highest `vX.Y_`,
  ignore `archive/`.
- **the driver is deterministic control flow** — no LLM; **advance is *detected*** (a new commit landed **and**
  `current_phase` moved), not trusted; a halt writes a disk contract the next run resumes from.
- roles are defined by a **prompt + a disk I/O contract** — each role prompt (the vault's `prompts/`, copied
  into the repo's `prompts/`) is the first-class authority for what that instance does.

---

## Guardrails (invariants — hold for every role)

- **Never commit `.env` or any secret** (the vault path, any API key). `.env` is gitignored; keep the vault path
  and secrets there only. The committed `CLAUDE.md` / `.env.example` stay path-free.
- **Deps minimal + human-gated.** Any new dependency (`uv add`) — argue for it and **wait for approval** before
  installing. Test/lint/type tools stay dev-only; keep the runtime lean.
- **No LLM in the orchestration layer; the orchestrator owns the objective checks.** The driver stays
  deterministic and testable; the gate + git state are run by the orchestrator (not the agent it drives) so they
  can't be gamed.
- **State lives on disk.** Reconstruct "where are we" from the plan's `current_phase` + Progress ledger + git —
  never from memory. Resume is therefore free.
- The **vault is the single source of truth** for "where are we." If your role updates it, keep it accurate
  (prepend newest-first in `log.md`, the plan's `current_phase` + Progress ledger, `backlog.md`); a fresh
  session relies on it.
