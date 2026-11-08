# Cross-model converge — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [x] 1 — The models line and the plan
- [x] 2 — The checker mailbox
- [ ] 3 — Shadow round 1
- [ ] 4 — The metrics
- [ ] 5 — The record

## 1 — The models line and the plan

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it, with `0096-codex-ready` landed.
  Verify: `grep -n -e 'names an executor' -e '^FINDINGS_KEYS = ' skills/mf-ship/scripts/conduct.py` prints a line for each; `grep -n '^STATIONS = ("build", "converge", "release", "cut")$' skills/mf-plan/scripts/brief_check.py` prints a line; `grep -n 'FAKE_CODEX_ARGV' tests/fake_codex.py` prints a line.
- [x] 1.2 Extend `test_a_hard_brief_is_ready_for_the_cut` and `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`, then
  the grammar of `models` in `skills/mf-plan/scripts/brief_check.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_brief_check.py -k "hard_brief_is_ready or out_of_shape_halts"` reports `2 passed`; `grep -n -e '^HOSTS = ' -e '^CHECKS = ' skills/mf-plan/scripts/brief_check.py` prints a line for each.
- [x] 1.3 Add `test_a_checker_on_another_host_is_planned_and_probed` and edit `test_a_worker_clause_names_its_model_and_effort` in
  `tests/test_conduct.py`, then `_models`, `_worker_clause`, `_shadows`, `_shadow`, `Run.named`, `read_plan`, `executors`, `admit`
  and the clause's caller in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k "another_host_is_planned or worker_clause_names or station_runs_on_its_executor or models_mismatch"` reports `4 passed`; `grep -n -e '^def _shadow(' -e '^def _shadows(' -e 'def named(' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.4 Edit the models line and its paragraph in `skills/mf-plan/SKILL.md`, and *Suggesting models*' paragraph and template in
  `skills/mf-cut-change/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -n 'conformance <host/model> <effort>' skills/mf-plan/SKILL.md` prints a line; `grep -n -e '# shadow = true' -e "from the brief's host" skills/mf-cut-change/SKILL.md` prints a line for each; `grep -n "usually the person's edit" skills/mf-cut-change/SKILL.md` prints nothing.

## 2 — The checker mailbox

- [x] 2.1 Add `tests/fake_claude.py`, `bin/claude` and `FAKE_CLAUDE_ARGV` to the `fake_codex` fixture of `tests/test_conduct.py`,
  and `FAKE_HOST` to `tests/fake_codex.py`, per [D7](design.md#d7).
  Verify: `grep -n 'FAKE_CLAUDE_ARGV' tests/fake_claude.py tests/test_conduct.py` prints a line for each file; `grep -n 'FAKE_HOST' tests/fake_codex.py` prints a line.
- [x] 2.2 Teach `tests/fake_worker.py` the `checker` station for any change, the `shadow-blocks` mode and the fake converge's
  mailbox and shadow clauses, per [D7](design.md#d7).
  Verify: `grep -n -e 'shadow-blocks' -e 'prompt.md' -e 'FAKE_HOST' tests/fake_worker.py` prints a line for each.
- [x] 2.3 Add `test_a_checker_request_is_bounded` to `tests/test_conduct.py`, then the constants of [D4](design.md#d4),
  `serve_requests`, `_answer`, `_open_mailbox` and `work`'s `between` in `skills/mf-ship/scripts/conduct.py`, per
  [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k checker_request_is_bounded` reports `1 passed`; `grep -n -e '^def serve_requests' -e '^def _answer(' -e '^def _open_mailbox' -e '^CHECKER_SPAWNS = 8$' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.4 Add `test_a_codex_checker_runs_through_the_mailbox` and `test_the_checker_command_sends_and_waits` to
  `tests/test_conduct.py`, then the rest of `skills/mf-ship/scripts/conduct.py` that [D4](design.md#d4)–[D6](design.md#d6) and
  [D8](design.md#d8) list for a checker on another host: `checker`, `_mailbox`, `Run.checker` and `argv`'s `mailbox` among it.
  Verify: `uv run pytest -q tests/test_conduct.py -k "runs_through_the_mailbox or checker_command_sends or carries_the_allowlist or codex_probe_runs_a_checker or station_runs_on_its_executor"` reports `5 passed`; `grep -n -e 'add_parser("checker"' -e '^def _mailbox' -e 'def checker(' -e '^CHECKER_WAIT = 100$' skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.5 Edit `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md` and `skills/mf-ship/SKILL.md` as
  [D8](design.md#d8) lists; add `("mf-converge", "../mf-ship/scripts/conduct.py")` to `_METRICS_SCRIPTS` and the expected lists
  of `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`.
  Verify: `grep -n 'conduct.py checker' skills/mf-converge/SKILL.md` prints a line; `grep -n '^executor: ' skills/mf-converge/references/worker.md` prints a line; `grep -n 'checker mailbox' skills/mf-ship/SKILL.md` prints a line; `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.

## 3 — Shadow round 1

- [ ] 3.1 Add `tests/test_overlap.py`, then `skills/mf-converge/scripts/overlap.py`, per [D10](design.md#d10).
  Verify: `uv run pytest -q tests/test_overlap.py` reports `2 passed`; `grep -n -e '^NEAR = 5$' -e '^def overlap(' skills/mf-converge/scripts/overlap.py` prints a line for each.
- [ ] 3.2 Add `test_a_shadow_round_drives_no_fix` over `fake_codex`, then `_open_mailbox` for a shadowed version and
  `Run.checker`'s `_shadow` models for a shadow role in `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5) and
  [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_conduct.py -k "shadow_round_drives_no_fix or runs_through_the_mailbox"` reports `2 passed`.
- [ ] 3.3 Add `## Shadow round 1` and the `shadow` rows of the events and resume tables to `skills/mf-converge/SKILL.md`, per
  [D9](design.md#d9), and `("mf-converge", "scripts/overlap.py")` to `_METRICS_SCRIPTS` and the expected lists of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`.
  Verify: `grep -n -e '^## Shadow round 1$' -e 'scripts/overlap.py' skills/mf-converge/SKILL.md` prints a line for each; `grep -c '^| .shadow. |' skills/mf-converge/SKILL.md` prints `2`; `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.

## 4 — The metrics

- [ ] 4.1 Extend `test_run_metrics_read_cost_and_review_yield` in `tests/test_metric_scripts.py` with a priced Codex
  `converge-conformance` log, then `CHECKERS`, `Version.spawns`, `spent` and `role_tokens` in `scripts/metrics/run.py`, per
  [D11](design.md#d11).
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k cost_and_review_yield` reports `1 passed`; `grep -n '^CHECKERS = ' scripts/metrics/run.py` prints a line.
- [ ] 4.2 Name the `## Resolution log` line's form in `skills/mf-converge/references/verify.md`, per
  [C5](design.md#goals--non-goals).
  Verify: `grep -n -F '<id> <from> → <to>' skills/mf-converge/references/verify.md` prints a line.
- [ ] 4.3 Add `test_the_cross_model_numbers` and edit the tests the design's [Tests](design.md#tests) names in
  `tests/test_review_metrics.py`, then the parts of `skills/mf-review-metrics/scripts/review_metrics.py` [D12](design.md#d12)
  lists, `headline` among them.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k "cross_model_numbers or page_draws_charts or codex_sessions_fill or cost_turns_and_tokens"` reports `4 passed`; `grep -n '^def headline' skills/mf-review-metrics/scripts/review_metrics.py` prints a line.
- [ ] 4.4 Name the headline numbers in *Run* and the role table in *Report* of `skills/mf-review-metrics/SKILL.md`, per
  [D12](design.md#d12).
  Verify: `grep -n -e 'headline' -e 'role, executor' skills/mf-review-metrics/SKILL.md` prints a line for each.

## 5 — The record

- [ ] 5.1 Add D68 after D66 in `docs/decisions.md`, and `D68` to the map's line of *The check loop and the release*, per
  [D13](design.md#d13).
  Verify: `grep -n "^### D68 · Converge's checkers may run on another host, and a shadow round measures it$" docs/decisions.md` prints a line; `grep -n 'D64, D66, D68' docs/decisions.md` prints a line.
- [ ] 5.2 Amend D11, D40, D41, D47, D49, D50 and D64 in `docs/decisions.md`, per [D13](design.md#d13), each new phrase on one line.
  Verify: `grep -n 'on Codex every worker runs on the conductor' docs/decisions.md` prints nothing; `grep -n -e 'a checker its executor too' -e "starts on the conductor's request" -e 'each host the brief names as its' -e "absent meaning converge's" -e 'and a converge worker its checker mailbox' -e 'a shadow file drives nothing' -e 'per role, executor and model, four headline numbers' -e "every worker on the conductor's host" docs/decisions.md` prints a line for each.
- [ ] 5.3 Edit *Entry points* and *Trust boundaries* in `THREAT_MODEL.md`, and the queue item in `docs/principles.md`, per
  [D13](design.md#d13), each new phrase on one line.
  Verify: `grep -n -e 'Checker requests, in the home' -e 'as it reads a subagent' -e "a converge worker's also in its checker mailbox" THREAT_MODEL.md` prints a line for each; `grep -n 'checker mailbox, which that worker writes' docs/principles.md` prints a line.
