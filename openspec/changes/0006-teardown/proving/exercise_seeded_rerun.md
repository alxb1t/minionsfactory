---
type: teardown
repo: seeded
head: 81b9c00
profile: python-uv
round: 2
criteria_total: 23
open_gaps: 2
open_blocking: 0
open_required: 1
verdict: gaps-found
---

# seeded — MinionsFactory compliance (mf-teardown, round 2)

## Summary

Contract-exercise target, re-measured after a producer round. A 6/6 · B 5/6 · C 3/4 · `python-uv` **7/7**.

Of the two gaps `mf-retrofit` marked `fixed`, **one holds and one does not**. `py:pinned-runtime` is confirmed
and flips to `verified`; `gate:make-mirrors` still fails and goes **back to `open`** with the rejected fix noted
below. `sdd:checker-in-gate` was never claimed and stays `open`.

## Gaps

### `gate:make-mirrors` · required · open
- **Evidence:** no root `Makefile` exists. The complete tracked file set holds no makefile under any name — the
  claimed fix is not present in the repo. There is nothing for a human-typed gate to mirror the array with.
- **Fix:** add a `Makefile` `gate` target running the array's commands in the same order.

### `py:pinned-runtime` · required · verified
- **Evidence:** *(round 1, retained)* no `.python-version` at the repo root. `pyproject.toml` declares
  `requires-python = ">=3.12"` but nothing pins a concrete interpreter.
- **Fix:** write the concrete pin into `.python-version` and commit it.

### `sdd:checker-in-gate` · advisory · open
- **Evidence:** the last entry of the `gate` array in `.minions/minions.toml` is `uv run pytest`; no entry
  invokes a spec-binding checker.
- **Fix:** add the checker as the final gate command — see the criterion's own note on why this ships advisory.

## Passing

`python-uv` reaches **7/7** this round — `py:pinned-runtime` now passes at source. Groups A and B are otherwise
unchanged from round 1.

## Resolution log

- 2026-08-24 · round 1 · first measurement, no prior report. 3 gaps opened at `open`. `verdict: gaps-found`.
- 2026-08-24 · `mf-retrofit` (producer) claims `gate:make-mirrors` and `py:pinned-runtime` **fixed** —
  awaiting an independent teardown re-run to confirm or reject.
- 2026-08-24 · round 2 · `py:pinned-runtime` **fixed → verified**: the blind re-measurement finds
  `.python-version` present and pinned to `3.12`, consistent with `requires-python`. Fix confirmed.
- 2026-08-24 · round 2 · `gate:make-mirrors` **fixed → open — fix rejected**: the producer marked it fixed, but
  the re-measurement finds no `Makefile` in the repo at all. The claim is not supported by the tree; the gap is
  reopened with its original evidence.
- 2026-08-24 · round 2 · `sdd:checker-in-gate` stays `open` (never claimed). `verdict: gaps-found`.
