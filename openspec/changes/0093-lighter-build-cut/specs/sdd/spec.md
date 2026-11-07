## MODIFIED Requirements

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
When the highest row of *Suggesting models* any phase of a change matches is the moderate row — fresh prose, moderate
logic — the cut SHALL suggest Sonnet 5.5 · high for the whole build where the session offers it, and the strongest tier · medium where it
does not; it SHALL suggest one model a change, never one per phase.
It SHALL write the suggestion to `.minions/changes/<change-id>/models.toml`, a table per station, as well as show it, and
SHALL never write it into the change. When the brief's `## For the cut` item names models for the change, the cut SHALL write
those instead, as the person's choice made at the plan's close. Authentication and provider configuration SHALL remain the
operator's responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

#### Scenario: The cut records its suggestion
- **WHEN** the cut commits a change
- **THEN** `.minions/changes/<change-id>/models.toml` holds a `build`, a `converge` and a `release` table, each with its
  `model`, and no file under `openspec/changes/<change-id>/` holds the suggestion for its own stations

#### Scenario: The brief names the models
- **WHEN** the brief's `## For the cut` item for the change names a model and effort per station
- **THEN** `.minions/changes/<change-id>/models.toml` holds exactly those

#### Scenario: A moderate build
- **WHEN** the highest row of *Suggesting models* any phase matches is the moderate row, and the session offers Sonnet 5.5
- **THEN** the cut suggests Sonnet 5.5 · high for the build
- **AND WHEN** one phase matches the row above it
- **THEN** the cut suggests the strongest tier · high for the whole build

### Requirement: A fresh worker reviews the plan before the cut commits

After its self-check, `skills/mf-cut-change/SKILL.md` SHALL hand the change directory and `HEAD` to a fresh read-only worker,
asked whether each task can be built as written, each `Verify:` pass after it, and each the search script did not run fail before
it, save a `**HALT CHECK**`, which should hold. The cut SHALL fix a
simple doubt itself — a check that cannot pass or breaks `I19`, a reader a deletion missed, a task two readings would build
differently — re-running the search script; a doubt that changes a settled decision, or one still standing after a second
review, SHALL go to the person. A second review SHALL run only when a fix after the first — the cut's, the person's or the
switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `decided by the cutter` row included, or adds or
removes a task; a simple fix SHALL NOT be reviewed again. Every plan review SHALL be a new worker given the change directory,
`HEAD` and the question; a message to an earlier reviewer SHALL NOT be a review. An unattended cut SHALL instead take such a doubt's recommended option when the brief says
`decide: recommended`, adding a `decided by the cutter` row to the brief, and else SHALL halt in `cut.halt`, committing
nothing. Before writing, the cut SHALL re-check each fact of the brief whose cited path changed in `<sha>..HEAD`,
`<sha>` the brief's `At` line, and each fact citing no path, letting a fact on an unmoved path stand, and re-check every fact of a
brief with no `At` line, or one whose `<sha>` `git rev-parse --verify` does not resolve to a commit; where the host starts fresh workers, up to four read-only helpers SHALL do that reading in parallel, one per
area of moved facts and one per design question, a helper not back in five minutes having its facts read by the cut. Before
writing, the cut SHALL also `git grep` every symbol, key or file the change deletes or renames and name each reader in a task, and
SHALL read the target's `CODING_STANDARDS.md` and `CONTRIBUTING.md`, planning to a target's own test rule over `T1`–`T6`.

#### Scenario: A deletion with a reader
- **WHEN** a change deletes a symbol a test still reads
- **THEN** the cut names that test in a task before it commits

#### Scenario: A design premise the code rules out
- **WHEN** the review finds a task the code cannot satisfy as the decision states it
- **THEN** the cut shows the doubt to the person with its `path:line`, and waits
- **AND WHEN** the cut is unattended and the brief does not say `decide: recommended`
- **THEN** it writes the doubt and its `path:line` to `cut.halt`, and commits nothing

#### Scenario: A brief at the cut's own commit
- **WHEN** the brief's `At` line names `HEAD`
- **THEN** the cut re-checks only the facts citing no path, and the deleted names

#### Scenario: A fact whose file moved
- **WHEN** a brief's fact cites a path that changed since its `At` line
- **THEN** the cut, or its helper, re-checks that fact at `HEAD` before writing

#### Scenario: A simple fix
- **WHEN** the first review's only doubts are a check that cannot pass and a task two readings would build differently,
  and the cut's fixes change no decision and add or remove no task
- **THEN** the cut re-runs the search script and goes on to Step 9 with no second review

#### Scenario: A fix that adds a task
- **WHEN** the cut's fix after the first review adds a task, or changes a `design.md` decision
- **THEN** a second review runs, by a new worker given the change directory, `HEAD` and the question
- **AND** no message goes to the first reviewer

### Requirement: An unattended cut decides by the brief's switch

`skills/mf-cut-change/SKILL.md` SHALL take `unattended=yes`, set by the cut station alone. Unattended, the cut SHALL hold no
awake hold, start in the worktree the conductor made with its own reservation standing, and never wait for the person. Where
the brief's `## For the cut` item for the change says `decide: recommended`, a moved fact that fails and a plan-review doubt
that changes a settled decision or survives the second review SHALL take the recommended option, and the cut SHALL add a row
`| C<n> | decided by the cutter: … | <reason> |` to the brief's `## Decisions`; a row added after the first plan review SHALL
call a second review, by a new worker. A `## Dependencies` row the brief's
`## Dependencies` does not list for the change, package and constraint as written, a
self-check item the cut cannot meet, a doubt with no clear recommendation and a `debt:` id not found SHALL always halt, and
without the switch every doubt SHALL halt; a row the brief lists SHALL be committed without a halt. A halt SHALL write one line
to `.minions/changes/<id>/cut.halt` and commit nothing.
After its commit, the cut SHALL write `.minions/changes/<id>/models.toml` from the brief's models, with
`decide = "recommended"` when the brief says so, and add `Cut <YYYY-MM-DD> as <id> at <sha>.` after the brief's `## For the cut`
list; it SHALL write nothing else outside the change and the run directory.

#### Scenario: A doubt with a recommendation under the switch
- **WHEN** an unattended cut's plan review raises a doubt that changes a settled decision, with a clear recommendation, and
  the brief says `decide: recommended`
- **THEN** the cut takes it, adds a `decided by the cutter` row to the brief, runs a second review by a new worker, and
  commits once no doubt stands

#### Scenario: A dependency
- **WHEN** an unattended cut's `## Dependencies` holds a row its brief's `## Dependencies` does not list for the change
- **THEN** it writes `cut.halt` and commits nothing, whatever the switch
- **AND WHEN** every row is one the brief lists, as written
- **THEN** it commits
