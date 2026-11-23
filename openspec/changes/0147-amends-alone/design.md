# Amends alone — design

The changes that let the line close a plan's own faults without a person, each with its reach and its exemptions. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

0146's halts were the plan's: the rescue's budget was spent by a stage, the fixer's right code met a plan text it may not touch, and a rule written in one sentence met files other stations also write. The rescue is a station ([D53](../../../docs/decisions.md#d53--a-rescue-amends-the-plan-never-the-code-or-a-decision)), the supervisor another ([D61](../../../docs/decisions.md#d61--a-supervisor-answers-what-rescue-diagnoses)), and the budgets live in `Run.rescued` and `Run.supervised` of `skills/mf-ship/scripts/conduct.py`, keyed today by the halted sub-task or stage alone. The fixer's rules are `skills/mf-converge/references/fix.md`'s, and `converge.py` reads no path of its commits. The brief's Q67 asks that each new rule name its reach and exemptions: each decision below does, and each carries cases for both.

## Goals / Non-Goals

- **Goals:** a halt answered once and a new head a new halt; a fixer that says in the plan what its fix does; a review that asks what else produces a rule's subject; the rescue and supervise parts of the models line; a first-word row that reads the same on every host.
- **Non-Goals:** a budget kept across runs; the run log's fields; a widening of what the rescue or the supervisor may edit; a change to any gate.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A rescue's and a supervision's budget key is the halted sub-task or stage joined to the halted head | 0146's second halt found both spent by a stage though the rescue could have closed it (Q67, Q74) | a budget kept by stage; a budget by run |
| [D2](#d2) | The cut's plan review asks of each new requirement and rule what else produces its subject | 0146 halted twice on a rule whose subject the fixer's commits and the changelog also produce (Q67, Q74) | a new checker row; a second reviewer |
| [D3](#d3) | The fixer may edit the delta and decision bodies in its fix commit under a `Plan-text:` trailer | R7 and R8 on 0146: the code was right and the plan's text lagged (Q70, Q74) | the fixer editing the table or `tasks.md`; a rescue for each |
| [D4](#d4) | The models line gains `rescue` and `supervise` parts, written as tables | both ran on Opus high for want of a part (Q72, Q74) | a host on either part; this version's own line carrying them |
| [D5](#d5) | Row `V7` passes over a command row `I19` refuses | a test read `cd` as a program on macOS and not on Linux (Q68, Q74) | a skip of the test on Linux |

### D1

**A halt is a halted sub-task or stage at the version's `HEAD` when the halt is read. `Run.rescued`, `Run.rescue`, `Run.supervised` and `Run.supervise` count that key: one halt is answered once, and a halt at a new head is a new halt.**

- **Key:** `<held>@<short HEAD>`; with no tree, `held` alone, as before. `_halt_key` in `conduct.py` builds it.
- **Reach:** a build's sub-task halt, a converge halt (`converge-halted`) and an integrate halt (`integrating`), for the rescue and the supervisor alike.
- **Exempt:** the caps of `RESCUES` rescues and `SUPERVISES` supervisions a version gets in a run stand, counted over keys, and stay a run's memory. The halt's ` · rescued` and ` · supervised` words name the sub-task or stage with no head. The version's final halt line reads the halts it holds, as before, and a taken amend clears them.
- **Cases:** converge halts at successive heads in one run, each rescued; the same key at the same head twice, answered once; a rescue and a supervision past their caps refused; a build's sub-task halted at successive heads; an integrate halt.

### D2

**The review packet's question of `skills/mf-cut-change/SKILL.md` covers, beside whether each task can be built as written, each requirement the delta adds or changes and each rule a decision states: what else produces the thing it judges, and what the plan exempts.**

- **Reach:** the build's commits, a fix commit, an amend, the release's edits and a generated file, as producers of what the rule judges.
- **Exempt:** a plan that adds or changes no requirement and states no rule is passed over by this part. The reviewer's budget of turns, the packet's contents and the table of what the cut does with a doubt stand; a doubt returns to the cutter as today.
- **Cases:** a packet for a plan with a new requirement; one for a plan with none.
- **Amends:** [D65](../../../docs/decisions.md#d65--a-lighter-plan-review-and-build) and [D80](../../../docs/decisions.md#d80--the-plan-reviews-run-on-sonnet), each edited where it lives.

### D3

**The fixer may edit the change's spec delta and the body of a `### D<n>` entry of `design.md`, in the commit of the fix, which carries a `Plan-text: <card ids>` trailer. `converge.py` reads each non-merge commit of a fix pass and halts `plan edit refused — <why>` outside this.**

- **Held:** under `openspec/changes/<id>/` only `design.md` and `specs/` may change; the decisions table, a `### D<n>` heading and a `## ` heading stay; `tasks.md` and `proposal.md` are refused; no trailer on a delta or a decision body is refused; a trailer naming a security card of `critical` or `high` severity is refused and the card stays an amend card.
- **Exempt:** a commit that touches nothing under the change's folder; drift prose of `design.md` outside its decisions section; a `Fix note` line. None needs the trailer, as today. A row of `## Tests` or `## Dependencies` stays the fixer's rule in `fix.md`, which `plan_text` does not read.
- **Verify and stacks:** the verify pass reads the plan-text edit in the fix's diff and judges its wording; the stack's re-plan test of `conduct.py` reads a `Plan-text:` commit that edits a decision's body as it reads an amend.
- **Cases:** a fix commit editing the delta with the trailer, with none, and editing a decision's body, the decisions table, `tasks.md` and `proposal.md`; a security card of high severity marked for an amend; a verify round reading a plan-text edit; a stacked dependent of a version whose fix commit edited a decision's body.
- **Amends:** [D53](../../../docs/decisions.md#d53--a-rescue-amends-the-plan-never-the-code-or-a-decision), edited where it lives.

### D4

**`rescue` and `supervise` are parts of a brief's models line, each a model and an effort with no host, after `fix`, written as the `[rescue]` and `[supervise]` tables the conductor already reads. Suggested: the rescue on Sonnet 5.5 · high, the supervisor on the strongest tier · high.**

- **Reach:** `brief_check.py`'s grammar, the map of `skills/mflib/modelsfile.py`, and the text of `skills/mf-plan/SKILL.md` and `skills/mf-cut-change/SKILL.md`. `auto_grant` stays the person's key.
- **Exempt:** `conduct.py`'s defaults, which read these tables already; a line with neither part; this version's own line, which carries none because the pin does not know them.
- **Cases:** a models line with the parts, out of order, and with a host.
- **Amends:** [D41](../../../docs/decisions.md#d41--model-suggestions-use-offered-capabilities), edited where it lives.

### D5

**Row `V7` of `cut_check.py` passes over a `Verify:` command whose first word is `cd`, a loop keyword or a shell assignment: the words `verify_check.py` refuses at a command's start under `I19`.**

- **Reach:** row `V7` alone.
- **Exempt:** any other first word that names nothing still halts `V7`; `I19` still halts each command it refuses.
- **Cases:** `cd x` under both rows with a `PATH` that holds a `cd` program and one that does not.
- **Amends:** [D89](../../../docs/decisions.md#d89--the-conductor-checks-the-cut), whose accepted cost named `V7` for such a word.

## Tests

The change adds unit tests and no end-to-end test: this repo's lowest layer is the unit test, and each case below reaches its branch there ([T1](../../../skills/mf-build/SKILL.md)). No test is deleted or merged.

| layer | file | tests the change adds |
|---|---|---|
| unit | `tests/test_conduct.py` | `test_a_halt_key_joins_the_halted_head`, `test_two_heads_are_two_halts`, `test_one_halt_is_answered_once`, `test_the_caps_stand_across_heads`, `test_a_build_subtask_halted_at_two_heads`, `test_an_integrate_halt_is_keyed_by_its_head`, `test_a_version_halted_at_two_heads_ends_on_its_newest_halt`, `test_a_plan_text_fix_commit_re_plans_a_stack` |
| unit | `tests/test_converge.py` | `test_a_fix_commit_may_edit_the_delta_with_the_trailer`, `test_a_fix_commit_editing_the_delta_without_the_trailer_halts`, `test_a_fix_commit_editing_tasks_md_halts`, `test_a_fix_commit_editing_proposal_md_halts`, `test_a_fix_commit_editing_a_decisions_body_is_taken`, `test_a_fix_commit_editing_the_decisions_table_halts`, `test_a_security_card_of_high_is_left_to_the_halt`, `test_a_fix_note_alone_needs_no_trailer`, `test_the_fix_pass_runs_the_plan_text_check`, `test_a_verify_round_reads_a_plan_text_edit` |
| unit | `tests/test_cut_check.py` | `test_v7_passes_over_a_command_i19_refuses` |
| unit | `tests/test_modelsfile.py` | `test_a_rescue_and_a_supervise_part_write_their_tables` |
| unit | `tests/test_brief_check.py` | `test_a_models_line_takes_rescue_and_supervise_after_fix`, `test_a_models_line_out_of_order_or_with_a_host_halts` |
| unit | `tests/test_skills.py` | `test_the_plan_review_asks_what_else_produces_a_rule_subject`, `test_the_skills_name_the_rescue_and_supervise_parts` |

End-to-end runs added: none. The tests the change edits, not adds: the tests of `tests/test_modelsfile.py` that read the person's tables as a map of their own or loop its tables, the tests of `tests/test_brief_check.py` that assert the models line's text, `test_a_usage_limit_converge_halt_gets_no_rescue` of `tests/test_conduct.py`, and `test_the_report_names_the_verdicts` of `tests/test_converge.py`. `test_the_folded_checks_report_their_failures` of `tests/test_cut_check.py` is run again, unedited, on a `PATH` with no `cd`.

## Dependencies

None.

## Risks / Trade-offs

- A fix commit's plan-text edit that passes the path check is a worker's decision, as a rescue's amend is: the verify pass and the next round judge its wording, never a rule.
- `converge.py` and `conduct.py` each spell the `Plan-text` trailer, as they spell each commit subject they read; a test of each holds its spelling.
- A halt at a head the rescue's own amend left is a new halt, so a rescue that amends wrongly can be rescued again until the cap of `RESCUES` stops it.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the budgets and the fixer, which change what the conductor and a worker may do, are rated hard; the review's question, the models parts and the Linux test with the records are rated moderate.
