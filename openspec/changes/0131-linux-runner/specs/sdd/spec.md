## MODIFIED Requirements

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under the host's OS sandbox, through `conduct.py sandboxed -- <cmd>`: macOS Seatbelt on a Mac, bubblewrap (`bwrap`) on Linux.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — to its
own fresh temporary folder, and to `/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied
(`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`,
`~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and
SHALL reach no network outside itself. On a Mac it SHALL have no network of any kind, loopback included; on Linux it SHALL have a
network of its own, where loopback is private to the command and a listener outside is not reached. On Linux a denied credential path
SHALL read as an empty folder or a missing file, not as an error. It SHALL send no signal to a process outside its sandbox, and SHALL
signal the children it started: on a Mac a call to a process outside fails with `Operation not permitted`, signal 0 included; on Linux
the process is not seen and the call fails with `No such process`. It SHALL start with the credential variables of a Claude worker unset, with
`VIRTUAL_ENV` unset, with git's hooks off, with `UV_OFFLINE=1`, with `uv`'s cache in the run directory, with npm offline, its
install scripts off and its cache in the run directory, and with `TMPDIR` naming that
temporary folder: one made for the command alone, outside every repository, under the conductor's own `TMPDIR`, and removed by
`conduct.py` when the command ends. A conductor whose own `TMPDIR` lies inside a git repository SHALL run nothing, print a line
naming `TMPDIR` and exit 2. Its exit code SHALL be the
command's own, a signal's exit shifted to `128` plus its number. When a failed command's output holds the OS's refusal —
`Operation not permitted` on a Mac, `Read-only file system` on Linux — `conduct.py` SHALL print one `sandboxed: denied —` line after
it, so a refused write or call reads as a refusal. Where the OS sandbox does not stand — `sandbox-exec` not on `PATH` on a Mac, `bwrap`
not on `PATH` or unable to apply a sandbox on Linux — `conduct.py` SHALL run nothing, print a line holding `no OS sandbox` and exit 2: it SHALL
never run the command bare.

A command the conductor starts with a deadline SHALL run in a process group of its own. Past its deadline the group SHALL be
sent SIGTERM and, after a short grace, SIGKILL; `conduct.py` SHALL then print one `sandboxed: timed out —` line and exit 124.
Converge SHALL give each command it runs the seconds left to its own deadline.

#### Scenario: A command writes outside the trees
- **WHEN** a command run through `conduct.py sandboxed` writes a file in a folder outside every tree
- **THEN** the write fails with the OS's refusal text, the command's exit is non-zero, and one `sandboxed: denied —` line
  follows its output
- **AND** a write inside a tree succeeds

#### Scenario: A command reads a credential
- **WHEN** a command run through `conduct.py sandboxed` reads a file under `~/.ssh`
- **THEN** on a Mac the read fails with `Operation not permitted`
- **AND** on Linux the file is missing, and the content a real file held is not printed

#### Scenario: A command calls the network
- **WHEN** a command run through `conduct.py sandboxed` connects to a loopback port that a listener outside holds open
- **THEN** the connect fails, and the listener sees none

#### Scenario: A command signals a process outside its sandbox
- **WHEN** a command run through `conduct.py sandboxed` sends SIGTERM, or signal 0, to a process the sandbox did not start
- **THEN** each call fails — with `Operation not permitted` on a Mac, with `No such process` on Linux — and the process is unharmed
- **AND WHEN** the command signals a child it started, or a process that child started in a session of its own
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
- **WHEN** the host's OS sandbox is not there — no `sandbox-exec` on a Mac, no `bwrap`, or one that cannot apply a sandbox, on Linux — and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox` and names the missing tool, and the exit is 2

#### Scenario: A command past its deadline
- **WHEN** a command that starts a child runs under a deadline and outlives it
- **THEN** the command and its child are gone, the output holds a `sandboxed: timed out —` line, and the exit is 124
- **AND WHEN** the command ignores SIGTERM
- **THEN** SIGKILL ends it after the grace

### Requirement: The platform is reached through one port

A script SHALL reach the operating system through `skills/mflib/platform.py`, the port, the one file under `skills/` that names `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` or `ps` in a command line. The port SHALL read the host's OS once, into one name, `macos` or `linux`, and give for that name: a command's confinement from a policy — its writable roots, its denied paths, its network as a yes or no and its temporary folder —, whether the sandbox stands and why it does not, the OS's refusal text, the host's native architecture, one field of a process, the awake hold and why there is none, and the names the host's worker sandbox leaves in a worktree. On Linux the sandbox SHALL stand only when `bwrap` applies a trivial sandbox, probed once a process. A script SHALL load the port with a plain import after one seed line that puts `skills/` on the import path, the same line in each script. `ty` and `pytest` SHALL have `skills/` on their path, and `skills/mflib/*` SHALL be a surface of `THREAT_MODEL.md`. A caller SHALL keep its own operator messages and the order of its checks, and name no OS tool for a reason the port words.

#### Scenario: A policy renders its profile
- **WHEN** the OS is `macos` and a policy holds writable roots, denied paths, a closed network and a temporary folder
- **THEN** the port renders the Seatbelt profile with a rule for each, in the order the roots, the folder and the denied paths were given
- **AND** a policy with the network open renders the same profile without the line that denies it

#### Scenario: A policy renders a bwrap command
- **WHEN** the OS is `linux` and a policy holds writable roots, denied paths, a closed network and a temporary folder
- **THEN** the port returns a `bwrap` command that binds the disk read-only, binds each root and the folder writable in the order given, masks each denied path that exists — a folder by an empty one, a file by `/dev/null` —, unshares the process ids and the network, and ends the command with its parent in a session of its own
- **AND** a policy with the network open leaves the network shared, and a root or a denied path that is absent is left out

#### Scenario: The sandbox's check on Linux
- **WHEN** the OS is `linux` and `bwrap` is absent, or exits non-zero on a trivial sandbox
- **THEN** the sandbox does not stand, and its reason names `bwrap`
- **AND WHEN** `bwrap` applies the trivial sandbox
- **THEN** the sandbox stands, and the port ran `bwrap` once for it in that process

#### Scenario: The refusal is read per OS
- **WHEN** a text holds `Operation not permitted` and the OS is `macos`, or holds `Read-only file system` and the OS is `linux`
- **THEN** the port reports a refusal
- **AND WHEN** a text holds the other OS's refusal
- **THEN** the port reports none

#### Scenario: The native architecture is read past a translated process
- **WHEN** `sysctl` prints `1` for the host's ARM flag, and `os.uname` names `x86_64`
- **THEN** the port reports `arm64`
- **AND WHEN** `sysctl` prints another value, is absent or times out
- **THEN** the port reports the machine `os.uname` names

#### Scenario: A process field is read, or nothing
- **WHEN** the conductor, `awake.py` or the viewer asks for a field of a pid and `ps` exits non-zero, is absent or times out
- **THEN** the port returns an empty string

#### Scenario: The awake hold starts in a session of its own
- **WHEN** the OS is `macos` and the conductor or `awake.py` holds the machine awake with `caffeinate` on `PATH`
- **THEN** `caffeinate` starts in a session of its own, and a caller with none on `PATH` prints its own `not held` line and goes on

#### Scenario: No hold on Linux
- **WHEN** the OS is `linux`, with a `caffeinate` on `PATH` or without
- **THEN** the port reports no hold, and its reason reads `no hold on Linux`

#### Scenario: The marks of the worker sandbox
- **WHEN** the OS is `linux`
- **THEN** the port lists `.bash_profile`, `.bashrc`, `.claude`, `.gitconfig`, `.gitmodules`, `.idea`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode`, `.zprofile` and `.zshrc`
- **AND WHEN** the OS is `macos`
- **THEN** it lists none

### Requirement: A live run holds the machine awake

On a Mac, at a run's start, `conduct.py` SHALL start `caffeinate -is -w <its own pid>`, never with `-d`, so the machine neither idles to sleep
nor, on AC power, sleeps, and the hold ends with the conductor. With no `caffeinate` on `PATH` the run SHALL go on; on Linux it SHALL hold nothing and go on. The `start` line
SHALL end `· awake: held`, or `· awake: not held — <why>`, the why the port words: `caffeinate not on PATH` on a Mac, `no hold on Linux` on Linux. A run of fake workers (`MF_SHIP_AGENT`) SHALL start no
hold and name none. `skills/mf-ship/SKILL.md` SHALL say that a closed lid sleeps the Mac whatever the run holds, unless it is in clamshell mode, and that Linux has no hold.

#### Scenario: A run on a Mac
- **WHEN** a run starts with `caffeinate` on `PATH`
- **THEN** it starts `caffeinate -is -w <the conductor's pid>` once, and its `start` line ends `· awake: held`

#### Scenario: No caffeinate
- **WHEN** no `caffeinate` is on `PATH` on a Mac
- **THEN** the run goes on, and its `start` line ends `· awake: not held — caffeinate not on PATH`

#### Scenario: A run on Linux
- **WHEN** a run starts on Linux
- **THEN** it starts no hold, the run goes on, and its `start` line ends `· awake: not held — no hold on Linux`

### Requirement: A cut run by hand holds the machine awake

The cut SHALL run `skills/mf-cut-change/scripts/awake.py start <change-id>` at the head of its Step 1, and `awake.py stop
<change-id>` at every halt from Step 1 on and at Step 11's close-out. On a Mac `start` SHALL start `caffeinate -is -t 7200 -w <host pid>`,
detached, the host being its nearest ancestor process that is neither a shell nor `uv`, so the hold ends at the stop, the host's
exit or two hours, whichever comes first. It SHALL record the hold's pid in `.minions/awake/<change-id>`, a generic folder of the run directory, and print
`awake: held (2 h at most)`; a hold already recorded for that id is stopped first, and a hold for another id is left alone.
`stop` SHALL kill the recorded pid only while `ps` names it `caffeinate`, and remove the record. With no `caffeinate` on `PATH`,
and on Linux, `start` SHALL print `awake: not held — <why>`, the why the port words — `caffeinate not on PATH` on a Mac, `no hold on Linux` on Linux —, start nothing and exit 0; the cut SHALL go on whatever `awake.py` prints.
`skills/mf-cut-change/SKILL.md` SHALL say that a closed lid sleeps the Mac whatever the cut holds, unless it is in clamshell mode, and that Linux has no hold.

#### Scenario: A cut on a Mac
- **WHEN** the cut starts with `caffeinate` on `PATH`
- **THEN** `awake.py start <change-id>` starts `caffeinate -is -t 7200 -w <host pid>` once, records its pid in
  `.minions/awake/<change-id>`, and prints `awake: held (2 h at most)`

#### Scenario: Two cuts at once
- **WHEN** holds stand for two change ids and one is stopped
- **THEN** its `caffeinate` is killed and its record removed, and the other's stands

#### Scenario: No caffeinate
- **WHEN** no `caffeinate` is on `PATH` on a Mac
- **THEN** `awake.py start` prints `awake: not held — caffeinate not on PATH`, records nothing and exits 0

#### Scenario: A cut on Linux
- **WHEN** `awake.py start` runs on Linux
- **THEN** it prints `awake: not held — no hold on Linux`, records nothing and exits 0

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. A script that loads the shared home SHALL load it after the seed line, the same in each script. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles and OS commands SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

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

## ADDED Requirements

### Requirement: A run on Linux hides the sandbox's marks from its tree checks

On Linux, before its first clean-tree check, a run's start SHALL write each name the port lists as the worker sandbox's marks that the clone's `.git/info/exclude` lacks, each on a line of its own, through no link; a second start SHALL write nothing, and a file the run cannot write safely SHALL stop it with exit 2, naming the file. On a Mac it SHALL write nothing. An untracked file of those names SHALL be unseen by the clean-tree checks on Linux: accepted.

#### Scenario: A first start on Linux
- **WHEN** a run starts on Linux in a clone whose `.git/info/exclude` holds none of the names
- **THEN** the file holds each name on a line of its own, the lines it held before are kept, and the start's clean-tree check passes beside an untracked `.bashrc`

#### Scenario: Some names already stand
- **WHEN** a run starts on Linux and `.git/info/exclude` already holds `.bashrc`
- **THEN** it adds each other name once, and `.bashrc` stays on one line

#### Scenario: A second start
- **WHEN** a run starts on Linux and `.git/info/exclude` holds every name
- **THEN** the file is not written

#### Scenario: A start on a Mac
- **WHEN** a run starts on a Mac
- **THEN** `.git/info/exclude` is not written, and an untracked `.bashrc` fails the clean-tree check

#### Scenario: A link where the file goes
- **WHEN** a run starts on Linux and `.git/info/exclude`, or `.git/info`, is a link
- **THEN** the run stops with exit 2 naming the file, and the link's target is not written
