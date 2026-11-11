# ui · state — tasks

The phases: the projector, the server, the page, the record, and a person's check against a live run.

## Progress

- [x] 1 — The projector · hard
- [x] 2 — The server · hard
- [ ] 3 — The page · moderate
- [ ] 4 — The record · moderate
- [ ] 5 — The live check **HUMAN**

## 1 — The projector

`viewer.py project <primary>` prints a project's tree; every sub-task adds its own tests to `tests/test_viewer.py`.

- [x] 1.1 **HALT CHECK** The readers the projector calls stand: `stage_of`, `open_versions`, `_progress`, `_cuts`, `_claim`, `_bounded` and `_run_end` in `conduct.py`; `CAP` and `FALLBACK` in `converge.py`.
  Verify: `git grep -n -e '^def stage_of' -e '^def open_versions' -e '^def _progress' -e '^def _cuts' -e '^def _claim' -e '^def _bounded' -e '^def _run_end' -e '^CAP = ' -e '^FALLBACK = ' -- skills/mf-ship/scripts/conduct.py skills/mf-converge/scripts/converge.py` prints each line.
- [x] 1.2 Create `skills/mf-ui/scripts/viewer.py`: header, `load`, `read_part`, and `main` with its usage exit 2 ([D1](design.md#d1), [D2](design.md#d2)).
  Add `tests/test_viewer.py` with `_primary` and `_version` helpers and `test_read_part_reads_a_regular_file_only`.
  Verify: `uv run pytest tests/test_viewer.py -k read_part -q` exits 0.
- [x] 1.3 `project <primary>` prints the tree of [D3](design.md#d3), every list empty.
  Add `test_main_dispatches_its_commands`.
  Verify: `uv run pytest tests/test_viewer.py -k main_dispatches -q` exits 0.
- [x] 1.4 List `open_versions` with each version's `phases` as [D5](design.md#d5) says, ticks from the worktree's `tasks.md`.
  Add `test_a_version_shows_its_phases_with_the_trees_ticks`.
  Verify: `uv run pytest tests/test_viewer.py -k phases_with_the_trees_ticks -q` exits 0.
- [x] 1.5 Fill `workers` from the newest run log and the `run` line from the claim, per [D5](design.md#d5).
  Add `test_workers_are_the_unfinished_spawns`.
  Verify: `uv run pytest tests/test_viewer.py -k unfinished_spawns -q` exits 0.
- [x] 1.6 Give each version its `stage`, `why` and `state` by the table of [D4](design.md#d4); a version whose read raises is `unread` alone.
  Add `test_the_projector_gives_each_state_its_why` and `test_a_version_that_raises_is_unread_alone`.
  Verify: `uv run pytest tests/test_viewer.py -k "each_state_its_why or raises_is_unread" -q` exits 0.
- [x] 1.7 Fill `converge` from the status log, `conformance.md`, `adversarial.md` and `CAP`, per [D5](design.md#d5).
  Add `test_converge_shows_its_round_cap_blockers_and_each_role`.
  Verify: `uv run pytest tests/test_viewer.py -k round_cap_blockers -q` exits 0.
- [x] 1.8 Fill `liveness` for each version with a worker, per [D5](design.md#d5).
  Add `test_liveness_is_active_then_quiet`.
  Verify: `uv run pytest tests/test_viewer.py -k active_then_quiet -q` exits 0.
- [x] 1.9 Fill `for_you`, the `notes` and the `queue` from `_cuts`, per [D4](design.md#d4).
  Add `test_for_you_holds_what_needs_a_person`.
  Verify: `uv run pytest tests/test_viewer.py -k for_you_holds -q` exits 0.
- [x] 1.10 Add `project --only liveness` and `--only fingerprint`, per [D7](design.md#d7).
  Add `test_the_only_options_print_liveness_and_the_fingerprint` and `test_the_projector_writes_nothing`.
  Verify: `uv run pytest tests/test_viewer.py -k "only_options or writes_nothing" -q` exits 0.
- [x] 1.11 Read the claim once per project, a `Stop` from it the claim `unread` ([D5](design.md#d5)); add the case `viewer` to `scripts/corpus.toml` ([D11](design.md#d11)), then run the readers over this checkout's run directory.
  Add `test_a_claim_ps_cannot_read_is_unread`.
  Verify: `make corpus` prints `corpus: viewer · 1 runs · pass`.

## 2 — The server

`viewer.py` gains the projects, the child read, the frame, the routes, the poll and the commands; no test opens a socket.

- [x] 2.1 Add `read_config` and `projects` for [D6](design.md#d6): the record, `ui.toml`, exit 2 on a bad file.
  Add `test_the_projects_come_from_the_record_and_the_config` and `test_a_bad_config_exits_2_naming_it`.
  Verify: `uv run pytest tests/test_viewer.py -k "from_the_record or bad_config" -q` exits 0.
- [x] 2.2 Add `read_project(primary, only, bound)`: the child, its environment and its kill, per [D2](design.md#d2).
  Add `test_a_project_read_past_its_bound_is_killed`, a pipe at the claim's `pid`, the bound 1 s.
  Verify: `uv run pytest tests/test_viewer.py -k read_past_its_bound -q` exits 0.
- [x] 2.3 Add `State.publish`, `State.latest` and `frame`, per [D7](design.md#d7).
  Add `test_a_frame_numbers_the_whole_state`.
  Verify: `uv run pytest tests/test_viewer.py -k numbers_the_whole_state -q` exits 0.
- [x] 2.4 Add `route` and the stream generator, with the `Host` check and the headers of [D7](design.md#d7).
  Add `test_the_routes_answer_and_refuse` and `test_the_stream_sends_each_new_state_once`.
  Verify: `uv run pytest tests/test_viewer.py -k "routes_answer or stream_sends" -q` exits 0.
- [x] 2.5 Add `tick`: the fingerprint, the 10 s re-read and the 5 s liveness, per [D7](design.md#d7).
  Add `test_a_tick_reads_on_a_change_and_on_time`, with a fake `read`.
  Verify: `uv run pytest tests/test_viewer.py -k reads_on_a_change -q` exits 0.
- [x] 2.6 Add `serve` and the handler's `do_GET`, each `# pragma: no cover`: bind `127.0.0.1`, the poll thread, `route` ([D7](design.md#d7)).
  Mark no other line; `serve` and `do_GET` are the only lines nothing can reach without a socket.
  Verify: `grep -c 'pragma: no cover' skills/mf-ui/scripts/viewer.py` prints `2`.
- [x] 2.7 Add `start`, `stop` and `serves`, and wire `serve`, `start` and `stop` into `main`, per [D8](design.md#d8).
  Add `test_start_finds_and_stop_removes_the_pid_file`, `test_stop_signals_only_the_servers_pid` and `test_main_runs_serve_start_and_stop`.
  Verify: `uv run pytest tests/test_viewer.py -k "stop_removes or signals_only or runs_serve" -q` exits 0.

## 3 — The page

- [ ] 3.1 Write `skills/mf-ui/page/index.html` as [D9](design.md#d9) says: tokens, one column, `EventSource`, text nodes only.
  Verify: `grep -c 'new EventSource("/events")' skills/mf-ui/page/index.html` prints `1`.
- [ ] 3.2 Add `test_the_page_sets_text_only`: no file under `skills/mf-ui/` holds a markup sink named in [D9](design.md#d9).
  Verify: `uv run pytest tests/test_viewer.py -k page_sets_text -q` exits 0.

## 4 — The record

- [ ] 4.1 Write `skills/mf-ui/SKILL.md`: the role OPERATOR, `/mf-ui` and `/mf-ui stop`, the state folder, `ui.toml`, `scripts/viewer.py`.
  Verify: `grep -n 'scripts/viewer.py' skills/mf-ui/SKILL.md` prints a line.
- [ ] 4.2 Add D81 to `docs/decisions.md` beside D50 and to its index lines, with the text of [D10](design.md#d10).
  Verify: `grep -c '^### D81 · ' docs/decisions.md` prints `1`.
- [ ] 4.3 Add the viewer's bullet to *The repo reaches nothing outside itself* in `docs/principles.md`, linking D81.
  Verify: `grep -n 'decisions.md#d81' docs/principles.md` prints a line.
- [ ] 4.4 Add the viewer's *Trust boundaries* bullet to `THREAT_MODEL.md`, as [D10](design.md#d10) says.
  Verify: `grep -n 'The viewer' THREAT_MODEL.md` prints a line.
- [ ] 4.5 Name `mf-ui` in `README.md`'s skill table, in `AGENTS.md`'s layout entry for `skills/` and in `docs/README.md`'s `skills/` row.
  Verify: `grep -l 'mf-ui' README.md AGENTS.md docs/README.md` prints each file name.

## 5 — The live check

The person runs these in their own terminal, in the primary, while a run is live; the files they write are the evidence.

- [ ] 5.1 Start the viewer: `uv run --script skills/mf-ui/scripts/viewer.py start > openspec/changes/0120-ui-state/live-url.txt`.
  Verify: `grep -n '^http://127.0.0.1:' openspec/changes/0120-ui-state/live-url.txt` prints a line.
- [ ] 5.2 Save each `<id> · <stage>` line: `uv run --script skills/mf-ship/scripts/conduct.py status > openspec/changes/0120-ui-state/live-status.txt`.
  Verify: `grep -n ' · ' openspec/changes/0120-ui-state/live-status.txt` prints a line per version.
- [ ] 5.3 Save each version's `"stage"`, the port being the one in `live-url.txt`: `curl -s http://127.0.0.1:8737/state > openspec/changes/0120-ui-state/live-state.json`.
  Verify: `grep -n '"stage"' openspec/changes/0120-ui-state/live-state.json` prints a line per version.
- [ ] 5.4 Open the URL in a browser; write `openspec/changes/0120-ui-state/live-check.md`, a line `<id> · <stage> · matches` per version whose stage on the page equals its line in `live-status.txt`.
  Verify: `grep -n ' · matches$' openspec/changes/0120-ui-state/live-check.md` prints a line per version.
- [ ] 5.5 Stop it, as [D8](design.md#d8) says: `uv run --script skills/mf-ui/scripts/viewer.py stop > openspec/changes/0120-ui-state/live-stop.txt`.
  Verify: `grep -n 'viewer: stopped' openspec/changes/0120-ui-state/live-stop.txt` prints a line.
