## ADDED Requirements

### Requirement: A machine sets whether a run pushes tags

`conduct.py` SHALL read `tags` under `[push]` in `ship.toml`, found as the cap's file is, at a run's start and in `status`, by the reader that reads `in_flight`. A missing file, a missing `[push]` table, a missing key, and `true`, SHALL mean a run pushes the tags it pushes as before. `false` SHALL make a run push no tag, at its start or after a release, whatever *A re-run recovers what a dead station left* says of a merged tag `origin` lacks, and halt on none: a release's check SHALL pass with its tag on no remote, the close and the offline list SHALL name the default branch alone, and `status` SHALL print `run · tags — this machine pushes none`. A value that is neither `true` nor `false`, and a file that cannot be read, SHALL stop `conduct.py run` and `conduct.py status` with exit 2, naming the file.

#### Scenario: No setting
- **WHEN** no `ship.toml` stands, or it holds no `[push]` table or no `tags` key, or `tags` is `true`
- **THEN** a run pushes a merged tag `origin` lacks, and `status` prints no `tags` line

#### Scenario: A release on a machine that pushes no tag
- **WHEN** `tags` is `false` and a version's release merges
- **THEN** the default branch is pushed, the tag is not, the release's check passes, the run halts on nothing, and the version's worktree is removed

#### Scenario: A tag left, and no tag pushed
- **WHEN** `tags` is `false` and a run starts with a local tag on a release merge `origin` lacks
- **THEN** the run pushes the default branch, pushes no tag, and halts on none
- **AND** `status` prints `run · tags — this machine pushes none`

#### Scenario: A bad value
- **WHEN** `tags` is a string, a number, or the file cannot be parsed
- **THEN** `conduct.py run` and `conduct.py status` exit 2 naming the file, and a run starts no worker

### Requirement: A run's start makes the tag of each release origin already holds

At its start, on every machine, a run SHALL make the local tag of each release commit that `origin`'s default branch holds and that has none: a commit whose subject is `chore(release): <tag>`, `<tag>` a `vX.Y.Z`, the second parent of a first-parent merge of `origin`'s default branch whose tree is the commit's own, read in the conductor's scratch repo. The tag SHALL be annotated, its message the tag, as the release makes it. A tag that already exists SHALL be left as it is, wherever it points, and a commit `origin`'s default branch does not hold SHALL get none. A run on a machine that pushes tags SHALL then push each tag it made, by the checks it makes of any tag it pushes; `tags = false` SHALL leave them local.

#### Scenario: A clone with no tags
- **WHEN** a run starts in a clone whose `origin`'s default branch holds a release merge of `v0.1.0` and the clone has no tag
- **THEN** the clone holds an annotated `v0.1.0` on the release commit, with `v0.1.0` as its message
- **AND** with `tags` unset `origin` then lists `v0.1.0`, and with `tags = false` it does not

#### Scenario: Several tags missing
- **WHEN** `origin`'s default branch holds the release merges of `v0.1.0` and `v0.2.0` and the clone has neither tag
- **THEN** each is made, on its own release commit

#### Scenario: A tag that points elsewhere
- **WHEN** the clone's `v0.1.0` points at another commit
- **THEN** the run makes no tag and moves none

#### Scenario: A release no origin holds
- **WHEN** a local release commit says `chore(release): v0.9.0` and `origin`'s default branch does not hold it
- **THEN** the run makes no tag for it

#### Scenario: A commit that only says it is a release
- **WHEN** a commit on `origin`'s default branch says `chore(release): v0.9.0`, or is merged with another tree
- **THEN** the run makes no tag for it

### Requirement: A run's start brings origin's default branch in

At its start a run SHALL, when the primary lacks the commit `origin`'s default branch lists, fetch that branch in the conductor's scratch repo, the one the push's reads use, with the fetched objects stored in the primary's object folder and no ref or config of the primary read. It SHALL then fast-forward the local default branch to that commit only when the local branch is a strict ancestor of it, with `git merge --ff-only`, and SHALL leave the branch where it is when it is equal to it, ahead of it or diverged from it. It SHALL merge nothing. A fetch that fails SHALL be a wait, as a failed read of `origin` is; a branch left diverged SHALL halt the run at its refused push, as before. A call that is no run's start, `status` among them, SHALL fetch nothing and halt naming a person's fetch where the primary lacks the commit.

#### Scenario: The local default is behind
- **WHEN** `origin`'s default branch holds a commit the primary lacks and the local branch is its ancestor
- **THEN** the primary holds the commit, the local branch and its tree are at it, and the run's log holds a `sync` line naming the fast-forward

#### Scenario: The local default is equal or ahead
- **WHEN** the local default branch is at `origin`'s tip, or holds a release `origin` lacks
- **THEN** the local branch does not move

#### Scenario: The local default has diverged
- **WHEN** `origin`'s default branch holds a commit the local branch lacks, and the local branch holds a release merge `origin` lacks
- **THEN** no merge is made, the local branch does not move, and the run halts at its refused push

#### Scenario: Origin cannot be fetched
- **WHEN** the read of `origin` answers and the fetch fails
- **THEN** the run waits as it does for a failed read, and the local branch does not move

#### Scenario: A status makes no fetch
- **WHEN** `status` runs and `origin`'s default branch holds a commit the primary lacks
- **THEN** it halts naming a person's fetch, and the primary holds nothing new

### Requirement: The git config guard allows gc.auto

The refusal of a git config key that could name a program SHALL allow `gc.auto` in the repo's own git config, and in each linked worktree's `config.worktree`: its value is a number, and it names no program. Every other `gc.` key SHALL stay off the list.

#### Scenario: The cloud's key
- **WHEN** the repo's own git config holds `gc.auto`
- **THEN** `status` exits 0 and a run does not halt for it

#### Scenario: A sibling key
- **WHEN** the repo's own git config holds `gc.autodetach`
- **THEN** `status` exits 1 naming the key, and a run halts

### Requirement: A checker on Codex runs on Claude where Codex is not installed

Where Codex is not on `PATH`, a converge checker a plan gives to Codex, a shadow of one included, SHALL run on Claude with converge's model and effort, as on a usage limit, and a run's start SHALL NOT probe Codex for it. The first time a run reads a checker table on Codex while Codex is missing, it SHALL log one `run · codex` line saying so. A station on Codex — a build, a cut, a rescue, the converge conductor or the fixer — SHALL halt at its probe as before, naming Codex.

#### Scenario: A checker on Codex, no Codex
- **WHEN** a plan gives the conformance checker to Codex and Codex is not on `PATH`
- **THEN** the run starts, the checker runs on Claude, and one `run · codex` line says Codex is not on `PATH`

#### Scenario: A station on Codex, no Codex
- **WHEN** a plan gives a build, or the converge fixer, to Codex and Codex is not on `PATH`
- **THEN** the run halts at its start with `probe-codex — codex is not on PATH`
