---
bump: minor
after: [0082-cut-station, 0084-ship-fixes-2]
---

# Self-healing ship

An `mf-ship` run handles its own halts as the person's supervising chat did: the rescue amends at `amend needed`, takes a card's
recommended fix where the version's switch allows it, and the run goes on while anything can move.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

Over runs 1–9 of 2026-11-05/06 a supervising chat answered every halt by hand: about 70% were the line's own gaps — a rescue's amend
at `amend needed` refused, an amend landing during a rescue freezing the version, eight restarts for halts already answered on
disk — and about 25% prose amends at `amend needed` a fresh reader could write. The person wants to run `mf-ship` and have it
manage its halts itself, with no supervisor role.

## What Changes

- **Rescue at `amend needed`** — the rescue gets the plan's amend paths at an `amend needed` halt, on entry and after a failed
  check, and an accepted amend takes the version back to converge in the same run; a security `critical` or `high` card gets a
  diagnosis.
- **The switch** — `decide = "recommended"` at the top of a version's models file lets its rescue edit `proposal.md` and
  `design.md`'s `## Decisions`, with a `Decided-by: rescue` trailer; the run logs `decided`, the close and `report` name each
  decision, and the run metrics count them.
- **The run goes on** — an amend landing during a rescue no longer freezes the version; each poll takes back every halted version
  answered on disk, with no request; the run ends only when nothing can move, its closing line naming what each halted version
  needs.
- **The record** — D47 and D53 amended, D59 added; `THREAT_MODEL.md` names a rescue committing a card's fix; `mf-ship`'s and
  `mf-rescue`'s skills.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A halted version is rescued in its run* — MODIFIED: an `amend needed` halt is rescued with an amend; the person's amends
    during a rescue let the version go on; the `decided` event.
  - *A halted version rejoins a live run* — MODIFIED (as `0082-cut-station` leaves it): the person's amends during a rescue are
    no rescue's answer.
  - *A rescue decides by the version's switch* — ADDED.
  - *A run goes on while anything can move* — ADDED: the re-check at each poll, the end condition, the closing line's needs.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-rescue/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md` (D47,
D53, D59), `THREAT_MODEL.md`, `scripts/metrics/run.py`, `metrics/catalogue.toml`, `tests/test_conduct.py`, `tests/fake_worker.py`
and `tests/test_metric_scripts.py`.

Builds on `0082-cut-station` (the switch's place, the queue, `admit`) and `0084-ship-fixes-2` (the halt before round 1).

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- A push notification when a person is needed — until a control surface exists, the close and `report` name it.
- A supervisor role watching the run.
- The cut's own decisions under the switch — `0082-cut-station`'s.
- A rescue at a timeout, a usage limit, a failed worker, a `**HUMAN` phase or a stopped release.
