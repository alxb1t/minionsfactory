---
version: v0.11
---

# 0011-cut-and-gate — proposal

**In one line:** a new skill, `mf-cut-change`, writes changes that `mf-build` can run without guessing, and
every skill runs the gate as `make gate`.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | every decision (`D1`…), the input contract (`I1`…), the evidence |
| [tasks.md](tasks.md) | the build: 4 phases, one commit each |
| [specs/sdd/spec.md](specs/sdd/spec.md) | 2 new requirements, each held by a test |

## Why

Real projects trip over two things.

**1. A fresh cut is often not ready for `mf-build`.** The agent that cuts never reads `mf-build`. So it writes
tasks the builder must halt on, or tasks that copy steps the builder owns. Every isekai cut from `0019` to
`0025` needed a fix before or during its build ([evidence](design.md#evidence)).

**2. The gate lives in two places.** The skills read `.minions/minions.toml`; people and CI run `make gate`.
The copies drift. KitchenScheduler's toml cannot run at all: its npm steps need `cd frontend`, and a toml array
has no way to say it.

## What Changes

```
  grilling ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
  (as is)        NEW: writes      checks its    runs           simpler: no
                 to the input     input         make gate      separate
                 contract         contract                     binding step
                      │               ▲
                      └── I1 … I15 ───┘   one list, owned by mf-build
```

- **New skill `mf-cut-change`.** It cuts a change from the grilling — the conversation, or a brief file. It
  creates the version branch, writes the four artifacts with the OpenSpec CLI, checks them against the input
  contract, shows you, and commits on your OK. See [D8](design.md#d8)–[D13](design.md#d13).
- **`mf-build` gets an input contract** — `I1`…`I15`, what a change must give it. It checks the mechanical
  items itself, halts before a **HUMAN** phase, halts on a failed **HALT CHECK**, ticks `N.M` boxes, adds a
  dependency that `design.md` approved, and writes short CHANGELOG entries. See [D5](design.md#d5)–[D7](design.md#d7).
- **The skills run `make gate`.** `mf-build`, `mf-converge` and `mf-release` stop reading the toml, and print
  `make -n gate` before the first run. **BREAKING** for a target repo with no `gate` target in a root
  `Makefile`: the skills now halt there. See [D1](design.md#d1)–[D3](design.md#d3).
- **`mf-release` gets simpler.** No separate spec-binding step. The full gate runs before the commit, and a
  repo's binding check, if it has one, runs inside it. See [D4](design.md#d4).
- **This repo keeps one list of gate commands** — the `Makefile` recipe. CI runs `make gate`. `CLAUDE.md`,
  `README.md` and `docs/sdd.md` name `make gate` instead of copying commands. See [D2](design.md#d2).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: two ADDED requirements.

| requirement | what changes |
|---|---|
| The skills run the repository's `make gate` | new: no skill names the toml, and the three gate-running skills name `make gate` |
| The cut and the build share one input contract | new: the `I` ids in `mf-build` and in `mf-cut-change` are the same set |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-build/SKILL.md` · `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` · new `skills/mf-cut-change/SKILL.md` |
| tests | new `tests/test_skills.py` |
| docs | `CLAUDE.md` · `README.md` · `docs/sdd.md` · `docs/architecture.md` |
| config | `.github/workflows/ci.yml` · `Makefile` (comment only) · `.minions/minions.toml` (comment only) · `openspec/config.yaml` |
| dependencies | none |
| target repos | each needs a root `Makefile` with a `gate` target — all five known targets have one ([evidence](design.md#evidence)) |

## Not in this change

- **The parked runner.** `orchestrator/` keeps reading the toml ([D3](design.md#d3)).
- **Target repos.** Deleting their toml and their `CLAUDE.md` cut section is each repo's own follow-up, after
  this ships.
- **The old v0.11 rows** — the security engine, R7, run events. They moved to the roadmap's *Later*.
- **A verification skill** — docs ↔ code, architecture ↔ code, spec binding. A later feature.
- **Backlog items not named in [D14](design.md#d14)** — including the two `sdd` items on `docs/sdd.md`, which
  this change opens for its gate text only.
