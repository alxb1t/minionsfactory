## MODIFIED Requirements

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL halt before it folds, archives, commits or tags when the default branch is not an
ancestor of `HEAD`, naming the merge-in: `/mf-integrate`, then converge's catch-up round when converge ran, then the release
again. The default branch SHALL be the one `git symbolic-ref --short
refs/remotes/origin/HEAD` names after `origin/`, or `main`. It SHALL, after the tag, ask the person once whether to
merge and push. Given `merge=yes`, it SHALL NOT ask: `merge=yes` is the yes, given once by the person who started
`mf-ship`; and it SHALL halt before the merge when Step 2 flagged a hand-edit. When the release runs in a linked
worktree other than the primary, that one ask SHALL name the
worktree and the ignored paths it holds, listed by name without reading file contents. On yes it SHALL halt when the
default branch is not an ancestor of the branch, naming the person's
recovery — the tag deleted and the release commit reset, by the person — then merge with `--no-ff` in the worktree
that holds the default branch, halting when that worktree's tree is not clean, check that the merged tree equals the
branch's, and push the default branch and the tag to `origin`, except under `merge=yes`, where `conduct.py` pushes. After the merge it SHALL remove the worktree the ask
named, without `--force`, keeping its branch. A listing that fails SHALL be named in the ask, and the worktree
retained. A worktree that refuses removal is reported, not forced. Its close-out SHALL name the worktree removed,
kept or refused. It SHALL never force a push, never push
the version branch, and SHALL merge without pushing when there is no `origin`. On anything but yes it SHALL print
the commands and stop.

#### Scenario: The release names the merge and its guards
- **WHEN** the tag is made and the person answers yes to `Merge <branch> into <default-branch> and push?`
- **THEN** `mf-release` halts if the default branch is not an ancestor of the branch, merges with `--no-ff`,
  checks the merged tree equals the branch's, and pushes the default branch and the tag without `--force`

#### Scenario: The person says anything else, or there is no origin
- **WHEN** the answer is not yes
- **THEN** the release prints the merge and push commands and stops
- **AND WHEN** the answer is yes and there is no `origin`
- **THEN** it merges and does not push

#### Scenario: The base moved before the release
- **WHEN** the default branch has a commit the version branch lacks when the release starts
- **THEN** it halts before the fold, the commit and the tag, naming `/mf-integrate`, the catch-up round and the release
  again

#### Scenario: A release run in a linked worktree
- **WHEN** the version branch is checked out in a linked worktree and the primary holds the default branch
- **THEN** the release merges in the primary, never switching branches in the version's worktree
- **AND** it removes the version's worktree after the merge, the branch kept

#### Scenario: A version's worktree contains ignored local files
- **WHEN** the version's worktree holds ignored paths, such as `.venv/` and the test caches
- **THEN** the ask names each path without reading its contents, and on yes the release removes the worktree with
  them, without `--force`
- **AND WHEN** the listing fails
- **THEN** the ask names the failure, and the release retains the worktree

#### Scenario: The conductor gives the yes
- **WHEN** the release is run with `merge=yes` and Step 2 flagged nothing
- **THEN** it asks nothing, merges and removes the worktree as on a yes, and `conduct.py` pushes
- **AND WHEN** Step 2 flagged a hand-edit
- **THEN** it halts after the tag and before the merge, naming the flagged prose

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor the models
file names for it, or of the executor running `mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL run in an OS sandbox, Claude Code's or Codex's workspace-write, its writes reaching the primary and
each open worktree and nothing outside them, under `conduct.py`'s allowlist on Claude Code, extended by `AGENTS.md`'s `Ship
tools:` line, its prompt carrying the shell rules, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt a version by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run. `conduct.py` SHALL run its own git with hooks and `core.fsmonitor` off, so a hook a worker
plants does not run at the conductor's rights.

#### Scenario: A worker plants a hook
- **WHEN** a `post-commit` hook stands in the repo and `conduct.py` commits a dependent's merge
- **THEN** the hook does not run on that commit

#### Scenario: Two cut versions ship
- **WHEN** two versions are cut, each in its own worktree, and `mf-ship` runs to the end
- **THEN** both are released, merged and pushed, the first ready first, the other integrated and judged by a
  catch-up round first, and only the primary is left

#### Scenario: A ready version ships past a slow one
- **WHEN** two versions run and the lower id is still building when the higher is ready
- **THEN** the higher is released first, and takes the lower number

#### Scenario: A worker runs a command off the list
- **WHEN** a build worker's command is denied by the allowlist and the build's check still passes
- **THEN** the run goes on, and the report lists the denial
- **AND WHEN** the build's check fails
- **THEN** the version halts, and its `halt` line names the denial

#### Scenario: No worktrees are declared
- **WHEN** `mf-ship` starts in a repo whose `AGENTS.md` declares no `Worktrees:`
- **THEN** it halts, naming the missing declaration, and starts no worker

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim and `origin`'s URLs in the home folder: a re-run derives every stage again
and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, or an `origin` that left the kept URLs. A worker stopped by a usage
limit SHALL be halted with its reset time named.

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
- **WHEN** integrate halted on a semantic conflict or a red gate, with the merge open and its note under
  `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/backlog.md` only while holding `.minions/backlog.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/backlog.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

## ADDED Requirements

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on and `allowUnsandboxedCommands` false, writing only to the primary, the
open worktrees and the common directory. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names. A Codex worker SHALL run with its network off. Both SHALL keep `uv`'s cache
in the run directory.

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

### Requirement: No worker pushes

Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL stop after its merge in the primary, and `conduct.py` SHALL push, through
the tagged-merges rule, before it judges the release. A hand release SHALL push as today. `conduct.py` SHALL make each remote
call from a scratch git directory outside every worker's reach, reading no repo's config. Before a run's first worker it SHALL
keep `origin`'s URLs in the home folder, outside every worker's reach, a file that stands staying, and SHALL push only to them.
It SHALL make no remote call, in a run or in `status`, `check` or `report`, while `origin` differs from the kept URLs, and only a
person SHALL clear that, repointing `origin` or removing the file. A run that read an `origin` SHALL halt, making no remote call,
when the repo's git config or `info/attributes` differs from its first read, a key off the list naming itself. `status`, `check`,
`report`, `stop` and `grant` SHALL halt, making no remote call, when git names a repo outside the folder they run in and no run
kept that repo's URLs.

#### Scenario: A release under mf-ship
- **WHEN** a release worker merges under `merge=yes`
- **THEN** it pushes nothing, the conductor logs a `push` event, and the release check passes

#### Scenario: A worker repoints origin during a run
- **WHEN** a worker sets `remote.origin.url` to another network URL
- **THEN** the run halts naming the changed config, and that host receives nothing

#### Scenario: A release worker plants a key off the list
- **WHEN** a release worker leaves such a key in a repo with an `origin`
- **THEN** the run halts naming the key, and makes no remote call

#### Scenario: A repoint outlasts the run
- **WHEN** a run stopped with `origin` repointed, and `status`, `check`, `report` or a new run follows
- **THEN** each that would make a remote call halts naming the file that keeps the URLs, and that host receives nothing
- **AND WHEN** a person repoints `origin`, or removes that file
- **THEN** the next run goes on, and a removed file keeps what that run reads

#### Scenario: A worker redirects git to another repo
- **WHEN** a `commondir` file, or a swapped `.git`, leaves git naming a repo no run kept, its `origin` on another host
- **THEN** `status`, `check` and `report` halt, and that host receives nothing
- **AND WHEN** a person removes the redirect
- **THEN** each reads the primary again

#### Scenario: A worker sets a key after the refusal
- **WHEN** a key that names a program stands in the repo's config after the refusal read it clean
- **THEN** the conductor's remote calls and pushes do not run that program

### Requirement: A run's plan is read once

`conduct.py` SHALL read every open version's executors, models and efforts, and `AGENTS.md`'s `Ship network:` and `Ship tools:`
lines, once, before the first worker, and SHALL halt a
version whose models file later differs. It SHALL halt a version before integrate when the default branch holds a first-parent
commit past `origin` that merges no release.

#### Scenario: A worker edits the models file
- **WHEN** a worker changes a later station's `executor`
- **THEN** that version halts, and no worker starts on the new executor

#### Scenario: A person commits to main during a run
- **WHEN** the default branch gains a person's commit while a version builds
- **THEN** that version halts before integrate, naming the commit
