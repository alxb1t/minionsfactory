## ADDED Requirements

### Requirement: The integrate station renumbers the branch's changelog entries

`skills/mf-integrate/scripts/integrate.py decisions` SHALL renumber each colliding decision id cited in the `[Unreleased]` entries
of the `CHANGELOG.md` the `changelog` rule wrote, and SHALL leave the released sections as they are. It SHALL NOT compare
`CHANGELOG.md` with a three-way merge of its sides.

#### Scenario: A renumbered decision in the branch's entry
- **WHEN** the branch's `[Unreleased]` entry cites a decision id the default branch also added, and a released section cites the
  same id
- **THEN** `decisions` renumbers the entry's citation, keeps the released section's, and exits 0

### Requirement: A blocked dependent comes back with its dependency

When a run takes back a version — a rejoin, a newly cut version, a fixed halt — `conduct.py` SHALL also take back each version
blocked by it, in change-id order, so a chain comes back in one pass with no request for its dependents. A rejoin SHALL re-read the
plan only of a version the run's plan does not hold. A version whose branch holds no commit but merges past its cut commit SHALL
count as cut-only.

#### Scenario: A chain comes back
- **WHEN** `0002` names `0001` in `after:`, `0003` names `0002`, `0001` halted, and the person rejoins `0001` alone
- **THEN** `0002` and `0003` come back with it, and the run ships all three

#### Scenario: A cut-only version merged in once
- **WHEN** a version holds only its cut commit and a merge of the default branch, and the default branch then changes
  `README.md`
- **THEN** the run merges the default branch in again, with no halt

### Requirement: The converge fixer leaves the plan to the person

`skills/mf-converge/SKILL.md`'s fix pass SHALL NOT edit the change's `tasks.md` or `design.md`. A card whose fix needs either SHALL be
set `wontfix`, naming the amend the person commits, and the round SHALL halt `amend needed — <card ids>`; the person's amend answers
that halt. Step 7's verify round SHALL
run `gate_check.py` as Step 1.6 does, after the gate.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, and the round halts `amend needed`

### Requirement: A verify halt is diagnosed by the run

When a version's converge halt is Step 1.6's `verify: halt`, `conduct.py` SHALL write its diagnosis to `.minions/rescue/<id>.md`
itself, from the halt line, through a file opened without following a link, start no rescue worker, and log `rescue — <id>: diagnosed
· <file>`. The diagnosis, and every rescue proposal `skills/mf-rescue/SKILL.md` writes, SHALL name the command the run takes back:
`conduct.py rejoin <id>` while a run is live, else `/mf-ship`. A version whose models file says `[rescue] skip = true` SHALL get no
diagnosis.

#### Scenario: A `Verify:` changed since the cut
- **WHEN** converge halts at Step 1.6 with `verify: halt`
- **THEN** the run writes the diagnosis with no worker, naming the person's amend commit and the command, and the version stays
  halted

## MODIFIED Requirements

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, take the version `change-id` names, or with none the
ready version with the lowest change id among the unmerged branches named by a change id that hold their change or a
release commit. It SHALL halt, naming the version, when the named one is not ready, or when none is: a phase unticked,
converge not clean, or an `after:` id missing from its tree. A named version whose merge is open with its note SHALL be
ready. It SHALL merge the default branch into that version's worktree, resolve each additive hunk git leaves — one whose union
keeps every addition and every removal of both sides and changes nothing else, whether its edits separate as lines, list
items or sentences — and a merged test the union breaks when the fix keeps both sides' intent, commit the merge with the version's
`Change:` trailer, its body naming each resolved hunk: the file, both
sides' intent and the union, then run `make gate` on the worktree through `skills/mf-converge/scripts/gate_run.py --tree
<worktree>`, and end with `Next: /mf-converge, then /mf-release`, or with `Next: /mf-ship, in the primary.` for a version with an
unticked phase. A red gate on a merged test the union broke SHALL be fixed once, when the fix keeps both sides' intent, by amending
the merge commit, and gated again. Any other red gate SHALL halt with the merge committed and write
`.minions/integrate/<change-id>.red` holding `head: <sha>`, the head the gate judged; with no merge open, `conduct.py` SHALL read
the version as halted while that sha is `HEAD`, and as to integrate again once it is not. Its integrate check SHALL fail while that
`.red` stands, and read the newest first-parent merge, so the person's fix commit after it passes once a green gate deletes it. It SHALL NOT release, tag, push or rebase.

#### Scenario: The next version is ready
- **WHEN** the version has every phase ticked and clean findings files
- **THEN** the station merges the default branch into its worktree, commits the merge and gates the worktree

#### Scenario: The next version is not ready
- **WHEN** `change-id` names a version with an unticked phase
- **THEN** the station halts, naming that version, and merges nothing

#### Scenario: The lowest open version is not ready, and no id is named
- **WHEN** the lowest-id open version has an unticked phase and a later one is ready
- **THEN** the station takes the later one

#### Scenario: The merged tree fails the gate
- **WHEN** `make gate` fails on the committed merge, on no test the union broke
- **THEN** the station halts with the merge committed, and `.minions/integrate/<change-id>.red` names the head it gated

#### Scenario: Coverage reads only the branch's lines
- **WHEN** the default branch brought in lines the branch's tests do not cover
- **THEN** the gate after the merge commit reads the branch's own changed lines alone

#### Scenario: A settled dependent has no build yet
- **WHEN** `/mf-integrate <change-id>` commits the merge of a version with an unticked phase
- **THEN** its last line is `Next: /mf-ship, in the primary.`

#### Scenario: Both sides add in one hunk
- **WHEN** the branch adds items to a list and the default branch removes another item from it, on one line
- **THEN** the station keeps the branch's items and the removal, commits the merge, and gates the worktree
- **AND** the commit's body names the file, both sides' intent and the union

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, with no pickup, unless the
selection is merges and amends only and every merge replays by the fixed rules, when the round is by rule and runs no worker.
**Merges and amends** are merges, and the person's `docs(<id>): amend the change directory` commits touching only
`openspec/changes/<id>/`. When the selection is merges and amends only, the run SHALL count its own rounds: one judge round and
at most one fix round, then a halt, with `round:` carrying on past three. Any other selection SHALL count against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup
- **AND WHEN** the selection is merges and amends only and every merge replays by the fixed rules
- **THEN** the round is by rule: no freeze, no worker, no verify round, and no pickup

#### Scenario: The catch-up round judges a merge-in by what the merge decided
- **WHEN** the range `head..HEAD` holds a merge of the default branch whose conflicts were resolved by hand
- **THEN** the round's patch holds that merge's remerge-diff, not the default branch's changes
- **AND** a merge with no conflicts adds nothing to read, and the gate judges the combined tree

#### Scenario: A catch-up over merges only has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge alone
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap
- **AND WHEN** a blocking finding is still open after its one fix round
- **THEN** it halts with `cap reached`, and the stage reads `converge-halted`

#### Scenario: A catch-up over a merge and the person's amend has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge and the person's amend of the change directory
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3 and the selection holds a commit that is neither a merge nor the person's amend
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: A converge halt answered by the person converges afresh

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the backlog lock's
SHALL be void when its head is both findings files' `head:` and `HEAD` is past it, a descendant that is not it: `conduct.py`'s
stage SHALL be `converge`, and its converge check SHALL not read the old halt. A halt in a catch-up run whose findings files are
both still clean, a Step 1.6 `verify: halt`, and a fix pass's `amend needed` halt SHALL also be void when `HEAD` is past its head and every commit since is the person's `docs(<id>): amend the
change directory`, one parent each, touching only `openspec/changes/<id>/`. Any other halt naming no head, one past the judged head,
and one whose head is no ancestor of `HEAD` SHALL stand. `skills/mf-converge/SKILL.md`, finding its newest run's top line a void
catch-up halt with both files clean, SHALL run the catch-up round again; finding any other void halt, it SHALL open a run marked `· amended`, and
converge from round 1 over the whole change, the findings files restarting at `round: 1`. A run marked `· grant` that resumes
SHALL stay a granted round.

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a new run marked `· amended`, from round 1, with no grant

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, or in a catch-up run, so its head is not the findings files' `head:`, and a
  commit other than the person's amend follows
- **THEN** its stage stays `converge-halted`, and no `· amended` run opens

#### Scenario: The person's amend answers a catch-up halt
- **WHEN** a catch-up round halts at Step 1.6 on a `Verify:` changed since the cut, and the person commits `docs(<id>): amend the
  change directory`
- **THEN** its stage is `converge`, and the next run's catch-up round counts the merge and the amend as its own

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
its conflicts with the `changelog` and `decisions` rules alone, run the `delta` rule, and exit 0 when `delta` names no requirement
and the rebuilt tree equals the merge's tree, else 1. Its git SHALL run no hook and fetch no missing object.
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

#### Scenario: A merge and the person's amend
- **WHEN** the selection is a merge that replays and the person's amend of the change directory, and Step 1 passes
- **THEN** the catch-up writes both findings files clean with `## By rule`, naming the merge and the amend, and dispatches no worker

#### Scenario: A merge someone judged
- **WHEN** the merge holds a hunk the integrator resolved as a union, a person's resolution, a test edited, or a requirement
  the delta edits that the default branch changed
- **THEN** replay exits 1, and the catch-up round dispatches review and security as before

#### Scenario: A merge of a commit the default branch does not hold
- **WHEN** the merge's second parent is not an ancestor of the default branch, though git merged it with no conflict
- **THEN** replay exits 2, and the catch-up halts, naming the merge, with no findings file written clean

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the offline base, the release ledger and a person's gate approval
in the home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, or a
default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset time named.

#### Scenario: A HUMAN phase halts its version
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** that version halts, naming the phase, and every other version goes on

#### Scenario: A later version halts, and the earlier ships
- **WHEN** two versions run and the later one's build check fails
- **THEN** the earlier is released, merged and pushed
- **AND** the run closes naming the later as halted and the earlier's tag as released, and exits 1

#### Scenario: A later version ships past a halted one
- **WHEN** two versions run and the earlier one's build check fails
- **THEN** the later is released, merged and pushed
- **AND** the run closes naming the earlier as halted and the later's tag as released, and exits 1

#### Scenario: A halted dependency blocks a chain
- **WHEN** a version halts, a second has it in `after:`, and a third has the second in `after:`
- **THEN** neither starts a worker, each logs `blocked — by <id>`, and the closing line names both as blocked

#### Scenario: No open version can start
- **WHEN** one version sits at a `**HUMAN` phase, and every other is `waiting`
- **THEN** the run starts no worker, and closes naming the first as halted and the others as blocked

#### Scenario: A failed probe stops the run
- **WHEN** the probe's check fails
- **THEN** no version starts a worker, and the run closes naming `run` as halted

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again

#### Scenario: The person resolves a semantic conflict
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/integrate/<change-id>.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing
