## MODIFIED Requirements

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's own `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines — those past the base's entries, which a stacked branch's base
holds and the default branch has released; a branch whose entries do not hold the base's SHALL halt the rule. It SHALL
renumber the branch's new decision to the next id free
on the default branch with its citations, and report each MODIFIED or REMOVED requirement title of the branch's delta
that the default branch changed since the branch's base. `.gitattributes` SHALL NOT set `merge=union`.
A **planned decision** — an id the branch's `openspec/changes/` files cite as `D<n> · <title>`, above the base's highest id and
headed nowhere in the branch's `docs/decisions.md` — SHALL count as the branch's new decision, save when the default branch's
`### D<n> · <title>` heading carries that title: then it is a dependency's, and stays. An id the plan cites with no title SHALL stay.
`skills/mf-converge/scripts/gate_check.py` SHALL compute the same moves for a merge commit. `conduct.py` and `integrate.py replay`
SHALL run the `decisions` rule on every merge they open, conflicted or clean, and the `changelog` rule on a conflicted
`CHANGELOG.md` and on every merge whose base holds `## [Unreleased]` entries.
The `decisions` rule SHALL renumber the `[Unreleased]` entries of `CHANGELOG.md` first, then recite each other changed path. A
path git left conflicted SHALL be skipped by the recital and printed as `decisions: conflicted — <path>: D<old> → D<new>`, for the
merge's note. A path whose citations the rule cannot attribute to a side SHALL be collected: the rule SHALL halt once, after every
path, naming each.
A MODIFIED title whose delta block only inserts into the default branch's current block — every edit an insertion, whitespace
ignored — and keeps nothing the default branch removed from the base's block SHALL NOT be reported. A delta that changes or
removes a line of that block, one that keeps what the default branch removed, a title the default branch removed, and every
REMOVED title the default branch changed SHALL be reported.

#### Scenario: Both sides added a decision
- **WHEN** the default branch took `D45` and the branch added its own `D45`
- **THEN** the branch's decision is renumbered `D46`, its citations with it

#### Scenario: Both sides changed a CHANGELOG
- **WHEN** the default branch cut a release section and the branch holds `[Unreleased]` entries
- **THEN** the entries stay above the release section, the blank lines intact

#### Scenario: A stacked branch's CHANGELOG
- **WHEN** a branch stacked on its dependency's built head holds that head's `[Unreleased]` entries and its own after them,
  and the default branch released the dependency, git merging `CHANGELOG.md` cleanly
- **THEN** the merge's `[Unreleased]` holds the branch's own entries alone, above the dependency's release section
- **AND WHEN** the branch's entries do not hold the base's
- **THEN** `changelog` halts

#### Scenario: A planned decision taken while the version waits
- **WHEN** the base's highest id is `D58`, the branch's plan cites `D59 · Branch rule` with no heading for it, and the default
  branch took `D59 · Main rule`, git merging `docs/decisions.md` cleanly
- **THEN** `decisions` renumbers the plan's `D59` to `D60`, its citations with it, and `gate_check.py` reads the same move from
  the merge commit

#### Scenario: A dependency's decision cited by title
- **WHEN** the branch's plan cites `D59 · Main rule`, and the default branch's `D59` heading carries `Main rule`
- **THEN** `decisions` leaves every `D59` as it is

#### Scenario: A conflicted file that cites the colliding decision
- **WHEN** the default branch took `D45`, the branch added its own `D45`, and a file git left conflicted cites it and sorts
  before the plan's files
- **THEN** `decisions` renumbers the plan's citations and the changelog's entry to `D46`, skips the conflicted file, and prints
  its path with `D45 → D46`
- **AND WHEN** two files hold citations that match neither merge
- **THEN** `decisions` renumbers every other path first, then halts once, naming both files

#### Scenario: A delta that only inserts
- **WHEN** the default branch changed a requirement since the base, and the branch's MODIFIED block holds the default branch's
  current block with lines added
- **THEN** `delta` reports nothing for it, and the merge goes on

#### Scenario: A delta that changes a line the default branch holds
- **WHEN** the default branch changed a requirement since the base, and the branch's MODIFIED block rewrites a line of the default
  branch's current block
- **THEN** `delta` reports the title, and exits 1

#### Scenario: A delta that keeps what the default branch removed
- **WHEN** the default branch dropped a sentence of a requirement since the base, and the branch's MODIFIED block keeps that
  sentence and adds a clause
- **THEN** `delta` reports the title, and exits 1

### Requirement: A version declares what it builds on

`skills/mf-cut-change/SKILL.md` SHALL take `after=<id>[,<id>]`, halting unless each id is an open or a released version with a
lower number — a released one has its `openspec/changes/archive/<id>/` in the default branch — and SHALL write `after: [<ids>]` into `proposal.md`'s frontmatter. A name a design takes from an `after:`
change's design, and a MODIFIED title a delta takes from an `after:` change's delta, SHALL count as present at the cut.
`conduct.py` SHALL start a dependent once each id has released, or once it stacks, as *A dependent builds on its dependency's
built head* says, and SHALL then merge the default branch into its cut-only branch, with no agent, running `integrate.py delta`
on the open merge and committing it when the check passes. A requirement the check names SHALL leave the merge open, with its
note under `.minions/changes/<change-id>/`, and halt the version as `integrating`. `mf-build` SHALL halt unless each id has
`openspec/changes/archive/<id>/` in `HEAD`, or, while `.minions/changes/<change-id>/stacked-on` stands, the commit it names is
an ancestor of `HEAD` and holds `openspec/changes/<id>/tasks.md`. `mf-release` and `mf-integrate`'s Ready SHALL halt unless each
id has `openspec/changes/archive/<id>/` in `HEAD`. `conduct.py status` SHALL print `waiting` for a dependent whose dependency has
not released and that has not stacked. An `after:` edited past the cut SHALL stop no other version: an unreleased id that is
not lower SHALL block its version, and an edit that leaves a running version `waiting` SHALL halt it.

#### Scenario: An edit makes a cycle
- **WHEN** two versions name each other in `after:`, or one names itself, and a third is free
- **THEN** the named versions block with no worker, the third ships, and the run closes

#### Scenario: A worker edits its own `after:`
- **WHEN** a build worker adds an unreleased id to its version's `after:`
- **THEN** that version halts on `waiting`, and every other version goes on

#### Scenario: A dependent waits
- **WHEN** a version names a lower open version in `after:`, and `mf-ship` runs
- **THEN** its build starts only once that version's build check passes, on its built head, and its converge only after that
  version's release, on a tree that holds it
- **AND** unrelated versions run in parallel meanwhile

#### Scenario: A dependent's delta edits what its dependency changed
- **WHEN** an unstacked dependent's delta modifies a requirement the default branch changed since its base, and the run
  takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** the merge stays open, the note names both changes, and the version halts with no build
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` builds the version

#### Scenario: A stacked dependent's delta edits what its dependency released
- **WHEN** a stacked dependent's build is done, its delta modifies a requirement its dependency's release changed, and the
  run takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** the merge back stays open, the note names both changes, `stacked-on` stands, and the version halts as
  `integrating`, its build done
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` removes `stacked-on`, builds nothing again, and runs converge from round 1

#### Scenario: A cut names a dependency it cannot have
- **WHEN** `after=` names an id that is unknown, or not lower than the change's
- **THEN** the cut halts, naming it

#### Scenario: A cut names a dependency that released while it waited
- **WHEN** a queued cut's `after` names a lower id whose archive folder the default branch holds
- **THEN** the cut goes on, and `conduct.py` hands its cutter no `after=` for that id

#### Scenario: A dependent built by hand
- **WHEN** `mf-build` starts on a change whose `after:` id is not in `HEAD`'s archive, and no `stacked-on` stands
- **THEN** it halts, naming `I17`

### Requirement: A run goes on while origin cannot be reached

`conduct.py` SHALL keep an **offline base** in the home folder, `~/.mf-ship-origin/<digest>.pushed`: the default branch's sha as
`origin` last listed it, written after every read of `origin` that succeeds and every push of the default branch. A run whose
read of `origin` fails SHALL try it three times, then go on with no remote call, judging the default branch's release merges
against the offline base wherever it judges them against `origin`; with no offline base it SHALL halt, naming
`conduct.py anchor`. Every failed read or push SHALL be a wait, whatever its error; a read that succeeds and shows a refused URL,
a moved default branch or a default named other than the kept one SHALL halt as before. A release made while `origin` is unread
SHALL pass its check as released locally, its worktree removed and its dependents merged from the local default branch, its
ledger entry kept until its push lands. The check that reads `origin`'s tag after the run's own push SHALL try a failed read
once more, logging each failure as a wait, before the run goes on with no remote call. Each release SHALL push what is pending,
and the run SHALL try once more before its close. The `start` line SHALL say when `origin` is unreachable, each failed push SHALL be logged as `push — waiting`, the close
SHALL name what stays unpushed, and `report` SHALL print every wait. `conduct.py anchor` SHALL write the first offline base from
`refs/remotes/origin/<default>` only when no run is live, no offline base stands, the ref is an ancestor of the local default
branch, it is a release merge whose tag stands, and the person names its sha with `--yes <sha>`; with no `--yes` it SHALL print
the sha and subject and write nothing, and otherwise it SHALL refuse, naming the check. The conductor's remote calls SHALL
pass `ssh -o ConnectTimeout=15 -o BatchMode=yes` when neither `GIT_SSH_COMMAND` nor a `core.sshCommand` in the operator's
config, or a file it includes, is set.

#### Scenario: A good read keeps the offline base
- **WHEN** a run reads `origin`, or pushes its default branch
- **THEN** the offline base holds the default branch's sha `origin` lists

#### Scenario: Origin is down at the start
- **WHEN** a run starts and every read of `origin` fails
- **THEN** it logs three tries, its `start` line says `origin: unreachable — pushes wait`, and it builds and converges every open
  version
- **AND WHEN** a commit on the local default branch is no release a ledger head explains, past the offline base
- **THEN** the run halts naming the commit, and pushes nothing

#### Scenario: No offline base
- **WHEN** a run starts, every read of `origin` fails, and no offline base stands
- **THEN** the run halts naming `conduct.py anchor`, and starts no worker

#### Scenario: A release while origin is down
- **WHEN** a version's release merges while `origin` cannot be read
- **THEN** its check passes as released locally, its worktree is removed, a `push — waiting` line is logged, and a dependent
  merges it from the local default branch and ships in the same run
- **AND** the close names the unpushed refs, the default branch and each local release's tag, and `report` prints the wait

#### Scenario: A read that fails once after a push
- **WHEN** a release's own push lands, and the next read of `origin`'s tag fails once, then answers
- **THEN** the check passes on the second read, the run stays online, and the first failure is logged as a wait

#### Scenario: Origin comes back
- **WHEN** `origin` answers again before the run's close, or at the next run's start
- **THEN** the pending default branch and tags are pushed, and the ledger entries whose heads landed are removed
- **AND WHEN** `origin`'s default branch moved meanwhile, so the local one is not its descendant
- **THEN** the run halts as before, and pushes nothing

#### Scenario: A person anchors the offline base
- **WHEN** no run is live, no offline base stands, and `refs/remotes/origin/<default>` is a tagged release merge on the local
  default branch
- **THEN** `conduct.py anchor` prints its sha and subject, naming `--yes <sha>`, and writes nothing
- **AND WHEN** the person runs `conduct.py anchor --yes <sha>` with that sha
- **THEN** it writes the sha as the offline base and prints its sha and subject
- **AND WHEN** a run is live, an offline base stands, the ref is not an ancestor of the local default branch or not a tagged
  release merge, or the `--yes` sha is not the ref's
- **THEN** it refuses, naming the check, and writes nothing

### Requirement: The integrate station renumbers the branch's changelog entries

`skills/mf-integrate/scripts/integrate.py decisions` SHALL renumber each colliding decision id cited in the `[Unreleased]` entries
of the `CHANGELOG.md` the `changelog` rule wrote, and SHALL leave the released sections as they are. It SHALL
renumber them before it recites any other changed path, so a path that halts the rule leaves them renumbered. It SHALL NOT compare
`CHANGELOG.md` with a three-way merge of its sides.

#### Scenario: A renumbered decision in the branch's entry
- **WHEN** the branch's `[Unreleased]` entry cites a decision id the default branch also added, and a released section cites the
  same id
- **THEN** `decisions` renumbers the entry's citation, keeps the released section's, and exits 0

### Requirement: A cut halt is the plan's, answered by a re-plan and a rejoin

A cut that does not pass SHALL put its queued cut at the stage `cut-halted`, with one line: the line the cutter wrote in
`.minions/changes/<id>/cut.halt`, else the failed check or worker exit, kept in its queue entry. The cutter's own line, and a
package outside the queue entry's rows, SHALL end
` · needs <id> its brief answered (/mf-plan <id> depth=hard brief=<brief> from=<brief>), then conduct.py rejoin <id>`, `<brief>`
the path its queue entry holds; every other cut halt keeps its line. No rescue SHALL run. `status`
SHALL print `<id> · cut` for a queued cut, `<id> · cut — waits: <n> in flight, cap <N>` for one that waits for room under the
cap, and `<id> · cut-halted — <line>` for a halted one, `report` SHALL print its halt
line, and the run's closing line SHALL name ` · needs <id> its brief answered (…), then conduct.py rejoin <id>` for a cut
halted with that answer. A run's start SHALL log each halted cut as a halt and take it into no thread. `conduct.py rejoin <id>`
naming a queued cut SHALL clear its halt, under the queue lock, keeping the queue entry's already-queued package rows, then
request it from the live run, or start a run when none is live, and SHALL clear and request, the same way and down the chain, each
queued cut whose halt reads `after <name> is cut-halted`, `<name>` the cut it rejoins or a dependent it cleared, naming each in
its line; a brief it cannot read, or whose `## Dependencies` is
neither `None.` nor a table, SHALL exit 2, naming it, and keep the halt. A row of the brief's `## Dependencies` for its slug
that the entry does not already hold SHALL be queued only when the rejoin is given `--yes <hash>`, `<hash>` the sha256 of
those new rows; without it, or with another hash, the rejoin SHALL exit 1, keep the entry and its halt, and name each new
row and the exact `conduct.py rejoin <id> --yes <hash>` command, the person's yes to those rows. `--yes` on a rejoin naming
no queued cut SHALL exit 2. The run SHALL then drop the cut's branch and worktree,
when its branch holds no change, and cut again from the brief.

#### Scenario: A cutter halts
- **WHEN** the cutter writes `cut.halt` and commits nothing
- **THEN** the run logs `<id> · halt — cut-halted — <its line> · needs <id> its brief answered (…), then conduct.py rejoin <id>`,
  runs no rescue, `status` prints `<id> · cut-halted — ` and the same line, and the closing line names the answer

#### Scenario: A re-plan and a rejoin
- **WHEN** the person re-plans the brief and runs `conduct.py rejoin <id>`
- **THEN** the cut's half-done branch is dropped, the brief is cut again, and a cut that passes goes into `build`

#### Scenario: A chain of cut halts rejoined at its head
- **WHEN** queued cuts `0002-a`, `0003-b` and `0004-c` stand halted, `0003-b` with `after 0002-a is cut-halted` and `0004-c` with
  `after 0003-b is cut-halted`, and the person runs `conduct.py rejoin 0002-a`
- **THEN** the halt of each of the three entries is cleared, the live run is asked for each, and the rejoin's line names the three

#### Scenario: A package approved at the re-plan
- **WHEN** a cut halted on a package outside its queued rows, and the person's re-plan adds that row to the brief's
  `## Dependencies` before `conduct.py rejoin <id>`
- **THEN** the rejoin exits 1 naming that row and `conduct.py rejoin <id> --yes <hash>`
- **AND WHEN** the person runs that command
- **THEN** the row is queued beside the queued rows, and the branch's cut is checked again and passes

#### Scenario: A rejoin whose brief adds a package row
- **WHEN** a queued cut's entry holds `left-pad 1.3.0`, its brief's `## Dependencies` also lists `right-pad ^2` for its slug,
  and `conduct.py rejoin <id>` runs with no `--yes`, after a fix on disk and no re-plan
- **THEN** it exits 1 naming `right-pad ^2` and `conduct.py rejoin <id> --yes <hash>`, the entry holds `left-pad 1.3.0`
  alone and keeps its halt, and no run is asked to take the cut
- **AND WHEN** `conduct.py rejoin <id> --yes <hash>` runs with that hash
- **THEN** the entry holds `left-pad 1.3.0` and `right-pad ^2`, its halt cleared, and the run takes the cut back

#### Scenario: A failed check on disk
- **WHEN** a cut halts on a dirty tree, a missing models file, a kept worktree or a worker's exit
- **THEN** its line names no brief, and the closing line names `a fix`

### Requirement: A rescue decides by the version's switch

A version's models file MAY say `decide = "recommended"` at its top, before its tables: the **switch**, which the cut writes
from the brief. `conduct.py` SHALL read it once a run, with the version's plan, and pass it to the rescue as `decide=recommended`.
Under the switch, `skills/mf-rescue/SKILL.md` SHALL take the fix a card or the plan itself proposes as its own decision, at a build
halt and an `amend needed` halt: it MAY edit `proposal.md` and `design.md`'s `## Decisions` besides `tasks.md` and
`design.md`'s prose, and its commit SHALL carry a `Decided-by: rescue` trailer. It SHALL never edit the spec delta, code or a
test, take a security card of `critical` or `high` severity, approve a gate makefile, settle an integrate conflict, release,
merge or push, or answer a run-wide halt. `conduct.py` SHALL take an amend that touches `proposal.md` or changes `design.md`'s
`## Decisions` section only under the switch and with that trailer, logging `rescue — <id>: decided · <sub-task> · <commit>`;
without the switch it SHALL refuse it, naming the decision. Lines of the form `Fix note (<YYYY-MM-DD>, <card id>): <text>` that
end a `### D<n>` entry, added or edited, SHALL be no change to that section; any other edit of the entry SHALL be one, each run of
whitespace read as one space, so a re-indented or re-wrapped line is no change and a reworded one is. The
run's closing line, and its `done` line, SHALL name
` · decided <ids>` when a rescue decided, `report` SHALL print a line for each decision, and the run's metrics SHALL count them as `rescues-decided`.

#### Scenario: A decided amend
- **WHEN** a version's models file says `decide = "recommended"`, and its rescue at `amend needed` commits an edit to a row of
  `design.md`'s `## Decisions` with `Decided-by: rescue`
- **THEN** the run takes it, logs `rescue — <id>: decided`, the version converges again, and `report` and the closing line name it

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue commits the same amend
- **THEN** the run refuses it, naming the decision, and the version stays halted

#### Scenario: An amend that appends a fix note
- **WHEN** the models file has no `decide`, and the rescue's amend appends a `Fix note (…)` line as the last line of D2's entry
- **THEN** the run takes it as an amend that decided nothing
- **AND WHEN** the amend also edits a line of D2's own words
- **THEN** the run refuses it, naming the decision

#### Scenario: A dedented code block
- **WHEN** the models file has no `decide`, and the rescue's amend dedents a code block inside D4's entry and changes no word
- **THEN** the run takes it as an amend that decided nothing
- **AND WHEN** the amend also changes a word of that entry
- **THEN** the run refuses it, naming the decision

#### Scenario: A worker writes the switch
- **WHEN** a worker adds `decide = "recommended"` to the models file during the run
- **THEN** no rescue of that run decides for that version

### Requirement: A plan check holds the plan to the built tree

`skills/mf-converge/scripts/plan_check.py --change <id> --base <rev>` SHALL exit 1, printing one `plan: ` line per problem,
when: the command of a ticked sub-task's `Verify:`, run again as argv with no shell from the repository root, exits non-zero,
save a search whose `Verify:` says `prints nothing` or `` prints `0` ``, which passes on exit 1 printing nothing, or `0` alone
for `` prints `0` ``; that command exits 0 printing anything where its `Verify:` says it `prints nothing`, or printing other
than the number alone where it says it `` prints `<N>` `` or `` reports `<N>` ``; a
`- [ ] N.M` box stands unticked under a ticked `## Progress` phase; a name the diff from the merge base of `<rev>` and `HEAD`
removes — a Python `def` or `class` name, or an upper-case module-level name, that nothing outside `openspec/` names at
`HEAD`, or the base name of a file the diff deletes — is still named, as a word, on a line of `openspec/specs/` or of the
change directory outside `tasks.md` and `design.md`'s `## Tests` section, that line holding no word of removal and, in
`openspec/specs/<capability>/spec.md`, standing in no requirement the change's `specs/<capability>/spec.md` lists under
`## REMOVED Requirements`; a `def test_`
name under `tests/` at the merge base is gone at `HEAD` and `design.md`'s `## Tests` section does not name it; or a sub-task
marked `**CORPUS**` names a case `scripts/corpus.toml` does not hold. It SHALL NOT run again a `**HALT CHECK**` sub-task's
command, a command of a `**HUMAN` phase, or a command naming `plan_check.py`, and SHALL run no command with a shell. It SHALL
exit 0 printing `plan: clean` when none holds, and 2 when it cannot read `tasks.md`, the base or git.

It SHALL read a `Verify:`'s spans as follows: once an output verb — `prints`, `exits` and the like — follows a command, each later
span is output, never a command, until a `then`, a `;` or the sentence's end. A command whose `Verify:` says it
`` exits `<N>` `` SHALL pass only on exit `<N>`, and on the output the `Verify:` says; the search that passes on exit 1 is the one
whose `Verify:` names no exit. It SHALL run each command without `VIRTUAL_ENV` in its environment, stderr kept in the output it
compares. `skills/mf-cut-change/scripts/verify_check.py` SHALL read a `Verify:`'s commands through this script's parser, loaded
from it, and keep no parser of its own.

It SHALL run each distinct command once a check, whatever the number of sub-tasks that name it, and hold the one result to each
sub-task's own words. It SHALL run the commands side by side, one slot for each core the machine has, and print the lines in
task order, then command order, whatever order they finish in: a `pytest` with `-n` takes every slot and runs alone, a `make`
runs one at a time, and every `pytest` starts with `-p no:cacheprovider` in its `PYTEST_ADDOPTS`. A command past 600 s SHALL
lose its whole process group and print `plan: <sub-task> — `<command>` timed out`; ended by SIGTERM, the check SHALL end the
process group of each command then running. A `pytest` command — one whose argv starts `pytest`, `uv run pytest` or `python -m pytest` — whose `Verify:` says nothing of its
output beyond that it exits 0, and whose words after its pytest prefix are only `-q`, `-v`, `-x` or `-s` flags and test paths
and `::` nodes that exist, SHALL pass unrun when `gate_run.py` holds a green record for the same tree and the same dry run of
`make -n gate` and the command's own collection finds a test; one that says what it prints, selects with `-k`, `-m` or `--deselect`, or carries another option still runs. On a settled tree the check SHALL keep each finished result — its exit and output — in
`.minions/plan-check/<tree>/`, named by the command, `HEAD` and every ref, and SHALL read it again on the same tree while
`HEAD` and every ref stand, whatever the command's words; a timed-out command SHALL be kept by no one, and an unsettled tree
SHALL keep and read none. With
`--only <sub-task ids>` it SHALL run the `Verify:` commands of those sub-tasks alone, ticked or not, with the same skips, print
only their lines and check nothing else.

`skills/mf-build/SKILL.md` SHALL run it at the build's close, after the metrics and before `build.done`, in the foreground within
600 s, and SHALL halt on any other exit than 0, writing no `build.done`. Converge's fixer SHALL run it in the foreground after
its gate and before its commit, clearing each problem as a blocking card of the same pass, or setting it `wontfix` naming the
amend; converge's Step 7 SHALL run it after `gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any
verify worker, counting no round; a line the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the
run `amend needed — plan check: <subjects>`, naming each line's sub-task, `path:line` or test name and never the command it
quotes. `skills/mf-rescue/SKILL.md` SHALL take that halt as a fix of the lines `plan_check.py` prints, in `tasks.md` and
`design.md`'s prose.

#### Scenario: A ticked check that no longer holds
- **WHEN** at the build's close a ticked sub-task's `Verify:` command exits 1
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command, and the build halts with no `build.done`

#### Scenario: A ticked check that exits 0 with other output
- **WHEN** a ticked sub-task's `Verify:` says a search prints nothing and the search finds a match, or says `printf 1` prints
  `2`
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command
- **AND WHEN** its `Verify:` says `printf 1` prints `1`, or says a `grep -c` that finds nothing prints `0`
- **THEN** that check halts nothing

#### Scenario: An exit the Verify: names
- **WHEN** a ticked `Verify:` says that `false` exits `1`
- **THEN** `plan_check.py` prints no line for it
- **AND WHEN** a ticked `Verify:` says that `true` exits `1`, or says that `false` exits nothing
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command

#### Scenario: Spans after an output verb
- **WHEN** a ticked `Verify:` says that `printf 1` prints `1`, then `printf 2` prints `2`
- **THEN** both commands run
- **AND WHEN** it says that a search lists `a.py`, `b.py` and `c.py`
- **THEN** the search is the one command, and no file name is run

#### Scenario: A command under a set VIRTUAL_ENV
- **WHEN** `VIRTUAL_ENV` is set in the environment of `plan_check.py`, and a ticked `Verify:` runs `printenv VIRTUAL_ENV`
- **THEN** the command prints nothing: it never saw the variable

#### Scenario: An unticked box under a finished phase
- **WHEN** `## Progress` ticks phase 2 and sub-task `2.3` stands unticked
- **THEN** `plan_check.py` exits 1, naming `2.3`

#### Scenario: A removed name still in the plan
- **WHEN** the diff removes `def _fence`, nothing outside `openspec/` names `_fence` at `HEAD`, and a `design.md` line names it
  with no word of removal
- **THEN** `plan_check.py` exits 1, naming that line
- **AND WHEN** the line says the change deletes `_fence`
- **THEN** that line halts nothing

#### Scenario: A removed name in a requirement the delta removes
- **WHEN** the diff removes `LIMIT`, and a line of `openspec/specs/cap/spec.md` names it with no word of removal
- **THEN** `plan_check.py` exits 1, naming that line
- **AND WHEN** the line stands in a requirement the change's `specs/cap/spec.md` lists under `## REMOVED Requirements`
- **THEN** that line halts nothing, and the same name in the next requirement, which the delta keeps, still exits 1

#### Scenario: A test the base had
- **WHEN** `def test_old` stands under `tests/` at the merge base and nowhere at `HEAD`
- **THEN** `plan_check.py` exits 1, naming `test_old`
- **AND WHEN** `design.md`'s `## Tests` section names `test_old`
- **THEN** it halts nothing

#### Scenario: A clean plan
- **WHEN** every ticked `Verify:` passes, every box under a ticked phase is ticked, and no removed name or base test is missing
- **THEN** `plan_check.py` exits 0 and prints `plan: clean`

#### Scenario: A fix that breaks a ticked check
- **WHEN** converge's fixer commits a fix and Step 7's `plan_check.py` exits 1
- **THEN** the conductor sends its lines to the fix station before any verify worker, and the round count stays
- **AND WHEN** the next Step 7's `plan_check.py` prints a line that fix pass was sent, naming sub-task `3.2`
- **THEN** converge halts `amend needed — plan check: 3.2`, and the rescue amends `tasks.md` or `design.md` to clear it

#### Scenario: A command named twice runs once
- **WHEN** sub-tasks `1.1` and `1.2` name the same command, `1.1` saying it prints `1` and `1.2` saying it prints nothing, and it prints `1`
- **THEN** the command runs once, and `plan_check.py` prints a line for `1.2` alone

#### Scenario: A bare pytest on a green gate
- **WHEN** a ticked `Verify:` says a `pytest` command exits 0, and `gate_run.py` holds a green record for the same tree and the same dry run
- **THEN** the command does not run, and `plan_check.py` prints no line for it
- **AND WHEN** the `Verify:` says the command prints `3`, or the tree or the dry run differs from the record's, or the command's collection finds no test, or a test path lies outside the repo's `testpaths`
- **THEN** the command runs
- **AND WHEN** the command selects with `-k`, or names a test file or node that does not exist
- **THEN** the command runs, and a selection that collects no test fails the check

#### Scenario: A result kept by tree
- **WHEN** `plan_check.py` runs a command on a settled tree and runs again on the same tree
- **THEN** the second check reads the kept result and does not run the command
- **AND WHEN** the tree is unsettled, or the command is another, or `HEAD` is another commit
- **THEN** the command runs
- **AND WHEN** another branch moves while `HEAD` and the tree stand, and the command reads it through a shell or a script it
  names, as `sh -c 'git diff --quiet other HEAD'` does
- **THEN** the command runs, and its new exit is judged

#### Scenario: Commands run side by side
- **WHEN** two commands each wait for a file the other writes, and a third fails after the first
- **THEN** both finish, and the failure lines print in task order, whatever order the commands finished in
- **AND** a `pytest` with `-n` starts only when no other command runs, and a `make` starts only when no other `make` runs

#### Scenario: A timed-out command's group
- **WHEN** a command starts a child, outlives the 600 s limit, and `plan_check.py` kills it
- **THEN** the child is gone too, and the line says the command timed out

#### Scenario: Only the named sub-tasks
- **WHEN** `plan_check.py --only 1.1 2.3` runs and `1.1` is unticked and `2.3` is a `**HALT CHECK**`
- **THEN** it runs the command of `1.1` alone and prints a `plan: ` line for it only if it fails

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
whose id is outside `R<n>` and `S<n>`, or whose verdict is `changes-requested` with no open card, SHALL be malformed. A card is
open until its status is `verified` or `accepted`; a role whose verdict is `changes-requested` while no open card blocks SHALL
count as clean, its file's verdict written `clean` and its open cards left to the pickup and the debt. `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py`
and `skip_stub.py` SHALL read a findings file's cards and frontmatter through `skills/mflib/findings.py`, a card's title a line that
starts `- **<id> — ` with an id holding no `*`, so a bullet that closes its bold after its first word, as `- **stale-claim** — ran.`,
is no card; `skills/mflib/debtfile.py` SHALL read a debt card's title, a line that starts `- **<digits>·<id> — ` with an id holding no `*`, and `debt_match.py` and `cut_context.py` SHALL read it through the module. The status log's events and their text
SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `replay` exiting 2 SHALL send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red, a security card and a debt the freeze may not read SHALL still halt.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: Changes requested with nits alone
- **WHEN** a checker's findings file says `changes-requested` and holds open cards, none of a blocking grade
- **THEN** the role counts as clean, its file reads `verdict: clean`, the pickup takes its small and drift cards, and the version converges with no halt

#### Scenario: Changes requested with no card
- **WHEN** a checker's findings file says `changes-requested` and holds no open card
- **THEN** one rewrite worker is started for it, as for a file that lacks `passes`, and the file reads `verdict: clean` after, the
  rewrite having fixed it or not

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

#### Scenario: A debt the freeze may not read
- **WHEN** `.minions/debt.md` is a link at a freeze
- **THEN** converge halts naming `debt_match.py`, and writes no empty `debt-cards.md`

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check

