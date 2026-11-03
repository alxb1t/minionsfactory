# Gate planning — tasks

Build the settled [design](design.md), one phase at a time. The skill text is the design's, word for word.

## Progress

- [ ] 1 — The message
- [ ] 2 — The cut
- [ ] 3 — The build
- [ ] 4 — The approval
- [ ] 5 — The record

## 1 — The message

- [ ] 1.1 Compute the edits before the planning-task test, and write D1's halt, in `skills/mf-converge/scripts/gate_check.py`;
  add `test_a_halt_lists_every_unquoted_line` to `tests/test_gate_check.py`, per [D1](design.md#d1).
  Verify: `grep -c 'approve-gate' skills/mf-converge/scripts/gate_check.py` prints a number above `0`, and
  `uv run pytest -q tests/test_gate_check.py -k every_unquoted_line` reports `1 passed`.

## 2 — The cut

- [ ] 2.1 Add `--tasks` to `gate_check.py`, and `I18` to the input-contract tables of `skills/mf-build/SKILL.md` and
  `skills/mf-cut-change/SKILL.md` together, with the cut's Step 8 running it; add `test_a_bare_makefile_task_fails_the_plan_check`,
  per [D2](design.md#d2).
  Verify: `grep -c '\*\*I18\*\*' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints `1` for each, and
  `uv run pytest -q tests/test_gate_check.py tests/test_skills.py -k 'plan_check or contract'` exits 0.

## 3 — The build

- [ ] 3.1 Add `--head` to `gate_check.py`, and the staged-tree check before `mf-build` Step 2's commit; add
  `test_a_staged_tree_is_checked`, per [D3](design.md#d3).
  Verify: `grep -c 'git write-tree' skills/mf-build/SKILL.md` prints `1`, and
  `uv run pytest -q tests/test_gate_check.py -k staged_tree` reports `1 passed`.

## 4 — The approval

- [ ] 4.1 Add `--digest` and the approval read to `gate_check.py`, `approve-gate` to `skills/mf-ship/scripts/conduct.py`, its
  row to `skills/mf-ship/SKILL.md`, and the approval to converge's precondition 6 and the release's gate step; add
  `test_an_approval_passes_until_the_diff_moves` and `test_approve_gate_records_the_hash`, per [D4](design.md#d4).
  Verify: `grep -c 'def approve_gate' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_gate_check.py tests/test_conduct.py -k 'approval_passes or approve_gate'` reports `2 passed`.

## 5 — The record

- [ ] 5.1 Edit `skills/mf-build/SKILL.md`'s start row, `skills/mf-release/SKILL.md`'s last line, and the diagrams in `README.md`,
  `docs/README.md` and `docs/decisions.md`, per [D5](design.md#d5).
  Verify: `git grep -c 'grill the next version' -- skills` prints nothing, and
  `grep -c 'a ## Progress. box is unticked' skills/mf-build/SKILL.md` prints `1`.
