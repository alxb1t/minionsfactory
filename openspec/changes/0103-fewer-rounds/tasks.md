# Fewer rounds — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code, save the guards its
`## Tests` names.

## Progress

- [x] 1 — The round-1 pickup and the mechanism repeat
- [x] 2 — The fix note
- [x] 3 — The plan check
- [x] 4 — The corpus
- [x] 5 — CommonMark readers
- [x] 6 — The plan review's model
- [ ] 7 — The record

## 1 — The round-1 pickup and the mechanism repeat

- [x] 1.1 **HALT CHECK** Confirm Step 8's pickup check is still no round in `skills/mf-converge/SKILL.md`, as
  [D1](design.md#d1) needs; missing, the plan is wrong.
  Verify: `grep -n "the pickup check is no round" skills/mf-converge/SKILL.md` prints a line.
- [x] 1.2 In `skills/mf-converge/SKILL.md`, make [D1](design.md#d1)'s Step 6, round-1 pickup, Step 8, due-rule, resume-row,
  events-row and diagram edits.
  Verify: `grep -n "with the fix" skills/mf-converge/SKILL.md` prints a line.
- [x] 1.3 In `skills/mf-converge/SKILL.md`, append [D1](design.md#d1)'s *Nothing committed* sentence to Step 6's paragraph on
  a fixer that committed nothing.
  Verify: `grep -n "checked — nothing" skills/mf-converge/SKILL.md` prints a line.
- [x] 1.4 In `skills/mf-converge/references/worker.md`, make [D2](design.md#d2)'s edits to *A repeat escalates*, the
  **Priority** row and the **Related** row.
  Verify: `grep -n "mechanism repeat" skills/mf-converge/references/worker.md` prints a line.

## 2 — The fix note

- [x] 2.1 Add the fix-note steps to `test_a_rescue_decides_under_the_switch` in `tests/test_conduct.py`, per the design's
  `## Tests` row.
  Verify: `grep -n "Fix note (2026-11-08, R2)" tests/test_conduct.py` prints a line.
- [x] 2.2 In `skills/mf-ship/scripts/conduct.py`, add `FIX_NOTE` and `_decisions`' split, and name the note in `_amend`'s
  docstring, per [D3](design.md#d3), each new why line citing `0103-fewer-rounds design D3`.
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue_decides_under_the_switch` reports `1 passed`.
- [x] 2.3 In `skills/mf-converge/SKILL.md`, edit the fixer's plan bullet and Step 10's sentences, and in
  `skills/mf-converge/references/worker.md` the amend card, per [D3](design.md#d3).
  Verify: `grep -l "fix note" skills/mf-converge/SKILL.md skills/mf-converge/references/worker.md` prints both paths.

## 3 — The plan check

- [x] 3.1 Add `tests/test_plan_check.py` with `test_a_plan_check_finds_what_the_plan_left` and
  `test_what_the_plan_check_cannot_read_exits_2`, their steps for checks 1 to 4 of [D4](design.md#d4), per the design's
  `## Tests` rows; the corpus steps come in 4.4.
  Verify: `grep -n "def test_what_the_plan_check_cannot_read_exits_2" tests/test_plan_check.py` prints a line.
- [x] 3.2 Write `skills/mf-converge/scripts/plan_check.py` with checks 1 to 4, per [D4](design.md#d4), its docstring citing
  `0103-fewer-rounds design D4`.
  Verify: `uv run pytest -q tests/test_plan_check.py` reports `2 passed`.
- [x] 3.3 In `skills/mf-build/SKILL.md`, open Step 3.6 with [D4](design.md#d4)'s plan-check paragraph.
  Verify: `grep -n "stop: plan check" skills/mf-build/SKILL.md` prints a line.
- [x] 3.4 In `skills/mf-converge/SKILL.md`, add [D4](design.md#d4)'s fixer bullet to Step 6 and its plan-check paragraph to
  Step 7, after `gate_check.py`.
  Verify: `grep -n "counting no round" skills/mf-converge/SKILL.md` prints a line.
- [x] 3.5 In `skills/mf-rescue/SKILL.md`, add [D4](design.md#d4)'s plan-check row to Step 2's table and its trailer clause.
  Verify: `grep -n "Rescue: plan check" skills/mf-rescue/SKILL.md` prints a line.

## 4 — The corpus

- [x] 4.1 Add `tests/test_corpus.py` with `test_the_corpus_runs_each_case` and `test_a_corpus_it_cannot_read_exits_2`, per the
  design's `## Tests` rows.
  Verify: `grep -n "def test_a_corpus_it_cannot_read_exits_2" tests/test_corpus.py` prints a line.
- [x] 4.2 Write `scripts/corpus.py` and `scripts/corpus.toml`, its cases named, per [D5](design.md#d5), the script's docstring
  citing `0103-fewer-rounds design D5`.
  Verify: `uv run pytest -q tests/test_corpus.py` reports `2 passed`.
- [x] 4.3 In `Makefile`, replace the `.PHONY` line, and after the `check` recipe add a blank line and the last three `+`
  lines, per [D5](design.md#d5); the `gate` and `check` recipes stay as they are:
  ```diff
  - .PHONY: fix gate check install-skills uninstall-skills
  + .PHONY: fix gate check corpus install-skills uninstall-skills
  + # The readers of run data over this checkout's run directory; no gate runs it.
  + corpus:
  + 	uv run --script scripts/corpus.py
  ```
  Verify: `make -n corpus` prints `uv run --script scripts/corpus.py`.
- [x] 4.4 Add the `**CORPUS**` steps to `test_a_plan_check_finds_what_the_plan_left` in `tests/test_plan_check.py`, then check 5
  to `skills/mf-converge/scripts/plan_check.py`, per [D5](design.md#d5).
  Verify: `grep -n "no case" skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 4.5 In `skills/mf-cut-change/SKILL.md`, add [D5](design.md#d5)'s Step 6 bullet; in `skills/mf-build/SKILL.md`, its
  Step 2 item 2 sentence.
  Verify: `grep -l "CORPUS" skills/mf-cut-change/SKILL.md skills/mf-build/SKILL.md` prints both paths.
- [x] 4.6 **HALT CHECK** Run the corpus over this checkout's run directory: a reader failing on its real data means the plan
  missed a reader's fix.
  Verify: `make corpus` exits 0.

## 5 — CommonMark readers

- [x] 5.1 Run `uv add --dev "markdown-it-py>=3,<4"`, as [D6](design.md#d6) and the design's `## Dependencies` approve.
  Verify: `grep -n "markdown-it-py>=3,<4" pyproject.toml` prints a line.
- [x] 5.2 Add the steps of the design's `## Tests` rows to `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in
  `tests/test_conduct.py` and to `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`.
  Verify: `grep -n "carriage return not before a newline" tests/test_brief_check.py` prints a line.
- [x] 5.3 Add `tests/test_markdown_corpus.py` with `test_the_markdown_readers_agree_with_the_rendered_page`, per
  [D6](design.md#d6).
  Verify: `grep -n "def test_the_markdown_readers_agree_with_the_rendered_page" tests/test_markdown_corpus.py` prints a line.
- [x] 5.4 In `skills/mf-ship/scripts/conduct.py`, set the header's dependency, add `_markdown`, rewrite `_headed` and `_rows`,
  delete `_fence`, and read `refs/heads/<id>` in `_unapproved`, `_check_cut`, `_holds` and `_tag_of`, per [D6](design.md#d6),
  each new why line citing `0103-fewer-rounds design D6`.
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_halt_is_shown` reports `1 passed`.
- [x] 5.5 In `skills/mf-plan/scripts/brief_check.py`, set the header's dependency, add `MARKDOWN`, rewrite `headed` and
  `headings`, and halt on a lone carriage return, per [D6](design.md#d6), the docstring citing `0103-fewer-rounds design D6`.
  Verify: `uv run pytest -q tests/test_brief_check.py tests/test_markdown_corpus.py` exits 0.
- [x] 5.6 Confirm no reader of the deleted fence helper is left.
  Verify: `git grep -n -w _fence -- skills tests/test_conduct.py tests/test_brief_check.py` prints nothing.
- [x] 5.7 Confirm loading `conduct.py` with no package installed still works, as `pin.py` and the escape drill load it
  ([F8](design.md#context)); a guard, per the design's `## Tests`.
  Verify: `uv run --no-project --isolated python -I -c "import runpy, sys; runpy.run_path(sys.argv[1])" skills/mf-ship/scripts/conduct.py` exits 0.

## 6 — The plan review's model

- [x] 6.1 In `skills/mf-cut-change/SKILL.md`, edit Step 8.5's first sentence per [D7](design.md#d7), keeping the review
  table's reviewer cells.
  Verify: `grep -n "model: opus" skills/mf-cut-change/SKILL.md` prints a line.
- [x] 6.2 In `skills/mf-plan/SKILL.md`, edit the cut station's default per [D7](design.md#d7).
  Verify: `grep -n "own is Sonnet 5.5" skills/mf-plan/SKILL.md` prints a line.

## 7 — The record

- [ ] 7.1 Run `grep -n "^### D[0-9]" docs/decisions.md`; add the decision [D8](design.md#d8) quotes to the group *The check
  loop and the release* in `docs/decisions.md`, `<n>` one above the highest id it printed, and `D<n>` to that group's list in
  the map.
  Verify: `grep -n "· Converge's rounds are cut at their causes$" docs/decisions.md` prints a line.
- [ ] 7.2 Edit D2 and D53 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -n "names a package the person approved" docs/decisions.md` prints a line.
- [ ] 7.3 Edit D65 and D71 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -n "fresh worker on Opus 5.5" docs/decisions.md` prints a line.
- [ ] 7.4 Edit `CODING_STANDARDS.md`'s script rule, per [D6](design.md#d6).
  Verify: `grep -n "markdown-it-py" CODING_STANDARDS.md` prints a line.
- [ ] 7.5 Add `AGENTS.md`'s `make corpus` sentence after its `make check` one, per [D8](design.md#d8).
  Verify: `grep -n "make corpus" AGENTS.md` prints a line.
- [ ] 7.6 Add [D8](design.md#d8)'s fix-note sentence and its new bullet to `THREAT_MODEL.md`'s *Entry points*.
  Verify: `grep -n "plan_check.py" THREAT_MODEL.md` prints a line.
- [ ] 7.7 **HALT CHECK** Run the plan check over this change: a line it prints is a plan the build cannot amend.
  Verify: `uv run --script skills/mf-converge/scripts/plan_check.py --change 0103-fewer-rounds --base main` prints `plan: clean`.
