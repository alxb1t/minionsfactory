## ADDED Requirements

### Requirement: The build runs a fresh worker per phase

Under `mf-ship`, `conduct.py` SHALL spawn one build worker for the first unticked `## Progress` phase that is not a
`**HUMAN` one, its prompt naming `phase=<N>`, and, once every phase is ticked and no `.minions/changes/<change-id>/build.done`
names `HEAD`, one build worker for the close, its prompt naming `phase=close` — right after the last phase's spawn passes, too,
when converge has already run. A phase worker's check SHALL pass only when its
phase is ticked at `HEAD` and the tree is clean; any other outcome SHALL halt the version as a build check does, so a phase is
spawned again only after a rescue's or a supervisor's taken amend. The close worker's check SHALL stay the build check.
`skills/mf-build/SKILL.md` SHALL build the named phase alone under `phase=<N>`, halting when it is not the first unticked one,
SHALL run simplify, the metrics and `build.done` alone under `phase=close`, halting on an unticked phase, and SHALL build every
phase and close when given neither. Each phase SHALL append what the next phase needs to
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

#### Scenario: A stacked dependent is reset
- **WHEN** a stacked dependent's dependency changes a decision, and the dependent is reset to its cut commit
- **THEN** its `build-notes.md` is gone, and its build starts again at phase 1

### Requirement: A moderate phase builds on its own model

`skills/mf-cut-change/SKILL.md` SHALL end each `## Progress` line but a `**HUMAN` one with ` · moderate` or ` · hard`: `hard`
when the phase matches the strongest-tier row of its *Suggesting models* table, `moderate` otherwise. `conduct.py` SHALL run a
phase whose line ends ` · moderate` on the models file's `[build.moderate]` model and effort, on `[build]`'s executor, when
that table names a model or an effort; every other phase, a phase with no rating among them, and the close SHALL run on
`[build]`'s. A `[build.moderate]` naming an `executor`, a model or effort outside `[A-Za-z0-9._-]`, or a `claude-*` model on a
Codex build SHALL halt the version before its worker starts. The run SHALL read `[build.moderate]` once with its plan.

#### Scenario: A moderate and a hard phase
- **WHEN** a version's models file holds `[build]` with `claude-opus-5-5` and `[build.moderate]` with `claude-sonnet-5-5` at
  `high`, phase 1 ends ` · moderate` and phase 2 ` · hard`
- **THEN** phase 1's worker runs on `claude-sonnet-5-5` at `high`, phase 2's and the close's on `claude-opus-5-5`

#### Scenario: No moderate table
- **WHEN** the models file holds no `[build.moderate]`
- **THEN** every build worker runs on `[build]`'s model

#### Scenario: A moderate table names a host
- **WHEN** `[build.moderate]` names `executor = "codex"`
- **THEN** the version halts naming the table, and no worker starts for it

## MODIFIED Requirements

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
When the highest row of *Suggesting models* any phase of a change matches is the moderate row — fresh prose, moderate
logic — the cut SHALL suggest Sonnet 5.5 · high for the whole build where the session offers it, and the strongest tier · medium where it
does not; it SHALL suggest one build model a change. A `build-moderate` part the brief's models line names SHALL be written
as `[build.moderate]`, for the phases the cut rates `moderate`.
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
- **AND WHEN** the item's models line also names `build-moderate claude-sonnet-5-5 high`
- **THEN** the file's `[build.moderate]` holds `model = "claude-sonnet-5-5"` and `effort = "high"`

#### Scenario: A moderate build
- **WHEN** the highest row of *Suggesting models* any phase matches is the moderate row, and the session offers Sonnet 5.5
- **THEN** the cut suggests Sonnet 5.5 · high for the build
- **AND WHEN** one phase matches the row above it
- **THEN** the cut suggests the strongest tier · high for the whole build

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one.
Lines split at a newline alone. It SHALL also exit 1 when a line of `## For the cut` is none of: a blank line; a head, opening
`<n>. ` and one space at the line's start; under a head, a `- models: ` or `- **Acceptance:** ` line indented three spaces or
as far as its head's text; a line indented at least two spaces past its Acceptance line, after that line or its
continuation; or the cut's `Cut <YYYY-MM-DD> as <id> at <sha>.` line. It SHALL also exit 1 when a head names a slug, an
`after` entry or a `beside` entry that `conduct.py`'s `SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or
more than one, or more than one `beside:`, or when an item has no `models:` line, more
than one, or one not naming the build, converge, release and cut station in order, then any of the build-moderate,
conformance, adversarial and fix parts in that order, each with a model and effort of `[A-Za-z0-9._-]` alone, then at most a
last `shadow`. A head MAY
omit `beside:`. A build,
converge, release, conformance or adversarial model MAY open with a host, `claude/` or `codex/`; a host it does not know, or a
host on the cut, fix or build-moderate model, SHALL exit 1, naming it. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or
`## For the cut` holds a character for which `str.isprintable()` is false, printing `brief: halt — <section> line <n>: a
character isprintable() refuses`; when a line of the brief that is not `## Decisions`, `## Dependencies` or `## For the cut` as
written reads as one of them once its `<h1>`…`<h6>` tags and every character but a letter or a digit are dropped and case is folded,
a letter or digit outside ASCII standing for any one, and at least one ASCII letter left, or a second line is
one of them as written; when the brief has no `## Dependencies`; and when that section is neither `None.` nor a table of item,
package, constraint and why whose every row names a `## For the cut` item's slug, a package and a constraint.
It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot
be parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`, or an
  item's slug or cut effort holds `$(…)` or `;`
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** a `## For the cut` line opens `- ` where `<n>. ` is due, a `| ` line sits under a head, an unindented line
  follows a head, or a head holds a second `after:`, or an item has a second models line
- **THEN** `brief_check.py` exits 1, naming the line or the item
- **AND WHEN** a head holds a second `beside:`, or a `beside` entry holding `;`
- **THEN** `brief_check.py` exits 1, naming the item

#### Scenario: A models or Acceptance line with no head
- **WHEN** a brief's `## For the cut` holds a `- models: ` or `- **Acceptance:** ` line three spaces in before any head
- **THEN** `brief_check.py` exits 1, naming the line as outside the item grammar

#### Scenario: A models line naming hosts
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · conformance codex/gpt-6.1-sol high · adversarial codex/gpt-6.1-sol
  high · fix claude-opus-5-5 high · shadow`
- **THEN** that line halts nothing
- **AND WHEN** a part names `gemini/x`, or the fix or cut model opens with a host
- **THEN** `brief_check.py` exits 1, naming the item and the word

#### Scenario: A models line naming a moderate build
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · build-moderate claude-sonnet-5-5 high`
- **THEN** that line halts nothing
- **AND WHEN** the `build-moderate` part comes after `conformance`, or its model opens with `claude/`
- **THEN** `brief_check.py` exits 1, naming the item

#### Scenario: A checked line holds other whitespace
- **WHEN** a line of a brief's `## For the cut`, `## Dependencies` or `## Decisions` holds a no-break space, an ideographic
  space, a tab, a vertical tab, a form feed, U+200B or U+2060
- **THEN** `brief_check.py` exits 1, printing `brief: halt — <section> line <n>: a character isprintable() refuses` for that line

#### Scenario: A For the cut heading in another form
- **WHEN** a brief holds ` ## For the cut`, `##<tab>For the cut`, `## For the cut ##`, `## For the cut` followed by U+200B,
  `For the cut` underlined `---`, `<h2>For the cut</h2>`, or `## For the cut` with a Cyrillic `о` for its `o`, besides its
  `## For the cut`, or that heading twice
- **THEN** `brief_check.py` exits 1, naming each such line

#### Scenario: A brief's packages
- **WHEN** a hard brief has no `## Dependencies`, or one that is prose, or a row naming no `## For the cut` item
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** it reads `None.`, or each row names an item, a package and a constraint
- **THEN** that section halts nothing

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, its `## Dependencies`, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`
- **AND WHEN** a head also carries `· beside: 0097-cross-model`
- **THEN** that head halts nothing
