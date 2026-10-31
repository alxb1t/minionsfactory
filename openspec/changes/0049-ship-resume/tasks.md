# Ship resume — tasks

Build the settled [design](design.md), one phase at a time. The skill and decision text is the design's, word for word.

## Progress

- [x] 1 — A dead worker
- [x] 2 — Integrate and release
- [x] 3 — The conductor

## 1 — A dead worker

- [x] 1.1 In `skills/mf-ship/scripts/conduct.py`, halt on a non-zero exit in `Run.spawn`, and add `usage_limit`, `_run_end`
  and `_converge_done`, per [D1](design.md#d1) and [D7](design.md#d7).
  Verify: `grep -c 'def _converge_done' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 1.2 In `skills/mf-ship/scripts/conduct.py`, make an unfinished run stage `converge`, per [D2](design.md#d2).
  Verify: `grep -c 'unfinished run' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 1.3 Add `## Resuming a run` to `skills/mf-converge/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -c '^## Resuming a run' skills/mf-converge/SKILL.md` prints `1`.
- [x] 1.4 In `tests/test_conduct.py`, make `_findings` write a status log ending on `done`, add `dies-<station>` to `_fake`,
  add `test_a_dead_converge_halts_and_a_rerun_finishes_it` and `test_a_usage_limit_is_named`, and edit
  `test_each_check_passes_only_on_disk_evidence`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "dead_converge or usage_limit"` reports `2 passed`.

## 2 — Integrate and release

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py`, make a no-note open merge stage `integrate`, read `tasks.md` from `HEAD`,
  and narrow `released`, per [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `grep -c 'the merge is left' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 2.2 Add `## A resumed release` to `skills/mf-release/SKILL.md`, per [D4](design.md#d4).
  Verify: `grep -c '^## A resumed release' skills/mf-release/SKILL.md` prints `1`.
- [x] 2.3 In `tests/test_conduct.py`, add `test_a_rerun_recovers_a_dead_release`, and edit
  `test_status_reads_each_stage_from_disk`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "dead_release or reads_each_stage"` reports `2 passed`.

## 3 — The conductor

- [x] 3.1 In `skills/mf-ship/scripts/conduct.py`, add `_unpushed` and `Run.push_left`, the `push` event, and `status`'s
  line, per [D5](design.md#d5).
  Verify: `grep -c 'def push_left' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py`, write the pid and the worker groups into the claim, and add `_claim` and
  `_clear`, per [D6](design.md#d6).
  Verify: `grep -c 'def _clear' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 3.3 In `tests/test_conduct.py`, add `test_a_rerun_pushes_what_a_release_left` and `test_a_stale_claim_is_cleared`, and
  edit `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py` reports `18 passed`.
- [x] 3.4 Edit `skills/mf-ship/SKILL.md`'s Step 2, per [D6](design.md#d6).
  Verify: `grep -c 'run · live' skills/mf-ship/SKILL.md` prints `1`.
- [x] 3.5 Amend D47 in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -c 'only a stage left in' docs/decisions.md` prints `1`.
