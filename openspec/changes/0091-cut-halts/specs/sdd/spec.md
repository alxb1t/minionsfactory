## MODIFIED Requirements

### Requirement: The build approves a dependency only as the cut committed it

`skills/mf-build/SKILL.md` SHALL add a package without a halt only when `## Dependencies` of the change's
`design.md`, as committed in the cut commit, lists it, and SHALL halt when the branch has changed that section
since the cut. The cut commit SHALL be the one commit that adds `design.md`; more than one SHALL be a halt.
`skills/mf-cut-change/SKILL.md` SHALL show `## Dependencies` to the human word for word when it is not `None.`,
each entry a row of an exact package name and a version constraint. An unattended cut SHALL show nothing: it SHALL commit
a row its brief's `## Dependencies` lists for its change, package and constraint as written, and SHALL halt in `cut.halt`
on any other row, committing nothing, whatever the brief's switch.

#### Scenario: A dependency added on the branch halts the build
- **WHEN** a build pass finds a package in `## Dependencies` that the cut commit's `design.md` does not list
- **THEN** the build halts and asks for approval, rather than adding the package

#### Scenario: A design re-added on the branch halts the build
- **WHEN** `design.md` was deleted and added again on the branch, so more than one commit adds it
- **THEN** the build halts rather than choose a cut commit

#### Scenario: An unattended cut adds an approved package
- **WHEN** an unattended cut's design needs a package its brief's `## Dependencies` lists for its change, with that
  constraint
- **THEN** the cut lists it in `design.md`'s `## Dependencies` and commits without a halt
- **AND WHEN** the design needs a package the brief does not list, or another constraint
- **THEN** the cut writes `cut.halt`, naming the package, and commits nothing

### Requirement: The cut commits without waiting, unless it adds a dependency

`skills/mf-cut-change/SKILL.md` SHALL commit the change once its self-check passes, without waiting for the human.
It SHALL wait for the human's OK before the commit only when `## Dependencies` is not `None.`, when a
self-check item cannot be met, or when the plan review leaves a doubt to the person; an unattended cut SHALL halt there
instead, committing nothing, save a `## Dependencies` whose every row its brief's `## Dependencies` lists for its change,
which it commits. An edit after the commit SHALL be a further commit on the branch.

#### Scenario: The cut's show step commits without waiting
- **WHEN** the self-check passes, `## Dependencies` is `None.`, and the plan review leaves no doubt to the person
- **THEN** `mf-cut-change` shows the change and commits without waiting

#### Scenario: A dependency, or an unmet item
- **WHEN** `## Dependencies` is not `None.`, or a self-check item cannot be met
- **THEN** the cut waits for the human's OK before committing
- **AND WHEN** the cut is unattended and a self-check item cannot be met, or a row is one its brief does not list
- **THEN** it halts in `cut.halt` and commits nothing

#### Scenario: A plan-review doubt left to the person
- **WHEN** the plan review leaves a doubt to the person
- **THEN** the cut waits for the human's OK before committing

### Requirement: The plan station checks the line's rules before its first round

Before its first round, `mf-plan` SHALL report as facts: the debt cards whose trigger the version fires, proposed
for `debt:`; a recommendation to pay down first when the debt holds more than ten open cards; whether
the version's bump fits the repository's rule for a patch; the decisions in force the version touches, naming any overturn; a split
when one diff would be too large for review; re-measured facts when continuing a brief written against an older
commit; each package the version would add, its exact name and version constraint; and, when the target holds
`metrics/catalogue.toml`, the metrics past their watch in the latest tracked data file. Where the host starts background
workers, the fact-finding and these checks SHALL run in background helpers: the station SHALL return to the chat at once,
saying it is gathering the facts, and SHALL write `## Facts` and post its first round when they report; a re-measure
between rounds SHALL run in the background too. The rounds, the person's answers and the brief's writes SHALL stay in the
main thread. A package the version would add SHALL be put to the person in a round, each approved or not.

#### Scenario: A version planned in a repo with metrics
- **WHEN** the target has a catalogue and a tracked data file with a metric past its watch
- **THEN** the first round lists that metric as a fact, read from the data file, with no collection run

#### Scenario: A brief continued against a newer commit
- **WHEN** `from=` names a brief whose facts cite an older commit than the default branch's
- **THEN** the station re-measures those facts before its first round

#### Scenario: A plan on a host with background workers
- **WHEN** `mf-plan` starts where the host runs background workers
- **THEN** it dispatches the fact-finding and the checks to background helpers and returns to the chat at once
- **AND WHEN** they report
- **THEN** it writes `## Facts` and posts its first round

#### Scenario: A version that adds a package
- **WHEN** the version's phases need a package the target does not hold
- **THEN** the facts name the package and its constraint, and a round asks the person to approve it

### Requirement: The plan station writes the brief after every round

`mf-plan` SHALL require `brief=<path>` and SHALL write the brief there after every round, with the sections: a title
naming the version, its form, its depth (`light` or `hard`) and the date; one bold line; an `At <sha>, <YYYY-MM-DD>.` line naming
the commit the newest round read; `## Facts`, each with
`path:line` at a named commit; `## Decisions`, one row per settled question; in a hard brief, `## Dependencies`, `None.` or
one row per package the person approved, naming the `## For the cut` item's slug, the package, its version constraint and
why; `## Phases`; `## Not in this`;
`## Open`, the frontier still to ask; and `## For the cut`, filled when the frontier is empty. A hard brief's `## For the cut`
SHALL name, per change in cut order, its slug, bump, `after`, `debt:` ids, `decide: recommended` when the person delegates a
cut's doubts, its Acceptance as commands, and a model and effort for the build, converge, release and the cut station, from
the models the session offers. A hard brief SHALL end
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

### Requirement: A cut reserves its id against every open version branch

`skills/mf-cut-change/SKILL.md` SHALL take a change id only when its number is higher than every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch and on every branch named by a change id and not merged
into it, and than every reservation in `.minions/cuts/`; an unattended cut SHALL instead find its own reservation there. A cut
by hand of an id whose reservation stands SHALL halt first with
`<id> is queued for the cut station: answer it in the brief, then conduct.py rejoin <id>`. It
SHALL take `bump=minor|patch`, write `bump:` into `proposal.md`'s frontmatter, and assign no number.

#### Scenario: Two cuts while one change is open
- **WHEN** a version branch holding change `0040-x` is not yet merged, and a second cut is asked for id `0040-y`
- **THEN** the cut halts: the id is taken by an open branch

#### Scenario: A cut by hand beside a queued cut
- **WHEN** `.minions/cuts/0041-q` stands, and a cut by hand is asked for id `0041-y`
- **THEN** the cut halts: the id is reserved

#### Scenario: A cut by hand of a queued id
- **WHEN** `.minions/cuts/0041-q` stands, and a cut by hand is asked for id `0041-q`
- **THEN** the cut halts with `0041-q is queued for the cut station: answer it in the brief, then conduct.py rejoin 0041-q`,
  and writes nothing

### Requirement: A settled brief is queued for a cut

`conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] --executor claude|codex [--model <m>] [--effort <e>]`, run
in the primary, SHALL take the next free change number under the repository's queue lock: one above every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch, every branch named by a change id and its committed
change directories, every reservation in `.minions/cuts/` and every queued cut. It SHALL write the reservation
`.minions/cuts/<id>` and keep the cut's bump, brief path, `after` ids, executor, model and effort in the queue in the home
folder, where no worker writes, with the package and constraint of each row of the brief's `## Dependencies` whose item is
`<slug>`, then hand the cut to the live run, or, with none live, start a run detached and wait, under
the lock, until that run holds its claim or has ended. A brief with no `## Dependencies` approves no package. A slug that is
not lowercase words joined by `-`, a bump other than
`minor` or `patch`, a brief that is no file, a brief whose `## Dependencies` is neither `None.` nor a table of item, package,
constraint and why, or an `after` id that names no open version or queued cut SHALL exit 2 and
reserve nothing; so SHALL a run that cannot start, its precondition named. Queuing a cut SHALL be the person's yes to cut,
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

### Requirement: A run cuts each queued brief in a station of its own

A run SHALL read the queue at its start and at every poll, and take each queued cut with no halt that it has not read
before, or that a request names. For each, `conduct.py` SHALL make the branch named by its id and its linked worktree from the
default branch, as code, then run `mf-cut-change` with `unattended=yes` as a fresh sandboxed worker in that worktree, logged
as the station `cut`. The cut SHALL pass when the branch's tip is the change's `docs(<id>): land the change directory` commit,
the branch holds `openspec/changes/<id>/`, its tree is clean, `.minions/changes/<id>/models.toml` stands, and each row of the
`## Dependencies` of the branch's `design.md` names a package and constraint the queue entry holds, as written; a
`## Dependencies` that is neither `None.` nor a table of package, constraint and why SHALL fail it, and a missing one adds no
package. The run SHALL then
delete its queue entry and reservation, read its models file and probe a new executor, and take the version through its
stations as any open version. A branch that already holds the change SHALL be checked, not cut again. A cut whose
`after` names a queued cut SHALL wait until that cut passes, and halt when it halts. The cutter's executor SHALL be probed
before its first worker, as a version's is. The run SHALL never read the brief for a package's approval.

#### Scenario: A queued cut is built
- **WHEN** a run takes a queued cut and the cutter commits its change directory and models file
- **THEN** the cut passes, its reservation goes, and the version goes into `build` in the same run

#### Scenario: A cut queued during a run
- **WHEN** a cut is queued while a run is live
- **THEN** the run takes it at its next poll, beside the versions it is running

#### Scenario: A cut that adds the approved packages
- **WHEN** the cutter commits a `design.md` whose `## Dependencies` lists only packages and constraints the queue entry holds
- **THEN** the cut passes, and the version goes into `build`

#### Scenario: A cut that adds another package
- **WHEN** the committed `design.md` lists a package the queue entry does not hold, or a constraint other than the one it holds
- **THEN** the cut halts at `cut-halted`, naming each such package and constraint

### Requirement: A cut halt is the plan's, answered by a re-plan and a rejoin

A cut that does not pass SHALL put its queued cut at the stage `cut-halted`, with one line: the line the cutter wrote in
`.minions/changes/<id>/cut.halt`, else the failed check or worker exit, kept in its queue entry. The cutter's own line, and a
package outside the queue entry's rows, SHALL end
` · needs <id> its brief answered (/mf-plan <id> depth=hard brief=<brief> from=<brief>), then conduct.py rejoin <id>`, `<brief>`
the path its queue entry holds; every other cut halt keeps its line. No rescue SHALL run. `status`
SHALL print `<id> · cut` for a queued cut and `<id> · cut-halted — <line>` for a halted one, `report` SHALL print its halt
line, and the run's closing line SHALL name ` · needs <id> its brief answered (…), then conduct.py rejoin <id>` for a cut
halted with that answer. A run's start SHALL log each halted cut as a halt and take it into no thread. `conduct.py rejoin <id>`
naming a queued cut SHALL clear its halt and copy the brief's `## Dependencies` rows for its slug again, under the queue lock,
then request it from the live run, or start a run when none is live; a brief it cannot read, or whose `## Dependencies` is
neither `None.` nor a table, SHALL exit 2, naming it, and keep the halt. The run SHALL then drop the cut's branch and worktree,
when its branch holds no change, and cut again from the brief.

#### Scenario: A cutter halts
- **WHEN** the cutter writes `cut.halt` and commits nothing
- **THEN** the run logs `<id> · halt — cut-halted — <its line> · needs <id> its brief answered (…), then conduct.py rejoin <id>`,
  runs no rescue, `status` prints `<id> · cut-halted — ` and the same line, and the closing line names the answer

#### Scenario: A re-plan and a rejoin
- **WHEN** the person re-plans the brief and runs `conduct.py rejoin <id>`
- **THEN** the cut's half-done branch is dropped, the brief is cut again, and a cut that passes goes into `build`

#### Scenario: A package approved at the re-plan
- **WHEN** a cut halted on a package outside its queued rows, and the person's re-plan adds that row to the brief's
  `## Dependencies` before `conduct.py rejoin <id>`
- **THEN** the rejoin copies the rows again, and the branch's cut is checked again and passes

#### Scenario: A failed check on disk
- **WHEN** a cut halts on a dirty tree, a missing models file, a kept worktree or a worker's exit
- **THEN** its line names no brief, and the closing line names `a fix`

### Requirement: An unattended cut decides by the brief's switch

`skills/mf-cut-change/SKILL.md` SHALL take `unattended=yes`, set by the cut station alone. Unattended, the cut SHALL hold no
awake hold, start in the worktree the conductor made with its own reservation standing, and never wait for the person. Where
the brief's `## For the cut` item for the change says `decide: recommended`, a moved fact that fails and a plan-review doubt
that changes a settled decision or survives the second review SHALL take the recommended option, and the cut SHALL add a row
`| C<n> | decided by the cutter: … | <reason> |` to the brief's `## Decisions`. A `## Dependencies` row the brief's
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
- **THEN** the cut takes it, adds a `decided by the cutter` row to the brief, and commits

#### Scenario: A dependency
- **WHEN** an unattended cut's `## Dependencies` holds a row its brief's `## Dependencies` does not list for the change
- **THEN** it writes `cut.halt` and commits nothing, whatever the switch
- **AND WHEN** every row is one the brief lists, as written
- **THEN** it commits

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one.
Lines split at a newline alone. It SHALL also exit 1 when a line of `## For the cut` is none of: a blank line; a head, opening
`<n>. ` and one space at the line's start; a `- models: ` or `- **Acceptance:** ` line indented three spaces or as far as its
head's text; a line indented at least two spaces past its Acceptance line, after that line or its continuation; or the cut's
`Cut <YYYY-MM-DD> as <id> at <sha>.` line. It SHALL also exit 1 when a head names a slug or an `after` entry that `conduct.py`'s
`SLUG` refuses, a bump other than `minor` or `patch`, no `after:` or more than one, or when an item has no `models:` line, more
than one, or one not naming the build, converge, release and cut station in order, each with a model and effort of
`[A-Za-z0-9._-]` alone. It SHALL also exit 1 when a line of `## Decisions`, `## Dependencies` or `## For the cut` holds a
character for which `str.isprintable()` is false, printing `brief: halt — <section> line <n>: a character isprintable()
refuses`; when a line of the brief that is not `## Decisions`, `## Dependencies` or `## For the cut` as written reads as one of
them once every character but a letter or a digit is dropped and case is folded, or a second line is one of them as written;
when the brief has no `## Dependencies`; and when that section is neither `None.` nor a table of item, package, constraint
and why whose every row names a `## For the cut` item's slug, a package and a constraint.
It SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot
be parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`, or an
  item's slug or cut effort holds `$(…)` or `;`
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** a `## For the cut` line opens `- ` where `<n>. ` is due, a `| ` line sits under a head, an unindented line
  follows a head, or a head holds a second `after:`, or an item has a second models line
- **THEN** `brief_check.py` exits 1, naming the line or the item

#### Scenario: A checked line holds a character not printable
- **WHEN** a line of a brief's `## For the cut`, `## Dependencies` or `## Decisions` holds a no-break space, an ideographic
  space, a tab, a vertical tab, a form feed, U+200B or U+2060
- **THEN** `brief_check.py` exits 1, printing `brief: halt — <section> line <n>: a character isprintable() refuses` for that line

#### Scenario: A For the cut heading in another form
- **WHEN** a brief holds ` ## For the cut`, `##<tab>For the cut`, `## For the cut ##`, `## For the cut` followed by U+200B, or
  `For the cut` underlined `---`, besides its `## For the cut`, or that heading twice
- **THEN** `brief_check.py` exits 1, naming each such line

#### Scenario: A brief's packages
- **WHEN** a hard brief has no `## Dependencies`, or one that is prose, or a row naming no `## For the cut` item
- **THEN** `brief_check.py` exits 1, naming each
- **AND WHEN** it reads `None.`, or each row names an item, a package and a constraint
- **THEN** that section halts nothing

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, its `## Dependencies`, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`

### Requirement: The plan's close queues the cut on the person's yes

At a hard close, once the person confirms the settled table, `skills/mf-plan/SKILL.md` SHALL run `brief_check.py` on the
brief, and fix and run it again until it exits 0. Unless `then=ship` was given, it SHALL then run `conduct.py status`, show
each `## For the cut` item as the brief holds it, its `models:` line and Acceptance included, each `## Dependencies` row, and
each open version or queued
cut `status` names that is not at a halt, and ask once, "confirm, and queue it?". On yes, or `then=ship`, it SHALL run
`conduct.py cut <slug> <bump> brief=<path> [after=<ids>] --executor <executor> --model <m> --effort <e>` from the primary for
each change of `## For the cut`, in order, an `after` that names an earlier change of the brief given as the id its `cut`
printed, and paste each line; that yes SHALL be the person's yes to every merge and push in the run it joins or starts: each
queued version, and each open version that run takes. On no, it SHALL end on one
`Next: /mf-cut-change <NNNN>-<slug> <bump> brief=<path>` line per change of `## For the cut`, in order, `<NNNN>` left for
the person. It SHALL still never cut: no branch, no change directory.

#### Scenario: The person says yes
- **WHEN** a hard close's brief passes `brief_check.py`, the close shows its `## For the cut` items, its `## Dependencies` rows
  and `conduct.py status`, and the person answers yes
- **THEN** `mf-plan` runs `conduct.py cut` for each change in order, pastes each line, and returns to the chat

#### Scenario: The person says no
- **WHEN** the person answers no
- **THEN** `mf-plan` queues nothing and ends on one `Next: /mf-cut-change <NNNN>-<slug> <bump> brief=<path>` line per change
