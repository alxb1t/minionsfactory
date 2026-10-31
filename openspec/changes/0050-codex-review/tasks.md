# Codex as reviewer — tasks

Build the settled [design](design.md), one phase at a time. The skill and decision text is the design's, word for word.

## Progress

- [x] 1 — The executor
- [x] 2 — The reach
- [ ] 3 — The record
- [ ] 4 — The proof

## 1 — The executor

- [x] 1.1 In `skills/mf-ship/scripts/conduct.py`, return the executor from `_models` with its validation, and build each
  worker from it, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -c '^EXECUTORS = ' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 1.2 In `skills/mf-ship/scripts/conduct.py`, add `Run.executors`, and probe each executor, per [D3](design.md#d3).
  Verify: `grep -c 'def executors' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 1.3 In `tests/test_conduct.py`, add `test_a_station_runs_on_its_executor` and
  `test_a_models_mismatch_halts_its_version`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "on_its_executor or models_mismatch"` reports `2 passed`.

## 2 — The reach

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py`, replace `edit_root` with `reach`, per [D5](design.md#d5), and edit
  `tests/test_conduct.py`'s `test_a_worker_carries_the_allowlist_and_a_denial_is_named`.
  Verify: `grep -c 'def edit_root' skills/mf-ship/scripts/conduct.py` prints `0`.
- [x] 2.2 In `skills/mf-ship/scripts/conduct.py`, load `integrate.py` once, and add `_git_state` to `merge_in`, per
  [D6](design.md#d6); edit `tests/test_conduct.py`'s `test_after_waits_for_its_dependency`, and add
  `test_a_changed_git_config_halts_a_merge_in`.
  Verify: `uv run pytest -q tests/test_conduct.py` reports `16 passed`.

## 3 — The record

- [ ] 3.1 Add the **Executors** bullet to D47 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -c '^- \*\*Executors:\*\*' docs/decisions.md` prints `1`.
- [ ] 3.2 Edit `skills/mf-ship/SKILL.md` and `skills/mf-cut-change/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -c 'executor = "codex"' skills/mf-cut-change/SKILL.md` prints `1`.

## 4 — The proof

- [ ] 4.1 Under `../mf_codex_probe/`, build `seeded` and `clean` per [D7](design.md#d7).
  Verify: `make -C ../mf_codex_probe/seeded gate` exits 0, and `make -C ../mf_codex_probe/clean gate` exits 0.
- [ ] 4.2 **HALT CHECK** Run the calibration on `seeded` and `clean`, score them, and write
  `openspec/changes/0050-codex-review/evidence/calibration.md`, per [D7](design.md#d7).
  Verify: `grep -c '^seeded: 5 of 5' openspec/changes/0050-codex-review/evidence/calibration.md` prints `1`, and
  `grep -c '^clean: no blocker' openspec/changes/0050-codex-review/evidence/calibration.md` prints `1`.
- [ ] 4.3 **HALT CHECK** Build `cross` and run it, per [D7](design.md#d7), adding its line to the evidence file.
  Verify: `grep -c '^cross: done · build claude · converge codex · release claude' openspec/changes/0050-codex-review/evidence/calibration.md` prints `1`.
- [ ] 4.4 Delete `../mf_codex_probe/`.
  Verify: `test ! -e ../mf_codex_probe` exits 0.
