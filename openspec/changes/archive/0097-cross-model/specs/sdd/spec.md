## ADDED Requirements

### Requirement: A converge checker on another host runs through the mailbox

When a version's conformance or adversarial table names an executor other than converge's, or `[converge] shadow = true`,
`conduct.py` SHALL give that version's converge worker one **checker mailbox**, `~/.mf-ship-origin/<digest>.queue/checkers/<change-id>/`,
made a folder and emptied before the worker starts, among its writable paths, and no other worker's; a mailbox that is a link
SHALL halt the version. The converge conductor SHALL send such a checker by writing its prompt to
`.minions/changes/<change-id>/<role>.prompt.md` and running `conduct.py checker <change-id> <role>` in the foreground, which
copies the prompt into the mailbox as `<role>.request` and waits for `<role>.answer`, exiting with its exit code, or exiting 3
after `CHECKER_WAIT` seconds, so a re-run with `--wait` waits on. While that converge worker runs, `conduct.py` SHALL take each
request of a role of `conformance`, `adversarial`, `shadow-conformance` and `shadow-adversarial`, read through one descriptor
following no link and refused past `REQUEST_BYTES`; spawn its checker as `converge-<role>`, logged as any station, with the
executor, model and effort its plan holds, never the request's; and answer `exit <n> · executor <x> · model <m> · effort <e>`.
It SHALL refuse a request past `CHECKER_SPAWNS` in one converge spawn, answering exit 1. A checker's exit SHALL never halt the
version itself. Each findings file SHALL name its checker's `executor:` in its frontmatter. The fixer SHALL run on converge's
host.

#### Scenario: A Codex checker under a Claude conductor
- **WHEN** a version's `[converge]` runs on Claude and `[converge.conformance]` names `executor = "codex"`, `model =
  "gpt-6.1-sol"` and `effort = "high"`
- **THEN** its converge prompt holds `and conformance=mailbox`, the converge worker's sandbox may write its mailbox, and its
  request makes `conduct.py` spawn `codex exec` with `-m gpt-6.1-sol` and `-c model_reasoning_effort=high`
- **AND** the conductor reads `conformance.md` from disk, its frontmatter naming `executor: codex`, and the fixer runs on Claude

#### Scenario: A forged request
- **WHEN** a request names a role outside the four, is a link, or holds more than `REQUEST_BYTES`, or a ninth request comes in
  one converge spawn
- **THEN** no checker starts for it, and a link's, a long request's and a ninth request's answer reads exit 1

#### Scenario: A checker outlasts the wait
- **WHEN** a checker runs past `CHECKER_WAIT` seconds
- **THEN** `conduct.py checker` exits 3, and `conduct.py checker <change-id> <role> --wait` prints the answer once it lands

### Requirement: A shadow round 1 runs the other host's checkers

Under `[converge] shadow = true`, round 1 of a converge run that is neither catch-up nor amend SHALL also send
`shadow-conformance` and `shadow-adversarial` through the mailbox, on the same freeze, each with its role's packet and
reference. Each SHALL run on the executor its role's checker does not, with `[converge]`'s model and effort when converge runs on
that executor, else that executor's default, and SHALL write `.minions/changes/<change-id>/shadow-<role>.md`. A shadow file
SHALL drive no fix, no verdict, no debt card and no release check, and a shadow checker that fails SHALL halt nothing.
`skills/mf-converge/scripts/overlap.py <change-folder>` SHALL match round 1's cards of each role with its shadow's by the
`path:line` spans of their **What it affects**, and print each role's shared cards, each side's own and the blockers among
them; the conductor SHALL write its line as the round's `shadow` event.

#### Scenario: A shadow round
- **WHEN** a version's models file says `shadow = true` and its checkers run on Codex
- **THEN** round 1 writes `shadow-conformance.md` and `shadow-adversarial.md`, each `executor: claude`, and the status log
  holds a `shadow` line counting shared and unique catches
- **AND WHEN** a shadow file holds an open blocking card
- **THEN** no fixer is sent it, and the version's converge check passes on its clean conformance and adversarial files

#### Scenario: Two catches of one line
- **WHEN** a conformance card names `total.py:12` and a shadow conformance card names `total.py:14`, and another shadow card
  names `README.md`
- **THEN** `overlap.py` counts one shared card and one card the shadow alone caught

## MODIFIED Requirements

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one.
Lines split at a newline alone. It SHALL also exit 1 when a line of `## For the cut` is none of: a blank line; a head, opening
`<n>. ` and one space at the line's start; a `- models: ` or `- **Acceptance:** ` line indented three spaces or as far as its
head's text; a line indented at least two spaces past its Acceptance line, after that line or its continuation; or the cut's
`Cut <YYYY-MM-DD> as <id> at <sha>.` line. It SHALL also exit 1 when a head names a slug or an `after` entry that `conduct.py`'s
`SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or more than one, or when an item has no `models:` line, more
than one, or one not naming the build, converge, release and cut station in order, then any of the conformance, adversarial and
fix parts in that order, each with a model and effort of `[A-Za-z0-9._-]` alone, then at most a last `shadow`. A build,
converge, release, conformance or adversarial model MAY open with a host, `claude/` or `codex/`; a host it does not know, or a
host on the cut or fix model, SHALL exit 1, naming it. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or
`## For the cut` holds a character for which `str.isprintable()` is false, printing `brief: halt — <section> line <n>: a
character isprintable() refuses`; when a line of the brief that is not `## Decisions`, `## Dependencies` or `## For the cut` as
written reads as one of them once every character but a letter or a digit is dropped and case is folded, or a second line is
one of them as written; when the brief has no `## Dependencies`; and when that section is neither `None.` nor a table of item,
package, constraint and why whose every row names a `## For the cut` item's slug, a package and a constraint.
It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot
be parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`, or an
  item's slug or cut effort holds `$(…)` or `;`
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** a `## For the cut` line opens `- ` where `<n>. ` is due, a `| ` line sits under a head, an unindented line
  follows a head, or a head holds a second `after:`, or an item has a second models line
- **THEN** `brief_check.py` exits 1, naming the line or the item

#### Scenario: A models line naming hosts
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · conformance codex/gpt-6.1-sol high · adversarial codex/gpt-6.1-sol
  high · fix claude-opus-5-5 high · shadow`
- **THEN** that line halts nothing
- **AND WHEN** a part names `gemini/x`, or the fix or cut model opens with a host
- **THEN** `brief_check.py` exits 1, naming the item and the word

#### Scenario: A checked line holds other whitespace
- **WHEN** a line of a brief's `## For the cut`, `## Dependencies` or `## Decisions` holds a no-break space, an ideographic
  space, a tab, a vertical tab, a form feed, U+200B or U+2060
- **THEN** `brief_check.py` exits 1, printing `brief: halt — <section> line <n>: a character isprintable() refuses` for that line

#### Scenario: A For the cut heading in another form
- **WHEN** a brief holds ` ## For the cut`, `##<tab>For the cut`, `## For the cut ##`, `## For the cut` followed by U+200B, or
  `For the cut` underlined `---`, besides its `## For the cut`, or that heading twice
- **THEN** `brief_check.py` exits 1, naming each such line

#### Scenario: A brief's packages
- **WHEN** a hard brief has no `## Dependencies`, or one that is prose, or a row naming no `## For the cut` item
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** it reads `None.`, or each row names an item, a package and a constraint
- **THEN** that section halts nothing

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, its `## Dependencies`, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort`, and the conformance and adversarial tables an `executor`; `[converge]` stays the
conductor's, and MAY say `shadow = true`. `conduct.py` SHALL read them once with the run's plan. A checker table with no
`executor` SHALL run on converge's. It SHALL halt a version, before its worker starts, on a fixer table that names an
`executor`, an `executor` it does not know, a checker table naming `executor = "codex"` with a `claude-*` model, or a `model` or
`effort` holding anything
but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later differs, as for any station's table.
It SHALL pass in the converge prompt, before any grant clause, for conformance, adversarial and the fixer in that order:
`and <role>=mailbox` for a checker whose executor differs from converge's, else `and <role>=<model>/<effort>` for a table that
names a model or an effort, `default` for the one absent, with converge on Claude; then `and shadow=yes` under `shadow = true`. Converge SHALL put each model on its worker's call,
send each `mailbox` role through `conduct.py checker`, and SHALL NOT read the models file itself. A fixer sent any blocking card
SHALL run on adversarial's model and effort when adversarial runs on converge's host, and otherwise on the fixer's. A role given
none, or a host whose worker call takes no model, SHALL run its worker on the conductor's model. The cut SHALL write the worker
tables from the brief's `conformance`, `adversarial` and `fix` parts, each host as `executor`, and else conformance on the mid
tier · high, adversarial on the strongest tier · high, the fixer on the mid tier · high; `[converge]` on the mid tier · medium
unless the brief names converge's model; and `shadow = true` when the brief's line ends `shadow`, each mapped to the offered
models.

#### Scenario: The converge prompt names each worker's model
- **WHEN** a version's models file holds `[converge.adversarial]` with `model = "claude-opus-5-5"` and `effort = "high"`, and
  `[converge.fix]` with `model = "claude-sonnet-5-5"` and `effort = "high"`, and its converge runs on Claude
- **THEN** its converge prompt reads `Run the mf-converge skill for change <change-id> and adversarial=claude-opus-5-5/high and
  fix=claude-sonnet-5-5/high.`

#### Scenario: Converge on Codex
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a worker table naming no executor
- **THEN** its converge prompt names no worker model, and every worker runs on the conductor's model

#### Scenario: A checker on another host
- **WHEN** `[converge.conformance]` names `executor = "codex"` and converge runs on Claude
- **THEN** its converge prompt holds `and conformance=mailbox`, and names no model for conformance

#### Scenario: A worker table names an executor
- **WHEN** `[converge.fix]` names `executor = "codex"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A worker table changes during the run
- **WHEN** a worker changes `[converge.fix]`'s model after the run read its plan
- **THEN** that version halts, naming the models file as changed during the run

#### Scenario: The fixer by grade
- **WHEN** converge dispatches a fixer sent a blocking card, adversarial running on converge's host
- **THEN** the fixer runs on adversarial's model and effort
- **AND WHEN** it dispatches a fixer sent only non-blocking cards
- **THEN** the fixer runs on the fixer's model and effort

### Requirement: A station's executor comes from the models file

`.minions/changes/<change-id>/models.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own — each station's, each checker table's, and
each shadow checker's under `shadow = true`; a failed probe at the start SHALL stop the run, and one for a joining version
SHALL halt only the versions on its executor.
A station on Codex SHALL report each denial, its usage limit with the reset time, its tokens and its priced cost from its JSON
event log, as a station on Claude does from its own; converge's per-role tokens SHALL read `unavailable` on Codex, save a
checker the mailbox started, whose own log holds them.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A checker's executor is probed
- **WHEN** a run's only Codex table is a version's `[converge.adversarial]`
- **THEN** the run probes Codex before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A Codex worker is refused a command
- **WHEN** a Codex worker's command fails with the sandbox's `Operation not permitted`
- **THEN** the run log holds a `denied` line naming the command, and the report lists it

#### Scenario: A Codex worker meets its usage limit
- **WHEN** a Codex worker exits 1 after a failed turn whose error names its usage limit and a time to try again
- **THEN** its version halts with `stopped by a usage limit · resets <time>`

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `shadow`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor, model and effort a mailbox checker's answer names, else the executor the conductor runs
on and the model and effort its worker was given, `default` where none, and `tokens` the worker's figure or `unavailable`. A
`shadow` line SHALL hold `overlap.py`'s line, or a shadow checker's failure. An adversarial head written by rule SHALL write one
`by rule` line, `no surface`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's conformance and adversarial files are read, each written by its worker
- **THEN** the log holds one `verdicts` line for each role, each naming the executor, and the model and effort that role's
  worker was given

#### Scenario: A mailbox checker's verdicts
- **WHEN** conformance ran through the mailbox and its answer reads `exit 0 · executor codex · model gpt-6.1-sol · effort high`
- **THEN** its `verdicts` line ends `executor codex · model gpt-6.1-sol · effort high · tokens unavailable`

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** `surfaces.py` exits 0 in a verify round
- **THEN** the log holds one `by rule` line, `no surface`, the round's `fan-out` names conformance alone, and its one
  `verdicts` line is conformance's

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — and the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. A Codex station's tokens SHALL be the sum over its log's `turn.completed` events of their input and output tokens, and
its dollars those tokens priced by `skills/mf-review-metrics/prices.toml` under the model its log's spawn line names; a model
with no row there, or no model named, SHALL make the cost metrics a gap naming it, and SHALL leave the token metrics read. A
checker the mailbox started, `converge-<role>` or `converge-shadow-<role>`, SHALL count in the cost and tokens of the stage
whose converge spawn holds its start, never in its minutes, and a `converge-<role>` log's tokens in that role's. The cut's `diff-lines` and `diff-files` SHALL be the
collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

#### Scenario: A converge on Codex
- **WHEN** a version's converge log is a Codex JSON log whose spawn line names a model the price table holds
- **THEN** `cost-usd-converge` holds its priced dollars and `tokens-converge` its summed tokens
- **AND WHEN** the price table holds no row for that model
- **THEN** `cost-usd-converge` is a gap naming the model, and `tokens-converge` is read

#### Scenario: A checker through the mailbox
- **WHEN** a version's run log spawns `converge-conformance` inside its converge, its log a priced Codex log
- **THEN** `cost-usd-converge` and `tokens-converge` hold that log's dollars and tokens beside converge's own,
  `conformance-tokens-per-confirmed` counts its tokens, and `minutes-converge` is unchanged

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/changes/<change-id>/` files and its worker logs, `.minions/changes/<change>/logs/<stamp>-<station>.log` and
`<stamp>-<station>-<n>.log` — in a repo no run has moved, the old `.minions/findings/` and `.minions/runs/<stamp>/<change>_<station>.log`
and `-<n>.log` alike — and the operator's Codex sessions,
`~/.codex/sessions/**/*.jsonl`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. It SHALL read a change's
`conformance.md`, else its `review.md`, and its `adversarial.md`, else its `security.md`, and SHALL record each role by the name
its file or line carries, with its file's `executor:` and `model:`. The page
SHALL hold a table per repo and per role, executor and model, a cost table per repo — each change's stations, the mailbox's
checkers among them, with their dollars, turns, tokens and seconds — charts over changes drawn by `mf-build`'s `chart()`, and the
list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a Codex JSON log's tokens SHALL be the sum over its `turn.completed` events of their input and output tokens, its dollars those
tokens priced by `skills/mf-review-metrics/prices.toml` under the model its spawn line names, a gap with no such row, and its
turns and seconds gaps;
a station with no log and a log with neither result nor `turn.completed` event SHALL be a gap, and a station the run log shows spawned more times than
the logs read SHALL be marked `<read> of <spawns>`. The status log's tokens SHALL be read per role, in every form a `verdicts` line
holds; a line naming both roles SHALL be recorded under the role `both`, credited to neither. A Codex worker's tokens SHALL be read from its session — the
last `token_count` event's totals, its model and effort from `turn_context` — matched to its round by its parent's `cwd` — the change's worktree, or the primary
when no other version's round overlaps — and the round's freeze-to-verdicts window, the guardian sessions left out, and never
into a round its line names `executor claude`. A role's executor SHALL be its file's `executor:`, else the one its round 1
`verdicts` line names. An **escape** SHALL be a card whose `repeat of` names an earlier change's card, traced to that change's
round 1 by the card's role and that role's executor. The shadow overlap SHALL be `overlap.py`'s count over each change's
round 1 and shadow files. It SHALL write `review-metrics.json`
beside the page: `records`, one per round and role, with its executor, model, effort, tokens and source; `roles`, one per change
and role; `shadow`, one per change and role with a shadow file; `escapes`; and `headline`; a gap as `null`. The page and
`headline` SHALL show four numbers: each executor's share of the shadow rounds' distinct blockers that it alone caught; escapes
per version; dollars of converge per confirmed blocker, by the checkers' executor; and, per executor of the checker that raised
it, the share of cards whose first verify after `fixed` read `verified`. It SHALL read no tier, and SHALL count a file's
`inconclusive` sections only when the file holds `## Refuted`, the review method's mark. It SHALL give numbers, never a
recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: A repo of each layout
- **WHEN** one repo holds `.minions/changes/<id>/` and another the old `.minions/findings/` and `runs/<stamp>/` logs
- **THEN** both repos' changes are read, with their cost, and neither is written

#### Scenario: Both role names
- **WHEN** one change's folder holds `conformance.md` and `adversarial.md`, and another's `review.md` and `security.md`
- **THEN** both changes are read, each round recorded under the role names its files and lines carry

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: Cost from the run logs
- **WHEN** a repo's run directory holds a converge log with two result events, a build log with none, and a run log naming two
  converge spawns
- **THEN** the converge cell holds the last cumulative dollars and the summed turns, marked as one log of two, and the build cell
  is a gap

#### Scenario: Cost from a Codex log
- **WHEN** a station's log is a Codex JSON log with two `turn.completed` events, and its spawn line names a model the price
  table holds
- **THEN** its cell holds the priced dollars and the summed tokens, its turns and seconds gaps
- **AND WHEN** the spawn line names a model the table lacks
- **THEN** its dollars are a gap and its tokens are read

#### Scenario: Tokens per role
- **WHEN** a status log holds `tokens review 45426, security 41346`, `tokens 128126 + 115356`, `tokens 115k (review 63k, security
  52k)` and a line naming one role with `tokens 97960`
- **THEN** each role's tokens are read from its own figure, and none is summed into the other

#### Scenario: A Codex worker
- **WHEN** a Codex session's parent ran in the repo's worktree inside a round's window, its path naming `conformance`
- **THEN** `review-metrics.json` holds that round's conformance record with the session's tokens, model and effort, `source:
  codex-session`

#### Scenario: Cross-model numbers
- **WHEN** a repo holds a change whose conformance ran on Codex with a Claude shadow, the shadow alone catching one blocker and
  both one, a later change carrying a card `repeat of` the first's, and a Codex card the Claude fixer fixed and a verify
  promoted to `verified`
- **THEN** `review-metrics.json` holds a `roles` record per role with its executor, a `shadow` record counting one shared and
  one shadow-alone blocker, an `escapes` record traced to the first change's conformance on Codex, and a `headline` holding the
  four numbers, and the page shows them

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per role, executor and model, and charts, and no repo has changed
