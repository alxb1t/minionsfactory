# mf-simplify — tasks

Build the settled [design](design.md), one phase at a time. The skill, station and decision text is the design's,
word for word.

## Progress

- [x] 1 — Write mf-simplify
- [x] 2 — Run it in the build
- [x] 3 — Record it
- [ ] 4 — Calibrate it

## 1 — Write mf-simplify

- [x] 1.1 Write `skills/mf-simplify/SKILL.md`, per [D1](design.md#d1).
  Verify: `grep -c '^name: mf-simplify$' skills/mf-simplify/SKILL.md` prints `1`, and `grep -c '^## Never applied — noted for review$' skills/mf-simplify/SKILL.md` prints `1`.

## 2 — Run it in the build

- [x] 2.1 Apply [D2](design.md#d2) to `skills/mf-build/SKILL.md`, and delete `skills/mf-build/references/generic-simplify.md`.
  Verify: `grep -c '/simplify' skills/mf-build/SKILL.md` prints `0`, `grep -c '../mf-simplify/SKILL.md' skills/mf-build/SKILL.md` prints `1`, and `test -e skills/mf-build/references/generic-simplify.md` fails.
- [x] 2.2 Apply [D2](design.md#d2) to `skills/mf-release/SKILL.md` and `skills/mf-cut-change/SKILL.md`.
  Verify: `grep -c 'native (Claude Code)' skills/mf-release/SKILL.md` prints `0`, and `grep -c '/simplify' skills/mf-cut-change/SKILL.md` prints `0`.

## 3 — Record it

- [x] 3.1 Rewrite D11 and amend D13 in `docs/decisions.md`, per [D3](design.md#d3).
  Verify: `grep -c 'Every station runs MF.s own method' docs/decisions.md` prints `1`, and `grep -c 'Its engine follows' docs/decisions.md` prints `0`.
- [x] 3.2 Edit `AGENTS.md`, `README.md` and `docs/README.md`, per [D3](design.md#d3).
  Verify: `grep -c '/simplify' README.md docs/README.md AGENTS.md` prints `0` for each file, and `grep -c 'skills/mf-simplify/SKILL.md' README.md` prints `1`.

## 4 — Calibrate it

[D4](design.md#d4)'s calibration, from this worktree under the shell rules: no `cd`; `uv run --directory` sets the
worker's cwd; the key never enters the fixture.

- [ ] 4.1 Build `../mf_simplify_probe/seeded` from [D4](design.md#d4)'s files: `git init -b main`, the base files and
  the `chore: base` commit, `git -C ../mf_simplify_probe/seeded switch -c v0.2_orders`, the change directory, `orders.py`
  and `tests/test_orders.py`, and the `feat: orders` commit with its `Change: 0002-orders` trailer.
  Verify: `make -C ../mf_simplify_probe/seeded gate` exits 0, and `git -C ../mf_simplify_probe/seeded log --oneline | wc -l` prints `2`.
- [ ] 4.2 `uv run --directory ../mf_simplify_probe/seeded --script ../../minionsfactory/skills/mf-ship/scripts/conduct.py agent --executor claude "Run the skill at ../../v0.38_simplify/skills/mf-simplify/SKILL.md for change 0002-orders."`.
  Verify: `git -C ../mf_simplify_probe/seeded log -1 --format=%s` prints `refactor(0002-orders): simplify`, and `make -C ../mf_simplify_probe/seeded gate` exits 0.
- [ ] 4.3 Score `../mf_simplify_probe/seeded/orders.py` by [D4](design.md#d4)'s key and the commit's body, and write
  `openspec/changes/0044-simplify/evidence/calibration.md` in this worktree, no absolute path:
  `pieces: <the applied ids> · traps kept: <the kept ids> · net: <the commit's net line> · tokens <n|unavailable>`.
  Verify: `grep -c '^pieces: P1 P2 P3 P4 P5 · traps kept: T1 T2 T3 T4 · net: -' openspec/changes/0044-simplify/evidence/calibration.md` prints `1`.
- [ ] 4.4 Delete the probe: `rm -rf ../mf_simplify_probe`.
  Verify: `test -e ../mf_simplify_probe` fails.
