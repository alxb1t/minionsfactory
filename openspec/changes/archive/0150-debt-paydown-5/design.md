# Debt paydown 5 — design

Pays the cards the sort chose to fix, and lists the cards it chose to close with no fix, so the release strikes both. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The debt file holds one card per deferred finding. The release deletes exactly the cards a change lists under `debt:` and reports an id it does not find; it checks nothing of the diff. No verb strikes a card outside a version, and converge and the release alone write the file, under its lock, so a card closed as won't-fix is struck by being listed, with no task ([D3](#d3)), as `0088-paydown-2` did.

The fixes below are bounded: each brings code or a skill's row to what a requirement or a decision in force already says, save rows V2 and V6 of the cut, whose requirements say too much and are corrected ([D14](#d14)).

```
phase 1  the cut's rows        cut_check.py       V2, V6, the spec delta
phase 2  the conductor         conduct.py         kept line, halt marker, environments, run log
phase 3  the drain             conduct.py         sandboxed() after the deadline
phase 4  converge, the viewer  converge.py        trailer's card; viewer.py failed start
phase 5  the texts             SKILL.md, D76      Step 4.3 row; the share's limit
```

## Goals / Non-Goals

**Goals:** each fix of [the cases](#cases) red before its edit and green after; every phase ends on a green `make check`; the build ends on a green gate.

**Non-Goals:** the riders of 5c3 `marks`; any edit of the debt file; a retry or a card for a timed-out plan check; a plan-text check of a fresh run after a fixer's halt ([D12](#d12)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The riders 0136·S3, 0138·S2, 0140·S3 and 0142·S2 stay with the refactoring's 5c3 `marks` (Q7) | the sort classed the riders accepted while token diet 5's Q91 counted them among those left; 5c3 already plans their fix | paying them here |
| [D2](#d2) | This brief has its own folder; paydown 4's brief is untouched (Q8) | that brief is the one queued as `0149-debt-paydown-4` | — |
| [D3](#d3) | A card closed as won't-fix is struck by being listed under `debt:` of this version, with no task: the release deletes every listed id (Q9) | the release checks nothing of the diff; `0088-paydown-2` did the same; no verb strikes a card outside a version, and a hand edit is outside the spec | a hand edit of the debt file |
| [D4](#d4) | The text of each card closed with no fix is copied to the closed file in the vault before the queue (Q10) | the release deletes a card's text for good, and the debt file is the only copy | — |
| [D5](#d5) | The cheap cards 0146·S10 and 0146·S15 are fixed: a kept line cut at 4000 characters keeps its newline; the cut's halt marker is matched at a line's start (Q11) | one line and a test each | — |
| [D6](#d6) | These fixes add no rule: Step 4.3 names every path the index changed, D61 standing; a worker's environment drops what preparation drops; `sandboxed()` bounds its drain after the deadline; the viewer's failed start forgets only its own pid; a run log that is gone ends in a named stop; a `Plan-text:` trailer must name a card (Q12) | each brings the code or a skill's row to what the spec already says | a bound of the settle's paths in code |
| [D7](#d7) | The cut's rows V2 and V6 halt a valid cut: V2 treats a negated `-k` word that the test's name does not hold as unknown and stays silent; V6 ties removed and added lines to their file's diff header, a block with no header staying silent (Q13) | each is structural and errs to silence; a false halt at the cut costs a second cutter or a halt | — |
| [D8](#d8) | 0104·S3: the limit is named — a clause in D76's accepts and the titles of the Codex window metrics; no attribution by tokens (Q14) | a clause and the titles against a new metric's script; the share over-counts whenever another line's checkers run on the account | attribution by tokens |
| [D9](#d9) | 0065·R8, 0085·R3, 0143·S2 and 0146·S12 close as won't-fix with the accepted cards, by listing (Q15) | a red gate that is loud and a line to fix by hand; a sibling's release, which the line's cap rules out; a retry or a card on a timeout adds halts under load; the exemption 0146 settled after its halts | a fix for each |
| [D10](#d10) | One version, `debt-paydown-5`, a minor, queued after `0149-debt-paydown-4` and before 5c3 `marks` (Q16) | V2's and V6's requirements and D76's text change; one cut, one converge and one release for all of it | a patch; a version for each fix |
| [D11](#d11) | The inflow of accepted cards from the last versions is not this version's; noted for a later round (Q17) | one concern a version | — |
| [D12](#d12) | 0147·S3 closes as won't-fix, in place of a fix (Q18) | the spec asks the plan-text check of a resumed run, paid since 0147; what is left is a fresh run after a fixer's halt, and a check over that range would reach a rescue's, a supervisor's and the person's amends and an integrate merge, each of which `plan_text` refuses | a check over a wider range |
| [D13](#d13) | Each rule has its reach: the drain's bound covers `sandboxed()`'s read after its deadline for every caller; the trailer's rule covers a fix commit that edits the spec delta or rewords a decision's body; the environment's rule covers a worker's environment and the fetch preparation's; the run log's rule covers the run's halt handler and `stop_run` (Q19) | Q12; a rule that names its reach is not widened a round at a time; a trailer with prose beside its ids must not halt | a wider reach |
| [D14](#d14) | V2's silence covers a negated identifier that is no substring of the test's name; V6 compares the lines of the searched file alone when a diff block names its file by a header (Q20) | Q13; the cases of each exemption are in [the cases](#cases) | — |
| [D15](#d15) | No phase edits the debt file, and none has a task for a card closed with no fix; the release deletes every listed id (Q21) | the debt file is written under its lock by converge and the release alone; the cut halts on a listed id it does not find | a task that strikes a card |
| [D16](#d16) | The drain's phase is rated hard; the rest and the close are moderate; the models are the brief's (Q22) | process groups, a pipe and a deadline, where a wrong fix hangs or turns a timing test red | — |
| [D17](#d17) | The settled table is confirmed and the queue's yes given (Q23) | the cycle of token diet 5's Q23 | — |
| [D18](#d18) | Queued at once behind `0149-debt-paydown-4`, with no `after:` (Q24) | the line does not idle through the night; the version needs nothing the versions before it ship | a chain by `after:` |
| [D19](#d19) | Decided by the cutter (C1): V2's case `-k "widget and not widget_old"` over `test_widget_old` is silent before and after the edit; the halting case kept for a negated word the name holds is `-k "a or not b"` over `test_a_b` | the brief's case halts under neither reading; D14 keeps a negated word the name holds read as before | — |
| [D20](#d20) | Decided by the cutter (C2): row V6 reads a header as a `--- ` line directly followed by a `+++ ` line, takes a needle as added back only in the section of its own file, and drops the test of the task's prose for the header; `stop_run` names the log in a stop of exit 2 at both of its stops | the second plan review found each of these open to two readings; each reading chosen is the one Q13 and Q20 state, the narrowest that errs to silence | the whole block's lines; a header read from any `---` line |

### D1

The riders stay out: no task here touches the findings their cards name. 5c3 `marks` plans their fix.

### D2

A process decision of the plan: this change reads the brief of its own folder.

### D3

The `debt:` frontmatter of [the proposal](proposal.md) lists every card this version pays and every card it closes with no fix. No task names a card of the second kind. The cut looked each id up in the debt file; the release deletes each and reports one it does not find.

### D4

A decision of the plan, done before the queue: the closed cards' text stands in the vault, beside the brief.

### D5

`_Tail.write` keeps `CUT_KEPT` lines of the cut's output, each cut to 4000 characters. A cut line keeps its newline when it had one, so the next line stays its own. `_cut_checked` takes the checker's exit 1 for a failed plan only when a line of the output starts with the halt marker; a crash whose text quotes the marker mid-line is a checker that could not run.

### D6

Step 4.3 of `skills/mf-integrate/SKILL.md` has a row for the supervisor's settle: it names each path the index changed, not each path the note named. D61 and the threat model already accept a settle that stages any Markdown under `openspec/` and `docs/`; the row says so in the commit body, a line a path. The rest of the six are [D13](#d13)'s reaches.

### D7

Both rows err to silence: a row that halts a valid cut costs a second cutter or a halt, one that stays silent costs a failed `Verify:` the build finds.

### D8

D76's *Accepts* clause says the headroom read counts any Codex use. It also says a spawn's recorded share, the rise between an account-wide read before and one after, counts the use of the account made while the spawn ran: a parallel version's, and the operator's. The titles of the Codex window metrics in `metrics/catalogue.toml` say the same, as `Codex 5-hour window used, account-wide` and `Codex weekly window used, account-wide`.

### D9

The cards 0065·R8, 0085·R3, 0143·S2 and 0146·S12 are in `debt:` and in no task. Their facts stand at `HEAD`, as the brief's facts say.

### D10

A minor: the requirements of [the delta](specs/sdd/spec.md) change, and D76's text.

### D11

Noted for a later round; no task.

### D12

0147·S3 is in `debt:` and in no task.

### D13

**The drain.** `sandboxed()` ends a command's group at its deadline. It then reads the output for at most the grace it already holds, and closes the pipe, as `plan_check.run` does after its own deadline. A command that ends in time is read to its end as before. The bound is in `sandboxed()`, so the cut's checks, the card checks of converge and every other caller have it.

**The trailer.** `plan_text` takes a fix commit that edits the spec delta or rewords a decision's body only when its `Plan-text:` trailer holds at least one id of a card in the change's findings files. Other words of the trailer are passed over; a security card's id is refused as before; a commit that edits no plan text needs no trailer.

**The environment.** `_operator_env()` returns the conductor's environment without every `UV_` and `PIP_` name and without `VIRTUAL_ENV`. Preparation, the fetch's preparation and `sandboxed()` build from it, `sandboxed()` also without the tokens, and each sets its own `UV_CACHE_DIR`, `sandboxed()` its `UV_OFFLINE`. A Claude and a Codex worker start through `env`, which unsets `VIRTUAL_ENV`, then each `UV_` and `PIP_` name the conductor holds, in sorted order, as `-u` pairs before `HOOKS_OFF` and any assignment. A test that reads the command's prefix clears those names first, so it holds on any host. An operator's `UV_PYTHON` no longer reaches a worker, and that is accepted.

**The run log.** An `OSError` of the log's write in the run's halt handler, or at either stop of `stop_run`, becomes a `Stop` with exit 2 reading `stop: cannot write .minions/runs/<log> · <reason>`; inside the `except Stop` of `stop_run`, the earlier stop's text follows, after ` · `, and the exit is 2 still. The log is not made again; a link or a pipe there is refused as before.

**The viewer.** `start` forgets the pid and port files after its child exits only while the pid file holds that child's pid.

### D14

**V2.** `selects` reads an identifier under a `not` that the name does not hold as unknown, and picks no test for that name. A negated identifier the name holds, and every identifier outside every `not`, are read as before.

**V6.** A new `_file_diffs` keeps the removed and added lines of a sub-task by the file its block's `---` and `+++` header names, the `a/` and `b/` prefixes dropped. `row_v6` reads it in place of `_diffs`, and halts only when the needle is removed, and added in none of the block's lines, in a block whose header names a file the search names. A **header** is a line that starts `--- ` directly followed by a line that starts `+++ `; any other line that starts `---` or `+++` is a changed line. The pair names one file: the path after `+++ `, else the path after `--- ` when the first is `/dev/null`; text after a tab and a leading `a/` or `b/` are dropped; a pair that names `/dev/null` twice names none. The pair starts a section, and a changed line belongs to the latest pair above it. The needle counts as added back only in a section of the same file. A block with no header takes no part. `row_v6` no longer asks that the task's prose name the file: the header does. `_diffs` stays as the reader of row `K7`, which takes a block with no header as before.

### D15

No task of any phase opens `.minions/debt.md`.

### D16

Phase 3 builds on the build's strong model; the other phases and the close build on the moderate model.

### D17

A process decision of the plan.

### D18

A process decision of the queue.

### D19

The cases of V2 are in [the cases](#cases).

### D20

The grammar of a header and the stop's text are in [D14](#d14) and [D13](#d13). The cases are in [the cases](#cases).

## Cases

Each case is red before its edit and green after, save the guards: the drain's cases for the cut and a card's check, and for a command that ends in time, which the bound of `sandboxed()` already gives when they are added.

| fix | case |
|---|---|
| V2 | `-k "widget and not slow"` over `test_widget` is silent; `-k "a or not b"` over `test_a_b` halts as before; `-k "widget and not widget_old"` over `test_widget_old` is silent ([D19](#d19)) |
| V6 | a needle removed from one file's block and searched in another's does not halt; one removed and not added back in the searched file's section halts; one removed under the searched file's header and added under another file's header halts; a later task whose prose names the searched file and whose header names another does not halt; a block with no header takes no part; a removed line `-- x` is a changed line, not a header |
| the kept output | a line over 4000 characters followed by another stays a line apart from it |
| the marker | a crash whose text quotes the marker mid-line is a checker that could not run, not a failed plan |
| the environment | an operator's `UV_PYTHON` is in neither a worker's environment nor the fetch preparation's |
| the run log | a log removed mid-run ends `conduct.py run` with exit 2 naming it, no traceback; `stop_run` on a log it cannot write ends in the same stop, at its stop after a kill and at its stop inside a failed clear |
| the drain | a command whose child leaves its group holding the pipe returns after the deadline, for a card's check and for a cut's; a command that ends in time is read whole |
| the trailer | `Plan-text: none` and a misspelled id are refused; an id with prose beside it passes; a commit that edits no plan text and carries no trailer passes |
| the viewer | a start that loses the bind leaves the winner's pid and port files |

## Tests

No test is deleted or merged, so `I16` holds no table. No end-to-end run is added: each new test is a unit test at the lowest layer that can fail for its case (`T1`). A new test that runs over 5 s carries the `slow` marker.

| test | layer | the step it carries |
|---|---|---|
| `test_v2_is_silent_on_a_negated_word_the_name_lacks` (new, `tests/test_cut_check.py`) | unit | the V2 cases of [the cases](#cases) |
| `test_v6_reads_the_searched_files_block_by_its_header` (new, `tests/test_cut_check.py`) | unit | the V6 cases |
| `test_a_kept_line_cut_at_4000_characters_keeps_its_newline` (new, `tests/test_conduct.py`) | unit | the kept output |
| `test_a_crash_that_quotes_the_halt_marker_mid_line_is_no_failed_plan` (new, `tests/test_conduct.py`) | unit | the marker |
| `test_an_operators_uv_python_reaches_no_preparation_or_fetch` and `test_an_operators_uv_python_reaches_no_worker` (new, `tests/test_conduct.py`) | unit | the environment |
| `test_a_run_log_removed_mid_run_ends_the_run_in_a_named_stop` (new, `tests/test_conduct.py`), `test_case_e_stop_run_names_a_log_it_cannot_write` and `test_case_e_stop_run_names_a_log_it_cannot_write_after_a_failed_clear` (new, `tests/test_runlog.py`) | unit | the run log, at each stop of `stop_run` |
| `test_a_child_that_leaves_the_group_holding_the_pipe_returns_after_the_deadline` and `test_a_command_that_ends_in_time_is_read_whole` (new, `tests/test_sandboxed.py`) | unit | the drain |
| `test_a_cuts_command_whose_child_holds_the_pipe_ends_at_the_deadline` and `test_a_cards_check_whose_child_holds_the_pipe_ends_at_the_deadline` (new, `tests/test_conduct.py`) | unit | the drain, for the cut and a card's check |
| `test_a_trailer_naming_no_card_of_the_findings_is_refused` and `test_a_trailer_with_prose_beside_a_card_id_passes` (new, `tests/test_converge.py`) | unit | the trailer |
| `test_a_start_that_loses_the_bind_leaves_the_winners_files` (new, `tests/test_viewer.py`) | unit | the viewer |

Edited, not removed: `test_v2_halts_only_on_a_selected_test`, `test_a_k_expression_selects_by_pytests_rules`, `test_each_mechanical_row_fails_by_name` and `test_a_needle_a_later_task_adds_back_passes_v6` (`tests/test_cut_check.py`); `test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment` (`tests/test_sandboxed.py`), which gains `UV_PYTHON` and `PIP_INDEX_URL`; the tests of `tests/test_conduct.py` that read a worker command's prefix after `env -u VIRTUAL_ENV`; `test_a_fix_commit_may_edit_the_delta_with_the_trailer` and `test_a_fix_commit_editing_a_decisions_body_is_taken` (`tests/test_converge.py`), which commit a trailer naming a card their findings files lack.

## Dependencies

None.

## Risks / Trade-offs

- V2 now stays silent for any expression with a `not` whose word the name lacks, even when a positive term does select a later-changed test, as `widget and not slow` does. The scenario `not widget and gadget` over `test_gadget` flips from a halt to silence. A missed halt costs a failed `Verify:`, which the build runs and finds.
- A worker that sets `UV_PYTHON` itself still can: the rule drops the operator's variables, not a worker's own.
- A drain bound past the deadline can lose the last lines of a command that writes after its group ended; the lines belong to a child that left the group.
- A trailer naming a card of the findings that the fix does not clear passes: the verify pass judges the wording against the code, as before ([D13](#d13)).

## Verdict

Ready to build.
