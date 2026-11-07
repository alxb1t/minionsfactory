## MODIFIED Requirements

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming them when both files stand, or when beside the old file the old lock is a file or younger than
ten minutes; with no old file, no old lock halts. An old file that is a link SHALL halt, naming it, and the move SHALL NOT
follow it. The move SHALL hold `.minions/debt.lock`, created with `mkdir`, halting naming it when it is held, and naming it a
file, not a lock, when a file or a link stands there; it SHALL NOT replace a `debt.md`. Everything about one change SHALL live in `.minions/changes/<change-id>/` — its review, security and status
log files, its diff patch, its models file, the cutter's `cut.halt`, integrate's notes, build's marks, rescue's diagnosis, release's `held`, its gate-check
export and its worker logs — each script finding it through one `_change_dir(primary, id)`; `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/`, `cuts/` and `debt.md` stay generic. A run SHALL move an old layout's files into it at its start, under its claim,
before any worker, idempotently, leaving every file it does not name; a link at `changes/`, `changes/<change-id>/` or an old file
SHALL halt, naming it, and so SHALL an old file beside its new one. `integrate.py`, `gate_check.py`, `run.py`, `conduct.py grant`, and a
hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`, finding a file of its change at its old path, SHALL halt, naming
`/mf-ship` to move it, before writing a file at a new path;
`conduct.py status` and `report` SHALL name such a change `old layout`, reading no stage; `review_metrics.py` SHALL read both
layouts.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/debt.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

#### Scenario: A dead worker left the lock
- **WHEN** a run starts and `.minions/debt.lock` is older than ten minutes
- **THEN** the run removes it and logs the removal before its first worker
- **AND WHEN** the lock is younger
- **THEN** the run leaves it

#### Scenario: A run moves an old backlog
- **WHEN** a run starts beside a `.minions/backlog.md` and no `.minions/debt.md`
- **THEN** it moves the file, removes any stale `backlog.lock`, logs both, and a second start moves nothing
- **AND WHEN** both files stand, the old file is a link, or beside it a `backlog.lock` that is a file or younger than ten
  minutes, or a `debt.lock` younger than ten minutes
- **THEN** the run halts, naming them, and starts no worker
- **AND WHEN** beside the old file `.minions/debt.lock` is a plain file
- **THEN** the run halts, naming `.minions/debt.lock` a file, not a lock, and starts no worker
- **AND WHEN** no old file stands beside a young `backlog.lock`, or a file there
- **THEN** the run goes on

#### Scenario: A run moves an old layout
- **WHEN** a run starts beside `.minions/findings/<id>_review.md`, `models/<id>.toml`, `build/<id>.done` and a stray `findings/notes.txt`
- **THEN** each moves into `.minions/changes/<id>/`, the stray stays, the version's stage reads as before, and a second start moves nothing

#### Scenario: A hand-run release on an old layout
- **WHEN** `mf-release` runs by hand for a change whose findings sit in `.minions/findings/`
- **THEN** it halts, naming `/mf-ship`, and releases nothing

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
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. Both SHALL keep `uv`'s cache in the run
directory, and both SHALL start with `TMPDIR` naming `.minions/tmp/`, which a run empties at its start, halting when `.minions`
is a link; a Claude worker's sandboxed command may take Claude Code's own `TMPDIR` instead, inside its sandbox, and a Codex
worker SHALL never take `TMPDIR` as a writable root of its own. Neither SHALL inherit the conductor's `VIRTUAL_ENV`.

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
- **THEN** the file is made inside its sandbox: under the primary's `.minions/tmp/` on Codex, and on Claude there or under
  Claude Code's own `TMPDIR`
- **AND WHEN** the next run starts
- **THEN** `.minions/tmp/` is empty, and a link there is replaced by a folder, its target untouched
- **AND WHEN** a run starts with `.minions` a link
- **THEN** it halts, naming the link, and its target's `tmp` keeps its files

#### Scenario: A worker links the scratch folder out
- **WHEN** a worker replaces `.minions/tmp` with a link to a folder outside its reach, and a Codex worker starts
- **THEN** that worker's command line excludes `TMPDIR` from its writable roots, so the link's target is not one

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one. It
SHALL also exit 1 when a top-level item of `## For the cut` does not open `<n>. ` and one space, when an item's head names a
slug or an `after` entry that `conduct.py`'s `SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or more than
one, when the item has no `models:` line naming the build, converge, release and cut station in order, each with a model and
effort of `[A-Za-z0-9._-]` alone, or when an item's models line is not written `- models:`, or it has more than one. It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be
read or a span cannot be parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`, or an
  item's slug or cut effort holds `$(…)` or `;`
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** a `## For the cut` item opens `- ` where `<n>. ` is due, or its head holds a second `after:`, or it has a
  second models line
- **THEN** `brief_check.py` exits 1, naming the item

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`, the executor, model and effort from the version's models file, else the run's, and `tokens` the
worker's figure or `unavailable`. The log SHALL NOT be a findings file: no station writes it and no
release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's review and security files are read
- **THEN** the log holds one `verdicts` line for each role, each naming that role's executor, model and effort

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the offline base, the release ledger and a person's gate approval
in the home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/debt.lock`, or an older `.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, an old
`.minions/backlog.md` beside `.minions/debt.md` or a file at `.minions/backlog.lock` or `.minions/debt.lock`, or one that is a
link, or a default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset
time named.

#### Scenario: A HUMAN phase halts its version
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** that version halts, naming the phase, and every other version goes on

#### Scenario: A later version halts, and the earlier ships
- **WHEN** two versions run and the later one's build check fails
- **THEN** the earlier is released, merged and pushed
- **AND** the run closes naming the later as halted and the earlier's tag as released, and exits 1

#### Scenario: A later version ships past a halted one
- **WHEN** two versions run and the earlier one's build check fails
- **THEN** the later is released, merged and pushed
- **AND** the run closes naming the earlier as halted and the later's tag as released, and exits 1

#### Scenario: A halted dependency blocks a chain
- **WHEN** a version halts, a second has it in `after:`, and a third has the second in `after:`
- **THEN** neither starts a worker, each logs `blocked — by <id>`, and the closing line names both as blocked

#### Scenario: No open version can start
- **WHEN** one version sits at a `**HUMAN` phase, and every other is `waiting`
- **THEN** the run starts no worker, and closes naming the first as halted and the others as blocked

#### Scenario: A failed probe stops the run
- **WHEN** the probe's check fails
- **THEN** no version starts a worker, and the run closes naming `run` as halted

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again

#### Scenario: The person resolves a semantic conflict
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/changes/<change-id>/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/changes/<change-id>/integrate.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing
