# Review metrics — tasks

Build the settled [design](design.md), one phase at a time. The skill, principle and decision text is the design's,
word for word.

## Progress

- [x] 1 — Read the findings
- [x] 2 — Draw the page
- [x] 3 — Ship the station
- [x] 4 — Run it on this machine

## 1 — Read the findings

- [x] 1.1 Write `skills/mf-review-metrics/scripts/review_metrics.py`'s config loading and reader, per [D1](design.md#d1),
  [D2](design.md#d2) and [D4](design.md#d4).
  Verify: `uv run --script skills/mf-review-metrics/scripts/review_metrics.py --help` exits 0.
- [x] 1.2 Write `tests/test_review_metrics.py`'s `test_no_config_exits_2_naming_the_path`,
  `test_each_era_parses_with_gaps` and `test_the_status_log_gives_duration_tokens_and_the_cap`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_review_metrics.py` reports `3 passed`.
- [x] 1.3 Add `test_the_resolution_log_counts_verified_and_reopened` to `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py` reports `4 passed`.

## 2 — Draw the page

- [x] 2.1 Add the page to `skills/mf-review-metrics/scripts/review_metrics.py`, `chart` and `_STYLE` loaded per
  [D3](design.md#d3), the layout per [D7](design.md#d7).
  Verify: `grep -c 'def chart(' skills/mf-review-metrics/scripts/review_metrics.py` prints `0`, and `grep -c 'mf-build/scripts/metrics.py' skills/mf-review-metrics/scripts/review_metrics.py` prints at least `1`.
- [x] 2.2 Add `test_the_page_draws_charts_and_lists_gaps` and `test_overrides_win_over_the_config` to
  `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py` reports `6 passed`.

## 3 — Ship the station

- [x] 3.1 Write `skills/mf-review-metrics/SKILL.md` and add its row to `README.md`, per [D6](design.md#d6).
  Verify: `grep -c '^name: mf-review-metrics$' skills/mf-review-metrics/SKILL.md` prints `1`, `grep -c 'skills/mf-review-metrics/SKILL.md' README.md` prints `1`, and `grep -c 'mf-review-metrics' AGENTS.md` prints `0`.
- [x] 3.2 Add the exception to `docs/principles.md` and D50 after D43 to `docs/decisions.md`, per [D5](design.md#d5).
  Verify: `grep -c '^### D50 · ' docs/decisions.md` prints `1`, `grep -c 'review-metrics station' docs/principles.md` prints `1`, and `uv run --script scripts/metrics/references.py` prints `0`.

## 4 — Run it on this machine

[D7](design.md#d7)'s live run, from this worktree under the shell rules: no `cd`, no shell variables.

- [x] 4.1 **HALT CHECK** The operator's config `../mf_metrics_probe/review-metrics.toml` exists, written before the run.
  Verify: `grep -c '^repos = ' ../mf_metrics_probe/review-metrics.toml` prints `1`.
- [x] 4.2 `uv run --script skills/mf-review-metrics/scripts/review_metrics.py --config ../mf_metrics_probe/review-metrics.toml`.
  Verify: `grep -c '<section class="repo">' ../mf_metrics_probe/page.html` prints `2`, and `grep -c '<script' ../mf_metrics_probe/page.html` prints `0`.
- [x] 4.3 Write `openspec/changes/0045-review-metrics/evidence/live_run.md`, with no path and no repo name: the
  `repos: <n> · changes: <n>` and `lacked:` lines the script printed, copied.
  Verify: `grep -c '^repos: 2 · changes: ' openspec/changes/0045-review-metrics/evidence/live_run.md` prints `1`.
- [x] 4.4 Delete the probe: `rm -rf ../mf_metrics_probe`.
  Verify: `test -e ../mf_metrics_probe` fails.
