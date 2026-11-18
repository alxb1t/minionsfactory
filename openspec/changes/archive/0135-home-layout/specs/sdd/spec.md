## MODIFIED Requirements

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or start with `.minions/`, unless the test lists the file and the name. No string constant outside `skills/mflib/layout.py` SHALL contain `.mf-ship-origin` or equal `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, and the test SHALL list no such site. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands and state paths SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

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
