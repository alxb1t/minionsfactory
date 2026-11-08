## ADDED Requirements

### Requirement: A dependent builds on its dependency's built head

`conduct.py` SHALL stack a dependent once its one unreleased `after:` dependency, lower than it, has a **built head** — the
commit its `.minions/changes/<id>/build.done` names, the tip of its branch or an ancestor of it, with every `## Progress` box
ticked — and the run records no halt for that dependency, and that head holds the dependent's merge-base with the default
branch. To stack, it SHALL write the head's full sha to `.minions/changes/<change-id>/stacked-on`, merge the built head into
the dependent's worktree with no agent, by `integrate.py`'s rules and with no `delta` check, commit it as
`chore(stack): merge <id> at <sha7> into <change-id>`, and log `stacked — on <id> at <sha7>`; the dependent then builds. A
dependency's thread that reads its stage past the build SHALL wake each dependent waiting on it. A dependent with two or more
unreleased dependencies, a halted one, or a built head that lacks its base SHALL wait as an unstacked dependent does. Until its
dependency's release is merged in, a stacked dependent whose build is done SHALL read as `stacked` in `conduct.py status` and
start no converge; while the dependency has not released, it SHALL wait for the dependency's thread to end, and a dependency
that ends unreleased SHALL block it. Once the dependency released — before or after the dependent's build ended — the run
SHALL merge the default branch into it, as for any dependent, remove `stacked-on` once that merge is committed, read the
build as closed past that merge, and run converge from round 1. `conduct.py` SHALL also remove a `stacked-on` that stands
before it spawns converge or the release. A stacked dependent re-run before its build ends SHALL build on, waiting on no
thread.

While `stacked-on` stands, `mf-build`'s gate check and metrics, `mf-simplify`'s range and the gate's diff coverage SHALL take
the sha it names as their base, in place of the merge-base with the default branch; the gate SHALL take only a line of 40
hex digits from it, resolved through `git rev-parse --verify`, never as text in its recipe.

An amend of the dependency's change directory past the stacked-on head that touches its `proposal.md` or changes its
`design.md`'s `## Decisions` SHALL, while `stacked-on` stands — before the dependency's release or after it, until the merge
back — reset the dependent's branch to its cut commit, past the config refusals, remove `stacked-on`, and log `reset`
naming the head it left; so SHALL a stacked-on head that the branch of a dependency that has not released no longer holds.
A dependent reset while its dependency has not released SHALL wait for a built head past that amend; one whose dependency
released SHALL get the default branch merged in and build again. The reset SHALL be read before each of the dependent's
stages, at each poll of its wait and before the merge back, never during a station's run.

#### Scenario: A dependent builds while its dependency converges
- **WHEN** `0002` names `0001` in `after:`, and `0001`'s build check passes while its converge is held
- **THEN** `conduct.py` commits `chore(stack): merge 0001-todo at <sha7> into 0002-marks`, `stacked-on` holds `0001`'s built
  head, and `0002` builds
- **AND WHEN** `0002`'s build is done and `0001` has not released
- **THEN** `conduct.py status` prints `0002-marks · stacked`, and no converge of `0002` starts
- **AND WHEN** `0001` releases
- **THEN** the run merges the default branch into `0002`, `stacked-on` is gone, and `0002`'s converge runs, then its release

#### Scenario: A dependency re-plans
- **WHEN** `0002` is stacked on `0001`'s built head, and an amend of `0001`'s change directory past that head touches its
  `proposal.md`
- **THEN** `0002`'s branch is back at its cut commit, `stacked-on` is gone, and the run log names the head it left
- **AND WHEN** the amend touches `tasks.md` alone
- **THEN** `0002` stays stacked

#### Scenario: A dependency re-plans and releases during the dependent's build
- **WHEN** `0002` is stacked on `0001`'s built head, an amend of `0001`'s change directory past that head touches its
  `proposal.md`, and `0001` releases before `0002`'s merge back
- **THEN** before the merge back `0002`'s branch is back at its cut commit, `stacked-on` is gone, and the run log names the
  head it left
- **AND** the run merges the default branch into `0002`, and `0002` builds again

#### Scenario: Two unreleased dependencies
- **WHEN** a version names two unreleased versions in `after:`, each with a built head
- **THEN** it stacks on neither, and waits as before

#### Scenario: A stacked base for diff coverage
- **WHEN** `make -n gate` runs in a version's worktree while its `stacked-on` names a commit
- **THEN** it prints `--compare-branch=<that sha>`
- **AND WHEN** `stacked-on` holds text that is no commit, or a shell command
- **THEN** it prints `--compare-branch=main`, and runs nothing the text names

## MODIFIED Requirements

### Requirement: A version declares what it builds on

`skills/mf-cut-change/SKILL.md` SHALL take `after=<id>[,<id>]`, halting unless each id is an open version with a lower
number, and SHALL write `after: [<ids>]` into `proposal.md`'s frontmatter. A name a design takes from an `after:`
change's design, and a MODIFIED title a delta takes from an `after:` change's delta, SHALL count as present at the cut.
`conduct.py` SHALL start a dependent once each id has released, or once it stacks, as *A dependent builds on its dependency's
built head* says, and SHALL then merge the default branch into its cut-only branch, with no agent, running `integrate.py delta`
on the open merge and committing it when the check passes. A requirement the check names SHALL leave the merge open, with its
note under `.minions/changes/<change-id>/`, and halt the version as `integrating`. `mf-build` SHALL halt unless each id has
`openspec/changes/archive/<id>/` in `HEAD`, or, while `.minions/changes/<change-id>/stacked-on` stands, the commit it names is
an ancestor of `HEAD` and holds `openspec/changes/<id>/tasks.md`. `mf-release` and `mf-integrate`'s Ready SHALL halt unless each
id has `openspec/changes/archive/<id>/` in `HEAD`. `conduct.py status` SHALL print `waiting` for a dependent whose dependency has
not released and that has not stacked. An `after:` edited past the cut SHALL stop no other version: an unreleased id that is
not lower SHALL block its version, and an edit that leaves a running version `waiting` SHALL halt it.

#### Scenario: An edit makes a cycle
- **WHEN** two versions name each other in `after:`, or one names itself, and a third is free
- **THEN** the named versions block with no worker, the third ships, and the run closes

#### Scenario: A worker edits its own `after:`
- **WHEN** a build worker adds an unreleased id to its version's `after:`
- **THEN** that version halts on `waiting`, and every other version goes on

#### Scenario: A dependent waits
- **WHEN** a version names a lower open version in `after:`, and `mf-ship` runs
- **THEN** its build starts only once that version's build check passes, on its built head, and its converge only after that
  version's release, on a tree that holds it
- **AND** unrelated versions run in parallel meanwhile

#### Scenario: A dependent's delta edits what its dependency changed
- **WHEN** an unstacked dependent's delta modifies a requirement the default branch changed since its base, and the run
  takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** the merge stays open, the note names both changes, and the version halts with no build
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` builds the version

#### Scenario: A stacked dependent's delta edits what its dependency released
- **WHEN** a stacked dependent's build is done, its delta modifies a requirement its dependency's release changed, and the
  run takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** the merge back stays open, the note names both changes, `stacked-on` stands, and the version halts as
  `integrating`, its build done
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` removes `stacked-on`, builds nothing again, and runs converge from round 1

#### Scenario: A cut names a dependency it cannot have
- **WHEN** `after=` names an id that is merged, unknown, or not lower than the change's
- **THEN** the cut halts, naming it

#### Scenario: A dependent built by hand
- **WHEN** `mf-build` starts on a change whose `after:` id is not in `HEAD`'s archive, and no `stacked-on` stands
- **THEN** it halts, naming `I17`

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue and, under its switch, its
supervisor, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker, save one
stacked on it before the halt, which builds on and then blocks. A failed
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
`.minions/debt.lock`, or an older `.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, an old
`.minions/backlog.md` beside `.minions/debt.md` or a file at `.minions/backlog.lock` or `.minions/debt.lock`, or one that is a
link, or a default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset
time named.

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

#### Scenario: A dependency halts after its dependent stacked
- **WHEN** a dependent stacked on its dependency's built head, and the dependency then halts in converge
- **THEN** the dependent's build runs to its end, and the dependent then logs `blocked — by <id>`

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
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/changes/<change-id>/`,
  and the run takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/changes/<change-id>/integrate.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

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
more, an unticked phase, no merge open and no `stacked-on`, whose base the default branch passed changing a gate makefile, `AGENTS.md`,
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
- **AND WHEN** the version's build has begun on its dependency's built head, `stacked-on` standing
- **THEN** the run merges nothing into it until its dependency releases

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

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's own `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines — those past the base's entries, which a stacked branch's base
holds and the default branch has released; a branch whose entries do not hold the base's SHALL halt the rule. It SHALL
renumber the branch's new decision to the next id free
on the default branch with its citations, and report each MODIFIED or REMOVED requirement title of the branch's delta
that the default branch changed since the branch's base. `.gitattributes` SHALL NOT set `merge=union`.
A **planned decision** — an id the branch's `openspec/changes/` files cite as `D<n> · <title>`, above the base's highest id and
headed nowhere in the branch's `docs/decisions.md` — SHALL count as the branch's new decision, save when the default branch's
`### D<n> · <title>` heading carries that title: then it is a dependency's, and stays. An id the plan cites with no title SHALL stay.
`skills/mf-converge/scripts/gate_check.py` SHALL compute the same moves for a merge commit. `conduct.py` and `integrate.py replay`
SHALL run the `decisions` rule on every merge they open, conflicted or clean, and the `changelog` rule on a conflicted
`CHANGELOG.md` and on every merge whose base holds `## [Unreleased]` entries.
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

#### Scenario: A stacked branch's CHANGELOG
- **WHEN** a branch stacked on its dependency's built head holds that head's `[Unreleased]` entries and its own after them,
  and the default branch released the dependency, git merging `CHANGELOG.md` cleanly
- **THEN** the merge's `[Unreleased]` holds the branch's own entries alone, above the dependency's release section
- **AND WHEN** the branch's entries do not hold the base's
- **THEN** `changelog` halts

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

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version), and the time a dependent waits on its `after:` ids (each `wait` event of the version until its next event in
the same run, a version with none 0); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. A Codex station's tokens SHALL be the sum over its log's `turn.completed` events of their input and output tokens, and
its dollars those tokens priced by `skills/mf-review-metrics/prices.toml` under the model its log's spawn line names; a model
with no row there, or no model named, SHALL make the cost metrics a gap naming it, and SHALL leave the token metrics read. A
checker the mailbox started, `converge-<role>` or `converge-shadow-<role>`, SHALL count in the cost and tokens of the stage
whose converge spawn holds its start, never in its minutes, and a `converge-<role>` log's tokens in that role's. The cut's `diff-lines` and `diff-files` SHALL be the
collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: A dependent's wait
- **WHEN** a version's run log holds `wait — after 0001-x` at `09:08:30` and its build spawn at `09:09:00`
- **THEN** `after-wait-minutes` reads `0.5`
- **AND WHEN** a version's run log holds no `wait` event
- **THEN** `after-wait-minutes` reads `0`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

#### Scenario: A converge on Codex
- **WHEN** a version's converge log is a Codex JSON log whose spawn line names a model the price table holds
- **THEN** `cost-usd-converge` holds its priced dollars and `tokens-converge` its summed tokens
- **AND WHEN** the price table holds no row for that model
- **THEN** `cost-usd-converge` is a gap naming the model, and `tokens-converge` is read

#### Scenario: A checker through the mailbox
- **WHEN** a version's run log spawns `converge-conformance` inside its converge, its log a priced Codex log
- **THEN** `cost-usd-converge` and `tokens-converge` hold that log's dollars and tokens beside converge's own,
  `conformance-tokens-per-confirmed` counts its tokens, and `minutes-converge` is unchanged
