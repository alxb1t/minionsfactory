---
version: v0.15
---

# 0015-runner-make-gate — proposal

**In one line:** the parked runner runs `make gate` like the skills do, and `.minions/minions.toml` — and its
name — leave the repository.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D7`) and every file the name leaves |
| [tasks.md](tasks.md) | the build: the runner first, then the file and its name |
| [specs/gate/spec.md](specs/gate/spec.md) · [specs/sdd/spec.md](specs/sdd/spec.md) | the gate requirement replaced, and a guard that the name stays gone |

## Why

The skills stopped reading `.minions/minions.toml` at v0.11 and run `make gate`. The parked runner
(`orchestrator/gate.py`) is its last reader, so this repository still keeps a second copy of the gate that can
drift from the `Makefile` ([evidence](design.md#evidence)). One gate means one list of commands.

## What Changes

```
  before:  skills ──▶ make gate          runner ──▶ .minions/minions.toml (a copy of the recipe)
  after:   skills ──▶ make gate          runner ──▶ make -n gate check ──▶ make gate
```

- **The runner runs `make gate`**, after the skills' `make -n gate` check. It raises an error naming the
  `Makefile` when the file is missing, has no `gate` target, or has a target that runs nothing. See
  [D1](design.md#d1), [D2](design.md#d2).
- **One gate event per run**, not one per command: the gate is one command now. See [D1](design.md#d1).
- **The file is deleted**, `.gitignore` ignores all of `.minions/`, and every live mention of the name goes. See
  [D5](design.md#d5).
- **The name joins the retired words** that `tests/test_conventions.py` fails on. See [D5](design.md#d5).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `gate`: one requirement REMOVED, one ADDED.
- `sdd`: one requirement ADDED.

| requirement | what changes |
|---|---|
| `gate` — Read the target's gate command list | removed: nothing reads a command list any more |
| `gate` — Run the target's `make gate` | new: the gate is `make gate`, checked first with `make -n gate` |
| `gate` — Run the gate, stop at the first failure | unchanged; its tests move to the `Makefile` fixture |
| `sdd` — The retired gate config is named nowhere | new: no shipped code, prompt, skill or doc names `minions.toml` |

## Impact

| area | files |
|---|---|
| runner | `orchestrator/gate.py` |
| tests | `tests/test_gate.py` · `tests/test_conventions.py` |
| docs | `docs/modules/gate.md` · `docs/modules/main.md` · `docs/architecture.md` · `CLAUDE.md` · `README.md` · `prompts/coder.md` |
| config | `.minions/minions.toml` (deleted) · `.gitignore` · `Makefile` (comment only) |
| dependencies | none |
| target repos | their leftover tomls are the human's to delete |

## Not in this change

- **The target repos.** Nothing there reads the toml since v0.11; the human deletes their copies.
- **The gate spec's Purpose paragraph.** It still names the toml, and the fold cannot reach a Purpose.
  `mf-release` flags it for a hand-edit ([D7](design.md#d7)).
- **Hardening the converge-skipped path** — backlog `0012·S1`, `S2`, `S4`, `R4`. It is the next patch.
