# Supervisor merge — tasks

Build the settled [design](design.md), one phase at a time, on 0089-supervisor's merged code.

## Progress

- [x] 1 — The brief kept
- [x] 2 — The integrate settle
- [ ] 3 — The record

## 1 — The brief kept

- [x] 1.1 **HALT CHECK** 0089's `Run.supervise` stands in `skills/mf-ship/scripts/conduct.py`, called at both sites of
  `advance`, as [the design's F1](design.md#context) reads it.
  Verify: `grep -c 'self.supervise(' skills/mf-ship/scripts/conduct.py` prints `2`.
- [x] 1.2 Record the brief in `cutting`'s pass, with its docstring line, and add `_brief_of` beside `_queue` in
  `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1).
  Verify: `grep -n '^def _brief_of(' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.3 Give `PROMPTS["supervise"]` its `{brief}` field, add `_supervise_prompt` beside `_brief_of`, and have `Run.supervise`
  take its prompt from it, per [D1](design.md#d1).
  Verify: `grep -n '_supervise_prompt(self.primary' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.4 Add the `cut-decides` mode to `_cut` and the brief clause to `_fake`'s call line in `tests/fake_worker.py`, as the
  design's `## Tests` tables them.
  Verify: `grep -n 'cut-decides' tests/fake_worker.py` prints a line.
- [x] 1.5 In `test_a_queued_cut_is_cut_then_built` of `tests/test_conduct.py`, assert the record after the first run, as the
  design's `## Tests` names it.
  Verify: `grep -n -F '"briefs" / "0001-a"' tests/test_conduct.py` prints a line.
- [x] 1.6 Add `test_a_cut_brief_reaches_the_supervisor` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_brief_reaches_the_supervisor` reports `1 passed`.
- [x] 1.7 Add the `brief` parameter and Step 1's read of the brief to `skills/mf-supervise/SKILL.md`, per [D6](design.md#d6),
  the words `passed cut recorded one` on one line.
  Verify: `grep -n 'passed cut recorded one' skills/mf-supervise/SKILL.md` prints a line.

## 2 — The integrate settle

- [x] 2.1 Add `Opened` beside `ShipLines`, `SETTLES` beside `SUPERVISES`, and `_opened` and `_settled` beside `_supervised` in
  `skills/mf-ship/scripts/conduct.py`, its refusals as [D3](design.md#d3)'s table words them.
  Verify: `grep -n '^def _settled(' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.2 Add `_merge_tried` beside `_brief_of`, widen `Run.supervise`'s trigger and record its try per [D2](design.md#d2),
  and give it [D4](design.md#d4)'s integrate branch, with `self.settled` in `Run.__init__`.
  Verify: `grep -n 'self.settled.add(' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.3 Add `SETTLED` and `Run.stage`, read `self.stage(version)` in `Run.advance`, give `PROMPTS["integrate"]` its
  `{settled}` field, and fill it in `Run.advance`, with its docstring line, per [D4](design.md#d4).
  Verify: `grep -n 'with settled=supervisor' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.4 Give `_supervise` its `primary` parameter and the `supervise-settle` and `supervise-settle-code` modes, and
  `_integrate` its `settled` parameter, in `tests/fake_worker.py`, as the design's `## Tests` tables them.
  Verify: `grep -n 'supervise-settle-code' tests/fake_worker.py` prints a line.
- [x] 2.5 Add `test_a_supervisor_settles_an_integrate_note` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_settles_an_integrate_note` reports `1 passed`.
- [x] 2.6 Add `test_a_supervisor_settle_outside_the_text_halts` to `tests/test_conduct.py`, as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k supervisor_settle_outside_the_text_halts` reports `1 passed`.
- [x] 2.7 Add the `settled` parameter, Step 2's resumed-run reading, Step 3.1's and Step 4.5's `integrate.settled` and Step
  4.3's `the supervisor` row to `skills/mf-integrate/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -n '<path>: the supervisor' skills/mf-integrate/SKILL.md` prints a line.
- [x] 2.8 Add Step 1's read of the note, Step 2's never-list edits, Step 3c and the description's clause to
  `skills/mf-supervise/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'Step 3c — an integrate note' skills/mf-supervise/SKILL.md` prints a line.

## 3 — The record

- [ ] 3.1 Edit D45 in `docs/decisions.md`, per [D7](design.md#d7), the words `whose settle of spec and docs text it commits`
  on one line.
  Verify: `grep -n 'whose settle of spec and docs text it commits' docs/decisions.md` prints a line.
- [ ] 3.2 Edit D57's file list in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -n -F 'integrate.{md,red,resolved,settled}' docs/decisions.md` prints a line.
- [ ] 3.3 Edit D61's trigger and its never list in `docs/decisions.md`, per [D7](design.md#d7), the words
  `integrate semantic-conflict halt` on one line.
  Verify: `grep -n 'integrate semantic-conflict halt' docs/decisions.md` prints a line.
- [ ] 3.4 Add D61's **An integrate note** and **The brief** bullets and its Rejected clause in `docs/decisions.md`, per
  [D7](design.md#d7).
  Verify: `grep -n -F '**The brief:** a passed cut records' docs/decisions.md` prints a line.
- [ ] 3.5 Add the brief record to the cut-queue bullet of `THREAT_MODEL.md`'s *Entry points*, per [D7](design.md#d7).
  Verify: `grep -n -F 'briefs/<id>' THREAT_MODEL.md` prints a line.
- [ ] 3.6 Add [D7](design.md#d7)'s integrate sentence to `THREAT_MODEL.md`'s *Out of scope*, the words
  `the integrate station then commits` on one line.
  Verify: `grep -n 'the integrate station then commits' THREAT_MODEL.md` prints a line.
- [ ] 3.7 Edit Step 4's `integrating` sentence in `skills/mf-ship/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n 'supervised integrating' skills/mf-ship/SKILL.md` prints a line.
- [ ] 3.8 Edit the answered row of `skills/mf-ship/SKILL.md`, per [D7](design.md#d7), the words
  `the supervisor at a converge or integrate halt` on one line.
  Verify: `grep -n 'the supervisor at a converge or integrate halt' skills/mf-ship/SKILL.md` prints a line.
- [ ] 3.9 Edit the `mf-supervise` row of `README.md`, per [D7](design.md#d7).
  Verify: `grep -n 'a settle of an integrate note' README.md` prints a line.
