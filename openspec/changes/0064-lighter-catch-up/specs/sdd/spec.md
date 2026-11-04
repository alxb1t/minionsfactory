## ADDED Requirements

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
its conflicts with the `changelog` and `decisions` rules alone, and exit 0 when the rebuilt tree equals the merge's tree, else 1.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL run it for each merge in its selection; when every merge replays and the
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
