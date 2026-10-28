## ADDED Requirements

### Requirement: A cut makes a worktree when the repository declares one

When root `AGENTS.md` declares `Worktrees:` with a path, `skills/mf-cut-change/SKILL.md` SHALL create the version's
branch with `git worktree add -b v<version>_<slug> <path>/v<version>_<slug> <default-branch>`, the path relative to
the primary checkout, and SHALL write and commit the change directory in that worktree, leaving the primary on the
default branch. When `AGENTS.md` also declares `Workspace setup:` with a command, the cut SHALL run it in the new
worktree, halting on a failure and naming it. A repository that declares no `Worktrees:` SHALL keep the branch
switch in place.

#### Scenario: A repository with worktrees declared
- **WHEN** the cut runs in the primary of a repository whose `AGENTS.md` declares `Worktrees: ../`
- **THEN** the change is committed in `../v<version>_<slug>`, a linked worktree on the new branch
- **AND** the primary is still on the default branch, its tree clean

#### Scenario: A repository with no worktrees declared
- **WHEN** `AGENTS.md` declares no `Worktrees:`
- **THEN** the cut switches to the new branch in place, as before

### Requirement: A cut reserves its id and version against every open version branch

`skills/mf-cut-change/SKILL.md` SHALL take a change id only when its number is higher than every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch and on every `v*` branch not merged into it,
and a version only when no such branch is named for it and no tag `<tag>` exists. Versions SHALL ship in the order
they were cut.

#### Scenario: Two cuts while one change is open
- **WHEN** a version branch holding change `0040-x` is not yet merged, and a second cut is asked for id `0040-y`
- **THEN** the cut halts: the id is taken by an open branch

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. Converge and the release SHALL write `.minions/backlog.md` only while holding `.minions/backlog.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/backlog.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

### Requirement: The plan station checks which versions can run side by side

When the person names versions to run side by side, `skills/mf-plan/SKILL.md` SHALL compare their briefs' `## Facts`
paths and `## Phases` files, and SHALL propose any pair that touches a file in common in an order, not side by side.

#### Scenario: Two versions that touch the same skill
- **WHEN** two briefs both name `skills/mf-release/SKILL.md`
- **THEN** `mf-plan` proposes them in order, naming the file

## MODIFIED Requirements

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL halt before it folds, archives, commits or tags when the default branch is not an
ancestor of `HEAD`, naming the merge-in: merge the default branch in, run the gate, converge's catch-up round when
converge ran, then the release again. The default branch SHALL be the one `git symbolic-ref --short
refs/remotes/origin/HEAD` names after `origin/`, or `main`. It SHALL, after the tag, ask the person once whether to
merge and push. On yes it SHALL halt when the default branch is not an ancestor of the branch, naming the person's
recovery — the tag deleted and the release commit reset, by the person — then merge with `--no-ff` in the worktree
that holds the default branch, halting when that worktree's tree is not clean, check that the merged tree equals the
branch's, and push the default branch and the tag to `origin`. After the merge it SHALL remove the version's linked
worktree, keeping its branch, only after a successful ignored-path check finds no ignored local files; otherwise
it SHALL retain the worktree and report cleanup skipped without reading file contents. A worktree that refuses
removal is reported, not forced. It SHALL never force a push, never push
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
- **THEN** it halts before the fold, the commit and the tag, naming `git merge <default-branch>`, the gate, the
  catch-up round and the release again

#### Scenario: A release run in a linked worktree
- **WHEN** the version branch is checked out in a linked worktree and the primary holds the default branch
- **THEN** the release merges in the primary, never switching branches in the version's worktree
- **AND** it removes the version's worktree after the merge when no ignored local files remain, the branch kept

#### Scenario: A version's worktree contains ignored local files
- **WHEN** the merge succeeds and the version's worktree contains ignored local files
- **THEN** the release retains the worktree and reports cleanup skipped without reading their contents
