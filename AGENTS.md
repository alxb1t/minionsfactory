# minions_factory — shared context for coding agents

MinionsFactory is **disciplined feature development with coding agents, shipped as skills**: each station of the
line is an `mf-*` skill, and a person conducts them. The project is built the way it builds. The map of the
record is [`docs/README.md`](docs/README.md).

> **This file is shared, role-independent context — what is *true* of this repo, not a script.** What you *do*
> comes from the prompt or task you were given: author a change, build a phase, check the diff's conformance, run
> an adversarial pass, apply fixes. Where your prompt conflicts with this file, **the prompt wins**; infer no workflow
> from this file alone.

## The record

**Before work, read [the coding standards](CODING_STANDARDS.md) and [the contribution guide](CONTRIBUTING.md):
mandatory shared context. Every station but the cut, the build and the converge conductor also reads
[the principles](docs/principles.md) and [the decisions in force](docs/decisions.md).**

**The cut and the build read the index `skills/mf-converge/scripts/bundle.py --decisions` prints and, in full, the
decisions their work cites or touches; [the principles](docs/principles.md) and [the threat model](THREAT_MODEL.md)
when a task names the file. The converge conductor reads none of it.**

**Converge's conformance worker reads, of the decisions, those its change cites, in full, and an index of all — its
`bundle.md` — in place of the whole page; its adversarial worker reads the threat model.**

- **A patch** (`vX.Y.Z`) fixes what the line already does — debt cards, a rule that misstates the behaviour, a
  defect. It adds no station, parameter, decision or requirement, and may modify a requirement to correct it.

## The quality gate — `make gate`

**`make gate`**, at the repository root, checks in order: the lock is in sync · format · lint (`D` docstrings, `ANN`
annotations, `B` bug patterns and `S` security enabled, and the wider families of `pyproject.toml`) · the
docstring check · the timeout rule of `sg-rules/` · strict types · the CI workflow's lint · the secret scan ·
the tests on every core, under coverage, writing the junit report `.minions/test-report.xml` · 100% coverage of the lines changed since `DIFF_BASE`. The `Makefile` recipe
is the only list of the commands; the skills and CI (`.github/workflows/ci.yml`) run `make gate`, and no prose copies
them. **`make check`** runs its fast steps, no `slow` test, between build phases. **`make corpus`** runs the readers of
run data over this checkout's run directory and Codex sessions; no gate runs it.

The secret scan is Betterleaks, operator tooling per D52: `betterleaks 1.9.0`, resolved on `PATH`, its allowlist in
`.betterleaks.toml`, which names each path `.gitignore` names: the scan reads what git can track.

## Layout — where things live here

- **`skills/`** — the `mf-*` skills, one `SKILL.md` each: plan, bootstrap, cut, build, converge, release,
  `mf-integrate`, which merges a moved base into the next version, `mf-ship`, which takes cut versions to the
  default branch unattended, `mf-rescue`, which `mf-ship` runs on a halted version to amend its plan or diagnose the
  halt, `mf-supervise`, which `mf-ship` runs under a version's switch when its rescue diagnosed or was spent, and
  `mf-simplify`, which the build runs to close a change. Tracked here;
  `make install-skills` pins one exported release per machine, both hosts linked to it, per D55.
- **`docs/`** — the map, the principles, the decisions.
- **`openspec/`** — the living specs and the changes. The OpenSpec CLI is operator tooling, recorded and not
  pinned: `@fission-ai/openspec@1.11.0`, installed globally and resolved on `PATH`, and out of the gate, per D8.
- **`.minions/`** — run artefacts, **gitignored**; nothing in it is tracked. It holds `debt.md`, where
  `mf-converge` keeps the deferred work: the only copy, one heading per change; and `changes/<change-id>/`, everything
  about one change — its findings, status log, marks and worker logs — per D57.
- **`metrics/`** — MF's metrics: `catalogue.toml` declares what is measured, and `changes/` holds the data file
  each release records, per D43.
- **`scripts/metrics/`** — the metric scripts the catalogue names. `uv` runs them and the bundled collector,
  `skills/mf-build/scripts/metrics.py`, as it runs the gate.
- **`tests/`** — the suite.
- **Project inputs and outputs stay inside the repository**, per the principle *The repo reaches nothing outside
  itself*.
- **Workers follow the host, or the models file's `executor`**, per D40; **every station runs MF's own method**, per D11; provider setup is the
  operator's, per D22.

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
  home path in any tracked file, and the gate's secret scan on a key.
- **Dependencies are minimal and human-gated.** Argue for any new one (`uv add`) and **wait for approval** before
  installing. Test, lint and type tools stay dev-only; the runtime stays lean.
