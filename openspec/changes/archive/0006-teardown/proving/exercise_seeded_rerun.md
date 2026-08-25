---
type: teardown
repo: "seeded"
head: "37fd7e9"
profile: python-uv
round: 3
criteria_total: 23
open_gaps: 3
open_blocking: 0
open_required: 2
verdict: gaps-found
---

# seeded — MinionsFactory compliance (mf-teardown, round 3)

## Summary

Contract-exercise target, third round. A 6/6 · B 5/6 · C 3/4 · `python-uv` **6/7** — 20 of 23 passing.

**This round exercises the merge table's fifth prior state: a `verified` criterion that fails again.**
`py:pinned-runtime` was `verified` at round 2 — the producer's fix was confirmed by a blind re-measurement and
`.python-version` was present at `b930975`. It is gone at `37fd7e9`. The blind measurement finds the criterion
failing, and the merge returns it to **`open`** with **this round's fresh evidence** and a rejected-regression
resolution-log line — it is **counted**, not carried forward as `verified`. Without that row a regressed
`required` criterion sits at `verified`, is counted in none of the three totals, and the verdict rule reads zero:
`verdict: compliant` on a repo with an open `required` gap.

`gate:make-mirrors` still fails and stays `open`; `sdd:checker-in-gate` was never claimed and stays `open`.

Nothing was withheld: `.minions/minions.toml` is at the path the orchestrator reads and its array is readable, so
the absent-subject rule never triggered. **`criteria_total: 23` — 23 − 0 not measured.**

## Gaps

### `gate:make-mirrors` · required · open
- **Evidence:** *(round 1, retained)* no root `Makefile` exists. A `find` over the whole worktree for any
  `*makefile*` returns nothing, so there is no `gate` target to mirror the array with.
- **Fix:** add a root `Makefile` with a `gate` target whose recipe runs the array's five commands in order.

### `py:pinned-runtime` · required · open
- **Evidence:** *(round 3, fresh — the entry was `verified` at round 2)* `.python-version` does not exist at the
  repo root; `git ls-files` does not list it. `pyproject.toml` declares `requires-python = ">=3.12"` but nothing
  pins a concrete interpreter. The pin that satisfied this criterion at `b930975` was removed at `37fd7e9`.
- **Fix:** write the concrete pin into `.python-version` and commit it.

### `sdd:checker-in-gate` · advisory · open
- **Evidence:** the last entry of the `gate` array in `.minions/minions.toml` is `uv run pytest -q`; no entry
  invokes a spec-binding checker.
- **Fix:** add the checker as the final gate command — see the criterion's own note on why this ships advisory.

## Passing

- **A · loop wiring — 6/6.** Including `wiring:claude-md`: the root `CLAUDE.md` carries no unfilled placeholder
  and no absolute vault path, names no retired `implementation_plans/` model, its account of where progress lives
  matches the tree — and **its account of the gate matches what the array runs** (five steps, lock sync first),
  the criterion's third (J) clause.
- **B · SDD layout — 5/6.** Only `sdd:checker-in-gate` fails. `sdd:active-change-contract` passes with nothing to
  measure: there is no active change, and the empty `openspec/changes/` is `sdd:changes-tree`'s subject, not this
  criterion's.
- **C · gate quality — 3/4.** `gate:contract-agrees` passes: `README.md`'s `bash` block is this repo's own gate
  and matches the array command-for-command, flags included, and `CLAUDE.md`'s prose axis list is out of that
  criterion's scope by its stated boundary — covered instead by `wiring:claude-md`'s (J) clause, which passes.
- **`python-uv` — 6/7.** Only `py:pinned-runtime` fails.

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
- 2026-08-25 · round 3 · `py:pinned-runtime` **verified → open — regression rejected**: the criterion passed at
  `b930975` and the entry was `verified`; the blind re-measurement at `37fd7e9` finds `.python-version` absent
  from the tree and from `git ls-files`. The entry returns to `open` with this round's fresh evidence and is
  counted in `open_gaps` and `open_required`. `verified` is a statement about the round that measured it, not a
  permanent one.
- 2026-08-25 · round 3 · `gate:make-mirrors` stays `open` (still failing); `sdd:checker-in-gate` stays `open`.
  3 open gaps (0 blocking, 2 required, 1 advisory); 0 withheld. `verdict: gaps-found`.
