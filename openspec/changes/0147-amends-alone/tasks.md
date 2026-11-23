# Amends alone — tasks

The phases that budget a halt by its head, ask the review's new question, let the fixer correct the plan's text, name the rescue and the supervisor in the models line, and read `cd` the same on every host.

## Progress

- [x] 1 — The budgets by halt · hard
- [ ] 2 — The plan review's question · moderate
- [ ] 3 — The fixer and the plan's text · hard
- [ ] 4 — The rescue's and the supervisor's models · moderate
- [ ] 5 — The Linux test and the records · moderate

## 1 — The budgets by halt

- [x] 1.1 Add `_halt_key(tree, held)` to `skills/mf-ship/scripts/conduct.py`: `<held>@<short HEAD>`, `held` alone with no tree
  ([D1](design.md#d1)). Test it in `tests/test_conduct.py` as `test_a_halt_key_joins_the_halted_head`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_halt_key_joins_the_halted_head` exits 0.
- [x] 1.2 `Run.rescue` and `Run.supervise` store `key = _halt_key(version.tree, held)`; `Run.rescued` and `Run.supervised` take an optional `tree`,
  passed by `Run.rescue`, `Run.supervise` and `Run.advance`; their words print each key's `held` alone ([D1](design.md#d1)).
  Verify: `git grep -n -F -e "key = _halt_key" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.3 Edit `test_a_usage_limit_converge_halt_gets_no_rescue` in `tests/test_conduct.py`: its `run.rescues` and `run.supervisions`
  assertions read the stored key, `converge-halted@` and the short `HEAD`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_usage_limit_converge_halt_gets_no_rescue` exits 0.
- [x] 1.4 Add `test_two_heads_are_two_halts`, `test_one_halt_is_answered_once` and `test_the_caps_stand_across_heads` to
  `tests/test_conduct.py`: converge halts at successive heads, each rescued; a key at its head, answered once; the caps count keys.
  Verify: `uv run pytest tests/test_conduct.py -q -k "two_heads_are_two or answered_once or caps_stand"` exits 0.
- [x] 1.5 Add `test_a_build_subtask_halted_at_two_heads`, `test_an_integrate_halt_is_keyed_by_its_head` and
  `test_a_version_halted_at_two_heads_ends_on_its_newest_halt` to `tests/test_conduct.py`: each kind of halt, and the final line.
  Verify: `uv run pytest tests/test_conduct.py -q -k "subtask_halted_at_two or keyed_by_its_head or ends_on_its_newest"` exits 0.
- [x] 1.6 Edit the budget sentences of the decisions "A rescue amends the plan, never the code or a decision" and "A supervisor
  answers what rescue diagnoses" in `docs/decisions.md`: a halt is a sub-task or stage at a halted head ([D1](design.md#d1)).
  Verify: `git grep -n -e "halted head" -- docs/decisions.md` exits 0.

## 2 — The plan review's question

- [ ] 2.1 Edit Step 8.5 of `skills/mf-cut-change/SKILL.md`: the packet's question asks of each requirement the delta adds or
  changes and each rule a decision states what else produces its subject, and what the plan exempts ([D2](design.md#d2)).
  Verify: `git grep -n -e "else produces" -- skills/mf-cut-change/SKILL.md` exits 0.
- [ ] 2.2 Add `test_the_plan_review_asks_what_else_produces_a_rule_subject` to `tests/test_skills.py`: the skill holds the new
  question beside the old one, and passes over a plan with no such rule.
  Verify: `uv run pytest tests/test_skills.py -q -k what_else_produces` exits 0.
- [ ] 2.3 Edit the decisions "A lighter plan review and build" and "The plan reviews run on Sonnet" in `docs/decisions.md` to
  carry what else produces the rule's subject ([D2](design.md#d2)).
  Verify: `git grep -n -e "else produces" -- docs/decisions.md` exits 0.

## 3 — The fixer and the plan's text

- [ ] 3.1 Add `plan_text(context, before, after)` to `skills/mf-converge/scripts/converge.py`: in each non-merge commit of
  `before..after`, a path under the change's folder past `design.md` and `specs/` halts `plan edit refused` ([D3](design.md#d3)).
  Verify: `git grep -n -F -e "plan_text(context" -- skills/mf-converge/scripts/converge.py` exits 0.
- [ ] 3.2 Add tests `test_a_fix_commit_editing_tasks_md_halts` and `test_a_fix_commit_editing_proposal_md_halts` to
  `tests/test_converge.py`: each halts with and without the trailer.
  Verify: `uv run pytest tests/test_converge.py -q -k "editing_tasks_md_halts or editing_proposal_md_halts"` exits 0.
- [ ] 3.3 `plan_text` halts a `specs/` file or a decision's body, a fix note aside, with no `Plan-text:` trailer, and takes one with it;
  tests in `tests/test_converge.py`: `test_a_fix_commit_may_edit_the_delta_with_the_trailer`, `test_a_fix_commit_editing_the_delta_without_the_trailer_halts`, `test_a_fix_commit_editing_a_decisions_body_is_taken`.
  Verify: `uv run pytest tests/test_converge.py -q -k "may_edit_the_delta or delta_without_the_trailer or decisions_body_is_taken"` exits 0.
- [ ] 3.4 `plan_text` halts a change to the decisions table or to a `### D<n>` or `## ` heading of `design.md`; a fix note or drift
  prose outside the decisions needs no trailer. Tests `test_a_fix_commit_editing_the_decisions_table_halts`, `test_a_fix_note_alone_needs_no_trailer`.
  Verify: `uv run pytest tests/test_converge.py -q -k "decisions_table_halts or fix_note_alone"` exits 0.
- [ ] 3.5 `plan_text` halts a `Plan-text:` trailer that names a card of the security category with severity `critical` or `high`.
  Test `test_a_security_card_of_high_is_left_to_the_halt` in `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -q -k security_card_of_high` exits 0.
- [ ] 3.6 Call `plan_text` from `fix()` of `skills/mf-converge/scripts/converge.py` after each fixer pass, before the gate.
  Test `test_the_fix_pass_runs_the_plan_text_check` in `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -q -k fix_pass_runs_the_plan_text_check` exits 0.
- [ ] 3.7 Edit `test_the_report_names_the_verdicts` in `tests/test_converge.py`: a commit local to it seeds `### D1` in `design.md`, and its
  fixer commit edits that body under a `Plan-text:` trailer, with the fix note.
  Verify: `uv run pytest tests/test_converge.py -q -k test_the_report_names_the_verdicts` exits 0.
- [ ] 3.8 Edit `skills/mf-converge/references/fix.md` and the amend-card paragraph of `skills/mf-converge/references/worker.md`:
  the fixer may say in the delta and a decision's body what its fix does, under `Plan-text:`; a security card stays an amend card. No brace: the prompt renders each as a template.
  Verify: `git grep -n -e "Plan-text" -- skills/mf-converge/references/fix.md` exits 0.
- [ ] 3.9 Edit `skills/mf-converge/references/verify.md`: the verify pass reads a plan-text edit in the fix's diff and judges its
  wording, with no brace. Test `test_a_verify_round_reads_a_plan_text_edit` in `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -q -k verify_round_reads_a_plan_text_edit` exits 0.
- [ ] 3.10 Make `_replanned` in `skills/mf-ship/scripts/conduct.py` read a `Plan-text:` fix commit that edits a decision's body as
  an amend. Test `test_a_plan_text_fix_commit_re_plans_a_stack` in `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -q -k plan_text_fix_commit_re_plans` exits 0.
- [ ] 3.11 Edit the fixer sentence of the decision "A rescue amends the plan, never the code or a decision" in
  `docs/decisions.md`: the delta and decision bodies under `Plan-text:` ([D3](design.md#d3)).
  Verify: `git grep -n -e "Plan-text" -- docs/decisions.md` exits 0.

## 4 — The rescue's and the supervisor's models

- [ ] 4.1 In `skills/mflib/modelsfile.py` add `rescue` and `supervise` to `TABLES` after `fix`, read `TABLES` alone and delete
  `PERSON` ([D4](design.md#d4)); edit `_EVERY_PART`, `_EVERY_TABLE` and each test of `tests/test_modelsfile.py` that reads it or loops `TABLES`.
  Verify: `uv run pytest tests/test_modelsfile.py -q` exits 0.
- [ ] 4.2 Add `test_a_rescue_and_a_supervise_part_write_their_tables` to `tests/test_modelsfile.py`: a models text with the parts
  writes `[rescue]` and `[supervise]`, each with `model` and `effort` and no `executor`.
  Verify: `uv run pytest tests/test_modelsfile.py -q -k rescue_and_a_supervise_part` exits 0.
- [ ] 4.3 In `skills/mf-plan/scripts/brief_check.py` add `rescue` and `supervise` to `PARTS` after the checks, to `HOSTLESS` and to `MODELS`
  ([D4](design.md#d4)); edit the tests of `tests/test_brief_check.py` that assert the `MODELS` text.
  Verify: `git grep -n -e "supervise" -- skills/mf-plan/scripts/brief_check.py` exits 0.
- [ ] 4.4 Add `test_a_models_line_takes_rescue_and_supervise_after_fix` and `test_a_models_line_out_of_order_or_with_a_host_halts` to
  `tests/test_brief_check.py`: the parts after `fix` pass, out of order or with a host they halt.
  Verify: `uv run pytest tests/test_brief_check.py -q -k "takes_rescue_and_supervise or out_of_order_or_with_a_host"` exits 0.
- [ ] 4.5 Edit the models grammar and the optional-parts paragraph of `skills/mf-plan/SKILL.md`: `supervise <model> <effort>` and
  `rescue <model> <effort>`, no host, after `fix`.
  Verify: `git grep -n -e "supervise <model>" -- skills/mf-plan/SKILL.md` exits 0.
- [ ] 4.6 Edit *Suggesting models* of `skills/mf-cut-change/SKILL.md`: the rescue on Sonnet 5.5 · high, the supervisor on the
  strongest tier · high, a `[rescue]` and `[supervise]` table in the template; test `test_the_skills_name_the_rescue_and_supervise_parts`.
  Verify: `uv run pytest tests/test_skills.py -q -k name_the_rescue_and_supervise_parts` exits 0.
- [ ] 4.7 Edit the decision "Model suggestions use offered capabilities" in `docs/decisions.md`: the models line's rescue and
  supervise part ([D4](design.md#d4)).
  Verify: `git grep -n -e "supervise part" -- docs/decisions.md` exits 0.

## 5 — The Linux test and the records

- [ ] 5.1 Make `row_v7` of `skills/mf-cut-change/scripts/cut_check.py` skip a command whose first word is `cd`, a loop keyword or a
  shell assignment ([D5](design.md#d5)); test it as `test_v7_passes_over_a_command_i19_refuses` in `tests/test_cut_check.py`.
  Verify: `uv run pytest tests/test_cut_check.py -q -k v7_passes_over` exits 0.
- [ ] 5.2 Edit Step 8 of `skills/mf-cut-change/SKILL.md`: row `V7` passes over a command `I19 refuses` ([D5](design.md#d5)).
  Verify: `git grep -n -e "I19 refuses" -- skills/mf-cut-change/SKILL.md` exits 0.
- [ ] 5.3 Edit the decision "The conductor checks the cut" in `docs/decisions.md`: its accepted cost on `V7` leaves out a command
  the plain-command row refuses ([D5](design.md#d5)).
  Verify: `git grep -n -e "plain-command row" -- docs/decisions.md` exits 0.
