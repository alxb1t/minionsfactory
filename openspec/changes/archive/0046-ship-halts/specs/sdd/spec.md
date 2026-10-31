## MODIFIED Requirements

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, with no
pickup. When the selection is merges only, the run SHALL count its own rounds: one judge round and at most one fix
round, then a halt, with `round:` carrying on past three. Any other selection SHALL count against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup

#### Scenario: The catch-up round judges a merge-in by what the merge decided
- **WHEN** the range `head..HEAD` holds a merge of the default branch whose conflicts were resolved by hand
- **THEN** the round's patch holds that merge's remerge-diff, not the default branch's changes
- **AND** a merge with no conflicts adds nothing to read, and the gate judges the combined tree

#### Scenario: A catch-up over merges only has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge alone
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap
- **AND WHEN** a blocking finding is still open after its one fix round
- **THEN** it halts with `cap reached`, and the stage reads `converge-halted`

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3 and the selection holds a commit that is not a merge
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time in change-id order, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor running
`mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL act under `conduct.py`'s allowlist on Claude Code — extended by
`AGENTS.md`'s `Ship tools:` line, with forced pushes, hard resets and cleans denied, its shell reaching the directory
`Worktrees:` names and nothing outside it, its prompt carrying the shell rules — or the workspace-write sandbox on Codex, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt a version by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run.

#### Scenario: Two cut versions ship
- **WHEN** two versions are cut, each in its own worktree, and `mf-ship` runs to the end
- **THEN** both are released, merged and pushed in change-id order, the later one integrated and judged by a
  catch-up round first, and only the primary is left

#### Scenario: A worker runs a command off the list
- **WHEN** a build worker's command is denied by the allowlist and the build's check still passes
- **THEN** the run goes on, and the report lists the denial
- **AND WHEN** the build's check fails
- **THEN** the version halts, and its `halt` line names the denial

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
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

## REMOVED Requirements

### Requirement: A halt stops the ship run, and a re-run resumes

**Reason:** a failed check now halts its version, not the run.

**Migration:** see *A halt stops its version, and a re-run resumes*.

## ADDED Requirements

### Requirement: A halt stops its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version's build
and converge SHALL go on. Integrate and release SHALL keep change-id order, so a halt SHALL hold every version behind
it. A failed probe and a conductor crash SHALL stop the run. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens. A run with a halt SHALL close on
`run · halt — halted <ids> · held <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every `halt`
line, then the closing line, and SHALL end a held version's line with `held behind <id>`. The run SHALL keep no state
outside git and the run directory: a re-run derives every stage again and continues.

#### Scenario: A HUMAN phase halts its version
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** that version halts, naming the phase, and nothing behind it is released

#### Scenario: A later version halts, and the earlier ships
- **WHEN** two versions run and the later one's build check fails
- **THEN** the earlier is released, merged and pushed
- **AND** the run closes naming the later as halted and the earlier's tag as released, and exits 1

#### Scenario: An earlier version halts, and the later is held
- **WHEN** two versions run and the earlier one's build check fails
- **THEN** the later finishes build and converge, and is neither integrated nor released
- **AND** the closing line names it as held, and `report` marks it `held behind` the earlier

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
- **AND WHEN** the person settles it and `/mf-integrate` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release
