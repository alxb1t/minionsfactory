# Queue cap — design

A run takes a queued cut only while the line has room under a cap the operator sets in `ship.toml`; with no setting it takes every cut at once, as today. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A run takes every queued cut with no halt at its start and at each poll (`Run.ship`, `Run.take_requests`, `Run.take_cut` in `skills/mf-ship/scripts/conduct.py`), and its close starts the next run when a cut was never read (`_close`). Nothing counts versions in flight: the threads are a dict local to `Run.ship`. A queue entry is one JSON file in the operator's home folder, with the keys of `CUT_KEYS` and optional extras (`beside`, `models`).

```
queue ──▶ run start / poll ──▶ room under the cap? ─ yes ─▶ take_cut ─▶ cut thread ─▶ build … release
                                      │ no
                                      └─▶ the cut waits: not seen, entry holds the reason, run stays alive
```

The conductor reads no operator config today. `skills/mf-ui/scripts/viewer.py` (`config_path`, `ui.toml`) and `skills/mf-review-metrics/scripts/review_metrics.py` (`config_path`, `review-metrics.toml`) each read one under `$XDG_CONFIG_HOME/minionsfactory/`.

## Goals / Non-Goals

- **Goals:** the cap is a setting of the machine, read once at a run's start; a waiting cut is shown by `status`, `conduct.py cut` and the viewer; no setting leaves every flow as it is.
- **Non-Goals:** a count across lines or a read of the CPU load; pausing a version; a new meaning for `after:` or `beside:`; a cap on versions already cut at a run's start; any config but the cap.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The cap is `in_flight` under `[queue]` in `ship.toml`, read once by `run()` | it is a fact of the machine, and no worker writes the operator's config folder | `AGENTS.md` switch and `.minions/` parameters ([D58](../../../docs/decisions.md#d58--a-settled-brief-is-cut-by-a-conductor-station) rejects both) · an environment variable |
| [D2](#d2) | In flight is counted by `Run.in_flight`, per repository | the person runs this repo's line and another repo's line on one machine, each at its own cap | a count across lines |
| [D3](#d3) | A cut is taken only while `Run.room` holds, in id order, at the start and at each poll | the order queued is the order run | a new meaning for `after:` |
| [D4](#d4) | A waiting cut is not read, keeps the run alive and starts no next run | the loop would lose or repeat a waiting cut at the start, the poll and the close | marking it read |
| [D5](#d5) | The reason is written into the queue entry; `status`, `conduct.py cut` and the viewer print it | one source for the reason | each reader recomputing the count |
| [D6](#d6) | The record: D47 amended, D84 new, the principles' list gains `ship.toml`, the skills' rows follow | the repo's decisions are edited where they live | a new principle |

### D1

`_cap() -> int | None` in `conduct.py` reads `ship.toml` in `$XDG_CONFIG_HOME/minionsfactory/`, else `~/.config/minionsfactory/`, the same folder as the viewer's and the metrics' configs.

| the file | `_cap` returns or raises |
|---|---|
| missing, or no `[queue]` table, or no `in_flight` key | `None`: no cap |
| `in_flight = 2` | `2` |
| unreadable, not UTF-8, not TOML | `Stop(2, "<path>: <error>")` |
| `0`, `-1`, `1.5`, `"2"`, `true` | `Stop(2, "<path>: `in_flight` is not a whole number above 0")` |

`run()` calls it in its first `try`, after `preconditions`, so `run --detach` refuses before it starts a child, and sets `conductor.cap` once the `Run` is built; `Run.__init__` keeps its parameters and sets `self.cap = None`, so a `Run` built as the tests build it has no cap. `cut()` calls it before it takes the queue lock, to name the cap in its line and refuse a bad file before it reserves an id. [D58](../../../docs/decisions.md#d58--a-settled-brief-is-cut-by-a-conductor-station)'s rejections hold: the setting is in neither `AGENTS.md` nor `.minions/`.

### D2

`Run.in_flight(threads)` returns how many of `threads` are at a station: the thread is alive, `self.stopped(change)` is false, and every `after` id of the change is shipped (`_shipped(primary, default, name)`).

The ids are the queue entry's `after` while the change is still a queued cut, else `_dependencies(primary, change)`. So a halted version, and a version or cut waiting on its `after`, uses no slot, and one halt at night does not stop the queue behind it.

A rejoin or grant starts a thread past `room`, so the count may pass the cap; `room` then refuses until it falls.

### D3

`Run.room(threads)` is `self.cap is None or self.in_flight(threads) < self.cap`. `Run.ship` starts the open versions' threads first, then each takeable cut in id order while `room` holds; the rest go to `Run.wait_cut`. `Run.take_requests` calls `room` before `take_cut` for each unread cut, unless a request names it; a rejoin's `take_back` and a version already cut at the start run past it. With `cap` `None`, `room` is true before it reads anything.

An open version never names a queued cut in `after`: a queued cut's id is above every open version's (`_next_id`), and an `after` id is lower than its own. So a cut that waits leaves no version without its dependency's thread.

### D4

`Run.waiting` maps each waiting cut to its reason. A waiting cut stays out of `self.seen`, so the next poll tries it again: `Run.ship` removes the waiting cuts from the `seen` it marked. `Run.join` needs no change, since a live version thread keeps its loop, and the thread's end frees the slot the next `take_requests` reads. `run()` gives `_close` `seen` joined with the waiting cuts, so the close starts a next run for a cut queued after the last poll and for none that only waited, which a halted run can leave. [D47](../../../docs/decisions.md#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended)'s "a cut it never read" stands for every other cut.

### D5

`Run.wait_cut(change, threads)` sets `self.waiting[change]` to `"<n> in flight, cap <N>"`, logs one `wait` event the first time, and rewrites the entry as `{**entry, "waits": reason}` under `_queue_lock` when the reason changed, only while the entry exists with no halt. The event takes the subject `run`, as `report` counts every other subject as a touched change: `run · wait — <id>: <reason>`.

`Run.unwait(change, entry)` drops the key from `self.waiting`, and, when `entry` holds `waits`, drops it from the entry under the lock while the entry exists. `Run.take_cut` passes its `entry` and `Run.ship` passes `cuts[change]`, so a run with no cap takes no lock and writes no entry. `status` prints `<id> · cut — waits: <reason>` for a halt-free entry holding `waits`, and `conduct.py cut` appends ` · cap <N>` to its line when `_cap` returns a number. The viewer's queue row takes the state `queued` for such an entry, with a `waits` field the page prints. A run killed while a cut waits leaves its reason in the entry until the next run's start rewrites or clears it.

### D6

[D47](../../../docs/decisions.md#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended) says every open version builds in parallel and a run takes each queued cut at its start and each poll; it gains "up to the cap for the queue".

A new decision, D84, states the cap, its count and its place in the operator's config folder. It takes the next number, after D83, in the group *Repo conventions*.

The closed list of [the principles](../../../docs/principles.md) gains the file, read-only, named in no repo. `mf-ship`'s flow, `status` and `cut` rows, and `mf-plan`'s close, say the run cuts the item when a slot frees. The spec changes are in [the delta](specs/sdd/spec.md).

## Tests

The cap's logic is tested at the lowest layer that can fail: `_cap` and `Run.in_flight` by direct calls on a `Run` with threads held on an event, `Run.take_requests` with `take_cut` stubbed, the viewer by its projector. A run end to end, with the `fake` worker, holds only what the units cannot: the order of the cuts under a cap. The close is tested through `run()` with `Run.ship` stubbed, as its neighbours are.

| test | file | layer | holds |
|---|---|---|---|
| `test_cap_reads_ship_toml` | `tests/test_conduct.py` | unit | no file, no key, a number, each bad value |
| `test_cap_file_that_is_bad_stops_the_run` | `tests/test_conduct.py` | integration | `run` exits 2 naming the file |
| `test_cap_counts_only_versions_at_a_station` | `tests/test_conduct.py` | unit | a halted version and one waiting on its `after` use no slot |
| `test_cap_gates_the_poll_and_not_a_request` | `tests/test_conduct.py` | unit | a cut waits, is not read, is taken when room returns; a request-named cut is taken |
| `test_cap_writes_the_reason_into_the_entry` | `tests/test_conduct.py` | unit | the entry holds `waits`, one `wait` line, cleared when taken |
| `test_cap_of_one_runs_the_cuts_one_at_a_time` | `tests/test_conduct.py` | end to end | the second cut is cut after the first's release, with a `wait` line for it, logged once |
| `test_cap_close_starts_no_run_for_a_waiting_cut` | `tests/test_conduct.py` | integration | `handled()` holds a waiting cut; `run()`'s close starts no run for it, and one for a cut it never read |
| `test_cap_status_and_cut_line` | `tests/test_conduct.py` | integration | `status` and `conduct.py cut` print the reason and the cap |
| `test_the_queue_shows_a_waiting_cut_as_queued` | `tests/test_viewer.py` | unit | the state `queued` and its reason |

- **Changed:** `test_for_you_holds_what_needs_a_person` in `tests/test_viewer.py` expects the queue rows with the `waits` field.
- **Held as it stands:** `test_three_versions_cut_built_converged_and_closed_at_once` runs with no file and must pass unchanged.
- **End to end:** the one test above is the only new run; no engine matrix applies, the worker is the `fake`. T2: `test_a_queued_cut_is_cut_then_built` reaches no state with a cap file, and a step there would leave the file standing for its later steps (T3).
- **Removed:** none, so no table of merged tests.

## Dependencies

None.

## Risks / Trade-offs

- A version stacked on its dependency builds with the CPU yet uses no slot: its `after` is not shipped. `after:` is the dependency's to hold, not the cap's.
- The cap is read once at a run's start; a change of the file takes effect at the next run.
- A killed run leaves a stale reason in an entry until the next run's start.
- The living spec holds `in_flight` only after the release folds the delta; the brief's grep on `openspec/specs/sdd/spec.md` is a release-time check.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the setting, the gate, what is shown, the record.
