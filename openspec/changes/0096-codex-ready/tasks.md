# Codex ready — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [ ] 1 — Config isolation
- [ ] 2 — JSON events
- [ ] 3 — The swap window
- [ ] 4 — The probe and the record

## 1 — Config isolation

- [ ] 1.1 **HALT CHECK** `argv`'s Codex branch and its argv test stand as the design's [Context](design.md#context) reads them.
  Verify: `grep -n -F -e '"workspace-write"' -e 'exclude_tmpdir_env_var=true' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n '^def test_a_worker_carries_the_allowlist_and_a_denial_is_named' tests/test_conduct.py` prints a line.
- [ ] 1.2 Add `tests/fake_codex.py` and the `fake_codex` fixture of `tests/test_conduct.py`, per [D2](design.md#d2).
  Verify: `grep -n 'FAKE_CODEX_ARGV' tests/fake_codex.py tests/test_conduct.py` prints a line for each file.
- [ ] 1.3 Add `test_a_codex_worker_starts_on_mf_settings_alone` and extend `test_a_worker_carries_the_allowlist_and_a_denial_is_named`
  for `--ignore-user-config` and `--json`, then add them to `argv` in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k "starts_on_mf_settings_alone or carries_the_allowlist"` reports `2 passed`; `grep -n -F '"--ignore-user-config", "--json"' skills/mf-ship/scripts/conduct.py` prints a line.

## 2 — JSON events

- [ ] 2.1 Add `test_a_codex_log_reads_as_json`, then the Codex branches of `denials`, `usage_limit` and `mcp_started` in
  `skills/mf-ship/scripts/conduct.py`, and `mcp_started`'s docstring, per [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "codex_log_reads_as_json or usage_limit_is_named or probe_halts_on_a_write_out or carries_the_allowlist"` reports `4 passed`; `grep -n "as Codex's, passes" skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 2.2 Extend `test_a_station_runs_on_its_executor` to read the Codex converge log's spawn line, then write it in `Run.spawn`,
  per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k station_runs_on_its_executor` reports `1 passed`; `grep -n '"mf.spawn"' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.3 Add `skills/mf-review-metrics/prices.toml`, its `[models]` table empty under the comment, per [D6](design.md#d6).
  Verify: `grep -n '^\[models\]$' skills/mf-review-metrics/prices.toml` prints a line.
- [ ] 2.4 Extend `test_run_metrics_read_cost_and_review_yield` with a priced Codex converge log and one whose model has no row,
  then `PRICES`, `_spent` and `Version.spent` in `scripts/metrics/run.py` and the `prices` path of `_reader`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k cost_and_review_yield` reports `1 passed`; `grep -n '^PRICES = ' scripts/metrics/run.py` prints a line.
- [ ] 2.5 Extend `test_run_logs_give_cost_turns_and_tokens_per_station` with a priced Codex cell and a gap, then `PRICES`,
  `_results` and `_spent` in `skills/mf-review-metrics/scripts/review_metrics.py`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_review_metrics.py -k cost_turns_and_tokens_per_station` reports `1 passed`; `grep -n '^PRICES = ' skills/mf-review-metrics/scripts/review_metrics.py` prints a line.

## 3 — The swap window

- [ ] 3.1 Add `test_a_swapped_root_halts_a_codex_spawn` — the worktree `argv` gets as `cwd`, then a cutter's brief folder, each
  swapped for a link to a sibling folder — and extend `test_a_worker_carries_the_allowlist_and_a_denial_is_named` for `exclude_slash_tmp`, then
  `_unswapped` and the flag in `argv` of `skills/mf-ship/scripts/conduct.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k "swapped_root_halts_a_codex_spawn or carries_the_allowlist"` reports `2 passed`; `grep -n -e '^def _unswapped' -e 'exclude_slash_tmp=true' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 3.2 Rewrite `reach`'s docstring in `skills/mf-ship/scripts/conduct.py`, per [D7](design.md#d7).
  Verify: `grep -n 'no listed path can be' skills/mf-ship/scripts/conduct.py` prints nothing.

## 4 — The probe and the record

- [ ] 4.1 Add `CHECKER_PROBE`, `FINDINGS_KEYS` and `checker_fixture` to `skills/mf-ship/scripts/conduct.py`, per [D8](design.md#d8).
  Verify: `grep -n -e '^CHECKER_PROBE = ' -e '^FINDINGS_KEYS = ' -e '^def checker_fixture' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 4.2 Teach `tests/fake_worker.py` the checker prompt and the `checker-silent` mode, per [D9](design.md#d9).
  Verify: `grep -n 'checker-silent' tests/fake_worker.py` prints a line.
- [ ] 4.3 Add `test_the_codex_probe_runs_a_checker` over `fake_codex`, and edit the call lists the design's [Tests](design.md#tests)
  names, then `check_checker`, `probe_checker` and `Run.probe`'s Codex path, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_conduct.py -k "codex_probe_runs_a_checker or probed_mid_run or station_runs_on_its_executor or probe_halts_on_a_write_out"` reports `4 passed`.
- [ ] 4.4 Add D67 after D51 in `docs/decisions.md`, and `D67` to the map's *Repo conventions* line, per [D10](design.md#d10).
  Verify: `grep -n "^### D67 · A Codex worker starts on MF's settings, logs JSON and is proved by a checker$" docs/decisions.md` prints a line; `grep -n 'D60, D61, D67' docs/decisions.md` prints a line.
- [ ] 4.5 Amend D51 and D47 in `docs/decisions.md`, per [D10](design.md#d10), each new phrase on one line.
  Verify: `grep -n 'until a change sets them empty' docs/decisions.md` prints nothing; `grep -n -e 'loads no user config' -e 'with a checker on a fixture' docs/decisions.md` prints a line for each.
- [ ] 4.6 Edit *Trust boundaries* and *Known gaps* in `THREAT_MODEL.md`, per [D10](design.md#d10), each new phrase on one line.
  Verify: `grep -n -e 'still starts the operator' -e 'until a change sets them' THREAT_MODEL.md` prints nothing; `grep -n -e 'ignore-user-config' -e 'never a stage' -e 'once or per command' THREAT_MODEL.md` prints a line for each.
- [ ] 4.7 Add the checker to the probe sentence of `skills/mf-ship/SKILL.md`, per [D10](design.md#d10).
  Verify: `grep -n 'one checker on a fixture' skills/mf-ship/SKILL.md` prints a line.
