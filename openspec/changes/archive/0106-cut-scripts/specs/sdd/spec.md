## MODIFIED Requirements

### Requirement: A fresh worker reviews the plan before the cut commits

After its self-check, `skills/mf-cut-change/SKILL.md` SHALL hand a fresh read-only worker the **review packet**: the change
directory, `HEAD`, the cut's notes file, the output of `cut_check.py` and one question — whether each task can be built as
written, each `Verify:` pass after it, and each the search script did not run fail before it, save a `**HALT CHECK**`, which
should hold. The reviewer SHALL take each row `cut_check.py` printed as met as settled and judge the rows it printed to judge.
Every plan reviewer SHALL run on Opus 5.5 at `high` effort where the host offers it, whatever model the cut runs on. The reviewer
SHALL start from the packet, opening another file only at a `path:line` the change or the notes cite. Its prompt SHALL give
it a budget of 40 turns; a review that reaches it SHALL return its doubts so far under a first line `budget reached`, and the
cut SHALL take each of them as a doubt still standing after the second review. The cut SHALL fix a
simple doubt itself — a check that cannot pass or breaks `I19`, a reader a deletion missed, a task two readings would build
differently — re-running the search script; a doubt that changes a settled decision, or one still standing after a second
review, SHALL go to the person. A second review SHALL run only when a fix after the first — the cut's, the person's or the
switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `decided by the cutter` row included, or adds or
removes a task; a simple fix SHALL NOT be reviewed again. Before the first review, the cut SHALL stage the change directory
and record its tree; a second review SHALL be given the packet and the change directory's diff since that tree, and SHALL
judge that diff, and each task that cites a decision or a path the diff changes. Every plan review SHALL be a new worker given its packet; a message to an
earlier reviewer SHALL NOT be a review. An unattended cut SHALL instead take such a doubt's recommended option when the brief says
`decide: recommended`, adding a `decided by the cutter` row to the brief, and else SHALL halt in `cut.halt`, committing
nothing. Before writing, the cut SHALL place each fact of the brief with `facts.py`, which reads a fact on an unmoved path as
standing and a fact whose lines moved as moved to its new range, and leaves each other fact unplaced; the cut SHALL re-read
no fact the script placed. Where the host starts fresh workers, up to four read-only helpers SHALL read the unplaced
facts in parallel, each on Sonnet 5.5 at `medium` effort where the host offers it, a helper not back in five minutes having
its facts read by the cut; with no unplaced fact no helper SHALL start. No helper SHALL write a file: the cut SHALL write each
answer, and each fact it reads for the design, to `.minions/changes/<change-id>/cut-notes.md`, and SHALL read that file in
place of a file already read. Before writing, the cut SHALL also name each symbol, key or file the change deletes or renames
to `facts.py readers`, which `git grep`s it at `HEAD`, and name each reader in a task, and SHALL read the target's
`CODING_STANDARDS.md` and `CONTRIBUTING.md`, planning to a target's own test rule over `T1`–`T6`.

#### Scenario: A deletion with a reader
- **WHEN** a change deletes a symbol a test still reads
- **THEN** the cut names that test in a task before it commits

#### Scenario: A design premise the code rules out
- **WHEN** the review finds a task the code cannot satisfy as the decision states it
- **THEN** the cut shows the doubt to the person with its `path:line`, and waits
- **AND WHEN** the cut is unattended and the brief does not say `decide: recommended`
- **THEN** it writes the doubt and its `path:line` to `cut.halt`, and commits nothing

#### Scenario: A brief at the cut's own commit
- **WHEN** every fact's file is untouched since its sha
- **THEN** `facts.py` places each as standing, and no helper starts

#### Scenario: A fact whose file moved
- **WHEN** a brief's fact cites lines of a file that changed since its sha, and every cited line's text is unchanged
- **THEN** `facts.py` places it as moved to the new range, and the cut writes that to `cut-notes.md`

#### Scenario: An unplaced fact
- **WHEN** a brief's fact cites a changed line, a deleted file, or a sha that names no commit
- **THEN** `facts.py` leaves it unplaced, and a helper, or the cut, reads that fact at `HEAD`

#### Scenario: The helpers' answers
- **WHEN** a helper answers a fact `moved to skills/x/SKILL.md:40`
- **THEN** the cut writes that answer to `cut-notes.md`, and the helper writes no file
- **AND** the review packet names `cut-notes.md`

#### Scenario: A simple fix
- **WHEN** the first review's only doubts are a check that cannot pass and a task two readings would build differently,
  and the cut's fixes change no decision and add or remove no task
- **THEN** the cut re-runs the search script and goes on to Step 9 with no second review

#### Scenario: A fix that adds a task
- **WHEN** the cut's fix after the first review adds a task, or changes a `design.md` decision
- **THEN** a second review runs, by a new worker given the packet and the change directory's diff since the first review
- **AND** no message goes to the first reviewer

#### Scenario: A review reaches its budget
- **WHEN** a plan review reaches its 40th turn with one doubt found
- **THEN** it returns that doubt under a first line `budget reached`
- **AND** the cut takes the doubt as one still standing after the second review: the person's, or under the switch the
  recommended option

#### Scenario: A cut on another model
- **WHEN** the cut runs on Sonnet 5.5 and the host offers Opus 5.5
- **THEN** each plan review runs on Opus 5.5 at `high` effort

#### Scenario: A packet with a mechanical row
- **WHEN** `cut_check.py` prints a row as met
- **THEN** the reviewer's packet holds that output, and the reviewer re-checks no such row

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
The cut SHALL write no models file: `conduct.py cut` wrote `.minions/changes/<id>/models.toml` from the brief's models, with
`decide = "recommended"` when the brief says so, when it queued the cut. After its commit, the cut SHALL add
`Cut <YYYY-MM-DD> as <id> at <sha>.` after the brief's `## For the cut` list; it SHALL write nothing else outside the change
and the run directory.

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

#### Scenario: The models file stands before the cutter starts
- **WHEN** an unattended cut starts
- **THEN** `.minions/changes/<id>/models.toml` already holds the brief's models, and the cut writes no other

### Requirement: The cut checks the brief's `At` value before any command takes it

`facts.py` SHALL leave a fact unplaced when its sha is not 7 to 40 lowercase hex digits, running no command with it. Else it
SHALL run `git rev-parse --verify --quiet '<sha>^{commit}'`, leave the fact unplaced when it prints nothing, and diff from the
full sha that it prints.

#### Scenario: A value that is not a sha
- **WHEN** a fact's sha reads `--output=x`
- **THEN** `facts.py` runs no git command with the value, and leaves the fact unplaced

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one.
It SHALL read the brief as CommonMark does: a section opens at the ATX heading written `## Decisions`, `## Dependencies` or
`## For the cut`, and runs to the next heading of level one or two, in any form, or HTML heading of those levels; a section's
lines split at a newline. A carriage return not before a newline SHALL exit 1, naming its line. It SHALL also exit 1 when a
line of `## For the cut` is none of: a blank line; a head, opening
`<n>. ` and one space at the line's start; under a head, a `- models: ` or `- **Acceptance:** ` line indented three spaces or
as far as its head's text; a line indented at least two spaces past its Acceptance line, after that line or its
continuation; or the cut's `Cut <YYYY-MM-DD> as <id> at <sha>.` line. It SHALL also exit 1 when a head names a slug, an
`after` entry or a `beside` entry that `conduct.py`'s `SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or
more than one, or more than one `beside:`, or when an item has no `models:` line, more
than one, or one not naming the build, converge, release and cut station in order, then any of the build-moderate,
conformance, adversarial and fix parts in that order, each with a model and effort of `[A-Za-z0-9._-]` alone, then at most a
last `shadow`. The converge, conformance and adversarial part MAY instead be the word `skip` alone, in place of its model and
effort. It SHALL exit 1, naming the item, on a skip beside `shadow`, on `converge skip` beside a conformance, adversarial or
fix part, and on `conformance skip` and `adversarial skip` together. A head MAY
omit `beside:`. A build,
converge, release, conformance or adversarial model MAY open with a host, `claude/` or `codex/`; a host it does not know, or a
host on the cut, fix or build-moderate model, SHALL exit 1, naming it. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or
`## For the cut` holds a character for which `str.isprintable()` is false, printing `brief: halt — <section> line <n>: a
character isprintable() refuses`; when a heading of any form, a line of an HTML block, or a line holding an inline `<h1>`…`<h6>`
tag, that is not `## Decisions`, `## Dependencies` or `## For the cut` as written, reads as one of them once its `<h1>`…`<h6>`
tags and every character but a letter or a digit are dropped and case is folded,
a letter or digit outside ASCII standing for any one, and at least one ASCII letter left, or a second heading is
one of them as written; a line inside a fenced or indented code block SHALL be none of these; when the brief has no
`## Dependencies`; and when that section is neither `None.` nor a table of item,
package, constraint and why whose every row names a `## For the cut` item's slug, a package and a constraint. It SHALL also
exit 1, naming the fact, when an item of `## Facts` does not end ``(`<path>:<line>[-<line>]`[, …] at `<sha>`)``, each path
repository-relative with a `/` or a leading `./`, none absolute or holding `..`, each sha 7 to 40 lowercase hex digits: a
basename, a bare line number and a legend are refused.
It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot
be parsed. It SHALL run no command it reads.
`brief_check.py --facts <brief>` SHALL print each fact of `## Facts` as JSON — its text, each cited path with its first and
last line, and its sha — or the lines of a fact out of grammar and exit 1. `brief_check.py --models <brief> <slug>` SHALL print
the models file of the `## For the cut` item named `<slug>` as TOML, in the form `conduct.py` reads, exit 1 printing the item's
halts when its line is out of shape, and exit 2 when no item has that slug.

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

#### Scenario: A models line naming a skip
- **WHEN** an item's models line reads `build claude-opus-5-5 high · converge claude-opus-5-5 high · release
  claude-sonnet-5-5 medium · cut claude-opus-5-5 high · conformance claude-opus-5-5 high · adversarial skip`, or its converge
  part reads `converge skip` with no conformance, adversarial, fix or shadow part
- **THEN** that line halts nothing
- **AND WHEN** a skip stands beside `shadow`, `converge skip` beside a `fix` part, or `conformance skip` beside `adversarial
  skip`
- **THEN** `brief_check.py` exits 1, naming the item
- **AND WHEN** a skip part names a model, as `adversarial skip claude-opus-5-5`
- **THEN** `brief_check.py` exits 1, naming the item

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

#### Scenario: A For the cut heading in a fenced block
- **WHEN** a brief holds `## For the cut` inside a fenced code block, besides its own `## For the cut`
- **THEN** that line halts nothing and opens no section, as CommonMark reads it

#### Scenario: A lone carriage return
- **WHEN** a brief's line holds a carriage return not before a newline
- **THEN** `brief_check.py` exits 1, naming that line

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

#### Scenario: A fact in the citation form
- **WHEN** a brief's `## Facts` item ends ``(`skills/x/a.py:12-14`, `docs/b.md:3` at `ccfa6a1`)``
- **THEN** `brief_check.py` accepts it, and `--facts` prints its text, its two paths with their lines, and `ccfa6a1`

#### Scenario: A fact out of the citation form
- **WHEN** an item cites a basename `a.py:12`, a bare `:12`, a legend `C:4357-4406`, a path holding `..`, or ends with no
  `at <sha>`
- **THEN** `brief_check.py` exits 1, naming that fact, and `--facts` prints no JSON

#### Scenario: A brief's models file
- **WHEN** an item's models line holds `build-moderate`, a `codex/` checker, a `skip` and a last `shadow`, and its head says
  `decide: recommended`
- **THEN** `--models <brief> <slug>` prints `decide = "recommended"`, a table per station and part with `executor` where a host
  is named, `skip = true` where the part skips, and `shadow = true` under `[converge]`
- **AND WHEN** `<slug>` names no item
- **THEN** it exits 2

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
When the highest row of *Suggesting models* any phase of a change matches is the moderate row — fresh prose, moderate
logic — the cut SHALL suggest Sonnet 5.5 · high for the whole build where the session offers it, and the strongest tier · medium where it
does not; it SHALL suggest one build model a change. A `build-moderate` part the brief's models line names SHALL be written
as `[build.moderate]`, for the phases the cut rates `moderate`.
It SHALL write the suggestion to `.minions/changes/<change-id>/models.toml`, a table per station, as well as show it, and
SHALL never write it into the change. When the brief's `## For the cut` item names models for the change, the file SHALL hold
those instead, as the person's choice made at the plan's close: `conduct.py cut` writes them at queue time, and a cut by hand
writes what `brief_check.py --models` prints. Authentication and provider configuration SHALL remain the
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

## ADDED Requirements

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL print each row it leaves to judgment — `I5` to `I10`, `I15`, `I16`, `P12` and
`P13`'s paragraphs — and a summary line, and exit 1 on a mechanical failure, which the cut SHALL fix and run again. The
self-check SHALL write that summary line and the judgment rows only. `gate_check.py --tasks` SHALL be called the gate-edit check
in the cut's prose. `mf-plan`'s re-measure of a continued brief SHALL run `facts.py` and re-read only the facts it leaves
unplaced.

#### Scenario: A precondition fails
- **WHEN** the tree is dirty, the id is taken, or `make -n gate` lists no command
- **THEN** `cut_pre.py` prints a line naming that check, exits 1, and the cut halts

#### Scenario: Every precondition holds
- **WHEN** each check holds
- **THEN** `cut_pre.py` prints one line per check and exits 0

#### Scenario: The readers of a deleted name
- **WHEN** a task deletes `_old_name`
- **THEN** `facts.py readers _old_name` prints each `git grep -nw` hit at `HEAD` with its `path:line`, or `none`, and the cut
  names each reader in a task

#### Scenario: A mechanical failure
- **WHEN** a sub-task of `tasks.md` has no `Verify:`, or the design has no `## Tests` section
- **THEN** `cut_check.py` prints the failed row, exits 1, and the cut fixes the file and runs it again

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts

### Requirement: A queued cut's models file is written by the queue

`conduct.py cut` SHALL run `brief_check.py --models <brief> <slug>` before it reserves an id, and stop with exit 2 reserving
nothing when it exits other than 0 or prints text TOML does not read. It SHALL write that text to
`.minions/changes/<id>/models.toml` through no link, and keep it in the queue entry. Each time the run takes the cut, before it
starts a cutter or checks the branch, the run SHALL write it there again. A cut SHALL pass only when the file's hash is the hash of the entry's text; an entry with no models text,
queued before this requirement, SHALL pass on the file standing, as before. The hash SHALL be checked at the cut alone.

#### Scenario: A cut is queued
- **WHEN** `conduct.py cut a minor brief=<path>` runs on a brief whose item `a` names its models
- **THEN** `.minions/changes/<id>/models.toml` holds the TOML `brief_check.py --models` printed, and the entry holds the same text

#### Scenario: A brief with no such item
- **WHEN** the brief has no `## For the cut` item for the slug
- **THEN** `conduct.py cut` exits 2, and no reservation or entry stands

#### Scenario: A cutter changes the file
- **WHEN** the cutter writes `.minions/changes/<id>/models.toml` with other text
- **THEN** the cut fails at `cut-halted`, naming the file

#### Scenario: A rejoin after a changed file
- **WHEN** a cut that halted on a changed file is rejoined
- **THEN** the run writes the entry's text back before it checks the branch, and the cut can pass

### Requirement: A tag that only starts like a heading ends no section

`brief_check.py` and `conduct.py`, reading a brief's or a `design.md`'s sections as CommonMark with GFM tables, SHALL read an
HTML block as a heading of level one or two only when its tag name is `h1` or `h2` exactly, followed by whitespace, `/`, `>` or
the end of the line. A custom tag such as `<h12>` or `<h2-widget>` SHALL end no section.

#### Scenario: A custom tag above a package table
- **WHEN** a `design.md`'s `## Dependencies` holds `None.`, a custom `<h12>` block, then a table listing a package
- **THEN** the cut station reads the section as neither `None.` nor one table, and fails the cut: the tag hides no table

#### Scenario: A real HTML heading
- **WHEN** a section is followed by a line `<h2 id="x">Next</h2>`
- **THEN** the section ends there, as before
