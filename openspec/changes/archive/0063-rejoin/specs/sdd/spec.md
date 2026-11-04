## ADDED Requirements

### Requirement: A halted version rejoins a live run

`conduct.py rejoin [<change-id>]` SHALL write a request in `.minions/runs/rejoin/`, and `/mf-ship` SHALL send it when a run is
live. The live run SHALL check that folder at most every 10 seconds and before its close, and SHALL take into the run every
open version the request names — every one for a request with no id — whose stage on disk is no longer a halt: a halted one,
a blocked one, and one cut after the run started. A version still at a halt SHALL stay out, logged with why. The poll SHALL
not end the run's loop while a version's thread runs: an entry it cannot delete SHALL be no request, and a version it fails
to take SHALL halt alone. A request folder that is a link SHALL hold no request, and the poll SHALL delete nothing through
it. A version the run's plan already holds SHALL stay out, logged, while its models file differs from what the run read;
any other taken version
SHALL have its models file read as it joins, then go through the run's base check, its dependencies, its stations and the
merge lock, as at a run's start, with its halts and blocks cleared. Its executor's probe SHALL run once in the run, before
the first worker on it; a failed probe SHALL halt only the versions on that executor, each later one with that probe's
reason and no second probe. The run SHALL log a `rejoin` event per
version taken, delete the requests it read, and a run's start SHALL delete every request it finds. A run-level halt SHALL
end the run, as before; a request reaches no ended run.

#### Scenario: A fixed version rejoins
- **WHEN** a version halts while another builds, the person fixes it on disk, and runs `/mf-ship`
- **THEN** the live run logs `rejoin` for it, and it releases in the same run, the other version's stations untouched

#### Scenario: A version still halted
- **WHEN** a request names a version whose stage is still a halt
- **THEN** it stays out, and the run logs why

#### Scenario: A version cut during the run
- **WHEN** a version is cut while a run is live, and `/mf-ship` runs
- **THEN** the live run takes it, and builds it beside the others
- **AND WHEN** a folder stands in `.minions/runs/rejoin/` beside the request
- **THEN** the poll skips it, and the run goes on
- **AND WHEN** `.minions/runs/rejoin` is a link to another folder
- **THEN** the poll reads no request there, and deletes nothing in it

#### Scenario: A new executor
- **WHEN** a taken version's models file names an executor the run has not probed
- **THEN** the run probes it before that version's first worker, and the version goes on
- **AND WHEN** that probe fails
- **THEN** only the versions on that executor halt, the probe run once for them all, and the others release

#### Scenario: A request at the close
- **WHEN** a request lands after the last version's thread ends
- **THEN** the run reads it before its close
- **AND WHEN** a request outlives its run
- **THEN** the next run's start deletes it, and takes every open version anyway

### Requirement: A converge halt answered by the person converges afresh

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the backlog lock's
SHALL be void when its head is both findings files' `head:` and `HEAD` is past it, a descendant that is not it: `conduct.py`'s
stage SHALL be `converge`, and its converge check SHALL not read the old halt. A halt naming no head, one past the judged
head — after converge's own fix, or in a catch-up run — and one whose head is no ancestor of `HEAD` SHALL stand.
`skills/mf-converge/SKILL.md`, finding its newest run's top line such a void halt, SHALL open a run marked `· amended`, and
converge from round 1 over the whole change, the findings files restarting at `round: 1`. A run marked `· grant` that
resumes SHALL stay a granted round.

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a new run marked `· amended`, from round 1, with no grant

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, or in a catch-up run, so its head is not the findings files' `head:`
- **THEN** its stage stays `converge-halted`, and no `· amended` run opens

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

## MODIFIED Requirements

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
plants does not run at the conductor's rights. At a run's start, a version whose branch holds nothing past its cut commit,
and whose base the default branch has passed, SHALL get the default branch merged in, as a dependent does; a version with
more, an unticked phase and no merge open, whose base the default branch passed changing a gate makefile, `AGENTS.md`,
`CODING_STANDARDS.md` or `CONTRIBUTING.md`, SHALL get the default branch merged in when the merge is clean or its conflicts
are all paths `integrate.py`'s `changelog`, `decisions` and `delta` rules settle, and SHALL else halt, naming the files and
`git -C <tree> merge <default>`; one
with an unticked phase and a merge open with no note SHALL halt, naming `git -C <tree> commit`, unless it is a
dependent whose merge `conduct.py` finishes; any other version SHALL go on from its stage. After a release's check passes, `conduct.py` SHALL
remove the version's worktree, without `--force`, keeping its branch, only when its path is `AGENTS.md`'s `Worktrees:`
path joined with the change id, logging the ignored paths it held, listed by name; a listing that fails SHALL keep the
worktree, logged, and a refusal SHALL be logged, never forced.

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

#### Scenario: A version cut before main moved
- **WHEN** a version's branch holds only its cut commit, and the default branch has moved since
- **THEN** the run merges the default branch into it before its first worker, and builds on the merge
- **AND WHEN** the version's build has begun, and the default branch changed `Makefile` since its base
- **THEN** the run merges the default branch in when the merge is clean or conflicts only in `CHANGELOG.md`, and builds on
  the merge
- **AND WHEN** the merge conflicts in a path no rule settles
- **THEN** that version halts before its next worker, naming `Makefile` and the merge to run
- **AND WHEN** every phase is ticked
- **THEN** the version goes on from its stage, and integrate merges the default branch in
- **AND WHEN** a phase is unticked and the merge is open in its worktree with no note
- **THEN** that version halts before its next worker, naming `git -C <tree> commit` to finish the merge
- **AND WHEN** the merge is open with its note
- **THEN** that version halts as `integrating`, naming the note

#### Scenario: A released worktree
- **WHEN** a release's check passes under `mf-ship`
- **THEN** the version's worktree is gone and its branch kept, and the run logs the ignored paths it held
- **AND WHEN** git's worktree entry names a path other than the `Worktrees:` path joined with the change id
- **THEN** nothing is removed, and the run logs it
- **AND WHEN** the worktree's ignored paths cannot be listed
- **THEN** nothing is removed, and the run logs it

### Requirement: A run's plan is read once

`conduct.py` SHALL read every open version's executors, models and efforts, and `AGENTS.md`'s `Ship network:` and `Ship tools:`
lines, once, before the first worker, and SHALL halt a
version whose models file later differs. A version cut during a live run SHALL have its own executors, models and efforts
read once as it joins; a rejoin request SHALL take back no version whose models file differs from what the run read, and
the `Ship` lines SHALL stay as the run read them. An `AGENTS.md` that declares `Ship loopback:` SHALL halt the run, naming the line
as removed. It SHALL halt a version before
integrate when the default branch holds a first-parent commit past `origin` that merges no release.

#### Scenario: A worker edits the models file
- **WHEN** a worker changes a later station's `executor`
- **THEN** that version halts, and no worker starts on the new executor
- **AND WHEN** a rejoin request then names that version
- **THEN** it stays out, the run logs why, and the plan stays as the run read it

#### Scenario: A person commits to main during a run
- **WHEN** the default branch gains a person's commit while a version builds
- **THEN** that version halts before integrate, naming the commit

#### Scenario: A repo declares loopback badly
- **WHEN** `AGENTS.md` declares `Ship loopback: yes`, `Ship loopback: maybe`, or any value
- **THEN** the run halts naming the removed line, and starts no worker

#### Scenario: A Codex station in a loopback repo
- **WHEN** a repo declares `Ship loopback:`, and a version's models file names `executor = "codex"` for a station
- **THEN** the run halts on the removed line before any worker, whatever the executor

#### Scenario: A run in a loopback repo
- **WHEN** a run starts in a repo that declares no `Ship loopback:`
- **THEN** its log holds no `loopback` event, and no worker's sandbox has `allowLocalBinding`

### Requirement: A station's executor comes from the models file

`.minions/models/<change-id>.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own; a failed probe at the start SHALL stop the
run, and one for a joining version SHALL halt only the versions on its executor.
A station on Codex SHALL report no denial, and converge's tokens SHALL read `unavailable`.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

### Requirement: A person can grant one more round

`/mf-ship grant <change-id>` SHALL work only on a version whose status log halted at the cap. It SHALL record the grant and
start a run, or, with a run live, write that version's rejoin request. A refusal SHALL name the stage and the command to
run instead: `/mf-ship`. `conduct.py` SHALL spend the grant when it spawns converge, with `grant=yes`. `skills/mf-converge/SKILL.md`
SHALL open a run marked as the grant, send the open blockers to a fixer, verify one round, and on clean write the rest to
the backlog with no pickup; a blocker left SHALL halt. The cap SHALL stay three.

#### Scenario: A grant on a version not at the cap
- **WHEN** a person grants a version at any other stage, a grant already waiting included
- **THEN** it refuses, naming the stage and `/mf-ship`, and no run starts

#### Scenario: A grant during a live run
- **WHEN** a person grants a version at the cap while a run is live
- **THEN** the live run takes it back and spends the grant in its converge, and the run log holds a `grant` event

#### Scenario: A grant is spent once
- **WHEN** a granted round ends on a blocker
- **THEN** the stage is `converge-halted`, and a run spends no second round
