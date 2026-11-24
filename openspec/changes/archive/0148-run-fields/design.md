# Run fields — design

A build's phase, the load, a halt's cause and the gates' lines join the run log, and its readers show them; the line shape stays. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The run log is one line per event: `<HH:MM:SS> · <who> · <event> — <detail>`. A reader takes a spawn's station as the text before the first ` · `, and matches a halt from its start, so a field placed right after the station or at the end of a line is read by every reader as it stands.

The conductor writes spawn and finish lines in `Run.worker`, the converge script's pair in `Run.conducted`, and halts in `Run.halt`, `Run.final` and the direct writers of the closing line and a crash. Converge writes no run-log line: its `Host` protocol has no method for one, and its gates leave an exit in a command log.

## Goals / Non-Goals

- Goals: each fact a measurement read by hand is a field of the log; the viewer and review metrics show them.
- Non-Goals: a catalogue metric over a cause or a phase; a retry, wait or halt rule that reads a field; a new event name.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A build spawn line names its phase right after the station word | every reader takes the station before the first ` · ` | a phase at the line's end · a new event |
| [D2](#d2) | Every spawn and finish line ends with the 1-minute load, left out where it cannot be read | the load is in no log, and reds and slow tests follow it | `plan_check.py`'s `load_average`, which reads a failure as 0.0 |
| [D3](#d3) | Every halt line ends with a cause word from a fixed list, given where the halt is written | a cause is free text, classed by hand in each measurement | a cause argument at each call site of `Run.halt` · a cause in the status log |
| [D4](#d4) | The conductor logs a gate's start; converge logs each gate it runs through a new host method | the viewer shows nothing while a gate runs, and converge's gates have no seconds | a start line from converge · a gate event |
| [D5](#d5) | The viewer, review metrics and the metrics script read the fields as stated | a field no reader shows is not seen | a metric over causes in the catalogue |
| [D6](#d6) | The tests that pin a line's end follow the new ends, with the load fixed | the lines' ends are asserted in many tests | removing an assertion |
| [D7](#d7) | The fields are recorded as D90 and four ADDED requirements | `A7`: a decision in force is edited where it lives | modifying the whole run-log requirement |

### D1

`Run.spawn` and `Run.worker` take a keyword `phase`, `None` by default, and the spawn line reads `<station> · <phase> · model …` when it is given. The build loop gives `phase N` for a numbered phase and `close` for the close; `Run.gate_built` gives `repair`. A rescue, a supervisor, a release, an integrate, a checker and the probe give none, so their lines stay as they were.

### D2

`conduct.py` reads the load in `_load_tail`: `os.getloadavg()[0]` as ` · load <n>`, one decimal, and an empty string when the read raises `OSError`. It ends the spawn and finish lines of `Run.worker` and the converge script's pair in `Run.conducted`. `plan_check.py`'s `load_average` keeps serving the gate's wait: it returns 0.0 on failure, so it cannot tell an unread load from a calm one.

### D3

`CAUSES` in `skills/mflib/runlog.py` is the list: `plan-text`, `gate-red`, `check-red`, `worker`, `limit`, `probe`, `merge`, `cut`, `amend`, `cap`, `human`, `release`, `run`, `other`. `cause_suffix` returns ` · cause <word>` and raises on a word off the list, so a typo is found by a test. `cause_of` in `conduct.py` classes a halt by its words, the first row that holds winning. The rows that anchor on a reason's start come first, so a worker's text quoted after `check fail` cannot win a later row:

| the reason | cause |
|---|---|
| starts `cut-halted` | `cut` |
| starts `converge check fail — the status log halts:` | the class of the text after it by the rows below that hold words, else `other` |
| starts `<stage> check fail — gate:` or `<stage> check fail — gate red after the repair`, or `integrating — red gate`, or `integrate check fail — integrate halted — red gate` | `gate-red` |
| starts `<stage> check fail — plan check` | `plan-text` |
| starts `release check fail`, `released —` or `git push origin` | `release` |
| starts `integrate check fail` or `integrating —` | `merge` |
| starts `human —` | `human` |
| starts `probe` and holds `limited until` | `limit` |
| starts `probe`, or holds `cannot write the probe mark` | `probe` |
| starts `<stage> check fail`, any other | `check-red` |
| starts `conduct.py failed`, or the halt is the run's own | `run` |
| holds `usage limit` or `limited until` | `limit` |
| holds `worker exit`, `timed out after`, `asked for a tool` or `left no findings file` | `worker` |
| holds `amend needed` | `amend` |
| holds `cap reached`, or starts `re-plan` | `cap` |
| holds `verify: halt` | `plan-text` |
| holds `the gate is red` | `gate-red` |
| none of these: `waiting —`, a rescue's diagnosis, a missing worktree, converge's own precondition texts | `other` |

`Run.halt` writes the reason and the suffix, and `self.halts` keeps the bare reason, so the closing line, the `needs` text and the rescue read what they read before. `Run.final` ends with the cause of its first reason, and the early crash's line ends ` · cause run`. The closing summary line, written from `Run.closing`, and the person's stop line, written by the run log's own module, carry none.

### D4

`_run_gate` says `check — gate · start` before each gate run it starts, the rerun after a load wait included, so the viewer's last line of the version is the start until a pass or a fail follows. `Run.logged(change, event, detail)` writes one run-log line, and `Host.logged` in `converge.py` is its protocol method. Converge times each gate itself and writes `check — gate · pass · <n>s` or `check — gate · fail — red · <n>s` at its gate sites: before round 1, after the fix, after the pickup, each fixer pass and the close. A reused record is written as any pass, with converge's own seconds, as the conductor writes one; converge writes no start line.

### D5

The viewer gives each worker a `phase`, and each version a `gate_running` that is true while its last line of the newest log is a gate start and the run's claim is live, and a `cause` read from its last halt line; the page shows them. Review metrics matches each build log to its spawn line by the stamp and the ordinal the log name holds, and books the log's cost under that line's phase, `None` for an older line with none or a log with no spawn line of its ordinal. `scripts/metrics/run.py` reads a spawn's station, a halt's start and a finish by patterns the suffixes leave whole, so it changes in its tests alone: its fixtures hold lines with the fields.

### D6

Tests that pin a spawn, finish, halt or gate line change their expected end or order; none is removed. `tests/test_conduct.py` and `tests/test_claim.py` fix `os.getloadavg` with an autouse fixture, so a line's load is known. A test of the load itself sets its own read.

### D7

`docs/decisions.md` gains D90 after D89, and the delta adds requirements to `sdd`, each naming its title once. The existing run-log and gate requirements are not modified: a line with more fields still holds what they say.

## Tests

The change adds unit tests only, each named in [tasks](tasks.md). It adds no end-to-end run and no browser run, and each runs under 5 s with no `slow` marker, save `test_a_running_gate_is_the_versions_last_line` and `test_a_halt_shows_its_cause` of `tests/test_viewer.py`, marked `slow` as their neighbours are. The tests a file holds are counted by `git grep -c -e "def test_" -- <file>`, read before the build and after it.

| test file | what it holds for the change |
|---|---|
| `tests/test_conduct.py` | the phase, the load, the cause and the gates' lines, and the lines' ends turned |
| `tests/test_claim.py` | the whole spawn and finish line with the load |
| `tests/test_runlog.py` | the cause list and its suffix |
| `tests/test_converge.py` | the host method and converge's gate lines |
| `tests/test_viewer.py` | the phase, the running gate and the cause |
| `tests/test_review_metrics.py` | a build's cost by phase and its table |
| `tests/test_metric_scripts.py` | the metrics script over lines with the fields |

| removed or merged test | carried by |
|---|---|
| none | none |

## Dependencies

None.

## Risks / Trade-offs

- A cause is classed by a reason's words: a new halt text classes `other` until a row is added. A test per row holds the table.
- A reused gate record reads as a short pass in converge's lines, as it does in the conductor's.
- The `gate_running` flag is true only at a start line, which converge never writes: a gate inside converge shows as the converge worker running.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the writers come first, the gates' lines need the host method before converge writes them, and the readers follow the writers.
