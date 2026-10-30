# The review method — tasks

Build the settled [design](design.md), one phase at a time. The reference, station and decision text is the
design's, word for word.

## Progress

- [x] 1 — Write the method
- [x] 2 — Run it at a tier
- [x] 3 — Record it
- [x] 4 — Calibrate it

## 1 — Write the method

- [x] 1.1 Replace `skills/mf-converge/references/generic-review.md` with [D1](design.md#d1)'s text.
  Verify: `grep -c '^## Inspect: one section each, in this order$' skills/mf-converge/references/generic-review.md` prints `1`, and `grep -c 'inconclusive' skills/mf-converge/references/generic-review.md` prints at least `2`.
- [x] 1.2 Replace `skills/mf-converge/references/generic-security.md` with [D2](design.md#d2)'s text.
  Verify: `grep -c 'source → control → sink → boundary → counterevidence' skills/mf-converge/references/generic-security.md` prints `1`, and `grep -c '^\*\*Trust precedents\*\*' skills/mf-converge/references/generic-security.md` prints `1`.
- [x] 1.3 Write `skills/mf-converge/references/high-tier.md`, per [D3](design.md#d3).
  Verify: `grep -c '^4\. \*\*Role writer\.\*\*' skills/mf-converge/references/high-tier.md` prints `1`.

## 2 — Run it at a tier

- [x] 2.1 Replace *Executor and worker selection* and edit Step 3 in `skills/mf-converge/SKILL.md`, per
  [D4](design.md#d4).
  Verify: `grep -c '/code-review\|/security-review' skills/mf-converge/SKILL.md` prints `0`, and `grep -c '^## The tier and the workers' skills/mf-converge/SKILL.md` prints `1`.
- [x] 2.2 Add the frontmatter keys, the card's fields, the status-log details and Step 10's sentence in
  `skills/mf-converge/SKILL.md`, per [D4](design.md#d4).
  Verify: `grep -c 'all fourteen keys' skills/mf-converge/SKILL.md` prints `1`, and `grep -c '^| \*\*Verdict\*\* |' skills/mf-converge/SKILL.md` prints `1`.
- [x] 2.3 Edit the release's close-out in `skills/mf-release/SKILL.md` and the cut's *Suggesting models* in
  `skills/mf-cut-change/SKILL.md`, per [D5](design.md#d5) and [D6](design.md#d6).
  Verify: `grep -c 'converge tier' skills/mf-release/SKILL.md` prints `1`, and `grep -c '^tier = ' skills/mf-cut-change/SKILL.md` prints `1`.
- [x] 2.4 Give `skills/mf-ship/scripts/conduct.py` [D7](design.md#d7)'s converge prompt and `_tier()`, and change the
  prompt assertion and add the tier step in `tests/test_conduct.py`.
  Verify: `grep -c 'Use the generic review' skills/mf-ship/scripts/conduct.py` prints `0`, `grep -c 'def _tier' skills/mf-ship/scripts/conduct.py` prints `1`, and `uv run pytest -q tests/test_conduct.py` reports `10 passed`.

## 3 — Record it

- [x] 3.1 Rewrite D11, amend D14, D40 and D47, and add D49 after D40 in `docs/decisions.md`, per [D9](design.md#d9).
  Verify: `grep -c '^### D49 · ' docs/decisions.md` prints `1`, `grep -c 'Claude Code keeps parallel dispatch' docs/decisions.md` prints `0`, and `uv run --script scripts/metrics/references.py` prints `0`.
- [x] 3.2 Correct `skills/mf-ship/SKILL.md`, `skills/mf-bootstrap/SKILL.md`, `README.md` and `docs/README.md`, per
  [D8](design.md#d8).
  Verify: `grep -c 'code-review\|security-review' README.md skills/mf-bootstrap/SKILL.md skills/mf-ship/SKILL.md` prints `0` for each file.
- [x] 3.3 **HALT CHECK** Measure the converge reading set against [D4](design.md#d4)'s bound, the value at v0.36.
  Verify: `uv run --script scripts/metrics/reading_set.py converge` prints a number no greater than `12143`.

## 4 — Calibrate it

[D10](design.md#d10)'s calibration, run from this worktree under the shell rules: no `cd`, `uv run --directory`
sets each worker's cwd, and the answer key never enters a fixture.

- [x] 4.1 Under `../mf_review_probe/`, build `seeded-standard`, `seeded-high`, `clean-standard` and `clean-high` from
  [D10](design.md#d10)'s files: in each, `git init -b main`, the base files, `git add` and the `chore: base` commit,
  `git -C <fixture> switch -c v0.2_discount`, the change directory, the seeded or clean `cart.py` and
  `tests/test_cart.py`, and the `feat: apply a discount code` commit with its `Change: 0002-discount` trailer.
  Verify: `make -C ../mf_review_probe/seeded-standard gate` exits 0, `make -C ../mf_review_probe/clean-high gate` exits 0, and `git -C ../mf_review_probe/seeded-high log --oneline | wc -l` prints `2`.
- [x] 4.2 For each fixture, `uv run --directory ../mf_review_probe/<fixture> --script ../../minionsfactory/skills/mf-ship/scripts/conduct.py agent --executor claude "Run the skill at ../../v0.37_review_method/skills/mf-converge/SKILL.md for change 0002-discount with tier=<tier>."`,
  `<fixture>` and `<tier>` paired as `seeded-standard` · `standard`, `seeded-high` · `high`, `clean-standard` ·
  `standard`, `clean-high` · `high`.
  Verify: `ls ../mf_review_probe/seeded-standard/.minions/findings/0002-discount_review.md ../mf_review_probe/seeded-high/.minions/findings/0002-discount_security.md ../mf_review_probe/clean-standard/.minions/findings/0002-discount_review.md ../mf_review_probe/clean-high/.minions/findings/0002-discount_security.md` lists all four.
- [x] 4.3 Score each fixture's findings files against [D10](design.md#d10)'s answer key, and write
  `openspec/changes/0042-review-method/evidence/calibration.md` in this worktree, one line per fixture and no absolute
  path: `<fixture>: <n> of 5 · <tier> · workers <n> · duration <s>s · tokens <n|unavailable>` for a seeded fixture,
  with the unmatched rows named; `<fixture>: no blocker` or `<fixture>: <n> blocking — <ids>` for a clean one.
  Verify: `grep -c '^seeded-standard: 5 of 5 · standard' openspec/changes/0042-review-method/evidence/calibration.md` prints `1`, `grep -c '^seeded-high: 5 of 5 · high' openspec/changes/0042-review-method/evidence/calibration.md` prints `1`, and `grep -c '^clean-.*: no blocker$' openspec/changes/0042-review-method/evidence/calibration.md` prints `2`.
- [x] 4.4 Delete the probe: `rm -rf ../mf_review_probe`.
  Verify: `test -e ../mf_review_probe` fails.
