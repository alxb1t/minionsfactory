# Converge roles — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `0094-lighter-converge`
merges in before this build: find each of its symbols and sections by name, never by line number.

## Progress

- [ ] 1 — The roles
- [ ] 2 — The debt and the diff
- [ ] 3 — Verify and the defaults
- [ ] 4 — The record

## 1 — The roles

- [ ] 1.1 **HALT CHECK** 0094's worker tables and `surfaces.py` stand in the tree this build starts from.
  Verify: `grep -n -e '^WORKERS = ' -e 'def _worker_clause' skills/mf-ship/scripts/conduct.py` prints a line for each; `git grep -n 'surfaces: no surface' -- skills/mf-converge/scripts/surfaces.py` prints a line.
- [ ] 1.2 Rename the roles in `tests/fake_worker.py` and the role tests of `tests/test_conduct.py` the design's `## Tests` names,
  extending the move and rescue tests, then `ROLES`, `BLOCKS`, `OLD_LAYOUT`, `OLD_ROLES`, `_old_files`, `migrate_layout`, `_category`,
  `_security_blocks`, `_security_held` and `report` in `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2).
  Verify: `grep -n '^OLD_ROLES = ' skills/mf-ship/scripts/conduct.py` prints a line; `uv run pytest -q tests/test_conduct.py -k "moves_an_old_layout or rescue_amends_at_amend_needed or ships_past_a_slow_one or drift_amend or supervisor_amend_outside_the_change or dead_converge_halts or small_cap_is_granted or fix_after_a_cap_halt or only_on_disk_evidence or release_cut_short_is_recovered or amend_past_the_judged_head"` reports `11 passed`.
- [ ] 1.3 Edit `tests/test_surfaces.py`, then `skills/mf-converge/scripts/surfaces.py`'s argument, reasons and docstring, per
  [D3](design.md#d3).
  Verify: `git grep -n 'adversarial card' -- skills/mf-converge/scripts/surfaces.py` prints a line; `uv run pytest -q tests/test_surfaces.py` reports `2 passed`.
- [ ] 1.4 Edit 0094's worker tests and rename its surfaces run test in `tests/test_conduct.py` as the design's `## Tests` says,
  then `WORKERS`, `OLD_WORKERS` and `_models` in `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_conduct.py -k "worker_clause or station_runs_on_its_executor or plan_is_read_once or carries_the_allowlist or takes_adversarial_by_rule"` reports `5 passed`.
- [ ] 1.5 Extend the old-layout tests of `tests/test_gate_check.py` and `tests/test_integrate.py`, then `OLD_LAYOUT` in
  `skills/mf-converge/scripts/gate_check.py` and `skills/mf-integrate/scripts/integrate.py`, and `unready`, per [D3](design.md#d3).
  Verify: `grep -n -F 'changes/{}/security.md' skills/mf-converge/scripts/gate_check.py skills/mf-integrate/scripts/integrate.py` prints a line for each file; `uv run pytest -q tests/test_gate_check.py tests/test_integrate.py -k "old_layout or lowest_ready_id"` reports `3 passed`.
- [ ] 1.6 Edit `test_run_metrics_read_cost_and_review_yield`, then `ROLES` and `ROLE` in `scripts/metrics/run.py` and the role
  entries of `metrics/catalogue.toml`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_metric_scripts.py -k cost_and_review_yield` reports `1 passed`; `grep -c '^id = "conformance-' metrics/catalogue.toml` prints `3`.
- [ ] 1.7 Extend the review-metrics tests the design's `## Tests` names, then
  `skills/mf-review-metrics/scripts/review_metrics.py`, per [D4](design.md#d4).
  Verify: `grep -n '^OLD_ROLES = ' skills/mf-review-metrics/scripts/review_metrics.py` prints a line; `uv run pytest -q tests/test_review_metrics.py -k "both_layouts or tokens_are_read_per_role or codex_sessions_fill"` reports `3 passed`.
- [ ] 1.8 Add `test_the_packets_hold_what_each_role_reads` to `tests/test_skills.py`; `git mv` both references and rewrite them,
  link them from *The workers* in `skills/mf-converge/SKILL.md`, and rename the path in `reading_set.py` and its test, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_skills.py tests/test_metric_scripts.py -k "packets_hold or role_references_resolve or reading_sets"` reports `3 passed`.
- [ ] 1.9 Rename the roles in `skills/mf-converge/references/worker.md`, per [D5](design.md#d5).
  Verify: `grep -n '^## Conformance and adversarial$' skills/mf-converge/references/worker.md` prints a line.
- [ ] 1.10 Rename the roles in `skills/mf-converge/SKILL.md` and add the old names to its old-layout bullet, per
  [D6](design.md#d6).
  Verify: `grep -n -i -e 'review and security' -e "review's" -e "security's" -e 'review-and-security' -e 'review=' -e '<change-id>/security.md' -e 'review dispatch' -e 'security head' skills/mf-converge/SKILL.md` prints nothing.
- [ ] 1.11 Rename the paths and preconditions in `skills/mf-release/SKILL.md` and add the old names to its old-layout list, per
  [D6](design.md#d6).
  Verify: `grep -n '\*\*conformance is clean\*\*' skills/mf-release/SKILL.md` prints a line.
- [ ] 1.12 Rename the roles in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`, and add the old names to the
  build's old-layout list, per [D6](design.md#d6).
  Verify: `grep -n 'the conformance and adversarial files' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints a line for each file.
- [ ] 1.13 Rename the read tables of `skills/mf-rescue/SKILL.md` and `skills/mf-supervise/SKILL.md`, adding the security-card
  line under each, and add the old names to the old-layout list of `skills/mf-integrate/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'adversarial.md' skills/mf-rescue/SKILL.md skills/mf-supervise/SKILL.md` prints a line for each file; `grep -n 'changes/<change-id>/review.md' skills/mf-integrate/SKILL.md` prints a line.
- [ ] 1.14 Rename the roles in `docs/principles.md`, per [D7](design.md#d7).
  Verify: `grep -n -i -e 'review and security' -e 'review ‖ security' -e "review's" docs/principles.md` prints nothing.
- [ ] 1.15 Rename the roles in `docs/decisions.md`, D12's heading and bold text among them, per [D7](design.md#d7).
  Verify: `grep -n '^### D12 · Conformance, adversarial and simplify are kept apart$' docs/decisions.md` prints a line; `grep -n -i -e 'review and security' -e 'review ‖ security' -e "review's" -e "security's" -e 'converge\.review' docs/decisions.md` prints nothing.
- [ ] 1.16 Rename the roles in `AGENTS.md`'s opening note, `README.md`, `docs/README.md`, `THREAT_MODEL.md` and
  `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`, per [D7](design.md#d7), "adversarial head" on one line.
  Verify: `grep -n 'conformance ‖ adversarial' README.md docs/README.md` prints a line for each file; `grep -n -e 'adversarial head' -e 'references/generic-adversarial.md' THREAT_MODEL.md` prints a line for each.

## 2 — The debt and the diff

- [ ] 2.1 Add `skills/mf-converge/scripts/debt_match.py`, per [D8](design.md#d8), and `tests/test_debt_match.py`, as the
  design's `## Tests` names its tests.
  Verify: `uv run pytest -q tests/test_debt_match.py` reports `2 passed`.
- [ ] 2.2 Add `debt_match.py` to `_METRICS_SCRIPTS` and its `not named` line to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`, per [D8](design.md#d8).
  Verify: `grep -n '"scripts/debt_match.py"' tests/test_skills.py` prints a line.
- [ ] 2.3 Run `debt_match.py` after `bundle.py` in Step 2 and Step 6's re-freeze of `skills/mf-converge/SKILL.md`, and drop
  Step 3's debt bullet, per [D9](design.md#d9).
  Verify: `grep -n 'scripts/debt_match.py' skills/mf-converge/SKILL.md` prints a line.
- [ ] 2.4 Edit the repeat rule in `skills/mf-converge/references/worker.md`, add the bundle and the read-once rule to the
  packets of both references, and extend `test_the_packets_hold_what_each_role_reads`, per [D9](design.md#d9), the section's
  name on one line.
  Verify: `grep -n "Debt cards on the diff's files" skills/mf-converge/references/worker.md` prints a line; `uv run pytest -q tests/test_skills.py -k packets_hold` reports `1 passed`.

## 3 — Verify and the defaults

- [ ] 3.1 Add `skills/mf-converge/scripts/open_cards.py`, per [D10](design.md#d10), and `tests/test_open_cards.py`, as the
  design's `## Tests` names its tests.
  Verify: `uv run pytest -q tests/test_open_cards.py` reports `2 passed`.
- [ ] 3.2 Add `open_cards.py` to `_METRICS_SCRIPTS` and its `not named` line to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`, per [D10](design.md#d10).
  Verify: `grep -n '"scripts/open_cards.py"' tests/test_skills.py` prints a line.
- [ ] 3.3 Add `skills/mf-converge/references/verify.md`, move `worker.md`'s verify pass into it, and point each role
  reference's *Verify freshly* at it, per [D10](design.md#d10).
  Verify: `grep -n '](verify.md)' skills/mf-converge/references/worker.md` prints a line.
- [ ] 3.4 Add the open-cards run and the verify dispatch to Step 7 of `skills/mf-converge/SKILL.md`, and the catch-up's judge
  round to its catch-up round, per [D10](design.md#d10).
  Verify: `grep -n -e 'scripts/open_cards.py' -e '](references/verify.md)' skills/mf-converge/SKILL.md` prints a line for each; `uv run pytest -q tests/test_skills.py -k role_references_resolve` reports `1 passed`.
- [ ] 3.5 Move conformance to the mid tier in the Converge bullet of `skills/mf-cut-change/SKILL.md`, in D64 of
  `docs/decisions.md` and in `README.md`'s converge sentence, per [D11](design.md#d11), each phrase on one line.
  Verify: `grep -n 'conformance on the mid tier · high' skills/mf-cut-change/SKILL.md` prints a line.

## 4 — The record

- [ ] 4.1 Add D66 after D64 in `docs/decisions.md`, and `D66` to the map's check-loop list, per [D12](design.md#d12).
  Verify: `grep -n '^### D66 · Two checkers: conformance and adversarial$' docs/decisions.md` prints a line.
- [ ] 4.2 Amend D48's bold text in `docs/decisions.md`, per [D12](design.md#d12), "hands its conformance worker its bundle" on
  one line.
  Verify: `grep -n 'hands its conformance worker its bundle' docs/decisions.md` prints a line.
- [ ] 4.3 Rewrite 0094's worker line in `AGENTS.md`, per [D12](design.md#d12).
  Verify: `grep -n "Converge's conformance worker reads" AGENTS.md` prints a line.
- [ ] 4.4 Edit `test_reading_sets_count_words` in `tests/test_metric_scripts.py` for the role sets, then the sets and docstring
  of `scripts/metrics/reading_set.py`, per [D13](design.md#d13).
  Verify: `uv run --script scripts/metrics/reading_set.py conformance` prints a number below `10500`; `uv run --script scripts/metrics/reading_set.py adversarial` prints a number below `10500`.
- [ ] 4.5 Replace `converge-worker-reading-set` in `metrics/catalogue.toml` with the conformance and adversarial entries, per [D13](design.md#d13).
  Verify: `grep -c -F 'args = ["conformance"]' metrics/catalogue.toml` prints `1`; `grep -c -F 'args = ["adversarial"]' metrics/catalogue.toml` prints `1`.
