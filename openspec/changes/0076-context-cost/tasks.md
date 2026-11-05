# Context cost — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The cost reader
- [x] 2 — No MCP server at a worker's start
- [ ] 3 — The worker reference
- [ ] 4 — The metric

## 1 — The cost reader

- [x] 1.1 Add `_cost_logs` and `cost_table` to `skills/mf-review-metrics/scripts/review_metrics.py`, and name cost in
  `skills/mf-review-metrics/SKILL.md`, per [D1](design.md#d1); add `_run_log` and `test_run_logs_give_cost_turns_and_tokens_per_station`
  to `tests/test_review_metrics.py`, and extend `test_the_page_draws_charts_and_lists_gaps`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k "run_logs_give_cost or page_draws_charts_and_lists_gaps"` reports `2 passed`.
- [x] 1.2 Amend D50 in `docs/decisions.md`, per [D5](design.md#d5).
  Verify: `grep -n 'status logs and run logs' docs/decisions.md` prints a line.

## 2 — No MCP server at a worker's start

- [x] 2.1 Add `--strict-mcp-config` to the Claude branch of `argv` in `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2);
  extend `test_a_claude_worker_starts_in_the_sandbox` in `tests/test_conduct.py`.
  Verify: `grep -n 'strict-mcp-config' skills/mf-ship/scripts/conduct.py` prints a line, and
  `uv run pytest -q tests/test_conduct.py -k "claude_worker_starts_in_the_sandbox or worker_carries_the_allowlist"` reports `2 passed`.
- [x] 2.2 Amend D51's *Accepts* in `docs/decisions.md` and `THREAT_MODEL.md`'s worker line, per [D5](design.md#d5).
  Verify: `grep -n 'starts no MCP server' docs/decisions.md` prints a line, and `grep -n 'no MCP server' THREAT_MODEL.md` prints a line.

## 3 — The worker reference

- [ ] 3.1 Move the worker's parts of `skills/mf-converge/SKILL.md` into `skills/mf-converge/references/worker.md`, link them from
  `SKILL.md`, tell the conductor to load it, repoint every anchor to a moved heading, and point `generic-review.md` and
  `generic-security.md` at it, their Step 5 and Step 7 citations included, per [D3](design.md#d3).
  Verify: `grep -n '^## The card' skills/mf-converge/references/worker.md` prints a line, and
  `grep -L '^## The card' skills/mf-converge/SKILL.md` prints `skills/mf-converge/SKILL.md`.
- [ ] 3.2 Point the readers [D3](design.md#d3) names at the worker reference: the card-owner, test-rule and resource scans in
  `tests/test_skills.py`, the Priority regex in `tests/test_review_metrics.py`, and the prose in `skills/mf-build/SKILL.md` and
  `review_metrics.py`'s comment.
  Verify: `uv run pytest -q tests/test_skills.py tests/test_review_metrics.py` exits 0.

## 4 — The metric

- [ ] 4.1 Add the `worker` set, `worker.md` in the `converge` set and the docstring's `worker` to `scripts/metrics/reading_set.py`, and
  `converge-worker-reading-set` to `metrics/catalogue.toml`, per [D4](design.md#d4); extend `test_reading_sets_count_words` in
  `tests/test_metric_scripts.py`.
  Verify: `grep -n "Converge worker's reading set" metrics/catalogue.toml` prints a line, and
  `uv run pytest -q tests/test_metric_scripts.py -k reading_sets_count_words` reports `1 passed`.
