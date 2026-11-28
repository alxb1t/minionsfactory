## ADDED Requirements

### Requirement: One module parses a status log's runs and its verdicts line

`skills/mflib/statuslog.py` SHALL give every run of a status log's text, newest first, each its heading's number, its mark and its events: a line that starts `## Run` is a heading, its number the ASCII digits after `## Run ` and none when there are none, its mark the text after the first ` · `, and its events the lines of the run that are events of the module's form, newest first. The module SHALL write the spent text converge puts at the end of a `verdicts` and a `pickup` line — `executor <x> · model <m> · effort <e> · tokens <n>`, the model and effort `default` where none, the tokens `unavailable` where none, then ` · fallback: codex usage limit` for a fallback that is true and ` · fallback: codex failed` for any string — and the `verdicts` line itself, and SHALL parse a `verdicts` event into its role, executor, model, effort, tokens and fallback, the fallback read from the event's own detail. `converge.py` SHALL write both lines through the module.

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

### Requirement: A reader's bounded stream of lines

`skills/mflib/statefile.py` SHALL give `lines(path, cut)`: each line of a regular file, one at a time, cut at `cut` characters with the rest of a longer line dropped, a bad byte replaced and the open made through no link and without blocking. A link, a FIFO, a folder or a missing file SHALL give no line, and no descriptor SHALL stay open.

#### Scenario: A long line

- **WHEN** a file holds a line longer than `cut` between two short lines
- **THEN** the stream gives the first line, the long line cut at `cut`, and the last line

#### Scenario: What is no regular file

- **WHEN** the path is a link, a FIFO or a folder
- **THEN** the stream gives no line, at once

## MODIFIED Requirements

### Requirement: The viewer projects every ship line, read-only

`skills/mf-ui/scripts/viewer.py project <primary>` SHALL load `conduct.py` and `converge.py` from the skill's sibling
packages by path, run with `GIT_OPTIONAL_LOCKS=0`, and print one project's state tree as JSON: each open version's stage and
its `why`, its state, its phases with the ticks of its worktree's `tasks.md`, its converge round, cap, blockers and each role's
executor, model, effort and fallback, its workers, its liveness and its dim notes; the project's run line, its **for you** rows
and its queued cuts. A state SHALL be one of `running`, `idle`, `waiting`, `stacked`, `blocked`, `halted`, `needs you` or
`unread`, by fixed rules read from the stage, the run log, the claim and the change folder: `running` is a station stage with an
unfinished spawn under a live claim, `idle` a station stage with none, `blocked` a waiting version that names a dependency
halted or needing a person, `halted` a `converge-halted` stage, a `build` stage whose `build.halt` names `HEAD`, or a version
whose last line of the newest run log is a halt, a worker's exit or a rescue's diagnosis alike, until a later line of the
version or a newer run log with none ends it, and
`needs you` a `human`, `integrating` or `released` stage. **For you** SHALL hold each version that needs a person or is halted,
each queued cut that halted, a stale claim, a usage limit whose reset is ahead and an unpushed default branch, each row with its
`why`; a rescue's or a supervisor's decision SHALL show dim on its version and never in it.

The viewer SHALL read the state formats through the home modules, each state file through no link, without blocking and as a regular
file alone, `ui.toml` read as it was: the run log through `skills/mflib/runlog.py` and `skills/mflib/statefile.py`, each line cut at 262,144 characters,
the status log through `skills/mflib/statuslog.py`, a findings file through `skills/mflib/findings.py`, the queue through
`skills/mflib/queue.py` and the record of projects through `skills/mflib/kept.py`; a status log, a findings file and the claim
SHALL be read through their first 262,144 bytes, and a file that cannot be read SHALL read as nothing, never as an error page.
The converge run's number and mark SHALL be the newest run's heading's, `fixing` SHALL be true when the newest run's newest event
is named `fix` and its detail starts with `sent`, and each role's executor, model, effort, tokens and fallback SHALL be those of
its newest `verdicts` event in any run, beside the verdict and open blockers its findings file holds.

The server SHALL list the projects the home folder's `repos` record names, each that holds `.minions/` as a folder and no link,
with the `[[container]]` rows of `ui.toml`, found under `$XDG_CONFIG_HOME/minionsfactory/`, else `~/.config/minionsfactory/`,
naming, ordering or hiding them; a missing file SHALL halt nothing, and a bad one SHALL exit 2 naming it. A line of the record that
is no absolute path SHALL list no project. A `repos` that cannot be read, a link, a FIFO, a folder, a bad byte, a NUL byte or a file
over 262,144 bytes, SHALL show one project row named `repos` that says so beside the projects `ui.toml` names, and the poll SHALL go
on; a missing record SHALL be no recorded project. It SHALL read each project in a child process and kill a read past 10 s, showing
that project unread with the reason; a version whose projection raises SHALL show unread alone, the rest of its project read. It
SHALL write no repo, run no git command that changes one, and touch no network. It SHALL answer `/` with the page, `/events` with
the newest whole state and each newer one as server-sent events, each frame numbered, and `/state` with the newest frame as JSON,
bound to `127.0.0.1`; any other path SHALL be 404, and a request whose `Host` is neither `127.0.0.1:<port>` nor
`localhost:<port>` SHALL be refused. The page SHALL set every string as text.

#### Scenario: Each state has its why
- **WHEN** fixture run directories hold a version in each state, a halted one, one needing a person, a waiting one and its
  blocked dependent, a stacked one and a queued cut that halted
- **THEN** the projector prints each version with its state, its stage and the stage's `why`, its phases with the worktree's ticks,
  and the halted cut in the queue and in **for you**

#### Scenario: A halt in the newest run log
- **WHEN** a version's last line of the newest run log is `halt — rescue diagnosed`, and then a newer run log holds only a
  sibling's lines, and then the newest log holds its halt again followed by the run's `rejoin — <id>: build`
- **THEN** the version shows halted, then the state its stage gives once the newer log stands, and again once the rejoin
  follows its halt, while a refused `rejoin — <id>: still …` leaves it halted

#### Scenario: Converge and workers
- **WHEN** a version's status log holds a run marked `· amend`, a `verdicts` line per role and a top line `fix — sent R1`, and the
  newest run log holds an unfinished spawn of each checker
- **THEN** the version shows the round, the mark, `fixing`, each role's executor, model, effort and fallback, the open blockers
  and each unfinished spawn as a worker, with liveness `active` while a write is under a minute old and `quiet` after five

#### Scenario: The newest run is the newest heading
- **WHEN** a status log holds `## Run 3 — 2026-11-03 10:00 · catch-up now` above a run 2 that holds a role's only `verdicts` line
- **THEN** the version shows run 3 with the mark `catch-up now`, and that role's fields from run 2

#### Scenario: A read that fails
- **WHEN** one version's `tasks.md` has no `## Progress` list, and another project's claim `pid` is a pipe the read cannot pass
- **THEN** that version shows unread with the reason while the rest of its project shows its state, and the project with the
  pipe is killed at the bound and shows unread

#### Scenario: A repos that cannot be read
- **WHEN** `repos` is a FIFO and `ui.toml` names one project
- **THEN** the page shows that project and one row named `repos` that says it could not be read, and the poll goes on

#### Scenario: A linked `.minions`
- **WHEN** a recorded path's `.minions` is a link to a folder
- **THEN** no project is listed for it

#### Scenario: A foreign Host
- **WHEN** a request names a `Host` other than `127.0.0.1:<port>` or `localhost:<port>`
- **THEN** it is refused on every path, and a request with an accepted `Host` for any path but `/`, `/events` and `/state` is 404

#### Scenario: The stream
- **WHEN** the state changes after a client holds `/events`
- **THEN** the client receives the newest numbered whole state, and a state that did not change is not sent again

### Requirement: One module writes and parses the run log

`skills/mflib/runlog.py` SHALL be the one writer and parser of the run log, `.minions/runs/<stamp>.md`: its title, its event line and the one pattern that reads it, the event list, the order of logs and the newest log, the verify, the stop line, the reads of the release's death, of the rescue and of `report`, the tail `wait` follows, the moment of an event and the cause of a halt. `conduct.py` SHALL write and read the run log through it, and SHALL keep `EVENT` and `last_log` bound to the module's. The viewer SHALL read the newest log, an event and its moment through the module and take neither `EVENT` nor `last_log` from the loaded conductor. The module SHALL name no state path: its callers find the folder through `skills/mflib/layout.py`.

A run log SHALL be a file of `.minions/runs/` whose name is a stamp, `<YYYYMMDD-HHMMSS>.md`, a real date and time, with a `-<n>` suffix or none; the newest log, the release's death read and `report` SHALL pass over any other `*.md`, a name that is no real date among them. An event line SHALL be `<HH:MM:SS> · <who> · <event> — <detail>`, the detail on one line, and the event list SHALL hold `sync` and `codex` beside the others, so `conduct.py log --verify` passes a run that wrote one. The verify SHALL pass an open spawn only when the log's last line is `run · halt — stopped by the person`, and a finish with no spawn SHALL pass.

An event's moment SHALL be dated from the log's stamp: between two events any step back of the clock is a day on, and the first event is a day on only when its clock is 12 hours or more earlier than the time in the stamp. A halt's cause SHALL be read as the word of lower-case letters and hyphens after ` · cause ` at the end of its detail.

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

### Requirement: The kept files are read and written through one module

`skills/mflib/kept.py` SHALL be the one home of the conductor's kept files in the home folder: the kept origin `<digest>`, `<digest>.default`, the offline base `<digest>.pushed`, the release ledger `<digest>.released/<change>`, a person's gate approval `<digest>.gate/<change>`, the live mark `live/<digest>`, `repos`, the probe mark `probe-<executor>-<pid>` and the pin's four files `source`, `pending`, `hold` and `checkout`, with each one's write, read, listing and removal, and of the operator's `ship.toml` the read. `conduct.py`, `gate_check.py` and `pin.py` SHALL go through it. `cloud_setup.py`'s write of `ship.toml` is not its.

A read of a kept file SHALL follow no link, SHALL not block, SHALL take a regular file alone, SHALL be bounded — 65,536 bytes, and for `repos` 262,144 — and SHALL decode strictly; the read of `ship.toml` and of a pin file is so too. A kept origin, `.default` or offline base that cannot be read SHALL stop the command, exit 2, naming the file: a name that is a link, a FIFO, a folder, over its bound, a bad byte, a kept origin that is not two lists of URLs, or a base that is not empty and not a commit id of 40 hex digits. A pin file and `ship.toml` that cannot be read SHALL stop the command as *The pin's files are read and written through kept.py* and *A ship.toml that cannot be read stops the command* say. A gate approval that cannot be read SHALL approve nothing. A ledger entry that is not one commit id, its whole text stripped being 40 lower-case hex digits, SHALL be no release head, SHALL be named in the run log or, for a command, on stderr, and SHALL stay. A live mark that cannot be read SHALL read as none, and a `repos` that cannot be read SHALL take no append. The read of the record, `kept.repos(path)`, SHALL give each line stripped, a blank one skipped, a missing file giving none, and SHALL raise `Broken` for a `repos` that is a link, a FIFO, a folder, over its bound or holds a bad byte, and for a line that holds a NUL byte.

A write of the offline base, a ledger entry, an approval, the live mark and a pin file SHALL be staged, mode 0600, and a failed write SHALL leave no staged file. The kept origin and `.default` SHALL be written once: a name that stands, of any kind, stays, and the next read of a link or a folder there stops the command as above. The probe mark SHALL be made empty, after a mark of its name is removed. `repos` SHALL be appended to through no link, to a regular file. A folder of the kept files SHALL be made at 0700, and one that stands SHALL keep its mode. A removal SHALL be by name under the folder's descriptor. `.default` SHALL be written with a newline and read stripped.

#### Scenario: A bad byte in `.default` stops the run
- **WHEN** `<digest>.default` holds a byte no text is made of and `conduct.py run` starts
- **THEN** the run's halt line names the file, `conduct.py run` exits 2, and no traceback prints

#### Scenario: A link at the kept origin is not kept
- **WHEN** a dangling link stands at `<digest>.default` and a run keeps the origin's URLs
- **THEN** the keep writes nothing over it
- **AND** the read that follows stops the command, exit 2, naming the file

#### Scenario: A kept file that stands stays
- **WHEN** a second run keeps the origin's URLs
- **THEN** the kept origin is as the first run wrote it

#### Scenario: A FIFO blocks no read
- **WHEN** the offline base is a FIFO
- **THEN** the read returns at once and the command stops, exit 2, naming the file

#### Scenario: An approval that cannot be read approves nothing
- **WHEN** an approval holds a bad byte
- **THEN** `gate_check.py` finds no approval and raises nothing

#### Scenario: An entry that is no commit id is no head
- **WHEN** a ledger entry holds `abc` or two lines
- **THEN** it authorizes no push, a run logs its name, and the entry stays

#### Scenario: A second approval replaces the first
- **WHEN** `conduct.py approve-gate` runs twice for one change with two hashes
- **THEN** the entry holds the second hash, mode 0600

#### Scenario: A live mark that cannot be read reads as none
- **WHEN** a live mark holds a bad byte or is a FIFO
- **THEN** a run takes it over and an install treats it as no live run

#### Scenario: A `repos` that cannot be read takes no append
- **WHEN** `repos` is over 262,144 bytes
- **THEN** a run appends no line and raises nothing

#### Scenario: A `repos` that cannot be read is broken to a reader
- **WHEN** `repos` is a FIFO, or holds a line `x` and a NUL byte, and `kept.repos` reads it
- **THEN** it raises `Broken`, at once for the FIFO

#### Scenario: `.default` ends in a newline
- **WHEN** a run keeps the default branch `main`
- **THEN** `<digest>.default` holds `main` and a newline, and a push to `main` halts nothing

#### Scenario: A pin file is written staged
- **WHEN** `make install-skills` writes `source` twice
- **THEN** `source` holds the second text and one newline, its mode is 0600, and no `source.tmp` stands
