## MODIFIED Requirements

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue and, under its switch, its
supervisor, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker, save one
stacked on it before the halt, which builds on and then blocks. A failed
probe, save one a usage limit stopped, and a conductor crash SHALL stop the run. A run with every open version at a halt stage
or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the default branch's name, the offline base, the release ledger, a person's gate approval,
the live mark, the list of repos a run started in, the probe's mark, the pin's four files `source`, `pending`, `hold` and `checkout`, the queue's entries, its `briefs` and `supervised` records and the rejoin requests in the home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/debt.lock`, or an older `.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, an old
`.minions/backlog.md` beside `.minions/debt.md` or a file at `.minions/backlog.lock` or `.minions/debt.lock`, or one that is a
link, or a default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset
time named, save a mailbox checker, which falls back.

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

#### Scenario: A dependency halts after its dependent stacked
- **WHEN** a dependent stacked on its dependency's built head, and the dependency then halts in converge
- **THEN** the dependent's build runs to its end, and the dependent then logs `blocked — by <id>`

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
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/changes/<change-id>/`,
  and the run takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/changes/<change-id>/integrate.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: The kept files are read and written through one module

`skills/mflib/kept.py` SHALL be the one home of the conductor's kept files in the home folder: the kept origin `<digest>`, `<digest>.default`, the offline base `<digest>.pushed`, the release ledger `<digest>.released/<change>`, a person's gate approval `<digest>.gate/<change>`, the live mark `live/<digest>`, `repos`, the probe mark `probe-<executor>-<pid>` and the pin's four files `source`, `pending`, `hold` and `checkout`, with each one's write, read, listing and removal, and of the operator's `ship.toml` the read. `conduct.py`, `gate_check.py` and `pin.py` SHALL go through it. `cloud_setup.py`'s write of `ship.toml` is not its.

A read of a kept file SHALL follow no link, SHALL not block, SHALL take a regular file alone, SHALL be bounded — 65,536 bytes, and for `repos` 262,144 — and SHALL decode strictly; the read of `ship.toml` and of a pin file is so too. A kept origin, `.default` or offline base that cannot be read SHALL stop the command, exit 2, naming the file: a name that is a link, a FIFO, a folder, over its bound, a bad byte, a kept origin that is not two lists of URLs, or a base that is not empty and not a commit id of 40 hex digits. A pin file and `ship.toml` that cannot be read SHALL stop the command as *The pin's files are read and written through kept.py* and *A ship.toml that cannot be read stops the command* say. A gate approval that cannot be read SHALL approve nothing. A ledger entry that is not one commit id, its whole text stripped being 40 lower-case hex digits, SHALL be no release head, SHALL be named in the run log or, for a command, on stderr, and SHALL stay. A live mark that cannot be read SHALL read as none, and a `repos` that cannot be read SHALL read as none and take no append.

A write of the offline base, a ledger entry, an approval, the live mark and a pin file SHALL be staged, mode 0600, and a failed write SHALL leave no staged file. The kept origin and `.default` SHALL be written once: a name that stands, of any kind, stays, and the next read of a link or a folder there stops the command as above. The probe mark SHALL be made empty, after a mark of its name is removed. `repos` SHALL be appended to through no link, to a regular file. A folder of the kept files SHALL be made at 0700, and one that stands SHALL keep its mode. A removal SHALL be by name under the folder's descriptor. `.default` SHALL be written with a newline and read stripped.

#### Scenario: A bad byte in `.default` stops the run
- **WHEN** `<digest>.default` holds a byte no text is made of and `conduct.py run` starts
- **THEN** the run's halt line names the file, `conduct.py run` exits 2, and no traceback prints

#### Scenario: A link at the kept origin is not kept
- **WHEN** a dangling link stands at `<digest>.default` and a run keeps the origin's URLs
- **THEN** the keep writes nothing over it
- **AND** the read that follows stops the command, exit 2, naming the file

#### Scenario: A kept file that stands stays
- **WHEN** a second run keeps the origin's URLs
- **THEN** the kept origin is as the first run wrote it

#### Scenario: A FIFO blocks no read
- **WHEN** the offline base is a FIFO
- **THEN** the read returns at once and the command stops, exit 2, naming the file

#### Scenario: An approval that cannot be read approves nothing
- **WHEN** an approval holds a bad byte
- **THEN** `gate_check.py` finds no approval and raises nothing

#### Scenario: An entry that is no commit id is no head
- **WHEN** a ledger entry holds `abc` or two lines
- **THEN** it authorizes no push, a run logs its name, and the entry stays

#### Scenario: A second approval replaces the first
- **WHEN** `conduct.py approve-gate` runs twice for one change with two hashes
- **THEN** the entry holds the second hash, mode 0600

#### Scenario: A live mark that cannot be read reads as none
- **WHEN** a live mark holds a bad byte or is a FIFO
- **THEN** a run takes it over and an install treats it as no live run

#### Scenario: A `repos` that cannot be read takes no append
- **WHEN** `repos` is over 262,144 bytes
- **THEN** a run appends no line and raises nothing

#### Scenario: `.default` ends in a newline
- **WHEN** a run keeps the default branch `main`
- **THEN** `<digest>.default` holds `main` and a newline, and a push to `main` halts nothing

#### Scenario: A pin file is written staged
- **WHEN** `make install-skills` writes `source` twice
- **THEN** `source` holds the second text and one newline, its mode is 0600, and no `source.tmp` stands

## ADDED Requirements

### Requirement: The pin's files are read and written through kept.py

`describe`, `move` and `install` of `pin.py` SHALL read, write and remove the pin's four files — `source`, `pending`, `hold` and `checkout`, each a text and one newline, read stripped — through `skills/mflib/kept.py` alone. A pin file that is absent SHALL read as none. An empty `source` SHALL read as none, and an empty `pending`, `hold` or `checkout` SHALL mean no pending release, no hold and no checkout.

A pin file that cannot be read — a link, a FIFO, a folder or any other name that is no regular file, a file over 65,536 bytes, or a bad byte — SHALL stop `describe`, so a run at its start halts, exit 2, its halt line naming `~/.mf-ship-origin/<name>`, with no traceback. At `move`, which runs at a run's close, it SHALL be named as `pin: cannot move — <text>`, SHALL move no link, and SHALL leave the run's exit as it was; it SHALL never read as no pin. `install` SHALL read no pin file. It SHALL write each one staged, mode 0600, in a folder made at 0700, replacing a link at the name and leaving the link's target as it was, and SHALL remove `pending` and `hold` by name under the folder's descriptor. A folder at a name it writes, or a home folder it cannot make, SHALL end `install` as `pin: cannot install — <error>`, exit 2. A live mark that cannot be read SHALL still read as none.

#### Scenario: A bad byte in hold stops the run
- **WHEN** `hold` holds a byte no text is made of and `conduct.py run` starts
- **THEN** the run's halt line names `~/.mf-ship-origin/hold`, `conduct.py run` exits 2, and no traceback prints

#### Scenario: A bad byte in source at a run's close
- **WHEN** `source` holds a byte no text is made of and the last live run ends
- **THEN** `pin: cannot move — ` names `~/.mf-ship-origin/source`, no link moves, and the run's exit is what it was

#### Scenario: A link at a pin file
- **WHEN** a link to a file stands at `pending` and `make install-skills` links a release
- **THEN** `pending` is gone, and the link's target holds its old text

#### Scenario: A folder where install writes
- **WHEN** a folder stands at `source` and `make install-skills` runs
- **THEN** it prints `pin: cannot install — ` naming `source`, and exits 2

#### Scenario: An empty source is no source
- **WHEN** `source` is a file of no bytes, or of white space alone, and the last live run ends
- **THEN** no link moves, and nothing is printed

### Requirement: A ship.toml that cannot be read stops the command

The read of the operator's `ship.toml` SHALL be `skills/mflib/kept.py`'s, as *The kept files are read and written through one module* says: through no link, without blocking, of a regular file, at most 65,536 bytes, decoded strictly. A link, dangling or not, a FIFO, a folder, any other name that is no regular file, a file over its bound, a bad byte, a TOML error and a file nested deeper than the parser's limit SHALL stop the command that reads it — `conduct.py run`, `cut`, `status` or `report` — with exit 2, printing `<path>: <reason>` and no traceback. A file that is absent or empty SHALL be no cap, with tags pushed. Each read SHALL read the file again.

#### Scenario: A link at ship.toml
- **WHEN** `ship.toml` is a link to a valid file and `conduct.py run` starts
- **THEN** it exits 2 naming the file, and starts no worker

#### Scenario: A FIFO at ship.toml
- **WHEN** `ship.toml` is a FIFO with no writer and `conduct.py status` runs
- **THEN** it exits 2 naming the file, and does not wait

#### Scenario: A nested file
- **WHEN** `ship.toml` holds arrays nested past the parser's limit and `conduct.py report` runs
- **THEN** it exits 2 naming the file, and prints no traceback

#### Scenario: No file
- **WHEN** no `ship.toml` stands
- **THEN** a run has no cap and pushes tags
