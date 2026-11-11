# Plan metrics — tasks

The phases: the transcript reader, then the spans and their booking, then the rows in the data and the page and the record. Each phase ends green.

## Progress

- [x] 1 — The transcript reader · hard
- [x] 2 — The spans, the binding and the operator booking · hard
- [x] 3 — The rows in the data and the page, and the record · moderate

## 1 — The transcript reader

- [x] 1.1 **HALT CHECK** `review_metrics.py` holds the seams this phase uses ([D1](design.md#d1), [D3](design.md#d3)).
  Verify: `git grep -n -e '^def settings' -e '^def _read_config' -e '^class CannotRun' -e '^def _usage' -e '^def _priced_worker' -e '^def _station_logs' -e '^def _moment' -- skills/mf-review-metrics/scripts/review_metrics.py` prints a line for each.
- [x] 1.2 In `skills/mf-review-metrics/scripts/review_metrics.py` add `session_folders(config)`, as [D1](design.md#d1) says; add `test_the_sessions_key_names_the_folders` to `tests/test_review_metrics.py`: a config with `sessions = ["a", "b"]` gives both folders resolved against the config's folder, no key gives an empty list, and `sessions = "a"` raises `CannotRun`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k sessions_key` exits 0.
- [x] 1.3 In `tests/test_review_metrics.py` add the helpers `_line(kind, time, **message)`, `_turn(id, time, usage, model)` and `_tool(id, time, name, **input)`, which each build one JSON line of a transcript, and `_written(folder, session, *lines)`, which writes `<session>.jsonl`; in `review_metrics.py` add `_transcript(path)` with the `message`, `call` and `result` events of [D2](design.md#d2)'s table; add `test_a_transcript_is_reduced_to_numbers_and_ids`: a `Skill` call of `mf-plan` with `brief=` and `from=`, a `Write` of the brief, a `Bash` of `conduct.py cut` and its result `cut: queued 0001-x` give the matching events, and the planted text of each line is in no event.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k reduced_to_numbers` exits 0.
- [x] 1.4 In `_transcript` return `[]` when no `call` holds a marker ([D2](design.md#d2)); add `test_a_session_with_no_marker_is_not_read` to `tests/test_review_metrics.py`: a session of messages and a `Bash` call of `ls` alone gives `[]`, and the same with a `Skill` call of `mf-plan` gives events.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k no_marker` exits 0.
- [x] 1.5 In `_transcript` keep one `message` event per `id`, the first line's ([D3](design.md#d3)); in `review_metrics.py` add `_spend(messages)`, which returns `dollars`, `turns` and `tokens` as [D3](design.md#d3) says; add `test_a_message_is_priced_once_by_its_id`: the streamed lines of one id price as a single turn, a message with no token is no turn, and a model with no `prices.toml` row gives `dollars` of `None` and its tokens.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k priced_once` exits 0.
- [x] 1.6 In `review_metrics.py` add `_subagents(folder, id)`, as [D2](design.md#d2) says; add `test_a_subagent_is_read_with_its_launching_call` to `tests/test_review_metrics.py`: a `<id>/subagents/agent-a.jsonl` beside `agent-a.meta.json` with a `toolUseId` is read as `{"launch", "messages"}`, and the meta file's other keys are in no event.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k subagent_is_read` exits 0.
- [x] 1.7 **CORPUS** `review-metrics` In `review_metrics.py` add `_station_sessions(repos)` of [D4](design.md#d4) and `_sessions(folders, skipped)` of [D2](design.md#d2); add `test_a_station_session_is_skipped` to `tests/test_review_metrics.py`: a station log of a change whose `init` line names session `s1`, in the moved layout and in the old one, makes `_sessions` skip `s1.jsonl` and its subagents and read `s2.jsonl`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k station_session_is_skipped` exits 0.

## 2 — The spans, the binding and the operator booking

- [x] 2.1 **HALT CHECK** `review_metrics.py` holds the seams this phase uses ([D5](design.md#d5), [D7](design.md#d7)).
  Verify: `git grep -n -e '^HALF_DAY = ' -e '^def _changes' -e '^def _utc' -e '^def _total' -- skills/mf-review-metrics/scripts/review_metrics.py` prints a line for each.
- [x] 2.2 In `review_metrics.py` add `_chains(sessions)`, which groups the `brief` and `origin` paths of the `mf-plan` calls, and `_spans(sessions)` of [D5](design.md#d5); add `test_a_plan_span_runs_from_the_skill_to_the_last_write` to `tests/test_review_metrics.py`: messages before the call, inside, and after the last write of the brief book as outside, inside and outside, a span with no write holds its opening alone, and a subagent launched inside the span joins it.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k skill_to_the_last_write` exits 0.
- [x] 2.3 In `_chains` tie a `from=` path to the `brief=` of its call, across sessions ([D5](design.md#d5)); add `test_a_continuation_joins_the_plan` to `tests/test_review_metrics.py`: a second session's `mf-plan` call with `from=` naming the first brief gives a chain of both briefs and a span in each session.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k continuation_joins` exits 0.
- [x] 2.4 **CORPUS** `review-metrics` In `review_metrics.py` add `_cut_made(repos, id, time)` and `_queued(repos, sessions)` of [D6](design.md#d6), which return the valid ids of each chain with each one's repo and call time; add `test_a_span_is_bound_to_the_ids_a_cut_queued` and `test_a_forged_queue_line_binds_nothing` to `tests/test_review_metrics.py`: a line in the result of a `Bash` call that is no `conduct.py cut`, an id with no change folder, and an id whose cut log is older than the call each bind nothing.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k 'cut_queued or forged_queue'` exits 0.
- [x] 2.5 In `review_metrics.py` add `_plan_rows(spans, queued)`, which books each chain's spans' `_spend` and `seconds` to its ids, each taking an equal share, unrounded, and a chain with no valid id as `unbooked` ([D6](design.md#d6), [D5](design.md#d5)); add `test_a_span_that_queued_two_versions_is_split_equally`, in which five turns book 2.5 to each id, and `test_a_plan_never_queued_is_unbooked` to `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k 'split_equally or never_queued'` exits 0.
- [x] 2.6 **CORPUS** `review-metrics` In `review_metrics.py` add `_marks(repos, queued)` and `_operator(sessions, spans, marks)` of [D7](design.md#d7), which return the `operator` rows; add `test_operator_work_is_booked_to_the_nearest_mark` and `test_a_subagent_books_where_its_call_was_launched` to `tests/test_review_metrics.py`: a run-log line of change `0002-y` before an operator message books it to `0002-y`, a line of `run` books nothing, a later `removed` line leaves the next message `unbooked`, and a subagent launched after a mark books to that mark though it ran later.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k 'nearest_mark or books_where'` exits 0.
- [x] 2.7 In `review_metrics.py` add `booked(repos, folders)`, which returns the `plan` and `operator` rows of [D8](design.md#d8) from `_station_sessions`, `_sessions`, `_spans`, `_queued`, `_plan_rows` and `_operator`, a row with the keys of a `_stations` row; add `test_booked_rows_have_the_keys_of_a_station_row` to `tests/test_review_metrics.py`.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k keys_of_a_station_row` exits 0.

## 3 — The rows in the data and the page, and the record

- [x] 3.1 In `review_metrics.py` make `main` read `session_folders(args.config)` and, when it is not empty, compute `booked(repos, folders)` once before the page is written and add it to `stations` ([D8](design.md#d8)); add `test_the_plan_and_operator_rows_reach_the_data_and_the_page` to `tests/test_review_metrics.py`, whose first half runs `main` over a repo and a transcript folder and finds `plan` and `operator` rows in `review-metrics.json`, and none when the config has no `sessions` key.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k reach_the_data` exits 0.
- [x] 3.2 In `review_metrics.py` give `render_page`, `_repo_section` and `cost_table` the parameter `booked=()` of [D8](design.md#d8), `main` passing it to `render_page`: the `plan` and `operator` columns after the stations, from the rows of the repo's name, when it is not empty, and a table `unbooked` of the rows with no change; extend `test_the_plan_and_operator_rows_reach_the_data_and_the_page` with the page's columns and its `unbooked` table, and the existing cost table, without rows, unchanged.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k reach_the_data` exits 0.
- [x] 3.3 Add `test_a_secret_in_a_transcript_is_never_written` to `tests/test_review_metrics.py`, per the scenario *A secret in a message*: a secret string in a message's text, a command, a result and a skill's `args`, and the brief's path, appear in none of the page, `review-metrics.json` and the printed summary.
  Verify: `uv run pytest -q tests/test_review_metrics.py -k secret_in_a_transcript` exits 0.
- [x] 3.4 In `skills/mf-review-metrics/SKILL.md` name the `sessions` key, the `plan` and `operator` stations and what a transcript is read for, in the description, *Parameters* and the paragraph on the data ([D9](design.md#d9)).
  Verify: `git grep -n -F transcripts -- skills/mf-review-metrics/SKILL.md` prints a line.
- [x] 3.5 In `docs/decisions.md` D50 add the transcripts of the folders the `sessions` key lists to what the station reads, and its `plan` and `operator` stations to what it writes ([D9](design.md#d9)).
  Verify: `git grep -n -F transcripts -- docs/decisions.md` prints a line.
- [x] 3.6 In `docs/principles.md`, in the exemption of *The repo reaches nothing outside itself* for the review-metrics station, add the session transcripts of the folders the config's `sessions` key names, read-only ([D9](design.md#d9)).
  Verify: `git grep -n -F transcripts -- docs/principles.md` prints a line.
