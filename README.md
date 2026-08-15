# MinionsFactory

A **CLI + orchestrator for autonomous Python feature development with Claude Code.** Pointed at a target
repo, it drives a **vault-backed implementation plan** to completion: a coder builds the plan phase by
phase, the **orchestrator runs the target's quality gate itself** and, on green, the phase advances and
commits; otherwise the run **halts** with a readable reason.

The design rests on four invariants:

- **No LLM in the orchestration layer** — the driver is deterministic, unit-tested Python control flow.
- **The orchestrator runs the objective checks itself** (gate + git state), so the agent it drives can't
  game them.
- **All state lives on disk** — a run resumes from the plan's `current_phase` + git, never from memory.
- **Roles are fresh instances behind a provider seam** — harness-agnostic; Claude Code (`claude -p`) is the
  default adapter.

## Status

**v0.1 — the "loop spine" (in progress).** This version builds the minimal warm-coder build spine
(spawn coder → gate → advance/commit or halt → resume), with all control flow unit-tested behind a fake
provider + fake gate. The end-of-plan review ‖ security ‖ simplify fan-out, the converge loop, release
automation, the installed CLI, extra provider adapters, and the UI are **≥ v0.2**.

Designed for **personal, local use** under a Claude Code subscription (headless `claude -p`).

## Usage (run-from-source)

```bash
uv sync
python -m orchestrator run --repo /path/to/target-repo
```

The **target repo** it drives must provide:

- a **`.env`** with `VAULT_PROJECT_DIR` — the path to its plan vault (an Obsidian folder holding the
  versioned `implementation_plans/`), and
- a **`minions.toml`** at its root — the ordered gate command list, e.g.:

  ```toml
  gate = [
    "uv sync --locked",
    "uv run ruff format --check .",
    "uv run ruff check .",
    "uv run ty check",
    "uv run pytest",
  ]
  ```

The orchestrator resolves the highest-version plan from the vault, drives it phase by phase, and exits
`0` on completion / `1` on a halt.

## The quality gate (this repo's own)

MinionsFactory dogfoods the discipline it enforces. Its own gate:

```bash
uv run ruff format --check .   # format
uv run ruff check .            # lint (D docstrings + ANN annotations)
uv run ty check                # strict type-check
uv run pytest                  # tests
```

CI (`.github/workflows/ci.yml`) mirrors it on every push.

## Docs

Developer docs live in [`docs/`](docs/): [architecture](docs/architecture.md) (invariants + component
graph), [data & control flow](docs/data-flow.md) (sequence/flow diagrams), and a per-package
[API reference](docs/modules/orchestrator.md). See [`CHANGELOG.md`](CHANGELOG.md) for what's shipped.
