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
when the repo's git config or `info/attributes` differs from its first read.

#### Scenario: A release under mf-ship
- **WHEN** a release worker merges under `merge=yes`
- **THEN** it pushes nothing, the conductor logs a `push` event, and the release check passes

#### Scenario: A worker repoints origin during a run
- **WHEN** a worker sets `remote.origin.url` to another network URL
- **THEN** the run halts naming the changed config, and that host receives nothing

#### Scenario: A repoint outlasts the run
- **WHEN** a run stopped with `origin` repointed, and `status`, `check`, `report` or a new run follows
- **THEN** each halts naming the file that keeps the URLs, and that host receives nothing
- **AND WHEN** a person repoints `origin`, or removes that file
- **THEN** the next run goes on, and a removed file keeps what that run reads

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
