# Amend round — tasks

Build the settled [design](design.md), one phase at a time, on 0088's, 0089's and 0090's merged code.

## Progress

- [x] 1 — The amend round
- [ ] 2 — The conductor and the metrics
- [ ] 3 — The record

## 1 — The amend round

- [x] 1.1 **HALT CHECK** 0089's `Supervisor:` words stand in the passages of `skills/mf-converge/SKILL.md` that
  [D1](design.md#d1) replaces whole, as the design's F8 reads them.
  Verify: `grep -c 'Supervisor:' skills/mf-converge/SKILL.md` prints `3`.
- [x] 1.2 Replace the paragraphs from "The top line is any other `halt`" through "is no person's answer." in *Resuming a run* of
  `skills/mf-converge/SKILL.md` with [D1](design.md#d1)'s **An answered halt** paragraph.
  Verify: `grep -n 'An answered halt:' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.3 Replace the last sentence of *A halt before round 1* in `skills/mf-converge/SKILL.md` with [D1](design.md#d1)'s, the
  words `a new run of its mark runs the` on one line.
  Verify: `grep -n 'a new run of its mark runs the' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.4 Edit the status log's run, the catch-up's check, its diagram and the run's mark in `skills/mf-converge/SKILL.md`, per
  [D1](design.md#d1).
  Verify: `grep -n 'merges only, replay?' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.5 In the catch-up of `skills/mf-converge/SKILL.md`, replace item 2's merges-and-amends sentence with
  [D4](design.md#d4)'s, item 3 with [D3](design.md#d3)'s and item 4 with [D5](design.md#d5)'s, the words
  `verify failed — <sub-task ids>` on one line.
  Verify: `grep -n 'verify failed — <sub-task ids>' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.6 Drop By rule's amend clauses, per [D5](design.md#d5), and edit Step 7's own-count sentence, per [D1](design.md#d1), in
  `skills/mf-converge/SKILL.md`, the words `or an answered halt's, has` on one line.
  Verify: `grep -n "or an answered halt's, has" skills/mf-converge/SKILL.md` prints a line.
- [x] 1.7 Make [D6](design.md#d6)'s edits to `skills/mf-converge/references/worker.md`, the words
  `An **amend round** judges its whole range` on one line.
  Verify: `grep -n -F 'An **amend round** judges its whole range' skills/mf-converge/references/worker.md` prints a line.
- [x] 1.8 **HALT CHECK** `skills/mf-converge/SKILL.md` and `skills/mf-converge/references/worker.md` hold fewer than the 7,408
  words they held at `bb4cf51`, as [D1](design.md#d1)'s **Words** plans.
  Verify: `wc -w skills/mf-converge/SKILL.md skills/mf-converge/references/worker.md` prints a `total` below `7408`.

## 2 — The conductor and the metrics

- [ ] 2.1 **HALT CHECK** `_answered` and `Run._amended_alone` in `skills/mf-ship/scripts/conduct.py` still read `_amendable`, as
  the design's F4 reads them.
  Verify: `grep -c '_amendable(runs, change, halt)' skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 2.2 Add `_amends` above `_amended_only` in `skills/mf-ship/scripts/conduct.py`, and rewrite `_amended_only` through it, per
  [D2](design.md#d2).
  Verify: `grep -n '^def _amends(' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.3 In `_answered` of `skills/mf-ship/scripts/conduct.py`, replace the `_amendable` and `_amended_only` test with
  [D2](design.md#d2)'s, and its docstring with D2's; edit `Run.advance`'s answered-halt comment, per D2.
  Verify: `grep -n 'if any(_amends(tree, change, halted)):' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.4 Have `_amendable` in `skills/mf-ship/scripts/conduct.py` read the `· amend` mark beside `· catch-up`, with its docstring,
  per [D7](design.md#d7).
  Verify: `grep -n '_run_marked(runs, change, "amend")' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.5 Make the edits the design's fake table names to `_findings`, `_by_rule`, `_person_amends` and the converge branch of
  `tests/fake_worker.py`.
  Verify: `grep -n 'verify-fails' tests/fake_worker.py` prints a line.
- [ ] 2.6 In `test_a_rescue_amends_at_amend_needed` of `tests/test_conduct.py`, assert the heading `## Run 2 — d · amend`, as the
  design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue_amends_at_amend_needed` reports `1 passed`.
- [ ] 2.7 Rename `test_a_fix_after_a_cap_halt_converges_afresh` in `tests/test_conduct.py` to
  `test_a_fix_after_a_cap_halt_gets_one_round`, and edit it, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k fix_after_a_cap_halt_gets_one_round` reports `1 passed`.
- [ ] 2.8 Edit the comments in `test_a_verify_halt_is_diagnosed_without_a_worker` and
  `test_a_halt_before_round_1_runs_again_at_the_same_head` of `tests/test_conduct.py`, as the design's `## Tests` names them.
  Verify: `git grep -n converges_afresh -- tests` prints nothing.
- [ ] 2.9 Rename `test_a_drift_amend_goes_on_by_rule` in `tests/test_conduct.py` to `test_a_drift_amend_answers_its_halt`.
  Verify: `uv run pytest -q tests/test_conduct.py -k drift_amend_answers_its_halt` reports `1 passed`.
- [ ] 2.10 Add `test_an_amend_past_the_judged_head_gets_one_round` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k amend_past_the_judged_head_gets_one_round` reports `1 passed`.
- [ ] 2.11 Make [D7](design.md#d7)'s edits to `Version.rounds`, `Version.amends` and `METRICS` in `scripts/metrics/run.py`.
  Verify: `grep -n '"amend-rounds": Version.amends' scripts/metrics/run.py` prints a line.
- [ ] 2.12 Add [D7](design.md#d7)'s `amend-rounds` entry after `grants` in `metrics/catalogue.toml`.
  Verify: `grep -n 'id = "amend-rounds"' metrics/catalogue.toml` prints a line.
- [ ] 2.13 Extend `_STATUS` and `expected` of `test_run_metrics_read_the_run_logs` in `tests/test_metric_scripts.py`, as the
  design's `## Tests` names them.
  Verify: `grep -n '"amend-rounds": 1,' tests/test_metric_scripts.py` prints a line.

## 3 — The record

- [ ] 3.1 Add D63 at the end of *The check loop and the release* in `docs/decisions.md`, after D50, as [D8](design.md#d8) quotes
  it, and its id after D50 in the map's list.
  Verify: `grep -n '^### D63 · An answered amend gets one round over its range$' docs/decisions.md` prints a line.
- [ ] 3.2 Edit D15's drift line in `docs/decisions.md`, per [D8](design.md#d8), the words `answers it, in one amend round` on one
  line.
  Verify: `grep -n 'answers it, in one amend round' docs/decisions.md` prints a line.
- [ ] 3.3 Edit D47's answered sentence in `docs/decisions.md`, per [D8](design.md#d8), the words
  `is answered, and gets one amend round` on one line.
  Verify: `grep -n 'is answered, and gets one amend round' docs/decisions.md` prints a line.
- [ ] 3.4 Edit D53's Why and D60's Accepts in `docs/decisions.md`, per [D8](design.md#d8), the words `every claim it changes` on
  one line in each.
  Verify: `grep -c 'every claim it changes' docs/decisions.md` prints `2`.
- [ ] 3.5 Edit *Nothing reads as clean by being absent* and the *A merge* bullet of `docs/principles.md`, per [D8](design.md#d8).
  Verify: `grep -n 'A merge or an amend:' docs/principles.md` prints a line.
- [ ] 3.6 Edit the rescue sentence of *Out of scope* in `THREAT_MODEL.md`, per [D8](design.md#d8), the words
  `every claim it changes` on one line.
  Verify: `grep -c 'every claim it changes' THREAT_MODEL.md` prints `1`.
- [ ] 3.7 Edit 0089's supervisor paragraph of *Out of scope* in `THREAT_MODEL.md`, per [D8](design.md#d8), the words
  `in an amend round, as every amend` on one line.
  Verify: `grep -n 'in an amend round, as every amend' THREAT_MODEL.md` prints a line.
- [ ] 3.8 Edit the role line of `skills/mf-rescue/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n 'converge judges your amend in one round' skills/mf-rescue/SKILL.md` prints a line.
- [ ] 3.9 Edit 0089's role line of `skills/mf-supervise/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n 'converge judges your amend in one round' skills/mf-supervise/SKILL.md` prints a line.
