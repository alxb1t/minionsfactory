## ADDED Requirements

### Requirement: One module writes and parses the run log

`skills/mflib/runlog.py` SHALL be the one writer and parser of the run log, `.minions/runs/<stamp>.md`: its title, its event line and the one pattern that reads it, the event list, the order of logs and the newest log, the verify, the stop line, the reads of the release's death, of the rescue and of `report`, and the tail `wait` follows. `conduct.py` SHALL write and read the run log through it, and SHALL keep `EVENT` and `last_log` bound to the module's, which the viewer takes from the loaded conductor. The module SHALL name no state path: its callers find the folder through `skills/mflib/layout.py`.

A run log SHALL be a file of `.minions/runs/` whose name is a stamp, `<YYYYMMDD-HHMMSS>.md`, with a `-<n>` suffix or none; the newest log, the release's death read and `report` SHALL pass over any other `*.md`. An event line SHALL be `<HH:MM:SS> · <who> · <event> — <detail>`, the detail on one line, and the event list SHALL hold `sync` and `codex` beside the others, so `conduct.py log --verify` passes a run that wrote one. The verify SHALL pass an open spawn only when the log's last line is `run · halt — stopped by the person`, and a finish with no spawn SHALL pass.

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

### Requirement: One module writes and parses the claim

`skills/mflib/claim.py` SHALL be the one writer and parser of the claim's entries under `.minions/runs/active`: the take, the conductor's `start` and `pid`, a group's entry named by its leader's pid and holding its start time, the groups, and the removal. `conduct.py` SHALL keep the kill of a group, `ps` and what a stale claim means to a run. The module's reads SHALL follow no link and take each entry by a bound of `4,096` bytes, and its writes SHALL go under the descriptor of the claim folder, opened beneath its parent and never created by a read; a claim whose parent is missing SHALL be no claim, and nothing is made. A bad byte in `pid` or `start` SHALL read as a stale claim, and a group's entry over the bound SHALL be passed over.

A claim that is no folder, a link or a file, SHALL stop each command that reads it, `run` and `stop` among them, naming it, and the viewer SHALL read it as unread. `stop` over such a claim SHALL kill nothing and write no stop line, and a worker started while the claim is no folder SHALL be ended with its group and the run SHALL halt, naming the claim.

#### Scenario: A link at the claim
- **WHEN** `.minions/runs/active` is a link
- **THEN** `run` exits 2 naming it, and the link and its target are unchanged

#### Scenario: A stop over a claim that is no folder
- **WHEN** a person runs `/mf-ship stop` and `.minions/runs/active` is a link
- **THEN** the command exits 2 naming the claim, no process is signalled, and no line is written to the run log

#### Scenario: A claim that becomes a link under a worker
- **WHEN** the claim is replaced by a link after the run took it and a worker has started
- **THEN** the worker's group is ended and the run halts naming the claim

#### Scenario: A bad byte in the claim
- **WHEN** the claim's `pid` holds a byte that is not UTF-8
- **THEN** the claim reads stale, and a run clears it

## MODIFIED Requirements

### Requirement: A person can stop a run

`/mf-ship stop` SHALL end the live run: the conductor, then each worker group in the claim and the claim, then a `halt — stopped
by the person` line in the run log. A group it cannot end SHALL keep the claim, and it SHALL still write that line and
exit 2, naming the group. A claim that is no folder SHALL be no run it can stop: the command SHALL exit 2 naming it, kill nothing and write no line. A re-run SHALL resume from disk, and `conduct.py log --verify` SHALL pass the stopped run. With no live
run it SHALL say so and exit 0.

#### Scenario: A run is stopped
- **WHEN** a person runs `/mf-ship stop` with a worker live
- **THEN** the worker's group is gone, the log's last line is the stop, and `.minions/runs/active` is gone

#### Scenario: A stop meets a group it cannot end
- **WHEN** a person runs `/mf-ship stop`, and a claimed group names no executor or refuses the kill
- **THEN** the conductor is gone, the log's last line is the stop, the command exits 2 naming the group, and the claim stays

#### Scenario: A claim names another process
- **WHEN** the claim's pid is at or below 1, or its process lacks the claim's start time
- **THEN** `status` reads `stale`, and `/mf-ship stop` says no run is live, signals nothing and leaves the claim

#### Scenario: A claim that is no folder
- **WHEN** a person runs `/mf-ship stop` and the claim is a link
- **THEN** the command exits 2 naming the claim, signals nothing and writes no line to the run log

### Requirement: `conduct.py wait` blocks until the run ends

`conduct.py wait` SHALL print `wait: none — no run is live` and exit 0 when no claim is live. With a live claim it SHALL poll the claim every `WAIT_SECONDS` seconds, make no read of `origin` at a poll, and print at each poll the whole lines the newest run log gained since the wait began or the previous poll, read from its offset through the log kept open across the polls of one log, at most `262,144` bytes a poll, then `wait: live · +<n> lines`, `<n>` the lines it just printed, 0 for none. A line longer than that SHALL be passed over whole, nothing of it printed, its tail included. A newer log SHALL be read from its start, and a link or a file that is no regular file SHALL never be read. When the claim is gone or stale it SHALL print `wait: ended` and `status`'s lines, and exit 0, whatever the run's close: a run that halted ends the wait as a run that is done does.

#### Scenario: No run
- **WHEN** no run is live
- **THEN** `wait` prints `wait: none — no run is live` and exits 0

#### Scenario: A run that ends
- **WHEN** a run is live at the first poll, its log gains two lines, and its claim is gone at the next
- **THEN** `wait` prints the two lines, `wait: live · +2 lines`, then `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A run that halts
- **WHEN** a run's log ends in a halt and its claim is gone
- **THEN** `wait` prints `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A poll with no new line
- **WHEN** the run's log gains nothing between two polls
- **THEN** `wait` prints `wait: live · +0 lines` at the second

#### Scenario: A poll reads no origin
- **WHEN** `wait` polls a live run
- **THEN** no remote git call is made until the one `status` makes at the end

#### Scenario: A newer log that is a link
- **WHEN** a worker plants a newer `<stamp>.md` that is a link during a live wait
- **THEN** `wait` prints nothing from it

#### Scenario: A log grown past the bound
- **WHEN** the run log gains more than `262,144` bytes between two polls
- **THEN** each poll prints the whole lines of at most that many bytes, and the rest is printed at the next polls

#### Scenario: A line past the bound
- **WHEN** the run log gains a line longer than `262,144` bytes with no newline
- **THEN** `wait` prints nothing of that line, its tail included, and prints the lines that follow it

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or start with `.minions/`, unless the test lists the file and the name. No string constant outside `skills/mflib/layout.py` SHALL contain `.mf-ship-origin` or equal `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, and the test SHALL list no such site. No string constant outside `skills/mflib/` SHALL equal `status_log.md`, contain `## Run`, contain `# Ship run`, contain the run log's clock, `\d\d:\d\d:\d\d` or `(\d\d):(\d\d):(\d\d)`, or contain `- **` or `- \*\*`, the head of a card, unless the test lists the file and the name. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands, state paths and formats SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

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
