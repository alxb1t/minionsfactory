# Cut halts — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [x] 1 — The brief
- [x] 2 — The queue
- [x] 3 — The cut
- [x] 4 — The answers
- [x] 5 — The record
- [ ] 6 — Rejoin takes a new package only on the person's hash

## 1 — The brief

- [x] 1.1 Add `DEPENDENCIES`, `APPROVED` and `_rows` beside `_cuts` in `skills/mf-ship/scripts/conduct.py`, per
  [D3](design.md#d3).
  Verify: `grep -n '^def _rows' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Add `## Dependencies` to `_READY`, `_OUT_OF_SHAPE`'s line and the section steps to `tests/test_brief_check.py`, as
  the design's `## Tests` rows say for 1.2, then the section's halts in `skills/mf-plan/scripts/brief_check.py`, `_rows`
  loaded from `CONDUCT`, per [D2](design.md#d2).
  Verify: `grep -n 'no ## Dependencies section' skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.3 Edit `test_a_brief_out_of_shape_halts` and `test_what_cannot_be_checked_exits_2`, as the design's `## Tests` rows
  say, then the grammar, printable and heading rules and the docstring in `brief_check.py`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_brief_check.py` reports `3 passed`.
- [x] 1.4 Add `## Dependencies` and its paragraph to the template of `skills/mf-plan/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n '| item | package | constraint | why |' skills/mf-plan/SKILL.md` prints a line.
- [x] 1.5 Add the packages row to Step 3, the packages bullet to Step 4, and edit Step 6's items 2 and 3 in
  `skills/mf-plan/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n 'each .## Dependencies. row' skills/mf-plan/SKILL.md` prints a line.
- [x] 1.6 Add the background bullet to Step 2's *Helpers* in `skills/mf-plan/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n 'gathering the facts' skills/mf-plan/SKILL.md` prints a line.

## 2 — The queue

- [x] 2.1 Add modes `cut-packages` and `cut-prose` to `_cut` in `tests/fake_worker.py`, and `dependencies` to `_queued` in
  `tests/test_conduct.py`, as the design's `## Tests` says.
  Verify: `grep -n 'cut-prose' tests/fake_worker.py` prints a line.
- [x] 2.2 Extend `test_parallel_cuts_reserve_apart_and_start_one_run` in `tests/test_conduct.py`, as the design's `## Tests`
  row says, then `_approved`, `_approval` and the copy in `cut` of `skills/mf-ship/scripts/conduct.py`, per
  [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k parallel_cuts_reserve_apart_and_start_one_run` reports `1 passed`.
- [x] 2.3 Add the `0005-p` step to `test_a_queued_cut_is_cut_then_built`, and the `0021-q` loop entry and the `0020-p` halt
  to `test_a_cut_halt_is_shown_and_rejoin_cuts_again`, in `tests/test_conduct.py`, then `_unapproved` and its call in
  `Run.cutting` of `skills/mf-ship/scripts/conduct.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_halt_is_shown_and_rejoin_cuts_again` reports `1 passed`.
- [x] 2.4 Add the `0020-p` rejoin steps to `test_a_cut_halt_is_shown_and_rejoin_cuts_again`, as the design's `## Tests` row
  says, then `_approval`'s use in `rejoin` of `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k "queued_cut_is_cut_then_built or cut_halt_is_shown"` reports `2 passed`.

## 3 — The cut

- [x] 3.1 Edit the *Always a halt* bullet and add the *A package the brief lists* bullet in the Unattended paragraph of
  `skills/mf-cut-change/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'A package the brief lists' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.2 Add the queued-id bullet to Step 1 of `skills/mf-cut-change/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'is queued for the cut station' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.3 Edit Step 6's `design.md` bullet, Step 9's unattended line and the *Never* dependency line of
  `skills/mf-cut-change/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n '| package | constraint | why |' skills/mf-cut-change/SKILL.md` prints a line.

## 4 — The answers

- [x] 4.1 Add the phase 4 steps to `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in `tests/test_conduct.py`, as the
  design's `## Tests` row says, then `_cut_answer`, `_cutter_halt`, the suffix in `Run.cutting` and the branch in
  `Run._needs` of `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_halt_is_shown_and_rejoin_cuts_again` reports `1 passed`.
- [x] 4.2 Add D5's sentences to the `cut-halted` row of `skills/mf-ship/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -n 'its brief answered' skills/mf-ship/SKILL.md` prints a line.

## 5 — The record

- [x] 5.1 Add D62 after D59 in `docs/decisions.md`, and its id to the map's Planning list after D59, as
  [D8](design.md#d8) quotes it.
  Verify: `grep -n '^### D62 · A queued cut.s packages are approved at the plan$' docs/decisions.md` prints a line.
- [x] 5.2 Edit D38 and D58 in `docs/decisions.md`, per [D8](design.md#d8), the phrase below on one line.
  Verify: `grep -n 'against its queued copy' docs/decisions.md` prints a line.
- [x] 5.3 Edit the brief bullet and the cut-queue bullet of *Entry points* in `THREAT_MODEL.md`, per [D8](design.md#d8), the
  phrase below on one line.
  Verify: `grep -n 'widens that list' THREAT_MODEL.md` prints a line.
- [x] 5.4 Edit *A new dependency halts for a person* in `docs/principles.md`, per [D8](design.md#d8), the phrase below on one
  line.
  Verify: `grep -n 'for a queued cut at the plan' docs/principles.md` prints a line.

## 6 — Rejoin takes a new package only on the person's hash

The person's decision on security S1, option (a): [D3](design.md#d3)'s C2.

- [ ] 6.1 Extend the `0020-p` rejoin steps of `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in `tests/test_conduct.py`,
  as the design's `## Tests` row says, then `_rows_hash` and the `--yes <hash>` path in `rejoin` of
  `skills/mf-ship/scripts/conduct.py` — the queued rows kept, a new row taken only with the hash, else the halt naming each
  new row and the exact `conduct.py rejoin <id> --yes <hash>` command — per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k cut_halt_is_shown_and_rejoin_cuts_again` reports `1 passed`.
- [ ] 6.2 Drop the unconditional copy from `rejoin` in `skills/mf-ship/scripts/conduct.py`, so no rejoin writes the brief's
  rows over the queued ones, per [D3](design.md#d3).
  Verify: `grep -L '"halt": None, "dependencies": approved' skills/mf-ship/scripts/conduct.py` prints its path.
- [ ] 6.3 Add `--yes` to `rejoin`'s parser and the module docstring's usage line, and edit `rejoin`'s docstring, in
  `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `grep -n 'conduct.py rejoin \[<change-id>\] \[--yes <hash>\]' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 6.4 Edit the `rejoin` command row and the `cut-halted` row of `skills/mf-ship/SKILL.md`, per [D3](design.md#d3) and
  the row [D5](design.md#d5) quotes.
  Verify: `grep -L 'the rejoin copies the rows again' skills/mf-ship/SKILL.md` prints its path.
- [ ] 6.5 Edit D62 and D58 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -L 'copies the brief.s approved packages again' docs/decisions.md` prints its path.
- [ ] 6.6 Replace the rejoin clause of the brief bullet of *Entry points* in `THREAT_MODEL.md`, per [D8](design.md#d8).
  Verify: `grep -L 'a .rejoin. after a re-plan' THREAT_MODEL.md` prints its path.
