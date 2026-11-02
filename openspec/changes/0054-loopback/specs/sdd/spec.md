## MODIFIED Requirements

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names. It SHALL bind loopback only in a repo whose `AGENTS.md` declares
`Ship loopback: yes`, where its sandbox has `allowLocalBinding` true. A Codex worker SHALL run with its network off, and SHALL
start with its working directory and every tree it reaches marked untrusted, whatever the operator's Codex config says, so a
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. Both SHALL keep `uv`'s cache
in the run directory, and neither SHALL inherit the conductor's `VIRTUAL_ENV`.

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

#### Scenario: A worker plants a Codex project config
- **WHEN** a worker leaves an `[mcp_servers]` entry in `.codex/config.toml`, in a tree the operator's Codex config trusts
- **THEN** it does not run at the next Codex worker's start
- **AND** no Codex worker's start writes a trust entry to the operator's Codex config

#### Scenario: The sandbox cannot start
- **WHEN** a Claude worker starts on a machine where Claude Code's sandbox cannot start
- **THEN** the worker ends without running a command, and its version halts on the exit

#### Scenario: A repo's gate serves on loopback
- **WHEN** a Claude worker runs a gate that binds `127.0.0.1` and connects to its own port, in a repo whose `AGENTS.md`
  declares `Ship loopback: yes`
- **THEN** the bind and the connection succeed
- **AND WHEN** the repo declares no `Ship loopback:`
- **THEN** the bind is refused, and the worker's sandbox has no `allowLocalBinding`

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: A run's plan is read once

`conduct.py` SHALL read every open version's executors, models and efforts, and `AGENTS.md`'s `Ship network:`, `Ship tools:`
and `Ship loopback:` lines, once, before the first worker, and SHALL halt a
version whose models file later differs. A `Ship loopback:` value other than `yes` SHALL halt the run, naming it. In a repo
that declares `Ship loopback: yes`, a version with a station on Codex SHALL halt before its first worker, naming the station,
and the run SHALL log, after its `start`, one `loopback` event per process listening on loopback, naming the process and its
address. It SHALL halt a version before integrate when the default branch holds a first-parent
commit past `origin` that merges no release.

#### Scenario: A worker edits the models file
- **WHEN** a worker changes a later station's `executor`
- **THEN** that version halts, and no worker starts on the new executor

#### Scenario: A person commits to main during a run
- **WHEN** the default branch gains a person's commit while a version builds
- **THEN** that version halts before integrate, naming the commit

#### Scenario: A repo declares loopback badly
- **WHEN** `AGENTS.md` declares `Ship loopback: maybe`
- **THEN** the run halts naming the value, and starts no worker

#### Scenario: A Codex station in a loopback repo
- **WHEN** a repo declares `Ship loopback: yes`, and a version's models file names `executor = "codex"` for a station
- **THEN** that version halts before its first worker, naming the station, and every other version goes on

#### Scenario: A run in a loopback repo
- **WHEN** a run starts in a repo that declares `Ship loopback: yes`, with a process listening on `127.0.0.1`
- **THEN** its log holds a `loopback` event naming that process and address
- **AND WHEN** the repo declares no `Ship loopback:`
- **THEN** its log holds no `loopback` event
