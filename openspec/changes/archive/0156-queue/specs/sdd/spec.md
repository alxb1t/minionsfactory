## ADDED Requirements

### Requirement: The queue is read and written through one module

`skills/mflib/queue.py` SHALL be the one home of the queue in the home folder: the entries of `cuts/`, the records `briefs/<id>` and `supervised/<id>`, the rejoin requests under `rejoin/`, the queue lock, and the text of a cut halt, `after <name> is cut-halted`. An entry SHALL be one typed record: `bump`, `brief`, `executor`, `after` and `halt` required, `model` and `effort` required as a string or null, `halt` a string or null, `after` a list of strings, and `dependencies`, `models`, `beside` and `waits` optional, each of its type; a value of a wrong type SHALL make the entry unreadable. `waits` SHALL be a wait when it is a non-empty string, to the conductor and to the viewer alike.

A read of an entry, `briefs/<id>` or `supervised/<id>` SHALL follow no link, SHALL not block, SHALL take a regular file alone, SHALL be bounded — 262,144 bytes an entry, 65,536 a record — and SHALL decode strictly. An entry that is a link, a FIFO, a folder, over its bound, of a wrong type, a bad byte, JSON too deep, no object or short of a required key SHALL be the unreadable entry: a halt to `status` and the viewer, refused by `rejoin`, skipped by the takers, its name still a live change to a worker's reach. A record that fails its read SHALL read as none. A write of an entry or a record SHALL be staged, mode 0600, and follow no link, and a write of an entry over its bound SHALL be refused.

A rejoin request SHALL be an empty file made by its name under the `rejoin` folder's descriptor, the folder and the name followed through no link. A name in that folder that is no change id and not `all` SHALL be removed and ignored. A failed queue write in `conduct.py cut` and in `conduct.py rejoin` SHALL stop the command with exit 2, naming the file, and `cut` SHALL remove the reservation it made; in a run it SHALL stay the halt it is.

#### Scenario: A link at an entry is the unreadable entry
- **WHEN** an entry in `cuts/` is a link to a valid entry
- **THEN** `conduct.py status` shows that cut as halted on `the queue entry is unreadable`
- **AND** `conduct.py rejoin` of it exits 2 and the takers skip it

#### Scenario: A FIFO blocks no read
- **WHEN** `cuts/<id>`, `briefs/<id>` or `supervised/<id>` is a FIFO
- **THEN** the read returns at once, the entry unreadable and each record none

#### Scenario: A wrong type is unreadable
- **WHEN** an entry holds `after` as a string, or `halt` as `0`
- **THEN** the entry is unreadable

#### Scenario: An empty wait is no wait
- **WHEN** an entry's `waits` is null or an empty string
- **THEN** `status`, the viewer and the run's `unwait` read it as no wait

#### Scenario: A deep JSON is unreadable
- **WHEN** an entry holds JSON nested past the parser's depth
- **THEN** the read returns the unreadable entry and raises nothing

#### Scenario: An entry over its bound is refused
- **WHEN** an entry to write is over 262,144 bytes
- **THEN** the write refuses it and leaves the entry that stands

#### Scenario: A request through a link
- **WHEN** the `rejoin` folder is a link, or a link stands at a request's name
- **THEN** the request is written through neither, and `conduct.py rejoin` stops, exit 2, naming the file

#### Scenario: A stray name in the request folder
- **WHEN** a file named `x.tmp` stands in `rejoin/` and the run takes its requests
- **THEN** the file is removed and no version is requested for it

#### Scenario: A failed write stops cut
- **WHEN** the queue entry of `conduct.py cut` cannot be written
- **THEN** the command exits 2, naming the file, and `.minions/cuts/<id>` is removed

#### Scenario: A failed write stops rejoin
- **WHEN** `conduct.py rejoin` cannot write an entry it clears
- **THEN** the command exits 2, naming the file, and the entries it cleared before stay cleared

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
outside git and the run directory, except the claim, `origin`'s URLs, the offline base, the release ledger, a person's gate approval,
the queue's entries, its `briefs` and `supervised` records and the rejoin requests in the home folder: a re-run derives every stage again and continues. A halt SHALL need
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
