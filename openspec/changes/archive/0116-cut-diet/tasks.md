# Cut diet — tasks

The phases: the context pack, the scaffold with the `V2` fix, then the skill, the cache and the decisions. Each phase ends green.

## Progress

- [x] 1 — cut_context.py: the context pack · hard
- [x] 2 — cut_context.py --scaffold, and row V2 on a negated -k · hard
- [x] 3 — The skill, the cache, the decisions and the skill's tests · hard

## 1 — cut_context.py: the context pack

- [x] 1.1 **HALT CHECK** the seams the pack reads from exist ([D4](design.md#d4)).
  Verify: `git grep -n -e '^def sections(' -e '^def place_all(' -e '^def brief_facts(' -e '^def write_notes(' -e '^def cards(' -e '^def matched(' -e '^def decisions_text(' -- skills/mf-plan/scripts/brief_check.py skills/mf-cut-change/scripts/facts.py skills/mf-converge/scripts/debt_match.py skills/mf-converge/scripts/bundle.py` prints a line for each.
- [x] 1.2 In `skills/mf-plan/scripts/brief_check.py` add `--sections` to the exclusive group, printing `json.dumps(sections(brief))` ([D8](design.md#d8)); add `test_the_sections_flag_prints_each_section_as_json` to `tests/test_brief_check.py`.
  Verify: `uv run pytest -q tests/test_brief_check.py -k sections_flag` exits 0.
- [x] 1.3 Create `skills/mf-cut-change/scripts/cut_context.py` with its PEP 723 header, docstring, `Stop`, the constants `RUNNER`, `BRIEF_CHECK`, `FACTS`, `BUNDLE`, `DEBT_MATCH` and `SLICE_LINES` (80), and `brief_sections(brief)`, which runs `--sections` by `RUNNER` ([D4](design.md#d4), [D8](design.md#d8)); create `tests/test_cut_context.py` with a loader that swaps `RUNNER` for the interpreter, and `test_the_brief_sections_come_from_brief_check`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k brief_sections_come` exits 0.
- [x] 1.4 In `skills/mf-cut-change/scripts/cut_context.py` add `item_parts(sections, slug)`, the ` · ` parts of the `## For the cut` item whose first part, stripped of `*` and backticks, is `slug`, else none ([D4](design.md#d4)); add `test_the_item_of_a_slug_gives_its_parts` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k item_of_a_slug` exits 0.
- [x] 1.5 In `skills/mf-cut-change/scripts/cut_context.py` add `cite_lines(cite)`, the numbered lines of a cite at `HEAD` from `git show`, cut at `SLICE_LINES` with a line saying where, or a line saying the file is missing ([D4](design.md#d4)); add `test_a_cite_is_read_at_head_and_cut_at_the_cap` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k cut_at_the_cap` exits 0.
- [x] 1.6 In `skills/mf-cut-change/scripts/cut_context.py` add `facts_section(brief)`, the `## The facts at HEAD` text and the placed facts ([D4](design.md#d4)).
  It loads `facts.py` by `importlib`, sets its `RUNNER` to this script's, and calls `brief_facts` and `place_all`, a `Stop` of it ending the run with its code; add `test_a_fact_is_listed_with_its_state_and_lines` to `tests/test_cut_context.py`. Verify: `uv run pytest -q tests/test_cut_context.py -k listed_with_its_state` exits 0.
- [x] 1.7 In `skills/mf-cut-change/scripts/cut_context.py` add `decisions_section(brief)`, the stdout of `bundle.py --decisions` run by `RUNNER`, a failure stopping with exit 2 ([D4](design.md#d4)); add `test_the_decisions_are_bundles_stdout` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k decisions_are_bundles` exits 0.
- [x] 1.8 In `skills/mf-cut-change/scripts/cut_context.py` add `requirements_sections(brief)`: each requirement block of the living specs whose title the brief holds, and the index line `<capability>:<line> · <title>` of every title ([D4](design.md#d4)); add `test_a_requirement_the_brief_names_is_read_in_full` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k brief_names_is_read` exits 0.
- [x] 1.9 **CORPUS** `debt-match` In `skills/mf-cut-change/scripts/cut_context.py` add `run_dir()` and `debt_section(item, placed)` ([D4](design.md#d4)).
  It reads `<run dir>/debt.md` through `debt_match.py`'s `cards` and `matched`, loaded by `importlib`, and keeps each card on a cited path or listed by the item's `debt:`; add `test_the_debt_cards_on_cited_files_and_listed_ids` to `tests/test_cut_context.py`. Verify: `uv run pytest -q tests/test_cut_context.py -k debt_cards_on_cited` exits 0.
- [x] 1.10 In `skills/mf-cut-change/scripts/cut_context.py` add `SKELETONS` and `skeletons_section()`, the A1 headings of each artifact in order and the OpenSpec form of a requirement and a scenario ([D4](design.md#d4)); add `test_each_skeleton_holds_its_headings_in_order` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k skeleton_holds` exits 0.
- [x] 1.11 In `skills/mf-cut-change/scripts/cut_context.py` add `pack(brief, change)` and `main`, which write `context.md` and `cut-notes.md` under `<run dir>/changes/<change-id>/` and print the one line of [D4](design.md#d4), exit 0, 1 or 2 as it says; add `test_the_pack_and_the_notes_are_written_and_exit_by_the_facts` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k pack_and_the_notes` exits 0.

## 2 — cut_context.py --scaffold, and row V2 on a negated -k

- [x] 2.1 **HALT CHECK** the scaffold's seams exist in `cut_context.py` ([D5](design.md#d5)).
  Verify: `git grep -n -e '^def item_parts(' -e '^def brief_sections(' -e '^def main(' -- skills/mf-cut-change/scripts/cut_context.py` prints a line for each.
- [x] 2.2 In `skills/mf-cut-change/scripts/cut_context.py` add `title_of(slug)` and `proposal_text(sections, slug)`, the proposal of [D5](design.md#d5); add `test_the_proposal_scaffold_holds_the_frontmatter_and_what_is_out` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k proposal_scaffold` exits 0.
- [x] 2.3 In `skills/mf-cut-change/scripts/cut_context.py` add `design_text(sections, slug)`, the decisions table and `## Dependencies` of [D5](design.md#d5); add `test_the_design_scaffold_numbers_the_decisions_and_lists_the_packages` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k design_scaffold` exits 0.
- [x] 2.4 In `skills/mf-cut-change/scripts/cut_context.py` add `tasks_text(sections)`, the progress lines and phase headings of [D5](design.md#d5), a phase with no rating stopping with exit 1; add `test_the_tasks_scaffold_lists_each_phase` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k tasks_scaffold` exits 0.
- [x] 2.5 In `skills/mf-cut-change/scripts/cut_context.py` give `main` the flag `--scaffold`, which writes the scaffold files and writes none when one exists ([D5](design.md#d5)); add `test_the_scaffold_refuses_a_file_that_exists` to `tests/test_cut_context.py`.
  Verify: `uv run pytest -q tests/test_cut_context.py -k scaffold_refuses` exits 0.
- [x] 2.6 In `skills/mf-cut-change/scripts/cut_check.py` add `selects(expression, name)`, the `-k` reading and positive match of [D7](design.md#d7); add `test_a_k_expression_selects_by_pytests_rules` to `tests/test_cut_check.py`.
  Verify: `uv run pytest -q tests/test_cut_check.py -k k_expression_selects` exits 0.
- [x] 2.7 In `skills/mf-cut-change/scripts/cut_check.py` make `_selected` return the expressions and `row_v2` halt on `selects`, as [D7](design.md#d7) says; in `tests/test_cut_check.py` assert the expressions in `test_a_search_names_its_literal_needle` and add `test_v2_halts_only_on_a_selected_test`.
  Verify: `uv run pytest -q tests/test_cut_check.py -k v2_halts_only` exits 0.

## 3 — The skill, the cache, the decisions and the skill's tests

- [x] 3.1 **HALT CHECK** `conduct.py` holds the cut's cache constant ([D3](design.md#d3)).
  Verify: `git grep -n 'CACHE_HOUR' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py` delete `CACHE_HOUR` and the `ENABLE_PROMPT_CACHING_1H=1` line, so `argv` sets `FORCE_PROMPT_CACHING_5M=1` for every station; in `tests/test_conduct.py` expect it for `cut` in `test_every_station_starts_lean` ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_conduct.py -k every_station_starts_lean` exits 0.
- [x] 3.3 In the reading step and Step 2 of `skills/mf-cut-change/SKILL.md` have the cut run `uv run --script scripts/cut_context.py <brief> <change-id>` in place of `facts.py place`, read `context.md` once, and read an unplaced fact's code from it; the reading step keeps naming `bundle.py --decisions <brief>` ([D9](design.md#d9)).
  Verify: `git grep -n 'cut_context.py' -- skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.4 In Step 6 of `skills/mf-cut-change/SKILL.md` have the cut run `cut_context.py` with `--scaffold` first, write the rest into the files, and take the skeletons from the pack in place of `openspec instructions` and archived changes read as examples ([D9](design.md#d9)).
  Verify: `git grep -n -e '--scaffold' -- skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.5 In Step 8.5 of `skills/mf-cut-change/SKILL.md` say each review runs in the foreground: the cut starts the worker, waits for its result and starts no background task for it ([D2](design.md#d2)).
  Verify: `git grep -n 'foreground' -- skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.6 In `tests/test_skills.py` add `("mf-cut-change", "scripts/cut_context.py")` to `_METRICS_SCRIPTS` after the `facts.py` row, and its line to `_CUT_UNNAMED` in the same place ([D9](design.md#d9)).
  Verify: `git grep -n 'scripts/cut_context.py' -- tests/test_skills.py` prints a line.
- [x] 3.7 In `docs/decisions.md` D77 names `the scaffold of its artifacts` and the context the cut reads among the scripts, and its `Rejected` line adds the cut reading archived changes as examples ([D10](design.md#d10)).
  Verify: `git grep -n 'the scaffold of its artifacts' -- docs/decisions.md` prints a line.
- [x] 3.8 In `docs/decisions.md` D80 replaces its last bold sentence `The cut keeps the 1-hour cache.` with `Each review runs in the foreground, the cut waiting on it, and the cut runs on the 5-minute cache with its reviews.`, and its `Rejected` line is changed as [D10](design.md#d10) says.
  Verify: `git grep -n 'Each review runs in the foreground' -- docs/decisions.md` prints a line.
- [x] 3.9 In `docs/decisions.md` D70 replaces `The cut asks for the 1-hour cache, every other station the 5-minute one.` with `Every station asks for the 5-minute cache.`, and its `Why` and `Accepts` lines change as [D10](design.md#d10) says.
  Verify: `git grep -n 'Every station asks for the 5-minute cache' -- docs/decisions.md` prints a line.
