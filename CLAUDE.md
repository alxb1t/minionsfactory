# minions_factory — shared context for Claude Code

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**. Pointed
at a target repo, it drives an **in-repo change** to completion: a **coder** builds the change's `tasks.md`
phase by phase (the orchestrator **runs the quality gate itself** and detects the advance); at plan end it fans
out **review ‖ security ‖ simplify** as fresh read-only instances, runs a **converge loop** over their blocking
findings, and hands a **release** step the gated, tagged result — which **folds the change's spec delta into the
living `openspec/specs/`** and archives the change. Every role is a **fresh, single-role Claude Code instance**; the
driver **advances or halts** on machine-checkable disk state. The project dogfoods its own conventions —
spec-driven changes, a strict quality gate, all state on disk.

Hard constraints that shape the code: **no LLM sits in the orchestration layer** (the driver is deterministic,
unit-testable control flow); **the orchestrator runs the objective checks itself** (the gate + git state — so
the agent it drives can't game them); **all state lives on disk** (a run resumes from the change's `tasks.md`
progress + git, never from memory); and **roles are fresh instances behind a provider seam** (harness-agnostic —
Claude Code is the default adapter, with no dependency on a harness's internals).

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (author a change, build a phase, review the
> branch diff, run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.**
> Read this for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## Where the work is defined — spec-driven changes (in-repo)

This repo follows **spec-driven development** (OpenSpec-style). Two in-repo trees under **`openspec/`** carry the
truth:

- **`openspec/specs/<capability>/spec.md`** — the **living, test-backed behavioral spec**: what the system does
  *now*. Each requirement carries WHEN/THEN **scenarios**, and every scenario is bound to a proving test
  (`@pytest.mark.spec("<key>")`) — enforced by the **spec-binding check** (`specs check`; see the gate below).
- **`openspec/changes/<change-id>/`** — the **active change** you build: `proposal.md` (scope/approach),
  `design.md` (technical decisions), `tasks.md` (the ordered phases + progress checkboxes), and `specs/` (the
  **delta** — `## ADDED / MODIFIED / REMOVED Requirements` for this change). Read the change **in-tree**; record
  progress in `tasks.md`. On release the delta **folds** into the living `openspec/specs/` and the change moves to
  `openspec/changes/archive/<change-id>/`.

**Progress lives in `tasks.md` + git** — read the active change (`openspec/changes/<id>/`), its `tasks.md`, and
the tail of the vault `log.md` to see where the work stands. Don't re-derive decisions already settled in the change; if
something there conflicts with reality, raise it with the human rather than silently diverging.

**The vault holds product intent, research, findings, and bookkeeping.** A private Obsidian vault whose path is
in **`.env`** (gitignored) as **`VAULT_PROJECT_DIR`** — **never hardcode or print it**; the committed
`CLAUDE.md` / `.env.example` stay path-free. There: the **PRD** (`prd/` — the product intent *upstream* of a
change), **research** (`research/`), the read-only roles' **findings files**, and the narrative record
(`log.md` **newest-first**, `overview.md`, `backlog.md`, `release_log.md`, `decisions.md`). Any vault writes stay
**inside `$VAULT_PROJECT_DIR`** and follow the shapes already there. If `.env` / `VAULT_PROJECT_DIR` is missing,
copy `.env.example` → `.env` and ask the human to fill it in.

**Commits carry a `Change: <change-id>` git trailer** so history reads back to intent
(`git log --grep "Change: <id>"` → the commits → `openspec/changes/archive/<id>/` → proposal/design/tasks/delta).

---

## The quality gate (a phase is done only when all are green)

The gate **leads with a locked lock-sync step** — `uv sync --locked`, which asserts `uv.lock` is up to date and
fails rather than silently re-resolving — so the gate certifies what the lock pins rather than whatever `.venv`
happens to hold. It is environment setup rather than a quality *axis*, so it is listed here as the step it is and
the four axes follow:

- `pytest` — all tests pass. **Test-first (red → green)** for every unit of logic we control. The suite doubles
  as executable documentation — name tests as behavioural sentences.
- `ruff format --check` + `ruff check` — format + lint clean (`D` docstrings + `ANN` annotations enabled).
- `ty check` — strict type-check clean.
- **`specs check`** — the spec binding holds: every scenario is test-backed and every `spec` marker resolves
  (a structural check; the reviewer judges whether a test *genuinely* exercises its scenario). This repo runs
  **from source**: invoke it like the existing `run` command —
  `uv run python -m orchestrator specs check --strict`. There is **no installed `minions` binary yet**;
  `minions specs check` is only the future installed alias.

Six steps in all — the sync, format, lint, typecheck, test, and the spec checker last. `.minions/minions.toml`'s
`gate` array is the source of truth (the orchestrator runs *it*); `Makefile`'s `gate` target, `README.md` and CI
mirror it command-for-command.

External effects are **faked** in tests behind their seams — the **provider** (`claude -p`) behind the
`Provider` Protocol (`FakeProvider`) and the **gate subprocess** behind the gate seam (`FakeGate`) — so **no
unit test spawns a real Claude Code instance or hits the network**; real `claude -p` is exercised only in an
end-to-end dogfood run. CI (`.github/workflows/ci.yml`) runs the gate on every push. The gate **command list is
read from the target repo** (`.minions/minions.toml`), not hardcoded, so a non-Python target needs no code change.

The repo keeps a **`CHANGELOG.md`** in [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format, aligned
to the version line (change `vX.Y` = CHANGELOG release = `pyproject` version = git tag `vX.Y.0`): each phase
appends under `## [Unreleased]`; the release step cuts `## [X.Y.0]`. Keeping it current is part of the phase
ritual — see the change + the vault's `conventions.md`.

---

## Engineering conventions

The change's **`design.md`** and the vault's **`decisions.md`** are authoritative — read them. In brief, the
load-bearing seams are:

- a **`Provider` Protocol** — a real `ClaudeCodeProvider` (`claude -p`, `--output-format json`) + a
  `FakeProvider`; the driver depends on the **seam**, never the CLI directly (harness-agnostic + unit-testable).
- **the orchestrator runs the gate itself** via a `run_gate(repo)` seam (real subprocess + `FakeGate`); the gate
  command list is **read from the target repo** (`.minions/minions.toml`), not hardcoded.
- **the active change is read from disk** — the coder resolves `openspec/changes/<change-id>/` in-tree and builds its
  `tasks.md` phase by phase; findings + spec state are read from disk, never trusted from a role's claim.
- **the driver is deterministic control flow** — no LLM; **advance is *detected*** (a new commit landed **and**
  the phase checkbox moved), not trusted; a halt writes a disk contract the next run resumes from.
- roles are defined by a **prompt + a disk I/O contract** — each role prompt (`prompts/`) is the first-class
  authority for what that instance does.

---

## Guardrails (invariants — hold for every role)

- **Never commit `.env` or any secret** (the vault path, any API key). `.env` is gitignored; keep the vault path
  and secrets there only. The committed `CLAUDE.md` / `.env.example` stay path-free.
- **Deps minimal + human-gated.** Any new dependency (`uv add`) — argue for it and **wait for approval** before
  installing. Test/lint/type tools stay dev-only; keep the runtime lean.
- **No LLM in the orchestration layer; the orchestrator owns the objective checks.** The driver stays
  deterministic and testable; the gate + git state are run by the orchestrator (not the agent it drives) so they
  can't be gamed.
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git (+ the folded
  `openspec/specs/`) — never from memory. Resume is therefore free.
- **Findings stay in the vault; progress + specs stay in the repo.** The read-only roles write only their vault
  findings file; the coder writes code + `tasks.md` + the change's spec delta, and a `Change:` trailer on every
  commit. Keep the vault narrative (`log.md` newest-first, `overview.md`, `backlog.md`) accurate — a fresh
  session relies on it.
