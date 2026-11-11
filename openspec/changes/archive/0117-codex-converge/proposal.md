---
bump: minor
version: 0.97
debt: [0104·S4]
---

# Codex converge

The fixer may run on Codex too, so the whole converge stage can run on Codex; a Codex fixer at a usage limit halts for the person, never falls back.

Reading map: [design](design.md) holds the decisions, the tests and the risks, [tasks](tasks.md) its phases: the models line, the fixer on Codex, the headroom and the record.

## Why

Only the fixer is still on Claude. The checkers, the verify workers, the pickup check, the rewrites and the retries all go through `Run.checker`, which runs on Codex with a per-checker Claude fallback; every one of 0110–0116 ran its checkers on Codex. The Claude fixer cost $9.87 over 0110–0116, the only Claude spend left in converge.

The line also reads one Codex window. `_headroom` reads the 5-hour window alone, and the weekly window stood at 98% on 2026-11-11 with nothing to say so.

## What Changes

- `fix codex/<model> <effort>` is valid in a brief, and `[converge.fix] executor = "codex"` in `models.toml`. A fixer naming no host runs on Claude, and no longer inherits `[converge]`'s executor.
- `converge.py` starts a Codex fixer through a new host call, `Host.fix`. When Codex is not ready, or a limit stops the fixer, the version halts `codex usage limit — the fixer · resets <time>`. The fixer never falls back to Claude.
- `_headroom` reads the 5-hour and the weekly window. Either at 90% or more sends a Codex checker to Claude before its spawn, and halts a Codex fixer before its spawn, naming the window.
- A limit no longer halts a version for a Codex station it no longer needs, or a rescue or supervisor that may never run (debt card 0104·S4).
- A Codex fixer's prompt fills its `Co-Authored-By:` with its own model, and `fix.md` says a fixer adds no package.
- `docs/decisions.md`'s D68, D76 and D40 are edited where they live.

Requirements the delta touches:

- MODIFIED *A station's executor comes from the models file*: a fixer table may name `executor`, and a fixer naming none runs on Claude.
- MODIFIED *Converge's workers take their models from the models file*: the same rule for the worker tables, and the cut writes a brief's `fix` host.
- MODIFIED *A Codex usage limit halts only what runs on Codex*: a Codex fixer halts at a limit, and a version past a station is not halted for it.
- MODIFIED *A Codex checker falls back to Claude while Codex is limited*: both windows are read.
- ADDED *A Codex fixer halts at a limit and never falls back*.
- ADDED *A Codex fixer carries its own attribution and adds no package*.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the executor, worker-table and usage-limit requirements above, and two added for the fixer.

## Impact

- `skills/mf-plan/scripts/brief_check.py`, `skills/mf-plan/SKILL.md`.
- `skills/mf-ship/scripts/conduct.py`: `_models`, `_headroom`, `Run.fix`, `Run.codex_ready`, `Run.on_stations`, `Run.hold_limited`.
- `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/references/fix.md`, `skills/mf-converge/SKILL.md`, `skills/mf-ship/SKILL.md`.
- `docs/decisions.md`; the living spec, folded from the delta at release.
- `tests/test_brief_check.py`, `tests/test_conduct.py`, `tests/test_converge.py`.

## Not in this change

- A Claude fallback for a Codex fixer: the person's call, to prove Codex alone (Q3).
- A separate verify executor: verify already rides its role's table.
- This version's own fixer on Codex: its converge runs v0.96.0's `converge.py` and `_models`, where a fixer naming a host halts, so its fixer stays Claude.
