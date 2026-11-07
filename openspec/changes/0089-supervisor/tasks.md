# Supervisor — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — The station
- [ ] 2 — The check's refusals
- [ ] 3 — The skills
- [ ] 4 — The record

## 1 — The station

- [ ] 1.1 **HALT CHECK** `advance` in `skills/mf-ship/scripts/conduct.py` still calls the rescue at its entry and check sites
  alone, as [D1](design.md#d1) reads them.
  Verify: `grep -c 'self.rescue(version' skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 1.2 Add `"supervise"` to `EVENTS`' third group and to `PLANNED`, `SUPERVISES = 2` and `SUPERVISOR` beside `RESCUES`, and
  `PROMPTS["supervise"]` in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1), [D2](design.md#d2) and [D5](design.md#d5).
  Verify: `grep -n 'SUPERVISES = 2' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 1.3 Give `_models` the supervisor's Claude default and its docstring line, per [D2](design.md#d2), and add
  `test_the_supervisor_runs_on_its_own_table` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_runs_on_its_own_table` reports `1 passed`.
- [ ] 1.4 Add `_supervised` beside `_amend` in `skills/mf-ship/scripts/conduct.py`, its refusals as [D3](design.md#d3)'s table
  words them.
  Verify: `grep -n '^def _supervised(' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 1.5 Add `self.supervisions` and `self.supervisor_decided` to `Run.__init__`, and `Run.supervised` and `Run.supervise` beside
  `Run.rescue`, per [D1](design.md#d1), [D4](design.md#d4) and [D5](design.md#d5), with no `_security_held` read and no `finally`:
  2.1 and 2.3 add them.
  Verify: `grep -n 'def supervise(self' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 1.6 Call `self.supervise` after the rescue at both sites of `Run.advance`, and append `Run.supervised`'s suffix to both
  halts, per [D1](design.md#d1) and [D5](design.md#d5).
  Verify: `grep -c 'self.supervise(' skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 1.7 Add `_supervise` to `tests/fake_worker.py` with its `supervise-delta` and `supervise-hollow` modes, dispatched on
  `station == "supervise"` beside `_rescue`, as the design's `## Tests` tables them.
  Verify: `grep -n 'def _supervise(' tests/fake_worker.py` prints a line.
- [ ] 1.8 Add `test_a_supervisor_answers_a_diagnosed_halt` to `tests/test_conduct.py`, its `done` line ending
  `released v0.1.0` and no `report` assertion, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_answers_a_diagnosed_halt` reports `1 passed`.
- [ ] 1.9 Add `test_a_spent_rescue_starts_the_supervisor_once` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k spent_rescue_starts_the_supervisor_once` reports `1 passed`.

## 2 — The check's refusals

- [ ] 2.1 Give `Run.hold` its `who` parameter and its two strings, and run it in `Run.supervise`'s `finally`, per
  [D6](design.md#d6).
  Verify: `grep -n 'self.hold(version, tree, before, "supervise")' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.2 Make `_amended_alone` read both trailers and say so in its docstring, per [D6](design.md#d6).
  Verify: `grep -n -F '%(trailers:key=Rescue)%(trailers:key=Supervisor)' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.3 Add `_security_held` beside `_security_blocks`, and read it in `Run.supervise` at `converge-halted`, per
  [D1](design.md#d1) and [D6](design.md#d6).
  Verify: `grep -n '^def _security_held(' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.4 Make `_rescuing` read `supervise` spawns, and reword `grant`'s refusal, per [D6](design.md#d6), with the string
  `test_a_grant_buys_one_round` in `tests/test_conduct.py` asserts, the words `its rescue or supervisor running` on one line in each.
  Verify: `grep -l 'its rescue or supervisor running' skills/mf-ship/scripts/conduct.py tests/test_conduct.py` prints both paths.
- [ ] 2.5 Add the `supervise-test`, `supervise-undecided` and `supervise-none` modes to `_supervise` in `tests/fake_worker.py`, as
  the design's `## Tests` tables them.
  Verify: `grep -n 'supervise-undecided' tests/fake_worker.py` prints a line.
- [ ] 2.6 Add `test_a_supervisor_amend_outside_the_change_halts` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_amend_outside_the_change_halts` reports `1 passed`.
- [ ] 2.7 Add `test_a_refused_supervisor_amend_is_not_the_persons` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k refused_supervisor_amend_is_not_the_persons` reports `1 passed`.
- [ ] 2.8 Add `test_a_grant_waits_for_the_supervisor` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k grant_waits_for_the_supervisor` reports `1 passed`.

## 3 — The skills

- [ ] 3.1 Write `skills/mf-supervise/SKILL.md` to [D7](design.md#d7)'s table, its commit message and [D8](design.md#d8)'s rule.
  Verify: `grep -n '^name: mf-supervise$' skills/mf-supervise/SKILL.md` prints a line.
- [ ] 3.2 Add [D8](design.md#d8)'s item 2 to Step 3a of `skills/mf-rescue/SKILL.md`, renumbering the items after it, the words
  `new unticked phase after the last` on one line.
  Verify: `grep -n 'new unticked phase after the last' skills/mf-rescue/SKILL.md` prints a line.
- [ ] 3.3 Edit the flow, the diagnosed and answered rows, and Step 4's close of `skills/mf-ship/SKILL.md`, per
  [D8](design.md#d8) and [D10](design.md#d10), the words `supervisor answered its halt` on one line.
  Verify: `grep -n 'supervisor answered its halt' skills/mf-ship/SKILL.md` prints a line.
- [ ] 3.4 Add `Supervisor:` to the three `Rescue:` readers of `skills/mf-converge/SKILL.md`, and the supervisor's amend to item
  2's merges and amends, per [D9](design.md#d9).
  Verify: `grep -c 'Supervisor:' skills/mf-converge/SKILL.md` prints `3`.

## 4 — The record

- [ ] 4.1 Add the `supervise` branch to `report`, and `Run.supervisors` to `Run.closing` and to the `done` line `Run.ship` logs, in
  `skills/mf-ship/scripts/conduct.py`, per [D10](design.md#d10).
  Verify: `grep -c 'self.supervisors()' skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 4.2 In `test_a_supervisor_answers_a_diagnosed_halt` of `tests/test_conduct.py`, assert the `done` line ending
  `released v0.1.0 · supervised 0001-todo` and `report`'s `0001-todo · supervised 1.1 · <sha7>`, as the design's `## Tests` names them.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_answers_a_diagnosed_halt` reports `1 passed`.
- [ ] 4.3 Add `"supervise"` to `STATIONS` and `SPENT`, `Version.supervised` and `METRICS["supervisor-decided"]` in
  `scripts/metrics/run.py`, per [D10](design.md#d10).
  Verify: `grep -n '"supervisor-decided"' scripts/metrics/run.py` prints a line.
- [ ] 4.4 Add the `supervisor-decided` metric after `rescues-decided` in `metrics/catalogue.toml`, per [D10](design.md#d10).
  Verify: `grep -n 'id = "supervisor-decided"' metrics/catalogue.toml` prints a line.
- [ ] 4.5 Extend `_RUN_B` and `expected` of `test_run_metrics_read_the_run_logs` in `tests/test_metric_scripts.py`, as the
  design's `## Tests` names them.
  Verify: `grep -n 'supervise — 0001-x: decided' tests/test_metric_scripts.py` prints a line.
- [ ] 4.6 Add D61 after D60 in `docs/decisions.md`, as [D10](design.md#d10) quotes it, and its id to the map's *Repo
  conventions* list after D60.
  Verify: `grep -n '^### D61 · A supervisor answers what rescue diagnoses$' docs/decisions.md` prints a line.
- [ ] 4.7 Edit D15's drift line in `docs/decisions.md`, per [D10](design.md#d10), the words
  `the rescue's or the supervisor's answers it` on one line.
  Verify: `grep -n "the rescue's or the supervisor's answers it" docs/decisions.md` prints a line.
- [ ] 4.8 Edit D47's `HALTS` sentence and its Rejected line in `docs/decisions.md`, per [D10](design.md#d10), the words
  `and under the switch its supervisor` on one line.
  Verify: `grep -n 'and under the switch its supervisor' docs/decisions.md` prints a line.
- [ ] 4.9 Add the trailer-less rescue amend to D53's Accepts in `docs/decisions.md`, per [D10](design.md#d10), the words
  `which reads as the person's` on one line.
  Verify: `grep -n "which reads as the person's" docs/decisions.md` prints a line.
- [ ] 4.10 Drop "a supervisor role" from D60's Rejected in `docs/decisions.md`, per [D10](design.md#d10).
  Verify: `grep -L 'a supervisor role' docs/decisions.md` prints `docs/decisions.md`.
- [ ] 4.11 Add [D10](design.md#d10)'s paragraph to *Out of scope* in `THREAT_MODEL.md`, the words
  `known by its subject and paths alone` on one line.
  Verify: `grep -n 'known by its subject and paths alone' THREAT_MODEL.md` prints a line.
- [ ] 4.12 Edit the *A merge* bullet of `docs/principles.md`, per [D9](design.md#d9), the words
  `the rescue's or the supervisor's amends` on one line.
  Verify: `grep -n "the rescue's or the supervisor's amends" docs/principles.md` prints a line.
- [ ] 4.13 Add the `mf-supervise` row to `README.md` and the `mf-supervise` clause to `AGENTS.md`'s *Layout*, per
  [D10](design.md#d10).
  Verify: `grep -l 'mf-supervise' README.md AGENTS.md` prints both paths.
