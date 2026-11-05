# Lighter cut — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — The brief's At line
- [ ] 2 — Only moved facts, with helpers
- [ ] 3 — The review and the show
- [ ] 4 — verify_check and a link

## 1 — The brief's At line

- [ ] 1.1 Add `At <sha>, <YYYY-MM-DD>.` to `skills/mf-plan/SKILL.md`'s brief template and its Step 5, per [D1](design.md#d1).
  Verify: `grep -n 'At <sha>, <YYYY-MM-DD>' skills/mf-plan/SKILL.md` prints a line.

## 2 — Only moved facts, with helpers

- [ ] 2.1 Read the `At` line and list the moved facts in `skills/mf-cut-change/SKILL.md`'s Step 2, re-check only those in Step 3,
  and reword the I10 row's "how" cell, per [D2](design.md#d2).
  Verify: `grep -n 'git diff --name-only <sha>..HEAD' skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 2.2 Add the helpers to `skills/mf-cut-change/SKILL.md`'s Step 2, per [D3](design.md#d3).
  Verify: `grep -n 'not back in five minutes' skills/mf-cut-change/SKILL.md` prints a line.

## 3 — The review and the show

- [ ] 3.1 Narrow Step 8.5's question and point Step 9 at `tasks.md`, in `skills/mf-cut-change/SKILL.md`, per [D4](design.md#d4)
  and [D5](design.md#d5); amend D7 and D40 in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -n 'the search script did not run' skills/mf-cut-change/SKILL.md` prints a line, and
  `grep -n 'lines it names' skills/mf-cut-change/SKILL.md` prints a line.

## 4 — verify_check and a link

- [ ] 4.1 Judge a `git grep`'s paths without the export, and turn a failed export into exit 2, in
  `skills/mf-cut-change/scripts/verify_check.py`, per [D6](design.md#d6); extend `test_what_cannot_run_exits_2` in
  `tests/test_verify_check.py` with a repository tracking a link out of its tree.
  Verify: `grep -n 'TarError' skills/mf-cut-change/scripts/verify_check.py` prints a line, and
  `uv run pytest -q tests/test_verify_check.py -k what_cannot_run_exits_2` reports `1 passed`.
