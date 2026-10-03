# minions_factory — shared context for Claude Code

MinionsFactory is **disciplined feature development with Claude Code, shipped as skills**: each station of the
line is an `mf-*` skill, and a person conducts them. The project is built the way it builds. The map of the
record is [`docs/README.md`](docs/README.md).

## The record

The rules every station follows, imported here so they are in context when a line is written:

@docs/principles.md

- **The decisions in force** are in [`docs/decisions.md`](docs/decisions.md), each with its reason. A change that
  adds or overturns a decision in force edits `docs/decisions.md` in one of its phases; its `design.md` keeps the
  history.
- **Docs are written to `mf-build`'s prose rules** `P1`…`P13`: terse, answer first, things named rather than
  counted.
- **A change is cut** with the `mf-cut-change` skill.

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (author a change, build a phase, review the
> branch diff, run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.**
> Read this for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## The quality gate — `make gate`

The gate is **`make gate`**, run at the repository root. It checks, in order: the lock is in sync · format ·
lint (`D` docstrings + `ANN` annotations enabled) · strict types · the tests. The `Makefile`
recipe is this repo's only list of the commands; the skills and CI (`.github/workflows/ci.yml`) run `make gate`,
and no prose here copies them.

---

## Layout — where things live here

- **`skills/`** — the `mf-*` skills, one `SKILL.md` each: cut, build, converge, release. Tracked here and
  installed by symlink (`make install-skills`).
- **`docs/`** — the map, the principles, the decisions, the autonomous design; and the deprecated runner's pages.
- **`openspec/`** — the living specs and the changes. The OpenSpec CLI is **operator tooling, recorded and not
  pinned**: `@fission-ai/openspec@1.11.0`, installed globally and resolved on `PATH`. It is deliberately **not** in
  the gate — nothing in CI runs it, so a moving version can never turn CI red; it can only hand a future author
  different authoring instructions.
- **`.minions/`** — run artefacts, **gitignored**; nothing in it is tracked. It holds `backlog.md`, where
  `mf-converge` keeps the deferred work: the only copy, one heading per change.
- **`tests/`** — the suite.
- **Everything a station reads or writes is inside the repository.**

---

## The deprecated runner

`orchestrator/` and `prompts/` hold a deterministic runner for the same line, with its tests. External effects
are faked behind its seams: the **provider** (`claude -p`) behind the `Provider` Protocol (`FakeProvider`), and
the **gate subprocess** behind the gate seam (`FakeGate`). The runner is not extended, and is deleted by the change
that retires it.

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
