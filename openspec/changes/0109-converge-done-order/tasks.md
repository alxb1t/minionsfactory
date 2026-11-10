# Converge done order — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `S` is
`skills/mf-converge/scripts/stamp.py`, `C` is `skills/mf-ship/scripts/conduct.py`, `W` is
`skills/mf-converge/references/worker.md`. Inside a phase a sub-task's `Verify:` is its own; only the phase's end is green.

## Progress

- [x] 1 — `stamp.py` refuses a misordered call · moderate
- [x] 2 — The converge check stamps a buried `done` again · hard
- [ ] 3 — D39's third way, in the decision and its copies · moderate

## 1 — `stamp.py` refuses a misordered call

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def stamp(' -e '^def main(' -- skills/mf-converge/scripts/stamp.py` prints a line for each.
- [x] 1.2 Extend `test_a_stamp_writes_the_clock_time_under_the_latest_run` and `test_a_log_out_of_shape_is_not_stamped` in
  `tests/test_stamp.py` as [the Tests table](design.md#tests) says, a step after a log reset: `debt` then `done` puts `done` on top; each refusal case of [D1](design.md#d1) exits 2, says its message, leaves the log.
  Verify: `git grep -n -e 'goes last in a call' -e 'the run ends on' -- tests/test_stamp.py` prints a line for each.
- [x] 1.3 Add `_ends` to `S`: it returns `done`, `halt` or None for an event line, by the test `_is_event` of `C` makes.
  Verify: `git grep -n '^def _ends(' -- skills/mf-converge/scripts/stamp.py` prints a line.
- [x] 1.4 In `stamp` of `S` refuse, per [D1](design.md#d1), a `done` or `halt` before another event (`<event> goes last in a call`)
  and an event under a run whose first non-blank line `_ends` names (`the run ends on <event>: open a ## Run for a new event`), save a `halt` naming `.minions/debt.lock` or `.minions/backlog.lock`. A `--run` heading is never refused.
  Verify: `uv run pytest -q tests/test_stamp.py` exits 0; `git grep -n -e 'goes last in a call' -e 'the run ends on' -- skills/mf-converge/scripts/stamp.py` prints a line for each.
- [x] 1.5 Say the refusals in `S`'s module docstring, and add `; 0109-converge-done-order design D1` before the final period of its existing `Why:` line.
  Verify: `git grep -n '0109-converge-done-order design D1' -- skills/mf-converge/scripts/stamp.py` prints a line.

## 2 — The converge check stamps a buried `done` again

- [x] 2.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def _check_converge(' -e '^def _converge_done(' -e '^def _run_end(' -e '^INTEGRATE = ' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.2 Add the mode `keep-log` to the converge branch of `tests/fake_worker.py`: after the branch's `_findings` call, in its default case, write back the `held` log text.
  Verify: `git grep -n '"keep-log" in modes' -- tests/fake_worker.py` prints a line.
- [x] 2.3 Add `test_a_done_under_the_top_line_is_stamped_again` to `tests/test_conduct.py`, its cases as [the Tests table](design.md#tests)
  says; the helpers and the closing `run` of `test_a_fix_after_a_cap_halt_gets_one_round` are its model, the fake host in mode `keep-log`, the log written after `_findings`.
  Verify: `git grep -n 'def test_a_done_under_the_top_line_is_stamped_again' -- tests/test_conduct.py` prints a line.
- [x] 2.4 In `C` add `STAMP_SCRIPT` beside `INTEGRATE`, and `_buried_done`: the newest run's `done` line under a top line that is neither `halt` nor `done`, else None.
  Verify: `git grep -n -e '^STAMP_SCRIPT = ' -e '^def _buried_done(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.5 In `C` add `_restamp`: `S`'s `main`, loaded by `runpy` from `STAMP_SCRIPT`, given `<the buried line's round> · done — re-stamped by the run`.
  Then make `_check_converge` follow [D2](design.md#d2): both findings files and the tree are read before the stamp, and a stamp that exits 2 fails `the status log has no done`.
  Verify: `git grep -n '^def _restamp(' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.6 Per [D3](design.md#d3): give `check` and `_check_converge` the keyword `notes: list[str] | None = None`, which the re-stamp appends `re-stamped done` to;
  in `Run.advance` pass a list named `restamped` to both `check` calls and show it after the pass in `judge`'s `shown`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "done_under_the_top_line"` exits 0; `git grep -n 'restamped' -- skills/mf-ship/scripts/conduct.py` prints a line.

## 3 — D39's third way, in the decision and its copies

- [ ] 3.1 **HALT CHECK** The rule stands where the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^### D39 · ' -e 'Never weaken the gate to pass' -- docs/decisions.md docs/principles.md` prints a line for each.
- [ ] 3.2 Edit D39 in `docs/decisions.md` and *Never weaken the gate to pass* in `docs/principles.md` with the wording of
  [D4](design.md#d4), the phrase `a requirement the change's delta removes` whole on one line in each.
  Verify: `git grep -n -e "requirement the change.s delta removes" -- docs/decisions.md docs/principles.md` prints a line for each.
- [ ] 3.3 Edit the `I16` row and the `T5` row in `skills/mf-build/SKILL.md` and in `skills/mf-cut-change/SKILL.md` with that wording, the same text in both files;
  `I16` adds `(retired by removing <requirement title>)`.
  Verify: `git grep -c -e "requirement the change.s delta removes" -- skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints `skills/mf-build/SKILL.md:2` and `skills/mf-cut-change/SKILL.md:2`.
- [ ] 3.4 Edit `W`'s coverage-trace row and its `T5`: a removed assertion or scenario id is `blocking` unless a requirement the
  change's delta removes, with the code under test, retires it as the table names.
  Verify: `uv run pytest -q tests/test_skills.py` exits 0; `git grep -c -e "requirement the change.s delta removes" -- skills/mf-converge/references/worker.md` prints `skills/mf-converge/references/worker.md:2`.
- [ ] 3.5 Edit the bullet of `skills/mf-bootstrap/templates/AGENTS.md.tmpl` that names the `## Tests` table with that wording, the phrase `a requirement the change's delta removes` whole on one line.
  Verify: `git grep -c -e "requirement the change.s delta removes" -- skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `skills/mf-bootstrap/templates/AGENTS.md.tmpl:1`.
