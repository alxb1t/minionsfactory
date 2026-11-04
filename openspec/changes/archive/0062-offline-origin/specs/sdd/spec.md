## ADDED Requirements

### Requirement: A run goes on while origin cannot be reached

`conduct.py` SHALL keep an **offline base** in the home folder, `~/.mf-ship-origin/<digest>.pushed`: the default branch's sha as
`origin` last listed it, written after every read of `origin` that succeeds and every push of the default branch. A run whose
read of `origin` fails SHALL try it three times, then go on with no remote call, judging the default branch's release merges
against the offline base wherever it judges them against `origin`; with no offline base it SHALL halt, naming
`conduct.py anchor`. Every failed read or push SHALL be a wait, whatever its error; a read that succeeds and shows a refused URL,
a moved default branch or a default named other than the kept one SHALL halt as before. A release made while `origin` is unread
SHALL pass its check as released locally, its worktree removed and its dependents merged from the local default branch, its
ledger entry kept until its push lands. Each release SHALL push what is pending, and the run SHALL try once more before its
close. The `start` line SHALL say when `origin` is unreachable, each failed push SHALL be logged as `push — waiting`, the close
SHALL name what stays unpushed, and `report` SHALL print every wait. `conduct.py anchor` SHALL write the first offline base from
`refs/remotes/origin/<default>` only when no run is live, no offline base stands, the ref is an ancestor of the local default
branch, it is a release merge whose tag stands, and the person names its sha with `--yes <sha>`; with no `--yes` it SHALL print
the sha and subject and write nothing, and otherwise it SHALL refuse, naming the check. The conductor's remote calls SHALL
pass `ssh -o ConnectTimeout=15 -o BatchMode=yes` when neither `GIT_SSH_COMMAND` nor a `core.sshCommand` in the operator's
config, or a file it includes, is set.

#### Scenario: A good read keeps the offline base
- **WHEN** a run reads `origin`, or pushes its default branch
- **THEN** the offline base holds the default branch's sha `origin` lists

#### Scenario: Origin is down at the start
- **WHEN** a run starts and every read of `origin` fails
- **THEN** it logs three tries, its `start` line says `origin: unreachable — pushes wait`, and it builds and converges every open
  version
- **AND WHEN** a commit on the local default branch is no release a ledger head explains, past the offline base
- **THEN** the run halts naming the commit, and pushes nothing

#### Scenario: No offline base
- **WHEN** a run starts, every read of `origin` fails, and no offline base stands
- **THEN** the run halts naming `conduct.py anchor`, and starts no worker

#### Scenario: A release while origin is down
- **WHEN** a version's release merges while `origin` cannot be read
- **THEN** its check passes as released locally, its worktree is removed, a `push — waiting` line is logged, and a dependent
  merges it from the local default branch and ships in the same run
- **AND** the close names the unpushed refs, the default branch and each local release's tag, and `report` prints the wait

#### Scenario: Origin comes back
- **WHEN** `origin` answers again before the run's close, or at the next run's start
- **THEN** the pending default branch and tags are pushed, and the ledger entries whose heads landed are removed
- **AND WHEN** `origin`'s default branch moved meanwhile, so the local one is not its descendant
- **THEN** the run halts as before, and pushes nothing

#### Scenario: A person anchors the offline base
- **WHEN** no run is live, no offline base stands, and `refs/remotes/origin/<default>` is a tagged release merge on the local
  default branch
- **THEN** `conduct.py anchor` prints its sha and subject, naming `--yes <sha>`, and writes nothing
- **AND WHEN** the person runs `conduct.py anchor --yes <sha>` with that sha
- **THEN** it writes the sha as the offline base and prints its sha and subject
- **AND WHEN** a run is live, an offline base stands, the ref is not an ancestor of the local default branch or not a tagged
  release merge, or the `--yes` sha is not the ref's
- **THEN** it refuses, naming the check, and writes nothing

## MODIFIED Requirements

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version SHALL go on
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
- **WHEN** integrate halted on a semantic conflict or a red gate, with the merge open and its note under
  `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. A version with every phase ticked, no converge run begun, and no `.minions/build/<change-id>.done`
naming `HEAD` SHALL be stage `build`, its closing steps left, and SHALL fail the build check: `skills/mf-build/SKILL.md`
SHALL then run its simplify step and the metrics again, restoring first, saved to a patch under `.minions/build/`, a dirty
tree whose paths are all in the change's range while its `.minions/build/<change-id>.closing` mark names `HEAD`, halting and
restoring nothing on a path outside it, a dirty tree with no such mark, or a patch an earlier save left, and SHALL write that file, naming `HEAD` and
simplify's outcome, only once both are done. Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL restore a tree dirty with only its own fold and a staged
archive move to `HEAD`, then start over; a hand release SHALL keep its clean-tree halt. It SHALL re-enter at its merge after reading its preamble against the archived delta, halting on a flag under `merge=yes` and naming it beside the ask by hand,
tagging `HEAD` first when the tag is missing, when `HEAD` is its release commit, converge was clean at `HEAD~1` and the
default branch has not moved. `conduct.py` SHALL read that stage as `release` only when the run logs show the release
worker died and the person left no `.minions/release/<change-id>.held` mark, and as `released` for any other release tip. It SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of
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
- **WHEN** a release worker dies with its fold staged and the change's folder moved
- **THEN** a re-run reads the stage as `release`, restores the tree, and releases with one tag

#### Scenario: A release dies after its commit
- **WHEN** a release worker dies between its commit and its tag, and the default branch has not moved
- **THEN** a re-run reads the stage as `release`, tags `HEAD`, merges and pushes

#### Scenario: A release dies after its tag
- **WHEN** a release worker dies after its commit and tag, and the default branch has not moved
- **THEN** a re-run merges and pushes
- **AND WHEN** the default branch has moved
- **THEN** the stage is `released`, a halt naming the person's recovery

#### Scenario: A release stopped on purpose stays stopped
- **WHEN** a release tip's worker exited 0 before its merge, or a person ran the release and said no
- **THEN** the stage is `released`, a halt naming `/mf-release`, and a re-run merges nothing

#### Scenario: A tip forges a release
- **WHEN** a version's tip says `chore(release): <tag>` and the tag is on another commit
- **THEN** the stage is `released`, and a re-run merges nothing

#### Scenario: A hand release finds uncommitted edits
- **WHEN** a person runs `mf-release` with edits uncommitted under `openspec/` or in `CHANGELOG.md`
- **THEN** the clean-tree precondition halts, and nothing is restored

#### Scenario: A person takes a flagged release
- **WHEN** a person runs `mf-release` on a release tip whose preamble is flagged
- **THEN** it reads the flag, does not halt on it, and names it beside the ask before the merge

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
- **WHEN** a release flags its preamble, commits and dies
- **THEN** a re-run halts on the flag before its merge

#### Scenario: A build dies in simplify
- **WHEN** a build worker ticks and commits every phase, marks its closing steps begun, then dies in simplify with an edit
  left uncommitted
- **THEN** a re-run reads the stage as `build`, closing steps left, and its worker saves the edit to a patch, restores it
  and runs simplify again
- **AND** the run converges only after `.minions/build/<change-id>.done` names `HEAD`

#### Scenario: A dirty tree the build did not mark
- **WHEN** every phase is ticked, no `.done` names `HEAD`, and the tree is dirty with no `.closing` mark naming `HEAD`
- **THEN** `mf-build` halts naming the dirty paths, and restores nothing

#### Scenario: A resume finds an earlier patch
- **WHEN** a resume finds the tree dirty while `.closing` names `HEAD`, and `.minions/build/<change-id>.discarded.patch`
  already exists
- **THEN** `mf-build` halts naming the dirty paths and the patch, restores nothing, and leaves the patch as it was

#### Scenario: A build exits without its marker
- **WHEN** a build worker exits 0 with every phase ticked and committed, and no `.done` names `HEAD`
- **THEN** the build check fails, the version halts, and no second build starts

#### Scenario: A build closed before this rule
- **WHEN** a version's phases are all ticked, its converge has begun, and no `.minions/build/<change-id>.done` exists
- **THEN** the stage is read from converge's status log, as before
