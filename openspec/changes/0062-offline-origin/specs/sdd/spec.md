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
branch, and it is a release merge whose tag stands; otherwise it SHALL refuse, naming the check. The conductor's remote calls SHALL
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
- **THEN** `conduct.py anchor` writes it as the offline base and prints its sha and subject
- **AND WHEN** a run is live, an offline base stands, or the ref is not an ancestor of the local default branch, or not a tagged
  release merge
- **THEN** it refuses, naming the check, and writes nothing
