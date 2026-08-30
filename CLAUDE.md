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
how a change is cut here, its guardrails, its layout.

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

The change's **`design.md`** is authoritative, with this file behind it — read it. It *is* the decision record:
the reasoning that settled a change, and the measurement behind each decision, are written there and nowhere
else. In brief, the load-bearing seams are:

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

## How a change is cut here

The method is `docs/sdd.md`'s and is not restated here; what follows is the mechanics — which commands, against
which tooling. Planning runs **in this repository**, and the four artifacts are the record.

1. **Settle the decisions first.** A change is cut from decisions that have been argued against a person, not from
   a first draft. The verdict that comes out of it — `feasible` / `feasible-with-caveats` / `needs-precursor` /
   `infeasible-as-specified` — is recorded in the change's `design.md`.
2. **Scaffold** — `openspec new change <NN-slug>`. It creates the change directory and the artifact skeletons.
3. **Author the four artifacts** against `openspec instructions <artifact> --change <NN-slug>`, which emits that
   artifact's structure together with this repo's overrides from `openspec/config.yaml`. `proposal.md` additionally
   opens with `version: vX.Y` frontmatter — **this repo's reader requires it and the CLI neither emits nor checks
   it**, so it is on the author.
4. **A change that changes no requirement** declares the absence rather than inventing one: `skip_specs: true` in
   the change's tracked `.openspec.yaml`, plus `specs/.gitkeep` so the directory stays tracked. The two are
   mutually exclusive — a spec file under `specs/` alongside `skip_specs` fails validation.
5. **Finish on a green check** — `openspec validate <NN-slug> --strict`.

The tooling is **operator tooling, recorded and not pinned**: `@fission-ai/openspec@1.11.0`, installed globally and
resolved on `PATH`. It is deliberately **not** in the gate array — nothing in CI runs it, so a moving version can
never turn CI red; it can only hand a future author different authoring instructions. This repository's own
`uv run python -m orchestrator specs check --strict` remains the binding authority, and it *is* in the gate.

---

## Layout — where things live here

- **`orchestrator/`** — the driver, the seams, the CLI. **`prompts/`** — the six role prompts. **`tests/`** — the
  suite. **`docs/`** — the orchestrator's own map, plus `sdd.md`, the one page there that is about the *method*
  rather than about this codebase.
- **`openspec/`** — the living specs and the changes (shape and contract: `docs/sdd.md`).
- **`.minions/`** — run artefacts, **gitignored**; `minions.toml`, the gate command list, is the one tracked file
  in it.
- **Everything a run reads or writes is inside the repository.** The orchestrator resolves **no path outside the
  target repo**. Product intent — the research and the narrative record the human keeps — lives *upstream* of the
  code in a private Obsidian vault, and **no role the orchestrator spawns reaches into it**; planning itself runs
  here, in the repository, and lands in the change's four artifacts. `.env` is gitignored local scaffolding
  declaring nothing the orchestrator needs, and the committed `CLAUDE.md` / `.env.example` stay path-free.

---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — `.env` itself, an API
  key; the **operator's home or vault path**, or **this repository's own root** transcribed out of a `.minions/`
  artefact or a planning tool's output into tracked prose. Planning runs in the repository and writes into the
  *tracked* `openspec/` tree, and those tools echo absolute paths, so a real path is one careless paste away from
  history. Paths a fixture or a worked example
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
