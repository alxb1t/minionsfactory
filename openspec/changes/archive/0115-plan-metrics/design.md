# Plan metrics — design

`review_metrics.py` reads the person's session transcripts into the stations `plan` and `operator`, with the numbers and markers of the transcript alone. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`review_metrics.py` books a station from a spawn log: `_cost_logs` reads each `<stamp>-<station>[-n].log`, `_spent` its last `result`, and `_stations` turns a change's record into a row per station for `review-metrics.json` (`skills/mf-review-metrics/scripts/review_metrics.py:744-819`, `:1029`). See [proposal](proposal.md) for what the page lacks.

An interactive session leaves `<session>.jsonl` in a Claude Code project folder. Each assistant line holds `message.id`, `message.model` and `message.usage`; the lines of one message share an id and a usage, so a message is counted once.

Its subagents sit in `<session>/subagents/agent-<id>.jsonl`, each beside an `agent-<id>.meta.json` that names the launching `toolUseId`. A run's own spawns write transcripts too, so booking every transcript as operator work would count a station twice.

The seams that exist: `settings()` and `_read_config` for the config, `_usage` and `_priced_worker` for the price of a usage, `_station_logs` for a change's logs, `_changes` for a repo's changes, `_utc` for a run-log clock time, `_stations`, `cost_table`, `render_page` and `main` for the output (`review_metrics.py:185`, `:820`, `:938`, `:773`, `:1145`, `:422`).

```
config sessions[]            run logs + station logs
      │                              │
      ▼                              ▼
 _transcript ──▶ calls, messages ──▶ _spans ──▶ plan rows (bound, split, unbooked)
 (numbers, ids)        │                │
                       └─ _operator ◀── marks ──▶ operator rows (by version, else unbooked)
```

## Goals / Non-Goals

**Goals:** the person's planning and hand work on the page and in the data, per change; a reader that keeps no word of a transcript; a run's own spawn counted once.

**Non-Goals:** Codex sessions of the person; a reading of any text a transcript holds beyond [D2](#d2)'s list; a recommendation; a write into any repo, per [D50](../../../docs/decisions.md#d50--review-metrics-are-read-across-repos-and-drawn-on-one-page).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the config's `sessions` key names the transcript folders; none listed, none read | config in the file, nothing implicit; Q1 | every folder of `~/.claude/projects`; a flag |
| [D2](#d2) | the reader keeps numbers, ids, times and booleans, and reads only a session holding an `mf-*` marker | the person's text and `Personal/` stay unread; Q6 | reading text to classify a message |
| [D3](#d3) | a message is priced once by its id, by `prices.toml`; a turn is a message with a token | the lines of one message share a usage; a cut worker's transcript then equals its `result` to the token | summing every line |
| [D4](#d4) | a session a station log's `init` names is skipped with its subagents | no double count; Q5 | booking it as operator work |
| [D5](#d5) | a plan span opens at an `mf-plan` call with `brief=` and closes at the last write of the brief; a `from=` joins the chains | planning apart from running the line; Q2, Q3 | a span to the end of the session |
| [D6](#d6) | a span is bound to the valid ids a matched `conduct.py cut` queued, split equally, else `unbooked` | a pasted line forges nothing; Q3, Q7 | binding by the brief's text; a weighted split |
| [D7](#d7) | the rest is `operator`, booked to the version the nearest earlier mark names; a subagent at its launching call's time | Q4 | booking by working directory |
| [D8](#d8) | the rows are `stations` rows and columns of the cost table; the rows with no change are a table of their own | one place for a version's cost | a second file |
| [D9](#d9) | `docs/decisions.md` edits D50, `docs/principles.md` its exemption and the skill its text | A7: a decision in force is edited where it lives | a new decision |
| [D10](#d10) | the person's ledger of cost per version is outside this repository | the repo reaches nothing outside itself | a task that writes it |

### D1

`session_folders(config)` returns the folders of the config's `sessions` list, each resolved against the config's folder and `~`-expanded as `out` is, from the file `config` names or `config_path()`. A `sessions` that is no list of strings raises `CannotRun`, as `repos` does.

No file, or no key, is an empty list: `main` then books nothing and reads no log or transcript for this change. `--repo` does not change it. The sessions of a folder are the `<id>.jsonl` files directly in it.

### D2

`_transcript(path)` returns the session's reduced events in file order, and `[]` for a session with no marker. It parses each line and keeps, never the line:

| event | fields | from |
|---|---|---|
| `message` | `id`, `time`, `model`, `usage` | an assistant line's `message.id`, `timestamp`, `message.model`, `message.usage` through `_usage`; the first line of an id |
| `call` | `id`, `time`, `mf`, `conduct`, `plan`, `cut`, `brief`, `origin`, `touched` | a `tool_use` block: its id, the time of the first line of its message, whether `Skill`'s `input.skill` starts `mf-` or `Bash`'s command names `conduct.py`, whether the skill is `mf-plan`, whether the command matches `conduct.py … cut`, the `brief=` and `from=` tokens of `Skill`'s `args` or of the `cut` command, and the `file_path` of `Write` or `Edit` |
| `result` | `call`, `ids` | a `tool_result` block: its `tool_use_id`, and the ids its lines `cut: queued <id>` name |

A **marker** is a `call` with `mf` or `conduct`. The `brief`, `origin` and `touched` paths are compared in memory after `os.path.normpath` of their `~`-expanded text, and are never written: the output holds ids, numbers and times only. The `file_path` of a `Write` or `Edit` is outside Q6's list; Q2 closes a span at the write of the brief, so it is read for that comparison alone and dropped (cutter's `C1` in the brief).

A session's subagents are read only for a session that has a marker: `_subagents(folder, id)` returns, for each `agent-<n>.meta.json`, `{"launch": <its toolUseId>, "messages": [...]}`, the `message` events of the `agent-<n>.jsonl` beside it, reduced the same way and with no marker test. `_sessions(folders, skipped)` returns `{"id", "events", "subagents"}` for each `<id>.jsonl` of the folders whose id is not in `skipped` and whose `_transcript` is not empty.

### D3

`_spend(messages)` takes the `message` events of one bucket and returns `dollars`, `turns`, `tokens`: one `message` per `id`, a message with no token skipped as no turn, `turns` the number kept, `tokens` the sum of every usage value as a worker's are, `dollars` the sum of each message through `_priced_worker(_prices().get(model), usage)` and `None` when any message has no price row, as `_total` makes it. A bucket with no message books no row. The row's `first` is `None`.

### D4

`_station_sessions(repos)` returns the `session_id` of the `init` event, `"subtype":"init"`, found in the first 5 lines of every station log of every repo read: `.minions/changes/*/logs/*.log` and `.minions/runs/*/*.log`, both always read. A transcript whose id is in the set is not read, nor its subagents.

### D5

The **chains** are the groups of `brief` and `origin` paths that `mf-plan` calls tie together: a call with `from=F` and `brief=B` puts `F` and `B` in one chain, whatever the session. `_chains(sessions)` returns a dict from each normalized path to its chain's number.

A **span** is a chain's calls in one session: it opens at the first `mf-plan` call of the chain in that session and closes at the last `touched` event of any path of the chain at or after the opening, else at the opening. Both ends are inclusive, and a `call`'s time is its message's, so the opening message is in. 

A message belongs to a span when its time is between the two, the span opened latest when two hold it; a subagent's message has the time of its launching call ([D7](#d7)). A message in no span is `operator`.

`_spans(sessions)` returns each span as `{"session", "chain", "open", "close", "messages"}`, `chain` the number `_chains` gives, `messages` the session's own and its subagents' that belong to it. `seconds` of a plan row is the sum of its spans' `(close - open).total_seconds()`, rounded; of an operator row, a gap (cutter's `C3`).

### D6

The ids a chain queued are the `result` events whose `call` is a `cut` call whose `brief` is a path of the chain, each id checked by `_cut_made(repos, id, time)`: a repo read holds a folder `.minions/changes/<id>/`, and a cut log of the change — `_station_logs(repo, id, "cut")` — has a modification time not before the call's time. The first repo that holds both gives the row's `repo`, its `repo.name` as `_stations` writes it.

`_queued(repos, sessions)` returns `{"chain", "id", "repo", "time"}` for each valid id, `chain` the number `_chains` gives the call's `brief`. The id of a result of any other call, or one that fails the check, binds nothing.

A chain with no valid id books its spans as `unbooked`: the rows have `repo` and `change` `None`. With several ids, each takes an equal share of dollars, turns, tokens and seconds, unrounded, a gap staying a gap: five turns over two ids are 2.5 each.

### D7

A **mark** is a time and a change: the call time of a valid queue line, and each line `HH:MM:SS · <change> · <event>` of a repo's `.minions/runs/<stamp>.md` whose second field is a change id, `\d{4}-[a-z0-9-]+`, never `run`.

A mark's date is the stamp's; going forward through the file, a clock time more than `HALF_DAY` before the line above it adds a day, and `_utc` makes it UTC. A line whose event is `removed`, the version's worktree removed after it landed, is a mark with no change: it closes the version. An operator message books to the change of the latest mark not after its time, `unbooked` when that mark closes or none is earlier; the cutter reads the open version as that mark (cutter's `C2` in the brief). A subagent's messages take the time of the launching `call`, with that call's span or mark; one whose launch is no event of the session books nowhere.

`_marks(repos, queued)` returns the marks sorted by time. `_operator(sessions, spans, marks)` skips every message that belongs to a span, and returns one row per repo and change, and one `unbooked`; a station's session and a session with no marker are never among `sessions`.

### D8

`booked(repos, folders)` returns the rows, each `{"repo", "change", "station", "dollars", "turns", "tokens", "seconds", "first"}` as `_stations` does, `station` `plan` or `operator`. `main` computes `booked` once, before the page is written, when `folders` is not empty; it passes it to `render_page` and appends it to `stations`.

`render_page(read, chart, style, booked=())` passes it to `_repo_section(name, records, chart, booked=())`, which passes the rows whose `repo` is its `name` to `cost_table(records, booked=())`. The table adds a `plan` and an `operator` column after the stations only when `booked` holds a row, each cell `$<dollars> · <turns> turns · <tokens> tokens · <seconds> s` as `_cost_cell` writes a station's, a gap `—`, by a helper that reads a row's own keys. `render_page` adds a table `unbooked` of the rows with no change.

### D9

`docs/decisions.md` D50 names the transcripts of the folders the config's `sessions` key lists among what the station reads, and its `plan` and `operator` stations among what it writes; `docs/principles.md` names them in the exemption of *The repo reaches nothing outside itself*; `skills/mf-review-metrics/SKILL.md` names the key, the stations and the reads. No decision id is added: the choice extends how D50 reads, and the requirement in `openspec/specs/sdd/spec.md` carries the rest, folded at release.

### D10

The person's ledger — the by-hand table of cost per version the brief measured against — takes `plan` and `operator` columns from the page's data, by the person's hand. No task writes it: the ledger is outside this repository.

## Tests

All new tests are unit tests at the lowest layer ([T1](../../../skills/mf-cut-change/SKILL.md#rules-for-tests)), in `tests/test_review_metrics.py`, with synthetic transcripts written under `tmp_path`; no real session is read. No end-to-end test is added, and none is deleted or merged.

| file | added | by |
|---|---|---|
| `tests/test_review_metrics.py` | `test_the_sessions_key_names_the_folders` | [D1](#d1) |
| `tests/test_review_metrics.py` | `test_a_transcript_is_reduced_to_numbers_and_ids`, `test_a_session_with_no_marker_is_not_read`, `test_a_subagent_is_read_with_its_launching_call`, `test_a_secret_in_a_transcript_is_never_written` | [D2](#d2) |
| `tests/test_review_metrics.py` | `test_a_message_is_priced_once_by_its_id` | [D3](#d3) |
| `tests/test_review_metrics.py` | `test_a_station_session_is_skipped` | [D4](#d4) |
| `tests/test_review_metrics.py` | `test_a_plan_span_runs_from_the_skill_to_the_last_write`, `test_a_continuation_joins_the_plan` | [D5](#d5) |
| `tests/test_review_metrics.py` | `test_a_span_is_bound_to_the_ids_a_cut_queued`, `test_a_span_that_queued_two_versions_is_split_equally`, `test_a_forged_queue_line_binds_nothing`, `test_a_plan_never_queued_is_unbooked` | [D6](#d6) |
| `tests/test_review_metrics.py` | `test_operator_work_is_booked_to_the_nearest_mark`, `test_a_subagent_books_where_its_call_was_launched` | [D7](#d7) |
| `tests/test_review_metrics.py` | `test_the_plan_and_operator_rows_reach_the_data_and_the_page` | [D8](#d8) |

The change turns no existing test red: `cost_table`, `render_page` and `main` keep their calls, and the added column appears only when a row is booked. `scripts/corpus.toml`'s `review-metrics` case runs with a config that has no `sessions` key, so it reads no transcript.

## Dependencies

None.

## Risks / Trade-offs

- A `brief=` written relative, or through a link, compares unequal to the path a `conduct.py cut` call names: the span is `unbooked`. The comparison is of normalized text, never of the file system; the span shows on the page as unbooked, a gap and no wrong figure.
- The run log's clock time is local, a stamp's date and a midnight crossing infer the day: an operator message near a mark can book to a neighbour. The page is a ranking, not a bill, as the skill says.
- Operator work is every message outside a span, including the person's chat that is no work on a version: it books to the nearest earlier mark, or `unbooked`. The number is an upper bound of hand work on that version.
- A model with no row in `prices.toml` makes a bucket's dollars a gap, never a zero; its tokens and turns stand.
- The `make corpus` case does not read a transcript. The person runs the script by hand over their own folders to see it on real data.

## Verdict

Ready: every file the phases edit exists at `HEAD`, every behaviour is a function with a seam in `tests/test_review_metrics.py`, and no decision of the brief is left open. The cutter's `C1`, `C2` and `C3` in the brief's `## Decisions` fix what the brief's Q2, Q4 and Q6 leave to a reading.
