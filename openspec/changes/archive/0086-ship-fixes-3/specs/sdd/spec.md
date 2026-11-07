## MODIFIED Requirements

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines, renumber the branch's new decision to the next id free
on the default branch with its citations, and report each MODIFIED or REMOVED requirement title of the branch's delta
that the default branch changed since the branch's base. `.gitattributes` SHALL NOT set `merge=union`.
A **planned decision** — an id the branch's `openspec/changes/` files cite as `D<n> · <title>`, above the base's highest id and
headed nowhere in the branch's `docs/decisions.md` — SHALL count as the branch's new decision, save when the default branch's
`### D<n> · <title>` heading carries that title: then it is a dependency's, and stays. An id the plan cites with no title SHALL stay.
`skills/mf-converge/scripts/gate_check.py` SHALL compute the same moves for a merge commit. `conduct.py` and `integrate.py replay`
SHALL run the `decisions` rule on every merge they open, conflicted or clean.
A MODIFIED title whose delta block only inserts into the default branch's current block — every edit an insertion, whitespace
ignored — and keeps nothing the default branch removed from the base's block SHALL NOT be reported. A delta that changes or
removes a line of that block, one that keeps what the default branch removed, a title the default branch removed, and every
REMOVED title the default branch changed SHALL be reported.

#### Scenario: Both sides added a decision
- **WHEN** the default branch took `D45` and the branch added its own `D45`
- **THEN** the branch's decision is renumbered `D46`, its citations with it

#### Scenario: Both sides changed a CHANGELOG
- **WHEN** the default branch cut a release section and the branch holds `[Unreleased]` entries
- **THEN** the entries stay above the release section, the blank lines intact

#### Scenario: A planned decision taken while the version waits
- **WHEN** the base's highest id is `D58`, the branch's plan cites `D59 · Branch rule` with no heading for it, and the default
  branch took `D59 · Main rule`, git merging `docs/decisions.md` cleanly
- **THEN** `decisions` renumbers the plan's `D59` to `D60`, its citations with it, and `gate_check.py` reads the same move from
  the merge commit

#### Scenario: A dependency's decision cited by title
- **WHEN** the branch's plan cites `D59 · Main rule`, and the default branch's `D59` heading carries `Main rule`
- **THEN** `decisions` leaves every `D59` as it is

#### Scenario: A delta that only inserts
- **WHEN** the default branch changed a requirement since the base, and the branch's MODIFIED block holds the default branch's
  current block with lines added
- **THEN** `delta` reports nothing for it, and the merge goes on

#### Scenario: A delta that changes a line the default branch holds
- **WHEN** the default branch changed a requirement since the base, and the branch's MODIFIED block rewrites a line of the default
  branch's current block
- **THEN** `delta` reports the title, and exits 1

#### Scenario: A delta that keeps what the default branch removed
- **WHEN** the default branch dropped a sentence of a requirement since the base, and the branch's MODIFIED block keeps that
  sentence and adds a clause
- **THEN** `delta` reports the title, and exits 1

### Requirement: A semantic conflict is handed to the person with the merge open

When the delta check reports a changed requirement, or git leaves a conflict that is not additive (one side editing what the
other removed, two values for one thing, designs that disagree, a choice between behaviours),
`skills/mf-integrate/SKILL.md` SHALL halt with the merge in progress in the version's worktree, write
`.minions/changes/<change-id>/integrate.md` holding both intents and a proposed resolution, and continue from the open
merge on its next run. A MODIFIED delta that only inserts into the default branch's current block, and keeps nothing the default
branch removed, SHALL NOT count as a semantic conflict.

#### Scenario: Both versions changed one requirement
- **WHEN** the branch's delta modifies a requirement the default branch also changed since the base, and changes or removes a
  line of the default branch's current block
- **THEN** the merge stays open, the note names both changes, and the next run continues from `MERGE_HEAD`

#### Scenario: Two values for one thing
- **WHEN** the branch sets a constant to one value and the default branch sets it to another
- **THEN** the merge stays open, the note names both changes, and nothing is resolved

#### Scenario: The branch already holds the default branch's change
- **WHEN** the branch's delta modifies a requirement the default branch also changed, and the delta's block holds the default
  branch's block with lines added
- **THEN** no note is written, and the merge is committed

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
a conflicted `CHANGELOG.md` with the `changelog` rule, run the `decisions` rule on every merge, conflicted or clean, run the
`delta` rule, and exit 0 when `delta` names no requirement and the rebuilt tree equals the merge's tree, else 1. Its line SHALL
name each path a rule settled: one git left unmerged, and `docs/decisions.md` when the `decisions` rule renumbered. Its git SHALL
run no hook and fetch no missing object.
It SHALL exit 2, rebuilding nothing, for a commit without two parents or whose second parent the default branch does not hold.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL first run *Catch-up scope*'s ancestry and parent checks, halting when one
fails, then run `replay` for each merge in its selection; when every merge replays and the selection holds nothing else but the
person's amends, which Step 1's gate and `gate_check.py` judge, it SHALL write both findings files `head: HEAD` and `verdict: clean`
with a `## By rule` section naming each merge's paths and each amend, log `round N · by rule — clean, <paths>`, dispatch no worker,
and count the round within the merges-and-amends count. Any other selection SHALL take the catch-up round as before.

#### Scenario: A changelog the rule settled
- **WHEN** the integrate merge conflicted in `CHANGELOG.md` alone, settled by `integrate.py changelog`
- **THEN** the catch-up replays it, writes both findings files clean with `## By rule`, dispatches no worker, and the release
  passes its preconditions

#### Scenario: A decision renumbered in a cleanly merged file
- **WHEN** git merged `docs/decisions.md` with no conflict, and the integrate merge's `decisions` rule renumbered the branch's id
- **THEN** replay prints `replay: by rule — docs/decisions.md` and exits 0

#### Scenario: A merge and the person's amend
- **WHEN** the selection is a merge that replays and the person's amend of the change directory, and Step 1 passes
- **THEN** the catch-up writes both findings files clean with `## By rule`, naming the merge and the amend, and dispatches no worker

#### Scenario: A merge someone judged
- **WHEN** the merge holds a hunk the integrator resolved as a union, a person's resolution, a test edited, or a requirement
  the delta edits that the default branch changed, the delta changing or removing a line of the default branch's block
- **THEN** replay exits 1, and the catch-up round dispatches review and security as before

#### Scenario: A merge of a commit the default branch does not hold
- **WHEN** the merge's second parent is not an ancestor of the default branch, though git merged it with no conflict
- **THEN** replay exits 2, and the catch-up halts, naming the merge, with no findings file written clean

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor the models
file names for it, or of the executor running `mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/changes/<change-id>/models.toml`
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
`git -C <tree> merge <default>`, or, when the merge is clean and its `decisions` rule halts, that halt and
`git -C <tree> merge --no-ff --no-commit <default>`; one
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
- **AND WHEN** the merge is clean and its `decisions` rule halts
- **THEN** that version halts before its next worker, naming the rule's halt and
  `git -C <tree> merge --no-ff --no-commit <default>`
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
- **AND WHEN** the repo's git config holds a key a run refuses, or changed since the run read it
- **THEN** nothing is removed, and the run logs it
- **AND WHEN** the `Worktrees:` path joined with the change id is a link
- **THEN** nothing is removed, and the run logs it
