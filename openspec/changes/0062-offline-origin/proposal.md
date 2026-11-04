---
bump: minor
backlog: [0051·R12]
---

# Offline origin

A run goes on when `origin` cannot be reached: it builds, converges, integrates and releases locally, and its pushes wait until
`origin` answers.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

isekai, 2026-11-04, during a GitHub incident: twice at a run's start, `conduct: halt — cannot read origin: nothing pushed`,
SSH with the same key refused intermittently, and no worker started. Builds, converges and local releases need no `origin`;
only the push does. Every run on the machine was blocked for the outage's length.

## What Changes

- **An offline base** — `~/.mf-ship-origin/<digest>.pushed`, the default-branch sha a run last saw on `origin`, written after
  every good read and push; offline, the run judges the default branch against it.
- **`conduct.py anchor`** — a person's session seeds the first offline base from the tracking ref, checked, once per repo,
  on `--yes <sha>` after it prints the sha and subject.
- **A failed read or push is a wait, not a halt** — three tries at the start, then the run goes on; each release pushes what is
  pending; one last round at the end. A read that succeeds and shows something wrong still halts.
- **A release made offline ships locally** — merged and tagged on the local default branch, its worktree removed, its
  dependents merged from the local default branch; the next run pushes it.
- **The record** — the `start` line, `push — waiting` events, the close's `· unpushed`, and `report` name every wait.
- **`ssh -o ConnectTimeout=15 -o BatchMode=yes`** on the conductor's remote calls, when the operator set no ssh command.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A run goes on while origin cannot be reached* — ADDED: the offline base, the anchor, the waits, the local release and the
    record.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: the offline base joins the home folder's state, and an
    unreadable `origin` with no offline base needs the person.
  - *A re-run recovers what a dead station left* — MODIFIED: an `origin` it cannot read leaves the push waiting.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `docs/decisions.md` (D47, D51), `docs/principles.md`,
`THREAT_MODEL.md` and `tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

Pays down `0051·R12`. `0049·S7` stays open: its remote half was closed at the base, and `_dirty` and `_unmerged` still race.

## Not in this change

Claude's or Codex's own API being down; a first-ever run with no kept URL; telling an auth failure from a network one; an
offline base seeded with no person's session.
