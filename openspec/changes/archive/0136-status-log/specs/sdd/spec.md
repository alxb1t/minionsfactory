## MODIFIED Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge`, `mf-integrate` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root, through `skills/mf-converge/scripts/gate_run.py`, which records a green run in `.minions/gate/<tree>` — the tree, the
dry run's hash, the date and the seconds — and on a later call reuses it when the worktree is clean, its tree is that tree,
and `make -n gate` prints the same lines. A red run SHALL record nothing, and no record SHALL be written through a linked
`.minions/gate` or staged record, and `mf-release`'s gate after its fold SHALL run
fresh. A green run whose record cannot be written or renamed SHALL print `gate: green — unrecorded, <reason>` and exit 0. `gate_run.py` SHALL run `make gate` and its dry run with no `VIRTUAL_ENV` in their environment. On a green run it
SHALL print its summary line alone, holding make's output back; on a red run it SHALL print make's output, then its summary
line. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **WHEN** `mf-build`, `mf-converge` or `mf-release` is about to run the gate for the first time in a session
- **THEN** it prints the output of `make -n gate` first
- **AND** it runs `make gate` from the repository root, never a command it found instead

#### Scenario: The repository has no runnable gate
- **WHEN** the root `Makefile` is missing, has no `gate` target, or its `gate` target prints no command under
  `make -n`
- **THEN** the station halts, naming the root `Makefile`

#### Scenario: A station reuses a green gate on the same tree
- **WHEN** a station's gate ran green on a tree, and a later station gates the same tree, clean, with the same dry run
- **THEN** the later station reuses the record and runs no `make gate`
- **AND WHEN** the tree, the dry run or a file in the worktree differs
- **THEN** it runs `make gate`
- **AND WHEN** `mf-release` gates the tree it folded
- **THEN** it runs `make gate`, whatever stands recorded

#### Scenario: A gate run from a uv environment
- **WHEN** `gate_run.py` runs with `VIRTUAL_ENV` set, and the gate's recipe echoes `VIRTUAL_ENV`
- **THEN** the recipe sees none
- **AND WHEN** the gate is green
- **THEN** `gate_run.py` prints one line, `gate: green — …`
- **AND WHEN** the gate is red
- **THEN** it prints make's output, then `gate: red — …`

#### Scenario: A green gate whose record cannot be renamed
- **WHEN** the gate is green and the record's staged file cannot be renamed over its target
- **THEN** `gate_run.py` prints `gate: green — unrecorded, <reason>`, removes the staged file and exits 0

### Requirement: Converge keeps a status log

`skills/mf-converge/scripts/converge.py` SHALL write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mflib/statuslog.py`, which takes the clock's time, and `skills/mf-converge/scripts/stamp.py` SHALL be the command over it, its arguments, output and exits unchanged. One `stamp.py` call MAY write several events, each its
own line, inserted so the last given is on top; the module SHALL write in one call the events it has with no command
between them. `stamp.py` SHALL exit 2, writing nothing, on a call that gives `done` or `halt` before another event, and on any
event for a run whose top line is `done`, or `halt` naming neither `.minions/debt.lock` nor `.minions/backlog.lock`: an event after
one needs a new `## Run` heading. A `halt` naming a lock takes the events of the converge that resumes it. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `shadow`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor, model and effort the checker's spawn names, `default` where none, and `tokens` its log's
figure or `unavailable`, then ` · fallback: codex usage limit` when the checker fell back. A
`shadow` line SHALL hold `overlap.py`'s line, or a shadow checker's failure. The writer SHALL hold one descriptor of the change's folder, opened with no link followed, across its read of the log, its create and its rename, for every
event and heading and for a new run's log; it SHALL refuse, exit 2 and write nothing, a log that is a link, no regular file, or holds a byte that is not UTF-8; and it SHALL write each run of line breaks in an event as one space. A reader of the log SHALL follow no link, SHALL replace a byte that is not UTF-8, and SHALL take a run as its heading to the next heading, blank lines skipped. The log SHALL NOT be a findings file: no station writes
it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `converge.py` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mflib/statuslog.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: Several events in one call
- **WHEN** `stamp.py` is given the events `round 1 · verdicts — conformance …` and `round 1 · verdicts — adversarial …`
- **THEN** the log holds both lines under the latest heading, adversarial's on top, each with the clock's time

#### Scenario: A round's verdicts
- **WHEN** a round's conformance and adversarial files are read, each written by its worker
- **THEN** the log holds one `verdicts` line for each role, each naming the executor, and the model and effort that role's
  worker was given

#### Scenario: A mailbox checker's verdicts
- **WHEN** conformance ran as a Codex checker the run started itself, no mailbox standing, `gpt-6.1-sol` at `high`
- **THEN** its `verdicts` line ends `executor codex · model gpt-6.1-sol · effort high` and its log's tokens

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A debt and a done in one call
- **WHEN** `stamp.py` is given the events `round 1 · debt — …` and then `round 1 · done — …`
- **THEN** the log holds both lines under the latest heading, `done` on top

#### Scenario: A done given before another event
- **WHEN** `stamp.py` is given the events `round 1 · done — …` and then `round 1 · debt — …`
- **THEN** it exits 2 with `stamp: cannot stamp — done goes last in a call`, and the log is unchanged

#### Scenario: An event after a run's end
- **WHEN** the latest run's top line is a `done`, or a `halt` naming no lock, and `stamp.py` is given an event
- **THEN** it exits 2 with `stamp: cannot stamp — the run ends on <event>: open a ## Run for a new event`, and the log is unchanged

#### Scenario: An event under a lock halt
- **WHEN** the latest run's top line is a `halt` naming `.minions/debt.lock`, and `stamp.py` is given the event `round 2 · debt — …`
- **THEN** the log holds the line under the latest heading, above the `halt`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** a verify round follows a fix that touched no path of the threat model's `## Surfaces`
- **THEN** the round's `fan-out` names both checkers, and the log holds one `verdicts` line for each, and no `by rule` line

#### Scenario: A change folder swapped for a link
- **WHEN** a stamp has read the log and the change's folder is swapped for a link to another folder before it writes
- **THEN** the write lands in the folder the descriptor holds, and the other folder's files are untouched

#### Scenario: A log that is a link or not UTF-8
- **WHEN** the log is a link, or holds a byte that is not UTF-8, and `stamp.py` is given an event
- **THEN** it exits 2 naming the log, and the log is unchanged
- **AND WHEN** the conductor reads a log that is a link
- **THEN** that version halts naming the log, and the run goes on

#### Scenario: A detail with a line break
- **WHEN** a halt's detail holds git's stderr, with line breaks, and ends with its head
- **THEN** the log holds the event on one line, the breaks written as spaces, and the halt's re-run reads the head from its end

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or start with `.minions/`, unless the test lists the file and the name. No string constant outside `skills/mflib/layout.py` SHALL contain `.mf-ship-origin` or equal `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, and the test SHALL list no such site. No string constant outside `skills/mflib/` SHALL equal `status_log.md` or contain `## Run`, unless the test lists the file and the name. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands, state paths and formats SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

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
