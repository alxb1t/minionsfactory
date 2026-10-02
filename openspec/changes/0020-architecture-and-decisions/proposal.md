---
version: v0.20
backlog: [0009·sdd-1, 0009·sdd-2, 0012·R3, 0011·R7, someday·dup]
---

# 0020-architecture-and-decisions — proposal

**In one line:** the repository becomes the one record of what MinionsFactory is and why — a map, the principles,
the decisions in force and the autonomous design under `docs/` — and the method page `docs/sdd.md` is deleted.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`E1`…`E13`), what each rewritten file holds, the text each skill sentence becomes |
| [pages/](pages/) | the pages as settled: [principles](pages/principles.md) · [decisions](pages/decisions.md) · [autonomous](pages/autonomous.md) |
| [tasks.md](tasks.md) | the build: the principles, the decisions, the autonomous page, the front door, `A7`, the method page's deletion |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one modified requirement |

## Why

`README.md`, `CLAUDE.md` and `docs/` describe MinionsFactory as a deterministic runner. The runner is deprecated;
what ships is the `mf-*` skills. The reasons behind the skills are written nowhere in this repository, and
`docs/architecture.md` sends its reader to a record the repository cannot reach. `docs/sdd.md` restates what
OpenSpec and the skills already say, and the skills cite it in repositories that do not have it.

## What Changes

```
docs/
├── README.md       REWRITTEN   the map: one diagram, a table of the pages
├── principles.md   NEW         Words · the rules every station follows · what holds each
├── decisions.md    NEW         D1…D35 — the choices in force, each with its reason
├── autonomous.md   NEW         the autonomous line's design — designed, not built
├── sdd.md          DELETED     last
└── architecture.md · modules/  KEPT, bannered deprecated — the runner's
```

- **The record.** `docs/principles.md` and `docs/decisions.md`, from [pages/](pages/). See [E1](design.md#e1),
  [E2](design.md#e2).
- **Written to the prose rules.** Every page follows `mf-build`'s `P1`…`P13`. See [E12](design.md#e12).
- **One check.** A test fails when a principle names a test that does not exist. See [E4](design.md#e4).
- **The autonomous design** enters the repository, marked designed-not-built. See [E5](design.md#e5).
- **The front door.** `README.md`, `CLAUDE.md`, `docs/README.md` and `openspec/config.yaml` describe the skills
  first; the runner is named deprecated. See [E6](design.md#e6), [E7](design.md#e7).
- **`A7`.** `mf-cut-change` gains an artifact rule: a change that adds or overturns a decision in force names
  `docs/decisions.md` in a task. See [E8](design.md#e8).
- **`docs/sdd.md` is deleted.** The skill sentences that cite it state their rule plainly. See
  [E9](design.md#e9), [E10](design.md#e10). A scan keeps its name out afterwards ([E13](design.md#e13)).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the MODIFIED requirement below.

| requirement | what changes |
|---|---|
| Anchored harms block, and drift has its own tier | the last sentence, "`docs/sdd.md` SHALL state the same vocabulary", is removed; the scenario scans `skills/mf-converge/SKILL.md` alone. Its title is kept: OpenSpec refuses a MODIFIED block that drops a scenario title |

## Impact

| area | files |
|---|---|
| docs | `docs/README.md` · `docs/principles.md` · `docs/decisions.md` · `docs/autonomous.md` · `docs/sdd.md` · `docs/architecture.md` · `docs/modules/provider.md` · `docs/modules/state.md` |
| front door | `README.md` · `CLAUDE.md` · `openspec/config.yaml` |
| skills | `skills/mf-cut-change/SKILL.md` · `skills/mf-build/SKILL.md` · `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` |
| tests | `tests/test_principles.py` · `tests/test_conventions.py` · `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change; a repo with a `docs/decisions.md` gets `A7` at its next cut |

## Not in this change

- **The runner.** `orchestrator/`, `prompts/`, `docs/modules/`, the runner's specs and tests stay, apart from the
  banner and the removed pointers of [E6](design.md#e6). Deleting them is its own change.
- **The spec↔test binding and the gate recipe.** Untouched; the binding retires when the runner is deleted.
- **Building the autonomous line.** Only its design enters the repository.
- **More checks on the docs.** No link, table or id check ([E4](design.md#e4)).
- **A scan for `A7`.**
