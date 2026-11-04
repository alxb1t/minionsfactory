# Rejoin — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [ ] 1 — The stale halt
- [ ] 2 — The request
- [ ] 3 — Grant
- [ ] 4 — The base
- [ ] 5 — The docs

## 1 — The stale halt

- [ ] 1.1 Add `_answered`, and its case to `stage_of` and `_check_converge`, and the unspent grant to `advance`, in
  `skills/mf-ship/scripts/conduct.py`; add `test_a_fix_after_a_cap_halt_converges_afresh` to `tests/test_conduct.py`, with its
  fake-worker mode in `tests/fake_worker.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k fix_after_a_cap_halt_converges_afresh` reports `1 passed`.
- [ ] 1.2 Add the `· amended` run and the resumed `· grant` run to *Resuming a run* in `skills/mf-converge/SKILL.md`, per
  [D4](design.md#d4).
  Verify: `grep -n '· amended' skills/mf-converge/SKILL.md` prints a line.
- [ ] 1.3 Check `is_file()` in `_closed`; add a FIFO step to `test_a_build_dead_in_simplify_resumes_at_it`, per the design's
  *Context* F8.
  Verify: `uv run pytest -q tests/test_conduct.py -k build_dead_in_simplify_resumes_at_it` reports `1 passed`.

## 2 — The request

- [ ] 2.1 Add `REJOIN_POLL`, the `rejoin` subcommand, `take_requests`, the polling join loop, the start's deletion of requests,
  and `rejoin` in `EVENTS`, per [D1](design.md#d1), [D2](design.md#d2) and [D7](design.md#d7); add
  `test_a_fixed_version_rejoins_a_live_run` and `test_a_version_cut_during_a_run_joins`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "rejoins_a_live_run or cut_during_a_run_joins"` reports `2 passed`.
- [ ] 2.2 Add `self.probed` and `probe`'s `who`; add `test_a_new_executor_is_probed_mid_run`, a passing and a failing probe, per
  [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k new_executor_is_probed_mid_run` reports `1 passed`.
- [ ] 2.3 Add `report`'s `rejoined` line, a step in `test_a_fixed_version_rejoins_a_live_run`, per [D7](design.md#d7).
  Verify: `grep -n 'rejoined' skills/mf-ship/scripts/conduct.py` prints a line.

## 3 — Grant

- [ ] 3.1 Add `grant`'s refusals naming `/mf-ship`, its live-run path, the `grant` event, `grant` in `EVENTS` and the `start`
  line's grants; update the refusal and add the live-run step in `test_a_grant_buys_one_round`, per [D5](design.md#d5) and
  [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k grant_buys_one_round` reports `1 passed`.

## 4 — The base

- [ ] 4.1 Load `changelog` and `decisions` from `integrate.py`, settle their conflicts in `merge_in`, and call `merge_in` from
  `catch_up`'s gate-change case; update that case's step in `test_after_waits_for_its_dependency` — a merge that is clean, one
  that conflicts in `CHANGELOG.md`, and one that conflicts elsewhere and halts, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k after_waits_for_its_dependency` reports `1 passed`.

## 5 — The docs

- [ ] 5.1 Add `rejoin [<change-id>]` to the command table, `run · live`'s request to Step 2, and the `grant` row's refusal to
  `skills/mf-ship/SKILL.md`, per [D1](design.md#d1) and [D5](design.md#d5).
  Verify: `grep -n 'conduct.py rejoin\|rejoin \[<change-id>\]' skills/mf-ship/SKILL.md` prints a line.
- [ ] 5.2 Amend D47 in `docs/decisions.md`: a live run takes a rejoin request, a mailbox that holds no state; add
  `.minions/runs/rejoin/` to `THREAT_MODEL.md`'s *Entry points*, per the design's *Risks*.
  Verify: `grep -n 'rejoin' docs/decisions.md` prints a line, and `grep -n 'runs/rejoin' THREAT_MODEL.md` prints a line.
