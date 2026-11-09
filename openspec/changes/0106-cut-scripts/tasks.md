# Cut scripts — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code, save the guards its
`## Tests` names.

## Progress

- [x] 1 — The brief's parser · hard
- [x] 2 — facts.py · hard
- [x] 3 — cut_pre.py and cut_check.py · hard
- [x] 4 — The queue writes the models file · hard
- [ ] 5 — The skills and the record · hard

## 1 — The brief's parser

- [x] 1.1 **HALT CHECK** Confirm `headed()` in `skills/mf-plan/scripts/brief_check.py` still ends a section on a `lower().startswith`
  prefix, as [D3](design.md#d3) needs; missing, the plan is wrong.
  Verify: `grep -n "lower().startswith" skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.2 Add `test_a_fact_citing_a_path_and_a_line_is_ready` and `test_a_fact_out_of_grammar_halts` to `tests/test_brief_check.py`,
  per the `## Tests` rows of [D1](design.md#d1).
  Verify: `grep -n "def test_a_fact_out_of_grammar_halts" tests/test_brief_check.py` prints a line.
- [x] 1.3 Add `test_models_prints_the_items_toml` and `test_a_custom_tag_opens_no_section` to `tests/test_brief_check.py`, per
  [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -n "def test_a_custom_tag_opens_no_section" tests/test_brief_check.py` prints a line.
- [x] 1.4 In `skills/mf-plan/scripts/brief_check.py`, add `FACT`, the fact halts and `--facts` as [D1](design.md#d1) says, and
  describe them in the module docstring; each new why line cites `0106-cut-scripts design D1`.
  Verify: `uv run pytest -q tests/test_brief_check.py -k "fact"` passes.
- [x] 1.5 In `skills/mf-plan/scripts/brief_check.py`, add `models_toml` and the `--models <brief> <slug>` form as
  [D2](design.md#d2) says; the positional `brief` stays, a `slug` positional follows it.
  Verify: `uv run pytest -q tests/test_brief_check.py -k "models_prints"` passes.
- [x] 1.6 In `skills/mf-plan/scripts/brief_check.py`, add `BLOCK_HEADING` beside `INLINE_HEADING` and use it in `headed()` in place of the
  `startswith` test, and cut `headed()`'s docstring to 3 lines, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_brief_check.py tests/test_markdown_corpus.py` passes.

## 2 — facts.py

- [x] 2.1 **HALT CHECK** Confirm `brief_check.py` now names `--facts`, which `facts.py` calls ([D4](design.md#d4)); missing, phase 1
  is not built.
  Verify: `grep -n -e "--facts" skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 2.2 Add `tests/test_facts.py` with the `place` rows of `## Tests`: `test_a_fact_on_an_untouched_path_stands`,
  `test_a_fact_whose_lines_shifted_is_moved`, `test_a_fact_on_a_changed_line_is_unplaced` and
  `test_a_fact_with_no_commit_or_a_bad_sha_is_unplaced`, in a scratch repository, feeding facts to `place_all`.
  Verify: `grep -n "def test_a_fact_with_no_commit_or_a_bad_sha_is_unplaced" tests/test_facts.py` prints a line.
- [x] 2.3 Add to `tests/test_facts.py` `test_readers_print_each_hit_or_none`, `test_the_notes_file_is_written_and_appended`,
  `test_what_cannot_be_read_exits_2` and `test_the_brief_reaches_the_placer`, the last with the runner swapped.
  Verify: `grep -n "def test_the_brief_reaches_the_placer" tests/test_facts.py` prints a line.
- [x] 2.4 Write `skills/mf-cut-change/scripts/facts.py`: the `uv` script header with `dependencies = []`, the runner constant, and
  `place` with the placement of [D4](design.md#d4), exits 0, 1 and 2.
  Verify: `uv run pytest -q tests/test_facts.py -k "stands or moved or unplaced"` passes.
- [x] 2.5 In `facts.py`, add `readers` and the `--notes` writing of [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_facts.py` passes.

## 3 — cut_pre.py and cut_check.py

- [x] 3.1 Add `tests/test_cut_pre.py` with the `## Tests` rows of [D5](design.md#d5), in a scratch repository with a
  `gate` target and a fake `openspec` first on `PATH`.
  Verify: `grep -n "def test_unattended_preconditions" tests/test_cut_pre.py` prints a line.
- [x] 3.2 Write `skills/mf-cut-change/scripts/cut_pre.py` per [D5](design.md#d5): one function a check, `main`, exits 0, 1 and 2.
  Verify: `uv run pytest -q tests/test_cut_pre.py` passes.
- [x] 3.3 Add `tests/test_cut_check.py` with the `## Tests` rows of [D6](design.md#d6), under a fake `openspec` on `PATH`.
  Verify: `grep -n "def test_each_mechanical_row_fails_by_name" tests/test_cut_check.py` prints a line.
- [x] 3.4 Write `skills/mf-cut-change/scripts/cut_check.py` with the rows `I2`, `I4`, `I11`, `I12`, `I13` and `I14` of
  [D6](design.md#d6), and `main` with its printed forms and exits.
  Verify: `uv run pytest -q tests/test_cut_check.py -k "mechanical and (I2 or I4 or I11 or I12 or I13 or I14)"` passes.
- [x] 3.5 In `cut_check.py`, add the rows `I17`, `A1`, `A2`, `P9` and `P13`, and the judgment rows with the `P12` and `P13`
  candidates, per [D6](design.md#d6); `cut_pre.py` loads by `runpy` for the open versions.
  Verify: `uv run pytest -q tests/test_cut_check.py -k "mechanical and (I17 or A1 or A2 or P9 or P13)"` passes.
- [x] 3.6 In `cut_check.py`, fold in `openspec validate`, `gate_check.py --tasks`, `verify_check.py` and the corpus check of
  `plan_check.py`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_cut_check.py` passes.
- [x] 3.7 Cut the module docstrings of `scripts/corpus.py` and `skills/mf-converge/scripts/plan_check.py` to 3 lines each, keeping each
  `Why:` citation, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_corpus.py tests/test_plan_check.py` passes.

## 4 — The queue writes the models file

- [x] 4.1 **HALT CHECK** Confirm `_check_cut` in `skills/mf-ship/scripts/conduct.py` still only tests that `models.toml` stands, as
  [D7](design.md#d7) needs; missing, the plan is wrong.
  Verify: `grep -n 'models.toml").is_file' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 4.2 In `tests/test_conduct.py`, edit `test_parallel_cuts_reserve_apart_and_start_one_run`, which `cut()` turns red: each brief it
  queues holds an item per slug, `UV_RUN` is swapped for this interpreter, and each entry holds `models`.
  Verify: `grep -n "UV_RUN" tests/test_conduct.py` prints a line.
- [x] 4.3 Add `test_a_cut_queues_its_models_file` to `tests/test_conduct.py`, per [D7](design.md#d7): the file, the entry's text, and
  exit 2 with nothing reserved for a brief with no item.
  Verify: `grep -n "def test_a_cut_queues_its_models_file" tests/test_conduct.py` prints a line.
- [x] 4.4 Extend `test_a_queued_cut_is_cut_then_built` and `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in `tests/test_conduct.py` with
  the steps of their `## Tests` rows, the custom-tag texts of [D3](design.md#d3) in the `_unapproved` loop among them.
  Verify: `grep -n "models.toml changed since the cut was queued" tests/test_conduct.py` prints a line.
- [x] 4.5 In `skills/mf-ship/scripts/conduct.py`, add `UV_RUN`, `BRIEF_CHECK` and the models read, and make `cut()` write the file and
  the entry's `models`, per [D7](design.md#d7); each new why line cites `0106-cut-scripts design D7`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "queues_its_models or reserve_apart"` passes.
- [x] 4.6 In `conduct.py`, write the entry's text again at the start of `cutting()`, before its test of the branch, and make
  `_check_cut` read the entry's text from the queue and fail a changed file, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k "cut_then_built or rejoin_cuts_again"` passes.
- [x] 4.7 In `conduct.py`, define `BLOCK_HEADING` beside `INLINE_HEADING`, use it in `_boundary` in place of the prefix test, and
  cut the docstrings of `_headed` and `_rows` to 3 lines, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k "rejoin_cuts_again"` passes.

## 5 — The skills and the record

- [ ] 5.1 In `tests/test_skills.py`, add the pairs [D9](design.md#d9) lists to `_METRICS_SCRIPTS`, and their `not named` lines to
  each expected list of the missing-script scan.
  Verify: `grep -n "scripts/cut_check.py" tests/test_skills.py` prints a line.
- [ ] 5.2 In `docs/decisions.md`, place the text of D77 from [D9](design.md#d9) after `### D69`, and add `D77` to the Planning
  group's index line.
  Verify: `grep -n "^### D77 · A mechanical step is a script" docs/decisions.md` prints a line.
- [ ] 5.3 In `docs/decisions.md`, make the edits [D9](design.md#d9) lists to `### D7`, `### D40` and `### D41`.
  Verify: `grep -n "facts.py" docs/decisions.md` prints a line.
- [ ] 5.4 In `skills/mf-cut-change/SKILL.md`, rewrite Step 1 to run `cut_pre.py`, keeping the hold, the run directory and
  `Workspace setup:`, per [D5](design.md#d5) and [D9](design.md#d9).
  Verify: `git grep -l scripts/cut_pre.py -- skills/mf-cut-change/SKILL.md` lists the file.
- [ ] 5.5 In `skills/mf-cut-change/SKILL.md`, rewrite Step 2's moved facts, helpers and notes to `facts.py place`, helpers for
  unplaced facts only, and Step 3's readers to `facts.py readers`, per [D4](design.md#d4).
  Verify: `git grep -l scripts/facts.py -- skills/mf-cut-change/SKILL.md` lists the file.
- [ ] 5.6 In `skills/mf-cut-change/SKILL.md`, rewrite Step 8 to run `cut_check.py` and hold its summary line and judgment rows
  alone, add its output to Step 8.5's packet, and call `gate_check.py --tasks` the gate-edit check, per [D6](design.md#d6).
  Verify: `git grep -l scripts/cut_check.py -- skills/mf-cut-change/SKILL.md` lists the file.
- [ ] 5.7 In `skills/mf-cut-change/SKILL.md`, edit Step 11 and *Suggesting models*: `conduct.py` wrote the unattended file, and a
  cut by hand writes what `brief_check.py --models` prints, per [D7](design.md#d7).
  Verify: `git grep -n -e "--models" -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 5.8 In `skills/mf-plan/SKILL.md`, make the `## Facts` line of the brief's template the grammar of [D1](design.md#d1), the
  re-measure row run `../mf-cut-change/scripts/facts.py`, and the models-file sentence name `conduct.py`.
  Verify: `uv run pytest -q tests/test_skills.py` passes.
