---
bump: minor
---

# Drift amends

Drift that needs the person's amend of the change directory halts converge `amend needed` at the debt write, instead of
going to the debt and shipping a stale archive; the rescue's amend answers it, and converge's catch-up round reads it in one
Step 7 round, passing only the person's amend by rule.

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
- **The amend is caught up** — an answered `amend needed` halt whose findings files are both still `verdict: clean` runs
  the catch-up round again, as an answered catch-up halt does: no new round 1. A rescue's amend, carrying a `Rescue:`
  trailer, gets one Step 7 round there; only the person's passes by rule. An amend card whose id an answered halt named, or
  whose qualified id the debt already holds, goes on as any card.
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
    save one an answered halt named or the debt already holds.
  - *A converge halt answered by the person converges afresh* — MODIFIED: an answered `amend needed` halt with both findings
    files clean runs the catch-up round again, a rescue's amend judged in one Step 7 round.
  - *A halted version is rescued in its run* — MODIFIED: the rescue amends what the halt's cards name; the version converges
    on in an `· amended` run, or in the catch-up round when both findings files are clean.
  - *The release ships only a reviewed head* — MODIFIED: merges and amends include the rescue's amend, which keeps the
    catch-up's own count; the round is by rule only when no amend carries a `Rescue:` trailer.
  - *Anchored harms block, and drift has its own tier* — MODIFIED: drift never blocks, save an amend card, on which converge
    halts at Step 9.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: by rule passes the person's
    amends alone, never one carrying a `Rescue:` trailer.

## Impact

Changes `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`, `skills/mf-rescue/SKILL.md`,
`skills/mf-ship/scripts/conduct.py` (the grant comment), `docs/decisions.md` (D15, D16) and `tests/test_conduct.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Amending the archives already released stale, and their cards `0071·R7`, `0076·R2`, `0083·R4`, `0085·R12`, `0084·R4` and
  `0084·R6` — debt paydown 2.
- A `nit` naming an amend found after the pickup — it goes to the debt, as now.
- A change to `conduct.py`'s handling of the halt: its `amend needed` rescue and amends-only answer already take it.
- A release precondition on converge's status log — until a release run by hand after a halt ships a stale archive; see the
  design's risks.
