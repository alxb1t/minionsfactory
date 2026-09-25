# 0012-converge-optional — tasks

**In one line:** one phase — `mf-release` accepts a skipped converge, `docs/sdd.md` says so, and a scan test
holds it. The why of every task is in [design.md](design.md).

## Progress

- [x] 1 — `mf-release` accepts a skipped converge

## 1 — `mf-release` accepts a skipped converge

One phase, because the docs describe the release and must not lag it ([D7](design.md#d7)). The before → after
text is in [design.md](design.md#d1d5--mf-release-before--after).

- [x] 1.1 **HALT CHECK** — `mf-converge` still carries the missing-file rule this change leaves with it ([D5](design.md#d5)).
  Verify: `grep -c 'A missing findings file is not clean' skills/mf-converge/SKILL.md` prints `1`.
- [x] 1.2 Test first: add the converge-optional scan and its twin to `tests/test_skills.py`, bound to
  `sdd:converge-optional:skip-is-stated` ([Seams](design.md#seams--what-the-test-holds)).
  Verify: `uv run pytest tests/test_skills.py -q` fails, naming the missing skip line in `mf-release`.
- [x] 1.3 `skills/mf-release/SKILL.md` precondition 4 becomes *converge ran, or was skipped* ([D1](design.md#d1), [D2](design.md#d2)).
  Verify: `grep -c 'converge: skipped — no findings files' skills/mf-release/SKILL.md` prints `1` or more.
- [x] 1.4 Preconditions 2 and 3 open with "If converge ran (precondition 4):"; the findings-paths paragraph drops
  its halt. Verify: `grep -c 'If converge ran (precondition 4)' skills/mf-release/SKILL.md` prints `2`.
- [x] 1.5 Step 4 item 4 and Step 5 report item 1 state the skip ([D4](design.md#d4)). Verify:
  `sed -n '/^## Step 4/,/^## Never/p' skills/mf-release/SKILL.md | grep -c 'converge: skipped'` prints `2` or more.
- [x] 1.6 The `description:` and the paragraph under the title stop requiring a converged change.
  Verify: `grep -c -i -e 'converged change' -e 'converge has returned' skills/mf-release/SKILL.md` prints `0`.
- [x] 1.7 Precondition 5 is left exactly as it is ([D3](design.md#d3)). Verify:
  `git diff main -- skills/mf-release/SKILL.md | grep -c '^[-+]5\. '` prints `0`.
- [x] 1.8 `docs/sdd.md`: the findings-contract sentence and the release-fold precondition ([D5](design.md#d5)). Verify:
  `grep -c 'cannot let the loop or the release pass falsely' docs/sdd.md` prints `0`; `grep -c 'skipped' docs/sdd.md` prints `2` or more.
- [x] 1.9 The scan passes. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
