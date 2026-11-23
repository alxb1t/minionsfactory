# Debt paydown 4 — tasks

Build the settled [design](design.md), one phase at a time; the checker row's test goes red before its fix.

## Progress

- [x] 1 — The archived texts · moderate
- [x] 2 — The live texts and the row · moderate
- [ ] 3 — The paid cards · moderate

## 1 — The archived texts

- [x] 1.1 In `openspec/changes/archive/0118-debt-paydown-3a/proposal.md` reword the opening line per the rows of [D2](design.md#d2)'s table for that file: it no longer holds `about 15`.
  Verify: `git grep -c -F -e 'about 15' -- openspec/changes/archive/0118-debt-paydown-3a/proposal.md` prints nothing.
- [x] 1.2 In `openspec/changes/archive/0118-debt-paydown-3a/design.md` reword the introduction, the decision rows and the risk bullet per the rows of [D2](design.md#d2)'s table for that file.
  Verify: `git grep -c -F -e 'four small' -e 'four ideas' -e 'two versions' -e 'seven old' -e 'about 45' -- openspec/changes/archive/0118-debt-paydown-3a/design.md` prints nothing.
- [x] 1.3 In `openspec/changes/archive/0119-debt-paydown-3b/proposal.md` replace the Impact line and the last exclusion with the blocks of [D2](design.md#d2) captioned with that file, each whole.
  Verify: `git grep -c -F -e '[D17]' -- openspec/changes/archive/0119-debt-paydown-3b/proposal.md` prints `openspec/changes/archive/0119-debt-paydown-3b/proposal.md:2`.
- [x] 1.4 In `openspec/changes/archive/0099-stacked-builds/design.md`, `openspec/changes/archive/0100-worker-diet/design.md` and `openspec/changes/archive/0104-codex-limits/design.md` link the decision per the rows of [D2](design.md#d2)'s table for those files.
  Verify: `git grep -c -F -e 'per 0119-debt-paydown-3b' -- openspec/changes/archive/0099-stacked-builds/design.md openspec/changes/archive/0100-worker-diet/design.md openspec/changes/archive/0104-codex-limits/design.md` prints nothing.
- [x] 1.5 In `openspec/changes/archive/0121-ui-prepare/design.md` replace the fetch command's step 4 with the block of [D2](design.md#d2) captioned with that file.
  Verify: `git grep -c -F -e '/dev/null' -- openspec/changes/archive/0121-ui-prepare/design.md` prints nothing.
- [x] 1.6 In `openspec/changes/archive/0134-run-layout/design.md` replace the risk bullet on the old-layout id with the block of [D2](design.md#d2) captioned with that file.
  Verify: `git grep -c -F -e 'four digits' -- openspec/changes/archive/0134-run-layout/design.md` prints nothing.
- [x] 1.7 In `openspec/changes/archive/0136-status-log/design.md` replace the Tests introduction with the block of [D2](design.md#d2) captioned with that file.
  Verify: `git grep -c -F -e 'Nothing runs' -- openspec/changes/archive/0136-status-log/design.md` prints nothing.

## 2 — The live texts and the row

- [x] 2.1 In `CHANGELOG.md` reword the first clause of the v0.117.0 line of its third phase per [D3](design.md#d3).
  Verify: `git grep -c -F -e 'or not,' -- CHANGELOG.md` prints `CHANGELOG.md:1`.
- [x] 2.2 In `skills/mf-converge/references/worker.md` insert the words of [D4](design.md#d4) into the `unplanned-file` row.
  Verify: `git grep -c -F -e 'whose files' -- skills/mf-converge/references/worker.md` prints `skills/mf-converge/references/worker.md:1`.
- [x] 2.3 In `skills/mf-converge/references/verify.md` insert the words of [D4](design.md#d4) into the line on the unplanned-file pass.
  Verify: `git grep -c -F -e 'whose files' -- skills/mf-converge/references/verify.md` prints `skills/mf-converge/references/verify.md:1`.
- [x] 2.4 Add `test_kexpr_naming_a_module_of_a_directory_holds` to `tests/test_cut_check.py` per [D5](design.md#d5) and run it red, then change `_defined` and `row_v8` in `skills/mf-cut-change/scripts/cut_check.py` to the same decision.
  Verify: `uv run pytest -q tests/test_cut_check.py -k test_kexpr_naming_a_module_of_a_directory_holds` exits 0.

## 3 — The paid cards

- [ ] 3.1 **HALT CHECK** `0120·R6` is paid, per [D6](design.md#d6): the design in `openspec/changes/archive/0120-ui-state/design.md` says the worker, halt, state and liveness tests carry the `slow` marker.
  Verify: `git grep -c -F -e 'liveness tests carry' -- openspec/changes/archive/0120-ui-state/design.md` exits 0.
- [ ] 3.2 **HALT CHECK** `0122·S1` is paid, per [D6](design.md#d6): the tick-read command in `skills/mf-build/SKILL.md` holds single backslashes before its brackets.
  Verify: `git grep -c -F -e '- \[.\] <N>' -- skills/mf-build/SKILL.md` exits 0.
- [ ] 3.3 **HALT CHECK** `0134·R1` is paid, per [D6](design.md#d6): `test_integrate_halts_on_each_old_entry_alone` in `tests/test_integrate.py` carries the `slow` marker.
  Verify: `uv run pytest -q tests/test_integrate.py -m "not slow" -k test_integrate_halts_on_each_old_entry_alone` exits 5.
- [ ] 3.4 **HALT CHECK** `0146·R5` is paid, per [D6](design.md#d6): `test_cutdeclared_command_fails_the_cut_check` in `tests/test_conduct.py` carries the `slow` marker.
  Verify: `uv run pytest -q tests/test_conduct.py -m "not slow" -k test_cutdeclared_command_fails_the_cut_check` exits 5.
- [ ] 3.5 **HALT CHECK** `0147·R1` is paid, per [D6](design.md#d6): `test_a_stuck_stage_halt_names_its_rescue_and_supervision` in `tests/test_conduct.py` asserts the halt line's rescue and supervision words.
  Verify: `git grep -c -F -e 'rescued converge-halted · supervised converge-halted' -- tests/test_conduct.py` exits 0.
- [ ] 3.6 **HALT CHECK** `0147·S4` is paid, per [D6](design.md#d6): `plan_text` in `skills/mf-converge/scripts/converge.py` lists the paths with `-z`.
  Verify: `git grep -c -F -e '"--name-only", "-r", "-z"' -- skills/mf-converge/scripts/converge.py` exits 0.
