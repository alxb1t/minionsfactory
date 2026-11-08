## ADDED Requirements

### Requirement: A version names what it builds beside

`skills/mf-cut-change/SKILL.md` SHALL take `beside=<id>[,<id>]`, the versions this one only shares files with, and SHALL
write `beside: [<ids>]` into `proposal.md`'s frontmatter. `conduct.py` SHALL pass a queued cut's `beside` ids to its cutter
as `beside=<ids>`. No station SHALL wait on, block on or check a `beside` id: `conduct.py status` SHALL print a version's
stage as it would with no `beside:`, and a halt in a version a `beside:` names SHALL stop no other version. A file both
versions touch SHALL be merged and settled as any moved base is: by integrate, and under a version's switch by its
supervisor.

#### Scenario: A version beside an unreleased one
- **WHEN** a version's `proposal.md` names a lower open version that has not released in `beside:`
- **THEN** `conduct.py status` prints its stage as `build`, never `waiting`

#### Scenario: A queued cut beside another
- **WHEN** a run cuts a cut `conduct.py cut` queued with `beside=<id>`
- **THEN** the cutter's prompt carries `beside=<id>`, and the committed `proposal.md` reads `beside: [<id>]`

## MODIFIED Requirements

### Requirement: The plan station checks which versions can run side by side

When the person names versions to run side by side, `skills/mf-plan/SKILL.md` SHALL compare their briefs' `## Facts`
paths and `## Phases` files, and SHALL warn of any pair that touches a file in common, naming the file. It SHALL propose
`after:` only when one version needs a symbol, decision or requirement the other adds, and `beside:`, the default, for
file overlap alone. It SHALL propose no order.

#### Scenario: Two versions that touch the same skill
- **WHEN** two briefs both name `skills/mf-release/SKILL.md`, and neither needs what the other adds
- **THEN** `mf-plan` warns, naming the file, proposes `beside:`, and proposes no order

#### Scenario: One version needs the other's code
- **WHEN** one brief's phases use a symbol, decision or requirement the other brief's phases add
- **THEN** `mf-plan` proposes `after:` naming the other

### Requirement: The plan station writes the brief after every round

`mf-plan` SHALL require `brief=<path>` and SHALL write the brief there after every round, with the sections: a title
naming the version, its form, its depth (`light` or `hard`) and the date; one bold line; an `At <sha>, <YYYY-MM-DD>.` line naming
the commit the newest round read; `## Facts`, each with
`path:line` at a named commit; `## Decisions`, one row per settled question; in a hard brief, `## Dependencies`, `None.` or
one row per package the person approved, naming the `## For the cut` item's slug, the package, its version constraint and
why; `## Phases`; `## Not in this`;
`## Open`, the frontier still to ask; and `## For the cut`, filled when the frontier is empty. A hard brief's `## For the cut`
SHALL name, per change in cut order, its slug, bump, `after`, any `beside` ids, `debt:` ids, `decide: recommended` when the
person delegates a cut's doubts, its Acceptance as commands, and a model and effort for the build, converge, release and the
cut station, from the models the session offers. A hard brief SHALL end
on a settled table the person confirmed, with `## Open` removed. `from=<brief>` SHALL continue a brief. The station
SHALL NOT write the brief's path into the target.

#### Scenario: A thread ends mid-grilling
- **WHEN** a session ends after some rounds
- **THEN** the brief holds every settled decision and the open frontier
- **AND** a new session with `from=` continues from it

#### Scenario: No brief path
- **WHEN** `mf-plan` is started without `brief=`
- **THEN** it halts and asks for the path

#### Scenario: A hard close names the models
- **WHEN** a hard close fills `## For the cut`
- **THEN** each change's item names a model and effort for the build, converge, release and the cut station

#### Scenario: A hard brief names its packages
- **WHEN** the person approved a package in a round of a hard plan
- **THEN** the brief's `## Dependencies` holds its row: the item's slug, the package, its constraint and why
- **AND WHEN** the version adds no package
- **THEN** `## Dependencies` reads `None.`

### Requirement: A settled brief is queued for a cut

`conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] [beside=<id>[,<id>]] --executor claude|codex [--model <m>]
[--effort <e>]`, run
in the primary, SHALL take the next free change number under the repository's queue lock: one above every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch, every branch named by a change id and its committed
change directories, every reservation in `.minions/cuts/` and every queued cut. It SHALL write the reservation
`.minions/cuts/<id>` and keep the cut's bump, brief path, `after` ids, any `beside` ids, executor, model and effort in the
queue in the home folder, where no worker writes, with the package and constraint of each row of the brief's
`## Dependencies` whose item is `<slug>`, then hand the cut to the live run, or, with none live, start a run detached and
wait, under the lock, until that run holds its claim or has ended. A brief with no `## Dependencies` approves no package. A
queue entry with no `beside` SHALL read as one naming none. A slug that is not lowercase words joined by `-`, a bump other
than `minor` or `patch`, a brief that is no file, a brief whose `## Dependencies` is neither `None.` nor a table of item,
package, constraint and why, an `after` id that names no open version or queued cut, a `beside` id that is no change id, or
an argument after the brief that is neither `after=` nor `beside=`, or names either twice, SHALL exit 2 and reserve nothing;
so SHALL a run that cannot start, its precondition named. Queuing a cut SHALL be the person's yes to cut,
run, merge and push that version, and to the packages its rows name. A run SHALL take the queue lock before it removes its
claim, and then start the next run when a rejoin request or a queued cut it never read stands.

#### Scenario: Two cuts at once with no run live
- **WHEN** two `conduct.py cut` calls run at once and no run is live
- **THEN** they reserve two different numbers, and exactly one run starts

#### Scenario: A cut while a run is live
- **WHEN** `conduct.py cut` runs while a run is live
- **THEN** it reserves the next number, starts no run, and prints that the live run takes it

#### Scenario: A cut as a run ends
- **WHEN** a cut is queued after a run's last poll and before it removes its claim
- **THEN** the run's close starts the next run, which takes it
- **AND WHEN** the run read every queued cut and no request stands
- **THEN** its close starts no run

#### Scenario: A brief that is no file
- **WHEN** `brief=` names no file
- **THEN** `conduct.py cut` exits 2, naming it, and reserves nothing

#### Scenario: A brief's packages
- **WHEN** the brief's `## Dependencies` holds rows for the queued slug and for another item
- **THEN** the queue entry holds the package and constraint of the slug's rows alone
- **AND WHEN** the section is prose, neither `None.` nor a table
- **THEN** `conduct.py cut` exits 2, naming the section, and reserves nothing

#### Scenario: A cut beside another
- **WHEN** `conduct.py cut <slug> minor brief=<path> beside=<id>` runs, `<id>` a change id
- **THEN** the queue entry holds `<id>` as its `beside` ids
- **AND WHEN** a `beside` id is no change id, or the argument after the brief opens neither `after=` nor `beside=`
- **THEN** `conduct.py cut` exits 2, naming it, and reserves nothing

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
than one, or one not naming the build, converge, release and cut station in order, then any of the conformance, adversarial and
fix parts in that order, each with a model and effort of `[A-Za-z0-9._-]` alone, then at most a last `shadow`. A head MAY
omit `beside:`. A build,
converge, release, conformance or adversarial model MAY open with a host, `claude/` or `codex/`; a host it does not know, or a
host on the cut or fix model, SHALL exit 1, naming it. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or
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

### Requirement: The plan's close queues the cut on the person's yes

At a hard close, once the person confirms the settled table, `skills/mf-plan/SKILL.md` SHALL run `brief_check.py` on the
brief, and fix and run it again until it exits 0. Unless `then=ship` was given, it SHALL then run `conduct.py status`, show
each `## For the cut` item as the brief holds it, its `models:` line and Acceptance included, each `## Dependencies` row, and
each open version or queued
cut `status` names that is not at a halt, and ask once, "confirm, and queue it?". On yes, or `then=ship`, it SHALL run
`conduct.py cut <slug> <bump> brief=<path> [after=<ids>] [beside=<ids>] --executor <executor> --model <m> --effort <e>` from
the primary for each change of `## For the cut`, in order, an `after` or `beside` id that names an earlier change of the
brief given as the id its `cut` printed, and paste each line; that yes SHALL be the person's yes to every merge and push in
the run it joins or starts: each queued version, and each open version that run takes. On no, it SHALL end on one
`Next: /mf-cut-change <NNNN>-<slug> <bump> brief=<path>` line per change of `## For the cut`, in order, `<NNNN>` left for
the person. It SHALL still never cut: no branch, no change directory.

#### Scenario: The person says yes
- **WHEN** a hard close's brief passes `brief_check.py`, the close shows its `## For the cut` items, its `## Dependencies` rows
  and `conduct.py status`, and the person answers yes
- **THEN** `mf-plan` runs `conduct.py cut` for each change in order, pastes each line, and returns to the chat

#### Scenario: The person says no
- **WHEN** the person answers no
- **THEN** `mf-plan` queues nothing and ends on one `Next: /mf-cut-change <NNNN>-<slug> <bump> brief=<path>` line per change
