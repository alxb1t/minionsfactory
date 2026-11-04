# Offline origin — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The offline base
- [x] 2 — The waits
- [x] 3 — The local release
- [ ] 4 — The record
- [ ] 5 — The docs

## 1 — The offline base

- [x] 1.1 Add `_pushed_file`, `_keep_base` and `_offline_base`, and write the base in `_unpushed` and `push_left`, in
  `skills/mf-ship/scripts/conduct.py`; add `test_a_good_read_keeps_the_offline_base` to `tests/test_conduct.py`, per
  [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k good_read_keeps_the_offline_base` reports `1 passed`.
- [x] 1.2 Add the `anchor` subcommand and its checks; add `test_anchor_seeds_the_offline_base`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k anchor_seeds_the_offline_base` reports `1 passed`.

## 2 — The waits

- [x] 2.1 Add `Unreachable`, `RETRIES` and the offline judge; read `origin` before the `start` line; halt with no offline base;
  add `test_a_run_goes_on_while_origin_is_down`, its run stopping at the release check, per [D2](design.md#d2) and
  [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k run_goes_on_while_origin_is_down` reports `1 passed`.
- [x] 2.2 Add the ssh options to `_outside`; add `test_the_remote_calls_carry_the_ssh_options`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k remote_calls_carry_the_ssh_options` reports `1 passed`.
- [x] 2.3 Name a missing `origin/<default>` in `_unpushed`'s no-read path; add its step to
  `test_status_reads_each_stage_from_disk`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k status_reads_each_stage_from_disk` reports `1 passed`, and
  `grep -n 'push it by hand' skills/mf-ship/scripts/conduct.py` prints a line.

## 3 — The local release

- [x] 3.1 Pass `offline` to `check` and `_check_release`; push pending refs at each release with `PUSH_RETRIES`, a refused
  push still a halt; add
  `test_a_local_release_is_pushed_when_origin_returns`, and take `test_a_run_goes_on_while_origin_is_down` through a local release
  and a dependent, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "origin_is_down or origin_returns or release_left"` reports `3 passed`.
- [x] 3.2 **HALT CHECK** Read `_pushed` for `0049·S7`'s *Still true?*: its remote call is `_listed`, through `_outside`; name
  that in the phase commit's body, per [D7](design.md#d7).
  Verify: `grep -n '_listed(primary, url' skills/mf-ship/scripts/conduct.py` prints a line.

## 4 — The record

- [ ] 4.1 Add the `start` line's field, the `push — waiting` events, the close's `· unpushed` and `report`'s `run · waited` lines;
  add their steps to `test_a_run_goes_on_while_origin_is_down`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k run_goes_on_while_origin_is_down` reports `1 passed`, and
  `grep -n 'origin: unreachable — pushes wait' skills/mf-ship/scripts/conduct.py` prints a line.

## 5 — The docs

- [ ] 5.1 Add `anchor` to the command table, and the no-offline-base halt to the halt table, in `skills/mf-ship/SKILL.md`, per
  [D6](design.md#d6).
  Verify: `grep -n 'conduct.py anchor' skills/mf-ship/SKILL.md` prints a line.
- [ ] 5.2 Amend D47 in `docs/decisions.md`: a failed read of `origin` waits, and the first offline base needs the person; amend
  D51: the offline base stands beside the kept URLs, per [D2](design.md#d2) and [D6](design.md#d6).
  Verify: `grep -n 'offline base' docs/decisions.md` prints a line.
- [ ] 5.3 Add to `THREAT_MODEL.md` *Known gaps*: the ledger's window held open by an outage, and the anchor's one trust in the
  tracking ref, per the design's *Risks*.
  Verify: `grep -n 'conduct.py anchor' THREAT_MODEL.md` prints a line.
