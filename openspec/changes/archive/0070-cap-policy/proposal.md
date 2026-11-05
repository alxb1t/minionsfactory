---
bump: minor
version: v0.59
---

# Cap policy

At a converge cap the run grants one more round on its own when every open blocker is small, and otherwise — or at the next cap —
halts the version as a re-plan pointing to `mf-plan`, not to another grant.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

MF `0067-rescue` capped on 2026-11-05 at 02:28 on two small blockers, each a line or a test, and waited for the person's grant
overnight. isekai `0095` capped six times and took five grants, each fixing one edge of a design and finding the next: a cap of
small cards is a grant's job, a cap that recurs is a plan's.

## What Changes

- **The card reader** — the conductor reads the open blocking cards and their sizes from the findings files.
- **The automatic grant** — at a cap of small cards no granted round reached, the conductor spawns converge with `grant=yes`.
- **The re-plan halt** — any other cap, and a granted round that blocks again, halts as `re-plan`; the rescue names `/mf-plan`.
- **`[converge] auto_grant`** — default `true`; `false` turns it off for a version.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A run grants one round at a small cap, and halts a large one for a re-plan* — ADDED: the rule, the spawn, the re-plan halt,
    the setting, the person's grant.
  - *A halted version is rescued in its run* — MODIFIED: a converge cap the run grants gets no rescue.

## Impact

Builds on `0067-rescue`, released as v0.56.0 before this cut's commit.

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-rescue/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md` (D47,
D54), `tests/test_conduct.py` and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

An automatic grant by hand, outside `mf-ship`; detecting a repeated function across caps; a cut that re-plans on its own.
