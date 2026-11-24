## ADDED Requirements

### Requirement: The release's fixed steps are a script's

`skills/mf-release/scripts/release.py` SHALL run each fixed step of a release, as the subcommands `pre`, `finish` and `merge`, each printing `release: ok — <what>` and exiting 0, or `release: halt — <why>` and exiting 1, or `release: cannot run — <why>` and exiting 2. `pre` SHALL check the release's preconditions, print the tag `next_tag.py` gives and write `.minions/changes/<change-id>/release.pre`. `finish` SHALL take the paths the worker left, archive the change, cut the changelog with its `Gate:` line, bump the version file with its lock, collect the metrics, run the gate fresh, make one commit, tag it and clear the paid cards. `merge` SHALL merge the branch into the default branch. The release worker SHALL fold the spec delta, read the capability preamble and correct prose that states the version, and SHALL NOT commit, tag or merge. `skills/mf-release/SKILL.md` SHALL run the same subcommands by hand, and a requirement that names the skill for one of these steps SHALL be held by the script. `finish` SHALL commit only a path under `openspec/specs/` or a Markdown file the worker changed, besides its own writes, and SHALL halt naming any other changed path. It SHALL halt before the commit while any change is unstaged after the fresh gate, and SHALL tag only once `git status --porcelain` prints nothing. The release commit SHALL carry `Change:` alone as its trailer. A `HEAD` SHALL count as the release commit only when its parent is the `head:` of `release.pre` and every path it changed is one the worker or `finish` writes, and `merge` SHALL halt unless `HEAD` is the release commit with its tag on it. Under `--run` the script's git SHALL sign nothing and run no hook. `release.flag`, a file of the change's `.minions/changes/<change-id>/` folder the worker writes when the preamble needs a hand-edit, SHALL stop `finish` and `merge` before the merge, the commit and the tag standing.

#### Scenario: A repository with a version file and its lock
- **WHEN** a repository holds `pyproject.toml` and `uv.lock` and the release's tag is `v0.5.0`
- **THEN** the release commit holds `pyproject.toml` at `0.5.0` and the `uv.lock` that `uv lock` writes

#### Scenario: A repository with no version file
- **WHEN** the repository holds none of `pyproject.toml` and `package.json`
- **THEN** `finish` records `version file: none` and bumps nothing

#### Scenario: The gate leaves a change unstaged
- **WHEN** the fresh gate leaves a tracked file changed that `finish` did not stage
- **THEN** `finish` halts naming it, with nothing committed and nothing tagged

#### Scenario: The worker edits code
- **WHEN** the worker's tree holds a changed Python file
- **THEN** `finish` halts naming that path, with nothing committed

#### Scenario: A flagged preamble
- **WHEN** `release.flag` stands after the worker
- **THEN** `finish` commits and tags, then halts naming the file, and `merge` merges nothing until a person removes it

#### Scenario: A worker makes a release commit
- **WHEN** the worker commits `chore(release): <tag>` with a Python file in it
- **THEN** `pre` and `finish` halt naming that path, and nothing is tagged or merged

#### Scenario: A script exits 1 under a run
- **WHEN** `release.py pre`, `finish` or `merge` exits 1 under `conduct.py`
- **THEN** the version halts with that line as its reason

## MODIFIED Requirements

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL have the release run `release.py pre`, which SHALL halt before anything is folded, archived, committed or tagged when the default branch is not an
ancestor of `HEAD`, naming the merge-in: `/mf-integrate`, then converge's catch-up round when converge ran, then the release
again. The default branch SHALL be the one `git symbolic-ref --short
refs/remotes/origin/HEAD` names after `origin/`, or `main`. It SHALL, after `release.py finish` has tagged, ask the person once whether to
merge and push. Given `merge=yes`, it SHALL NOT ask: `merge=yes` is the yes, given once by the person who started
`mf-ship`; and `release.py merge` SHALL halt before the merge while `release.flag` stands. When the release runs in a linked
worktree other than the primary, that one ask SHALL name the
worktree and the ignored paths it holds, listed by name without reading file contents. On yes `release.py merge` SHALL halt when the
default branch is not an ancestor of the branch, naming `/mf-release` to run again, whose `pre` drops a release it may drop, then merge with `--no-ff` in the worktree
that holds the default branch, halting when that worktree's tree is not clean, with the message `Merge branch '<branch>'` and `Change: <change-id>` alone as its trailer, check that the merged tree equals the
branch's, and the skill SHALL push the default branch and the tag to `origin`, except under `merge=yes`, where `conduct.py` pushes. After the merge it SHALL remove the worktree the ask
named, without `--force`, keeping its branch, except under `merge=yes`, where `conduct.py` removes it. A listing that fails SHALL be named in the ask, and the worktree
retained. A worktree that refuses removal is reported, not forced. Its close-out SHALL name the worktree removed,
kept or refused. It SHALL never force a push, never push
the version branch, and SHALL merge without pushing when there is no `origin`. On anything but yes it SHALL print
the commands and stop.

#### Scenario: The release names the merge and its guards
- **WHEN** the tag is made and the person answers yes to `Merge <branch> into <default-branch> and push?`
- **THEN** `release.py merge` halts if the default branch is not an ancestor of the branch, merges with `--no-ff`, and
  checks the merged tree equals the branch's, and the skill pushes the default branch and the tag without `--force`

#### Scenario: The person says anything else, or there is no origin
- **WHEN** the answer is not yes
- **THEN** the release prints the merge and push commands and stops
- **AND WHEN** the answer is yes and there is no `origin`
- **THEN** it merges and does not push

#### Scenario: The base moved before the release
- **WHEN** the default branch has a commit the version branch lacks when the release starts
- **THEN** `release.py pre` halts before the fold, the commit and the tag, naming `/mf-integrate`, the catch-up round and the release
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
- **WHEN** the release is run with `merge=yes` and no `release.flag` stands
- **THEN** it asks nothing, `release.py merge` merges as on a yes, and `conduct.py` pushes and removes the worktree
- **AND WHEN** `release.flag` stands
- **THEN** `release.py merge` halts before the merge, naming the file

#### Scenario: A release under mf-ship leaves its worktree to the conductor
- **WHEN** a release under `merge=yes` merges
- **THEN** it removes no worktree, and its close-out says `conduct.py` removes it

### Requirement: The release assigns the version

`skills/mf-release/SKILL.md` SHALL have `release.py pre` read `bump:` from the change's `proposal.md`, halting on anything but `minor` or
`patch`, and print `<tag>` from `skills/mf-release/scripts/next_tag.py`, which SHALL print the next tag after the
highest `vX.Y.Z` tag the default branch holds merged, a local tag on no branch read as none, or `v0.1.0` when there is none. `release.py finish` SHALL write `version:` into the proposal it archives, before
it collects metrics. `conduct.py` SHALL read a released version's tag from the branch tip's `chore(release): <tag>`,
SHALL pass the release check only when that tag's commit is the tip and, with an `origin`, origin's tag is on that
tip, and SHALL hold no number before it.

#### Scenario: A minor after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: minor`
- **THEN** the release tags `v0.41.0` and the archived proposal holds `version: v0.41`

#### Scenario: A patch after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: patch`
- **THEN** the release tags `v0.40.1` and the archived proposal holds `version: v0.40.1`

#### Scenario: A repository with no version tag
- **WHEN** no tag has the form `vX.Y.Z`
- **THEN** `next_tag.py` prints `v0.1.0`

#### Scenario: A stray local tag
- **WHEN** the default branch holds `v0.9.0`, a local `v0.10.0` is on no branch, and the proposal says `bump: patch`
- **THEN** `next_tag.py` prints `v0.9.1`

#### Scenario: A draft page before the release
- **WHEN** the build draws its metrics page and `proposal.md` holds no `version:`
- **THEN** the page reads `unreleased`, and compares with the highest tracked release

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. A version with every phase ticked, no converge run begun, and no `.minions/changes/<change-id>/build.done`
naming `HEAD` SHALL be stage `build`, its closing steps left, and SHALL fail the build check: `skills/mf-build/SKILL.md`
SHALL then run its simplify step again, restoring first, saved to a patch under `.minions/changes/<change-id>/`, a dirty
tree whose paths are all in the change's range while its `.minions/changes/<change-id>/build.closing` mark names `HEAD`, halting and
restoring nothing on a path outside it, a dirty tree with no such mark, or a patch an earlier save left; `conduct.py close` SHALL then run the gate, the metrics and the plan check again, and SHALL write `build.done`, naming `HEAD` and
simplify's outcome, only once they are done. Under `merge=yes`, `release.py pre` SHALL restore, at a `HEAD` that is no release commit, a tree dirty, or holding untracked files, with only a dead release's derived work — the worker's paths, a staged archive move, the changelog cut, the version file and its lock, and the metrics data file — to `HEAD`, removing the archive, the data file and a stale `release.flag`, then the release SHALL start over; a hand release SHALL keep its clean-tree halt. `release.py finish` SHALL re-enter where a dead release stopped, tagging `HEAD` first when the tag is missing, when `HEAD` is its release commit, converge was clean at `HEAD~1` and the
default branch has not moved, and `release.py merge` SHALL then go on, halting while `release.flag` stands. `release.py pre` SHALL pass an existing tag of this release only when it is on a commit that is on no branch and not on `origin`, and `release.py finish` SHALL then move it to the release commit; either SHALL halt on a tag `origin` or the default branch holds. `release.py finish` SHALL run the gate on a release commit before it tags it, a recorded green of that tree reused, and `release.py pre` SHALL halt on a release commit that lacks `release.pre`. `release.py pre` SHALL drop a release commit the default branch moved past, its tag and its commit, when neither is on `origin` nor reachable from the default branch, and halt naming what holds it otherwise. `conduct.py` SHALL read that stage as `release` only when the run logs show the release died, its worker or a `release.py` run, and the person left no `.minions/changes/<change-id>/release.held` mark and no `release.flag` stands, or while the script may drop the tip, and as `released` for any other release tip. It SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of
a run, push the default branch and each merged tag `origin` lacks, only when every first-parent commit past `origin`'s default
branch, as `origin` lists it, is a merge of a tagged release holding that release's tree, whose release commit's parent is a
head the release ledger holds that is not yet on `origin`, and every such tag is on such a release commit, and SHALL else halt, naming the commit or the
tag; an `origin` it cannot read SHALL leave the push waiting, as *A run goes on while origin cannot be reached* says. It
SHALL push the sha it checked, never force, a rejected push halting the run; `status`
SHALL report that work, so a run starts for it. It SHALL make no remote call, merge nothing into a dependent, and read no
tree's status or diff, while the repo's own git config holds a key off its list of keys that name no program, with an
`origin` or without one. It SHALL make no remote call while `origin`'s
fetch or push URL is not a network URL. The claim
`.minions/runs/active` SHALL hold the conductor's pid with its start time, and each worker's process
group with its leader's start time: a pid at or below 1, a dead pid or one that lost its start time is a stale claim, whose
groups a run kills, each only while its leader keeps that start time and names an executor, before it clears the claim and
starts, and `status` SHALL name it. A group that keeps its start time and names no executor SHALL stop the run, naming the
group and keeping the claim, and a run SHALL clear a stale claim before it detaches, so that stop reaches its caller. A start
time SHALL read the same in any zone or locale. A pid `ps` cannot read that still runs is no stale claim: `status`, `run` and
`/mf-ship stop` SHALL exit 2, naming it, and signal nothing, and a run that cannot read its own start time SHALL stop.

#### Scenario: A release dies before its commit
- **WHEN** a release dies with its fold staged and the change's folder moved
- **THEN** a re-run reads the stage as `release`, `pre` restores the tree, and the release goes on with one tag

#### Scenario: A release dies after its commit
- **WHEN** a release dies between its commit and its tag, and the default branch has not moved
- **THEN** a re-run reads the stage as `release`, `finish` tags `HEAD`, and `merge` merges, and the conductor pushes

#### Scenario: A release dies after its tag
- **WHEN** a release dies after its commit and tag, and the default branch has not moved
- **THEN** a re-run merges, and the conductor pushes

#### Scenario: A stranded release is dropped
- **WHEN** a release dies after its commit and tag, the default branch has moved, and neither the commit nor the tag is on `origin` or reachable from the default branch
- **THEN** `pre` deletes the tag and drops the commit, and the stage reads `integrate`
- **AND WHEN** `origin` or the default branch holds the tag or the commit
- **THEN** `pre` halts naming it, and drops nothing

#### Scenario: A worker dies mid-fold
- **WHEN** a release worker dies with an edited spec file, a new untracked spec file and a `release.flag` left
- **THEN** a re-run's `pre` under `--run` restores the tree, removes the untracked file and the flag, and the worker folds again

#### Scenario: A tag on an orphan commit
- **WHEN** a tag of this release is on a commit that is on no branch and not on `origin`
- **THEN** `pre` passes it and `finish` moves it to the release commit
- **AND WHEN** `origin` holds the tag
- **THEN** the script halts naming it, and moves nothing

#### Scenario: A release stopped on purpose stays stopped
- **WHEN** a release tip's script exited 0 before its merge, or a person ran the release and said no
- **THEN** the stage is `released`, a halt naming `/mf-release`, and a re-run merges nothing

#### Scenario: A tip forges a release
- **WHEN** a version's tip says `chore(release): <tag>` and the tag is on another commit
- **THEN** the stage is `released`, and a re-run merges nothing

#### Scenario: A hand release finds uncommitted edits
- **WHEN** a person runs `mf-release` with edits uncommitted under `openspec/` or in `CHANGELOG.md`
- **THEN** the clean-tree precondition halts, and nothing is restored

#### Scenario: A person takes a flagged release
- **WHEN** a person runs `mf-release` on a release tip whose `release.flag` stands
- **THEN** `finish` and `merge` halt naming the file, and merge once the person has read the prose and removed it

#### Scenario: A release dies before its push
- **WHEN** the default branch is ahead of `origin` with a run's release, and no version is open
- **THEN** `status` names the unpushed work, and a run pushes it and ends on `done`

#### Scenario: A hand release left unpushed
- **WHEN** the default branch holds a release a person merged by hand, and `origin` lacks it
- **THEN** a run halts naming the merge and `git push`, and pushes nothing

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

#### Scenario: A claimed group names no executor
- **WHEN** a stale claim names a group that keeps its start time, and whose leader names no executor
- **THEN** a run, detached or not, kills the claim's executors, stops naming that group, and keeps the claim

#### Scenario: A running conductor cannot be read
- **WHEN** `ps` prints nothing for the claim's pid, and that process still runs
- **THEN** `status`, `run` and `/mf-ship stop` exit 2 naming the pid, nothing is signalled, and the claim stays

#### Scenario: The time zone changes during a run
- **WHEN** `TZ` differs between the run's write of its start time and a later read
- **THEN** `status` still reads `live`

#### Scenario: A person's local commit on the default branch
- **WHEN** `main` holds a commit that is no merge of a tagged release, and `origin` lacks it
- **THEN** a run halts naming the commit, and pushes nothing

#### Scenario: A merge a release check refused
- **WHEN** `main` holds a merge of a tagged release whose tree is not that release's, and `origin` lacks it
- **THEN** a run halts naming the merge, and pushes nothing

#### Scenario: A person's version-shaped tag
- **WHEN** `main` reaches a `vX.Y.Z` tag `origin` lacks, on no `chore(release): vX.Y.Z` commit
- **THEN** a run halts naming the tag, and pushes nothing

#### Scenario: A flagged release dies
- **WHEN** a release's `release.flag` stands, and its script dies after the commit and the tag
- **THEN** a re-run halts on the flag before its merge

#### Scenario: A build dies in simplify
- **WHEN** a build worker ticks and commits every phase, marks its closing steps begun, then dies in simplify with an edit
  left uncommitted
- **THEN** a re-run reads the stage as `build`, closing steps left, and its worker saves the edit to a patch, restores it
  and runs simplify again
- **AND** the run converges only after `.minions/changes/<change-id>/build.done` names `HEAD`

#### Scenario: A dirty tree the build did not mark
- **WHEN** every phase is ticked, no `.done` names `HEAD`, and the tree is dirty with no `.closing` mark naming `HEAD`
- **THEN** `mf-build` halts naming the dirty paths, and restores nothing

#### Scenario: A resume finds an earlier patch
- **WHEN** a resume finds the tree dirty while `.closing` names `HEAD`, and `.minions/changes/<change-id>/build.discarded.patch`
  already exists
- **THEN** `mf-build` halts naming the dirty paths and the patch, restores nothing, and leaves the patch as it was

#### Scenario: A build exits without its marker
- **WHEN** a build worker exits 0 with every phase ticked and committed, and no `.done` names `HEAD`
- **THEN** the build check fails, the version halts, and no second build starts

#### Scenario: A build closed before this rule
- **WHEN** a version's phases are all ticked, its converge has begun, and no `.minions/changes/<change-id>/build.done` exists
- **THEN** the stage is read from converge's status log, as before
