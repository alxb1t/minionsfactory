---
version: v0.24
---

# 0024-bootstrap — proposal

**In one line:** a new skill, `mf-bootstrap`, turns a new directory into a repo where `mf-cut-change` passes its
preconditions.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`B1`…`B12`), the skill text and its templates |
| [tasks.md](tasks.md) | the build: the skill, the layout scan, the record |

## Why

Nothing sets up a target today. The operator writes the gate, `openspec/`, `CLAUDE.md`, `CHANGELOG.md` and the
`.gitignore` by hand, then commits them, before the first cut can run. A missed piece shows up as a halt later:
an unignored `.minions/` fails the release's clean-tree check, and a missing `## [Unreleased]` has no owner.

## What Changes

```
  new directory ──▶ mf-bootstrap ──▶ committed main ──▶ mf-cut-change ──▶ …
                    writes D18's layout,
                    runs the gate, commits once
```

- **A skill, `skills/mf-bootstrap/SKILL.md`,** with its templates in `skills/mf-bootstrap/templates/`. It writes the
  starting files, runs `make -n gate` and `make gate`, and makes one commit. See [B1](design.md#b1)–[B10](design.md#b10).
- **A layout scan in `tests/test_skills.py`:** every entry of D18's tree has a template, and the gate template
  validates the specs. See [B11](design.md#b11).
- **The decisions in force, amended** in `docs/decisions.md`: D2 and D18 (the stations install nothing; the
  bootstrap writes once), D8 (a target's gate may run the OpenSpec CLI), D21 (the bootstrap commit names no
  change). See [B12](design.md#b12).
- **The front door:** the skills table and *What a target repo needs* in `README.md`, and the skills line in
  `CLAUDE.md`.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: **ADDED** *The bootstrap writes the target layout* — the templates cover D18's tree, `.minions/` as a
  `.gitignore` line, `CHANGELOG.md` and `README.md`; the gate template validates the specs.

## Impact

| area | files |
|---|---|
| skills | `skills/mf-bootstrap/SKILL.md` and `skills/mf-bootstrap/templates/` (new) |
| tests | `tests/test_skills.py` |
| docs | `docs/decisions.md`, `README.md`, `CLAUDE.md` |
| dependencies | none |
| target repos | none changed; a new one is bootstrapped by the skill |

## Not in this change

- **CI, a remote, `docs/` or `.minions/` in the target.** The skill reports a missing remote and adds none
  ([B8](design.md#b8)).
- **Adopting an existing codebase.** A repo that already holds a `Makefile`, `CLAUDE.md`, `CHANGELOG.md` or
  `openspec/` halts the skill ([B5](design.md#b5)).
- **A CHANGELOG entry for the bootstrap.** It is not a version ([B9](design.md#b9)).
- **An autonomous copy.** The autonomous line assumes a target already bootstrapped.
- **This repo's own gate.** It still runs no OpenSpec CLI ([B12](design.md#b12)).
