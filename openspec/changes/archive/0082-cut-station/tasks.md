# Cut station — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The queue
- [x] 2 — The station
- [x] 3 — The unattended cut
- [x] 4 — The record

## 1 — The queue

- [x] 1.1 Add `SLUG`, `CLAIM_SECONDS`, `_queue`, `_queue_lock`, `_next_id`, `_cuts`, `_write_cut`, `_detach`, `_start_run`
  and `cut`, with its `cut` parser in `main` and its usage line in the module docstring, to
  `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1) and [D2](design.md#d2); `run(…, detach=True)` starts its
  child through `_detach`.
  Verify: `grep -n 'def _start_run' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Move the mailbox to `_queue(primary) / "rejoin"` — `_request(primary, name)`, `_requests(queue)`, `rejoin` and
  `grant` under the lock, `Run.queue` at the start and each poll — per [D3](design.md#d3), and replace `run()`'s
  `shutil.rmtree(active)` with `_close`, which starts the next run on a standing request once `Run.seen` — `None` in
  `__init__`, a set as `ship`'s first act — is a set, per
  [D2](design.md#d2); `grant` with none live starts the run through `_start_run`, per [D3](design.md#d3).
  Verify: `grep -L 'runs / "rejoin"' skills/mf-ship/scripts/conduct.py` prints `skills/mf-ship/scripts/conduct.py`.
- [x] 1.3 Point the planted and read requests of `test_a_new_executor_is_probed_mid_run`, `test_the_plan_is_read_once` and
  `test_a_grant_buys_one_round` in `tests/test_conduct.py` at `conduct["_queue"](root) / "rejoin"`, the last one's `run`
  spy turned into a `_start_run` stub, and have
  `rescue-answers` in `tests/fake_worker.py` touch the home request too, per [the design's Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "new_executor_is_probed or plan_is_read_once or grant_buys_one_round"` reports `3 passed`.
- [x] 1.4 Add `test_parallel_cuts_reserve_apart_and_start_one_run`, `test_a_started_run_is_seen_by_its_claim_or_its_end`
  and `test_a_request_at_a_runs_close_starts_the_next_run` to `tests/test_conduct.py`, per
  [the design's Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "parallel_cuts_reserve or started_run_is_seen or request_at_a_runs_close"` reports `3 passed`.

## 2 — The station

- [x] 2.1 In `tests/fake_worker.py`, read the station with `Run the mf-([a-z-]+) skill(?: for change (\S+?)[ .])?`, and add
  the `cut-change` station: it commits `openspec/changes/<id>/proposal.md` and `tasks.md` as
  `docs(<id>): land the change directory` and writes `.minions/changes/<id>/models.toml`; under `cut-halts` it writes
  `.minions/changes/<id>/cut.halt` holding `<id> waits on one doubt: two readings · tasks.md:3` and commits nothing;
  `cut-empty`, `cut-dirty`, `cut-bare` and `dies-cut` as [the design's Tests](design.md#tests) name them.
  Verify: `grep -n 'cut-halts' tests/fake_worker.py` prints a line.
- [x] 2.2 Add `PROMPTS["cut"]`, `cut` to `EVENTS`, the queue read into `Run.seen` at `ship`'s start and in `take_requests`,
  `Run.cut`, `_check_cut`, `Run.admit` moved out of `take_back`, and `Run.cut_halted` to
  `skills/mf-ship/scripts/conduct.py`, per [D4](design.md#d4) and [D6](design.md#d6); `_close` also starts the next run
  on a queued cut with no `halt` the run never read, per [D2](design.md#d2).
  Verify: `grep -n 'Run the mf-cut-change skill for change' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.3 Give `argv` and `spawn` a `brief: Path | None = None`, passed on only when set, that narrows the worker's reach to its worktree, the run
  directory, the common directory and the brief, per [D5](design.md#d5).
  Verify: `grep -n 'brief: Path | None = None' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.4 Print `<id> · cut` and `<id> · cut-halted — <halt>` in `status`, and have `rejoin <id>` clear a queued cut's halt,
  then request it or start a run, per [D6](design.md#d6).
  Verify: `grep -n 'cut-halted — ' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.5 Add `test_a_queued_cut_is_cut_then_built` and `test_a_cut_halt_is_shown_and_rejoin_cuts_again`, both `slow`, and
  extend `test_a_worker_carries_the_allowlist_and_a_denial_is_named` and `test_a_request_at_a_runs_close_starts_the_next_run`,
  in `tests/test_conduct.py`, per [the design's Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k "queued_cut_is_cut or cut_halt_is_shown or carries_the_allowlist or request_at_a_runs_close"` reports `4 passed`.

## 3 — The unattended cut

- [x] 3.1 Add the `unattended` row to the *Parameters* table of `skills/mf-cut-change/SKILL.md`, and the **Unattended**
  paragraph after it, per [D7](design.md#d7).
  Verify: `grep -n 'decided by the cutter' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.2 Edit Steps 1, 3, 4, 6, 8.5, 9 and 11 of `skills/mf-cut-change/SKILL.md` for the unattended cut, per
  [D7](design.md#d7).
  Verify: `grep -n 'Next: the run builds it.' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.3 Edit *Suggesting models* and *Never* in `skills/mf-cut-change/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -n 'where the brief names the models' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 3.4 Rewrite Step 2's *Moved facts* opening in `skills/mf-cut-change/SKILL.md`, per [D8](design.md#d8).
  Verify: `grep -n '7 to 40 characters of' skills/mf-cut-change/SKILL.md` prints a line.

## 4 — The record

- [x] 4.1 Add **D58 · A settled brief is cut by a conductor station** to *Planning* in `docs/decisions.md`, and its id to the
  diagram's Planning list, per [D9](design.md#d9).
  Verify: `grep -n '### D58 · A settled brief is cut by a conductor station' docs/decisions.md` prints a line.
- [x] 4.2 Amend D20, D38, D41, D44, D47, D51 and D57 in `docs/decisions.md`, per [D9](design.md#d9).
  Verify: `grep -L 'a reservation file' docs/decisions.md` prints `docs/decisions.md`.
- [x] 4.3 Edit *Unattended workers*, *A person's yes*, the brief's and the rejoin requests' *Entry points*, and add the cut
  queue's entry point, in `THREAT_MODEL.md`, per [D9](design.md#d9).
  Verify: `grep -n 'a cut the person queued' THREAT_MODEL.md` prints a line.
- [x] 4.4 Edit *The repo reaches nothing outside itself* in `docs/principles.md`, per [D9](design.md#d9).
  Verify: `grep -n -F '.queue/' docs/principles.md` prints a line.
- [x] 4.5 Edit the role line, the diagram, the command table, the `status` and `rejoin` rows and Step 2's table in
  `skills/mf-ship/SKILL.md`, per [D9](design.md#d9).
  Verify: `grep -n 'cut-halted' skills/mf-ship/SKILL.md` prints a line.
- [x] 4.6 Name the queued cut in the `mf-ship` row and *Parallel workspaces* of `README.md`, per [D9](design.md#d9).
  Verify: `grep -n 'conduct.py cut' README.md` prints a line.
