## ADDED Requirements

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — and the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version); converge's rounds, round 1's blockers and the grants; the halts by station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role, the confirmed and refuted cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. The cut's `diff-lines` and `diff-files` SHALL be the collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and review's yield

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

### Requirement: A station keeps a log per spawn

`conduct.py` SHALL write each spawn's worker log to `.minions/runs/<stamp>/<who>_<station>.log`, and a later spawn of the same
station in the same stamp to `<who>_<station>-<n>.log`, `n` from 2, so no spawn's log overwrites another's.

#### Scenario: A converge spawned twice in a run
- **WHEN** a version's converge is spawned, granted a round, and spawned again in the same run
- **THEN** the run directory holds `<id>_converge.log` and `<id>_converge-2.log`

## MODIFIED Requirements

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `backlog`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`, the executor, model and effort from the version's models file, else the run's, and `tokens` the
worker's figure or `unavailable`. The log SHALL NOT be a findings file: no station writes it and no
release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, its time taken from `date`
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's review and security files are read
- **THEN** the log holds one `verdicts` line for each role, each naming that role's executor, model and effort

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/findings/` files and its run logs, `.minions/runs/<stamp>/<change>_<station>.log` and `<change>_<station>-<n>.log`, and the operator's Codex sessions,
`~/.codex/sessions/**/*.jsonl`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. The page
SHALL hold a table per repo and per model, a cost table per repo — each change's stations with their dollars, turns, tokens and
seconds — charts over changes drawn by `mf-build`'s `chart()`, and the list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a station with no log and a log with no result event SHALL be a gap, and a station the run log shows spawned more times than
the logs read SHALL be marked `<read> of <spawns>`. The status log's tokens SHALL be read per role, in every form a `verdicts` line
holds; a line naming both roles SHALL be recorded under the role `both`, credited to neither. A Codex worker's tokens SHALL be read from its session — the
last `token_count` event's totals, its model and effort from `turn_context` — matched to its round by its parent's `cwd` — the change's worktree, or the primary
when no other version's round overlaps — and the round's freeze-to-verdicts window, the guardian sessions left out, and never
into a round its line names `executor claude`. It SHALL write `review-metrics.json`
beside the page: one record per round and role, with its executor, model, effort, tokens and source, a gap as `null`. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: Cost from the run logs
- **WHEN** a repo's run directory holds a converge log with two result events, a build log with none, and a run log naming two
  converge spawns
- **THEN** the converge cell holds the last cumulative dollars and the summed turns, marked as one log of two, and the build cell
  is a gap

#### Scenario: Tokens per role
- **WHEN** a status log holds `tokens review 45426, security 41346`, `tokens 128126 + 115356`, `tokens 115k (review 63k, security
  52k)` and a line naming one role with `tokens 97960`
- **THEN** each role's tokens are read from its own figure, and none is summed into the other

#### Scenario: A Codex worker
- **WHEN** a Codex session's parent ran in the repo's worktree inside a round's window, its path naming `review`
- **THEN** `review-metrics.json` holds that round's review record with the session's tokens, model and effort, `source:
  codex-session`

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed
