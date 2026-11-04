## ADDED Requirements

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
its conflicts with the `changelog` and `decisions` rules alone, and exit 0 when the rebuilt tree equals the merge's tree, else 1.
It SHALL exit 2, rebuilding nothing, for a commit without two parents or whose second parent the default branch does not hold.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL first run *Catch-up scope*'s ancestry and parent checks, halting when one
fails, then run `replay` for each merge in its selection; when every merge replays and the
selection holds nothing else, it SHALL write both findings files `head: HEAD` and `verdict: clean` with a `## By rule` section
naming each merge's paths, log `round N · by rule — clean, <paths>`, dispatch no worker, and count the round within the
merges-only count. Any other selection SHALL take the catch-up round as before.

#### Scenario: A changelog the rule settled
- **WHEN** the integrate merge conflicted in `CHANGELOG.md` alone, settled by `integrate.py changelog`
- **THEN** the catch-up replays it, writes both findings files clean with `## By rule`, dispatches no worker, and the release
  passes its preconditions

#### Scenario: A merge someone judged
- **WHEN** the merge holds a hunk the integrator resolved as a union, a person's resolution, or a test edited
- **THEN** replay exits 1, and the catch-up round dispatches review and security as before

#### Scenario: A merge of a commit the default branch does not hold
- **WHEN** the merge's second parent is not an ancestor of the default branch, though git merged it with no conflict
- **THEN** replay exits 2, and the catch-up halts, naming the merge, with no findings file written clean

### Requirement: The integrate merge commit names every path it settled

`skills/mf-integrate/SKILL.md`'s merge commit SHALL hold one body line per path it settled: `<path>: integrate.py <rule>` for a
fixed rule, the union line as before, `<path>: the person` after a note halt, and `<path>: test fixed — <what it now asserts>`
for a test the integrator edited, which SHALL never remove or loosen an assertion.

#### Scenario: A merge the rules and a person settled
- **WHEN** a merge's `CHANGELOG.md` was settled by the rule and a requirement by the person after a note halt
- **THEN** the commit body names `CHANGELOG.md: integrate.py changelog` and the requirement's path as `the person`

## MODIFIED Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge`, `mf-integrate` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root, through `skills/mf-converge/scripts/gate_run.py`, which records a green run in `.minions/gate/<tree>` — the tree, the
dry run's hash, the date and the seconds — and on a later call reuses it when the worktree is clean, its tree is that tree,
and `make -n gate` prints the same lines. A red run SHALL record nothing, and `mf-release`'s gate after its fold SHALL run
fresh. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **WHEN** `mf-build`, `mf-converge` or `mf-release` is about to run the gate for the first time in a session
- **THEN** it prints the output of `make -n gate` first
- **AND** it runs `make gate` from the repository root, never a command it found instead

#### Scenario: The repository has no runnable gate
- **WHEN** the root `Makefile` is missing, has no `gate` target, or its `gate` target prints no command under
  `make -n`
- **THEN** the station halts, naming the root `Makefile`

#### Scenario: A station reuses a green gate on the same tree
- **WHEN** a station's gate ran green on a tree, and a later station gates the same tree, clean, with the same dry run
- **THEN** the later station reuses the record and runs no `make gate`
- **AND WHEN** the tree, the dry run or a file in the worktree differs
- **THEN** it runs `make gate`
- **AND WHEN** `mf-release` gates the tree it folded
- **THEN** it runs `make gate`, whatever stands recorded

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, with no pickup, unless the
selection is merges only and every merge replays by the fixed rules, when the round is by rule and runs no worker.
When the selection is merges only, the run SHALL count its own rounds: one judge round and at most one fix
round, then a halt, with `round:` carrying on past three. Any other selection SHALL count against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup
- **AND WHEN** the selection is merges only and every merge replays by the fixed rules
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

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3 and the selection holds a commit that is not a merge
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `backlog`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. The log SHALL NOT be a findings file: no station writes it and no
release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, its time taken from `date`
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

### Requirement: The release records the gate's time

`skills/mf-release/SKILL.md` SHALL take precondition 1's gate time from the seconds `gate_run.py`'s last line prints —
`gate: green`, the run's, or `gate: reused`, the record's — and SHALL write one `Gate:` line under the new
release heading in `CHANGELOG.md`: that time, CI's latest green run on the default branch read with `gh run list`
or `none`, and the previous release's `Gate:` line's times. Under `merge=yes` the CI part SHALL read `CI not read under
mf-ship`: the sandbox keeps `gh` from its config.

#### Scenario: The release names the line and the CI read
- **WHEN** `mf-release` renames `## [Unreleased]` to the release heading
- **THEN** it writes one `Gate:` line under it: precondition 1's gate time, CI's latest green run on the default
  branch from `gh run list` or `none`, and the previous release's `Gate:` times

#### Scenario: A release under mf-ship
- **WHEN** a release under `merge=yes` writes its `Gate:` line
- **THEN** the CI part reads `CI not read under mf-ship`, never `CI none`

#### Scenario: A release whose gate was reused
- **WHEN** precondition 1's `gate_run.py` prints `gate: reused — <tree> · <n>s · <date>`
- **THEN** the `Gate:` line's local time is that record's `<n>` seconds

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins, and SHALL record `mode: parallel` or `mode: sequential`,
or `mode: by-rule` with `workers: 0` for a by-rule catch-up, which dispatches no worker. The
station SHALL halt before work requiring an unavailable worker capability, naming that
capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

#### Scenario: A host runs one worker at a time
- **WHEN** converge runs on a host that cannot run workers in parallel
- **THEN** it runs the review worker, then the security worker, over the same frozen head, and the findings files record
  `mode: sequential`

#### Scenario: A by-rule catch-up records no worker
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** both findings files record `mode: by-rule` and `workers: 0`
