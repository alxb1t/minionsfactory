# Remove the high tier — tasks

Build the settled [design](design.md), one phase at a time. The skill and decision text is the design's, word for word.

## Progress

- [x] 1 — Converge
- [ ] 2 — The run
- [ ] 3 — The metrics
- [ ] 4 — The record

## 1 — Converge

- [x] 1.1 Rewrite *The tier and the workers* and the tier lines in `skills/mf-converge/SKILL.md`, edit
  `references/generic-review.md` and `references/generic-security.md`, and delete `references/high-tier.md`, per [D1](design.md#d1).
  Verify: `grep -c -E 'tier=standard|tier: standard|high-tier' skills/mf-converge/SKILL.md` prints `0`, and
  `grep -c 'parameter was removed' skills/mf-converge/SKILL.md` prints `1`.

## 2 — The run

- [ ] 2.1 Remove `TIERS` and `_tier` from `skills/mf-ship/scripts/conduct.py` and give the converge prompt `{grant}`; edit
  `tests/fake_worker.py`, `tests/drill_resume.py` and `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, per [D2](design.md#d2).
  Verify: `grep -c -E 'TIERS|def _tier' skills/mf-ship/scripts/conduct.py` prints `0`, and
  `uv run pytest -q tests/test_conduct.py -k 'carries_the_allowlist or grant_buys_one_round'` reports `2 passed`.
- [ ] 2.2 Edit `skills/mf-ship/SKILL.md` and `skills/mf-cut-change/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -c 'tier the cut chose' skills/mf-ship/SKILL.md` prints `0`, and
  `grep -c 'tier = "standard"' skills/mf-cut-change/SKILL.md` prints `0`.

## 3 — The metrics

- [ ] 3.1 Drop the tier dimension from `skills/mf-review-metrics/scripts/review_metrics.py` and its `SKILL.md`, and edit
  `test_each_era_parses_with_gaps` and `test_the_page_draws_charts_and_lists_gaps`, per [D3](design.md#d3).
  Verify: `grep -c 'tier' skills/mf-review-metrics/scripts/review_metrics.py` prints `0`, and
  `uv run pytest -q tests/test_review_metrics.py` exits 0.

## 4 — The record

- [ ] 4.1 Amend D49, D47 and D50 in `docs/decisions.md`, and edit `README.md` and `skills/mf-release/SKILL.md`, per
  [D4](design.md#d4).
  Verify: `grep -c 'One review method, one depth' docs/decisions.md` prints `1`, and
  `git grep -n -E 'tier=high|high-tier|TIERS|tier × model' -- skills tests docs README.md` prints nothing.
