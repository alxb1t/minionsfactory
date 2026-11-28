# Metric scripts — design

The metric scripts and the price table read their formats through the home, and the home gains the pieces they need. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`scripts/metrics/run.py` and `scripts/metrics/debt.py` parse the run log, the status log, the findings, `build.done` and the debt file with regexes of their own; `run.py` and `skills/mf-review-metrics/scripts/review_metrics.py` each parse `skills/mf-review-metrics/prices.toml`. The home already holds a parser for each of those formats, written for the conductor and the viewer, and it answers differently from the scripts on a clock, a heading, a mark, a card, a head and a debt line. Where a script and the home disagree on a file of today's format, the home's answer is the answer ([D12](#d12)); a form of an old run, and the `## Refused` spelling a checker still slips into, is read by `eras.py`, never by a station ([D5](#d5)).

```
  run.py ──▶ runlog.logs · statefile.lines · runlog.timed          the run log
         ──▶ layout.status_log · statuslog.read · runs · blocking   the status log
         ──▶ findings.read · cards · refuted                        the findings
         ──▶ marks.done_head                                        build.done
         ──▶ debtfile.read · count                                  the debt file
         ──▶ prices.rows                                            prices.toml
         ──▶ eras.blocking · eras.refuted                           the old forms
  debt.py ─▶ debtfile.read · count
  review_metrics.py ─▶ prices.rows                                  its prices lines alone
```

The mutation run of the region left mutants alive; phase 1 pins each on today's side, so a phase that re-points a script shows exactly which answer it turned. Here the move is the turn: the home answers differently, so phases 3 and 4 change right sides, and the asserts that change are listed in [the turns](cases.md#the-turns) and no others ([D12](#d12)).

The build's per-phase CHANGELOG entry says, for phases 3 and 4, each side the phase turned; no task writes it, and no task runs the gate, which the close runs.

## Goals / Non-Goals

- **Goals:** one parser per format on the metric side; the home gains `runlog.logs`, `statuslog.blocking`, `findings.refuted`, `prices.py` and `eras.py`; each turned reading is listed and tested; the entries of the two scripts leave the structure test's format list.
- **Non-Goals:** the list in [the proposal's last section](proposal.md#not-in-this-change) — worker logs, the proposal's `debt:` list, git calls, the rest of `review_metrics.py`, and a corpus case for `run.py` and `debt.py`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `runlog` gains `logs(runs)`, and `timed` passes by a line whose clock is no time of day | the scripts need every log, and one bad line costs every metric of every version today | a script's reach into the private listing; widening `parse`, which the conductor reads as it does |
| [D2](#d2) | `statuslog` gains `blocking(event)`, the count of a `verdicts` line | `Verdicts` has no count, and the viewer's pins compare that tuple whole | a wider `Verdicts` |
| [D3](#d3) | `findings` gains `refuted(text)`, the refuted section's entries | nothing in the home parses `## Refuted`, and a card is the module's | a copy in `run.py` |
| [D4](#d4) | A new `skills/mflib/prices.py` gives `rows(path)` and `Unreadable` | one file parsed in each script, neither safe on a bad file | a parser in each script |
| [D5](#d5) | A new `skills/mflib/eras.py` reads the old forms, read-only, and no conductor or station loads it | the metrics keep reading old eras, and a listed format site in a reader hides a new copy | old forms in the live modules |
| [D6](#d6) | `run.py` reads the run log through `runlog.logs`, `statefile.lines` and `runlog.timed`, and keeps its own `Event` | one day rule, one file list, nothing blocks | its own reader of each log over a glob |
| [D7](#d7) | `run.py` reads the status log through `layout.status_log`, `statuslog.read`, `statuslog.runs`, `statuslog.blocking` and `eras.blocking` | one heading, one mark, one round | its regexes |
| [D8](#d8) | `run.py` reads the findings through `layout.findings_file`, `findings.read`, `findings.cards` and `findings.refuted`, else `eras.refuted` | a card is the module's; `## Refused` files stop being gaps | its card cut |
| [D9](#d9) | `run.py` reads `build.done` through `marks.done_head` | the mark's own bound and strict read are every reader's | its `head:` regex |
| [D10](#d10) | `debt.py` and `Version.debt` read and count the debt file through `debtfile` | one count of a card, one read | the script's own card pattern |
| [D11](#d11) | `run.py` and `review_metrics.py` take the price table from `prices.rows`; `review_metrics.py` changes in its prices lines alone | one parser; the rest of the file is 5e3's | the whole file in this version |
| [D12](#d12) | The move is the turn: an assert changes only in a case [the turns](cases.md#the-turns) lists for its phase, and phase 1 types each fixture in the home's form | where reader and module disagree on today's format the module's answer holds; an unlisted change is a regression | an unchanged-assert move, which the home's answers rule out |
| [D13](#d13) | Each entry of `run.py` and `debt.py` leaves `FORMAT_SITES` in the phase that empties it, and the module map changes with the imports | the structure test fails on a listed entry the tree no longer holds and on a row that differs from a file's imports | one edit at the end |
| [D14](#d14) | A changed or added line that only an error path reaches gets its test in the same phase, and a new test over 1 s carries `slow` | the gate wants every changed line covered, and `make check` runs no `slow` test | a test in a later phase |
| [D15](#d15) | The test sets are fixed, each command over more than one test file carries `-n auto`, and no `Verify:` expecting nothing from a search names a path a later phase edits | the plan check stops a command at 600 s; an earlier version halted on a search of a path the next phase made call the new functions | `make check` as a phase's proof |
| [D16](#d16) | The sub-task that edits `review_metrics.py`'s prices lines carries `**CORPUS**` `review-metrics`; the sub-tasks of `run.py` and `debt.py` carry none | `scripts/corpus.toml` holds no case that runs either script, and a new case is scope the brief did not settle | a new case |
| [D17](#d17) | The record: the recipes name `prices.py` and `eras.py`, the threat model lists them, and D83's list of accepted breaches loses `run.py` | each says what is true after | leaving the lists stale |

### D1

`skills/mflib/runlog.py` gains `logs(runs)`: every run log of a folder, public, oldest first by `order`, a name that is no real date and time left out. A name with a `-N` suffix on a real stamp stays a log.

`timed` passes by a line whose clock is no time of day — an hour of 24 or more, a minute or a second of 60 or more — as it passes by a line `parse` rejects. `parse` and `events` keep reading a clock of `25:00:00` as an event: the conductor's reads do not change.

A case: `runlog.timed("20261105-100000", ["25:00:00 · x · spawn — build"])` yields nothing. A case for the exemption: `runlog.parse("25:00:00 · x · spawn — build")` is an event. The viewer shows the events around such a line, where it raised before.

### D2

`skills/mflib/statuslog.py` gains `blocking(event)`: for an event named `verdicts` whose detail starts with the role `conformance` or `adversarial`, the number after the detail's first ` · open_blocking `; None for any other event and when no such number stands.

No verdict word and no spent tail are needed. `Verdicts` and `verdicts` stay as they are.

### D3

`skills/mflib/findings.py` gains `refuted(text)`: the top-level `- ` lines of the refuted section, None when the text holds no such heading.

The heading is the first line that starts with `## Refuted`. The section runs from it to the next line that starts with `## `, or to the end; a last line with no newline is included.

### D4

`skills/mflib/prices.py`, new: `rows(path)` is the `[models]` table as a row of numbers by model. A row that is no table, or holds a price that is no number (a bool is none), is left out.

`Unreadable`, raised with a reason, covers a missing file, a link, a pipe, a folder, a file over 262,144 bytes, text that is no TOML and a `models` that is missing or no table. The reasons are those of [the turns](cases.md#the-turns): `it is a link`, `it is not a file`, `it is over 262144 bytes`, the system's text for a missing file, the decoder's or the TOML parser's text, and `no models table`.

A bad row is no row, so one bad row costs its own model's price alone.

### D5

`skills/mflib/eras.py`, new, reads and never writes. `blocking(event)` is the count of a `verdicts` event of an old form: a detail that starts with the role `review` or `security` and holds ` · open_blocking N`, or a detail that holds `open_blocking: N`. `refuted(text)` is `findings.refuted`'s section under the heading `## Refused`.

No conductor and no station loads it; `scripts/metrics/run.py` does from phase 3, and `review_metrics.py` from 5e3. The old forms are the status logs on disk with the old roles and the one colon form. The `## Refused` spelling is a checker's slip that new adversarial files still carry; converge refusing such a file is for the next ship fixes, and with `eras` no recorded value moves.

### D6

`run.py` takes the logs from `runlog.logs`, a log's lines from `statefile.lines(log, 262144)` and each event's moment from `runlog.timed`. It keeps its own `Event` record — `stamp`, `at`, `who`, `name`, `detail` — built from each pair, `at` being `datetime.fromtimestamp` of the moment.

`STAMP`, `EVENT`, `MIDNIGHT`, `_logs` and `_events` are removed. It covers `Version.events` and everything read from it, and exempts `_versions`, the `start` line's `versions` detail, and every other detail the conductor writes, which stay in `run.py`.

A case: beside a good log, a `20261399-250000.md` is passed by and the metrics read. A case for the exemption: `versions none` still names no version.

### D7

The path is `layout.status_log`, the text `statuslog.read`'s and the runs `statuslog.runs`'. A log `statuslog.read` refuses is the gap a missing log is today, `no <change>/status_log.md`.

- `rounds` is the highest round of an event in a run whose mark is neither `catch-up` nor `amend`.
- `grants` and `amends` count the runs whose mark is `grant` or `amend`, the module's mark whole.
- `blockers` takes the oldest run that holds an event of round 1 named `verdicts` and sums each such event's count, `statuslog.blocking`'s or else `eras.blocking`'s; no count is the gap of today.

The rule of which run counts, and that counts are summed, is the metric's own and stays. A case: the lines of isekai's `0037` give 2 through `eras`. A case for the exemption: a newer run's count is still ignored when an older run holds a round-1 `verdicts` line with none.

### D8

The path is `layout.findings_file`; the text is `findings.read`'s, where None and an `OSError` are both the gap `no <change>/<role>.md`; the cards are `findings.cards`'.

`Version.cards` stays the one place that gaps without a refuted section: it takes `findings.refuted`, else `eras.refuted`, and None from both is the gap `no ## Refuted in …`, so `confirmed`, `per_confirmed` and `escapes` gap with it. A card is confirmed when `word("Verdict")` is `confirmed`; a card's text for `escapes` is its `lines` joined with newlines. `PRIORITY` and `CONFIRMED` are removed; `REPEAT` and `ROLES` stay.

`paid`, the proposal's `debt:` list, has no home and stays. A case: `- **Verdict:** Confirmed` under a titled card counts. A case for the exemption: `debt: []` still reads as one card named `""`.

### D9

`build.done` is `marks.done_head(primary, change)`; None is the gap `no head in <change>/build.done`. The mark's own read holds: a file over 65,536 bytes, a bad byte, a link and a doubled `head:` line are each no head; `head:` followed by two blanks, a tab or nothing before the digits is a head.

The git calls after it stay. A case: a `build.done` with two `head:` lines is a gap. A case for the exemption: a head that is no ancestor is still the gap `… is not in the version's history`.

### D10

`debt.py` and `Version.debt` read the file with `debtfile.read` and count with `debtfile.count`, the second by the change's section. Each asks `is_file()` first, so a missing file, a dangling link, a folder and a pipe stay what they are: `debt.py` exits with `no <file>`, `Version.debt` is the gap `no .minions/debt.md`.

A file `debtfile.read` then refuses, a link to a regular file, raises `debtfile.Unreadable` out of `debt.cards`; `debt.py`'s `__main__` turns it into the exit `no <file>: <reason>` and `Version.debt` into the gap `no .minions/debt.md: <reason>`. `CARD` is removed.

`debt.py`'s git call still ends in a traceback outside a repository. A case: `- **0023·a**` with no ` — ` is no card, so `test_the_backlog_is_read_from_the_primary_run_directory`, which types such lines and expects 2, has them retyped as `- **0023·a — x**` and `- **0024·b — y**` and keeps its 2. A case for the exemption: a missing file is still `no .minions/debt.md`, never 0.

### D11

`run.py`'s `_priced`, which stays, and `review_metrics.py` take the table from `prices.rows`, imported as `import mflib.prices`; each keeps its own `PRICES` path, which the tests set.

In `run.py` an `Unreadable` is the gap `prices: <reason>`, and a model with no row or a row that lacks a key it needs the gap `no price for model <model>`. In `review_metrics.py` `_prices` is removed and its test call sites are re-pointed at `prices.rows`, imported from `mflib` in the test file; an `Unreadable` escapes as the exceptions of today do, its meaning there being 5e3's; a model with no row stays None.

The price arithmetic and the usage counts stay in each script, so what a float, a negative or a bool count is worth is as today. `review_metrics.py` changes in its prices lines alone: its call sites, some of which bind a local named `prices`, so the module is reached as `mflib.prices`. A case: `_codex_spent` calls `mflib.prices.rows(PRICES)`. A case for the exemption: its own run-log, status-log and card readers and its list entries stand.

### D12

A phase that re-points a script changes right sides in the same step, so there is no phase that moves with every assert unchanged. In phases 3 and 4 an assert of `tests/test_metric_pins.py` changes only in a case [the turns](cases.md#the-turns) lists for that phase, and no assert of `tests/test_metric_scripts.py`, `tests/test_review_metrics.py` or `tests/test_run_dir_finders.py` changes at all.

Phase 1 types every fixture in the home's form — a whole event line, a full `verdicts` line, a titled card — but where the odd form is the shape under test, which the case's key says. The exemptions are the typed text of the one test [D10](#d10) names and the lines of `tests/test_review_metrics.py` that call the private prices reader, whose call alone changes.

A case: the case of a clock stepping back one minute turns from -1.0 minutes to 1439.0 in phase 3. A case for the exemption: the cost test of `tests/test_metric_scripts.py` passes unchanged in both phases.

### D13

`FORMAT_SITES` loses `run.py`'s `## Run`, `status_log.md` and clock pattern in phase 3, and `run.py`'s `- **` and `build.done` and `debt.py`'s `- **` in phase 4, each in the phase that empties it. No entry is added; the four readers' entries fall to those of the viewer and `review_metrics.py`.

`docs/modules.md` changes with the imports, in the phase that adds the import, since the structure test reads it and runs at the phase's `make check`: phase 2 adds the rows of `eras.py` and `prices.py`; phase 3 makes `run.py`'s row `eras.py, layout.py, runlog.py, statefile.py, statuslog.py`; phase 4 makes it `debtfile.py, eras.py, findings.py, layout.py, marks.py, prices.py, runlog.py, statefile.py, statuslog.py`, `debt.py`'s `debtfile.py, layout.py`, and adds `prices.py` to `review_metrics.py`'s.

The row of a new module lists what it imports; `eras.py` imports `statuslog.py`, `prices.py` imports `statefile.py`.

### D14

A changed or added line that only an error path reaches gets its test in the same phase: the task that changes it names the line and the test. It covers every such line of `run.py`, `debt.py`, `review_metrics.py` and the new and changed home modules, and exempts a line a phase only moves.

A new test over 1 s carries `slow`: a phase 1 case that reads a FIFO in a child with a timeout does, a case that types one status log and calls `run.measure` does not.

### D15

- The metric set: `uv run pytest tests/test_metric_scripts.py tests/test_metric_pins.py tests/test_run_dir_finders.py -n auto -q`.
- The module set: `uv run pytest tests/test_runlog.py tests/test_statuslog.py tests/test_findings.py tests/test_marks.py tests/test_debtfile.py tests/test_prices.py tests/test_eras.py tests/test_structure.py -n auto -q`.
- The viewer set, since `runlog.timed` changes: `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q`.
- The review set: `uv run pytest tests/test_review_metrics.py -q`.

No `Verify:` runs `tests/test_conduct.py`. A `Verify:` that expects nothing from a `git grep` names no path a later phase edits; the closing sub-tasks of phase 5 are the exception, which run after the last edit.

### D16

`scripts/corpus.toml` holds no case that runs `run.py` or `debt.py`, and each needs the change's environment and a version's run data a case cannot give. The cut therefore marks no sub-task of either; the one case that reads the same run directory, `review-metrics`, marks the sub-task that edits `review_metrics.py`.

The measure of the old eras ran both parses over the repositories' run directories in a scratch clone and found no file on which the new parse raises, so the real-data check the corpus gives has been made once for this version.

### D17

`docs/recipes.md`'s reader recipe names `prices.py` and `eras.py`; `THREAT_MODEL.md`'s list of the home gains both and says `eras.py` is read-only and loaded by no station; D83's *Accepts* line loses `run.py` and keeps `review_metrics.py`. A sentence that stays true is not edited.

## Tests

The change adds tests at the unit layer and one layer above: subprocess runs of `debt.py` and of a FIFO read in a child. No end-to-end test and no browser run is added, so no engine count applies (rule `T1`). Each new test over 1 s carries `slow` ([D14](#d14)).

| file | layer | what changes |
|---|---|---|
| `tests/test_metric_pins.py` | unit, subprocess | new: the cases of [the cases](cases.md#the-cases), today's side in phase 1, the listed asserts turned in phases 3 and 4 |
| `tests/test_runlog.py` | unit | cases for `logs` and for `timed` passing by a clock that is no time |
| `tests/test_statuslog.py` | unit | cases for `blocking` |
| `tests/test_findings.py` | unit | cases for `refuted` |
| `tests/test_prices.py` | unit | new: `rows` and each reason of `Unreadable`, a pipe in a child with a timeout |
| `tests/test_eras.py` | unit | new: `blocking` and `refuted` on the old forms |
| `tests/test_viewer.py` | unit | one case: the page shows the events around a `25:00:00` line |
| `tests/test_metric_scripts.py` | unit | the typed lines of one test retyped; no assert changes |
| `tests/test_review_metrics.py` | unit | the lines that call the private prices reader call `prices.rows`, imported from `mflib`; no assert changes |
| `tests/test_structure.py` | unit | the entries of `run.py` and `debt.py` leave `FORMAT_SITES` |

No test is deleted or merged, so the `I16` table is empty. The tests the change adds are counted at the close with `git grep -c -e "def test_" -- tests/test_metric_pins.py tests/test_prices.py tests/test_eras.py`.

## Dependencies

None.

## Risks / Trade-offs

- **The turns are many.** Many asserts turn across phases 3 and 4. Each is listed in [the turns](cases.md#the-turns); the conformance check holds the list on each phase's diff, and an assert changed outside it is a finding.
- **Phase 3 is the one hard phase.** It re-points the run log and the status log and turns the day rule, the heading, the mark and the old forms; its halves are separate tasks, each green on its own.
- **Local time.** `datetime.fromtimestamp` of a moment `runlog.timed` made from a naive local time may differ at a DST fold; no case sets a zone, as the viewer's.
- **A clock set back.** Between two events any step back of the clock is a day on, as [the spec delta](specs/sdd/spec.md) says, so a run log that crosses the end of summer time dates every event after the step a day on, and a stage's minutes that span it read about a day long. Accepted, per Q279 ([the cases](cases.md), R7): the old bound of 12 hours dates a quiet gap of over 12 hours a day early — a halt at 11:00 answered at 09:00 the next morning — the viewer already reads a step back as a day on, and no log on disk steps back by less than 12 hours.
- **`prices.Unreadable` escapes `review_metrics.py`.** A bad price table raises there, as a bad one does today; its meaning is 5e3's.
- **No corpus case reads `run.py` and `debt.py`.** [D16](#d16) records why; a regression on real data shows at the next release's collect.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin, the module, the logs, the files, the record.
