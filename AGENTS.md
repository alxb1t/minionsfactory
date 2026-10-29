# minions_factory — shared context for coding agents

MinionsFactory is **disciplined feature development with coding agents, shipped as skills**: each station of the
line is an `mf-*` skill, and a person conducts them. The project is built the way it builds. The map of the
record is [`docs/README.md`](docs/README.md).

> **This file is shared, role-independent context — what is *true* of this repo, not a script.** What you *do*
> comes from the prompt or task you were given: author a change, build a phase, review the branch diff, run a
> security pass, apply fixes. Where your prompt conflicts with this file, **the prompt wins**; infer no workflow
> from this file alone.

## The record

**Before work, read [the principles](docs/principles.md), [the decisions in force](docs/decisions.md),
[the coding standards](CODING_STANDARDS.md) and [the contribution guide](CONTRIBUTING.md): mandatory shared
context.**

- **A patch** (`vX.Y.Z`) fixes what the line already does — backlog cards, a rule that misstates the behaviour, a
  defect. It adds no station, parameter, decision or requirement, and may modify a requirement to correct it.

## The quality gate — `make gate`

**`make gate`**, at the repository root, checks in order: the lock is in sync · format · lint (`D` docstrings and
`ANN` annotations enabled) · strict types · the tests. The `Makefile` recipe is the only list of the commands; the
skills and CI (`.github/workflows/ci.yml`) run `make gate`, and no prose copies them.

## Layout — where things live here

- **`skills/`** — the `mf-*` skills, one `SKILL.md` each: plan, bootstrap, cut, build, converge, release,
  `mf-integrate`, which merges a moved base into the next version, and `mf-ship`, which takes cut versions to the
  default branch unattended. Tracked here and installed by symlink (`make install-skills`).
- **`docs/`** — the map, the principles, the decisions.
- **`openspec/`** — the living specs and the changes. The OpenSpec CLI is operator tooling, recorded and not
  pinned: `@fission-ai/openspec@1.11.0`, installed globally and resolved on `PATH`, and out of the gate, per D8.
- **`.minions/`** — run artefacts, **gitignored**; nothing in it is tracked. It holds `backlog.md`, where
  `mf-converge` keeps the deferred work: the only copy, one heading per change.
- **`metrics/`** — MF's metrics: `catalogue.toml` declares what is measured, and `changes/` holds the data file
  each release records, per D43.
- **`scripts/metrics/`** — the metric scripts the catalogue names. `uv` runs them and the bundled collector,
  `skills/mf-build/scripts/metrics.py`, as it runs the gate.
- **`tests/`** — the suite.
- **Project inputs and outputs stay inside the repository**, per the principle *The repo reaches nothing outside
  itself*.
- **Execution follows the host**, per D11 and D40; provider setup is the operator's, per D22.

## Workspaces

Where `mf-cut-change` puts a version's branch, per
[D44](docs/decisions.md#d44--versions-run-side-by-side-in-worktrees-one-primary-merges-them).

- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`, relative to the primary checkout.
- **Workspace setup:** none — the gate's first step is `uv sync --locked`.

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — `.env`, an API key; the
  **operator's home or vault path**, or **this repository's own root** transcribed out of a `.minions/` artefact
  or a planning tool's output into tracked prose. Planning writes into the *tracked* `openspec/` tree and its tools
  echo absolute paths, so a real path is one careless paste from history. A path a fixture or a worked example
  *constructs* — a fictional home, a `tmp_path` expression in a test — is not the target; a rendered one, carrying
  a real username, is. `.env` is gitignored; `AGENTS.md` stays path-free. `tests/test_guardrails.py` fails on a
  home path or a key shape in any tracked file.
- **Dependencies are minimal and human-gated.** Argue for any new one (`uv add`) and **wait for approval** before
  installing. Test, lint and type tools stay dev-only; the runtime stays lean.
