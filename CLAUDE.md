# minions_factory — shared context for Claude Code

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**. Pointed
at a target repo, it drives an **in-repo change** to completion, spawning a **fresh, single-role Claude Code
instance** per role and **advancing or halting** on machine-checkable disk state. The project **dogfoods what it
automates** — it is built the way it builds.

**The method it automates is stated once, in [`docs/sdd.md`](docs/sdd.md)** — the change contract and the
`Change:` trailer, the traceability bindings and the version line, the gate rules, the loop, the findings
contract and the release fold; and, in its Part II, what must be settled before a change is cut and the
readiness checklist for a repository. That page is authoritative for *how the work is done*, and this file does
not restate it. What follows is what is true of **this repository in particular**: its gate commands, its seams,
its guardrails, its layout.

Hard constraints that shape the code here: **no LLM sits in the orchestration layer** (the driver is
deterministic, unit-testable control flow); **the orchestrator runs the objective checks itself** (the gate + git
state — so the agent it drives can't game them); and **roles are fresh instances behind a provider seam**
(harness-agnostic — Claude Code is the default adapter, with no dependency on a harness's internals).

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (author a change, build a phase, review the
> branch diff, run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.**
> Read this for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## The quality gate — this repo's six commands

**These** are the commands this repo declares, in `.minions/minions.toml`'s `gate` array, in order:

- `uv sync --locked` — locked lock-sync. Environment setup rather than a quality axis, so it is the step it is
  and the four axes follow.
- `uv run ruff format --check .` + `uv run ruff check .` — format + lint clean (`D` docstrings + `ANN`
  annotations enabled).
- `uv run ty check` — strict type-check clean.
- `uv run pytest -q` — all tests pass.
- `uv run python -m orchestrator specs check --strict` — the spec binding holds. Note the form: this repo runs
  **from source**, like the existing `run` command. There is **no installed `minions` binary yet**;
  `minions specs check` is only the future installed alias.

`Makefile`'s `gate` target, `README.md` and CI (`.github/workflows/ci.yml`) mirror that array; the array is the
one the orchestrator runs.

External effects are faked in tests behind this repo's two seams — the **provider** (`claude -p`) behind the
`Provider` Protocol (`FakeProvider`) and the **gate subprocess** behind the gate seam (`FakeGate`); real
`claude -p` is exercised only in an end-to-end dogfood run.

---

## Engineering conventions

The change's **`design.md`** is authoritative, with this file behind it — read it. (The human keeps a longer
decision record upstream in the vault; it is the *human's*, not an input any role reads.) In brief, the
load-bearing seams are:

- a **`Provider` Protocol** — a real `ClaudeCodeProvider` (`claude -p`, `--output-format json`) + a
  `FakeProvider`; the driver depends on the **seam**, never the CLI directly (harness-agnostic + unit-testable).
- **the orchestrator runs the gate itself** via a `run_gate(repo)` seam (real subprocess + `FakeGate`); the gate
  command list is **read from the target repo** (`.minions/minions.toml`), not hardcoded, so a non-Python target
  needs no code change.
- **the change is read from disk** — the coder resolves `openspec/changes/<change-id>/` in-tree; findings + spec
  state are likewise read from disk, never trusted from a role's claim.
- **the driver is deterministic control flow** — no LLM; **advance is *detected*** on disk, never trusted from a
  role's report (what counts as an advance is the method's, `docs/sdd.md`); a halt writes a disk contract the
  next run resumes from.
- roles are defined by a **prompt + a disk I/O contract** — each role prompt (`prompts/`) is the first-class
  authority for what that instance does.

---

## Layout — where things live here

- **`orchestrator/`** — the driver, the seams, the CLI. **`prompts/`** — the six role prompts. **`tests/`** — the
  suite. **`docs/`** — the orchestrator's own map, plus `sdd.md`, the one page there that is about the *method*
  rather than about this codebase.
- **`openspec/`** — the living specs and the changes (shape and contract: `docs/sdd.md`).
- **`.minions/`** — run artefacts, **gitignored**; `minions.toml`, the gate command list, is the one tracked file
  in it.
- **Everything a run reads or writes is inside the repository.** The orchestrator resolves **no path outside the
  target repo**. Product intent lives *upstream* of the code, in a private Obsidian vault the human keeps — the
  planning docs, research, the narrative record — and **no role the orchestrator spawns reaches into it**. Any
  PM-side tooling runs from the vault, out of band, resolving the repo it targets from there: **the vault reaches
  the repo; the repo never reaches the vault.** `.env` is gitignored local scaffolding declaring nothing the
  orchestrator needs, and the committed `CLAUDE.md` / `.env.example` stay path-free.

---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — `.env` itself, an API
  key; the **operator's home or vault path** (PM-side tooling runs from the vault and writes into this repo's
  *tracked* `openspec/` tree, so that path is one careless paste away from history), or **this repository's own
  root** transcribed out of a `.minions/` artefact into tracked prose. Paths a fixture or a worked example
  *constructs* — a fictional home, a `tmp_path` expression in a test — are not the target of this rule; a rendered
  one, carrying a real username, is. `.env` is gitignored; the committed `CLAUDE.md` / `.env.example` stay
  path-free.
- **Deps minimal + human-gated.** Any new dependency (`uv add`) — argue for it and **wait for approval** before
  installing. Test/lint/type tools stay dev-only; keep the runtime lean.
- **No LLM in the orchestration layer; the orchestrator owns the objective checks.** The driver stays
  deterministic and testable; the gate + git state are run by the orchestrator (not the agent it drives) so they
  can't be gamed.
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git — never from
  memory.
