---
type: teardown
repo: isekai
head: bbe69240bcd0531d7adc7e18ec3d24866166fec6
profile: python-uv
round: 1
criteria_total: 19
open_gaps: 8
open_blocking: 4
open_required: 4
verdict: gaps-found
---

# isekai — MinionsFactory compliance (mf-teardown, round 1)

## Summary

isekai **cannot be run by the orchestrator as it stands** — four `blocking` gaps. The gate config exists and is
well-formed but sits at the repo **root** rather than `.minions/minions.toml`, where the orchestrator is the only
thing that looks; there is **no `openspec/` tree at all**, so neither the living spec nor the change contract the
driver reads exists; and the root `CLAUDE.md` still instructs a cold agent to read the retired vault
`implementation_plans/` model that v0.5 deleted. Four `required` gaps follow behind them.

Profile `python-uv` matched (`pyproject.toml` tracked, `uv.lock` tracked). **`criteria_total: 19` — 23 − 4 not
measured** (see below).

The good news is that most of it is misplacement rather than absence: the gate array is genuinely well-formed —
it *leads* with `uv sync --locked`, which minionsfactory's own does not — and moving one file makes four
withheld criteria measurable.

## Not measured

`.minions/minions.toml` is absent — the array lives in a root `minions.toml` — so every criterion whose subject
**is** the gate array is withheld rather than failed. Measuring the content of a file the orchestrator cannot
read would report gaps that evaporate the moment the file moves. Each is excluded from `open_gaps` and from
`criteria_total`:

- `gate:covers-axes` — gated by `wiring:gate-config`
- `gate:contract-agrees` — gated by `wiring:gate-config`
- `sdd:checker-in-gate` — gated by `wiring:gate-config`
- `py:gate-commands` — gated by `wiring:gate-config`

They are not silently passing: the gap that gates them is itself `blocking`, so this repo cannot read `compliant`
on their account.

## Gaps

### `wiring:gate-config` · blocking · open
- **Evidence:** `.minions/` does not exist. The gate config is at the repo root as `minions.toml`, tracked, and
  declares a non-empty 5-entry `gate` array — but the orchestrator reads only `.minions/minions.toml`, so the
  array is unreadable to it where it currently sits.
- **Fix:** `git mv minions.toml .minions/minions.toml` and commit — the orchestrator reads that path and no
  other. This one move also un-gates the four criteria listed under *Not measured*.

### `wiring:claude-md` · blocking · open
- **Evidence:** root `CLAUDE.md` exists and its (M) layer is clean — no unfilled `{{placeholder}}`, no absolute
  vault path. Its **(J)** layer fails: `CLAUDE.md:15-38` is built on the retired model. Line 24 instructs *"Read
  the latest implementation plan in `$VAULT_PROJECT_DIR/implementation_plans/` — the
  `vX.Y_implementation_plan.md` with the highest version number"*, and lines 28–31 place progress in that plan's
  Progress ledger plus `overview.md`'s `current_phase` frontmatter. The file mentions `openspec` zero times and
  gives no account of the in-tree change contract.
- **Fix:** restamp from the reconciled template (`notes/generic_root_claude.md`, rewritten in v0.6) and fill the
  placeholders — it now points a cold agent at the active change's `tasks.md` `## Progress` checklist.

### `sdd:specs-tree` · blocking · open
- **Evidence:** no `openspec/` directory anywhere in the repo — `find . -maxdepth 3 -type d -name openspec`
  returns nothing and `git ls-files` records no path under it. No `<capability>/spec.md` exists.
- **Fix:** create `openspec/specs/<capability>/spec.md` describing behaviour the repo already has; the eight test
  modules under `tests/` are the natural starting material.

### `sdd:changes-tree` · blocking · open
- **Evidence:** the same absence — `openspec/changes/` does not exist, so neither does `openspec/changes/archive/`.
- **Fix:** create `openspec/changes/archive/` and author the first change; until one exists the driver has no
  work to read and refuses at preflight.

### `wiring:gitignore` · required · open
- **Evidence:** `.gitignore` (25 lines) ignores `.env` (line 2, confirmed by `git check-ignore -v .env`) and does
  not ignore the lockfile (`git check-ignore uv.lock` exits 1) — but it carries **no** `.minions/*` line and no
  `!.minions/minions.toml` negation; the string `.minions` does not appear in it.
- **Fix:** add `.minions/*` with the `!.minions/minions.toml` negation, so per-run artifacts stay out of history
  while the gate config stays tracked. Pairs with the `wiring:gate-config` move.

### `gate:make-mirrors` · required · open
- **Evidence:** no `Makefile` exists — `ls Makefile makefile GNUmakefile` finds none, a case-insensitive `find`
  over the tree matches nothing, and `git ls-files` records no makefile. There is nothing for a human-typed gate
  to mirror the array with.
- **Fix:** add a `Makefile` with a `gate` target running the same commands, in the same order, as the `gate`
  array — so the gate a human types and the gate the orchestrator runs cannot drift apart.

### `py:pinned-runtime` · required · open
- **Evidence:** no `.python-version` at the repo root — absent from disk and from `git ls-files`.
  `pyproject.toml:4` pins only the range `requires-python = ">=3.12"`, so no concrete interpreter is fixed.
- **Fix:** write the concrete pin into `.python-version` and commit it, so every machine and CI resolve the same
  interpreter.

### `py:lint-select` · required · open
- **Evidence:** no ruff lint `select` list is declared anywhere. `pyproject.toml` has only `[project]`,
  `[dependency-groups]` and `[tool.pytest.ini_options]` — no `[tool.ruff]` or `[tool.ruff.lint]` table — and no
  `ruff.toml` / `.ruff.toml` exists. `E`, `F` and `I` are therefore not explicitly selected; `I` (import sorting)
  is off entirely and only ruff's default subset of `E` applies.
- **Fix:** add `[tool.ruff.lint] select = ["E", "F", "I"]` at minimum; without it the lint axis passes on code it
  never looked at.

## Passing

- **A · loop wiring — 3/6.** `wiring:git-repo` (HEAD `bbe6924`), `wiring:vault-perms` (the `Read`/`Edit`/`Write`
  globs and the `additionalDirectories` entry both name the vault dir `.env` declares), `wiring:env-example`
  (tracked, same five keys as `.env`, placeholder or empty values only).
- **B · SDD layout — 3/6** (1 withheld). `sdd:active-change-contract`, `sdd:scenario-shape` and
  `sdd:test-binding` pass **vacuously**: the sets they quantify over are empty because the `openspec/` trees do
  not exist, and that single absence is already reported by the two existence criteria above. They become real
  the moment a specs tree lands — `grep -rn "pytest.mark.spec\|spec_exempt" tests` currently returns nothing and
  `pyproject.toml` declares no `markers` key.
- **C · gate quality — 1/4** (2 withheld). `gate:no-gaming` passes: the tool configuration holds no waivers at
  all — no `[tool.ruff]` table, no `per-file-ignores`, `exclude` or severity override, no `ruff.toml` / `ty.toml`,
  and no `noqa` or `type: ignore` anywhere in `isekai/`, `tests/`, `convert.py` or `scripts/`.
- **`python-uv` — 4/7** (1 withheld). `py:manifest`, `py:lockfile` (`uv.lock` tracked),
  `py:dev-deps-isolated` (`dependencies = []`; pytest, ruff and ty all in `[dependency-groups] dev`), and
  `py:import-resolution` — exactly one declared mechanism, `[tool.pytest.ini_options] pythonpath = ["."]`, with
  no `[build-system]` and therefore no editable install competing with it.

**No group D–G criterion was measured or reported.** isekai has no `CHANGELOG.md` and no `docs/`; those belong to
the project-shape groups planned for v0.8, no id in them is live, and reporting one would be a false gap.

## Resolution log

- 2026-08-24 · round 1 · first measurement, no prior report. 8 gaps opened at `open` (4 blocking, 4 required);
  4 criteria withheld under the absent-subject rule, gated by `wiring:gate-config`. `verdict: gaps-found`.
