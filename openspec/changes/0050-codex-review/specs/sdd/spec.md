## MODIFIED Requirements

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor the models
file names for it, or of the executor running `mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL act under `conduct.py`'s allowlist on Claude Code — extended by
`AGENTS.md`'s `Ship tools:` line, with forced pushes, hard resets and cleans denied, its edits and shell reaching the
primary and each open worktree and nothing outside them, its prompt carrying the shell rules — or the workspace-write sandbox on Codex, and SHALL never run with permission prompts bypassed. A denial SHALL
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

### Requirement: A station's executor comes from the models file

`.minions/models/<change-id>.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own, and any failed probe SHALL stop the run.
A station on Codex SHALL report no denial, and converge's tokens SHALL read `unavailable`.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

### Requirement: A worker's reach stops at the repository

A Codex worker's writable roots and a Claude worker's `Edit` and `--add-dir` SHALL be the primary and each open worktree,
from `git worktree list`, and never the directory holding them. `conduct.py` SHALL load `integrate.py` once, before the
first worker, and SHALL halt a version's merge when the local git config or `info/attributes` changed since then.

#### Scenario: A sibling project
- **WHEN** a worker runs in a repository whose parent holds other projects
- **THEN** no writable root and no `--add-dir` names that parent

#### Scenario: A worker plants git config
- **WHEN** a worker changes the common directory's config during a run
- **THEN** the conductor merges nothing for a dependent, and that version halts, naming the change
