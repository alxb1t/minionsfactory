# Converge switches — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code, save the guards its
`## Tests` names.

## Progress

- [x] 1 — The grammar · hard
- [x] 2 — Conduct reads the switches · hard
- [x] 3 — Converge with one role, the stub and the release · hard
- [x] 4 — The repo default and the surfaces warning · moderate
- [ ] 5 — The record · moderate

## 1 — The grammar

- [x] 1.1 **HALT CHECK** Confirm `models()` still takes a part's name only from a three-word part in
  `skills/mf-plan/scripts/brief_check.py`, as [D1](design.md#d1) needs; missing, the plan is wrong.
  Verify: `grep -n "len(part) == 3" skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.2 Add `test_a_models_line_naming_a_skip` to `tests/test_brief_check.py`, per the design's `## Tests` row.
  Verify: `grep -n "def test_a_models_line_naming_a_skip" tests/test_brief_check.py` prints a line.
- [x] 1.3 In `skills/mf-plan/scripts/brief_check.py`, make [D1](design.md#d1)'s `models()` and `MODELS` edits, the new why
  line citing `0105-converge-switches design D1`.
  Verify: `uv run pytest -q tests/test_brief_check.py -k models_line_naming_a_skip` reports `1 passed`.
- [x] 1.4 In `skills/mf-plan/SKILL.md`, make [D1](design.md#d1)'s edit to the `models:` grammar line.
  Verify: `grep -n "converge skip" skills/mf-plan/SKILL.md` prints a line.
- [x] 1.5 In `skills/mf-cut-change/SKILL.md`, replace the dead `skip, read by hand` text of the Converge bullet and the
  suggestion block, and drop the comment of the template's `[converge]` line, per [D1](design.md#d1).
  Verify: `grep -n "skip, read by hand" skills/mf-cut-change/SKILL.md` prints nothing.
- [x] 1.6 In `skills/mf-cut-change/SKILL.md`, add [D1](design.md#d1)'s new comment line to the template, after its `# shadow = true`
  line, and the sentence before the template that writes a brief's `skip` parts into `models.toml`.
  Verify: `grep -n "no worker tables" skills/mf-cut-change/SKILL.md` prints a line.

## 2 — Conduct reads the switches

- [x] 2.1 **HALT CHECK** Confirm `ROLES` still names both checkers in `skills/mf-ship/scripts/conduct.py`, as
  [D2](design.md#d2) needs; missing, the plan is wrong.
  Verify: `grep -n "^ROLES = " skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.2 Add the steps of the design's `## Tests` rows for `test_a_worker_clause_names_its_model_and_effort` and
  `test_a_checker_on_another_host_is_planned_and_probed` to `tests/test_conduct.py`.
  Verify: `grep -n "adversarial=skip" tests/test_conduct.py` prints a line.
- [x] 2.3 Add the step of the design's `## Tests` row for `test_a_ready_version_ships_past_a_slow_one` to `tests/test_conduct.py`.
  Verify: `grep -n "converge skipped — plan" tests/test_conduct.py` prints a line.
- [x] 2.4 In `skills/mf-ship/scripts/conduct.py`, add `_skips`, edit `_unjudged`, `stage_of`, `Run`, `_worker_clause` and the
  converge spawn, per [D2](design.md#d2), each new why line citing `0105-converge-switches design D2`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "worker_clause_names or another_host_is_planned or ships_past_a_slow_one"` reports `3 passed`.
- [x] 2.5 In `skills/mf-ship/SKILL.md`, per [D2](design.md#d2), add to the flow diagram's converge steps and to the paragraph that opens `Converge runs MF's
  method` the words that a version whose models file says `[converge] skip = true` skips converge and its catch-up round.
  Verify: `grep -n "skips converge" skills/mf-ship/SKILL.md` prints a line.

## 3 — Converge with one role, the stub and the release

- [x] 3.1 Add `tests/test_skip_stub.py` with `test_a_stub_is_written` and `test_a_stub_it_cannot_write_exits_2`, per the design's
  `## Tests` rows.
  Verify: `grep -n "def test_a_stub_it_cannot_write_exits_2" tests/test_skip_stub.py` prints a line.
- [x] 3.2 Write `skills/mf-converge/scripts/skip_stub.py`, per [D3](design.md#d3), its docstring citing
  `0105-converge-switches design D3`.
  Verify: `uv run pytest -q tests/test_skip_stub.py` reports `2 passed`.
- [x] 3.3 Add `test_a_stub_bars_no_rescue` and `test_a_version_with_adversarial_skipped_ships_on_a_stub` to `tests/test_conduct.py`,
  per the design's `## Tests` rows; the second goes red here, as the fake still writes a findings file for adversarial.
  Verify: `grep -n "def test_a_version_with_adversarial_skipped_ships_on_a_stub" tests/test_conduct.py` prints a line.
- [x] 3.4 In `tests/fake_worker.py`'s converge branch, run `skip_stub.py` for each role its prompt holds `=skip` for, in place of that
  role's findings file, per the design's `## Tests` row.
  Verify: `uv run pytest -q tests/test_conduct.py -k "stub_bars_no_rescue or adversarial_skipped_ships"` reports `2 passed`.
- [x] 3.5 **CORPUS** `review-metrics` In `skills/mf-review-metrics/scripts/review_metrics.py`, anchor `WORKER` and read `mode: skipped` as a gap in
  `_workers`, per [D6](design.md#d6) and [D3](design.md#d3); add `test_review_metrics_books_a_worker_by_its_description` to
  `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k books_a_worker_by_its_description` reports `1 passed`.
- [x] 3.6 In `skills/mf-converge/SKILL.md`, add [D3](design.md#d3)'s `## A skipped checker` section after *Shadow round 1*.
  Verify: `grep -n "skip_stub.py" skills/mf-converge/SKILL.md` prints a line.
- [x] 3.7 In `skills/mf-converge/SKILL.md`, make [D3](design.md#d3)'s edits to Steps 3, 5, 6, 7 and 8, and [D6](design.md#d6)'s
  descriptions in Steps 3, 6 and 7.
  Verify: `grep -n "fix round <N>" skills/mf-converge/SKILL.md` prints a line.
- [x] 3.8 In `skills/mf-converge/SKILL.md`, make [D3](design.md#d3)'s edits to *By rule*, *Never* and Step 10, and the halt on a
  `shadow=yes` beside a skip.
  Verify: `grep -n "a skipped role" skills/mf-converge/SKILL.md` prints a line.
- [x] 3.9 In `skills/mf-converge/references/worker.md`, make [D3](design.md#d3)'s `mode` and `workers` edits.
  Verify: `grep -n "by-rule | skipped" skills/mf-converge/references/worker.md` prints a line.
- [x] 3.10 In `skills/mf-release/SKILL.md`, make [D4](design.md#d4)'s edits to precondition 4, Step 4.4's line and the report.
  Verify: `grep -n "skipped — by plan" skills/mf-release/SKILL.md` prints a line.

## 4 — The repo default and the surfaces warning

- [x] 4.1 In `skills/mf-plan/SKILL.md`, add [D5](design.md#d5)'s `**Converge:**` pre-fill to the paragraph after the `models:` grammar
  line.
  Verify: `grep -n -F "**Converge:**" skills/mf-plan/SKILL.md` prints a line.
- [x] 4.2 In `skills/mf-cut-change/SKILL.md`, add [D5](design.md#d5)'s pre-fill to *Suggesting models*, and its surfaces warning to
  Step 9 and the unattended notes.
  Verify: `grep -n "surfaces warning" skills/mf-cut-change/SKILL.md` prints a line.

## 5 — The record

- [ ] 5.1 **HALT CHECK** Confirm no decision D75 stands in `docs/decisions.md`, as [D7](design.md#d7) needs; one standing, the
  plan is wrong.
  Verify: `grep -n "^### D75" docs/decisions.md` prints nothing.
- [ ] 5.2 In `docs/decisions.md`, after D74's entry, add D75 with [D7](design.md#d7)'s heading and text, and add `D75` to the
  check-loop group's index on line 13.
  Verify: `grep -n "^### D75 · " docs/decisions.md` prints a line.
- [ ] 5.3 In `docs/decisions.md`, add [D7](design.md#d7)'s sentence to D14's first paragraph.
  Verify: `grep -n "A plan may also skip converge" docs/decisions.md` prints a line.
- [ ] 5.4 In `THREAT_MODEL.md`'s `## Out of scope`, add [D7](design.md#d7)'s planted-skip entry after the worker-steering class.
  Verify: `grep -n "planted skip" THREAT_MODEL.md` prints a line.
