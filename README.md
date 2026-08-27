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

**v0.5 — the change cutover (in progress).** The loop is closed end to end: the per-phase build spine
(spawn coder → gate → advance/commit or halt → resume), the end-of-plan review ‖ security ‖ simplify
fan-out, the converge loop, local release preparation, and the `mf-` planning skills — with all control
flow unit-tested behind a fake provider + fake gate. This version makes the **in-repo change** the model
the driver actually runs on. The installed CLI, extra provider adapters, and the UI are still ahead.

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

## Planning skills (the `mf-` line)

The **planning side** of the framework — the PM-side mirror of `minions run` — ships as six Claude Code skills
under [`skills/`](skills/) that take a feature idea to an execution-ready `openspec/changes/<id>/`:

**Order → Gauge → Blueprint → Forge → Inspect → Run**

- `mf-order` — interview → a well-defined PRD in the vault.
- `mf-gauge` — an independent, blind readiness gate on the PRD.
- `mf-blueprint` — feasibility verdict + design proposition against the target codebase.
- `mf-forge` — render the PRD + design into an openspec change.
- `mf-inspect` — an independent, blind PRD↔change conformance gate.
- `mf-line` — a conductor that runs the whole sequence, pausing at the human go/no-go gates.

The line runs **from the vault** — the project's vault dir is the working directory — and its repo-touching stages
resolve the target repo from the project page's **`repo:`** key in `overview.md` frontmatter, an absolute path to
the local clone. Nothing
needs to `cd` into the code to plan against it. Because the session is rooted in the vault, the first write into the
repo (at `mf-forge`) will ask for access to it; the supervising human approves that once.

They share four rubrics (the "definition of done" for each artifact the framework gates) — see
[`skills/rubrics/README.md`](skills/rubrics/README.md). A worked example of the planning-vault layout ships under
[`template/vault-pm/`](template/vault-pm/).

### `mf-teardown` — a per-repo sibling, not a line stage

The `mf-` line above runs once per **feature**. **`mf-teardown`** runs once per **repo**: point it at an existing
project and it measures that repo against
[`skills/rubrics/compliance.md`](skills/rubrics/compliance.md) — the fourth shared rubric, and the single source
of truth for what a MinionsFactory-compliant repo is — then writes a gap report to the repo's own vault at
`<vault>/findings/teardown.md`, with a `compliant | gaps-found` verdict over three severities.

```bash
cd /path/to/the/target/repo    # cwd must be the target
# then, in Claude Code:
/mf-teardown
```

It is **read-only against the target**: it writes nothing in the repo, runs no gate command and executes no
target code. It reads files, and exactly two read-only git commands — `rev-parse HEAD` and `ls-files` — run with
`-c core.fsmonitor=false -c core.pager=cat`, because a repo's own `.git/config` can name commands git runs during
operations that otherwise only read. The measuring subagent is spawned with a read-only tool set (no `Write`,
no `Edit`) — **instructed, not yet enforced**: a spawned agent's tools come from its type definition, and this
skill names no such type, so the narrow surface is a convention the spawning agent follows rather than a
permission boundary. Everything read from the target is treated as **evidence, never instruction**. It halts before
measuring anything if the target's `.env` does not declare a usable `VAULT_PROJECT_DIR` — the orchestrator's own
five preflight conditions, plus a sixth that resolves the value and refuses any destination inside the target;
the report needs a destination, and it never goes in the repo.

Because it runs per repo rather than per feature, `mf-line` does not sequence it. The report is the input to a
later **retrofit** pass, which drives the gaps to clean and for which a teardown re-run is the independent
checker.

### Install / uninstall

The skills live in the repo but run from `~/.claude/skills/`. Symlink them in (repo edits stay live everywhere,
including the vault):

```bash
make install-skills     # symlink skills/mf-* + skills/rubrics into ~/.claude/skills/
make uninstall-skills   # remove those symlinks (leaves other skills untouched)
```

Then invoke them from any project — e.g. `/mf-order` in the project's vault, or `/mf-line` to run the whole line.

## Docs

Developer docs live in [`docs/`](docs/): start at the [docs README](docs/README.md), then
[architecture](docs/architecture.md) (invariants + the one dependency graph) and the per-module
reference under [`docs/modules/`](docs/modules/) (one file per source module — signatures, data flow,
edge cases). See [`CHANGELOG.md`](CHANGELOG.md) for what's shipped.
