---
version: v0.38
---

# mf-simplify

MF's own simplify, `mf-simplify`, on every host: it edits a change's own lines by fixed angles and closed edit kinds,
held by the change's spec, design, decisions, standards and threat model, with the gate after each angle; native
`/simplify` leaves the build, and MF is model-independent end to end.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The build closes with native `/simplify` on Claude Code and a thin generic reference elsewhere. Native `/simplify`
runs only on Claude Code and never runs the tests; the generic one has no checklist and uses none of the documents MF
keeps. The simplify research (the vault's simplify research note: Claude Code, Codex, Matt Pocock, gstack) found no
safe automatic simplify anywhere — and MF has what one needs: a spec that says what is intended, decisions and a
threat model that say what to keep, and a gate.

## What Changes

- **`skills/mf-simplify/SKILL.md`**, a new skill: the angles (reuse, simplification, efficiency, altitude,
  conventions), the closed edit kinds (`delete`, `stdlib`, `native`, `reuse`, `speculative`, `shrink`), the oracles, the
  never-touch list, the gate after each angle, and one commit naming what it applied and skipped, `net: -N lines`.
- **The build's Step 3 runs `mf-simplify`**; *Executor selection* reports the executor and chooses no engine;
  `references/generic-simplify.md` is deleted.
- **D11** — every station runs MF's own method; **D13** loses its engine sentence.
- **A calibration** on a seeded fixture: the simplifiable pieces applied, the traps untouched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Engine selection follows the executor* — REMOVED, renamed to *Every station runs MF's own method* — ADDED: no
    native `/simplify`; the build reports the executor.
  - *Generic passes preserve the station boundaries* — MODIFIED: simplify is `mf-simplify`'s method.
  - *Bundled generic role references resolve* — MODIFIED: the build's link to `mf-simplify` resolves.
  - *The build collects a draft of the metrics after simplify* — MODIFIED: worded as `lean already` and `nothing kept`.
  - *A data file records where its values came from* — MODIFIED: worded as the build's *Executor*.
  - *mf-simplify simplifies a change inside its oracles* — ADDED.

## Impact

Adds `skills/mf-simplify/SKILL.md`; deletes `skills/mf-build/references/generic-simplify.md`; changes
`skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-release/SKILL.md`, `docs/decisions.md`,
`AGENTS.md`, `README.md` and `docs/README.md`. The [delta](specs/sdd/spec.md) is folded by release. After release the
person runs `make install-skills` once: a new skill directory is not linked until then.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A parallel, per-angle simplify; simplify outside an active change; whole-repo cleanups; renames for their own sake;
a findings file or a verdict for simplify (D13).
