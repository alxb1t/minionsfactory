## ADDED Requirements

### Requirement: One module writes and parses the models file

`skills/mflib/modelsfile.py` SHALL be the one writer and parser of `.minions/changes/<change-id>/models.toml`: the map of its tables and keys, the text `brief_check.py --models` prints, the parser, each key's reader, the token rule, the hash and the write. `brief_check.py` and `conduct.py` SHALL go through it; `conduct.py` SHALL keep each station's executor, model and effort defaults, the comparison with the plan and its child run of `brief_check.py`. The module SHALL find the file through `skills/mflib/layout.py`. The models line's grammar SHALL stay `brief_check.py`'s, and its `cut` part SHALL write no table: the cut's model goes on `conduct.py cut`'s own arguments.

The module's one map SHALL name `[rescue]`, `[supervise]` and `auto_grant` as the person's keys, which a tool reads and never writes; a key the map does not name SHALL be ignored, `tier` among them, and `[converge.review]` and `[converge.security]` SHALL be read no more. Every `model` and `effort` of every table of the map SHALL be letters, digits, `.`, `_` and `-` alone, and a table that holds another word SHALL halt its version, naming the table and the word.

The module's read SHALL follow no link, not block, take a regular file alone, read at most `65,536` bytes and decode them strictly. A missing file SHALL be no file, and a version with none SHALL run on the defaults; a link, a dangling link, a pipe, a folder, a file over the bound, a byte that is not UTF-8 and text that is not TOML SHALL each be a broken file. A broken file SHALL halt its version alone, wherever the run plans or takes it, naming the file and why, and SHALL fail the cut's check naming it. `conduct.py status` SHALL name it after the version's line and go on, and the viewer SHALL read no skip from it. The hash the cut's check compares SHALL be taken over the bytes of that read.

The module's write SHALL go through the staged write under the change folder's descriptor and refuse a link; a failed write SHALL stop `conduct.py cut` with exit 2. `brief_check.py --models <brief> <slug> --write <change-id>` SHALL run the parse `--models` runs, then write its text through the module in the current directory's repository, and print `brief: wrote .minions/changes/<change-id>/models.toml`; its exits SHALL be `--models`', and 2 for a failed write.

#### Scenario: A bad byte in a models file
- **WHEN** a version's models file holds a byte that is not UTF-8 and another version is open
- **THEN** the run halts the first version, naming the file, and the other version goes on

#### Scenario: Text that is not TOML
- **WHEN** a version's models file holds `[converge`
- **THEN** the run halts that version at its take, and the plan reads no skip from it

#### Scenario: A link, a pipe or a folder at the file
- **WHEN** a link, a pipe or a folder stands at `.minions/changes/<id>/models.toml`
- **THEN** the version halts naming the file, no read blocks, and a cut's check fails naming it

#### Scenario: A file over the bound
- **WHEN** a version's models file is `65,537` bytes
- **THEN** the version halts naming the file, and the file is not parsed

#### Scenario: No models file
- **WHEN** a change's folder holds no `models.toml`
- **THEN** each station of the version runs on the defaults, and the cut's check fails as no models file

#### Scenario: A word that is no token
- **WHEN** a version's `[build]` table holds `model = "TMPDIR=/tmp/mf-codex-x"`
- **THEN** the version halts naming `build` and the word, and no worker starts on it

#### Scenario: An old checker table
- **WHEN** a version's models file holds `[converge.review]` and no `[converge.conformance]`
- **THEN** conformance runs on the checkers' defaults, and `[converge.review]` is read for nothing

#### Scenario: A key the map does not name
- **WHEN** a version's `[converge]` table holds `tier = "high"`
- **THEN** the key is ignored, and no table of the file is refused for it

#### Scenario: A status read of a broken file
- **WHEN** `conduct.py status` runs and a version's models file is not UTF-8
- **THEN** that version's line keeps its stage and gains ` — changes/<id>/models.toml: it is not UTF-8`, and the command exits 0

#### Scenario: A link where the write lands
- **WHEN** a link stands at `.minions/changes/<id>/models.toml` and the run writes the entry's text
- **THEN** the cut stops with exit 2 naming the file, and the link's target is unchanged

#### Scenario: A hard link at the file
- **WHEN** the file has a second name and the run writes the entry's text
- **THEN** the name holds the new text and the other name keeps its old bytes

#### Scenario: The attended cut's writer
- **WHEN** `brief_check.py --models <brief> a --write 0001-a` runs on a brief whose item `a` names its models
- **THEN** `.minions/changes/0001-a/models.toml` holds what `--models` prints, and the command prints `brief: wrote .minions/changes/0001-a/models.toml`

#### Scenario: The writer's flag beside no `--models`
- **WHEN** `brief_check.py <brief> --write 0001-a` runs
- **THEN** it exits 2 and writes nothing

## MODIFIED Requirements

### Requirement: A run moves the old findings files to the checkers' names

At its start, under its claim, before any worker, `conduct.py run` SHALL move each `.minions/changes/<change-id>/review.md` to
`conformance.md` and each `security.md` to `adversarial.md`, and an old layout's `.minions/findings/<change-id>_review.md`  and
`_security.md` straight to the new names, by the old-layout move's rules: a link at an old file or its folder, an old file
beside its new one, or two old files naming one new path SHALL halt with nothing moved, and a second start SHALL move nothing.
`gate_check.py`, `integrate.py`, `run.py`, `conduct.py grant`, and a hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`,
finding a change's `review.md` or `security.md` in its folder, SHALL halt naming `/mf-ship`; `conduct.py status` and `report`
SHALL name such a change `old layout`. A models file's `[converge.review]` and `[converge.security]` SHALL be read no more:
the one map of the file's tables holds neither.

#### Scenario: A run moves the old names
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `security.md`
- **THEN** they move to `conformance.md` and `adversarial.md`, the version's stage reads as before, and a second start moves
  nothing

#### Scenario: Both names stand
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `conformance.md`
- **THEN** the run halts, naming both, and moves nothing

#### Scenario: A hand-run converge on the old names
- **WHEN** `mf-converge` runs by hand for a change whose folder holds `review.md`
- **THEN** it halts, naming the file and `/mf-ship`, and writes no status log

#### Scenario: A metrics read on the old names
- **WHEN** `scripts/metrics/run.py` reads a change whose folder holds `review.md` or `security.md`
- **THEN** it halts, naming the file and `/mf-ship`, as every station does

#### Scenario: An old worker table
- **WHEN** a version's models file holds `[converge.review]` and no `[converge.conformance]`
- **THEN** conformance's worker runs on the checkers' defaults
