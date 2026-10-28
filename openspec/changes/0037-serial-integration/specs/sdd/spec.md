## ADDED Requirements

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, pick the version with the lowest change id among
the unmerged `v*` branches, halting and naming it when it is not ready — a phase unticked, or converge not clean —
never skipping ahead. It SHALL merge the default branch into that version's worktree, run `make gate` there, commit
the merge with the version's `Change:` trailer, and end with `Next: /mf-converge, then /mf-release`. It SHALL NOT
release, tag, push or rebase.

#### Scenario: The next version is ready
- **WHEN** the lowest-id open version has every phase ticked and clean findings files
- **THEN** the station merges the default branch into its worktree, gates the result and commits the merge

#### Scenario: The next version is not ready
- **WHEN** the lowest-id open version has an unticked phase
- **THEN** the station halts, naming that version, and merges nothing

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines, renumber the branch's new decision to the next id free
on the default branch with its citations, and report each MODIFIED or REMOVED requirement title of the branch's delta
that the default branch changed since the branch's base. `.gitattributes` SHALL NOT set `merge=union`.

#### Scenario: Both sides added a decision
- **WHEN** the default branch took `D45` and the branch added its own `D45`
- **THEN** the branch's decision is renumbered `D46`, its citations with it

#### Scenario: Both sides changed a CHANGELOG
- **WHEN** the default branch cut a release section and the branch holds `[Unreleased]` entries
- **THEN** the entries stay above the release section, the blank lines intact

### Requirement: A semantic conflict is handed to the person with the merge open

When the delta check reports a changed requirement or git leaves a conflict the rules do not cover,
`skills/mf-integrate/SKILL.md` SHALL halt with the merge in progress in the version's worktree, write
`.minions/integrate/<change-id>.md` holding both intents and a proposed resolution, and continue from the open
merge on its next run.

#### Scenario: Both versions changed one requirement
- **WHEN** the branch's delta modifies a requirement the default branch also changed since the base
- **THEN** the merge stays open, the note names both changes, and the next run continues from `MERGE_HEAD`

## MODIFIED Requirements

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, counted against the cap, with no
pickup. When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, counted against the cap, with no pickup

#### Scenario: The catch-up round judges a merge-in by what the merge decided
- **WHEN** the range `head..HEAD` holds a merge of the default branch whose conflicts were resolved by hand
- **THEN** the round's patch holds that merge's remerge-diff, not the default branch's changes
- **AND** a merge with no conflicts adds nothing to read, and the gate judges the combined tree

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL halt before it folds, archives, commits or tags when the default branch is not an
ancestor of `HEAD`, naming the merge-in: `/mf-integrate`, then converge's catch-up round when converge ran, then the release
again. The default branch SHALL be the one `git symbolic-ref --short
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
- **THEN** it halts before the fold, the commit and the tag, naming `/mf-integrate`, the catch-up round and the release
  again

#### Scenario: A release run in a linked worktree
- **WHEN** the version branch is checked out in a linked worktree and the primary holds the default branch
- **THEN** the release merges in the primary, never switching branches in the version's worktree
- **AND** it removes the version's worktree after the merge when no ignored local files remain, the branch kept

#### Scenario: A version's worktree contains ignored local files
- **WHEN** the merge succeeds and the version's worktree contains ignored local files
- **THEN** the release retains the worktree and reports cleanup skipped without reading their contents

