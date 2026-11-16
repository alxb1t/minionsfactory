# Queue cap — tasks

The phases follow [design](design.md): the setting, the gate, what is shown, the record. Each task names its files and links the decisions it follows.

## Progress

- [ ] 1 — The setting · moderate
- [ ] 2 — The gate · hard
- [ ] 3 — What is shown · moderate
- [ ] 4 — The record · moderate

## 1 — The setting

- [ ] 1.1 In `tests/test_conduct.py` add the helper `_ship_toml(text)`, which writes `ship.toml` under `$XDG_CONFIG_HOME/minionsfactory/`, and `test_cap_reads_ship_toml`: no file, no `[queue]` table and no key give `None`; `in_flight = 2` gives `2`; an unparsable file, `0`, `-1`, `1.5`, `"2"` and `true` raise `Stop` with code 2, naming the file ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_reads"` lists `test_cap_reads_ship_toml`.
- [ ] 1.2 In `skills/mf-ship/scripts/conduct.py` add `_cap() -> int | None` beside `_queue`, as [D1](design.md#d1) tabulates, with a docstring and an `e.g.` line.
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_reads"` passes.
- [ ] 1.3 In `tests/test_conduct.py` add `test_cap_file_that_is_bad_stops_the_run`: with `in_flight = 0` written, `_run_claude` returns 2, the output names `ship.toml`, and no `.minions/runs/active` stands.
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_file"` lists `test_cap_file_that_is_bad_stops_the_run`.
- [ ] 1.4 In `skills/mf-ship/scripts/conduct.py` set `self.cap: int | None = None` in `Run.__init__`, leaving its parameters as they are, and make `run()` call `_cap()` in its first `try` after `preconditions` and assign the value to `conductor.cap` once `Run` is built.
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_file"` passes.
- [ ] 1.5 In `docs/principles.md` add to the closed list of *The repo reaches nothing outside itself*, before the `pin.py` bullet, a bullet: `conduct.py`'s read-only read of the operator's `ship.toml` under `$XDG_CONFIG_HOME/minionsfactory/`, named in no repo, linking D84 ([D6](design.md#d6)).
  Verify: `git grep -n "ship.toml" -- docs/principles.md` prints a line of the closed list.

## 2 — The gate

- [ ] 2.1 **HALT CHECK** With no cap file, the test that holds the cuts and versions at once passes at HEAD: the gate of this phase must leave it as it stands ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_conduct.py -q -k "three_versions"` passes.
- [ ] 2.2 In `tests/test_conduct.py` add `test_cap_counts_only_versions_at_a_station`: on a `Run` whose `cap` is set, threads held on an event count, and a dead thread, a halted change (`halts` holds it), a change whose proposal's `after` names an unshipped id and a queued cut whose entry's `after` does the same do not; `room` is false at the cap of 1 with one live version and true at the cap of 2 ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_counts"` lists `test_cap_counts_only_versions_at_a_station`.
- [ ] 2.3 In `skills/mf-ship/scripts/conduct.py` add `Run.in_flight(threads)` and `Run.room(threads)` after `Run.live`, as [D2](design.md#d2) and [D3](design.md#d3) say; `room` reads nothing when `self.cap` is `None`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_counts"` passes.
- [ ] 2.4 In `tests/test_conduct.py` add `test_cap_gates_the_poll_and_not_a_request`: with `take_cut` stubbed and the cap full, `take_requests` takes no queued cut and the cut stays out of `seen`, and a `run · wait — <id>: 1 in flight, cap 1` line is logged once however many polls pass; once `room` holds, the next poll takes it; a cut named by a rejoin request is taken with the cap full ([D3](design.md#d3), [D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_gates"` lists `test_cap_gates_the_poll_and_not_a_request`.
- [ ] 2.5 In `skills/mf-ship/scripts/conduct.py` add `Run.waiting` (a dict), `Run.wait_cut(change, threads)` and `Run.unwait(change, entry)`; the first logs the `wait` event of [D5](design.md#d5) when a cut enters `waiting`, the second drops it. In `Run.take_requests` call `wait_cut` and skip a cut that `room` refuses, unless `names` holds it; make `Run.take_cut` call `unwait` first ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_gates"` passes.
- [ ] 2.6 In `tests/test_conduct.py` add `test_cap_of_one_runs_the_cuts_one_at_a_time`, marked `slow`: with `in_flight = 1` and a first and a second cut queued, `_run_claude` returns 0, the calls show `cut-change` of the second after `release` of the first, and the log holds a `wait` line for the second, logged once.
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_of_one"` lists `test_cap_of_one_runs_the_cuts_one_at_a_time`.
- [ ] 2.7 In `skills/mf-ship/scripts/conduct.py` change the thread start of `Run.ship`: start each open version's thread first, then walk `sorted(takeable - cut_held)`. While `room` holds, `unwait` a cut with its entry and start its thread; hand each other cut to `wait_cut`, and remove `self.waiting` from `self.seen` after ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_of_one or three_versions"` passes.
- [ ] 2.8 In `tests/test_conduct.py` add `test_cap_close_starts_no_run_for_a_waiting_cut`: `handled()` holds `seen` joined with `waiting` and is `None` when `seen` is; through `run()`, with `Run.ship` stubbed and `_start_run` recorded as its neighbours do, a cut left waiting starts no next run and a queued cut the run never read starts one.
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_close"` lists `test_cap_close_starts_no_run_for_a_waiting_cut`.
- [ ] 2.9 In `skills/mf-ship/scripts/conduct.py` add `Run.handled()`, which returns `self.seen` joined with the waiting cuts and is `None` when `seen` is, and make `run()` give `_close` its value in place of `conductor.seen` ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_close"` passes.

## 3 — What is shown

- [ ] 3.1 In `tests/test_conduct.py` add `test_cap_writes_the_reason_into_the_entry`: a waiting cut's entry holds `waits` as `1 in flight, cap 1`, rewritten when the count changes, none for a halted entry and none for a vanished one; `unwait` with an entry that holds `waits` clears it, and writes nothing for an entry that holds none or has gone ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_writes"` lists `test_cap_writes_the_reason_into_the_entry`.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py` make `Run.wait_cut` and `Run.unwait` write and clear the entry's `waits` under `_queue_lock`, with `_write_cut`, as [D5](design.md#d5) says; a run with no cap takes no lock.
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_writes"` passes.
- [ ] 3.3 In `tests/test_conduct.py` add `test_cap_status_and_cut_line`: `status` prints `<id> · cut — waits: 1 in flight, cap 1` for an entry holding `waits`, `<id> · cut` for one without; `cut()` appends ` · cap 2` to its line under `in_flight = 2`, and exits 2 under a bad file with nothing reserved.
  Verify: `uv run pytest tests/test_conduct.py --collect-only -q -k "cap_status"` lists `test_cap_status_and_cut_line`.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` make `status` print the waiting line, and `cut()` call `_cap()` before it takes the queue lock and append ` · cap <N>` to the line it prints for a live run and for a started run, when a cap is set ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_conduct.py -q -k "cap_reads or cap_file or cap_counts or cap_gates or cap_of_one or cap_close or cap_writes or cap_status or three_versions"` passes.
- [ ] 3.5 In `tests/test_viewer.py` give the `_queue` helper a `waits` mapping, add `test_the_queue_shows_a_waiting_cut_as_queued` for the state `queued` with its reason, and change the queue rows `test_for_you_holds_what_needs_a_person` expects to carry `"waits": None`.
  Verify: `uv run pytest tests/test_viewer.py --collect-only -q -k "queue_shows"` lists `test_the_queue_shows_a_waiting_cut_as_queued`.
- [ ] 3.6 In `skills/mf-ui/scripts/viewer.py` give each queue row a `waits` field and the state `queued` when the entry holds `waits` and no halt; in `skills/mf-ui/page/index.html` print `cut.waits` after the halt and add a style for the state.
  Verify: `uv run pytest tests/test_viewer.py -q -k "queue_shows or for_you"` passes.

## 4 — The record

- [ ] 4.1 In `docs/decisions.md` amend D47: where it says a run takes each queued cut at its start and each poll, add that it does so up to the cap of D84 ([D6](design.md#d6)), and that its close starts no run for a cut that only waits.
  Verify: `git grep -n "D84" -- docs/decisions.md` prints a line of D47's section.
- [ ] 4.2 In `docs/decisions.md` add `### D84 · A queued cut waits while the line is at its cap` after D72, in the form of its neighbours: the setting `in_flight` in `ship.toml`, what counts as in flight, the exceptions, a *Why*, *Rejected* and *Accepts* list; add `D84` to the *Repo conventions* line of the index at the top.
  Verify: `git grep -n "^### D84 " -- docs/decisions.md` prints a line.
- [ ] 4.3 In `skills/mf-ship/SKILL.md` edit the flow line of each queued cut to wait for a slot under the cap first, the `status` row to print `<change-id> · cut — waits: <n> in flight, cap <N>`, the `cut` row to name the cap in its lines, and the `run` row to name `in_flight` under `[queue]` in `ship.toml`.
  Verify: `git grep -n "in_flight" -- skills/mf-ship/SKILL.md` prints a line of the `run` row.
- [ ] 4.4 In `skills/mf-plan/SKILL.md` change the close's `Next:` line for a queued hard brief to say the run cuts it when a slot frees under the cap, and `conduct.py status` says where it stands.
  Verify: `git grep -n "slot frees" -- skills/mf-plan/SKILL.md` prints a line.
