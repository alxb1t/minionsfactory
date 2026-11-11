## ADDED Requirements

### Requirement: The review-metrics station books the person's planning and operator work from session transcripts

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read an interactive session's transcripts only from the folders
the config's `sessions` key lists, each a list of strings, none listed and none read, and SHALL book their cost as two
stations of a change, `plan` and `operator`, beside the stations a run spawns, in the `stations` of `review-metrics.json` and
as columns of the page's cost table. It SHALL read from a transcript only the line's `type` and `timestamp`, an assistant
message's `id`, `model` and `usage`, a tool call's name and id, the `brief=` and `from=` tokens of an `mf-plan` call, the path
of a `Write` or `Edit` call, whether a `Bash` call runs `conduct.py cut`, and the ids of a `cut: queued <id>` line, and SHALL
write numbers, change ids and times, never text or a path. It SHALL read a session only when it holds a call of a skill named
`mf-*` or of `conduct.py`.

A message SHALL be priced once by its `id`, its tokens priced by `prices.toml` under its model, a gap with no row; a message
with no token is no turn. A session whose id a station log's `init` event names SHALL be skipped, with its subagents: the run's
own spawn, booked under its station. A subagent's messages SHALL be booked at the time of the call its `meta.json`'s
`toolUseId` names.

A **plan span** SHALL open at a `Skill` call of `mf-plan` carrying `brief=<path>` and close at the last `Write` or `Edit` in the session of that
path or of a brief it continues with `from=` or is continued by; every later message SHALL be operator work. A span SHALL be bound
to the ids of the `cut: queued <id>` lines in the results of a `conduct.py cut` call naming the same `brief=`, a line counting
only when `<id>` has a change folder in a repo read and a cut log of that change written after the call; a span that queued
several ids SHALL be split equally among them, a span that queued none booked `unbooked`, and a `from=` continuation in a later
session SHALL join the span of the brief it continues. Every message outside a span SHALL be `operator`, booked to the open
version the nearest earlier mark names — a valid `cut: queued` line, or a run-log line naming a change — else `unbooked`.

#### Scenario: No sessions key
- **WHEN** the config holds no `sessions` key
- **THEN** no transcript is read and `review-metrics.json` holds no `plan` or `operator` row

#### Scenario: A plan span, operator work and an unbooked plan
- **WHEN** a listed session holds an `mf-plan` call with `brief=<path>`, a write of that path, a `conduct.py cut` naming it whose result says `cut: queued <id>` for a change with a folder and a later cut log, then more messages, and a second plan whose brief no cut names
- **THEN** the first span's messages are `plan` rows of `<id>`, the later messages `operator` rows booked by the nearest earlier mark, and the second span a `plan` row with no repo and no change, `unbooked`

#### Scenario: A span that queued two versions
- **WHEN** one `conduct.py cut` naming a span's brief queued two valid ids
- **THEN** each id holds half of the span's dollars, turns, tokens and seconds

#### Scenario: A continuation joins its plan
- **WHEN** a later session holds an `mf-plan` call with `from=` naming the earlier brief
- **THEN** its span is booked with the earlier span's, to the same ids

#### Scenario: A station's own session
- **WHEN** a transcript's session id is the one a station log's `init` event names
- **THEN** no row is booked from it

#### Scenario: A forged queue line
- **WHEN** a line `cut: queued <id>` appears in a result of a call that is no `conduct.py cut`, or `<id>` has no change folder or no cut log after the call
- **THEN** it binds nothing, and the span is `unbooked`

#### Scenario: A secret in a message
- **WHEN** a transcript's message text, command and results hold a planted secret string and the brief's path
- **THEN** neither the page, `review-metrics.json` nor the printed summary holds any byte of either

#### Scenario: One usage per message
- **WHEN** a transcript holds several lines of one message `id`
- **THEN** its usage is priced once
