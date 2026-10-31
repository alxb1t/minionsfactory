## MODIFIED Requirements

### Requirement: A cut reserves its id against every open version branch

`skills/mf-cut-change/SKILL.md` SHALL take a change id only when its number is higher than every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch and on every branch named by a change id and not merged
into it. It SHALL take `bump=minor|patch`, write `bump:` into `proposal.md`'s frontmatter, and assign no number.

#### Scenario: Two cuts while one change is open
- **WHEN** a version branch holding change `0040-x` is not yet merged, and a second cut is asked for id `0040-y`
- **THEN** the cut halts: the id is taken by an open branch

### Requirement: The plan station checks which versions can run side by side

When the person names versions to run side by side, `skills/mf-plan/SKILL.md` SHALL compare their briefs' `## Facts`
paths and `## Phases` files, and SHALL warn of any pair that touches a file in common, suggesting `after:` when one needs the other's code. It SHALL
propose no order.

#### Scenario: Two versions that touch the same skill
- **WHEN** two briefs both name `skills/mf-release/SKILL.md`
- **THEN** `mf-plan` warns, naming the file, and proposes no order

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, take the version `change-id` names, or with none the
ready version with the lowest change id among the unmerged branches named by a change id that hold their change or a
release commit. It SHALL halt, naming the version, when the named one is not ready, or when none is: a phase unticked,
converge not clean, or an `after:` id missing from its tree. A named version whose merge is open with its note SHALL be
ready. It SHALL merge the default branch into that version's worktree, run `make gate` there, commit
the merge with the version's `Change:` trailer, and end with `Next: /mf-converge, then /mf-release`. A red gate SHALL
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

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor running
`mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL act under `conduct.py`'s allowlist on Claude Code — extended by
`AGENTS.md`'s `Ship tools:` line, with forced pushes, hard resets and cleans denied, its shell reaching the directory
`Worktrees:` names and nothing outside it, its prompt carrying the shell rules — or the workspace-write sandbox on Codex, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt a version by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run.

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

## REMOVED Requirements

### Requirement: A halt stops its version, and a re-run resumes

**Reason:** a halt no longer holds the versions behind it, so its scenario goes.

**Migration:** see *A halt stops only its version, and a re-run resumes*.

## ADDED Requirements

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory: a re-run derives every stage again and continues.

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

#### Scenario: A failed probe stops the run
- **WHEN** the probe's check fails
- **THEN** no version starts a worker, and the run closes naming `run` as halted

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again

#### Scenario: The person resolves a semantic conflict
- **WHEN** integrate halted on a semantic conflict or a red gate, with the merge open and its note under
  `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

### Requirement: A version declares what it builds on

`skills/mf-cut-change/SKILL.md` SHALL take `after=<id>[,<id>]`, halting unless each id is an open version with a lower
number, and SHALL write `after: [<ids>]` into `proposal.md`'s frontmatter. A name a design takes from an `after:`
change's design SHALL count as present at the cut. `conduct.py` SHALL start a dependent only once each id has released,
and SHALL then merge the default branch into its cut-only branch, with no agent, running `integrate.py delta` on the open
merge and committing it when the check passes. A requirement the check names SHALL leave the merge open, with its note
under `.minions/integrate/`, and halt the version as `integrating`. `mf-build` and `mf-release` SHALL halt unless each id
has `openspec/changes/archive/<id>/` in `HEAD`. `conduct.py status` SHALL print `waiting` for a dependent whose dependency
has not released.

#### Scenario: A dependent waits
- **WHEN** a version names a lower open version in `after:`, and `mf-ship` runs
- **THEN** its build starts only after that version's release, on a tree that holds it
- **AND** unrelated versions run in parallel meanwhile

#### Scenario: A dependent's delta edits what its dependency changed
- **WHEN** a dependent's delta modifies a requirement the default branch changed since its base
- **THEN** the merge stays open, the note names both changes, and the version halts with no build
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` builds the version

#### Scenario: A cut names a dependency it cannot have
- **WHEN** `after=` names an id that is merged, unknown, or not lower than the change's
- **THEN** the cut halts, naming it

#### Scenario: A dependent built by hand
- **WHEN** `mf-build` starts on a change whose `after:` id is not in `HEAD`'s archive
- **THEN** it halts, naming `I17`
