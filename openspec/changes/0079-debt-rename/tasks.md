# Debt rename — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The file, the lock and the key
- [x] 2 — The word
- [x] 3 — The move at a run's start

## 1 — The file, the lock and the key

- [x] 1.1 Rename the debt's file, lock, status-log event and word in `skills/mf-ship/scripts/conduct.py` and
  `skills/mf-converge/SKILL.md`, and the key, file, lock, word and diagram in `skills/mf-release/SKILL.md`, each reader taking the old name too, per
  [D1](design.md#d1); extend `test_a_stale_lock_is_cleared_and_converge_resumes` and `test_a_fix_after_a_cap_halt_converges_afresh`
  in `tests/test_conduct.py`.
  Verify: `grep -n 'debt.lock' skills/mf-ship/scripts/conduct.py` prints a line, `grep -n 'Step 9 — Write the debt' skills/mf-converge/SKILL.md`
  prints a line, and `uv run pytest -q tests/test_conduct.py -k "stale_lock_is_cleared_and_converge_resumes or fix_after_a_cap_halt_converges_afresh"` reports `2 passed`.
- [x] 1.2 Read `debt.md` and either key in `scripts/metrics/run.py`, and either wording in
  `skills/mf-review-metrics/scripts/review_metrics.py`, per [D1](design.md#d1); extend `test_run_metrics_read_cost_and_review_yield`
  in `tests/test_metric_scripts.py` and `test_the_status_log_gives_duration_tokens_and_the_cap` in `tests/test_review_metrics.py`.
  Verify: `grep -n 'to (?:backlog|debt)' skills/mf-review-metrics/scripts/review_metrics.py` prints a line, and
  `uv run pytest -q tests/test_metric_scripts.py tests/test_review_metrics.py -k "run_metrics_read_cost_and_review_yield or status_log_gives_duration"` reports `2 passed`.

## 2 — The word

- [x] 2.1 Move `scripts/metrics/backlog.py` to `scripts/metrics/debt.py`, point the catalogue entry `open-backlog-cards` at it with the
  title "Open debt cards", retitle `debt-added` and `debt-paid`, and load it as `debt` in `tests/test_metric_scripts.py`, per
  [D2](design.md#d2).
  Verify: `grep -n 'scripts/metrics/debt.py' metrics/catalogue.toml` prints a line, and
  `uv run pytest -q tests/test_metric_scripts.py -k "unavailable_without_a_backlog or read_from_the_primary_run_directory"` reports `2 passed`.
- [x] 2.2 Rename the word in D15 and D16 of `docs/decisions.md`, `CONTRIBUTING.md`'s D16 link, `docs/principles.md`, `AGENTS.md`,
  `THREAT_MODEL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/references/worker.md` and
  `skills/mf-converge/references/generic-review.md`, per [D2](design.md#d2).
  Verify: `grep -n "card in the repo's debt file" docs/decisions.md` prints a line, `grep -n 'debt: \[<ids>\]' skills/mf-plan/SKILL.md`
  prints a line, and `grep -L -i 'backlog' AGENTS.md CONTRIBUTING.md` prints `AGENTS.md` and `CONTRIBUTING.md`.

## 3 — The move at a run's start

- [x] 3.1 Add `Run.migrate_debt`, called in `ship()` before `_clear_stale_lock`, in `skills/mf-ship/scripts/conduct.py`, per
  [D3](design.md#d3); add `test_a_run_moves_an_old_backlog_to_the_debt` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k run_moves_an_old_backlog_to_the_debt` reports `1 passed`.
