# Codex limits — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [x] 1 — The limit data
- [x] 2 — The probe
- [x] 3 — The mailbox fallback
- [x] 4 — The record
- [ ] 5 — The linked worktree
- [ ] 6 — The request id and the record of decisions
- [ ] 7 — The real Codex check **HUMAN**

## 1 — The limit data

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `grep -n -e '^def usage_limit(log: Path) -> str:' -e '^def _codex_limit(' -e '^CHECKER_WAIT = 100$' -e '^def _shadow(' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n '"thread_id": "fake"' tests/fake_codex.py` prints a line.
- [x] 1.2 Add the autouse fixture `_no_codex_sessions` and `test_the_codex_limit_data_is_read_from_its_rollout` to
  `tests/test_conduct.py`, then the constants, `Window`, `_codex_home`, `_thread_id`, `_rollout`, `_windows`, `_next_clock`,
  `_reset_at` and `_headroom` in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k codex_limit_data_is_read` reports `1 passed`; `grep -n -e '^LIMIT_WAIT = 900$' -e '^HEADROOM = 90$' -e '^def _thread_id(' -e '^def _reset_at(' -e '^def _headroom(' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'def _no_codex_sessions' tests/test_conduct.py` prints a line.

## 2 — The probe

- [x] 2.1 Add `test_a_usage_limit_at_the_probe_is_no_refusal`, joining versions included, and edit
  `test_a_checker_on_another_host_is_planned_and_probed`'s `probe_for` stub, in `tests/test_conduct.py`; then the `Run`
  members [D2](design.md#d2) lists before `hold_limited`, in `skills/mf-ship/scripts/conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "usage_limit_at_the_probe or new_executor_is_probed_mid_run or codex_probe_runs_a_checker or another_host_is_planned"` reports `4 passed`; `grep -n -e 'def limited_until(' -e 'def on_stations(' -e 'def limited_reason(' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.2 Extend `test_a_usage_limit_at_the_probe_is_no_refusal` with `hold_limited`, then `Run.hold_limited`, the
  start's `held` and `take`'s return in `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_conduct.py -k "usage_limit_at_the_probe or station_runs_on_its_executor or probe_halts_on_a_write_out"` reports `3 passed`; `grep -n 'def hold_limited(' skills/mf-ship/scripts/conduct.py` prints a line.

## 3 — The mailbox fallback

- [x] 3.1 Extend `test_a_checker_request_is_bounded` as D3's *The refusal* says, with `checker-sleep` in `tests/fake_worker.py`;
  then `work`'s and `Run.worker`'s `timeout`, the `deadline` of `Run.spawn`, `Run.server` and `Run.checker`, and the
  refusal, in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k "checker_request_is_bounded or carries_the_allowlist or run_halts_on_a_timeout"` reports `3 passed`; `grep -n -F "refused: converge's time is spent" skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.2 Add `test_a_limited_checker_falls_back_to_claude`, with the cases D3's *The fallback's test* names, to
  `tests/test_conduct.py`; then `Run.codex_ready`, `Run.checker`'s fallback and shadow rule, and `_answer`'s `fallback`,
  per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k "limited_checker_falls_back or runs_through_the_mailbox or shadow_round_drives_no_fix"` reports `3 passed`; `grep -n -e 'def codex_ready(' -e '^FALLBACK = "fallback: codex usage limit"$' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 3.3 Add `test_a_usage_limit_converge_halt_gets_no_rescue` to `tests/test_conduct.py`, then the usage-limit test in
  `Run.rescue` and `Run.supervise`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "usage_limit_converge_halt or rescue_amends_at_amend_needed or rescue_diagnoses_a_decision_halt"` reports `3 passed`.
- [x] 3.4 Add `test_a_codex_limit_at_the_probe_halts_its_stations_alone`, marked `slow`, to `tests/test_conduct.py`, per
  [D2](design.md#d2) and [D3](design.md#d3); its commit body says why no run in the suite reaches its state (`T2`).
  Verify: `uv run pytest -q tests/test_conduct.py -k "limit_at_the_probe_halts_its_stations"` reports `1 passed`.
- [x] 3.5 Edit *A mailbox role* and the `verdicts` row of the events table in `skills/mf-converge/SKILL.md`, per
  [D3](design.md#d3) and [C17](design.md#goals--non-goals).
  Verify: `grep -n -e 'tokens its answer names' -e 'fallback: codex usage limit' -e 'stopped by a usage limit' skills/mf-converge/SKILL.md` prints a line for each.

## 4 — The record

- [x] 4.1 Add `test_a_mailbox_checker_is_stamped_and_counted` to `tests/test_conduct.py`, and `FAKE_CODEX_ROLLOUT` and
  `FAKE_CODEX_USED` to `tests/fake_codex.py`, then `tokens_of`, `_stamp`, `_answer`'s `tokens` and the quota line of
  `Run.worker` in `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k "mailbox_checker_is_stamped or limited_checker_falls_back or checker_request_is_bounded"` reports `3 passed`; `grep -n -e '^def tokens_of(' -e '^def _stamp(' -e '"mf.quota"' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'FAKE_CODEX_ROLLOUT' tests/fake_codex.py` prints a line.
- [x] 4.2 Edit the frontmatter block of `skills/mf-converge/references/worker.md` and the comment above `FINDINGS_KEYS` in
  `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Verify: `grep -n '^tokens: <int' skills/mf-converge/references/worker.md` prints a line; `grep -n 'save .tokens., which .conduct.py. stamps' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 4.3 Extend `test_run_metrics_read_cost_and_review_yield` in `tests/test_metric_scripts.py`, then `_spent`,
  `Version.quota` and `METRICS` in `scripts/metrics/run.py`, and the `codex-window-5h` and `codex-window-week` tables in
  `metrics/catalogue.toml`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_metric_scripts.py` exits 0; `grep -n 'def quota(' scripts/metrics/run.py` prints a line; `grep -n -e '^id = "codex-window-5h"$' -e '^id = "codex-window-week"$' metrics/catalogue.toml` prints a line for each.
- [x] 4.4 Add `test_the_claude_rows_price_a_worker` to `tests/test_review_metrics.py`, then the rows and the `Why:` of
  `skills/mf-review-metrics/prices.toml`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_review_metrics.py -k claude_rows_price` reports `1 passed`; `grep -n -e '^"claude-opus-5-5" = ' -e '^"claude-sonnet-5-5" = ' skills/mf-review-metrics/prices.toml` prints a line for each.

## 5 — The linked worktree

- [ ] 5.1 Extend `test_a_worker_carries_the_allowlist_and_a_denial_is_named` in `tests/test_conduct.py` with a linked
  tree's folder under `worktrees/`, then `_gitdirs` and `argv`'s Codex roots, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k "carries_the_allowlist or swapped_root_halts"` reports `2 passed`; `grep -n '^def _gitdirs(' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 5.2 Add `test_a_program_key_in_a_worktree_config_halts` to `tests/test_conduct.py`, then `_config_held`, per
  [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k "worktree_config_halts or no_hook_runs_in_a_worker or mixed_key_list"` reports `3 passed`; `grep -n 'config.worktree' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 5.3 Extend `test_the_codex_probe_runs_a_checker` with `tree-silent`, and teach `tests/fake_worker.py` the tree step and
  `tree-silent`, then `TREE_PROBE`, `check_tree` and `probe`'s linked tree in `skills/mf-ship/scripts/conduct.py`, per
  [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k "codex_probe_runs_a_checker or usage_limit_at_the_probe or limit_at_the_probe_halts_its_stations"` reports `3 passed`; `grep -n -e '^TREE_PROBE = ' -e '^def check_tree(' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n 'tree-silent' tests/fake_worker.py` prints a line.
- [ ] 5.4 Add `test_a_linked_tree_writes_under_the_codex_sandbox` to `tests/test_conduct.py`, marked `slow` and skipped
  unless `MF_REAL_CODEX=1` and `codex` is on `PATH`, per [D6](design.md#d6) and [C14](design.md#goals--non-goals).
  Verify: `uv run pytest -q tests/test_conduct.py -k linked_tree_writes_under` reports `1 skipped`.

## 6 — The request id and the record of decisions

- [ ] 6.1 Rewrite `test_the_checker_command_sends_and_waits` as D7's *The CLI's test* says, and give
  `test_a_checker_request_is_bounded`'s requests their id, in `tests/test_conduct.py`; then `REQUEST_ID`, `checker`,
  `serve_requests`, `Run.server` and `Run.checker`'s `request`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k "checker_command_sends or checker_request_is_bounded or runs_through_the_mailbox or shadow_round_drives_no_fix or mailbox_checker_is_stamped"` reports `5 passed`; `grep -n -e '^REQUEST_ID = ' -e 'names no request' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 6.2 Add D72 after D70's block in `docs/decisions.md`, and `D72` after `D70` on the map's *Repo conventions* line, per
  [D8](design.md#d8).
  Verify: `grep -n '^### D72 · A Codex usage limit falls back, and halts only what runs on Codex$' docs/decisions.md` prints a line; `grep -n 'D67, D70, D72' docs/decisions.md` prints a line.
- [ ] 6.3 Amend D47, D51, D53, D67 and D68 in `docs/decisions.md`, per [D8](design.md#d8), each new phrase on one line.
  Verify: `grep -n -e 'a probe a usage limit stopped, only the versions with a station on its executor' -e "a Codex worker writes each linked worktree's folder" -e 'a converge halt naming one, a' -e "writes a linked worktree's index" -e 'which holds the fitted Claude rows' -e "within converge's remaining time, or on Claude while Codex is limited" docs/decisions.md` prints a line for each.
- [ ] 6.4 Edit *Trust boundaries* and *Entry points* in `THREAT_MODEL.md`, per [D8](design.md#d8), each new phrase on one line.
  Verify: `grep -n -e 'a forged .thread_id. reads another Codex rollout' -e 'and appends a Codex log' -e "each checker within converge's remaining time" -e "a Codex worker's also in each linked" THREAT_MODEL.md` prints a line for each.
- [ ] 6.5 Edit the diagram and the say-once paragraph of `skills/mf-ship/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n -e 'codex limited until <time>' -e 'a usage limit at it halts only the versions' -e 'a Codex checker runs on Claude' skills/mf-ship/SKILL.md` prints a line for each.

## 7 — The real Codex check

The person runs the real-Codex test in their own terminal, outside any sandbox, at the worktree's root, per
[C14](design.md#goals--non-goals).

- [ ] 7.1 Run the test against the installed `codex`, writing its summary into the change directory:
  ```sh
  MF_REAL_CODEX=1 uv run pytest -q tests/test_conduct.py -k linked_tree_writes_under_the_codex_sandbox > openspec/changes/0104-codex-limits/real-codex.txt
  ```
  Verify: `grep -n '1 passed' openspec/changes/0104-codex-limits/real-codex.txt` prints a line.
