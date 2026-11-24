## ADDED Requirements

### Requirement: Converge stamps a findings file's counts

After a checker, a verify worker or a pickup check returns, and before converge reads its findings file, converge SHALL set the file's `head`, `files` and `commits` to its round's freeze's head and counts, and its `round` to the round converge counts, through `skills/mflib/findings.py` and the staged write of `skills/mflib/statefile.py` at mode `0600`. A pickup check SHALL leave `round`. Converge SHALL leave a file whose `mode` is `skipped` or `by-rule`, and a file with no frontmatter, which stays malformed. A worker's reference SHALL NOT tell it to write `head`, `round`, `files` or `commits`; `verdict`, `open_blocking`, `inconclusive`, `passes` and the cards SHALL stay the worker's. Converge SHALL compare no count of a findings file with its freeze's, and SHALL send no checker out again for its scope.

#### Scenario: A count the worker got wrong
- **WHEN** a verify round's freeze holds 4 files and the worker wrote `files: 3`
- **THEN** converge sets `files: 4` and reads the file clean

#### Scenario: A key the worker left out
- **WHEN** a worker wrote no `files` and no `commits` key
- **THEN** converge adds both from the freeze, and reads the file clean

#### Scenario: A verify round
- **WHEN** a verify worker returns after a fix
- **THEN** its file's `head` is the fix's head, its `files` and `commits` are the fix diff's, and its `round` is the round converge counts

#### Scenario: A pickup check keeps its round
- **WHEN** a pickup check returns on round 2
- **THEN** each file it judged carries the fix's `head`, `files` and `commits`, and the `round` it held before

#### Scenario: A stub and a by-rule file
- **WHEN** a role is skipped, or a catch-up round writes `mode: by-rule`
- **THEN** converge stamps neither file

### Requirement: Row V9 reads the token after exits

The cut's check, `cut_check.py`, SHALL halt in its row `V9` each sub-task whose `Verify:` holds the word `exits` outside a code span with anything but a code span of whole digits right after it, a `**HALT CHECK**` sub-task included, naming the sub-task. It SHALL read no `exits` outside a `Verify:` line.

#### Scenario: An unquoted exit
- **WHEN** a sub-task's `Verify:` reads `` `make gate` exits 5 ``
- **THEN** `cut_check.py` prints the failed row `V9` naming the sub-task, and exits 1

#### Scenario: A quoted exit
- **WHEN** a sub-task's `Verify:` reads `` `make gate` exits `5` ``
- **THEN** the row holds

#### Scenario: The word in a task's prose
- **WHEN** a sub-task's text before its `Verify:` holds the word `exits` and no code span after it
- **THEN** the row holds

### Requirement: Status prints a halting stage's reason

`conduct.py status` SHALL print `<change-id> · <stage> — <reason>` for a version whose stage is `integrating`, `released`, `human` or `converge-halted` and carries a reason, and `<change-id> · <stage>` for any other stage.

#### Scenario: A release tip tagged on another commit
- **WHEN** a version's tip is not the commit its tag names
- **THEN** `status` prints `<change-id> · released — ` and the reason that names the tag

#### Scenario: A stage that is no halt
- **WHEN** a version is at `build`
- **THEN** `status` prints `<change-id> · build` and no reason

## REMOVED Requirements

### Requirement: A verdict that misses the freeze's scope is sent out once more

**Reason:** Converge stamps a findings file's `files` and `commits` from its freeze, so no file holds a count to compare and no scope misses.
**Migration:** *Converge stamps a findings file's counts*.

## MODIFIED Requirements

### Requirement: The release assigns the version

`skills/mf-release/SKILL.md` SHALL read `bump:` from the change's `proposal.md`, halting on anything but `minor` or
`patch`, and SHALL take `<tag>` from `skills/mf-release/scripts/next_tag.py`, which SHALL print the next tag after the
highest `vX.Y.Z` tag the default branch holds merged, a local tag on no branch read as none, or `v0.1.0` when there is none. It SHALL write `version:` into the proposal it archives, before
it collects metrics. `conduct.py` SHALL read a released version's tag from the branch tip's `chore(release): <tag>`,
SHALL pass the release check only when that tag's commit is the tip and, with an `origin`, origin's tag is on that
tip, and SHALL hold no number before it.

#### Scenario: A minor after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: minor`
- **THEN** the release tags `v0.41.0` and the archived proposal holds `version: v0.41`

#### Scenario: A patch after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: patch`
- **THEN** the release tags `v0.40.1` and the archived proposal holds `version: v0.40.1`

#### Scenario: A repository with no version tag
- **WHEN** no tag has the form `vX.Y.Z`
- **THEN** `next_tag.py` prints `v0.1.0`

#### Scenario: A stray local tag
- **WHEN** the default branch holds `v0.9.0`, a local `v0.10.0` is on no branch, and the proposal says `bump: patch`
- **THEN** `next_tag.py` prints `v0.9.1`

#### Scenario: A draft page before the release
- **WHEN** the build draws its metrics page and `proposal.md` holds no `version:`
- **THEN** the page reads `unreleased`, and compares with the highest tracked release

### Requirement: Converge's conductor is a script

`skills/mf-converge/scripts/converge.py` SHALL conduct converge: its preconditions, the freeze, the dispatch of each checker, the
fixer and each verify worker, the read of each findings file's frontmatter and cards, the loop to its cap of three rounds, the
pickup, a granted round, a catch-up round with its by-rule write, the resume from the status log, the debt write and the report.
`conduct.py` SHALL load it in-process, as it loads `integrate.py`, and call it in the version's thread; `conduct.py converge
<change-id> [conformance=<model>/<effort>] [adversarial=<model>/<effort>] [fix=<model>/<effort>] [grant=yes]` SHALL run it by hand.
No converge worker that conducts SHALL start: the workers are the checkers, the fixer and the verify workers, each a fresh agent
process the run starts through its own worker and checker calls, with a prompt the script fills from the `## Prompt` section of the
role's reference. The script SHALL run the gate, `gate_check.py`, `plan_check.py` and each `Verify:` and **Still true?** command
under `conduct.py`'s sandbox runner, never bare. It SHALL stamp each findings file's `head`, `round`, `files` and `commits` after its
checker returns, as *Converge stamps a findings file's counts* says, and SHALL read a findings file's frontmatter keys `passes` and
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them or with no
frontmatter, or with a card whose id is outside `R<n>` and `S<n>`, or whose verdict is `changes-requested` with no open card, SHALL be malformed. A card is
open until its status is `verified` or `accepted`; a role whose verdict is `changes-requested` while no open card blocks SHALL
count as clean, its file's verdict written `clean` and its open cards left to the pickup and the debt. `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py`
and `skip_stub.py` SHALL read a findings file's cards and frontmatter through `skills/mflib/findings.py`, a card's title a line that
starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word, as `- **stale-claim** — ran.`,
is no card; `skills/mflib/debtfile.py` SHALL read a debt card's title, a line that starts `- **<digits>·<id> — ` with an id holding no `*`, and `debt_match.py` and `cut_context.py` SHALL read it through the module. The status log's events and their text
SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `replay` exiting 2 SHALL send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red, a security card and a debt the freeze may not read SHALL still halt.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: Changes requested with nits alone
- **WHEN** a checker's findings file says `changes-requested` and holds open cards, none of a blocking grade
- **THEN** the role counts as clean, its file reads `verdict: clean`, the pickup takes its small and drift cards, and the version converges with no halt

#### Scenario: Changes requested with no card
- **WHEN** a checker's findings file says `changes-requested` and holds no open card
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`, and the file reads `verdict: clean` after, the
  rewrite having fixed it or not

#### Scenario: A card titled outside the contract's ids
- **WHEN** a checker's findings file holds a card titled `- **S-1 — a title**`
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`

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

#### Scenario: A debt the freeze may not read
- **WHEN** `.minions/debt.md` is a link at a freeze
- **THEN** converge halts naming `debt_match.py`, and writes no empty `debt-cards.md`

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check

### Requirement: A queued cut waits while the line is at its cap

A run SHALL read `in_flight` under `[queue]` in `ship.toml`, found under `$XDG_CONFIG_HOME/minionsfactory/`, else
`~/.config/minionsfactory/`, once at its start; a missing file, a missing `[queue]` table or a missing key SHALL mean no cap, as
before. A file that cannot be read, or a value that is no whole number above 0, SHALL stop `conduct.py run` and `conduct.py cut`
with exit 2, naming the file. With a cap, the run SHALL take a queued cut, at its start and at each poll, in id order, only
while fewer versions are in flight than the cap, and SHALL count the versions of its own repository alone. A version SHALL be in
flight while its thread runs, its rescue and supervisor included, whether a halt names it or not, and every `after` id it names is
shipped, its cut included; a version whose halt is final, its thread done, a version or cut waiting on its `after`, and every
version once a halt names the run, SHALL not be. A rejoin request naming a cut, the take-back of a version by a rejoin or a
grant, and a version already cut at the run's start SHALL run whatever the cap.

A cut that waits SHALL not count as read: the run SHALL take it at the first poll after a slot frees, SHALL stay alive while it
waits and a version is in flight, and its close SHALL start no next run for a cut that only waits. A waiting cut SHALL carry its
reason, `<n> in flight, cap <N>`, in its queue entry, written under the queue lock and cleared when the run takes the cut, and
the run SHALL log one `wait` line when a cut starts to wait. `status` SHALL print the reason, the viewer SHALL show the state
`queued` with it, and `conduct.py cut` SHALL name the cap in its line.

#### Scenario: No file
- **WHEN** no `ship.toml` stands, or it holds no `in_flight` key, and cuts are queued for a run
- **THEN** the run takes every queued cut at its start, and each cut queued into the live run at the next poll

#### Scenario: A bad file
- **WHEN** `ship.toml` cannot be parsed, or `in_flight` is `0`, negative, a fraction, a string or a boolean
- **THEN** `conduct.py run` exits 2 naming the file, and starts no worker, and `conduct.py cut` exits 2 and reserves nothing

#### Scenario: A cap of 1
- **WHEN** `in_flight` is 1 and two cuts are queued
- **THEN** the run takes the lower id, logs one `wait` line for the other, and takes it only after the first's release

#### Scenario: A halted version does not hold the queue
- **WHEN** `in_flight` is 1 and the one version in flight halts, and its thread has ended on a halt that stands
- **THEN** the run takes the next queued cut at its next poll, the halted version still open

#### Scenario: A halted version keeps its slot while its thread lives
- **WHEN** `in_flight` is 1 and the one version in flight halts, and its rescue or supervisor runs in its thread
- **THEN** a queued cut waits, its entry holding `1 in flight, cap 1`

#### Scenario: A supervisor revives a version
- **WHEN** a halted version's supervisor answers and the version goes on, and a cut waited
- **THEN** the cut is still waiting, and no second version was in flight

#### Scenario: A run-wide halt
- **WHEN** a halt names the run
- **THEN** no version counts as in flight, as before

#### Scenario: A version waiting on its after does not hold the queue
- **WHEN** `in_flight` is 1 and the one version at a station names an `after` id that is not shipped
- **THEN** the run takes the next queued cut at its next poll

#### Scenario: A cut queued into a live run
- **WHEN** `in_flight` is 1, a version is in flight and a cut is queued
- **THEN** the cut waits, its queue entry holds `1 in flight, cap 1`, and the run takes it at the poll after the version leaves the line

#### Scenario: A rejoin runs past the cap
- **WHEN** `in_flight` is 1, a version is in flight and `conduct.py rejoin <id>` names a halted cut
- **THEN** the live run takes that cut at its next poll

#### Scenario: A cap above 1
- **WHEN** `in_flight` is 2 and three cuts are queued
- **THEN** the run takes the two lowest ids and holds the third until one of them leaves the line

#### Scenario: The run stays alive for a waiting cut
- **WHEN** a cut waits and the only version in flight is still building
- **THEN** the run does not end, and takes the cut once the version releases

#### Scenario: The close starts no run for a waiting cut
- **WHEN** a run ends with a queued cut that only waited for room
- **THEN** its close starts no next run, and a cut queued after its last poll still starts one

#### Scenario: A waiting cut is shown
- **WHEN** a cut waits at `1 in flight, cap 1`
- **THEN** `status` prints `<id> · cut — waits: 1 in flight, cap 1`, the viewer's queue shows `<id>` in the state `queued` with that reason, and `conduct.py cut` prints the cap in its line

