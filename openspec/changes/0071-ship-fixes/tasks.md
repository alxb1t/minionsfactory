# Ship fixes — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — Integrate commits, then gates
- [x] 2 — The changelog renumber
- [x] 3 — Dependents come back
- [ ] 4 — An amend answers a halt
- [ ] 5 — The fixer and rescue

## 1 — Integrate commits, then gates

- [x] 1.1 Add `--tree <path>` to `skills/mf-converge/scripts/gate_run.py`'s `main` and docstring, per [D1](design.md#d1); extend
  `test_records_go_under_the_primary_run_directory` in `tests/test_gate_run.py` with a commit in the worktree, a `--tree` run from
  the primary, and a missing path.
  Verify: `uv run pytest -q tests/test_gate_run.py -k records_go_under_the_primary_run_directory` reports `1 passed`.
- [x] 1.2 Add `_red` to `skills/mf-ship/scripts/conduct.py` and read it in `stage_of` and `_check_integrate`, per
  [D2](design.md#d2); extend `test_status_reads_each_stage_from_disk` and `test_each_check_passes_only_on_disk_evidence` in
  `tests/test_conduct.py` with the `.red` and fix-commit cases the design's `## Tests` names.
  Verify: `uv run pytest -q tests/test_conduct.py -k "status_reads_each_stage_from_disk or each_check_passes_only_on_disk_evidence"` reports `2 passed`.
- [x] 1.3 Rewrite `skills/mf-integrate/SKILL.md`'s description, flow, Step 2 table, Step 4 and Never line to commit, then gate
  with `--tree`, and `skills/mf-release/SKILL.md`'s account of integrate, per [D2](design.md#d2).
  Verify: `grep -n 'gate_run.py --tree <worktree>' skills/mf-integrate/SKILL.md` prints a line.

## 2 — The changelog renumber

- [x] 2.1 Skip `CHANGELOG.md` in `decisions()`'s recite loop and renumber its `[Unreleased]` entries, in
  `skills/mf-integrate/scripts/integrate.py`, per [D3](design.md#d3); extend
  `test_decisions_renumbers_a_colliding_decision_and_its_citations` in `tests/test_integrate.py` with an `[Unreleased]` citation
  and a released one.
  Verify: `uv run pytest -q tests/test_integrate.py -k decisions_renumbers_a_colliding_decision_and_its_citations` reports `1 passed`.

## 3 — Dependents come back

- [x] 3.1 Add `Run._unblock`, called from `take_requests` and `join()`, and guard `take_back`'s `read_plan`, in
  `skills/mf-ship/scripts/conduct.py`, per [D4](design.md#d4); extend `test_a_halted_dependency_blocks_a_chain` with a rejoin of the
  dependency alone, and `test_the_plan_is_read_once` with a rejoin of a planned version.
  Verify: `uv run pytest -q tests/test_conduct.py -k "halted_dependency_blocks_a_chain or plan_is_read_once"` reports `2 passed`.
- [x] 3.2 Count `catch_up`'s commits with `--no-merges`, per [D4](design.md#d4); extend `test_after_waits_for_its_dependency` with a
  cut-only version holding a `merge_in` commit, behind a `README.md` change on the default branch.
  Verify: `uv run pytest -q tests/test_conduct.py -k after_waits_for_its_dependency` reports `1 passed`.

## 4 — An amend answers a halt

- [ ] 4.1 Add `_amended_only` to `skills/mf-ship/scripts/conduct.py` and call it from `_answered`, per [D5](design.md#d5); let
  `tests/fake_worker.py`'s by-rule mimic take merges and amends, per [D6](design.md#d6); extend
  `test_a_fix_after_a_cap_halt_converges_afresh` with the halts the design's `## Tests` names, each answered by the person's amend.
  Verify: `uv run pytest -q tests/test_conduct.py -k fix_after_a_cap_halt_converges_afresh` reports `1 passed`.
- [ ] 4.2 State the answer rule at `skills/mf-converge/SKILL.md`'s void-halt paragraph, per [D5](design.md#d5), and **merges and
  amends** in its catch-up diagram, cap item, By rule and `docs/principles.md`'s catch-up line, per [D6](design.md#d6).
  Verify: `grep -n 'Merges and amends' skills/mf-converge/SKILL.md` prints a line.

## 5 — The fixer and rescue

- [ ] 5.1 Add the fixer's plan rule to `skills/mf-converge/SKILL.md`'s Step 6, `gate_check.py` to Step 7, and the one-line
  `verify: halt` to Step 1.6, per [D7](design.md#d7).
  Verify: `grep -n 'never edits the change' skills/mf-converge/SKILL.md` prints a line.
- [ ] 5.2 Write a verify halt's diagnosis in `rescue()` with no worker, in `skills/mf-ship/scripts/conduct.py`, per
  [D8](design.md#d8); add the `verify-halts` mode to `tests/fake_worker.py` and `test_a_verify_halt_is_diagnosed_without_a_worker`
  to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k verify_halt_is_diagnosed_without_a_worker` reports `1 passed`.
- [ ] 5.3 Add the verify-halt row and the command to `skills/mf-rescue/SKILL.md`'s table and proposal template, per
  [D8](design.md#d8).
  Verify: `grep -n 'conduct.py rejoin <change-id>' skills/mf-rescue/SKILL.md` prints a line.
- [ ] 5.4 Amend D45, D47 and D53 in `docs/decisions.md`, and the rejoin, `run · live`, diagnosed and `integrating` lines in `skills/mf-ship/SKILL.md`, per
  [D9](design.md#d9).
  Verify: `grep -c 'converge or integrate halt was answered while its rescue ran' skills/mf-ship/SKILL.md` prints `2`.
