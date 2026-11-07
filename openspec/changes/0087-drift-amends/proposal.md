---
bump: minor
---

# Drift amends

Drift that needs the person's amend of the change directory halts converge `amend needed` at the debt write, instead of
going to the debt and shipping a stale archive; the rescue's amend answers it, and converge replays it by rule.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The fixer may not edit the change's `tasks.md` or `design.md`, so it marks such a card `wontfix`, naming the amend. But the
verify pass turns that `wontfix` into `accepted`, and a drift card found after the pickup stays `open` and goes to the debt
at Step 9. The release reads no debt. `0084` released this way with R4 and R6 stale (v0.68.1), and the cards of its class wait
in the debt. v0.70.0's rescue can already write the amend at an `amend needed` halt: converge just never raises one for drift.

## What Changes

- **The verify pass keeps an amend's `wontfix`** — a `wontfix` naming the person's amend stays `wontfix`, never `accepted`.
- **An amend card** — a card whose **Fix**, or whose `wontfix` note, names the change's `tasks.md` or `design.md` by path.
- **Step 9 halts on amend cards** — a non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?**
  check still shows it, halts `amend needed — <card ids>` before the debt lock, writing nothing to the debt.
- **The amend replays by rule** — an answered `amend needed` halt whose findings files are both still `verdict: clean` runs
  the catch-up round again, as an answered catch-up halt does: no new round 1. There the amend cards go on as any card.
- **The rescue's row** — `mf-rescue` amends what the halt's cards name, the `open` drift card's **Fix** included.
- **D15 amended** — drift never blocks, save a card naming the plan's amend; D16's debt line names the same exception.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The converge fixer leaves the plan to the person* — MODIFIED: a blocking card's amend halts after the fix pass; the
    verify pass keeps an amend's `wontfix`; a non-blocking amend card halts at Step 9.
  - *Converge keeps deferred work in one repository debt file* — MODIFIED: an amend card halts instead of going to the debt,
    save in the catch-up run its amend answered.
  - *A converge halt answered by the person converges afresh* — MODIFIED: an answered `amend needed` halt with both findings
    files clean runs the catch-up round again.
  - *A halted version is rescued in its run* — MODIFIED: the rescue amends what the halt's cards name; the version converges
    on in an `· amended` run, or in the catch-up round when both findings files are clean.

## Impact

Changes `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`, `skills/mf-rescue/SKILL.md`,
`skills/mf-ship/scripts/conduct.py` (the grant comment), `docs/decisions.md` (D15, D16), `tests/fake_worker.py` and
`tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Amending the archives already released stale, and their cards `0071·R7`, `0076·R2`, `0083·R4`, `0085·R12`, `0084·R4` and
  `0084·R6` — debt paydown 2.
- A `nit` naming an amend found after the pickup — it goes to the debt, as now.
- A change to `conduct.py`'s handling of the halt: its `amend needed` rescue and amends-only answer already take it.
- A release precondition on converge's status log — until a release run by hand after a halt ships a stale archive; see the
  design's risks.
