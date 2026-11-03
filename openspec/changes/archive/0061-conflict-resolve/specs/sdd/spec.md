## MODIFIED Requirements

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, take the version `change-id` names, or with none the
ready version with the lowest change id among the unmerged branches named by a change id that hold their change or a
release commit. It SHALL halt, naming the version, when the named one is not ready, or when none is: a phase unticked,
converge not clean, or an `after:` id missing from its tree. A named version whose merge is open with its note SHALL be
ready. It SHALL merge the default branch into that version's worktree, resolve each additive hunk git leaves — one whose union
keeps every addition and every removal of both sides and changes nothing else, whether its edits separate as lines, list
items or sentences — and a merged test the union breaks when the fix keeps both sides' intent, run `make gate` there, commit
the merge with the version's `Change:` trailer, its body naming each resolved hunk: the file, both sides' intent and the
union, and end with `Next: /mf-converge, then /mf-release`, or with
`Next: /mf-ship, in the primary.` for a version with an unticked phase. A red gate SHALL
halt with the merge open and write `.minions/integrate/<change-id>.red`, which the commit deletes. It SHALL NOT
release, tag, push or rebase.

#### Scenario: The next version is ready
- **WHEN** the version has every phase ticked and clean findings files
- **THEN** the station merges the default branch into its worktree, gates the result and commits the merge

#### Scenario: The next version is not ready
- **WHEN** `change-id` names a version with an unticked phase
- **THEN** the station halts, naming that version, and merges nothing

#### Scenario: The lowest open version is not ready, and no id is named
- **WHEN** the lowest-id open version has an unticked phase and a later one is ready
- **THEN** the station takes the later one

#### Scenario: The merged tree fails the gate
- **WHEN** `make gate` fails on the merged tree
- **THEN** the station halts with the merge open, and `.minions/integrate/<change-id>.red` exists

#### Scenario: A settled dependent has no build yet
- **WHEN** `/mf-integrate <change-id>` commits the merge of a version with an unticked phase
- **THEN** its last line is `Next: /mf-ship, in the primary.`

#### Scenario: Both sides add in one hunk
- **WHEN** the branch adds items to a list and the default branch removes another item from it, on one line
- **THEN** the station keeps the branch's items and the removal, gates the result, and commits the merge
- **AND** the commit's body names the file, both sides' intent and the union

### Requirement: A semantic conflict is handed to the person with the merge open

When the delta check reports a changed requirement, or git leaves a conflict that is not additive (one side editing what the
other removed, two values for one thing, designs that disagree, a choice between behaviours),
`skills/mf-integrate/SKILL.md` SHALL halt with the merge in progress in the version's worktree, write
`.minions/integrate/<change-id>.md` holding both intents and a proposed resolution, and continue from the open
merge on its next run.

#### Scenario: Both versions changed one requirement
- **WHEN** the branch's delta modifies a requirement the default branch also changed since the base
- **THEN** the merge stays open, the note names both changes, and the next run continues from `MERGE_HEAD`

#### Scenario: Two values for one thing
- **WHEN** the branch sets a constant to one value and the default branch sets it to another
- **THEN** the merge stays open, the note names both changes, and nothing is resolved
