# MinionsFactory

A **CLI + orchestrator for autonomous Python feature development with Claude Code.** Pointed at a target
repo, it drives an **in-repo change** to completion: a coder builds the change's `tasks.md` phase by
phase, the **orchestrator runs the target's quality gate itself** and, on green, the phase advances and
commits; otherwise the run **halts** with a readable reason.

The design rests on four invariants:

- **No LLM in the orchestration layer** — the driver is deterministic, unit-tested Python control flow.
- **The orchestrator runs the objective checks itself** (gate + git state), so the agent it drives can't
  game them.
- **All state lives on disk** — a run resumes from the change's `tasks.md` progress + git, never from memory.
- **Roles are fresh instances behind a provider seam** — harness-agnostic; Claude Code (`claude -p`) is the
  default adapter.

## Status

**v0.7.0 is the current release; work on the v0.8 line is in progress.** The loop is closed end to end: the
per-phase build spine (spawn coder → gate → advance/commit or halt → resume), the end-of-plan review ‖
security ‖ simplify fan-out, the converge loop, and local release preparation — with all control flow
unit-tested behind a fake provider + fake gate. The **in-repo change** is the model the driver runs on, and
everything a run declares, resolves or writes lands inside the target repository. The installed CLI, extra
provider adapters, and the UI are still ahead.

Designed for **personal, local use** under a Claude Code subscription (headless `claude -p`).

## Usage (run-from-source)

```bash
uv sync
python -m orchestrator run --repo /path/to/target-repo
```

The **target repo** it drives must provide:

- an **`openspec/changes/<id>/`** change — `proposal.md` (with leading `version: vX.Y` frontmatter),
  `design.md`, `tasks.md` (a `## Progress` checklist — the driver's phase pointer) and a `specs/` delta, and
- a **`.minions/minions.toml`** — the ordered gate command list, e.g.:

  ```toml
  gate = [
    "uv sync --locked",
    "uv run ruff format --check .",
    "uv run ruff check .",
    "uv run ty check",
    "uv run pytest",
  ]
  ```

  (git-ignore the generated `.minions/` artifacts but keep the config: `.minions/*` + `!.minions/minions.toml`.)

That is the whole contract — **nothing outside the repo is declared, resolved or written.** Everything a run
produces lands under the gitignored `.minions/`: each role's findings at
`.minions/findings/<change-id>_<role>.md`, the coder's halt report at `.minions/HALT.md`, deferred work at
`.minions/<version>_backlog.md` (any list line there blocks the release; a missing file means nothing was
deferred), and the run's `events.jsonl` + `status.json`.

The orchestrator runs a zero-token **preflight** first — the active change is well-formed and declares its
version — then resolves the active change in the target repo, drives its phases one fresh coder at a time, and
exits `0` on completion / `1` on a halt. Every refusal is a diagnostic and a non-zero exit, never a traceback.

## The quality gate (this repo's own)

MinionsFactory dogfoods the discipline it enforces. Its own gate:

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
uv run python -m orchestrator specs check --strict
```

Lock sync · format · lint (`D` docstrings + `ANN` annotations) · strict type-check · tests · the spec-binding
checker. The list above is `.minions/minions.toml`'s `gate` array **verbatim**, and `make gate` runs the same six
in the same order — the orchestrator runs the array, so a paraphrase here would be a gate the repo does not
actually run.

CI (`.github/workflows/ci.yml`) mirrors it on every push.

## The method

The discipline behind the loop is stated once, on its own page, so tools can reference it rather than restate
it: [`docs/sdd.md`](docs/sdd.md). Three practices carry it. **Spec-driven changes** — work is defined before it
is built, in the repository, as a written change with machine-checkable acceptance, folding into a living
behavioural spec rather than a document rotting beside the code. **A strict quality gate** — one declared
command list; a unit of work is done when every step is green, not when it looks done. **All state on disk** —
where the work stands is reconstructed from the repository, never from an agent's memory of what it just did,
so resume is free and any stage can be re-run by a fresh reader who was not there.

## Docs

Developer docs live in [`docs/`](docs/): start at the [docs README](docs/README.md), then
[architecture](docs/architecture.md) (invariants + the one dependency graph) and the per-module
reference under [`docs/modules/`](docs/modules/) (one file per source module — signatures, data flow,
edge cases). See [`CHANGELOG.md`](CHANGELOG.md) for what's shipped.
