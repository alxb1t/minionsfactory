## ADDED Requirements

### Requirement: One module writes and parses a findings file

`skills/mflib/findings.py` SHALL be the one writer and parser of a findings file: its card, its fields, its frontmatter, the read of the file, a halt's card ids, the stub and the stamp. `converge.py`, `conduct.py` and `integrate.py` SHALL read and write a findings file through it, and `open_cards.py`, `overlap.py` and `skip_stub.py` SHALL be commands over it with their arguments, output and exits as they were. A **card** SHALL be its title line `- **<id> — <title>**` and the indented lines after it, a blank line not ending it; a **field line** SHALL be `- **<Name>:**`, `- **<Name>**:` or a bare `- **Still true?**`, the first of a repeated field read. A field's **word** SHALL be its first word with backticks and `*` dropped, a trailing `.,;:` stripped and case folded, read the same for a Status, a grade and a category; a Status word no reader knows, and an empty Status, SHALL read as not cleared. A card id outside `R<n>` and `S<n>`, and a Status or Priority line under no card, SHALL make the file malformed at its read, in every reader. The **frontmatter** SHALL be the block at the start of the file, closed by its first `---` line, a key and its whole value stripped. Every reader SHALL follow no link and replace a byte that is not UTF-8, a missing file keeping each caller's answer; a malformed file SHALL reach `conduct.py`'s security readers as a blocking security card. The conductor's stamp of a checker's `model:` and `tokens:` SHALL write through the staged write of `skills/mflib/statefile.py` at mode `0600`, renaming over the file, and SHALL NOT unlink it first.

#### Scenario: A Status read the same everywhere
- **WHEN** a blocking card's Status reads `Open` and its grade is bold
- **THEN** converge, the conductor's automatic grant and `open_cards.py` each count it open and blocking

#### Scenario: A card runs through a blank line
- **WHEN** a card's Fix field follows a blank line after its Status
- **THEN** every reader reads the Fix as the card's own, and its size is the one it names

#### Scenario: A field written either way
- **WHEN** a card holds `- **Status**: fixed` and another holds `- **Status:** fixed`
- **THEN** every reader reads `fixed` for each

#### Scenario: A security card in an unread category
- **WHEN** an adversarial card blocks and its category is none of the named non-security ones
- **THEN** converge and `conduct.py` each read it as a security card

#### Scenario: A card titled outside the contract's ids
- **WHEN** a findings file holds a card titled `- **S-1 — a title**`
- **THEN** every reader reads the file as malformed, and `conduct.py`'s security readers read it as a blocking security card

#### Scenario: A frontmatter value that crosses a line break
- **WHEN** a findings file's `verdict:` is followed by a blank value and a word on the next line
- **THEN** the conductor and integrate read the value converge reads: the whole stripped value, which is empty

#### Scenario: A linked findings file
- **WHEN** a findings file is a link
- **THEN** each reader refuses it, follows no link and writes nothing

#### Scenario: A stamp keeps the file
- **WHEN** the conductor stamps `model:` and `tokens:` into a findings file
- **THEN** the file is renamed over from `<name>.tmp` at mode `0600`, and no moment holds it deleted

#### Scenario: A file still malformed after its rewrite
- **WHEN** a role's findings file is malformed after its rewrite worker
- **THEN** converge reads the role clean at `HEAD` and files a spoiled card, and the conductor and integrate read the file's own `verdict:` and `head:`

#### Scenario: Which Status clears
- **WHEN** a findings file holds a card whose Status is `accepted`
- **THEN** converge clears it and `skip_stub.py` does not

## MODIFIED Requirements

### Requirement: The card is defined in converge alone

`skills/mf-converge/references/worker.md`, converge's worker reference, SHALL own the card: a `## The card` section whose
table rows are the card's fields, one per row, the first cell holding the field's label in bold (`**Why it's a problem**`). No
other shipped skill SHALL carry a `## The card` section. `skills/mflib/findings.py` SHALL write and parse the card as that
section defines it, and no other script SHALL carry a parser of a findings file's card.

#### Scenario: Only converge carries the card
- **WHEN** every `skills/*/SKILL.md` and converge's worker reference are scanned for a `## The card` section
- **THEN** the worker reference carries one, with at least one label
- **AND** no other skill carries one

#### Scenario: One parser reads the card
- **WHEN** converge, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py` and `skip_stub.py` read a findings file
- **THEN** each reads it through `skills/mflib/findings.py`

### Requirement: A run grants one round at a small cap, and halts a large one for a re-plan

When a version's converge halts with `cap reached` in a run, `conduct.py` SHALL read the open blocking findings in its
conformance and adversarial findings files, through `skills/mflib/findings.py` — conformance's `blocking`, adversarial's `critical` and `high`, each
`Status: open`, a Status or grade read as converge reads it — and, when every one's fix is
sized `one line`, `a test` or `one line and a test`, no granted round reached the cap — its converge run is not marked `· grant`,
and the run has not granted the version already — and its models
file's `[converge]` table does not say `auto_grant = false`, SHALL spawn converge with `grant=yes` itself, writing no grant file and
starting no rescue, log `grant — <id>: automatic · <ids>`, and check the round as it checks a person's grant's. Otherwise — a blocker sized `a design change`, no open blocking card read, a granted
round's cap, automatic or a person's, in this run or an earlier one, a second cap in the run, or `auto_grant = false` — the run SHALL write the version a last halt line, `re-plan: <ids>`, and the version's rescue SHALL
diagnose it, naming `/mf-plan` with the version's brief as the way back. A person's grant SHALL still spend a round on a re-plan
halt. `mf-converge` run by hand grants nothing on its own.

#### Scenario: A small cap
- **WHEN** a version caps with open blockers sized `one line` and `a test`
- **THEN** the run logs `grant — <id>: automatic`, converges one more round, writes no `.minions/grants/<id>`, and releases the
  version in the same run when that round is clean

#### Scenario: A design change at the cap
- **WHEN** an open blocker at the cap is sized `a design change`
- **THEN** no grant is spent, and the version halts as `re-plan`, its rescue naming `/mf-plan`

#### Scenario: The granted round blocks again
- **WHEN** the automatically granted round ends with a blocker open
- **THEN** the version halts as `re-plan`, and no second automatic grant is spent
- **AND WHEN** a later run reads that cap
- **THEN** it halts the version as `re-plan` and spawns no converge

#### Scenario: The granted round ends unfinished
- **WHEN** the automatically granted round's converge exits 0 with its status log not on `done`
- **THEN** the run logs the converge check's failure and halts the version, spawning no other converge

#### Scenario: Turned off
- **WHEN** the version's models file says `[converge] auto_grant = false`
- **THEN** its cap halts as `re-plan` with no automatic grant

#### Scenario: A blocker written in capitals
- **WHEN** a version caps with a blocking card whose Status reads `Open` and whose grade is bold, sized `a test`
- **THEN** the run reads it as an open blocker, as converge counts it, and grants the round

### Requirement: A converge conductor stubs a skipped checker

`skills/mf-converge/scripts/skip_stub.py <findings-file> <round>` SHALL write the findings file of a checker a plan skips as a
stub: the findings contract's frontmatter with `head:` the commit `git rev-parse HEAD` prints, `round:` as given, `reviewed:`
today, `open_blocking: 0`, `verdict: clean`, `mode: skipped`, `workers: 0`, `model: none`, `executor: none` and `packet:
skipped: all`, and no card. It SHALL print the line it wrote, exit 0, and exit 2 with `skip_stub: cannot stub — <why>` when the
path is a link, is not of the form `changes/<change-id>/conformance.md` or `changes/<change-id>/adversarial.md`, no repository
holds the working directory, or the path holds a checker's file that is not clean, is malformed or holds a card other than `verified`, the file read
through `skills/mflib/findings.py`, a card's Status read as converge reads it, and an unknown or empty Status not cleared. `converge.py`
SHALL start no worker for a role it is given `<role>=skip` for, and SHALL run `skip_stub.py` for that role after the freeze of
round 1, each re-freeze, a catch-up round's freeze and its by-rule write, and before its `done`, so that the stub's `head:` is
`HEAD` whenever converge ends. The script SHALL read a stub for `verdict: clean` and its `head:` alone, with no `verdicts` line. A
pickup check SHALL need the checker the plan did not skip. `conduct.py`'s readers of a findings file SHALL read through the same module: a
stub is clean at `HEAD`, holds no card, and bars no rescue or supervisor.

#### Scenario: A stub is written
- **WHEN** `skip_stub.py .minions/changes/0001-a/adversarial.md 1` runs in a repository whose `HEAD` is `abc1234…`
- **THEN** the file holds `head: abc1234…`, `verdict: clean`, `mode: skipped` and `workers: 0`, and the line it printed names the
  path

#### Scenario: A stub for a path it does not take
- **WHEN** the findings path is a link, or ends `review.md`
- **THEN** `skip_stub.py` exits 2, writes nothing, and prints `skip_stub: cannot stub — <why>`

#### Scenario: A stub over a judged file
- **WHEN** the findings path holds a checker's file that is not clean, or holds a card whose Status is not `verified`
- **THEN** `skip_stub.py` exits 2, the file is kept, and the line names what it holds

#### Scenario: A stub over a card whose Status is written in backticks
- **WHEN** the findings path holds a card whose Status reads `` `open` `` or `**open**`
- **THEN** `skip_stub.py` exits 2 and keeps the file, as it does for `open`

#### Scenario: A stub over a malformed file
- **WHEN** the findings path holds a card titled `- **S-1 — a title**`
- **THEN** `skip_stub.py` exits 2 and keeps the file

#### Scenario: A version with adversarial skipped
- **WHEN** converge runs for a version whose plan skips adversarial, and conformance finds nothing
- **THEN** `conformance.md` and the stub of `adversarial.md` are both clean at `HEAD`, `conduct.py` reads the version as
  judged, and its rescue and supervisor are barred by no security card
- **AND** the release states `adversarial: skipped`

#### Scenario: A skipped converge writes no debt and no hand read
- **WHEN** a version's plan says `converge skip`
- **THEN** no findings file, no diff patch and no debt card is written for it, and no hand read is asked for

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
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them, or with a card
whose id is outside `R<n>` and `S<n>`, SHALL be malformed. `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py`
and `skip_stub.py` SHALL read a findings file's cards and frontmatter through `skills/mflib/findings.py`, a card's title a line that
starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word, as `- **stale-claim** — ran.`,
is no card; `debt_match.py` and `cut_context.py` SHALL read a debt card's title by that rule. The status log's events and their text
SHALL stay as before.

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

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check

### Requirement: The gate holds the structure rules

`make gate` and `make check` SHALL run `tests/test_structure.py`, which holds the structure rules over every Python file under `skills/` and `scripts/`. A script SHALL name only a file of its own folder, a file of the shared home, or — the conductor alone — a station's script. No script SHALL take a name starting with `_` from a file it names. The files a script names SHALL make no cycle. `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps` SHALL be named only in the files the test lists and in the port, `skills/mflib/platform.py`. No string constant outside `skills/mflib/layout.py` SHALL equal `.minions` or start with `.minions/`, unless the test lists the file and the name. No string constant outside `skills/mflib/layout.py` SHALL contain `.mf-ship-origin` or equal `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, and the test SHALL list no such site. No string constant outside `skills/mflib/` SHALL equal `status_log.md`, contain `## Run`, or contain `- **` or `- \*\*`, the head of a card, unless the test lists the file and the name. A script that loads the shared home SHALL load it after the seed line its folder fixes: the same line in each script under `skills/`, and under `scripts/` the one that reaches `skills/` from the file's depth. Every Python file under `skills/` SHALL match a path glob of the threat model's `## Surfaces`. `docs/modules.md` SHALL hold one row for each of those files, with its layer and the files it names, and no row for a file that is gone. The rules for loads, names, cycles, OS commands, state paths and formats SHALL each carry a list of today's exceptions in the test, and a listed exception that no longer exists SHALL fail the test.

#### Scenario: A load the map does not declare
- **WHEN** a script names a file of another station that its row in `docs/modules.md` does not list
- **THEN** `tests/test_structure.py` fails naming both files, and the gate is red

#### Scenario: A station loads a station
- **WHEN** a station's script names a script of another station and the pair is on no exception list
- **THEN** the loads rule fails naming the pair

#### Scenario: A private name crosses a file
- **WHEN** a script reads `_name` from a file it names and the pair is on no exception list
- **THEN** the names rule fails naming the file and the name

#### Scenario: A cycle
- **WHEN** two scripts name each other and the cycle is on no exception list
- **THEN** the cycles rule fails naming the files of the cycle

#### Scenario: An OS command outside its files
- **WHEN** a script outside the listed files and the port names `caffeinate` or `bwrap`
- **THEN** the OS-command rule fails naming the file and the command
- **AND WHEN** the port names it
- **THEN** the rule passes

#### Scenario: A state path joined outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant equal to `.minions`, or one that starts with `.minions/`, and the file is on no exception list
- **THEN** the state-path rule fails naming the file and the name
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: The home folder's name outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant that contains `.mf-ship-origin`
- **THEN** the state-path rule fails naming the file and the name, whatever the test lists
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: An XDG variable's name outside the layout module
- **WHEN** a script outside `skills/mflib/layout.py` holds a string constant equal to `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`
- **THEN** the state-path rule fails naming the file and the name, whatever the test lists
- **AND WHEN** `skills/mflib/layout.py` holds it
- **THEN** the rule passes

#### Scenario: A format name outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant equal to `status_log.md`, or one that contains `## Run`, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** a file of `skills/mflib/` holds it
- **THEN** the rule passes

#### Scenario: A card head outside the home
- **WHEN** a script outside `skills/mflib/` holds a string constant that contains `- **` or `- \*\*`, and the file and the name are on no exception list
- **THEN** the format rule fails naming the file and the name
- **AND WHEN** `skills/mflib/findings.py` holds it
- **THEN** the rule passes

#### Scenario: A load of the home with no seed
- **WHEN** a script under `skills/` imports `mflib` and the statement before that import is not the seed line
- **THEN** the seed rule fails naming the script

#### Scenario: A load of the home from scripts with no seed
- **WHEN** a script under `scripts/` imports `mflib` and no seed line of its depth stands before the import
- **THEN** the seed rule fails naming the script

#### Scenario: A file on no surface
- **WHEN** a Python file under `skills/` matches no glob of the threat model's surfaces
- **THEN** the surfaces rule fails naming the file

#### Scenario: A file with no row
- **WHEN** a Python file under `skills/` has no row in `docs/modules.md`
- **THEN** the map rule fails naming the file
- **AND WHEN** a row names a file that is gone
- **THEN** the map rule fails naming the row

#### Scenario: A stale exception
- **WHEN** a listed exception no longer exists in the tree
- **THEN** the rule that lists it fails naming the exception, so a list only shrinks
