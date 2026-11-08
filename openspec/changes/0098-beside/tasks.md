# Beside — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code, save the guards its
`## Tests` names.

## Progress

- [x] 1 — The field
- [x] 2 — The plan and the record
- [ ] 3 — The record without counts

## 1 — The field

- [x] 1.1 **HALT CHECK** Confirm `0088·S9` and `0088·S10` are held at the base by the `split` and `forms` steps of
  `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`, per [D2](design.md#d2); missing, the plan is wrong.
  Verify: `grep -c -e 'S7: a .| . line under a head' -e 'S8: a .## For the cut. heading' tests/test_brief_check.py` prints `2`.
- [x] 1.2 Add the `besides` step to `test_a_brief_out_of_shape_halts` and the `beside:` head step to
  `test_a_hard_brief_is_ready_for_the_cut` in `tests/test_brief_check.py`, as the design's `## Tests` rows say, then the
  `beside:` halts in `head()` of `skills/mf-plan/scripts/brief_check.py`, per [D1](design.md#d1).
  Verify: `grep -n 'more than one beside:' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.3 Add the `headless` step to `test_a_brief_out_of_shape_halts` in `tests/test_brief_check.py`, then `seen_head` in
  `grammar()` of `skills/mf-plan/scripts/brief_check.py`, per [D2](design.md#d2) (`0091·R3`).
  Verify: `grep -n 'seen_head' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.4 Add the `html` step to `test_a_brief_out_of_shape_halts` and the `Результат` step to
  `test_a_hard_brief_is_ready_for_the_cut` in `tests/test_brief_check.py`, then `HEADING_TAG`, `fold()`'s tag drop and
  `alike()`, read by `headings()`, in `skills/mf-plan/scripts/brief_check.py`, per [D2](design.md#d2) (`0091·S3`).
  Verify: `grep -n '^def alike' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.5 Edit the docstrings [D2](design.md#d2)'s last bullet names: the module's, `head`'s, `grammar`'s, `fold`'s and
  `headings`' in `skills/mf-plan/scripts/brief_check.py`, and `_headed`'s in `skills/mf-ship/scripts/conduct.py`.
  Verify: `grep -n '0098-beside design D1, D2' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.6 Add `beside` to `_version` and the new `test_beside_waits_on_nothing` to `tests/test_conduct.py`, as the design's
  `## Tests` says, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k beside_waits_on_nothing` reports `1 passed`.
- [x] 1.7 Extend `test_parallel_cuts_reserve_apart_and_start_one_run` in `tests/test_conduct.py`, as the design's `## Tests`
  row says, then the `links` argument, its checks, the `beside` shape check, the entry's key, the usage line and the why line
  in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `grep -n 'expected after=<ids> or beside=<ids>' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.8 Add `beside` to `_queued` and the `0006-s` step to `test_a_queued_cut_is_cut_then_built` in
  `tests/test_conduct.py`, and ` beside=` to `_cut` in `tests/fake_worker.py`, as the design's `## Tests` says, then
  `{beside}` in `PROMPTS["cut"]` and its value in `Run.cutting` of `skills/mf-ship/scripts/conduct.py`, per
  [D4](design.md#d4).
  Verify: `grep -n '{after}{beside}' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.9 Add the `beside` parameter row and the Step 6 `beside` bullet to `skills/mf-cut-change/SKILL.md`, as
  [D4](design.md#d4) quotes them.
  Verify: `grep -n 'also lists them: .beside: \[0047-x\]' skills/mf-cut-change/SKILL.md` prints a line.

## 2 — The plan and the record

- [x] 2.1 Replace the how of the `parallel with` row in Step 3 of `skills/mf-plan/SKILL.md`, as [D5](design.md#d5)
  quotes it.
  Verify: `grep -n 'else .beside:., the default (D69)' skills/mf-plan/SKILL.md` prints a line.
- [x] 2.2 Edit Step 6's items 2 and 4 in `skills/mf-plan/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -n '\[after=<ids>\] \[beside=<ids>\]' skills/mf-plan/SKILL.md` prints a line.
- [x] 2.3 Add the `beside:` part to the template's head, and its sentence to the end of the paragraph opening
  "`## For the cut` is filled when the frontier is empty", in `skills/mf-plan/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -n 'beside: <ids, or the slug of an earlier item>' skills/mf-plan/SKILL.md` prints a line.
- [x] 2.4 Edit the `cut` row of `skills/mf-ship/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -n 'an .after. id or a .beside. id it refuses' skills/mf-ship/SKILL.md` prints a line.
- [x] 2.5 Add D69 after D65 in `docs/decisions.md`, as [D6](design.md#d6) quotes it.
  Verify: `grep -n '^### D69 · A version names what it builds beside$' docs/decisions.md` prints a line.
- [x] 2.6 Add `, D69` after `D65` in the Planning list of the map at the top of `docs/decisions.md`, per
  [D6](design.md#d6).
  Verify: `grep -n 'D59, D62, D65, D69' docs/decisions.md` prints a line.

## 3 — The record without counts

- [ ] 3.1 Replace D69's `**Why:**` bullet in `docs/decisions.md` with the count-free one [D6](design.md#d6) quotes, so the
  record and its quotation agree and the counts stay in [Evidence](design.md#evidence) (`0098-beside conformance R1`).
  Verify: `grep -n "most of 0081–0095's .after:. links only avoided file overlap" docs/decisions.md` prints a line.
