# Viewer — design

The viewer reads each state format through its home module, the home gains the parsers the viewer held alone, and phase 4 turns the readings the person settled. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The viewer is the operator's live page. It parses the status log, the run log, a findings file, the queue and `repos` with its own regexes and reads, beside the home module that writes each, and where the two disagree on a file of today's format the module's answer is the answer ([D13](#d13)).

```
before   viewer.py ── own regex, own read ──▶ status_log.md · run log · findings · repos
                   └─ EVENT, last_log, _cuts, _frontmatter borrowed from the loaded conduct.py

after    viewer.py ──▶ statuslog · runlog · findings · queue · kept · statefile · layout
                   └─ stage_of, _claim, _build_halt, _progress, _rating, _maybe: still loaded (D3)
```

The version is the first of the series' readers' versions. Phase 1 pins today's behaviour with the cases of a mutation run, phases 2 and 3 move the code and change no assert, and phase 4 alone changes a right side.

## Goals / Non-Goals

- Goal: the viewer holds no regex of a state format that a home module owns, save the lines of [D23](#d23).
- Goal: each reading the person settled is pinned by a named test before it is turned, and turned in phase 4 alone.
- Goal: the lists of `tests/test_structure.py` shrink by the entries the move empties ([D32](#d32)).
- Non-goal: `stage_of`, the loads of the conductor and converge, the page, the frame and the conductor ([D3](#d3), [D31](#d31)).
- Non-goal: a reading no decision turns, such as the words of a status log that is a folder ([The readings, settled](#the-readings-settled)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | In a move phase no assert changes, only the line by which a test reaches a name; a region's tests leave `tests/test_conduct.py` with it | an unchanged assert over moved code proves the move changed nothing | a one-time split of the conductor's tests |
| [D2](#d2) | `.minions` and `.mf-ship-origin` are joined in the layout module alone, with a list of today's sites that only shrinks | the rule stops a new copy | — |
| [D3](#d3) | The viewer's format reads go through the modules; `stage_of` stays a listed load until the station table | station logic over git runs ahead of later versions | moving `stage_of` now |
| [D4](#d4) | One read follows no link, does not block and takes a regular file alone; the bound is the caller's | the bounds are separate policies | one bound for every reader |
| [D5](#d5) | Outside `skills/mflib/` no string constant equals `status_log.md` or contains `## Run`, its sites listed | exact for these names | a rule for marks and event names |
| [D6](#d6) | The format rule gains the run log: no `# Ship run` and no event clock outside the home | the third format | — |
| [D7](#d7) | `ui.toml` and `review-metrics.toml` stay out of the home; `prices.toml` goes to a later version | one parser each | — |
| [D8](#d8) | `queue.py` and `kept.py` hold their formats' writes and reads; the viewer's borrows of them leave in this version | each format's writer and parser sat in different scripts | — |
| [D9](#d9) | One read for every kept file: no link, no block, a regular file alone, `65536` bytes, `repos` `262144` | no home read of the conductor's went through the helper | — |
| [D10](#d10) | A broken kept file ends no command in a traceback and never reads as its permissive answer | a bad byte raised in a traceback | — |
| [D11](#d11) | A `Verify:` or an Acceptance command that runs `uv run pytest` over more than one test file, or over `tests/test_conduct.py` alone, carries `-n auto` | the plan check stops a command at `600` s | — |
| [D12](#d12) | The readers' round is a version a reader or a pair: this one, the metric scripts, review metrics, one in flight | `kept` was a large version and halted once | one version for every reader |
| [D13](#d13) | Where a reader and its format's module disagree on a file of today's format, the module's answer is the answer; the reader keeps its byte bound and what an unreadable file means to it | one parser a format is the series' end state | each reader's own parse |
| [D14](#d14) | The viewer's bounds stay: `262144` bytes through `statefile.read(limit=)`; a link, a FIFO or a missing file reads as nothing, never as an error page; the module parses the text it is handed | the viewer is unsandboxed and reads what a worker wrote, in a child the server kills | the module opening the file |
| [D15](#d15) | The metrics keep reading the old eras in one read-only home module that no conductor and no station loads | an old era is data on disk | a listed format site in a reader |
| [D16](#d16) | Each parser the home lacks lands in its format's module beside its writer; no module for a worker log, a transcript, a session or `tasks.md`'s progress | one module a format | a module of each file |
| [D17](#d17) | After the readers' round the viewer's loads of `conduct.py` and `converge.py` and its borrowed station logic stay listed until the station table | station logic over git | — |
| [D18](#d18) | Terms: a minor, `decide: recommended`, a mutation run before the cut, one hard phase at most | the series' terms | — |
| [D19](#d19) | The board keeps each role's executor, model, effort and tokens from that role's newest `verdicts` line in any run, beside the verdict its findings file holds | a role absent from the newest run would show a verdict with blank fields | the newest run's lines alone |
| [D20](#d20) | An event's day is one on when its clock steps back `12` hours or more from the event before; amended by [D25](#d25) | `run.py` holds this rule | — |
| [D21](#d21) | A run log's name that is no real date and time is no log, in `runlog`, for the conductor as for the viewer; a `-N` suffix on a real stamp stays a log | the name stops the viewer's whole project today | — |
| [D22](#d22) | `kept.repos` raises `Broken` on a link, a FIFO, a bad byte or a file over `262144` bytes; the page keeps `ui.toml`'s projects and says in one line that `repos` could not be read; a missing file is no recorded project | a broken kept file never reads as its permissive answer | silence |
| [D23](#d23) | Of the event details the conductor writes only the cause suffix moves; a spawn's `model`, `effort` and `executor`, the phase, `limited until`, a worker log's stamp and `tasks.md`'s ticks stay in the viewer | their writers are station code | — |
| [D24](#d24) | `docs/recipes.md` gains the recipe "a new fact on the board" | the series promises it | — |
| [D25](#d25) | One day rule, in `runlog`: between two events any step back of the clock is a day on; the first event is a day on only when its clock is `12` hours or more earlier than the time in the log's own stamp | `12` hours between events dates a quiet gap of that length a day early; the viewer's pinned side is on purpose | `12` hours between events |
| [D26](#d26) | The mutation run's readings are settled each on the side nearest today's behaviour unless a row here turns it, those turned in phase 4 alone | the series' rule of readings | — |
| [D27](#d27) | A new test over `1` s carries `slow`; a case that reads a FIFO in a child with a timeout carries it | in this repository a test over `1` s is `slow`, and `make check` runs none | — |
| [D28](#d28) | No `Verify:` runs `tests/test_conduct.py` as a whole file: it names the conductor set with `-n auto` | the plan check stops a command at `600` s | — |
| [D29](#d29) | `statuslog` gains `runs`, the spent text and the `verdicts` line's writer and parser; `runlog` gains an event's moment and the cause's parser; `statefile` gains `lines`; `kept` gains `repos`; the viewer calls them | one module a format, its writer beside its parser | a converge type in the home |
| [D30](#d30) | The run log's bound is the line's cut, narrowing [D14](#d14): the viewer streams the log whole through `statefile.lines`, each line cut at `262144` characters | a read of the first bytes would drop the newest events, a read of the last would lose a midnight | `statefile.read(limit=)` on the log |
| [D31](#d31) | The viewer keeps `stage_of`, `default_branch`, `open_versions`, `primary_of`, `Stop`, `_claim`, `_build_halt`, `_progress`, `_rating` and `_maybe` of the conductor and `CAP` of converge; nothing of `conduct.py` changes | its own code and the tests read the borrowed names | editing the conductor |
| [D32](#d32) | The lists after this version: the entries the move empties leave in phase 3 and 4, none is added, both loads stay | a listed entry the tree no longer holds fails the structure test | — |
| [D33](#d33) | A heading is the module's: the newest run, its number and its mark come from `statuslog.runs` | the viewer shows the older run as the newest today | the viewer's regex |
| [D34](#d34) | `fixing` and a `verdicts` line are events of the module's form | today the first non-blank line under the matched heading is searched, an older run's too | a text search of a line |
| [D35](#d35) | A line of `repos` is stripped and a blank one skipped; a NUL byte, a relative line and a linked `.minions` are no project; the page's line is a row named `repos` built in a function a test reaches | `record_repo` writes a resolved absolute path alone | a line in `serve` or `poll` |
| [D36](#d36) | A recorded path whose `.minions` is a link is no project, `ui.toml`'s paths too; a path through a linked parent folder still lists | every opener of the home refuses a link at `.minions` | — |
| [D37](#d37) | Phase ratings: the pin, the module, the readers and the record moderate; the fix hard | phase 2 adds functions with no caller, phase 4 changes right sides in `runlog`, `kept`, `statuslog` and the viewer | — |
| [D38](#d38) | A changed or added line that only an error path reaches gets its test in the same phase, the test running the real path | the gate wants full coverage of changed lines and runs at the close | a test at the end |
| [D39](#d39) | The region's slow sets are named in a task's `Verify:` from phase 3 on: the viewer, module, converge, conductor and pins sets | conductor tests broke late in `kept` | the whole file |
| [D40](#d40) | The acceptance the plan queued carries the same sets and the gate, and each reading phase 4 turns is pinned by a named test of `tests/test_viewer_pins.py` | a fix that changes a reading breaks that test at its verification | — |
| [D41](#d41) | `statuslog.runs` holds no date and no clock | the heading's date and each event's clock are a later version's | — |
| [D42](#d42) | The person confirmed the planner's rows and the queue; the narrowing of [D14](#d14) by [D30](#d30) stands | the settled table | — |
| [D43](#d43) | Decided by the cutter: `projects` takes a record of None as no record and raises `Broken`, `snapshot(now, record, rows, memory, read)` ticks the entries and puts the `repos` row first, and phase 4 splits the kept change from the viewer's | [D35](#d35) names a function a test reaches but no inputs, and `projects` cannot list `ui.toml`'s projects once the record raises | a `projects` that returns a pair, which changes the asserts of `tests/test_viewer.py` |

### D1

A phase 3 task changes the line that reaches a moved name in a test, never an assert. The conformance check holds it on the phase's diff.

### D2

Carried from the series. The viewer's one `.minions` site leaves the layout list in phase 3, through `layout.run_dir`.

### D3

The viewer keeps its loads and the station logic they bring. Its format reads leave the loaded scripts.

### D4

Carried. `statefile.lines` is this version's one new read: no link, no block, a regular file alone, each line cut at the caller's length.

### D5

Carried. The viewer's `status_log.md` entry leaves the format list in phase 3, its `## Run` entry in phase 4.

### D6

Carried. The viewer spells neither `# Ship run` nor the event clock; `runlog` reads both.

### D7

`ui.toml` and `read_config` stay as they are. A test plants no link at `ui.toml`.

### D8

Carried. The viewer reads the queue through `queue.entries` and `queue.is_wait`, and `repos` through `kept.repos`.

### D9

Carried. `kept.repos` takes the bound `REPOS_BOUND` in phase 4.

### D10

Carried. `kept.repos` raises `Broken` as the kept files do, from phase 4.

### D11

Carried. Every `Verify:` here that runs more than one test file carries `-n auto`.

### D12

This version is the viewer alone. The status log's every run lands here, not in the metric scripts' version, per [D19](#d19).

### D13

Each divergence of the series is read by this rule in [the readings](#the-readings-settled). The pin holds today's side and phase 4 turns it.

### D14

The viewer's `os.open` goes. A bounded read of a status log, a findings file and the claim stays `read_part`, which calls `statefile.read` with a limit.

### D15

Not in this version.

### D16

The status log's parsers land in `statuslog`, the run log's in `runlog`, the record's in `kept`, the stream in `statefile`.

### D17

Both loads stay on the lists of `tests/test_structure.py` and in the viewer's header comment.

### D18

Carried. The terms of this version are in the brief's close, not in the change.

### D19

`statuslog.runs` lands in this version, amending the series' split. The viewer's `converge_of` reads a role's spent fields from the newest `verdicts` event of any run, newest run first.

### D20

Amended by [D25](#d25); phase 2 and phase 3 keep the viewer's own rule, a step back of any size is a day on.

### D21

Phase 1 pins that `20261399-250000.md` passes the pattern and is newest; phase 4 turns it. A real stamp with a `-N` suffix stays a log.

### D22

The row is shaped as a project, named `repos`, its `unread` holding the words `repos could not be read` and the phrase of the `Broken`. The poll goes on.

### D23

These lines stay in `viewer.py`: `SPAWNED`, `PHASE`, `LIMIT`, `TIMESTAMP` and `SUBTASK`, each with its caller.

### D24

The recipe's steps are the module's parser, the viewer's projector, the page, the test.

### D25

Phase 2's `timed` reads as the viewer does; phase 4 changes the first event only. The case: a first event of `00:00:01` in a log stamped `23:59:00` is on the next day, and one three hours before the stamp stays on the stamp's day.

### D26

The readings are in [the readings](#the-readings-settled). A reading not turned there is kept as phase 1 pins it, through phase 4.

### D27

`tests/test_viewer_pins.py` marks a FIFO case and the long-line case `slow`, each in a child with a timeout of its own.

### D28

A `Verify:` that runs the conductor's tests names the set of [D39](#d39).

### D29

Where each function lands is [the table below](#where-each-thing-lands).

### D30

The run log is the one file the viewer reads whole. A status log, a findings file and `repos` are read through the first `262144` bytes.

### D31

The viewer's subscripts of `EVENT`, `last_log`, `_cuts` and `_frontmatter` of the conductor, and of `FALLBACK` and `FAILED` of converge, are removed. The conductor's own use of those names stays, and `tests/test_runlog.py` still reads `conduct["EVENT"]`.

### D32

`FORMAT_SITES` loses `status_log.md` in phase 3 and `## Run` in phase 4. `LAYOUT_SITES` loses `.minions`, and `PRIVATE_REACH` drops `_cuts` and `_frontmatter`, in phase 3.

### D33

After phase 4 a line that starts `## Run` is a heading, its number the ASCII digits after `## Run `, None when there are none, its mark the text after the first ` · `. The case: `## Run 3 — 2026-11-03 10:00 · catch-up now` above run 2 shows run 3 with the mark `catch-up now`. A role with no `verdicts` line in run 3 still shows run 2's fields.

### D34

After phase 4 `fixing` is true when the newest run's newest event is named `fix` and its detail starts with `sent`. A `verdicts` line is an event named `verdicts`, its fallback read from the detail's own fields. A findings file that says `verdict: clean` shows `clean` whatever the log holds.

### D35

`projects(record, rows)` keeps returning the list of entries, raises `Broken` for a record that cannot be read, and takes a record of None as no record. A new function `snapshot(now, record, rows, memory, read)` returns the projects the page shows: it ticks the entries of `projects`, or of `projects` over None when `Broken` is raised, and puts the row named `repos` first in that case. The poll of `serve` calls it; the frame, `State` and `skills/mf-ui/page/index.html` do not change.

### D36

The case: `repo/.minions` a link to a folder is no project; a record line under a linked home folder still lists.

### D37

Carried into [tasks](tasks.md): one hard phase, the fix.

### D38

Each task that changes such a line names the line and the test. The case: `kept.repos`' `Broken` for a FIFO, reached in a child with a timeout.

### D39

The sets, named in a task's `Verify:`:

- The viewer set: `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q`.
- The module set: `uv run pytest tests/test_statuslog.py tests/test_status_log_copies.py tests/test_runlog.py tests/test_kept.py tests/test_structure.py -n auto -q`.
- The converge set and the conductor set: the `-k` runs of [tasks](tasks.md).
- The pins set: `tests/test_mark_pins.py` and `tests/test_queue_pins.py`, for a task that edits `runlog`.

### D40

A turned reading's test carries the reading's id in its name: `test_p1_…`, `test_s1_…`, `test_l1_…`, `test_v3_…`.

### D41

Phase 2's `runs` holds each run's number, mark and events alone.

### D42

Carried.

### D43

The cut's own row, written to the brief as `C1`. Tasks 4.2 and 4.3 hold the two halves: the module raises, then the viewer shows the row.

## Where each thing lands

Each function is a module's, and each viewer line it replaces goes in the phase that calls it.

| module | gains | takes | gives | phase |
|---|---|---|---|---|
| `statefile` | `lines(path, cut)` | a path, a length | each line of a regular file, cut at `cut` characters; nothing for a link, a FIFO or a missing file | 2 |
| `runlog` | `timed(stem, lines)` | a log's stem, its lines | each event with its epoch second | 2, 4 |
| `runlog` | `cause(detail)` | a detail | the word after ` · cause ` at its end, lower-case letters and hyphens, else None | 2 |
| `statuslog` | `runs(text)` | a log's text | each run, newest first, a `Section` of number, mark and events | 2 |
| `statuslog` | `spent(models, tokens, fallback)` | plain values | converge's spent text | 2 |
| `statuslog` | `verdicts_line(role, verdict, open_blocking, spent)` | plain values | the `verdicts` detail converge writes | 2 |
| `statuslog` | `verdicts(source)` | a line, then an event | a `Verdicts` of role, executor, model, effort, tokens, fallback, else None | 2, 4 |
| `statuslog` | `FALLBACK`, `FAILED` | — | the fallback words, which move with `spent` and are removed from converge | 2, 3 |
| `kept` | `repos(path)` | the record's path | each line stripped, a blank skipped | 2, 4 |

The spent text is `executor <x> · model <m or default> · effort <e or default> · tokens <n or unavailable>`, then ` · fallback: codex usage limit` for a true fallback, and ` · fallback: codex failed` for any string. Phase 2 reads a `verdicts` line anywhere in its text, as the viewer does; phase 4 reads an event of `statuslog`'s form.

## The cases

Phase 1 writes these into `tests/test_viewer_pins.py`, each green on today's code. A viewer case reaches the code through `project(primary)`, `projects()` or `read_part`; a module case through the module's public functions. Phase 3 re-points the case that calls `read_lines` and the one that calls converge's `_spent`, both names removed there.

**Slice L, the reads and the run log**

- `read_lines` of a folder, drained repeatedly: no lines, and the count of open descriptors in `/dev/fd` is unchanged. The one case that calls `read_lines`, a name removed in phase 3.
- A log of `spawn` then a `halt` line ending in the bytes `\xff\xfe`: `run.last` is the halt with two U+FFFD, and the spawn is a worker.
- A line of `262144` characters with its newline, then a `halt`: `run.last` is the halt and the state `halted`; a last line of `262144` characters with no newline is kept whole.
- A `300000`-character event line then a `halt`: `run.last` is the halt. As a last line with no newline `run.last` is its first `262144` characters. A `524288`-character line then a `halt`: the halt reads. This case runs with a timeout of its own.
- Lines ending `\r\n`: `run.last` holds no `\r`. A lone `\r` between two events splits them.
- `conformance.md` with `open_blocking: ٣` and `round: ٢`, and a `verdicts` line with `tokens ٣`, read as None; the ASCII values read as numbers.
- Logs `<stamp>`, `<stamp>-2` and `<stamp>-10`, each with a spawn: `run.log` ends `-10`, and `started` is the stamp's day plus the line's clock. A stem `20271231-235959-3` starts on 2027-12-31.
- A first event `00:00:00` then `00:00:01`: both on the stem's day. A first event `09:00:00` before a stem's `10:00:00` is on the stem's day.
- Spawns `10:00:30` then `10:00:10`: the second a day on. `10:00:30` twice, `10:00:59` then `10:01:00`, and `10:59:59`, `11:00:00`, `11:00:59`: one day.
- Spawns `11:00:00`, `10:00:00`, `09:00:00`, `23:59:59`, `00:00:05`: days `0`, `1`, `2`, `2`, `3`.
- The JSON text of one spawn holds `"started": <epoch>.0`, a float.
- With a live claim, a log `0001-a · check — gate · start` then `0002-b · check — gate · pass`: `0001-a` shows `gate_running`, and `run.last` is the `0002-b` line.
- A log `0001-a · check` then `0002-b · spawn`: `run.last` is the spawn. A spawn, `0001-a` check, a `run` wait, a spawn, `0001-a` push: `run.last` is the push.
- `runlog.events` over `\r\n` ends, a U+2028 and a `\x0b` inside lines: details `x`, `y`, `w`.
- `runlog.events` of a log of `400` KB: every event, the first and the last present. Of a link, a missing file or a folder: none. Of a bad byte: the detail holds `��`.
- `runlog.newest`: none for a missing or empty folder or a `notes.md`; among `<stamp>`, `-2`, `-10` and `20261102-235959-99` the `-10`; and `20261399-250000.md` passes the pattern and is newest.
- Shapes: a log that is a link, a dangling link, a folder or empty: `run` holds the claim `none`, the log's stem and `last` None, no worker, the state `idle`; no log: `log` None. A FIFO log, in a child for `60` s: as empty, no block. A log over `262144` bytes of short lines is read whole. A claim `active` that is a file, a link to a folder or a FIFO: `run.claim` is `unread`, the log still reads.

**Slice S, the status log, the `verdicts` line and the findings files**

- `## Run 2` with `verdicts — conformance clean · open_blocking 10 · tokens 5`: executor, model and effort None, tokens `5`, fallback false.
- An adversarial line with `fallback: codex failed` before the word `verdicts`: fallback true and executor `codex` today. A line `verdicts — conformance executor · open_blocking 0 · tokens 5`: executor None, tokens `5`.
- `## Run 10 — 2026-11-03 11:00 · grant-x` then `fix — sent R1`: run `10`, mark `grant-x`, `fixing` true. A top line `11:05:00 · round 2 · fix — R1`: `fixing` false. A log whose last line is the heading: run `2`, mark None, no error. A log with no heading whose first line is `fix — sent R1`: run None.
- `conformance.md` `round: 0` and no other round: round `0`; with adversarial `round: 2`: `2`. A heading `## Run 3 — … · catch-up` above `## Run 2 … · amend`: run `3`, mark `catch-up`, `fixing` true.
- A run log of versions halting `· cause plan-text`, `· cause other` and `— worker said cause gate-red`: `plan-text`, `other`, None.
- Converge's `_spent`, removed in phase 3, called through `runpy`: tokens `0` shows `tokens 0`; None shows `tokens unavailable`; fallback true shows `· fallback: codex usage limit`; a string, an empty one too, shows `· fallback: codex failed`.
- `statuslog.is_heading`: `## Run 2 — d` and `## Running` true; `## Notes`, `##Run 1` and `  ## Run 1` false. `newest` keeps a `## Notes` inside a run in its lines. `parse_event` of `done2`, `fix—x`, `Fix — x` and a detail with a line break: None; of `fix —`: an event with an empty detail.
- Module heading shapes, above `## Run 2 — d · amend`: `· catch-up now` reads as the mark `catch-up now`; a trailing space, no date, `## Running` and an empty mark read as mark None; `· a · b` reads `a · b`; CRLF text reads.
- Viewer, the same headings above `## Run 2 — 2026-11-03 09:00 · amend` holding a `verdicts` line: `· catch-up now`, a trailing space, `## Run 3` and `## Running` are not seen, so run `2`, mark `amend` and `fixing` false show; `· catch-up` shows run `3`. A CRLF status log shows run None and `fixing` false, yet its `verdicts` line reads. A newest `## Run 3` with no line above an older run whose top line is `fix — sent`: run `3`, `fixing` false. A newest run with no `verdicts` line above `## Run 1` holding conformance's: conformance shows the older run's model; of two lines of one role the first in the file wins; a model `gpt-6.1-sol-x` reads whole.
- A `status_log.md` that is a link, a dangling link, a folder or a FIFO: the version is `unread` with `conduct: halt — .minions/changes/0001-a/status_log.md is a link`, converge None, the project read.
- A status log with a bad byte alone, or empty: run None, mark None, round from the findings, `fixing` false, the roles' verdicts read. Good text then `262144` `x`: read as normal; `262144` `x` before the good text: as empty. A missing status log: converge None, the version not unread. A CRLF log: run None, the spent fields read.
- A findings file that is a link, a dangling link, a folder, a FIFO, empty, missing, a bad byte alone, CRLF, or whose frontmatter lies after `262144` `x`: that role's verdict and `open_blocking` None, the version not unread, the round from the other file. A good file then `262144` `x`: read. A FIFO file runs in a child, no hang.
- Frontmatter `verdict: "clean"`, `open_blocking: '0'`, `round: "2"`: the verdict is the string with its quotes, `open_blocking` and `round` None.

**Slice P, the projects, the queue row and the borrowed names**

- `projects` over a record path that does not exist and `[row a "First", row a "Second"]`: one entry named `First`. A row `~/p` with `HOME` set and `p/.minions`: the path under that home. A row path that is a link to `a`, and `a/../a`, with the record listing `a`: one entry, the row's name.
- A row `hide = true`: dropped, the record's listing too; `"yes"`, `1` and `false` show. A name `""`, `5`, `["x"]` or None: the folder's name.
- A record of line `a`, `262144` blank lines, line `c`: only `a`. Blanks up to `262141` bytes then `c`: only `a`, `c` cut with no project and no error. A line `  <a> \t`: `a`. Blank lines, `\t` and spaces: none. Lines `b` and `./a/../a` with the working folder `top`: `top/b` and `top/a`. A path twice, with and without spaces: once, in first-listed order, a row first.
- `.minions` a regular file or a dangling link: no project; a link to a folder: a project, by a row and by the record.
- Record shapes: CRLF ends and a leading blank CRLF line read; a bad byte as a line leaves the path; an empty, missing or folder record, a link to a file or a dangling link: none. A line `~/a`: no project. A line `x\x00y`: `ValueError` escapes `projects`. A FIFO record, in a child for `20` s: none, a row still shows.
- A queue entry with `halt` `""`: `cut halted` with halt `""`. `halt` `0`, `waits` `5`, `waits` `["x"]`, no JSON, JSON `[1]` or an empty file: `cut halted`, `the queue entry is unreadable`, waits None. `waits` `""`: `cut`; None: `cut`; `"1 in flight, cap 1"`: `queued`; a halt and a `waits` together: `cut halted`, waits None. An entry with no `halt` key: unreadable.
- Run log lines `10:00:01 · x · converge skipped — plan` then `10:00:02 · y · Converge Skipped — plan`: `run.last` is the first.

**Equivalent mutants, and what a later phase must keep**

- Text mode translates `\r\n`, so no `\r` reaches `rstrip`; the event pattern opens with `^` and ends with `$`, so `search`, `match` and `fullmatch` agree; `runlog._lines` gives `read` no limit, so no tail acts.
- `entry["halt"]` against `.get("halt")`: `queue.entries` returns only an entry with every required key, or a copy of the unreadable one, which holds `halt`.
- `key.lower()` in `findings.frontmatter`: every caller passes a lower-case key.
- A FIFO case runs in a child with a timeout and carries `slow` ([D27](#d27)).

## The readings, settled

Each is settled by [D26](#d26), the divergences of the series answered by [D13](#d13). "As today" is pinned by phase 1, kept by phases 2 and 3 and still true after phase 4. "Turned" is pinned in phase 1 on today's side and changed in phase 4 alone, its case with it.

**Turned in phase 4**

- `S1`, `S2`, `S5`: a heading with a mark of several words, a trailing space, no date or CRLF line ends is the newest run's heading, and `## Running` is a heading with no number; the board shows that run, never the next older one ([D33](#d33)).
- `L6`'s second half: the first event is a day on when its clock is `12` hours or more earlier than the time in the log's stamp ([D25](#d25)).
- `L1`: `20261399-250000.md` is no log; the list and the newest pass it by, and the project reads ([D21](#d21)).
- `P1`, `P2`, `P3`: a `repos` that is a link, a FIFO, a folder, over `262144` bytes, or holds a bad byte or a NUL byte is broken; `kept.repos` raises `Broken`, the page keeps `ui.toml`'s projects and says it in one line, and the poll goes on ([D22](#d22), [D35](#d35)).
- `V3`, `V4`: `fixing` is the newest run's newest event, never a line of an older run and never a halt that holds the words ([D34](#d34)).
- `V6`, `S9`'s second half: a `verdicts` line is an event of the module's form, and the words `fallback: codex failed` before the word `verdicts` mark no fallback ([D34](#d34)).
- `P4`: a relative line of `repos` is no project ([D35](#d35)).
- `P6`: a `.minions` that is a link is no project ([D36](#d36)).

**As today, through every phase**

- `S3`: a status log that is a link, a dangling link, a folder or a FIFO shows its version `unread`, naming the file; the conductor's stage logic says so.
- `S4`: a status log that is empty, a bad byte alone, or whose first `262144` bytes hold no heading reads as no run, with no error.
- `S6`: a role's spent fields come from its newest `verdicts` line in any run ([D19](#d19)).
- `S7`: a findings file that cannot be read, or whose frontmatter lies past the bound, reads as no verdict for its role alone.
- `S8`: a quoted frontmatter value keeps its quotes, and a quoted number is no number.
- `S9`'s first half: `spent` words any string fallback, an empty one too, as `fallback: codex failed`.
- `L2`: a run log that is a link, a dangling link, a folder, a FIFO or empty is still the newest log by its name.
- `L3`, `L4`: the viewer's stream ends a line where a text-mode read does and cuts it at `262144` characters; `runlog.events` splits by `splitlines` and cuts nothing ([D30](#d30)).
- `L6`'s first half: between two events any step back of the clock is a day on, and days add ([D25](#d25)).
- `L5`: a claim that is a plain file, a link or a FIFO reads `unread`.
- `P5`: `hide` hides on a real `true` alone, and a `name` that is no string falls back to the folder's name.
- `P7`: a queue entry that is no JSON, no object, or holds a wrong-typed `halt` or `waits` shows as a halted cut, `the queue entry is unreadable`; `waits` is asked of `queue.is_wait`.
- `V14`: `ui.toml` is read as today.

The words of `S3` for a folder or a FIFO, `S8`, `L3`, `P5` and a queue `halt` of `""` shown as a halted cut look wrong and are left for the person: no decision turns them.

## Tests

The cost of the tests, each count with the command that produced it.

| layer | file | before | after |
|---|---|---|---|
| unit | `tests/test_viewer.py` | `git grep -c -e "def test_" -- tests/test_viewer.py` prints `36` | the same; one call line changes in phase 3 |
| unit | `tests/test_viewer_pins.py` | none | each case of [the cases](#the-cases), counted by `git grep -c -e "def test_" -- tests/test_viewer_pins.py` |
| unit | `tests/test_statuslog.py`, `tests/test_runlog.py`, `tests/test_statefile.py`, `tests/test_kept.py` | their own | one unit case per new function and per turned side |
| unit | `tests/test_kept_pins.py` | its cases of the viewer's reader of `repos` read a bad byte and a mode-0 file as today | those two cases of the viewer's reader raise `Broken` in phase 4; the metrics reader's cases hold |
| unit | `tests/test_structure.py` | the lists of the structure rules | the entries of [D32](#d32) leave in phases 3 and 4 |

- No end-to-end test is added, none runs on an engine: the viewer is a script and a page the tests reach through `project`, `projects` and `read_part` (`T1`).
- Each new test over `1` s carries `slow`; `git grep -c -e "pytest.mark.slow" -- tests/test_viewer.py` prints `14` at the base ([D27](#d27)).
- The cases extend no end-to-end test; a case that needs a git repo with a linked worktree builds it as `tests/test_viewer.py` does, which keeps each case at the lowest layer that can fail (`T2`).
- Tests deleted or merged: none. A case phase 3 re-points keeps its assertions, so no row maps a removed test (`T5`).
- The tests that name a moved name, by `facts.py readers`: `tests/test_viewer.py` for `read_lines`; none for `RUN_HEADING`, `VERDICT` and `SPENT` outside the viewer; no test of `tests/test_converge.py` calls `_spent`.
- A search of the tests for a log name that is no real date finds none outside the cases this version adds, so [D21](#d21) turns no existing test red.

## Dependencies

None.

## Risks / Trade-offs

- The cases are the proof of the move. A case written from the brief's words may pin a side the mutation run did not; the build names the case a mutant needs in the task's commit.
- Phase 4 changes right sides in `runlog`, `kept`, `statuslog` and the viewer, and the conductor reads `runlog` too, so the conductor set runs in it ([D39](#d39)).
- A `repos` that now raises shows one row where the viewer showed nothing; a person with a broken record sees the line, which is the point of [D22](#d22).
- The viewer keeps its loads and the lines of [D23](#d23); the next versions of the series do not remove them.
- The structure test and the map are red between the first viewer task that imports a module and the task that edits the lists and the row, by construction; each phase ends green, which is where the build runs `make check`.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): each phase ends on a green `make check`, the close on a green `make gate`.
