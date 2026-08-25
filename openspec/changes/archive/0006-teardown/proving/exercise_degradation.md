---
type: teardown
repo: degrade
head: a3d91c8
profile: none
round: 1
criteria_total: 16
open_gaps: 3
open_blocking: 1
open_required: 1
verdict: gaps-found
---

# degrade — MinionsFactory compliance (mf-teardown, round 1)

## Summary

A contract-exercise target: a git repo with a `package.json` and **no Python manifest**. It exists to prove the
degradation path — that an unrecognised toolchain produces a complete report rather than a guess or an abort.

**No profile matched, so `profile: none` and the toolchain criteria were not assessed.** The repo carries a
`package.json` and no `pyproject.toml`, so the `python-uv` detection rule (a tracked `pyproject.toml` **plus** a
uv signal) does not fire and no other profile ships at v0.6. The seven `python-uv` criteria were **never in this
run's baseline** — they are *not assessed*, which is different from *not measured*: nothing was withheld, they
were simply out of scope, and no toolchain gap is reported against this repo.

**`criteria_total: 16` — the universal tier baseline, 16 − 0 not measured.** The measurement covered groups A, B
and C only.

## Gaps

### `gate:covers-axes` · blocking · open
- **Evidence:** `.minions/minions.toml` declares `gate = ["npm run lint", "npm test"]` — two entries covering at
  most two of the four axes. **format:** no entry, and no formatter config anywhere in the tree. **typecheck:**
  no entry, and no `tsconfig*.json`. **lint:** `npm run lint` names a script `package.json` does not define — its
  `scripts` block is `{"test": "node --test"}` only, so the axis has no runnable command behind it. **test:**
  covered by `npm test`.
- **Fix:** add a command for each uncovered axis, and define the `lint` script the array already invokes. A gate
  missing an axis still exits `0`, so the loop advances on it.

### `gate:make-mirrors` · required · open
- **Evidence:** no `Makefile` exists at the repo root under any name — `ls Makefile makefile GNUmakefile` finds
  none and a case-insensitive `find` over the tree (excluding `.git`) matches nothing.
- **Fix:** add a `Makefile` `gate` target mirroring the array. Note this criterion is **not** withheld by the
  absent-subject rule: its subject is the `Makefile`, not the gate config.

### `sdd:checker-in-gate` · advisory · open
- **Evidence:** the **last** entry of the `gate` array in `.minions/minions.toml` is `npm test`, which
  `package.json` defines as `node --test` — a test runner, not a spec-binding checker. No entry in the array
  invokes one.
- **Fix:** add the checker as the final gate command — **but see the criterion's own note:** the checker is not
  distributable into a target today, which is why this ships `advisory` and does not withhold the verdict.

## Passing

- **A · loop wiring — 6/6.**
- **B · SDD layout — 5/6.** `openspec/specs/greeter/spec.md` and `openspec/changes/archive/` both present; the
  universally-quantified criteria pass over the scenarios actually shipped.
- **C · gate quality — 2/4.** `gate:contract-agrees` passes vacuously — there is no `README.md` and `CLAUDE.md`
  is prose with no fenced code block and no list of command lines, so nothing declares the gate *as commands* to
  compare against the array. `gate:no-gaming` passes: the only config the gate's commands read is `package.json`,
  which declares no ignore, exclude, per-path override or severity downgrade.

**Nothing was withheld under the absent-subject rule** — `.minions/minions.toml` is at the correct path, tracked
and readable, so every gate-array-subject criterion was measured normally.

## Resolution log

- 2026-08-24 · round 1 · first measurement, no prior report. 3 gaps opened at `open` (1 blocking, 1 required,
  1 advisory); 0 withheld. `profile: none` — the seven `python-uv` criteria not assessed and excluded from the
  baseline. `verdict: gaps-found`.
