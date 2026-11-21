# Halt fixes — tasks

Phases: the plan check, the conductor, the queue, integrate and converge, then the rule. Each fix lands with the case that fails without it.

## Progress

- [x] 1 — The plan check · moderate
- [ ] 2 — The conductor · moderate
- [ ] 3 — The queue · moderate
- [ ] 4 — Integrate and converge · moderate
- [ ] 5 — The rule · moderate

## 1 — The plan check

- [x] 1.1 In `skills/mf-converge/scripts/plan_check.py`, `Command` gains `exits: int | None = None`, and `commands` reads spans as
  [D2](design.md#d2) says and sets `exits` as [D3](design.md#d3) says.
  Verify: `git grep -n "exits: int" -- skills/mf-converge/scripts/plan_check.py` prints the field.
- [x] 1.2 In the same file `passed`, `report` and `bare_pytest` hold a command to `command.exits` when it is set, as
  [D3](design.md#d3) says.
  Verify: `git grep -n "command.exits" -- skills/mf-converge/scripts/plan_check.py` prints the uses.
- [x] 1.3 In the same file `run` builds its environment without `VIRTUAL_ENV`, as [D4](design.md#d4) says.
  Verify: `git grep -n "VIRTUAL_ENV" -- skills/mf-converge/scripts/plan_check.py` prints the line.
- [x] 1.4 In `tests/test_plan_check.py` add `test_a_span_after_an_output_verb_is_output`, `test_exits_names_the_exit_a_command_must_have` and `test_a_command_runs_without_virtual_env`, with the cases of [D2](design.md#d2), [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `uv run pytest tests/test_plan_check.py::test_a_span_after_an_output_verb_is_output tests/test_plan_check.py::test_exits_names_the_exit_a_command_must_have tests/test_plan_check.py::test_a_command_runs_without_virtual_env -q` exits 0.
- [x] 1.5 In `skills/mf-cut-change/scripts/verify_check.py` load `plan_check.py` with `runpy` and take `SPAN`, `Unparsed`, `commands` and
  `tokens` from it, deleting its own parser, verbs and `Command`, and importing `Any` for `check_command`, as [D1](design.md#d1) says.
  Verify: `git grep -n "plan_check.py" -- skills/mf-cut-change/scripts/verify_check.py` prints the load.
- [x] 1.6 In `tests/test_structure.py` add the pair `("verify_check.py", "plan_check.py")` to `LOADS_OUTSIDE`, between the pairs of
  `review_metrics.py` and `viewer.py`.
  Verify: `git grep -n -F '("verify_check.py", "plan_check.py")' -- tests/test_structure.py` prints the pair.
- [x] 1.7 In `docs/modules.md` set the loads of the `verify_check.py` row to `plan_check.py`, so the row ends `| station | plan_check.py |`.
  Verify: `git grep -n -F "| station | plan_check.py |" -- docs/modules.md` prints the row.
- [x] 1.8 In `tests/test_verify_check.py` add `test_a_span_after_an_output_verb_is_no_command`: a `Verify:` that says a search
  exits `1` with the text `$(date)` breaks no `I19`.
  Verify: `uv run pytest tests/test_verify_check.py::test_a_span_after_an_output_verb_is_no_command -q` exits 0.

## 2 — The conductor

- [ ] 2.1 In `skills/mf-ship/scripts/conduct.py` `_decisions` reads each run of whitespace as one space ([D5](design.md#d5)); add
  `test_a_dedent_inside_a_decision_is_no_decision` to `tests/test_conduct.py`: a dedented code block in `### D4` is equal, a reworded sentence is not.
  Verify: `uv run pytest tests/test_conduct.py::test_a_dedent_inside_a_decision_is_no_decision tests/test_conduct.py::test_a_rescue_decides_under_the_switch -q` exits 0.
- [ ] 2.2 In `Run.advance` remove `build.halt` through `_remove_in` just before a stage `build` spawn ([D6](design.md#d6)); add
  `test_a_build_spawn_removes_the_halt_the_last_build_left` to `tests/test_conduct.py`: a `build.halt` naming `HEAD` is gone once the build worker ran.
  Verify: `uv run pytest tests/test_conduct.py::test_a_build_spawn_removes_the_halt_the_last_build_left -q` exits 0.
- [ ] 2.3 In `Run.advance` try a failed read of the release check once more before the run goes offline ([D7](design.md#d7)); add
  `test_a_failed_read_after_a_push_is_tried_once_more` to `tests/test_conduct.py`, beside `test_a_run_goes_on_while_origin_is_down`.
  Verify: `uv run pytest tests/test_conduct.py::test_a_failed_read_after_a_push_is_tried_once_more tests/test_conduct.py::test_a_run_goes_on_while_origin_is_down -q` exits 0.

## 3 — The queue

- [ ] 3.1 In `skills/mf-cut-change/scripts/cut_pre.py` `after_problem` passes a name whose archive folder the default branch holds
  ([D8](design.md#d8)); add `test_a_released_after_is_met` to `tests/test_cut_pre.py`: `--after 0001-old` prints `cut_pre: ok — after`.
  Verify: `uv run pytest tests/test_cut_pre.py::test_a_released_after_is_met -q` exits 0.
- [ ] 3.2 In `Run.cutting` hand the cutter only the `after` ids `_shipped` says have not shipped ([D8](design.md#d8)); add
  `test_a_cutter_is_handed_no_released_after` to `tests/test_conduct.py`: an `after` released while its cut waited leaves the prompt.
  Verify: `uv run pytest tests/test_conduct.py::test_a_cutter_is_handed_no_released_after -q` exits 0.
- [ ] 3.3 In `rejoin` clear and request each dependent halted `after <name> is cut-halted`, down the chain, and name each in the line
  ([D9](design.md#d9)); add `test_a_rejoin_clears_a_chain_of_cut_halts` to `tests/test_conduct.py`: a chain of queued cuts, rejoined at its head.
  Verify: `uv run pytest tests/test_conduct.py::test_a_rejoin_clears_a_chain_of_cut_halts -q` exits 0.
- [ ] 3.4 In `tests/test_conduct.py` `test_a_cut_halt_is_shown_and_rejoin_cuts_again` expects the line `rejoin: requested 0001-a, 0002-b · run started · pid 4242` and
  rejoins `0001-a` alone where it rejoined each dependent.
  Verify: `uv run pytest tests/test_conduct.py::test_a_cut_halt_is_shown_and_rejoin_cuts_again -q` exits 0.

## 4 — Integrate and converge

- [ ] 4.1 **HALT CHECK** Confirm `integrate.py` defines `_unmerged`, which [D10](design.md#d10) skips by.
  Verify: `git grep -n "def _unmerged" -- skills/mf-integrate/scripts/integrate.py` prints the definition.
- [ ] 4.2 In `skills/mf-integrate/scripts/integrate.py` `decisions` renumbers the changelog first, skips a conflicted path, collects an
  ambiguous one and halts once ([D10](design.md#d10)); add `test_decisions_skips_a_conflicted_file_and_goes_on` and `test_decisions_halts_once_after_every_ambiguous_file` to `tests/test_integrate.py`.
  Verify: `uv run pytest tests/test_integrate.py::test_decisions_skips_a_conflicted_file_and_goes_on tests/test_integrate.py::test_decisions_halts_once_after_every_ambiguous_file tests/test_integrate.py::test_decisions_renumbers_a_colliding_decision_and_its_citations -q` exits 0.
- [ ] 4.3 In `skills/mf-integrate/SKILL.md` add to the `decisions` row that a path git left conflicted is skipped and printed as
  `decisions: conflicted` with its renumber, for the note.
  Verify: `git grep -n "decisions: conflicted" -- skills/mf-integrate/SKILL.md` prints the row.
- [ ] 4.4 In `skills/mf-converge/scripts/converge.py` `read_findings` reads a `changes-requested` file with no open card as malformed, as
  `verdict is changes-requested with no open card`, and `held` and a failed `rewrite` write `clean` as [D11](design.md#d11) says; the halt in `rounds` goes.
  Verify: `git grep -n -F "changes-requested with no open card" -- skills/mf-converge/scripts/converge.py` prints the reason.
- [ ] 4.5 In `tests/test_converge.py` add `test_changes_requested_with_nits_alone_counts_clean` (the file reads `clean` after) and
  `test_changes_requested_with_no_card_gets_a_rewrite` (one rewrite worker, then the file reads `clean`); drop the `no card` row from the loop of halts in `test_a_blocker_is_fixed_verified_and_cleared`.
  Verify: `uv run pytest tests/test_converge.py::test_changes_requested_with_nits_alone_counts_clean tests/test_converge.py::test_changes_requested_with_no_card_gets_a_rewrite tests/test_converge.py::test_a_blocker_is_fixed_verified_and_cleared -q` exits 0.

## 5 — The rule

- [ ] 5.1 In `skills/mf-rescue/SKILL.md` add after the table of halts the rule of [D12](design.md#d12): a `Verify:` that cannot pass is
  retargeted or split, never replaced by one that proves less, an exact count staying exact; else a diagnosis.
  Verify: `git grep -n -w retargeted -- skills/mf-rescue/SKILL.md` prints the rule.
- [ ] 5.2 In `skills/mf-supervise/SKILL.md` add the rule of [D12](design.md#d12) under Step 2's table: a `Verify:` that cannot pass is
  retargeted or split, never replaced by one that proves less; else a diagnosis.
  Verify: `git grep -n -w retargeted -- skills/mf-supervise/SKILL.md` prints the rule.
