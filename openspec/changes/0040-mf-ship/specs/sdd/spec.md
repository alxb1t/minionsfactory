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
branch's, and push the default branch and the tag to `origin`. After the merge it SHALL remove the worktree the ask
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
- **THEN** it asks nothing, merges, pushes and removes the worktree as on a yes
- **AND WHEN** Step 2 flagged a hand-edit
- **THEN** it halts after the tag and before the merge, naming the flagged prose

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
It SHALL write the suggestion to `.minions/models/<change-id>.toml`, a table per station, as well as show it, and
SHALL never write it into the change. Authentication and provider configuration SHALL remain the operator's
responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

#### Scenario: The cut records its suggestion
- **WHEN** the cut commits a change
- **THEN** `.minions/models/<change-id>.toml` holds a `build`, a `converge` and a `release` table, each with its
  `model`, and nothing under `openspec/changes/<change-id>/` names a model

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, pick the version with the lowest change id among
the unmerged `v*` branches, halting and naming it when it is not ready — a phase unticked, or converge not clean —
never skipping ahead. It SHALL merge the default branch into that version's worktree, run `make gate` there, commit
the merge with the version's `Change:` trailer, and end with `Next: /mf-converge, then /mf-release`. A red gate SHALL
halt with the merge open and write `.minions/integrate/<change-id>.red`, which the commit deletes. It SHALL NOT
release, tag, push or rebase.

#### Scenario: The next version is ready
- **WHEN** the lowest-id open version has every phase ticked and clean findings files
- **THEN** the station merges the default branch into its worktree, gates the result and commits the merge

#### Scenario: The next version is not ready
- **WHEN** the lowest-id open version has an unticked phase
- **THEN** the station halts, naming that version, and merges nothing

#### Scenario: The merged tree fails the gate
- **WHEN** `make gate` fails on the merged tree
- **THEN** the station halts with the merge open, and `.minions/integrate/<change-id>.red` exists

## ADDED Requirements

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time in change-id order, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor running
`mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. Starting `mf-ship` SHALL be the person's yes to every merge and push of
the run.

#### Scenario: Two cut versions ship
- **WHEN** two versions are cut, each in its own worktree, and `mf-ship` runs to the end
- **THEN** both are released, merged and pushed in change-id order, the later one integrated and judged by a
  catch-up round first, and only the primary is left

#### Scenario: No worktrees are declared
- **WHEN** `mf-ship` starts in a repo whose `AGENTS.md` declares no `Worktrees:`
- **THEN** it halts, naming the missing declaration, and starts no worker

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when its check on disk passes after the worker exits — never on the worker's report. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the run halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

### Requirement: A halt stops the ship run, and a re-run resumes

The ship run SHALL halt at the first failed check, starting no new worker and waiting for running ones. A `**HUMAN`
phase, a dependency waiting for approval, converge's cap, an open integrate merge, a red gate, a release stopped
before its merge, and a worker past its timeout SHALL each halt the run. The run SHALL keep no state outside git
and the run directory: a re-run derives every stage again and continues.

#### Scenario: A HUMAN phase halts the run
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** the run halts, naming the version and the phase, and releases nothing after it

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again
