# Plan review diet — tasks

The phases: the rows of `cut_check.py`, the reader kinds of `facts.py`, then the skill, the decision and the debt card. Each phase ends green.

## Progress

- [x] 1 — cut_check.py: Verify sequencing and record consistency · hard
- [x] 2 — facts.py readers: signatures, files and strings · hard
- [ ] 3 — Step 8.5, the decision and the reading step · hard

## 1 — cut_check.py: Verify sequencing and record consistency

- [x] 1.1 **HALT CHECK** `cut_check.py` holds the seams the rows extend ([D2](design.md#d2)).
  Verify: `git grep -n -e '^ROWS = ' -e '^def blocks(' -e '^def row_p9(' -- skills/mf-cut-change/scripts/cut_check.py` prints a line for each.
- [x] 1.2 In `tests/test_cut_check.py` add the line `It keeps the line x.` to the decision section of `_DESIGN`, and keep a decision link in the replaced text of `test_a_fenced_block_does_not_count_toward_the_limit` and in the defect `_id_outside_a_link` ([D2](design.md#d2)).
  Verify: `git grep -n 'It keeps the line x' -- tests/test_cut_check.py` prints a line.
- [x] 1.3 In `tests/test_cut_check.py` make `_PROPOSAL`'s `## Impact` read ``Edits the file `a.py`.`` ([D3](design.md#d3)).
  Verify: `git grep -n 'Edits the file' -- tests/test_cut_check.py` prints a line.
- [x] 1.4 In `cut_check.py` add `search_parts(command)`, which returns the literal needles and the file operands of a `grep` or `git grep`, else none, as [D2](design.md#d2) says; add `test_a_search_names_its_literal_needle` to `tests/test_cut_check.py`.
  Verify: `uv run pytest -q tests/test_cut_check.py -k literal_needle` exits 0.
- [x] 1.5 In `cut_check.py` add `row_v1`, with `V1` in `ROWS` and in `check`'s `rows`, skipping a HALT CHECK; in `tests/test_cut_check.py` add a defect for `V1` to `test_each_mechanical_row_fails_by_name` that trips `V1` alone ([D2](design.md#d2)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k V1` exits 0.
- [x] 1.6 In `cut_check.py` add `row_v2`, with `V2` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect to `test_each_mechanical_row_fails_by_name` ([D2](design.md#d2)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k V2` exits 0.
- [x] 1.7 In `cut_check.py` add `row_v3`, with `V3` in `ROWS`, computed in `check` before `folded`, a hit returning that failure alone; in `tests/test_cut_check.py` add its defect ([D2](design.md#d2)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k V3` exits 0.
- [x] 1.8 In `cut_check.py` add `row_v4`, with `V4` in `ROWS` and in `rows`, skipping a HALT CHECK; in `tests/test_cut_check.py` add its defect ([D2](design.md#d2)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k V4` exits 0.
- [x] 1.9 In `cut_check.py` add `path_spans(text)` and `row_k1`, with `K1` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K1` exits 0.
- [x] 1.10 In `cut_check.py` add `row_k2`, with `K2` in `ROWS` and in `rows`, reading `design.md`'s `## Tests` through `section`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K2` exits 0.
- [x] 1.11 In `cut_check.py` add `row_k3`, with `K3` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K3` exits 0.
- [x] 1.12 In `cut_check.py` add `row_k4`, with `K4` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K4` exits 0.
- [x] 1.13 In `cut_check.py` add `row_k5`, which asks `git grep` at `HEAD` for each `Step` heading and constant, with `K5` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K5` exits 0.
- [x] 1.14 In `cut_check.py` add `row_k6`, with `K6` in `ROWS` and in `rows`; in `tests/test_cut_check.py` add its defect ([D3](design.md#d3)).
  Verify: `uv run pytest -q tests/test_cut_check.py -k K6` exits 0.

## 2 — facts.py readers: signatures, files and strings

- [x] 2.1 **HALT CHECK** `facts.py` holds the seams the kinds extend ([D4](design.md#d4)).
  Verify: `git grep -n -e '^def reader_lines(' -e '^def run_readers(' -- skills/mf-cut-change/scripts/facts.py` prints a line for each.
- [x] 2.2 In `facts.py` give `readers` the repeatable flags `--signature`, `--file` and `--string`, names optional, exit 2 with none of them or with a `--signature` value that is no identifier ([D4](design.md#d4)); add `test_readers_refuse_a_bare_call_and_a_bad_signature` to `tests/test_facts.py`.
  Verify: `uv run pytest -q tests/test_facts.py -k refuse_a_bare_call` exits 0.
- [x] 2.3 In `facts.py` add `signature_lines(name)`, the `stand-in` and `monkeypatch` kinds of [D4](design.md#d4); add `test_a_changed_signature_lists_its_stand_ins_and_monkeypatches` to `tests/test_facts.py`.
  Verify: `uv run pytest -q tests/test_facts.py -k changed_signature` exits 0.
- [x] 2.4 In `facts.py` add `file_lines(path)`, the `runpy reader` and `import reader` kinds of [D4](design.md#d4); add `test_a_changed_file_lists_its_runpy_and_import_readers` to `tests/test_facts.py`.
  Verify: `uv run pytest -q tests/test_facts.py -k changed_file` exits 0.
- [x] 2.5 In `facts.py` add `string_lines(text)`, the `string reader` kind of [D4](design.md#d4), searched with `-F` and no word bound; add `test_a_changed_string_lists_each_line_holding_it` to `tests/test_facts.py`.
  Verify: `uv run pytest -q tests/test_facts.py -k changed_string` exits 0.

## 3 — Step 8.5, the decision and the reading step

- [ ] 3.1 **HALT CHECK** Step 8.5 holds the Opus line and the 40-turn budget at `HEAD`.
  Verify: `git grep -n -F -e 'Opus 5.5 · high' -e '40 turns' -- skills/mf-cut-change/SKILL.md` prints a line for each.
- [ ] 3.2 In Step 8.5 of `skills/mf-cut-change/SKILL.md` the reviewer's line reads `subagent, on Sonnet 5.5 · high where the host offers it`, on Claude Code `model: sonnet` and `effort: high` ([D1](design.md#d1)).
  Verify: `git grep -n 'subagent, on Sonnet 5.5 · high' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.3 In Step 8.5 the budget reads `25 turns`, and the reviewer stops at the 25th ([D6](design.md#d6)).
  Verify: `git grep -n '25 turns' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.4 After the budget paragraph add the overrun sentence of [D6](design.md#d6): the cut counts the tool calls from the transcript and appends `plan review <n> over budget: <calls> tool calls` to `cut-notes.md`.
  Verify: `git grep -n 'over budget' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.5 In Step 8.5 the packet's met rows and `each facts.py readers line of the notes` are taken as settled, the reviewer skipping them ([D5](design.md#d5)), on one line.
  Verify: `git grep -n 'readers line of the notes' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.6 In Step 3 of `skills/mf-cut-change/SKILL.md` name the flags `--signature <name>`, `--file <path>` and `--string <text>` beside the names, each for the change it finds ([D4](design.md#d4)).
  Verify: `git grep -n -e '--signature' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.7 In Step 8 of `skills/mf-cut-change/SKILL.md` list `V1`–`V4` and `K1`–`K6` among the rows the script decides, and say in the `Verify:` bullet that the cut reads what they leave: a pattern that is no literal ([D2](design.md#d2), [D3](design.md#d3)).
  Verify: `git grep -n 'K1' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.8 In the reading step of `skills/mf-cut-change/SKILL.md` write `from the conversation, read the ### D headings of docs/decisions.md as the index, and in full each decision` in place of the index it prints, the phrase on one line ([D9](design.md#d9)).
  Verify: `git grep -n 'as the index, and in full each' -- skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.9 In `skills/mf-plan/SKILL.md` the cut's line reads `plan reviews run on Sonnet 5.5 · high whatever the cut runs on`, in place of Opus 5.5 ([D1](design.md#d1)).
  Verify: `git grep -n 'plan reviews run on Sonnet 5.5' -- skills/mf-plan/SKILL.md` prints a line.
- [ ] 3.10 In `docs/decisions.md` add the block of [D1](design.md#d1) as `### D80 · The plan reviews run on Sonnet` after D77, and `D80` to the `Planning` list of the index tree.
  Verify: `git grep -n 'The plan reviews run on Sonnet' -- docs/decisions.md` prints a line.
- [ ] 3.11 In `docs/decisions.md` D65 reads `a fresh worker on Sonnet 5.5 · high` in place of Opus 5.5, per [D1](design.md#d1).
  Verify: `git grep -n 'a fresh worker on Sonnet 5.5' -- docs/decisions.md` prints a line.
- [ ] 3.12 In `docs/decisions.md` D71 reads `budget of 25 turns`, and its `Rejected` line drops `plan reviews on Sonnet — both of 0097's caught real defects` ([D6](design.md#d6)).
  Verify: `git grep -n 'budget of 25 turns' -- docs/decisions.md` prints a line.
- [ ] 3.13 In `docs/decisions.md` D74 reads `Plan reviews run on Sonnet 5.5 · high`, in place of Opus 5.5 ([D1](design.md#d1)).
  Verify: `git grep -n 'Plan reviews run on Sonnet 5.5' -- docs/decisions.md` prints a line.
