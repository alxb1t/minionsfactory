## ADDED Requirements

### Requirement: One module writes and parses the marks of a change folder

`skills/mflib/marks.py` SHALL be the one home of the marks of `.minions/changes/<change-id>/`: `build.done`, `build.halt`, `build.closing`, `build.simplified`, `build-notes.md`, `stacked-on`, `cut.halt`, `cut.red`, `integrate.md`, `integrate.red`, `integrate.settled`, `integrate.resolved`, `release.held`, `release.flag`, `release.pre`, `release.discarded.<n>.patch`, `rescue.md`, `replan.mark`, `plan-check.txt` and `gate.red`. It SHALL name each once, write the text of each mark whose form a reader depends on, and parse or test each mark a script reads. `conduct.py`, `integrate.py`, `converge.py` and `release.py` SHALL go through it; `conduct.py` SHALL keep what a mark means to a run. The module SHALL find the folder through `skills/mflib/layout.py` and SHALL offer no command.

A mark has a head when its text holds exactly one `head:` line whose value, the text after `head:` less spaces, tabs and a carriage return, is 7 to 40 lower-case hexadecimal digits; else it has none. `HEAD`, a branch name, a value on the next line and two `head:` lines are no head. A `build.done` with no head SHALL be no done build, a `build.simplified` with none SHALL be absent, a `build.halt` with none SHALL be stale, a `release.pre` with none SHALL stop its caller, and an `integrate.red` with none SHALL, outside a merge, be a red gate on another head.

The module's read SHALL open the change folder without making it, follow no link, not block, take a regular file alone, read at most `65,536` bytes — `1,048,576` for `plan-check.txt`, `gate.red` and `build-notes.md` — and decode them strictly. A mark that stops a version — `build.halt`, `cut.halt`, `integrate.red`, `integrate.md` and `release.held` — and stands as a link, a pipe, a folder, over the bound or with a byte that is not UTF-8 SHALL halt its version, naming the mark; `conduct.py status` SHALL name it and go on, and the viewer SHALL show the version halted and raise nothing. A mark that lets a run go on — `build.done`, `build.simplified`, `stacked-on`, `integrate.settled` and `plan-check.txt` — that cannot be read SHALL be absent, and the check it holds SHALL run again. A `gate.red` that cannot be read SHALL read as no output, a plain red gate. `rescue.md` and `integrate.settled` SHALL be read for their time alone, by `lstat` of a regular file. `replan.mark` and `release.flag` SHALL stand when anything stands at their name, no link followed, and their text SHALL be read by no script. A missing `release.pre` or one that cannot be read SHALL stop its caller, naming it, and the conductor's drop test SHALL take it only when it reads whole.

The module's write SHALL stage `<name>.tmp` under the change folder's descriptor and refuse a link; a failure SHALL raise to the caller, which SHALL keep its own answer: the conductor's close, the plan check and the gate stop with exit 1, a diagnosis halts its version, an `integrate.md` stops it with exit 1, and a failed write of `stacked-on` halts its version and not the run. A hard link at the mark SHALL keep the other name's text. The module's removal SHALL unlink by name under the change folder's descriptor, say nothing of a missing name, and raise on a folder or a linked change folder; `release.py`'s removals of `release.pre` and `release.flag` SHALL go through it and halt the script naming the mark. A saved patch SHALL take the first `release.discarded.<n>.patch` at which nothing stands, no link followed.

#### Scenario: A pipe at a stop mark
- **WHEN** a pipe stands at `.minions/changes/<id>/cut.halt` and the cut's check reads it
- **THEN** the read does not block and the version halts, naming `cut.halt`

#### Scenario: A link at a pass mark
- **WHEN** `build.done` stands as a link to a file that names `HEAD`
- **THEN** the build is not done and the close runs again

#### Scenario: A head that names no commit
- **WHEN** `build.done` holds `head: HEAD`, or two `head:` lines
- **THEN** it has no head and the build is not done

#### Scenario: A bad byte in `gate.red`
- **WHEN** `gate.red` holds a byte that is not UTF-8 after a red gate that names its limit
- **THEN** the file reads as no output, and the close drops a simplify commit as for any red gate

#### Scenario: A flag in any shape
- **WHEN** `release.flag` stands as a folder, a pipe or a dangling link
- **THEN** it stands, and the release halts before its merge, naming it

#### Scenario: A failed write of `stacked-on`
- **WHEN** the run cannot write `stacked-on` for a dependent
- **THEN** that version halts, and the other versions of the run go on

#### Scenario: A hard link at a mark the conductor writes
- **WHEN** `rescue.md` has a second name and the run writes a diagnosis
- **THEN** the mark holds the new text and the other name keeps its old text

#### Scenario: A dangling link at a saved patch's name
- **WHEN** a dangling link stands at `release.discarded.1.patch` and a restore saves a patch
- **THEN** the patch goes to `release.discarded.2.patch` and the link is left

#### Scenario: A linked change folder at a removal
- **WHEN** `release.py` drops a release commit and the change folder is a link
- **THEN** the script halts, naming `release.flag` or `release.pre`, and removes nothing

## MODIFIED Requirements

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or start with `.minions/`, unless the test lists the file and the name. No string constant outside `skills/mflib/layout.py` SHALL contain `.mf-ship-origin` or equal `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, and the test SHALL list no such site. No string constant outside `skills/mflib/` SHALL equal `status_log.md` or the name of a mark of `skills/mflib/marks.py`, contain `## Run`, contain `# Ship run`, contain the run log's clock, `\d\d:\d\d:\d\d` or `(\d\d):(\d\d):(\d\d)`, or contain `- **` or `- \*\*`, the head of a card, unless the test lists the file and the name; a string that only contains a mark's name, and a name the module builds, are not held. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands, state paths and formats SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

#### Scenario: A load the map does not declare
- **WHEN** a script names a file of another station that its row in `docs/modules.md` does not list
- **THEN** `tests/test_structure.py` fails naming both files, and the gate is red

#### Scenario: A station loads a station
- **WHEN** a station's script names a script of another station and the pair is on no exception list
- **THEN** the loads rule fails naming the pair

#### Scenario: A private name crosses a file
- **WHEN** a script reads `_name` from a file it names and the pair is on no exception list
- **THEN** the names rule fails naming the file and the name

#### Scenario: A cycle
- **WHEN** two scripts name each other and the cycle is on no exception list
- **THEN** the cycles rule fails naming the files of the cycle

#### Scenario: An OS command outside its files
- **WHEN** a script outside the listed files and the port names `caffeinate` or `bwrap`
- **THEN** the OS-command rule fails naming the file and the command
- **AND WHEN** the port names it
- **THEN** the rule passes

#### Scenario: A state path joined outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant equal to `.minions`, or one that starts with `.minions/`, and the file is on no exception list
- **THEN** the state-path rule fails naming the file and the name
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: The home folder's name outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant that contains `.mf-ship-origin`
- **THEN** the state-path rule fails naming the file and the name, whatever the test lists
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: An XDG variable's name outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant equal to `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`
- **THEN** the state-path rule fails naming the file and the name, whatever the test lists
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: A format name outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant equal to `status_log.md`, or one that contains `## Run`, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** a file of `skills/mflib/` holds it
- **THEN** the rule passes

#### Scenario: A card head outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant that contains `- **` or `- \*\*`, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** `skills/mflib/findings.py` holds it
- **THEN** the rule passes

#### Scenario: A run log's name outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant that contains `# Ship run`, or the run log's clock in either spelling, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** `skills/mflib/runlog.py` holds it
- **THEN** the rule passes

#### Scenario: A mark's name outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant equal to `build.done`, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** `skills/mflib/marks.py` holds it
- **THEN** the rule passes

#### Scenario: A message that contains a mark's name
- **WHEN** a script outside `skills/mflib/` holds a string constant that contains `build.done` among other words
- **THEN** the format rule passes

#### Scenario: A load of the home with no seed
- **WHEN** a script under `skills/` imports `mflib` and the statement before that import is not the seed line
- **THEN** the seed rule fails naming the script

#### Scenario: A load of the home from scripts with no seed
- **WHEN** a script under `scripts/` imports `mflib` and no seed line of its depth stands before the import
- **THEN** the seed rule fails naming the script

#### Scenario: A file on no surface
- **WHEN** a Python file under `skills/` matches no glob of the threat model's surfaces
- **THEN** the surfaces rule fails naming the file

#### Scenario: A file with no row
- **WHEN** a Python file under `skills/` has no row in `docs/modules.md`
- **THEN** the map rule fails naming the file
- **AND WHEN** a row names a file that is gone
- **THEN** the map rule fails naming the row

#### Scenario: A stale exception
- **WHEN** a listed exception no longer exists in the tree
- **THEN** the rule that lists it fails naming the exception, so a list only shrinks
