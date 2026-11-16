## ADDED Requirements

### Requirement: The platform is reached through one port

A script SHALL reach the operating system through `skills/mflib/platform.py`, the port, the one file under `skills/` that names `sandbox-exec`, `caffeinate`, `sysctl` or `ps` in a command line. The port SHALL give a command's confinement from a policy — its writable roots, its denied paths, its network as a yes or no and its temporary folder —, the host's native architecture, one field of a process, the awake hold and the OS's refusal text. A script SHALL load the port with a plain import after one seed line that puts `skills/` on the import path, the same line in each script. `ty` and `pytest` SHALL have `skills/` on their path, and `skills/mflib/*` SHALL be a surface of `THREAT_MODEL.md`. A caller SHALL keep its own operator messages and the order of its checks.

#### Scenario: A policy renders its profile
- **WHEN** a policy holds writable roots, denied paths, a closed network and a temporary folder
- **THEN** the port renders the Seatbelt profile with a rule for each, in the order the roots, the folder and the denied paths were given
- **AND** a policy with the network open renders the same profile without the line that denies it

#### Scenario: The native architecture is read past a translated process
- **WHEN** `sysctl` prints `1` for the host's ARM flag, and `os.uname` names `x86_64`
- **THEN** the port reports `arm64`
- **AND WHEN** `sysctl` prints another value, is absent or times out
- **THEN** the port reports the machine `os.uname` names

#### Scenario: A process field is read, or nothing
- **WHEN** the conductor, `awake.py` or the viewer asks for a field of a pid and `ps` exits non-zero, is absent or times out
- **THEN** the port returns an empty string

#### Scenario: The awake hold starts in a session of its own
- **WHEN** the conductor or `awake.py` holds the machine awake with `caffeinate` on `PATH`
- **THEN** `caffeinate` starts in a session of its own, and a caller with none on `PATH` prints its own `not held` line and goes on

## MODIFIED Requirements

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under macOS Seatbelt, through `conduct.py sandboxed -- <cmd>`.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — to its
own fresh temporary folder, and to `/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied
(`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`,
`~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and
SHALL have no network of any kind, loopback included. It SHALL send no signal to a process outside its sandbox, signal 0 included,
and SHALL signal the children it started. It SHALL start with the credential variables of a Claude worker unset, with
`VIRTUAL_ENV` unset, with git's hooks off, with `UV_OFFLINE=1`, with `uv`'s cache in the run directory, with npm offline, its
install scripts off and its cache in the run directory, and with `TMPDIR` naming that
temporary folder: one made for the command alone, outside every repository, under the conductor's own `TMPDIR`, and removed by
`conduct.py` when the command ends. A conductor whose own `TMPDIR` lies inside a git repository SHALL run nothing, print a line
naming `TMPDIR` and exit 2. Its exit code SHALL be the
command's own, a signal's exit shifted to `128` plus its number. When a failed command's output holds the OS's refusal,
`Operation not permitted`, `conduct.py` SHALL print one `sandboxed: denied —` line after it, so a refused write or call reads as
a refusal. Where `sandbox-exec` is not on `PATH`, `conduct.py` SHALL run nothing, print a line holding `no OS sandbox` and exit 2: it SHALL
never run the command bare.

A command the conductor starts with a deadline SHALL run in a process group of its own. Past its deadline the group SHALL be
sent SIGTERM and, after a short grace, SIGKILL; `conduct.py` SHALL then print one `sandboxed: timed out —` line and exit 124.
Converge SHALL give each command it runs the seconds left to its own deadline.

#### Scenario: A command writes outside the trees
- **WHEN** a command run through `conduct.py sandboxed` writes a file in a folder outside every tree
- **THEN** the write fails with `Operation not permitted`, the command's exit is non-zero, and one `sandboxed: denied —` line
  follows its output
- **AND** a write inside a tree succeeds

#### Scenario: A command reads a credential
- **WHEN** a command run through `conduct.py sandboxed` reads a file under `~/.ssh`
- **THEN** the read fails with `Operation not permitted`

#### Scenario: A command calls the network
- **WHEN** a command run through `conduct.py sandboxed` connects to a loopback port that a listener holds open
- **THEN** the connect fails, and the listener sees none

#### Scenario: A command signals a process outside its sandbox
- **WHEN** a command run through `conduct.py sandboxed` sends SIGTERM, or signal 0, to a process the sandbox did not start
- **THEN** each call fails with `Operation not permitted`, and the process is unharmed
- **AND WHEN** the command signals a child it started
- **THEN** the signal is delivered

#### Scenario: The command's exit passes through
- **WHEN** a command run through `conduct.py sandboxed` exits with 3
- **THEN** `conduct.py` exits with 3, and a command a signal ended exits with `128` plus the signal's number

#### Scenario: A worker's credentials stay unset
- **WHEN** `GITHUB_TOKEN` and `VIRTUAL_ENV` are set where `conduct.py sandboxed` starts
- **THEN** the command sees neither, and sees `UV_OFFLINE=1`

#### Scenario: A command's npm
- **WHEN** a command run through `conduct.py sandboxed` reads its environment
- **THEN** it sees `npm_config_offline=true`, `npm_config_ignore_scripts=true` and `npm_config_cache` naming `.minions/npm-cache` of the primary

#### Scenario: A command's own temporary folder
- **WHEN** a command run through `conduct.py sandboxed` runs `git rev-parse` in its `TMPDIR`, and writes a file there
- **THEN** the `git rev-parse` fails, the write succeeds, and the folder is gone after the command ends

#### Scenario: The conductor's temporary folder lies in a repository
- **WHEN** `conduct.py sandboxed -- true` runs with `TMPDIR` naming a folder inside a git repository
- **THEN** `true` does not run, the output names `TMPDIR`, and the exit is 2

#### Scenario: No OS sandbox stands
- **WHEN** `sandbox-exec` is not on `PATH` and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox`, and the exit is 2

#### Scenario: A command past its deadline
- **WHEN** a command that starts a child runs under a deadline and outlives it
- **THEN** the command and its child are gone, the output holds a `sandboxed: timed out —` line, and the exit is 124
- **AND WHEN** the command ignores SIGTERM
- **THEN** SIGKILL ends it after the grace

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. A script that loads the shared home SHALL load it after the seed line, the same in each script. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles and OS commands SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

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
- **WHEN** a script outside the listed files and the port names `caffeinate`
- **THEN** the OS-command rule fails naming the file and the command
- **AND WHEN** the port names it
- **THEN** the rule passes

#### Scenario: A load of the home with no seed
- **WHEN** a script under `skills/` imports `mflib` and the statement before that import is not the seed line
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
