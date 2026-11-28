## MODIFIED Requirements

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version), and the time a dependent waits on its `after:` ids (each `wait` event of the version until its next event in
the same run, a version with none 0); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. A Codex station's tokens SHALL be the sum over its log's `turn.completed` events of their input and output tokens, and
its dollars those tokens priced by `skills/mf-review-metrics/prices.toml` under the model its log's spawn line names; a model
with no row there, or no model named, SHALL make the cost metrics a gap naming it, and SHALL leave the token metrics read. A
converge worker's log, `<stamp>-converge-<role>-r<N>.log` — a checker's, the fixer's or a verify worker's — SHALL count in the cost
and tokens of the converge stage, never in its minutes, which the run log's `converge` spawn and finish hold, and a checker's log's
tokens in that role's. The cut's `diff-lines` and `diff-files` SHALL be the
collector's station values.

`scripts/metrics/run.py` SHALL read each format of a version through the home module that owns it. It SHALL take the run logs from `runlog.logs`, passing over a name that is no real date and time, read each through `statefile.lines` so that a link, a pipe, a folder or a missing file gives no event, and date each event through `runlog.timed`: between two events any step back of the clock is a day on, the first event is a day on only when its clock is 12 hours or more earlier than the time in the log's stamp, and a line whose clock is no time of day is no event. It SHALL read the status log through `layout.status_log` and `statuslog.runs`: a round is an event's, a run's mark is the module's whole, and a round-1 `verdicts` count is `statuslog.blocking`'s for a `conformance` or `adversarial` line and `eras.blocking`'s for the old `review`, `security` and colon forms. It SHALL read a findings file through `findings.cards`, a card being a titled line and its indented lines and a Verdict a word read with its case folded, and the refuted section through `findings.refuted`, else `eras.refuted`; a file with neither is a gap. It SHALL read the head of `build.done` through `marks.done_head`, count a debt card as `debtfile` does — a title `- **<digits>·<id> — ` — and read `prices.toml` through `prices.rows`, an unreadable table making the Codex cost metrics a gap `prices: <reason>` and a model with no usable row a gap naming the model.

`scripts/metrics/debt.py` SHALL read and count the debt file through `debtfile`, and exit `no <file>: <reason>` for a file the module refuses, a link to a regular file among them.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: A dependent's wait
- **WHEN** a version's run log holds `wait — after 0001-x` at `09:08:30` and its build spawn at `09:09:00`
- **THEN** `after-wait-minutes` reads `0.5`
- **AND WHEN** a version's run log holds no `wait` event
- **THEN** `after-wait-minutes` reads `0`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

#### Scenario: A converge on Codex
- **WHEN** a version's converge checker logs are Codex JSON logs whose spawn lines name a model the price table holds
- **THEN** `cost-usd-converge` holds their priced dollars and `tokens-converge` their summed tokens
- **AND WHEN** the price table holds no row for that model
- **THEN** `cost-usd-converge` is a gap naming the model, and `tokens-converge` is read

#### Scenario: A checker through the mailbox
- **WHEN** a version's logs hold `<stamp>-converge-conformance-r1.log`, a priced Codex log, no mailbox standing
- **THEN** `cost-usd-converge` and `tokens-converge` hold that log's dollars and tokens,
  `conformance-tokens-per-confirmed` counts its tokens, and `minutes-converge` is the run log's

#### Scenario: A clock that steps back
- **WHEN** a version's run log holds a build spawn at `10:00:00` and its finish at `09:59:00`
- **THEN** `build-minutes` reads `1439`, the finish being a day on

#### Scenario: A name that is no date
- **WHEN** `20261399-250000.md` stands beside a version's run log
- **THEN** the metrics read the run log and none raises

#### Scenario: An old verdicts line
- **WHEN** a status log's round 1 holds `verdicts — review changes-requested · open_blocking 2 (R1, R2)` and a `security` line with `open_blocking 0`
- **THEN** `blockers-round-1` reads `2`

#### Scenario: A findings file whose section is spelled `## Refused`
- **WHEN** an adversarial file holds a `## Refused` section and no `## Refuted`
- **THEN** its refuted, confirmed and escape metrics are read, not gaps

#### Scenario: A price table that cannot be read
- **WHEN** `prices.toml` is a link, a pipe or no TOML and a Codex log is priced
- **THEN** the cost metrics are a gap `prices: <reason>`, the token metrics are read, and nothing blocks

#### Scenario: A debt line with no title
- **WHEN** the debt file holds `- **0023·a**` with no ` — `
- **THEN** `debt.py` and `debt-added` count no card

### Requirement: One module writes and parses the run log

`skills/mflib/runlog.py` SHALL be the one writer and parser of the run log, `.minions/runs/<stamp>.md`: its title, its event line and the one pattern that reads it, the event list, the order of logs, the list of every log and the newest log, the verify, the stop line, the reads of the release's death, of the rescue and of `report`, the tail `wait` follows, the moment of an event and the cause of a halt. `conduct.py` SHALL write and read the run log through it, and SHALL keep `EVENT` and `last_log` bound to the module's. The viewer SHALL read the newest log, an event and its moment through the module and take neither `EVENT` nor `last_log` from the loaded conductor. The module SHALL name no state path: its callers find the folder through `skills/mflib/layout.py`.

A run log SHALL be a file of `.minions/runs/` whose name is a stamp, `<YYYYMMDD-HHMMSS>.md`, a real date and time, with a `-<n>` suffix or none; the list of logs, the newest log, the release's death read and `report` SHALL pass over any other `*.md`, a name that is no real date among them, and the list SHALL be oldest first. An event line SHALL be `<HH:MM:SS> · <who> · <event> — <detail>`, the detail on one line, and the event list SHALL hold `sync` and `codex` beside the others, so `conduct.py log --verify` passes a run that wrote one. The verify SHALL pass an open spawn only when the log's last line is `run · halt — stopped by the person`, and a finish with no spawn SHALL pass.

An event's moment SHALL be dated from the log's stamp: between two events any step back of the clock is a day on, and the first event is a day on only when its clock is 12 hours or more earlier than the time in the stamp. A line whose clock is no time of day, an hour of 24 or more or a minute or a second of 60 or more, SHALL have no moment, while the event reads of the conductor keep reading it as an event. A halt's cause SHALL be read as the word of lower-case letters and hyphens after ` · cause ` at the end of its detail.

The log's create, its appends and the stop line SHALL open the log under the runs folder's descriptor, follow no link, take a regular file alone and not block. Each line SHALL be one `O_APPEND` write, the appends of one conductor SHALL be held by a lock in the process, and the stop line SHALL have one writer, the module's append. Every conductor read of a log SHALL follow no link, not block, take a regular file alone and replace a byte that is not UTF-8.

#### Scenario: A run that wrote a sync line
- **WHEN** a run log holds `run · sync — <note>` or `run · codex — not on PATH: …` and ends on `done`
- **THEN** `conduct.py log --verify` exits 0

#### Scenario: An open spawn under a version's own halt
- **WHEN** a log ends on a version's `halt` line with a worker's spawn still open
- **THEN** `conduct.py log --verify` exits 1 naming the spawn
- **AND WHEN** the last line is `run · halt — stopped by the person`
- **THEN** it exits 0

#### Scenario: A link at the log
- **WHEN** a worker plants a link at `<stamp>.md` and the run appends an event or a person stops the run
- **THEN** the write fails naming the link, and the link's target is unchanged

#### Scenario: A pipe at the log
- **WHEN** a pipe stands at `<stamp>.md`
- **THEN** each reader and each writer of the conductor ends at once without reading or writing it

#### Scenario: A bad byte in the log
- **WHEN** a run log holds a byte that is not UTF-8
- **THEN** `report`, the verify and the release's death read it with the byte replaced, and none raises

#### Scenario: A file that is no stamp
- **WHEN** `.minions/runs/notes.md` stands beside the run's logs
- **THEN** the newest log, the stop line and `report`'s closing line are the newest stamp's

#### Scenario: A name that is no real date
- **WHEN** `20261399-250000.md` stands beside `20261102-100000.md` and `20261102-100000-10.md` stands beside `20261102-100000-2.md`
- **THEN** the first is passed over and the second pair's newest is the suffix `-10`

#### Scenario: An event's day
- **WHEN** a log stamped `20261103-235900` holds an event at `00:00:01` and then one at `00:00:00`, and another log stamped `20261103-130000` holds `10:00:00` first
- **THEN** the first event of the first log is on the next day and its second a day on again, and the first event of the second log is on the stamp's day

#### Scenario: Every log, oldest first
- **WHEN** `.minions/runs/` holds `20261105-100000.md`, `20261105-090000-2.md`, `20261104-235959-3.md`, `20261105-090000.md` and `notes.md`
- **THEN** the list is `20261104-235959-3`, `20261105-090000`, `20261105-090000-2`, `20261105-100000`

#### Scenario: A clock that is no time
- **WHEN** a log holds `25:00:00 · x · spawn — build` beside good events
- **THEN** the event has no moment and the others do, the conductor's event reads still hold it as an event, and the viewer raises nothing

### Requirement: One module parses a status log's runs and its verdicts line

`skills/mflib/statuslog.py` SHALL give every run of a status log's text, newest first, each its heading's number, its mark and its events: a line that starts `## Run` is a heading, its number the ASCII digits after `## Run ` and none when there are none, its mark the text after the first ` · `, and its events the lines of the run that are events of the module's form, newest first. The module SHALL write the spent text converge puts at the end of a `verdicts` and a `pickup` line — `executor <x> · model <m> · effort <e> · tokens <n>`, the model and effort `default` where none, the tokens `unavailable` where none, then ` · fallback: codex usage limit` for a fallback that is true and ` · fallback: codex failed` for any string — and the `verdicts` line itself, and SHALL parse a `verdicts` event into its role, executor, model, effort, tokens and fallback, the fallback read from the event's own detail. It SHALL also give the open-blocking count of a `verdicts` event whose detail starts with the role `conformance` or `adversarial`, the number after the detail's first ` · open_blocking `, and none for any other event. `converge.py` SHALL write both lines through the module.

#### Scenario: Every run, newest first

- **WHEN** a status log holds `## Run 3 — 2026-11-03 10:00 · catch-up now` above `## Run 2 — 2026-11-03 09:00 · amend`
- **THEN** the module gives run 3 with the mark `catch-up now` and then run 2 with the mark `amend`, each with its events

#### Scenario: A heading with no number

- **WHEN** a line reads `## Running`
- **THEN** it is a heading with no number

#### Scenario: A verdicts line written and read

- **WHEN** converge writes a `verdicts` line for a checker that fell back with a string
- **THEN** the module reads that event's role, executor, model, effort, tokens and a fallback that is true

#### Scenario: Words before the event's name

- **WHEN** a line holds `fallback: codex failed` before the word `verdicts`, outside the event's detail
- **THEN** the line is no `verdicts` event, and no fallback is read from it

#### Scenario: The count of a verdicts line

- **WHEN** an event named `verdicts` holds `conformance clean · open_blocking 2 · executor claude`, and another holds `review changes-requested · open_blocking 2`
- **THEN** the module gives `2` for the first and none for the second

### Requirement: One module writes and parses a findings file

`skills/mflib/findings.py` SHALL be the one writer and parser of a findings file: its card, its fields, its frontmatter, the read of the file, a halt's card ids, the stub, the stamp and the entries of its refuted section. `converge.py`, `conduct.py` and `integrate.py` SHALL read and write a findings file through it, and `open_cards.py`, `overlap.py` and `skip_stub.py` SHALL be commands over it with their arguments, output and exits as they were.

A **card** SHALL be its title line `- **<id> — <title>**` and the indented lines after it, a blank line not ending it; a **field line** SHALL be `- **<Name>:**`, `- **<Name>**:` or a bare `- **Still true?**`, the first of a repeated field read. A field's **word** SHALL be its first word with backticks and `*` dropped, a trailing `.,;:` stripped and case folded, read the same for a Status, a grade and a category; a Status word no reader knows, and an empty Status, SHALL read as not cleared. A card id outside `R<n>` and `S<n>`, and a Status or Priority line under no card, SHALL make the file malformed at its read, in every reader.

The **refuted section** SHALL be the lines from the first line that starts `## Refuted` to the next line that starts `## `, or to the end of the text, and its entries the top-level `- ` lines of it; a text with no such heading has none.

The **frontmatter** SHALL be the block at the start of the file, closed by its first `---` line, a key and its whole value stripped. Every reader SHALL follow no link and replace a byte that is not UTF-8, a missing file keeping each caller's answer; a malformed file SHALL reach `conduct.py`'s security readers as a blocking security card. The conductor's stamp of a checker's `model:` and `tokens:` SHALL write through the staged write of `skills/mflib/statefile.py` at mode `0600`, renaming over the file, and SHALL NOT unlink it first.

#### Scenario: A Status read the same everywhere
- **WHEN** a blocking card's Status reads `Open` and its grade is bold
- **THEN** converge, the conductor's automatic grant and `open_cards.py` each count it open and blocking

#### Scenario: A card runs through a blank line
- **WHEN** a card's Fix field follows a blank line after its Status
- **THEN** every reader reads the Fix as the card's own, and its size is the one it names

#### Scenario: A field written either way
- **WHEN** a card holds `- **Status**: fixed` and another holds `- **Status:** fixed`
- **THEN** every reader reads `fixed` for each

#### Scenario: A security card in an unread category
- **WHEN** an adversarial card blocks and its category is none of the named non-security ones
- **THEN** converge and `conduct.py` each read it as a security card

#### Scenario: A card titled outside the contract's ids
- **WHEN** a findings file holds a card titled `- **S-1 — a title**`
- **THEN** every reader reads the file as malformed, and `conduct.py`'s security readers read it as a blocking security card

#### Scenario: A frontmatter value that crosses a line break
- **WHEN** a findings file's `verdict:` is followed by a blank value and a word on the next line
- **THEN** the conductor and integrate read the value converge reads: the whole stripped value, which is empty

#### Scenario: A linked findings file
- **WHEN** a findings file is a link
- **THEN** each reader refuses it, follows no link and writes nothing

#### Scenario: A stamp keeps the file
- **WHEN** the conductor stamps `model:` and `tokens:` into a findings file
- **THEN** the file is renamed over from `<name>.tmp` at mode `0600`, and no moment holds it deleted

#### Scenario: A file still malformed after its rewrite
- **WHEN** a role's findings file is malformed after its rewrite worker
- **THEN** converge reads the role clean at `HEAD` and files a spoiled card, and the conductor and integrate read the file's own `verdict:` and `head:`

#### Scenario: Which Status clears
- **WHEN** a findings file holds a card whose Status is `accepted`
- **THEN** converge clears it and `skip_stub.py` does not

#### Scenario: The refuted section
- **WHEN** a findings file's text ends on `## Refuted` and `- a claim` with no newline
- **THEN** the entries are `- a claim`, and a text with no such heading has none

## ADDED Requirements

### Requirement: One module reads the price table

`skills/mflib/prices.py` SHALL give `rows(path)`: the `[models]` table of `skills/mf-review-metrics/prices.toml` as a row of numbers by model, a row that is no table or holds a price that is no number, a bool included, left out. It SHALL raise `Unreadable` with a reason for a missing file, a link, a pipe, a folder, a file over 262,144 bytes, text that is no TOML, and a `models` that is missing or no table, following no link and not blocking. `scripts/metrics/run.py` and `skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the table through it and parse it nowhere else.

#### Scenario: A table read
- **WHEN** `prices.toml` holds two Claude rows and a Codex row
- **THEN** `rows` gives the three rows by model, each a row of numbers

#### Scenario: A row with a string price
- **WHEN** a row of the table holds `input = "1"`
- **THEN** that model has no row and the other models keep theirs

#### Scenario: A file that is no regular file
- **WHEN** `prices.toml` is a link, a folder or a pipe
- **THEN** `rows` raises `Unreadable` at once, and nothing blocks

#### Scenario: A table that is no table
- **WHEN** the file holds no `models` key, or `models = 1`
- **THEN** `rows` raises `Unreadable` saying there is no models table

### Requirement: One module reads the formats an old run left

`skills/mflib/eras.py` SHALL read the forms of old runs, and the spelling `## Refused` a checker still slips into, and write nothing: `blocking(event)` the count of a `verdicts` event whose detail starts with the role `review` or `security` and holds ` · open_blocking <n>`, or holds `open_blocking: <n>`; and `refuted(text)` the entries of the refuted section under the heading `## Refused`. No conductor and no station SHALL load it; the metric scripts SHALL.

#### Scenario: An old role line
- **WHEN** an event named `verdicts` holds `review changes-requested · open_blocking 2 (R1, R2) · 7 commits`
- **THEN** `blocking` gives `2`

#### Scenario: A colon count
- **WHEN** a `verdicts` detail holds `review verdict: changes-requested; open_blocking: 2 (R1, R2)`
- **THEN** `blocking` gives `2`

#### Scenario: The old section's spelling
- **WHEN** a findings text holds a `## Refused` section with one top-level entry
- **THEN** `refuted` gives that entry, and `findings.refuted` of the same text gives none

#### Scenario: No station loads it
- **WHEN** the scripts of the conductor and of each station are searched for `eras`
- **THEN** none loads the module
