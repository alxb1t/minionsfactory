# Debt paydown 2 — tasks

Build the settled [design](design.md), one phase at a time; each fix's test step goes red before its fix.

## Progress

- [x] 1 — The conductor's small cards
- [x] 2 — The brief check
- [x] 3 — The status-log stamp
- [x] 4 — The archives and the threat model
- [x] 5 — The whitespace rule

## 1 — The conductor's small cards

- [x] 1.1 Add the plain-file step to `test_a_run_moves_an_old_backlog_to_the_debt` in `tests/test_conduct.py`, as the design's
  `## Tests` says, then the file check in `Run.migrate_debt` of `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k run_moves_an_old_backlog_to_the_debt` reports `1 passed`.
- [x] 1.2 Edit the `0018-v` assertion of `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in `tests/test_conduct.py`, then the
  kept line in `Run.cutting` of `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_halt_is_shown_and_rejoin_cuts_again` reports `1 passed`.
- [x] 1.3 Add the kept-worktree sentence to the `cut-halted` row of `skills/mf-ship/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -n 'git worktree remove <path>' skills/mf-ship/SKILL.md` prints a line.
- [x] 1.4 Extend the bottom-take step of `test_a_halt_answered_on_disk_comes_back` in `tests/test_conduct.py`, then the sleep in
  `Run.join` of `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k halt_answered_on_disk_comes_back` reports `1 passed`.
- [x] 1.5 Wrap `Run.hold` in `test_an_amend_during_a_rescue_goes_on` in `tests/test_conduct.py`, then discard the diagnosis in
  `Run.hold` of `skills/mf-ship/scripts/conduct.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k amend_during_a_rescue_goes_on` reports `1 passed`.

## 2 — The brief check

- [x] 2.1 Add the item-form and second-`after:` steps to `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`, then
  both halts in `fields` and `head` of `skills/mf-plan/scripts/brief_check.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_brief_check.py -k brief_out_of_shape_halts` reports `1 passed`.
- [x] 2.2 Rewrite the why line of `skills/mf-plan/scripts/brief_check.py`'s module docstring, per [D5](design.md#d5).
  Verify: `grep -L 'converge card' skills/mf-plan/scripts/brief_check.py` prints `skills/mf-plan/scripts/brief_check.py`.

## 3 — The status-log stamp

- [x] 3.1 Add `skills/mf-converge/scripts/stamp.py`, per [D7](design.md#d7), and `tests/test_stamp.py`, as the design's
  `## Tests` names its tests.
  Verify: `uv run pytest -q tests/test_stamp.py` reports `2 passed`.
- [x] 3.2 Rewrite the event and run-heading lines of *The status log* in `skills/mf-converge/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n 'scripts/stamp.py' skills/mf-converge/SKILL.md` prints a line.
- [x] 3.3 Add `stamp.py` to `_METRICS_SCRIPTS` and to each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` in `tests/test_skills.py`, per [D7](design.md#d7).
  Verify: `grep -n '"scripts/stamp.py"' tests/test_skills.py` prints a line.

## 4 — The archives and the threat model

- [x] 4.1 Correct D2 of `openspec/changes/archive/0071-ship-fixes/design.md`, per [D8](design.md#d8).
  Verify: `grep -L -e 'reads it before its' -e 'fails on the sha being' openspec/changes/archive/0071-ship-fixes/design.md` prints `openspec/changes/archive/0071-ship-fixes/design.md`.
- [x] 4.2 Correct D1 of `openspec/changes/archive/0076-context-cost/design.md`, per [D8](design.md#d8).
  Verify: `grep -L 'above the logs found' openspec/changes/archive/0076-context-cost/design.md` prints `openspec/changes/archive/0076-context-cost/design.md`.
- [x] 4.3 Correct D1, its flow, the `## Tests` bullet and the *Risks* line of
  `openspec/changes/archive/0084-ship-fixes-2/design.md` for `0084·R4`, per [D8](design.md#d8).
  Verify: `grep -n '_granted_run' openspec/changes/archive/0084-ship-fixes-2/design.md` prints a line.
- [x] 4.4 Correct D6 and its `## Tests` bullet in `openspec/changes/archive/0084-ship-fixes-2/design.md` for `0084·R6`, per
  [D8](design.md#d8).
  Verify: `grep -L 'which a run.s worker writes' openspec/changes/archive/0084-ship-fixes-2/design.md` prints `openspec/changes/archive/0084-ship-fixes-2/design.md`.
- [x] 4.5 Correct D4 of `openspec/changes/archive/0085-self-healing-ship/design.md`, per [D8](design.md#d8).
  Verify: `grep -L 'the text from that heading to the next' openspec/changes/archive/0085-self-healing-ship/design.md` prints `openspec/changes/archive/0085-self-healing-ship/design.md`.
- [x] 4.6 Correct D3, D4's D59 text and `## Tests` of `openspec/changes/archive/0083-plan-queues/design.md`, per
  [D8](design.md#d8).
  Verify: `grep -L -e 'merge and push each' -e "today's" openspec/changes/archive/0083-plan-queues/design.md` prints `openspec/changes/archive/0083-plan-queues/design.md`.
- [x] 4.7 Add the item-head and models checks to D1 of `openspec/changes/archive/0083-plan-queues/design.md`, per
  [D8](design.md#d8).
  Verify: `grep -n 'not a slug' openspec/changes/archive/0083-plan-queues/design.md` prints a line.
- [x] 4.8 Correct *What Changes* of `openspec/changes/archive/0083-plan-queues/proposal.md`, per [D8](design.md#d8).
  Verify: `grep -L "today's" openspec/changes/archive/0083-plan-queues/proposal.md` prints `openspec/changes/archive/0083-plan-queues/proposal.md`.
- [x] 4.9 Reword the carded list, the config-race line and the LFS line of *Known gaps* in `THREAT_MODEL.md`, per
  [D9](design.md#d9).
  Verify: `grep -L -e '0049·S7' -e '0049·R15' THREAT_MODEL.md` prints `THREAT_MODEL.md`.
- [x] 4.10 Add the `0050·R11` line to *Known gaps* in `THREAT_MODEL.md`, per [D9](design.md#d9).
  Verify: `grep -n '0050·R11.: a concurrent worker' THREAT_MODEL.md` prints a line.

## 5 — The whitespace rule

- [x] 5.1 Add the whitespace rule to `main` of `skills/mf-plan/scripts/brief_check.py`, per [D5](design.md#d5), once 5.2's steps
  run red: a line of `## Decisions` or `## For the cut` holding a character other than a space or a tab for which
  `isspace()` holds halts `<section> line <n>: whitespace other than a space or a tab`. Remove a per-form fold the rule makes
  dead only if the tests still pass; the CHANGELOG's brief-check line names the rule.
  Verify: `grep -n 'whitespace other than a space or a tab' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 5.2 Add the whitespace-rule steps to `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`, as the design's
  `## Tests` row says: lines of NBSP, U+3000, `\x0b` and `\x0c` each halt with their section and line number, R5's NBSP-led head
  after a blank line among them; the vertical-tab and `unblank` steps expect the rule's line.
  Verify: `uv run pytest -q tests/test_brief_check.py -k brief_out_of_shape_halts` reports `1 passed`.
