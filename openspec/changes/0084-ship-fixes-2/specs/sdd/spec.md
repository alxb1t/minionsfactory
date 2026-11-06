## MODIFIED Requirements

### Requirement: A converge halt answered by the person converges afresh

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an older backlog lock's,
SHALL be void when its head is both findings files' `head:` and `HEAD` is past it, a descendant that is not it: `conduct.py`'s
stage SHALL be `converge`, and its converge check SHALL not read the old halt. A halt in a catch-up run whose findings files are
both still clean, a Step 1.6 `verify: halt`, and a fix pass's `amend needed` halt SHALL also be void when `HEAD` is past its head and every commit since is the person's `docs(<id>): amend the
change directory`, one parent each, touching only `openspec/changes/<id>/`. A **halt before round 1** — a halt other than a
`verify: halt` in a run with no `start` line, not marked `· grant` — SHALL be void when `HEAD` is past its head, by any commit, and SHALL be re-run when
`HEAD` is its head: `conduct.py`'s stage SHALL be `converge` in both, and it SHALL start no rescue for it. A run SHALL re-run a
version once at the same head: one that halts before round 1 again SHALL stay out for the rest of that run, a rejoin logging it
still halted. Any other halt naming no head, one past the judged head,
and one whose head is no ancestor of `HEAD` SHALL stand. `skills/mf-converge/SKILL.md`, finding its newest run's top line a halt
before round 1, SHALL open a plain new run, with no mark, as a fresh invocation does; finding a void
catch-up halt with both files clean, it SHALL run the catch-up round again; finding any other void halt, it SHALL open a run marked `· amended`, and
converge from round 1 over the whole change, the findings files restarting at `round: 1`. A run marked `· grant` that resumes
SHALL stay a granted round.

#### Scenario: A gate red before round 1
- **WHEN** converge halts on a red gate before round 1 at head H, writing no `start` line, and the person asks a live run to take
  it back with no new commit
- **THEN** the run takes it back, and converge runs again in a plain new run
- **AND WHEN** it halts before round 1 again in that run
- **THEN** it stays out for the rest of the run, and a rejoin logs it still halted
- **AND WHEN** a commit past H follows
- **THEN** its stage is `converge`

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a new run marked `· amended`, from round 1, with no grant

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the cap is a granted round's, in a run with no `start` line, and `HEAD` is its head
- **THEN** its stage stays `converge-halted`, and it is no halt before round 1

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, or in a catch-up run past its `start` line, so its head is not the findings
  files' `head:`, and a commit other than the person's amend follows
- **THEN** its stage stays `converge-halted`, and no `· amended` run opens

#### Scenario: The person's amend answers a catch-up halt
- **WHEN** a catch-up round halts at Step 1.6 on a `Verify:` changed since the cut, and the person commits `docs(<id>): amend the
  change directory`
- **THEN** its stage is `converge`, and the next run's catch-up round counts the merge and the amend as its own

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing, and SHALL start with `--strict-mcp-config` and no `--mcp-config`, so the
MCP servers of the operator's own config start nothing. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
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
- **THEN** it halts, naming the link, and removes nothing

#### Scenario: A worker links the scratch folder out
- **WHEN** a worker replaces `.minions/tmp` with a link to a folder outside its reach, and a Codex worker starts
- **THEN** that worker's command line excludes `TMPDIR` from its writable roots, so the link's target is not one

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

