## MODIFIED Requirements

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing, and SHALL start with `--strict-mcp-config` and no `--mcp-config`, so the
MCP servers of the operator's own config start nothing; the run's probe SHALL fail when a Claude worker's `init` event lists an
MCP server, naming it. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names, and its sandbox SHALL never have `allowLocalBinding`: it binds no
loopback port, in any repo. A Codex worker SHALL run with its network off, and SHALL
start with its working directory and every tree it reaches marked untrusted, whatever the operator's Codex config says, so a
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. A Codex worker SHALL start with
`--ignore-user-config`, so the operator's Codex config — its MCP servers, plugins, profiles and model — starts nothing and
sets nothing, and with `--json`, so its log is one event a line; the run's probe SHALL fail when a Codex worker's log holds an
MCP tool call, naming its server. A Codex worker SHALL never have `/tmp` as a writable root. Both SHALL keep `uv`'s cache in
the run directory. A Claude worker SHALL start with `TMPDIR` naming `.minions/tmp/`, which a run empties at its start, halting when
`.minions` is a link; its sandboxed command may take Claude Code's own `TMPDIR` instead, inside its sandbox. A Codex worker SHALL
start with `TMPDIR` naming a fresh folder made for it alone, outside every repository, under the conductor's own `TMPDIR`, and with
`TMPPREFIX` naming a file prefix in that folder, so the files of a shell's here-document land there: that folder SHALL be the only
writable root the worker has beyond the roots its station already reaches, and the conductor SHALL remove it when the worker
ends. A run SHALL halt, starting no Codex worker, when the conductor's own `TMPDIR` lies inside a git
repository, and a Codex worker SHALL never take `.minions/tmp/` or the `TMPDIR` variable as a writable root. Every worker's
prompt SHALL carry the shell rules, which forbid a here-document. Neither SHALL inherit the conductor's `VIRTUAL_ENV`.

#### Scenario: A script tries to leave
- **WHEN** a worker or its subagent runs a script that writes outside its reach, reads `~/.ssh`, reads a credential variable and
  calls an unlisted domain, the npm registry among them
- **THEN** each fails, on Claude; on Codex the read may pass, and that is a stated gap

#### Scenario: A worker uses its Read tool on a credential
- **WHEN** a Claude worker or its subagent calls `Read` on a path under `~/.ssh`
- **THEN** the call is denied, and the report lists the denial

#### Scenario: A worker plants a start-up
- **WHEN** a worker leaves a `SessionStart` hook in `.claude/settings.local.json`, or a server in `.mcp.json`
- **THEN** neither runs at the next Claude start

#### Scenario: The operator has MCP servers
- **WHEN** the operator's user config names an MCP server
- **THEN** a Claude worker's command line holds `--strict-mcp-config` and no `--mcp-config`
- **AND WHEN** a Claude probe worker's `init` event lists an MCP server all the same
- **THEN** the probe fails, naming the server, and the run halts

#### Scenario: The operator has a Codex config
- **WHEN** the operator's `~/.codex/config.toml` names a model, an MCP server and a plugin
- **THEN** a Codex worker's command line holds `--ignore-user-config` and `--json`
- **AND WHEN** a Codex probe worker's log holds an MCP tool call all the same
- **THEN** the probe fails, naming the server, and no station runs on Codex

#### Scenario: A worker plants a Codex project config
- **WHEN** a worker leaves an `[mcp_servers]` entry in `.codex/config.toml`, in a tree the operator's Codex config trusts
- **THEN** it does not run at the next Codex worker's start
- **AND** no Codex worker's start writes a trust entry to the operator's Codex config

#### Scenario: The sandbox cannot start
- **WHEN** a Claude worker starts on a machine where Claude Code's sandbox cannot start
- **THEN** the worker ends without running a command, and its version halts on the exit

#### Scenario: A repo's gate serves on loopback
- **WHEN** a Claude worker runs a gate that binds `127.0.0.1`
- **THEN** the bind is refused, and the worker's sandbox has no `allowLocalBinding`

#### Scenario: A worker makes a scratch file
- **WHEN** a worker on either executor runs `mktemp`
- **THEN** the file is made inside its sandbox: on Codex under its own fresh `TMPDIR`, outside every repository, and on Claude
  under the primary's `.minions/tmp/` or under Claude Code's own `TMPDIR`
- **AND WHEN** the next run starts
- **THEN** `.minions/tmp/` is empty, and a link there is replaced by a folder, its target untouched
- **AND WHEN** a run starts with `.minions` a link
- **THEN** it halts, naming the link, and its target's `tmp` keeps its files

#### Scenario: A Codex worker's own temporary folder
- **WHEN** a Codex worker starts
- **THEN** its `TMPDIR` names a fresh folder in which `git rev-parse` fails, its `TMPPREFIX` names a prefix in that folder, the
  folder is among its writable roots, and the roots its station already reaches are the same as before
- **AND WHEN** the worker ends
- **THEN** the folder is gone

#### Scenario: A worker links the scratch folder out
- **WHEN** a worker replaces `.minions/tmp` with a link to a folder outside its reach, and a Codex worker starts
- **THEN** that worker's writable roots name its own fresh folder and not the link's target, so the target is not one

#### Scenario: The conductor's temporary folder lies in a repository
- **WHEN** a run starts with the conductor's `TMPDIR` inside a git repository
- **THEN** the run halts before it starts a Codex worker, naming `TMPDIR`

#### Scenario: A worker needs a temporary file in a here-document
- **WHEN** a worker's command line is built on either executor
- **THEN** its prompt ends with the shell rules, which say to write a file with the edit tool and never with a here-document

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under macOS Seatbelt, through `conduct.py sandboxed -- <cmd>`.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — to its
own fresh temporary folder, and to `/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied
(`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`,
`~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and
SHALL have no network of any kind, loopback included. It SHALL start with the credential variables of a Claude worker unset, with
`VIRTUAL_ENV` unset, with git's hooks off, with `UV_OFFLINE=1`, with `uv`'s cache in the run directory, and with `TMPDIR` naming that
temporary folder: one made for the command alone, outside every repository, under the conductor's own `TMPDIR`, and removed by
`conduct.py` when the command ends. A conductor whose own `TMPDIR` lies inside a git repository SHALL run nothing, print a line
naming `TMPDIR` and exit 2. Its exit code SHALL be the
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

#### Scenario: A command's own temporary folder
- **WHEN** a command run through `conduct.py sandboxed` runs `git rev-parse` in its `TMPDIR`, and writes a file there
- **THEN** the `git rev-parse` fails, the write succeeds, and the folder is gone after the command ends

#### Scenario: The conductor's temporary folder lies in a repository
- **WHEN** `conduct.py sandboxed -- true` runs with `TMPDIR` naming a folder inside a git repository
- **THEN** `true` does not run, the output names `TMPDIR`, and the exit is 2

#### Scenario: No OS sandbox stands
- **WHEN** `sandbox-exec` is not on `PATH` and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox`, and the exit is 2
