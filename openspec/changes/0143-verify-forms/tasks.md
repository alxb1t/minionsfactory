# Verify forms — tasks

Phases, each green on its own: the judge, the cut, the build, then time. Decisions are cited by [design](design.md) id.

## Progress

- [x] 1 — The judge · moderate
- [x] 2 — The cut · moderate
- [x] 3 — The build · moderate
- [ ] 4 — Time · moderate

## 1 — The judge

- [x] 1.1 **HALT CHECK** The parser's names stand in `skills/mf-converge/scripts/plan_check.py` before they change.
  Verify: `git grep -n -e OUTPUT_VERBS -e CLAUSE -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 1.2 Rewrite `commands` in `skills/mf-converge/scripts/plan_check.py` per [D1](design.md#d1). Extend `test_a_span_after_an_output_verb_is_output` in `tests/test_plan_check.py` with the probe's line and the `, and` clause cases.
  Verify: `uv run pytest tests/test_plan_check.py::test_a_span_after_an_output_verb_is_output -q` exits 0.
- [x] 1.3 Add the probe's line to `test_a_span_after_an_output_verb_is_no_command` in `tests/test_verify_check.py`: `verify_check.py` runs no span after the verb as a command.
  Verify: `uv run pytest tests/test_verify_check.py::test_a_span_after_an_output_verb_is_no_command -q` exits 0.
- [x] 1.4 Keep stderr apart per [D2](design.md#d2): `Result`, `run`, `report`, `keep` and `load` in `skills/mf-converge/scripts/plan_check.py`. Add `test_stderr_is_shown_and_never_compared` to `tests/test_plan_check.py`.
  Verify: `uv run pytest tests/test_plan_check.py::test_stderr_is_shown_and_never_compared -q` exits 0.
- [x] 1.5 Turn `test_every_pytest_runs_without_the_cache_provider` and `test_a_command_runs_without_virtual_env` in `tests/test_plan_check.py`: each compares `run`'s result with the fourth field. Turn the `plan_check.py` row of `tests/test_staged_writes.py`: its kept text holds `"stderr": ""` after `"output"`.
  Verify: `uv run pytest tests/test_plan_check.py::test_every_pytest_runs_without_the_cache_provider tests/test_plan_check.py::test_a_command_runs_without_virtual_env tests/test_staged_writes.py -q` exits 0.
- [x] 1.6 Gate each start on the load per [D3](design.md#d3): `schedule` in `skills/mf-converge/scripts/plan_check.py` reads the load through one module name. Add `test_a_command_starts_under_the_load_or_when_none_runs` and patch the load in `test_commands_run_side_by_side_and_print_in_task_order`, both in `tests/test_plan_check.py`.
  Verify: `uv run pytest tests/test_plan_check.py::test_a_command_starts_under_the_load_or_when_none_runs tests/test_plan_check.py::test_commands_run_side_by_side_and_print_in_task_order -q` exits 0.

## 2 — The cut

- [x] 2.1 **HALT CHECK** The search options stand in `skills/mf-cut-change/scripts/verify_check.py` before they change.
  Verify: `git grep -n -e HIDING_LONG -- skills/mf-cut-change/scripts/verify_check.py` prints a line.
- [x] 2.2 Refuse a count off `grep -c` over one file per [D4](design.md#d4): `search` and `check_command` in `skills/mf-cut-change/scripts/verify_check.py`. Add `test_a_form_the_close_refuses_breaks_at_the_cut` to `tests/test_verify_check.py` and move the `git grep -c` and multi-file `grep -c` sub-tasks of `test_a_search_prints_the_lines_it_matches_at_head` into it.
  Verify: `uv run pytest tests/test_verify_check.py::test_a_form_the_close_refuses_breaks_at_the_cut tests/test_verify_check.py::test_a_search_prints_the_lines_it_matches_at_head -q` exits 0.
- [x] 2.3 Refuse `-L` and `--files-without-match` per [D5](design.md#d5): `SHORT`, `HIDING` and `LONG` in `skills/mf-cut-change/scripts/verify_check.py`. Add a `-L` sub-task to `test_a_check_out_of_shape_breaks_and_is_not_run` and to the new test.
  Verify: `uv run pytest tests/test_verify_check.py::test_a_check_out_of_shape_breaks_and_is_not_run -q` exits 0.
- [x] 2.4 Refuse a line number, a prose phrase and a range per [D6](design.md#d6): `check_command` and `check` in `skills/mf-cut-change/scripts/verify_check.py`, which loads `default_branch` from `cut_pre.py` by `runpy`. Add `cut_pre.py` to the `verify_check.py` row of `docs/modules.md`. Add to the new test a sub-task for each of a line number, a prose phrase and a range, each refused, and one for the HALT CHECK exemption.
  Verify: `uv run pytest tests/test_verify_check.py::test_a_form_the_close_refuses_breaks_at_the_cut tests/test_structure.py -q` exits 0.
- [x] 2.5 In `skills/mf-cut-change/SKILL.md` put the `I3` row right (`openspec validate --strict` and `verify_check.py`), word `I19` to name the count form, the absence form and the plain forms, and drop `-L` from Step 8's options, `-l -L -n` becoming `-l -n`.
  Verify: `git grep -c -e '-l -L -n' -- skills/mf-cut-change/SKILL.md` prints nothing.
- [x] 2.6 In `skills/mf-cut-change/SKILL.md` Step 3 add a line for a search of the tests with `facts.py readers --string` for each input a new refusal blocks, and a line for a task that reruns the deriver of a generated file whose input a task changes.
  Verify: `git grep -n -e 'deriver' -- skills/mf-cut-change/SKILL.md` prints a line.
- [x] 2.7 Put the `I3` and `I19` rows of `skills/mf-build/SKILL.md` in the cut skill's words, so `tests/test_skills.py` keeps the ids equal and no `\*\*I3\*\*.*plan check` match stands in the build skill.
  Verify: `git grep -c -e '\*\*I3\*\*.*plan check' -- skills/mf-build/SKILL.md` prints nothing.

## 3 — The build

- [x] 3.1 **HALT CHECK** The build's step for a failing HALT CHECK stands in `skills/mf-build/SKILL.md` before it changes.
  Verify: `git grep -n -e 'HALT CHECK.*sub-task whose check fails' -- skills/mf-build/SKILL.md` prints a line.
- [x] 3.2 Judge a HALT CHECK that `--only` names per [D7](design.md#d7): `jobs` in `skills/mf-converge/scripts/plan_check.py`, and the skip of a command one of whose words has the file name `plan_check.py`, whatever its directory. Turn `test_only_runs_the_named_sub_tasks` in `tests/test_plan_check.py`: `1.1 2.3` runs both, and a command holding `test_plan_check.py` runs.
  Verify: `uv run pytest tests/test_plan_check.py::test_only_runs_the_named_sub_tasks tests/test_plan_check.py::test_a_plan_check_finds_what_the_plan_left -q` exits 0.
- [x] 3.3 Leave each HALT CHECK sub-task out of the lines `added` hands to `--only` in `skills/mf-converge/scripts/converge.py`. Extend `test_a_catch_up_runs_the_changed_verifies_in_one_plan_check` in `tests/test_converge.py` with a HALT CHECK line the range adds.
  Verify: `uv run pytest tests/test_converge.py::test_a_catch_up_runs_the_changed_verifies_in_one_plan_check -q` exits 0.
- [x] 3.4 In `skills/mf-build/SKILL.md` Step 2 write [D7](design.md#d7) and [D8](design.md#d8): the phase's HALT CHECK sub-tasks run first through `plan_check.py --only`, then each other sub-task's `Verify:` the same way, a **HUMAN** phase's run as written.
  Verify: `git grep -n -e '--only' -- skills/mf-build/SKILL.md` prints a line.
- [x] 3.5 Word the `I15` row in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md` as a check of the state before the phase's edits, whose `Verify:` states the exit its command really gives, and Step 1's note `Step 2 halts on it` as `Step 2 runs it first, and halts on it`.
  Verify: `git grep -c -e 'Step 2 halts on it' -- skills/mf-build/SKILL.md` prints nothing.
- [x] 3.6 In `skills/mf-build/SKILL.md` Step 3.6 take `<base>` from Step 3.5 per [D9](design.md#d9): the match of `default-branch>.,`, the `<default-branch>` that ends the wrapped `--base` operand, becomes `<base>`.
  Verify: `git grep -c -e 'default-branch>.,' -- skills/mf-build/SKILL.md` prints nothing.
- [x] 3.7 In `docs/decisions.md` edit D74 per [D13](design.md#d13) to name the build's run at each phase through `plan_check.py --only`, and D72 to name the plan check among the bases `stacked-on` serves, as `metrics and .plan_check.py`.
  Verify: `git grep -n -e 'metrics and .plan_check.py' -- docs/decisions.md` prints a line.

## 4 — Time

- [ ] 4.1 **HALT CHECK** The fixed limit stands in `skills/mf-converge/scripts/plan_check.py` before it changes.
  Verify: `git grep -n -e TIMEOUT_SECONDS -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [ ] 4.2 Read the limit per [D10](design.md#d10): `verify_limit` in `skills/mf-converge/scripts/plan_check.py`, taken by `run`, `schedule` and `check_verifies` as an optional argument that falls back to `TIMEOUT_SECONDS` read at call time, so the tests that patch it stand. Add `test_a_verify_timeout_line_sets_the_limit` to `tests/test_plan_check.py`: a `**Verify timeout:**` line in the checked repository's root agents file sets it, no line gives 600.
  Verify: `uv run pytest tests/test_plan_check.py::test_a_verify_timeout_line_sets_the_limit -q` exits 0.
- [ ] 4.3 Send back no timeout alone per [D12](design.md#d12): `planned` in `skills/mf-converge/scripts/converge.py`. Add `test_a_timeout_alone_sends_nothing_back` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py::test_a_timeout_alone_sends_nothing_back -q` exits 0.
- [ ] 4.4 In `skills/mf-converge/references/fix.md` say a `timed out` line is no card and drop "ends within 600 s"; in `skills/mf-converge/references/worker.md` say a `timed out` line of the plan check's evidence is no finding.
  Verify: `git grep -c -e 'ends within 600' -- skills/mf-converge/references/fix.md` prints nothing.
- [ ] 4.5 In `skills/mf-build/SKILL.md` write [D11](design.md#d11) into Step 2 and Step 3.6: one background command, waited on once, the limit the repository's `**Verify timeout:**`, 600 s where none; drop "ends within 600 s".
  Verify: `git grep -c -e 'ends within 600' -- skills/mf-build/SKILL.md` prints nothing.
- [ ] 4.6 In `docs/decisions.md` edit D79 to say a timed-out command in the plan check's lines is no finding.
  Verify: `git grep -n -e 'timed.out' -- docs/decisions.md` prints a line.
