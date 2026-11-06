# Ship fixes 2 — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The halt before round 1 answered
- [ ] 2 — The load-bound tests
- [ ] 3 — A scratch folder for every worker

## 1 — The halt before round 1 answered

- [x] 1.1 Add `RERUN`, `_run_started`, `_before_round` and `_rerun` to `skills/mf-ship/scripts/conduct.py`, read in `_answered` and
  `stage_of`, per [D1](design.md#d1) and [D2](design.md#d2); in `test_a_fix_after_a_cap_halt_converges_afresh`, add a `start` line
  below each headed halt it writes, save the debt lock's, per the design's `## Tests`.
  Verify: `grep -n '^RERUN = ' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Add `RERAN` and `Run.reruns`, filled in `advance` and read in `take_back`, per [D1](design.md#d1); add the `red-halts`
  converge mode to `tests/fake_worker.py`, and `test_a_halt_before_round_1_runs_again_at_the_same_head` to `tests/test_conduct.py`,
  as the design's `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k halt_before_round_1_runs_again_at_the_same_head` reports `1 passed`.
- [x] 1.3 Add the halt-before-round-1 paragraph to `skills/mf-converge/SKILL.md`'s *Resuming a run*, after the debt-lock one, per
  [D1](design.md#d1).
  Verify: `grep -n 'open a plain new run' skills/mf-converge/SKILL.md` prints a line.

## 2 — The load-bound tests

- [ ] 2.1 Age the young lock in `test_a_stale_lock_is_cleared_and_converge_resumes` by `LOCK_STALE - 60`, per [D3](design.md#d3).
  Verify: `grep -nF '(conduct["LOCK_STALE"] - 60)' tests/test_conduct.py` prints a line.
- [ ] 2.2 Raise `tests/test_metrics.py`'s limit to 5 s and move the timed-out script to
  `test_a_metric_past_the_limit_is_unavailable`, marked `slow`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_metrics.py -k metric_past_the_limit_is_unavailable` reports `1 passed`.
- [ ] 2.3 Name each version's thread for its change in `skills/mf-ship/scripts/conduct.py`, and replace `_when_logged`'s
  `time.sleep(0.5)` with the poll on those threads, in `tests/test_conduct.py`, per [D5](design.md#d5).
  Verify: `grep -L 'time.sleep(0.5)' tests/test_conduct.py` prints `tests/test_conduct.py`.

## 3 — A scratch folder for every worker

- [ ] 3.1 Add `TMPDIR` to `argv`'s `env` prefix on both executors, and `_fresh_tmp`, called in `Run.ship`, to
  `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6); extend `test_a_claude_worker_starts_in_the_sandbox`,
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named` and `test_a_stale_lock_is_cleared_and_converge_resumes` as `## Tests` says.
  Verify: `grep -n 'TMPDIR=' skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 3.2 Add the `mktemp` line to `skills/mf-release/SKILL.md` Step 2, per [D6](design.md#d6).
  Verify: `grep -n 'mktemp' skills/mf-release/SKILL.md` prints a line.
