## MODIFIED Requirements

### Requirement: Converge's conductor is a script

`skills/mf-converge/scripts/converge.py` SHALL conduct converge: its preconditions, the freeze, the dispatch of each checker, the
fixer and each verify worker, the read of each findings file's frontmatter and cards, the loop to its cap of three rounds, the
pickup, a granted round, a catch-up round with its by-rule write, the resume from the status log, the debt write and the report.
`conduct.py` SHALL load it in-process, as it loads `integrate.py`, and call it in the version's thread; `conduct.py converge
<change-id> [conformance=<model>/<effort>] [adversarial=<model>/<effort>] [fix=<model>/<effort>] [grant=yes]` SHALL run it by hand.
No converge worker that conducts SHALL start: the workers are the checkers, the fixer and the verify workers, each a fresh agent
process the run starts through its own worker and checker calls, with a prompt the script fills from the `## Prompt` section of the
role's reference. The script SHALL run the gate, `gate_check.py`, `plan_check.py` and each `Verify:` and **Still true?** command
under `conduct.py`'s sandbox runner, never bare. It SHALL read a findings file's frontmatter keys `files`, `commits`, `passes` and
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them SHALL be
malformed. `converge.py`, `open_cards.py`, `debt_match.py`, `overlap.py`, `conduct.py` and `cut_context.py` SHALL read a card's
title as a line that starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word,
as `- **stale-claim** — ran.`, is no card. The status log's events and their text SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `debt_match.py` or `replay` exiting 2 SHALL leave an empty
`debt-cards.md` or send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red and a security card SHALL still halt.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: A bold-led bullet that is no card
- **WHEN** a findings file holds `- **stale-claim** — ran.` under a `## Passes` heading and `- **Spec** — none.` in its Summary, beside cards that carry their `Amend:` fields
- **THEN** the file is read with those cards alone, and no rewrite worker is started for it
- **AND** `open_cards.py` writes those cards alone

#### Scenario: A worker exits 1
- **WHEN** a checker exits 1 or leaves no findings file
- **THEN** one fresh worker is started for that role, and a second failure halts the version, naming the role

#### Scenario: A prose check
- **WHEN** a non-blocking card's **Still true?** holds no command in backticks
- **THEN** the card goes to the debt unchecked, and no command runs for it

#### Scenario: A check command writes outside the trees
- **WHEN** a card's **Still true?** command tries to write a file outside the worktrees
- **THEN** the sandbox denies it, the card goes to the debt unchecked, and nothing is written outside

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check

### Requirement: The build runs a fresh worker per phase

Under `mf-ship`, `conduct.py` SHALL spawn one build worker for the first unticked `## Progress` phase that is not a
`**HUMAN` one, its prompt naming `phase=<N>`, and, once every phase is ticked and no `.minions/changes/<change-id>/build.done`
names `HEAD`, one build worker for the close, its prompt naming `phase=close` — right after the last phase's spawn passes, too,
when converge has already run. A phase worker's check SHALL pass only when its
phase is ticked at `HEAD` and the tree is clean; any other outcome SHALL halt the version as a build check does, so a phase is
spawned again only after a rescue's or a supervisor's taken amend. The close worker's check SHALL stay the build check.
`skills/mf-build/SKILL.md` SHALL build the named phase alone under `phase=<N>`, halting when it is not the first unticked one,
SHALL run simplify, the metrics and `build.done` alone under `phase=close`, halting on an unticked phase, and SHALL build every
phase and close when given neither. After each phase's commit it SHALL print the phase's `## Progress` line as `HEAD` holds it,
quote that line in its close-out, and tick and commit a line still unticked before it ends. Each phase SHALL append what the next phase needs to
`.minions/changes/<change-id>/build-notes.md`, under a `## <N> — <Title>` line, and SHALL read that file as evidence. After a
phase worker exits 0, `conduct.py` SHALL keep at most 40 lines of what it appended, dropping the rest and logging it, and SHALL
halt the version, writing nothing, when the file is a link. A stacked dependent's amend reset SHALL remove its
`build-notes.md`.

#### Scenario: A change of three phases
- **WHEN** `mf-ship` builds a version whose `tasks.md` holds three unticked phases
- **THEN** it spawns three build workers, naming `phase=1`, `phase=2` and `phase=3` in turn, then one naming `phase=close`
- **AND** each spawn's worker log is its own under `.minions/changes/<change-id>/logs/`

#### Scenario: An amend adds a phase after converge began
- **WHEN** an amend at a converge halt adds a new unticked phase, and the run builds it
- **THEN** a worker naming that phase, then one naming `phase=close`, run before converge's amend round

#### Scenario: A phase writes long notes
- **WHEN** a phase worker appends 50 lines to `build-notes.md`
- **THEN** the file keeps the first 40 of them, and the run log names the cut

#### Scenario: A halt in phase 2
- **WHEN** the phase-2 worker halts and its rescue's amend is taken
- **THEN** the next spawn is a fresh worker naming `phase=2`, and phase 1 is not built again

#### Scenario: A phase worker that ticks nothing
- **WHEN** a phase worker exits 0 and its phase is still unticked at `HEAD`
- **THEN** the version halts on the build check, and no worker for that phase is spawned again without an amend

#### Scenario: A phase's tick is read back
- **WHEN** a build worker has committed a phase whose `## Progress` line `HEAD` still holds unticked
- **THEN** the worker ticks the box, commits it, and prints the line again before its close-out
- **AND** its close-out quotes the line it printed

#### Scenario: A stacked dependent is reset
- **WHEN** a stacked dependent's dependency changes a decision, and the dependent is reset to its cut commit
- **THEN** its `build-notes.md` is gone, and its build starts again at phase 1
