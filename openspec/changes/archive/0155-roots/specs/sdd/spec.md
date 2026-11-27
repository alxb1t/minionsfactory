## ADDED Requirements

### Requirement: A state module opens `.minions` from the primary and refuses a link there

Every folder open of the shared home's state modules SHALL take the primary checkout as its root and `.minions` as the first part it opens, so a link at `.minions`, at `.minions/runs` or at `.minions/changes` is refused, and the link's target is left as it was. This covers the folders `skills/mflib/marks.py`, `skills/mflib/modelsfile.py`, `skills/mflib/findings.py`, `skills/mflib/claim.py` and `skills/mflib/runlog.py` open, and the conductor's and converge's opens of a change's folder, of a run's log and worker logs, and of the folder a cut's reservation is made in; the conductor's reads of `grants/` and `cuts/` keep their paths. A module that holds a path below `.minions` SHALL split it at `.minions` through `skills/mflib/layout.py`; a path with no `.minions` above it is opened as it stands. The opens whose root is the primary today, and the open of the git common directory's `info` folder, stay as they are.

#### Scenario: A link at `.minions` under a mark's write
- **WHEN** `.minions` is a link and the run writes a mark of a change
- **THEN** the write fails, and the link's target is unchanged

#### Scenario: A link at `.minions` under the models file
- **WHEN** `.minions` is a link and a version's models file is read or written
- **THEN** the read or the write is refused, and the version halts as for a broken file

#### Scenario: A link at `.minions` under a stamp
- **WHEN** `.minions` is a link and the conductor stamps a checker's `model:` and `tokens:`
- **THEN** the stamp writes nothing, and the link's target is unchanged

#### Scenario: A link at `.minions` under the claim and the run log
- **WHEN** `.minions` is a link and a run takes its claim or opens its log
- **THEN** the run stops with a named `run: cannot run` line and no traceback, and nothing is made in the link's target

#### Scenario: A link at `.minions/runs`
- **WHEN** `.minions/runs` is a link and the run appends an event or a person stops the run
- **THEN** the write fails, and the link's target is unchanged

#### Scenario: A link at `.minions` under a re-stamp and a cut
- **WHEN** `.minions` is a link and the conductor re-stamps a status log or reserves a cut
- **THEN** the open is refused, and the link's target is unchanged

### Requirement: The gate's record, the cut's notes and reservation and a grant follow no link

The gate's record, `.minions/gate/<name>`, SHALL be read through no link, and a record that is a link, or holds a byte that is not UTF-8, SHALL read as no record, so the gate runs again. A cut's `cut-notes.md` and `context.md` SHALL be written and appended through the staged write of `skills/mflib/statefile.py`, which refuses a link at the file. A grant's file, `.minions/grants/<change-id>`, SHALL be written through the folder's descriptor, opened beneath the primary with no link followed. The cut's check SHALL read a reservation, `.minions/cuts/<change-id>`, through no link and take a regular file alone: a link or a folder there SHALL fail the check, naming it, and a link at `.minions` or `.minions/cuts` SHALL fail it too. `bundle.py` and `open_cards.py` SHALL write through one wrapper of the staged write, and converge SHALL name an open page through `layout.open_name`.

#### Scenario: A bad byte in the gate's record
- **WHEN** the gate's record holds a byte that is not UTF-8
- **THEN** it reads as no record and the gate runs again, and nothing raises

#### Scenario: A link at the gate's record
- **WHEN** the gate's record is a link to a file holding a valid record
- **THEN** it reads as no record and the gate runs again

#### Scenario: A link at the cut's notes
- **WHEN** `cut-notes.md` or `context.md` is a link and the cut writes it
- **THEN** the write stops naming the link, and the link's target is unchanged

#### Scenario: A link at a grant
- **WHEN** `.minions/grants/<change-id>` is a link and a person grants a round
- **THEN** the grant stops with a `grant: cannot run` line, and the link's target is unchanged; a pipe or a folder there stops it the same way

#### Scenario: A reservation that is a link
- **WHEN** `.minions/cuts/<change-id>` is a link and the cut's check runs
- **THEN** the check fails, naming the reservation, and reads nothing through the link

#### Scenario: A cuts folder that is a link
- **WHEN** `.minions/cuts` is a link and the cut's check runs
- **THEN** the check fails, and lists nothing through the link
