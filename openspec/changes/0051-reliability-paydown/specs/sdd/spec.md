## MODIFIED Requirements

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL restore a tree dirty with only its own fold and a staged
archive move to `HEAD`, then start over; a hand release SHALL keep its clean-tree halt. It SHALL re-enter at its merge, after reading its preamble against the archived delta and halting on a flag,
tagging `HEAD` first when the tag is missing, when `HEAD` is its release commit, converge was clean at `HEAD~1` and the
default branch has not moved. `conduct.py` SHALL read that stage as `release` only when the run logs show the release
worker died and the person left no `.minions/release/<change-id>.held` mark, and as `released` for any other release tip. It SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of
a run, push the default branch and each merged tag `origin` lacks, only when every first-parent commit `origin` lacks is a
merge of a tagged release, and SHALL else halt, naming the commit; it SHALL never force, a rejected push halting the run; `status`
SHALL report that work, so a run starts for it. It SHALL make no remote call, merge nothing into a dependent, and read no
tree's status or diff, while the repo's own git config holds a key off its list of keys that name no program, with an
`origin` or without one. It SHALL make no remote call while `origin`'s
fetch or push URL is not a network URL. The claim
`.minions/runs/active` SHALL hold the conductor's pid and each worker's process
group with its leader's start time: a dead pid is a stale claim, whose groups a run kills, each only while its leader
keeps that start time, before it clears the claim and starts, and `status` SHALL name it.

#### Scenario: A release dies before its commit
- **WHEN** a release worker dies with its fold staged and the change's folder moved
- **THEN** a re-run reads the stage as `release`, restores the tree, and releases with one tag

#### Scenario: A release dies after its commit
- **WHEN** a release worker dies between its commit and its tag, and the default branch has not moved
- **THEN** a re-run reads the stage as `release`, tags `HEAD`, merges and pushes

#### Scenario: A release dies after its tag
- **WHEN** a release worker dies after its commit and tag, and the default branch has not moved
- **THEN** a re-run merges and pushes
- **AND WHEN** the default branch has moved
- **THEN** the stage is `released`, a halt naming the person's recovery

#### Scenario: A release stopped on purpose stays stopped
- **WHEN** a release tip's worker exited 0 before its merge, or a person ran the release and said no
- **THEN** the stage is `released`, a halt naming `/mf-release`, and a re-run merges nothing

#### Scenario: A tip forges a release
- **WHEN** a version's tip says `chore(release): <tag>` and the tag is on another commit
- **THEN** the stage is `released`, and a re-run merges nothing

#### Scenario: A hand release finds uncommitted edits
- **WHEN** a person runs `mf-release` with edits uncommitted under `openspec/` or in `CHANGELOG.md`
- **THEN** the clean-tree precondition halts, and nothing is restored

#### Scenario: A release dies before its push
- **WHEN** the default branch is ahead of `origin` and no version is open
- **THEN** `status` names the unpushed work, and a run pushes it and ends on `done`

#### Scenario: The repo's config names a command
- **WHEN** the repo's own git config holds `remote.origin.uploadpack`, and `origin` exists
- **THEN** `status` exits 1 naming the key, a run halts, and the conductor makes no remote call

#### Scenario: The repo's config holds an unlisted key
- **WHEN** the repo's own git config holds a `hook.*` key, or any key off the list
- **THEN** `status` exits 1 naming the key, a run halts, and no hook runs on a push or a dependent's merge

#### Scenario: A worker plants a filter
- **WHEN** a worker leaves a `filter.*` key in the repo's config, over a stat-dirty tracked file
- **THEN** the check that follows halts its version naming the key, and the filter never runs

#### Scenario: A worker repoints origin at a local repo
- **WHEN** `origin`'s URL is a local path or a `file://` URL
- **THEN** `status` exits 1, a run halts, the conductor makes no remote call, and that repo's hooks do not run

#### Scenario: The conductor is killed
- **WHEN** `.minions/runs/active` holds a dead pid and a live worker group
- **THEN** `status` reads `stale`, and a run kills the group, clears the claim and starts

#### Scenario: A claim outlives a reboot
- **WHEN** a stale claim names a group whose leader's start time is not the one the entry holds
- **THEN** a run leaves that group alive, and clears the claim

#### Scenario: A person's local commit on the default branch
- **WHEN** `main` holds a commit that is no merge of a tagged release, and `origin` lacks it
- **THEN** a run halts naming the commit, and pushes nothing

#### Scenario: A flagged release dies
- **WHEN** a release flags its preamble, commits and dies
- **THEN** a re-run halts on the flag before its merge

## ADDED Requirements

### Requirement: A person can stop a run

`/mf-ship stop` SHALL end the live run: the conductor, then each worker group in the claim, then a `halt — stopped by the
person` line in the run log, then the claim. A re-run SHALL resume from disk, and `conduct.py log --verify` SHALL pass the
stopped run. With no live run it SHALL say so and exit 0.

#### Scenario: A run is stopped
- **WHEN** a person runs `/mf-ship stop` with a worker live
- **THEN** the worker's group is gone, the log's last line is the stop, and `.minions/runs/active` is gone

### Requirement: A person can grant one more round

`/mf-ship grant <change-id>` SHALL work only on a version whose status log halted at the cap. It SHALL record the grant and
start a run. `conduct.py` SHALL spend the grant when it spawns converge, with `grant=yes`. `skills/mf-converge/SKILL.md`
SHALL open a run marked as the grant, send the open blockers to a fixer, verify one round, and on clean write the rest to
the backlog with no pickup; a blocker left SHALL halt. The cap SHALL stay three.

#### Scenario: A grant on a version not at the cap
- **WHEN** a person grants a version at any other stage
- **THEN** it refuses, naming the stage, and no run starts

#### Scenario: A grant is spent once
- **WHEN** a granted round ends on a blocker
- **THEN** the stage is `converge-halted`, and a run spends no second round

### Requirement: A run needs its skills linked

At a run's start, `conduct.py` SHALL find each `skills/mf-*` beside itself linked where its executor looks,
`~/.claude/skills` for `claude` and `~/.agents/skills` for `codex`, and SHALL else stop, naming the skill and
`make install-skills`.

#### Scenario: A skill added by a release
- **WHEN** a release adds a skill and nobody installs it
- **THEN** the next run stops at its start, naming it

### Requirement: No hook runs in a run

Every worker SHALL run with `core.hooksPath` set to `/dev/null` and `core.fsmonitor` off through git's environment, as the
conductor's own git does. `make gate` SHALL be the only check. `core.hookspath` and `lfs.repositoryformatversion` SHALL be
allowed in a repo's own git config.

#### Scenario: A repo with a pre-commit hook
- **WHEN** a repo's hook would run on a worker's `git commit`
- **THEN** it does not run, and a repo whose tooling set `core.hooksPath` does not halt

### Requirement: Converge never ends a turn with a worker running

`skills/mf-converge/SKILL.md` SHALL dispatch its checkers and its fixer in the foreground, and SHALL NOT end a turn while one
runs.

#### Scenario: A long fix
- **WHEN** a fixer runs for longer than the host waits on background work
- **THEN** the converge worker stays until the fixer returns
