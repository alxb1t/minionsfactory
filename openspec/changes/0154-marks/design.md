# Marks — design

One module holds every mark of a change folder, behind a pin, and a fix gives each side of the copies' disagreements one answer. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A **mark** is a file of `.minions/changes/<change-id>/` that a station leaves for the run: `build.done`, `build.halt` and the rest of [D2](#d2)'s list. The conductor reads, writes and removes most of them in `skills/mf-ship/scripts/conduct.py`; `skills/mf-integrate/scripts/integrate.py` tests one, `skills/mf-converge/scripts/converge.py` reads two, `skills/mf-release/scripts/release.py` writes and reads three, and `scripts/metrics/run.py` reads `build.done` a second way.

```
today                                    after
conduct.py  ─ reads, writes, removes     conduct.py  ─┐
integrate.py ─ stand test                integrate.py ─┤
converge.py  ─ reads build.done,         converge.py  ─┼─▶ skills/mflib/marks.py ─▶ layout.py, statefile.py
               plan-check.txt            release.py   ─┘
release.py   ─ reads, writes, removes    run.py, viewer.py: their own read stays, listed, until 5e
```

The copies disagree:

- `build.done`, `integrate.red` and `build.halt` each match a `head:` line by a pattern of their own.
- A path reader follows a link and reads a file of any size.
- A stop mark read as absent lets a run go on past a halt.
- One conductor writer truncates in place, through a hard link, and another stages.

The series' rule applies: a move changes no assert, and a fix lands in its own phase behind a pin.

Already in force and relied on: `skills/mflib/statefile.py` holds `read_bytes`, `write`, `open_folder`, `folder`; `skills/mflib/layout.py` holds `change_dir`, `CHANGES`; `skills/mflib/modelsfile.py` is the pattern for a format module.

## Goals / Non-Goals

Goals:

- Each mark's name appears once, in the module; no script outside `skills/mflib/` spells one but `scripts/metrics/run.py`.
- Each mark's text has one writer, and each parsed mark one parser, in the module.
- One read, one `head:` rule and one write for every mark, as [D4](#d4) to [D6](#d6) say.

Non-Goals:

- What a mark means to a run (`stage_of`, the checks, the git resolution of a head) stays in `conduct.py`.
- The commands that write a mark from prose, `build.discarded.patch`, the Makefile's read of `stacked-on`, and the home's folder opens refusing a link at `.minions` (version `roots`).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One module `skills/mflib/marks.py`, on `layout` and `statefile`, holds the marks | the series' shape for a format: one module writes and parses it | a module per mark; the conductor keeps them |
| [D2](#d2) | The module names the marks listed there, once each, and offers the functions of its table | a name spelled twice is a name that drifts | leaving `release.py`'s and `converge.py`'s names where they are |
| [D3](#d3) | Phase 2 holds each copy as it behaves; phase 4 keeps one side | a move changes no assert | fixing while moving |
| [D4](#d4) | One `head:` rule, for the marks that hold one | a pattern a copy today, one crossing a line end | keeping a pattern a copy |
| [D5](#d5) | One read; a broken stop mark halts its version, a broken pass mark is absent | a stop mark read as nothing lets a run go on | reading every broken mark as absent |
| [D6](#d6) | One staged write under the change folder's descriptor; a failed write keeps each caller's answer, `stacked-on` halting its version | a truncating write goes through a hard link | keeping the in-place writer |
| [D7](#d7) | `release.py` goes through the module, its unlinks through the module's remover | a linked change folder is followed there today | leaving `release.py` as another copy |
| [D8](#d8) | The pin is a file of cases written against the conductor first, reaching names as the tests do | the series moves no code without a pin | pinning after the move |
| [D9](#d9) | The format rule gains the marks' names by equality, its list `run.py` | the rule holds the module's one home | a rule over names a message contains |
| [D10](#d10) | No command; the debt stays; the marks that have no reader keep a name or nothing | the version that first calls a command is later | a thin command now |
| [D11](#d11) | Phase 4 turns the cases and pins of its table, name and fixture kept | a pin that turns keeps its history | deleting a pin and adding another |

### D1

`skills/mflib/marks.py` imports `layout` and `statefile` and nothing else of the repository. It is a file of the home, so `docs/modules.md` gets a row for it and the threat model's `skills/mflib/*` surface already covers it.

### D2

**The names.** One constant a mark: `BUILD_DONE`, `BUILD_HALT`, `BUILD_CLOSING`, `BUILD_SIMPLIFIED`, `BUILD_NOTES`, `STACKED_ON`, `CUT_HALT`, `CUT_RED`, `INTEGRATE_MD`, `INTEGRATE_RED`, `INTEGRATE_SETTLED`, `INTEGRATE_RESOLVED`, `RELEASE_HELD`, `RELEASE_FLAG`, `RELEASE_PRE`, `RESCUE`, `REPLAN`, `PLAN_CHECK` and `GATE_RED`, each equal to the file's name, and `discarded(n)` building `release.discarded.<n>.patch`. `BOUND` is `65536`, `NOTES_BOUND` is `1048576`.

**The functions.** Each takes the primary checkout and the change id; the ones that read raise `Broken` (a `ValueError` with a phrase) where [D5](#d5) says.

| function | does | replaces |
|---|---|---|
| `read(primary, change, name, bound=BOUND)` | the one read of [D5](#d5); `None` for a missing file; written in phase 4 | the path readers |
| `stands(primary, change, name)` | a boolean that never raises: a regular file stands; in phase 2 as `is_file()` does, a link to a file standing, and in phase 4 by `lstat`, a link not | the `is_file()` stand tests |
| `standing(primary, change, name)` | the stand test of a stop mark: `True` for a regular file, `False` for none, `Broken` for a link, a pipe, a folder or a dangling link; written in phase 4, where the stop marks' stand sites take it | the stand tests of `integrate.md`, `integrate.red` and `release.held` |
| `present(primary, change, name)` | anything stands at the name, no link followed (`os.path.lexists`) | the `release.flag` and `replan.mark` tests |
| `gate_red_text(primary, change)` | `gate.red`'s text, as the close reads it back; in phase 4 `''` for a file that cannot be read, a bad byte or one over `NOTES_BOUND` among them | the read of the close's gate step |
| `head_of(text)` | the one head of [D4](#d4), or `None`; written in phase 4 | each copy's pattern |
| `done_head`, `simplified_head`, `red_head` | the head a mark holds | replaces `_done_head`, `_simplified_head` and the read of the integrate reader |
| `done_lines`, `plan_check_text` | `build.done`'s lines and `plan-check.txt`'s text, as `converge.py` compares them; phase 4 deletes `done_lines` with its unit case for `done_head` ([Tests](#tests)) | `_read`, `_text` at those marks |
| `build_halt(primary, change)` | the `sub-task`, `stop` and `head` of `build.halt`, or `None` | `_build_halt`'s read |
| `stacked_head(primary, change)` | the first word of `stacked-on` when it is 40 hex digits | `_stacked_on`'s read |
| `cutter_halt(primary, change)` | the first line of `cut.halt`, stripped, cut to 300 characters | replaces `_cutter_halt` |
| `release_pre(primary, change)` | the keys of `release.pre`: `tag`, `version`, `gate`, `head` | `release.py`'s `_read_mark` |
| `open_notes`, `note_lines` | `build-notes.md`, opened as today | replaces `_open_notes`, `_note_lines` |
| `mtime(primary, change, name)` | the time in nanoseconds of a regular file, by `lstat`; `None` on any error | replaces `_mtime` |
| `done_text`, `halt_text`, `diagnosis_text`, `head_text`, `stacked_text`, `plan_check_body` | the text of each mark whose form a reader depends on: `build.done`, `build.halt`, `rescue.md`, the `head:` marks, `stacked-on` and `plan-check.txt`'s `base:` line and output | the f-strings |
| `write(primary, change, name, text)` | the staged write of [D6](#d6) | `_write_state` |
| `write_in_place(primary, change, name, text)` | the in-place write of today, until phase 4 deletes it | replaces `_write_in_change` |
| `remove(primary, change, name)` | unlink by name under the folder's descriptor; a missing name is no error | `_remove_in` at a mark |

`release.discarded.<n>.patch`, `cut.red` and `build.closing` have a name and no parser. The text of `gate.red`, `cut.red` and the conductor's `integrate.md` note is free text or output, and stays with its writer.

### D3

In phase 2 each function reproduces the copy it replaces, argument by argument: `done_head` reads by path as `_done_head` did and `red_head` matches `^head:[ \t]*(\S+)`. Each copy's head pattern is private to the module until phase 4 deletes them for [D4](#d4). The phase-2 unit cases hold today's behaviour; the phase-4 task turns them.

The module imports no conductor class. A function that raises a conductor `Stop` today raises `Broken` or `Unwritten` with the same words, and the conductor's caller wraps it in the `Stop` it raised, its message unchanged.

### D4

**One head rule.** A mark has a head when its text holds exactly one `head:` line whose value, the text after `head:` less spaces, tabs and a carriage return, is 7 to 40 lower-case hexadecimal digits; else it has none. The rule covers `build.done`, `build.halt`, `integrate.red`, `build.simplified` and `release.pre`; `replan.mark`'s `head:` line is written and not read.

| mark with no head | answer |
|---|---|
| `build.done` | the build is not done |
| `build.simplified` | absent: simplify runs again |
| `build.halt` | stale, as today |
| `integrate.red` outside a merge | a red gate on another head; inside an open merge today's reading stands: no head is the merge's red gate, a headed one is stale |
| `release.pre` | the caller stops, as it does for a missing or broken one |

`release.pre`'s other keys stay as they are: split at the first colon, stripped, the last of two winning, a line with no colon ignored. A value `HEAD`, a branch name, six digits or two `head:` lines is no head. The plan-output reader of `converge.py` takes `build.done` as naming the frozen head only when `done_head` equals it, so two `head:` lines match nothing.

### D5

**One read.** `read` opens the change folder through `statefile.open_folder` (nothing made), then the file through `statefile.read_bytes` of one byte past the bound, follows no link, does not block, takes a regular file alone, and decodes strictly. A missing file is `None`; a file over the bound is `Broken`, as `modelsfile.py` takes it.

**The classes.** A *stop mark* halts the version when it cannot be read; a *pass mark* is absent when it cannot be read.

| class | marks | a link, a pipe, a folder, a file over the bound or a bad byte |
|---|---|---|
| stop | `build.halt`, `cut.halt`, `integrate.red`, `integrate.md`, `release.held` | halts the version, naming the mark; `conduct.py status` names it and goes on |
| pass | `build.done`, `build.simplified`, `stacked-on`, `plan-check.txt` | absent: the check runs again |
| evidence | `gate.red` | reads as no output: a plain red gate, which drops a simplify commit |
| time only | `integrate.settled` (a pass mark) and `rescue.md` | read for their time by `lstat`, no content, no bound |
| stand only | `replan.mark`, `release.flag` | anything standing there, no link followed, stands: a re-plan spent, a flag a person reads; its text is never read |
| required | `release.pre` | the caller stops, naming it; the conductor's drop test takes it only when `release_pre` reads it whole |
| bound `NOTES_BOUND` | `plan-check.txt`, `gate.red`, `build-notes.md` | as their class; `build-notes.md` keeps its own open and its refusal of a hard link |

An empty `cut.halt` stays a halt. `release.held` stands as a regular file, and a dangling link, a folder or a pipe there halts the version, naming it. The one read takes a hard link. A `gate.red` or `plan-check.txt` written over the bound is written whole, as today, and reads by its class.

**Where `Broken` goes.** The conductor turns a stop mark's `Broken` into a halt of the version, naming the mark and the phrase. `_build_halt`, which the viewer borrows, answers a halt that names the mark, so the viewer shows `halted` and raises nothing. `conduct.py status` prints the phrase after the version's line. The settling test of the integrate script lets `Broken` rise to the script's halt, exit 1, naming the mark.

### D6

**One write.** `write` stages `<name>.tmp` through `statefile.write(refuse_link=True)` under the change folder's descriptor. `rescue.md`, `integrate.md` and `stacked-on` take it; so do the marks `_write_state` writes today and `release.pre`. A failure raises `Unwritten`, which names the mark and the cause; each caller keeps its answer.

| caller | on a failed write |
|---|---|
| `conduct.py`'s close, `_halt_build`, `cut.red`, `gate.red`, `plan-check.txt`, `build.simplified`, `replan.mark` | `Stop(1)`, as `_write_state` says today |
| `Run.diagnose` | a version halt, once, the version left undiagnosed |
| `Run.merge_in` | a `Stop` of the version, code 1, the merge left open |
| `Run.stack` | a version halt, not the whole run |
| `release.py` | a halt of the script naming the mark |

A hard link at the name keeps the other name's text; a folder at the name is the caller's stop.

### D7

`release.py` names `release.pre`, `release.flag` and the saved patches through the module. Its unlinks, in `_restore` and `_again`, take `marks.remove` in phase 4: a missing mark is no error, a folder or a linked change folder is a halt of the script naming the mark. A saved patch's free name is the first `release.discarded.<n>.patch` at which nothing stands, a link not followed: a dangling link is skipped, as a folder and a pipe are. `release.flag` stands in every shape and `release.held` by the rule of [D5](#d5); the module tests both.

### D8

**The pin.** `tests/test_mark_pins.py` holds each case and pin of the tables below, green on the code as it stands.

- A lettered case is a test whose name begins `test_case_<letter>`.
- A pin's name begins `test_pin_readers`, `test_pin_stands`, `test_pin_notes`, `test_pin_cut_halt`, `test_pin_writers`, `test_pin_failed_write`, `test_pin_head` or `test_pin_new_marks`, by its row of the pin table; the loop cases' begin `test_loop_`.
- A case reaches a conductor name by `tests/conduct_load.py`'s key, as `tests/test_conduct.py` does, and `release.py` through its commands.
- A run-level case plants disk state and starts no worker.
- A test that needs a blocking open runs the read in a thread, asserts it has not returned after a short wait, then opens the pipe for writing to free it.
- Phase 3 changes only the line by which a case reaches a name. Phase 4 turns the cases [D11](#d11) lists, each to the one side.

#### The lettered cases

| case | reaches | holds today |
|---|---|---|
| c | `cut.halt` | a link reads as no halt; the line is stripped, then cut to 300 characters; a bad byte is replaced; an empty file is a halt of no words |
| d | `build.done`, the built head | `\s*` crosses a line end; `HEAD`, a branch name and an annotated tag resolve; a pipe or a bad byte reads as none; the built head refuses an off-branch head, no box, an open box, a re-planned change, a side merge and an octopus merge; a merged-back build passes `stage_of` |
| g | `rescue.md` by `Run.diagnose`, `release.held` | the exact text; a failed write halts the version once and leaves it undiagnosed; `release.held` stands as a file or as a link to one |
| h | `build.halt` | a value keeps its inner spaces; the last `head:` wins; a key with no value on its line, or in mid-line, is not read; `head: <sha> x` is stale; the checks and `held` name the sub-task |
| m | `integrate.md` by `Run.merge_in` | the note is written and the merge stays open; a failed write stops the version, code 1; an open merge with a note commits nothing; `_note`'s exact text; `_settled` and `integrate.py`'s `_settling` test the note by `is_file()` |
| n | `build-notes.md` | a link, a hard link, a folder and a pipe each stop the version; lines are counted whole; the trim keeps the lines before the phase and its allowance, and logs it |
| r | `integrate.red` | the first `head:` wins; a head that names no commit is kept raw; outside a merge red on `HEAD` reads integrating, on another head integrate, with no head passes; in a merge a headed red is stale and a folder stands for nothing |
| s | `stacked-on` | a full 40-hex first word alone; the ancestry and the tasks file are checked; `_unstack` removes a dangling link; `Run.stack` writes the head and a newline before it merges; `catch_up` passes a stacked version |
| t | the times | `_mtime` (→ `mtime`) is by `lstat`, in nanoseconds, of a regular file alone, none on any error; `_opened` keeps the settled time; `_settled` passes on a new time alone; the rescue's compare of `rescue.md` |
| w | `_write_in_change` (→ `write_in_place`), `_remove_in` | the write truncates, makes the folder, mode 0644, refuses a link at the mark and at the change folder; `_unstack` raises on a folder |
| x | `build.simplified` | the reader takes the first `head:` word, from the line start or a later line; an empty word, no key, an empty file and a bad byte read as none; `head:` then a newline reads the next line's word, and `head:` then a blank line and `head: z` reads `head:`; a link and a hard link are followed, a dangling link and a folder read as none, a pipe reads as none without blocking; a file over `BOUND` reads whole; the writer writes `head: <sha>` and a newline alone and stops on a link and a folder; the amends-only test passes an empty span, fails a head off the branch or naming no commit, a subject that only begins as the amend subject, a path in a folder that only begins as the change's, a path outside it, and a merge or octopus whose own subject is the amend subject; `HEAD`, the branch name and an annotated tag resolve, `main` does not pass |
| p | `plan-check.txt`, `_text` | converge's reader treats a regular file and a hard link as the kept run, a link, a dangling link, a folder and a pipe as no file, so the plan check runs again; a bad byte is replaced; a file over `BOUND` is read whole; a `build.done` that is a link names no head; `_text` returns the whole text with a byte replaced, none for a missing file, and raises `ELOOP` on a link and `EINVAL` on a folder and a pipe |
| a | `gate.red` | red keeps the whole output, green removes it; `_close_gate` reads the file back: an output naming "past its limit" or "sandboxed: denied" keeps the simplify commit, a near spelling or a bad byte does not, a green gate keeps it |
| l | `replan.mark` | a design cap with the mark standing as a file, an empty file, a link, a dangling link, a folder or a pipe gets no supervisor; with no mark it gets one with `replan=yes`; a standing mark stops no cap that is no design cap |
| b | `_write_state`, `_write_in_change`, `_remove_in`, the `build.halt` removals | `_write_in_change` makes the folder, writes mode 0644, truncates, writes in place through a hard link, refuses a link at the name and at the change folder, raises on a folder, and leaves no descriptor open; `_remove_in` removes a name, a link, a hard link and a pipe by their name, says nothing of a missing name, raises on a folder and on a linked change folder; `_write_state` stages a file and stops with code 1 on a link, a folder and a linked change folder; the repair spawn and the build spawn each find the last build's `build.halt` gone |
| e | `release.py`'s marks | `_read_mark` reads its keys, strips key and value, splits at the first colon, the last of two `head:` lines wins, lines with no colon name no key, a head past `BOUND` reads, a missing, empty or malformed key is a `cannot`, a link, a folder and a pipe cannot be read; `finish` and `merge` halt on a flag of any shape; a release subject with more after it is no release commit; a drop with no flag removes the mark; a restore of a clean tree saves no patch; `_save` numbers past a folder, replaces a dangling link and keeps a binary file |
| o | the conductor's release reads | `release.held` stands as a file, an empty file or a link to a file, not as a dangling link, a folder or a pipe; `release.flag` stands in every shape; a stranded tip drops only under a `release.pre` that is a file or a link to one |

#### The pins

| pin | holds today |
|---|---|
| the path readers of `build.done`, `build.halt`, `integrate.red`, `stacked-on`, `build.simplified` | a link and a hard link are followed; a pipe reads as none with no block; a folder and a bad byte read as none; a file over `BOUND` reads whole |
| `cut.halt` | a link is no halt; a pipe blocks; a folder raises |
| `build-notes.md` | a link, a hard link, a folder and a pipe each stop the version; no bound; the read makes the change folder |
| the stand tests of `release.held`, `integrate.red`, `integrate.md` | a link to a file stands; a dangling link, a pipe and a folder do not |
| the head forms | in each mark that holds a `head:`: `HEAD`, a branch name, six digits, seven, forty zeros, a value on the next line, a second `head:` line, `head: <sha> x` and none, and each caller's answer |
| the writers | `_write_in_change` (→ `write_in_place`) through a hard link; at a link `ELOOP`, at a folder `EISDIR`, at a pipe it blocks |
| a failed write | `Run.diagnose` halts the version, `Run.merge_in` stops it with code 1, `Run.stack` halts the whole run, the close stops with code 1 |
| the marks the conductor gained since the models file | each read and stand test of `build.simplified`, `plan-check.txt`, `gate.red`, `replan.mark` and `cut.red` stands as the table above says |

The cases of the run's loop: `advance` removes `stacked-on` before converge and before the release; `advance` does not close a closed build again.

### D9

The format rule of `tests/test_structure.py` gains the marks' names by equality: outside `skills/mflib/` no string constant equals one of them, its list `scripts/metrics/run.py` until 5e. A message that only contains a name is not held, and neither is a name the module builds. `Run._needs`' action word `rescue.md` becomes the module's constant. The rule lists no exception for the conductor, `converge.py`, `release.py` or `integrate.py`.

### D10

The module offers no command. `integrate.md`'s forms, the Makefile's read of `stacked-on`, and the names `build.closing` and `integrate.resolved`, which get a name and no parser, stay as they are. A card is neither closed nor opened by an edit of this change.

### D11

**What turns in phase 4.** A case or pin of [D8](#d8) turns to the one side of [D4](#d4) to [D7](#d7), its name kept and its fixture kept:

| case or pin | turns to |
|---|---|
| x | a link followed, the next line's word after a bare `head:`, the first of two heads, a file over `BOUND`, `HEAD`, a branch and a tag's name: no head, simplify runs again |
| p | a bad byte and a file over the bound: the plan check runs again; `_text` itself is not touched |
| a | a link at the read, a bad byte and a file over the bound: `gate_red_text` answers `''`, a plain red gate |
| b | `_write_in_change` (→ `write`) through a hard link: the staged write, the other name keeps its text, a folder there the caller's stop |
| e | the last of two heads, a bad byte and a mark over the bound: the caller's stop; a write at a link: a refusal; a dangling link at a patch's name: skipped; a removal through a linked folder: a stop |
| o | `release.held` as a dangling link, a folder or a pipe: a halt of the version naming it; `release.pre` as a link: no whole mark |
| the path readers, `cut.halt`, the stand tests | per [D5](#d5) |
| the head forms | per [D4](#d4) |
| a failed write of `stacked-on` | a version halt |
| l | none |

`build.simplified` keeps the amends test as it is: a merge in the span fails it.

## Tests

The change adds unit tests of the module, pins of the marks in the conductor and `release.py`, and cases of the structure rule. One test is deleted, with the function it holds, in the table below. No end-to-end run is added, and no case starts a worker or a browser.

Each test file's tests are counted by `uv run pytest <file> --collect-only -q`, run at the end of the phase that adds them.

| layer | file | why this layer |
|---|---|---|
| unit | `tests/test_marks.py` | a function of the module on a planted change folder: `T1` |
| unit | `tests/test_mark_pins.py` | a conductor function reached by key, or a `release.py` command, on planted disk state: `T1`; the loop cases call `advance` with the spawns recorded |
| unit | `tests/test_structure.py` | the rule's planted-breach twin and its stale-list case: `T6` |
| unit | `tests/test_conduct.py` | the lines by which a test reaches a name change; no assert does: `T3`, `T5` |

`tests/test_structure.py`'s twins take their own list, as the other rules' do. A pin whose side [D11](#d11) turns is edited in place.

| test deleted in phase 4 | carried by |
|---|---|
| the unit case of `done_lines` in `tests/test_marks.py`, deleted with it | the unit case of `done_head` in `tests/test_marks.py`, whose scenarios are a bare `head:`, two `head:` lines and a head past a line end |

## Dependencies

None.

## Risks / Trade-offs

- The module's phase-2 functions keep each copy's head pattern for a phase, so the module holds a disagreement it was made to end. [D3](#d3) accepts it: the pin is green before the fix.
- A stop mark that halts its version on a broken file is a new halt. A person can read it: `conduct.py status` names the file.
- `release.py` is the module's fourth caller and lives in a station: it loads the home through its seed, as it does the models file.
- This change touches `conduct.py` at about the marks' lines and a rebase against another version that edits them conflicts in the lines [tasks](tasks.md) names; `mf-integrate` settles it.

## Verdict

Ready to build. Phase 1 pins, phase 2 adds the module with no caller, phase 3 moves the callers, phase 4 gives each disagreement one answer, and phase 5 closes the rule and the record.
