# Status log — design

The staged write, the no-follow read and the status log each get one home module, and every script that wrote or parsed them takes it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The status log, `.minions/changes/<change-id>/status_log.md`, is written by `stamp.py` and by converge's `open_run`, and parsed by the conductor's readers and by converge. The viewer, the review metrics and `scripts/metrics/run.py` parse it too, and wait for the readers' version. Each copy keeps its own idea of where the newest run ends, what its mark is, what an event is, and what a halt on the debt lock is.

The staged write — clear `<name>.tmp`, create it `O_EXCL`, rename it over the file — stands in the writers of `stamp.py`, `bundle.py`, `debt_match.py`, `open_cards.py`, `skip_stub.py`, `gate_run.py` and `plan_check.py`. The copies disagree on a link at the target and on a `.tmp` left behind. The no-follow read stands in `stamp.py`, converge's `_text`, the conductor's `_bounded` and the viewer's `read_part`, each with its own bound, and `skip_stub.py` reads the file it replaces by a plain read.

The shared home is `skills/mflib/`, born with the port and grown by the layout module. This change adds the first format modules. The method is the series': pin the region, move it, fix it in a phase of its own ([D2](#d2), [D3](#d3)).

## Goals / Non-Goals

Goals:

- `skills/mflib/statefile.py` writes a staged file and reads a regular file that follows no link; `skills/mflib/statuslog.py` writes and parses the status log; `skills/mflib/layout.py` names the log's path.
- Every writer of a staged file and every reader of the log takes them, and the copies' disagreements are settled to one side each ([D4](#d4), [D5](#d5), [D6](#d6)).
- Card 0109·S1 is paid: the writer holds one folder descriptor across its read and its write ([D7](#d7)).
- The gate holds the format names ([D9](#d9)), and the record agrees ([D12](#d12)).

Non-Goals:

- The viewer's, the review metrics' and `scripts/metrics/run.py`'s parsers of the log: they wait for the readers' version ([D11](#d11)).
- The card, the debt file, the run log, the claim, the marks and the home files: each has its own version.
- The conductor's bound on a read of the log, and the survivors in converge's consumers of events ([D11](#d11)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Home modules `statefile.py` and `statuslog.py`, standard library only; the layout names the log's path (brief Q99, Q74, Q121) | one writer and one parser per format; the pin carries `skills/mflib/` | a Python package; one module for both |
| [D2](#d2) | Phase 1 pins the region first: the cases of [the pin](#the-pin), each green on today's code and red on the mutants that survive it (brief Q23, Q25, Q126) | a refactoring needs a net the move cannot slip through | a pin written after the move |
| [D3](#d3) | A difference between copies is an argument of the module until phase 5; the move changes no assert (brief Q4, Q26, Q97) | a checker can judge a pure move; a move mixed with a fix it cannot | one right side chosen in the move |
| [D4](#d4) | The write's right side: one mechanism; the staged file removed on any failure; a link at the target refused for the change-folder writers; a green gate's unwritten record is green and unrecorded (brief Q100, Q122) | all copies already write through no link; `gate_run.py` renames outside its `try`, so a failed rename reads as red | refusing a link at the gate's or the plan check's store |
| [D5](#d5) | The read's right side: one read that follows no link, does not block and takes a regular file alone; the bound is the caller's; a parser replaces a bad byte and the writer refuses it; the conductor's readers follow no link (brief Q101, Q103, Q123) | the threat model says no read of the conductor's follows a link; a FIFO at the log hangs it today | one bound for every caller |
| [D6](#d6) | The log's right sides: a run runs from its heading to the next heading, blank lines skipped; the mark is the text after the heading's first ` · `, stripped, `None` when absent; an event is one pattern with an optional detail; a `done` ends a run whatever it names, a `halt` leaves it open only when it names a debt lock; one predicate says a halt names a debt lock (brief Q102, Q124, Q125) | the extent a design states (0084); what the writer writes | the extent that stops at a blank line |
| [D7](#d7) | The writer holds one folder descriptor across the read, the create and the rename, for every stamp and for `open_run`; card 0109·S1 is paid here (brief Q104) | since 0108 converge runs in the conductor's process, so every stamp is of the card's class | a pathname write with a check before it |
| [D8](#d8) | The writer flattens a detail's line breaks to one space and refuses no event outside the spec's form (brief Q105) | a halt that carries git's stderr puts its head on a later line, which can be neither re-run nor answered | a refusal of an event outside the form |
| [D9](#d9) | The sixth structure rule gains a third kind, a format name: outside `skills/mflib/` no string constant equals `status_log.md` or contains `## Run`, unless `FORMAT_SITES` lists the file and the name (brief Q106) | exact for these two names; the marks and the event names are many and foreign | a rule on the marks or the event names |
| [D10](#d10) | `stamp.py` stays, a thin command over `statuslog.py`: its arguments, output and exits as they are (brief Q99) | no worker prose runs it, and its exits are designed and pinned | removing the command |
| [D11](#d11) | Left out: the viewer's, the metrics' and `run.py`'s parsers; the conductor's bound on a read; the survivors in converge's consumers of events (brief Q99, Q101, Q127) | one region a version; the bound is card 0120·S4's | moving the readers now |
| [D12](#d12) | The record agrees: D78, D83 and D57 amended where they live; the status-log and gate requirements; the threat model; the map; the recipe (brief Q99, Q106) | the series' fifth end-state fact | leaving the record to a later version |
| [D13](#d13) | The conductor's readers and `_restamp` keep their names and become wrappers over `statuslog.py`; converge's `stamp`, `open_run` and `latest` do the same; `Event` and `Run` move to the module | the tests reach those names, and a move changes no line by which they do | deleting the wrappers |

### D1

`statefile.py` holds `write`, `read_bytes`, `read` and `folder`. `statuslog.py` holds the title and the create, the heading and its mark, the event and its names, a run, the newest run, the stamp and the debt-lock predicate. `layout.py` gains `STATUS_LOG` and `status_log(primary, change)`. Each module imports `layout` and `statefile` as `from . import …`, and no script's private name crosses a file.

### D2

The pin is tests only and runs green before any code moves. A case for each difference of [the differences](#the-differences) is its own test, so a move that drops one fails it. [The pin](#the-pin) lists the cases and the file each lives in.

### D3

[The differences](#the-differences) names each argument, who passes which value, and what phase 5 does with it. The module's tests hold every value; the stations' tests hold their callers. Phase 5 deletes an argument and its branch, and turns the cases that held two values to the one.

### D4

The staged file is `<name>.tmp` beside the target, cleared before the create, created `O_EXCL | O_NOFOLLOW`, and renamed over the target. After the fix it is removed on any failure, and the helper raises `WriteFailed` with the step and the `OSError` for the caller to word.

A green gate whose record cannot be renamed exits 0, unrecorded, instead of reading as red.

### D5

The read opens the path `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, refuses what is no regular file, and takes a bound and a tail as arguments. A link or a FIFO raises `OSError`, `ELOOP` or `EINVAL`; a missing file raises `FileNotFoundError`.

The conductor's readers turn a link or a FIFO into `Stop(1, "conduct: halt — <path> is a link")`: the version thread's handler halts that version, and `main`'s handler prints it for `status` and `report`. The writer refuses a log that is not UTF-8 with exit 2.

### D6

After phase 5 `newest` has no `extent` argument, and a run is its heading to the next heading with blank lines skipped. A run just opened, with no event yet and an older run below, reads as a run of no event: `_run_end` names its own heading, so `stage_of` shows `unfinished run: ## Run …` for the new run, not the old. The answers to a missing log stay: no run to the conductor, a run of no event to converge, exit 2 to `stamp.py`. `_restamp` keeps its fallback to round 1.

### D7

After phase 5 `stamp`, `command` and `open_run` take an optional `folder` descriptor and read, create and rename through it. Converge and the conductor hand in `statefile.folder(run_dir, CHANGES, change)`, each part `O_DIRECTORY | O_NOFOLLOW`; with none given, the module opens the log's parent by pathname, making nothing, and holds it. The other sinks of the card's class are paid as their formats move.

### D8

Each run of line breaks in an event becomes one space before the writer writes. The re-run of a halt reads its head from the end of the one line.

### D9

`FORMAT_SITES` lists `(file, name)` pairs and only shrinks; a listed pair the tree no longer holds fails the rule. The pair `("stamp.py", ".minions/")` leaves `LAYOUT_SITES` in the phase that removes `LOCKS`.

### D10

`stamp.py` imports `statuslog` after the seed line its folder fixes. It prints each written line and, on a refusal, `stamp: cannot stamp — <reason>` with exit 2.

### D11

Left out is not forgotten: [the proposal](proposal.md) names the trigger of each.

### D12

Cards that cite a moved line are re-pointed by converge where it reads the diff, not by a task, because `.minions/debt.md` is written under its lock by converge and the release alone (decided as 0134's was). The release deletes card 0109·S1, which [D7](#d7) pays.

### D13

A wrapper keeps its name, its arguments and its return, and reads the file itself: the conductor's `Path.read_text()` until phase 5, `statefile.read` after. `_restamp` and converge's `stamp` call `command`, so the printed lines and the exit stay the same. The map rows follow the imports.

## The modules

The names a task may use. A function's docstring holds its example.

| module | name | does |
|---|---|---|
| `statefile.py` | `write(path, text, *, refuse_link, remove, folder, mode)` | stages `<name>.tmp`, renames it over `path`; raises `WriteFailed` |
| `statefile.py` | `read_bytes(path, *, folder, limit, tail, guard)` | the bytes of a regular file, no link followed; `OSError` on a link, a FIFO or a missing file |
| `statefile.py` | `read(path, *, folder, limit, tail, guard)` | `read_bytes` decoded, a bad byte replaced |
| `statefile.py` | `folder(root, *parts)` | a descriptor on `root`'s folder `parts`, each made, none read as a link |
| `statefile.py` | `WriteFailed` | holds `step` — `create` or `replace` — and `error` |
| `layout.py` | `STATUS_LOG`, `status_log(primary, change)` | the log's name, and its path in the change's folder |
| `statuslog.py` | `Refused` | the writer's reason; the command prints it |
| `statuslog.py` | `Event`, `Run`, `Block` | an event's round, name and detail; a run's mark and events; a heading and its lines |
| `statuslog.py` | `NAMES` | the spec's event names, in its order |
| `statuslog.py` | `title(change)`, `create(log, change)` | the log's first line; the create that passes when the log stands |
| `statuslog.py` | `heading(number, now, mark)`, `mark_of(heading)`, `marked(heading, mark)` | a run's heading; its mark; whether it is `mark` |
| `statuslog.py` | `is_heading(line)`, `parse_event(line)`, `is_event(line, name)`, `ends(line)` | whether a line is a run's heading; an event of a line; whether a line is `name`; `done` or `halt` for a line that ends a run |
| `statuslog.py` | `newest(text, *, extent)`, `latest(text)` | the newest run's heading and lines; converge's `Run` of it |
| `statuslog.py` | `names_lock(text)` | whether a halt names the debt lock or its old name: it tests `str(layout.debt_lock(Path(".")))` and `str(layout.backlog_lock(Path(".")))`, which spell no `.minions` |
| `statuslog.py` | `insert(text, events, run, mark)` | the pure step: the log's lines with the new lines inserted, and those lines; raises `Refused` |
| `statuslog.py` | `stamp(log, events, run, mark)`, `open_run(log, change, mark)` | reads the log, calls `insert`, writes it; opens a run, creating the log and its folder |
| `statuslog.py` | `command(log, events, run, mark)` | what the stamp command does: stamps, prints each written line, or prints `stamp: cannot stamp — <reason>` and returns 2 |

## The differences

Each row is an argument of a module until phase 5. A value not named in a row's today column is no caller's.

| argument | of | values and who passes them today | after phase 5 |
|---|---|---|---|
| `refuse_link` | `statefile.write` | true: `bundle.py`, `debt_match.py`, `open_cards.py`; false: `stamp.py`, `skip_stub.py`, `gate_run.py`, `plan_check.py` | true for `stamp.py` and `skip_stub.py` too; false stays for the gate's and the plan check's stores |
| `remove` | `statefile.write` | `any`: `bundle.py`, `debt_match.py`, `open_cards.py`; `rename`: `stamp.py`; `never`: `skip_stub.py`, `gate_run.py`, `plan_check.py` | deleted: every caller removes on any failure |
| `guard` | `statefile.read_bytes`, `read` | false: the stamp's read, which blocks and takes any file; true: the rest | deleted: every read is guarded |
| `extent` | `statuslog.newest` | `blank`: converge's `latest`; `heading`: the conductor's `_run_started` and `_buried_done`; `line`: the conductor's `_run_end` and the stamp's top line | deleted: the extent is `heading` |

Pairs of functions hold the other differences, and phase 5 makes one answer of each. `mark_of` takes the text after the first ` · ` as it stands, and `marked` tests the heading's end after dropping trailing blanks. `parse_event` needs a round and a ` — `, and `is_event` and `ends` split the line at its first ` — ` and test the name's end.

`skip_stub.py`'s read of the file it replaces is no row: it stays its plain read, which follows a link, until phase 5 moves it to `statefile.read`. Every value of `guard` opens with `O_NOFOLLOW`, so no argument keeps case A's link row in the move.

## The pin

Each case is a test named `…_case_<letter>_…`, green on today's code and red on every mutant it names. A case over the staged writes is a table over `stamp.py`'s `write`, `bundle.py`'s, `debt_match.py`'s, `open_cards.py`'s, `skip_stub.py`'s, `gate_run.py`'s `write_record` and `plan_check.py`'s `keep`.

| case | asserts, as the code stands | file |
|---|---|---|
| A | each staged write clears a stale `.tmp` that links outside the folder; the target holds exactly the text, the outside file is untouched, no `.tmp` stands | `tests/test_staged_writes.py` |
| B | each staged write refuses a file that appears at `.tmp` between the clear and the create, with `os.open` patched | `tests/test_staged_writes.py` |
| C | each staged write leaves the target a new file of mode 0644; a hard link to the old file keeps the old text | `tests/test_staged_writes.py` |
| D | each staged write whose rename fails — the target is a folder — ends as it does today: `stamp.py`, `bundle.py`, `debt_match.py` and `open_cards.py` refuse and leave no `.tmp`; `skip_stub.py` refuses and leaves it; `gate_run.py` raises `IsADirectoryError` and leaves it; `plan_check.py` is silent and leaves it | `tests/test_staged_writes.py` |
| E | `gate_run.py` answers `tree.tmp could not be created` when the staged file cannot be made | `tests/test_gate_run.py` |
| F | `plan_check.py`'s `keep` writes nothing into a linked store folder, and swallows a store folder that is a file | `tests/test_plan_check.py` |
| G | `skip_stub.py` reads the file it replaces with a bad byte replaced | `tests/test_skip_stub.py` |
| H | on a byte that is not UTF-8, the stamp's `read` and the conductor's `_run_end` raise; converge's `_text`, the conductor's `_bounded` and the viewer's `read_part` replace it | `tests/test_log_reads.py` |
| I | the bounds as literals: the stamp's `read`, `_text` and `_run_end` have none; `_bounded` reads 65,536 bytes and gives `None` at 65,537; `read_part` reads 100,000 bytes whole | `tests/test_log_reads.py` |
| J | `_bounded(path, fd)` reads relative to the folder `fd` holds | `tests/test_conduct.py` |
| K | `stamp.py --run` on an empty log exits 2; a heading right under the title is kept | `tests/test_stamp.py` |
| L | the stamp's run end: the top event is found past a blank line; a `done` that names the lock refuses, a `halt` that names it does not; `predone` ends nothing | `tests/test_stamp.py` |
| M | converge's `latest`: round 12, an empty detail, a blank line or a heading ends the run, no mark is `None`, a dangling link raises the stamp's `Stop` | `tests/test_converge.py` |
| N | converge's `HALTED` is anchored at the end; `statuslog.names_lock` needs `.minions/` | `tests/test_converge.py` |
| O | `stage_of`: `.minions/debt.lock` gives the lock stage, a bare `debt.lock` stays halted — a twin line of the existing `stage_of` test | `tests/test_conduct.py` |
| P | converge's `stamp` and `open_run`: a refused stamp raises `Cannot` with today's message; runs are counted by heading line; a linked log raises the stamp's `Stop` | `tests/test_converge.py` |
| Q | the conductor's readers: the line stripped, a link followed, a missing log `False`, the exact ` · mark` with trailing blanks dropped, ` · event`, a run read past blank lines | `tests/test_conduct.py` |
| R | `_buried_done`: the newest heading to the next heading, blank lines skipped, a `done` on top buries nothing | `tests/test_conduct.py` |
| S | `_restamp` keeps a two-digit round, and uses round 1 when none is named | `tests/test_conduct.py` |

Beside them, a case for each difference the mutants do not reach, in `tests/test_status_log_copies.py`: a link at the log in the stamp, converge and the conductor; an event outside the spec's form in the stamp and in converge; a missing log in each of them; a halt whose detail holds a line break. A FIFO planted at the path given to converge's `_text` and to the viewer's `read_part` fails inside ten seconds, each run in a thread the test joins with a timeout, so a dropped `O_NONBLOCK` is a red test and no hang.

## Tests

The change adds tests at the lowest layer: unit cases over a module or a script's function, with `tmp_path` files and a patched clock. It adds no end-to-end test (`T1`) and no test that boots a browser. One test starts a run, `test_a_refused_status_log_at_the_start_halts_its_version_alone` of `tests/test_conduct.py`: it runs over five seconds and carries the `slow` marker.

| file | layer | adds | turns in phase 5 |
|---|---|---|---|
| `tests/test_staged_writes.py` | unit | cases A–D over the staged writes | the ends of D and the link row of A |
| `tests/test_log_reads.py` | unit | cases H, I and the two FIFO cases | H's strict rows |
| `tests/test_status_log_copies.py` | unit | the cases the mutants do not reach | each case whose copies differed |
| `tests/test_statefile.py` | unit | each argument of `statefile.py`, with `os.open` reached through the module | the deleted arguments' rows |
| `tests/test_statuslog.py` | unit | each function of `statuslog.py`, each `extent`, and card 0109·S1's swapped parent | the deleted `extent` rows |
| `tests/test_stamp.py`, `tests/test_converge.py`, `tests/test_conduct.py`, `tests/test_gate_run.py`, `tests/test_plan_check.py`, `tests/test_skip_stub.py`, `tests/test_layout.py` | unit | the rest of the cases of [the pin](#the-pin) | the rows whose copies differed |
| `tests/test_structure.py` | unit | the format rule's cases | none |

No test is deleted or merged. A test the change turns keeps its name and its scenario; its assert moves to the one side, and the phase that turns it says which. The count of tests comes from `uv run pytest --collect-only -q`, which the build's last phase prints and the release's metrics record.

## Dependencies

None.

## Risks / Trade-offs

- Phase 3 moves the stamp, converge and the conductor together; the pin of phase 1 is the net, and no assert changes in the move.
- A wrapper per reader keeps every test line, and leaves a thin function the conductor could drop when its station table arrives.
- The module holds each difference as an argument from phase 2 to phase 5. The cost is dead branches until phase 5, in exchange for a move a checker can judge.
- The conductor's readers follow no link after phase 5: a version whose log is a link halts where it ran on before, which is the threat model's own rule.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): pin, modules, stations, helpers, fix, rule and record.
