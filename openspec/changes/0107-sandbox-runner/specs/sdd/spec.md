## ADDED Requirements

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under macOS Seatbelt, through `conduct.py sandboxed -- <cmd>`.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — and to
`/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied (`~/.ssh`, `~/.aws`,
`~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`, `~/.config/git/credentials`,
`~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and SHALL have no network of any
kind, loopback included. It SHALL start with the credential variables of a Claude worker unset, with `VIRTUAL_ENV` unset, with
git's hooks off, with `UV_OFFLINE=1`, and with `uv`'s cache and `TMPDIR` in the run directory. Its exit code SHALL be the
command's own, a signal's exit shifted to `128` plus its number. When a failed command's output holds the OS's refusal,
`Operation not permitted`, `conduct.py` SHALL print one `sandboxed: denied —` line after it, so a refused write or call reads as
a refusal. Where `sandbox-exec` is not on `PATH`, `conduct.py` SHALL run nothing, print a line holding `no OS sandbox` and exit 2: it SHALL
never run the command bare.

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

#### Scenario: The command's exit passes through
- **WHEN** a command run through `conduct.py sandboxed` exits with 3
- **THEN** `conduct.py` exits with 3, and a command a signal ended exits with `128` plus the signal's number

#### Scenario: A worker's credentials stay unset
- **WHEN** `GITHUB_TOKEN` and `VIRTUAL_ENV` are set where `conduct.py sandboxed` starts
- **THEN** the command sees neither, and sees `UV_OFFLINE=1`

#### Scenario: No OS sandbox stands
- **WHEN** `sandbox-exec` is not on `PATH` and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox`, and the exit is 2
