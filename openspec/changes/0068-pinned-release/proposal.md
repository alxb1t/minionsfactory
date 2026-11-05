---
bump: minor
backlog: [0051·R10]
---

# Pinned release

The machine runs one released MF, exported from its tag, not the live checkout: MF ships its next versions while other repos keep
running, and the machine moves to a new release on its own, never under a live run.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`make install-skills` links every `mf-*` into the live checkout, so every MF release, and every checkout of the primary, changed the
skills isekai's and gpunit's workers read mid-run (2026-11-03). Since 2026-11-04 the person has pinned by hand: each release's
`skills/` exported into `~/.local/share/minionsfactory/<tag>/`, both hosts re-linked between runs. This makes that the install.

## What Changes

- **`pin.py`** — exports a tag's `skills/` from a scratch clone of the kept `origin` (or, for `TAG=<tag>`, the checkout) with a
  `VERSION`; links both hosts; holds; records the source; keeps every tree; `make install-skills [TAG=<tag>|live]` calls it.
- **Live marks and the quiet move** — each conductor marks itself live; an install under a live run writes `pending`; the first
  starting or last ending conductor moves the links to the pending or newest origin-held tag.
- **The record** — the `start` line names the release, `mf_version` reads `VERSION`, `_unlinked` checks one tree.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A machine runs one pinned MF release* — ADDED: the export, the links, the hold, the live marks, the move, the `start` line.
  - *Skills install into the shared user directory by default* — REMOVED: `SKILLS_DIR` goes; both hosts link together.
  - *A run needs its skills linked* — MODIFIED: every link into one tree.
  - *A data file records where its values came from* — MODIFIED: `mf_version` from `VERSION`.

## Impact

Changes `Makefile` (the install recipes, quoted), `skills/mf-ship/scripts/pin.py` (new), `skills/mf-ship/scripts/conduct.py`,
`skills/mf-build/scripts/metrics.py`, `skills/mf-ship/SKILL.md`, `README.md`, `AGENTS.md`, `docs/decisions.md` (a new decision),
`docs/principles.md`, `THREAT_MODEL.md` and the tests.

Dependencies: none. The gate recipe stays unchanged; only the install recipes in `Makefile` change.

## Not in this change

A pin per project; a Python package or plugin; pruning old trees; a live mark from a station run by hand.
