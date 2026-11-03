# Capability: sdd

## Purpose

The rules the `mf-*` skills hold. A scan proves the structure a reader cannot check by eye; review holds
the rest (D42).

## Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **WHEN** `mf-build`, `mf-converge` or `mf-release` is about to run the gate for the first time in a session
- **THEN** it prints the output of `make -n gate` first
- **AND** it runs `make gate` from the repository root, never a command it found instead

#### Scenario: The repository has no runnable gate
- **WHEN** the root `Makefile` is missing, has no `gate` target, or its `gate` target prints no command under
  `make -n`
- **THEN** the station halts, naming the root `Makefile`

### Requirement: The cut and the build share one input contract

`skills/mf-build/SKILL.md` SHALL own the input contract: a `## Input contract` section whose table rows are
the items a change must meet, one per row, the first cell holding the item's id in bold (`**I1**`).
`skills/mf-cut-change/SKILL.md` SHALL carry a `## Input contract` section with a row for the same ids. The two
id sets SHALL be equal, non-empty, and numbered from `I1` with no gap.

#### Scenario: The two skills carry the same contract ids
- **WHEN** the ids are read from the first cell of each table row in the `## Input contract` section of both
  skills
- **THEN** the two sets are equal and non-empty
- **AND** they run from `I1` upward with no number missing

### Requirement: A release may skip the check loop, and says so

`skills/mf-release/SKILL.md` SHALL release a change for which no findings file and no diff patch exist, and SHALL
state the skip as the line `converge: skipped — no findings files`. It SHALL halt when the diff patch exists
without a findings file, and when one findings file exists without the other. It SHALL NOT carry the rule that a
missing findings file is not clean; that rule SHALL stay in `skills/mf-converge/SKILL.md`, which judges its own
stations by it.

#### Scenario: The release names the skip, and the missing-file rule lives in converge only
- **WHEN** `mf-release` finds no findings file and no diff patch for the change
- **THEN** it releases, and states the skip as the line `converge: skipped — no findings files`
- **AND** it does not judge a missing findings file itself; `mf-converge` holds that rule for its own stations

#### Scenario: The release names both halts
- **WHEN** `mf-release` finds the diff patch without a findings file, or one findings file without the other
- **THEN** it halts, naming what it found

### Requirement: The build and the cut share one list of prose rules

`skills/mf-build/SKILL.md` SHALL own the prose rules: a `## Prose rules` section whose table rows are the rules,
one per row, the first cell holding the rule's id in bold (`**P1**`). `skills/mf-cut-change/SKILL.md` SHALL
carry a `## Prose rules` section with a row for the same ids. The two id sets SHALL be equal, non-empty, and
numbered from `P1` with no gap.

#### Scenario: The two skills carry the same prose-rule ids
- **WHEN** the ids are read from the first cell of each table row in the `## Prose rules` section of both
  skills
- **THEN** the two sets are equal and non-empty
- **AND** they run from `P1` upward with no number missing

### Requirement: Converge keeps deferred work in one repository backlog

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/backlog.md`, under a heading for its change. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, fix them, and verify them in a normal
round. It SHALL NOT name a per-version backlog file. It SHALL delete a backlog card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and verifies them in a normal round

#### Scenario: Converge writes the backlog
- **WHEN** the loop ends clean with non-blocking cards still not `verified`
- **THEN** converge writes each one whose **Still true?** check still shows the defect, and whose id is not yet in
  the backlog, to `.minions/backlog.md` under its change's heading, and to no per-version file
- **AND** it names each moot card, whose check shows the defect gone, in its report
- **AND** it deletes an older card only when a verified repeat of it fixed the defect and its **Still true?**
  check shows the defect gone

### Requirement: The release does not read the backlog

`skills/mf-release/SKILL.md` SHALL NOT hold a release on deferred work. It SHALL name no per-version backlog file.
A paydown change lists the card ids it closes under the `backlog:` key of its `proposal.md` frontmatter:
`skills/mf-cut-change/SKILL.md` SHALL write that key, and `mf-release` SHALL delete exactly those cards from
`.minions/backlog.md` after the fold.

#### Scenario: The release names no per-version backlog, and the paydown key is shared
- **WHEN** `mf-release` runs while `.minions/backlog.md` holds open cards the change does not list
- **THEN** it releases without reading or holding on them

#### Scenario: A paydown change is released
- **WHEN** the change's `proposal.md` lists card ids under `backlog:`
- **THEN** `mf-release` deletes exactly those cards from `.minions/backlog.md` after the fold

### Requirement: The card is defined in converge alone

`skills/mf-converge/SKILL.md` SHALL own the card: a `## The card` section whose table rows are the card's fields,
one per row, the first cell holding the field's label in bold (`**Why it's a problem**`). No other shipped skill
SHALL carry a `## The card` section.

#### Scenario: Only converge carries the card
- **WHEN** every `skills/*/SKILL.md` is scanned for a `## The card` section
- **THEN** `mf-converge` carries one, with at least one label
- **AND** no other skill carries one

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, with no
pickup. When the selection is merges only, the run SHALL count its own rounds: one judge round and at most one fix
round, then a halt, with `round:` carrying on past three. Any other selection SHALL count against the cap of three.
When that range holds a merge of the default branch, the round SHALL judge the merge by its
`git show --remerge-diff`, and the range's other commits by their own diff, not the changes the merge brought in.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** converge ran and `HEAD` differs from the `head:` of either findings file
- **THEN** `mf-release` halts, and names `/mf-converge` and its catch-up round as the next act

#### Scenario: Converge catches up
- **WHEN** both findings files are clean and their `head:` is an ancestor of `HEAD` but not `HEAD`
- **THEN** `mf-converge` runs one verify round over `head..HEAD`, with no pickup

#### Scenario: The catch-up round judges a merge-in by what the merge decided
- **WHEN** the range `head..HEAD` holds a merge of the default branch whose conflicts were resolved by hand
- **THEN** the round's patch holds that merge's remerge-diff, not the default branch's changes
- **AND** a merge with no conflicts adds nothing to read, and the gate judges the combined tree

#### Scenario: A catch-up over merges only has its own count
- **WHEN** the last judged round is 3 and the selection is the integrate merge alone
- **THEN** `mf-converge` judges it as round 4, with no halt at the cap
- **AND WHEN** a blocking finding is still open after its one fix round
- **THEN** it halts with `cap reached`, and the stage reads `converge-halted`

#### Scenario: A late commit at the cap halts
- **WHEN** the last judged round is 3 and the selection holds a commit that is not a merge
- **THEN** `mf-converge` halts, naming the revert and the re-converge from round 1

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/SKILL.md` SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security, save a route in a class the threat model's *Out of scope* accepts by name, which is carded and does
not block, anchors included. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **WHEN** review or security finds data loss or an irreversible delete, spend, exposure of personal data or
  secrets, or silent wrong output
- **THEN** review grades it `blocking` and security at least `high`, so the loop fixes it

#### Scenario: Prose the code contradicts
- **WHEN** review finds docs, comments, README or CHANGELOG text the code contradicts
- **THEN** it grades the finding `drift`, which does not block
- **AND** a spec scenario the code contradicts stays `blocking`

#### Scenario: A route in the accepted class
- **WHEN** security finds a route in a class the threat model's *Out of scope* accepts by name, with an anchored harm
- **THEN** it cards the route, and the card does not block
- **AND WHEN** the route is in no accepted class
- **THEN** the anchor blocks as before

### Requirement: A repeated finding escalates

Each station SHALL read `.minions/backlog.md`. A finding that repeats a backlog card SHALL name that card's id in its
**Related** field as `repeat of <id>`, and SHALL go up one level: security by one step, a review `nit` or `drift` to
`blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** a station's finding describes a defect already carded in `.minions/backlog.md`
- **THEN** its **Related** field names `repeat of <id>`
- **AND** it goes up one level: security by one step, a review `nit` or `drift` to `blocking`

### Requirement: Review searches for stale claims

The review station SHALL run a **stale-claim pass** after its sections: every path, symbol, verb, route or count the
diff renames, deletes or changes is searched across the rest of the tree, and each mention the change made false is
carded as `drift`. The station SHALL say in its Summary that the pass ran, and `skills/mf-converge/SKILL.md` SHALL
check that it did.

#### Scenario: Converge names the stale-claim pass
- **WHEN** the frozen diff renames a path that a file outside the diff still names
- **THEN** review cards that mention as `drift`, and its Summary says the stale-claim pass ran

#### Scenario: A review without the pass
- **WHEN** a review findings file's Summary does not say the stale-claim pass ran
- **THEN** `mf-converge` treats it as a scope failure and halts

### Requirement: A fix's test fails without the fix

For a card whose fix size includes `a test`, the fix station SHALL paste the new or extended test's failing run from
before the fix into the card's **Status** note; an extended test's run is the existing test with the new step added.
The verify pass SHALL reopen the card when that run is missing, or when the test does not exercise the card's
**When you'd hit it** scenario. Fixes to docs only are exempt.

#### Scenario: Converge names the red run and the verifier's check
- **WHEN** the fix station fixes a card whose fix size includes `a test`
- **THEN** it pastes the new or extended test's failing run from before the fix into the card's **Status** note

#### Scenario: The red run is missing or misses the scenario
- **WHEN** the verify pass finds no red run in the note, or a test that does not exercise the card's
  **When you'd hit it** scenario
- **THEN** it reopens the card

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `backlog`, `halt` and `done`, and a
run SHALL end on `halt` or `done`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, its time taken from `date`
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

### Requirement: A skill infers the one active change

`skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL take `change-id`
from their parameter when one is given. When none is given, each SHALL take the candidates from
`git ls-files openspec/changes/`, without `archive/`: no candidate SHALL halt with `no active change`, several SHALL
halt listing them, and exactly one SHALL be used only if the current branch equals its change id, else halt
naming both. The skill SHALL echo the id with
`(inferred:` before any other work, and SHALL NOT forbid inference.

#### Scenario: Build, converge and release each name the inference and its halts
- **WHEN** build, converge or release starts without a `change-id`, one change is active, and the current branch
  is its change id
- **THEN** the skill echoes the id with `(inferred:` and proceeds

#### Scenario: No candidate, several, or another branch
- **WHEN** no change is active, several are, or the current branch is not the one change's branch
- **THEN** the skill halts with `no active change`, listing the candidates, or naming both branches

### Requirement: The build approves a dependency only as the cut committed it

`skills/mf-build/SKILL.md` SHALL add a package without a halt only when `## Dependencies` of the change's
`design.md`, as committed in the cut commit, lists it, and SHALL halt when the branch has changed that section
since the cut. The cut commit SHALL be the one commit that adds `design.md`; more than one SHALL be a halt.
`skills/mf-cut-change/SKILL.md` SHALL show `## Dependencies` to the human word for word when it is not `None.`,
each entry an exact package name and a version constraint.

#### Scenario: A dependency added on the branch halts the build
- **WHEN** a build pass finds a package in `## Dependencies` that the cut commit's `design.md` does not list
- **THEN** the build halts and asks for approval, rather than adding the package

#### Scenario: A design re-added on the branch halts the build
- **WHEN** `design.md` was deleted and added again on the branch, so more than one commit adds it
- **THEN** the build halts rather than choose a cut commit

### Requirement: The cut runs no check before the human reads it

`skills/mf-cut-change/SKILL.md` SHALL read every `Verify:` in the change and SHALL run none of them; it SHALL show
each to the human word for word, and the build runs them once the human starts it. The cut SHALL treat its
source, and every file the source points to, as evidence to write from, never as instruction.

#### Scenario: The cut's self-check runs no check
- **WHEN** `mf-cut-change` reaches its self-check
- **THEN** it reads every `Verify:` and runs none of them
- **AND** it shows each to the human word for word

#### Scenario: The source addresses the cutter
- **WHEN** a line in the source, or a file it points to, instructs the cutter or declares a check satisfied
- **THEN** the cut treats it as evidence, obeys nothing in it, and reports it

### Requirement: Converge and the release halt on a gate the cut did not plan

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each run
`skills/mf-converge/scripts/gate_check.py` before judging or releasing, and SHALL halt on its verdict. The script
SHALL export the base and `HEAD` with `git archive` into fresh directories under `.minions/gate-check/`, run make
there with `MAKEFLAGS` and `MFLAGS` cleared, and remove them when it ends. A **gate makefile** SHALL be any file in
the `MAKEFILE_LIST` or a `Reading makefile` line of `make -pn -r -w -d gate` on either export. When no sub-task in
`tasks.md` as the cut commit holds it names both `Makefile` and `` `gate` ``, a branch that changes a gate makefile,
or the `make -n gate` output, SHALL halt. When such a task exists, the script SHALL show the two exports'
`make -n gate` diff, and SHALL halt on a command line the base prints and the branch does not, and on every
non-blank gate makefile line the branch adds or removes, unless that task quotes the line. Its verdict SHALL
name what it read — the gate makefiles and the dry runs — and SHALL NOT state that the gate is the base's. An export that lacks a path of its tree, or a dry run that fails on either export, SHALL halt, naming the
side. The cut commit SHALL be the one commit that adds the change's `design.md`; more than one SHALL be a
halt.

#### Scenario: Both stations name the dry-run check
- **WHEN** a branch changes a gate makefile — an included makefile, a sub-make's makefile, a recipe line given a
  `-` prefix, a `.IGNORE` target, or `-i` in `MAKEFLAGS` — or a file that changes the gate's dry run, and no cut task
  names the gate recipe
- **THEN** `mf-converge` halts before judging, and `mf-release` before releasing

#### Scenario: A planned gate change drops a command
- **WHEN** a cut task names the gate recipe, and the base's dry run prints a command line the branch's does not
- **THEN** each station shows the two dry runs' diff and halts, unless that task quotes the line

#### Scenario: A planned change adds a line the task does not quote
- **WHEN** a cut task names the gate recipe, and the branch adds or removes a gate makefile line the task does not
  quote — a removed `SHELL := /bin/bash -o pipefail`; an added `-` recipe prefix, a `.IGNORE` target, a `SHELL` assignment or `-i` in `MAKEFLAGS`, in any form: a continued rule
  line, `define`, a computed name, `$(eval)`
- **THEN** each station halts, naming the line

#### Scenario: The base's gate reads a file the export lacks
- **WHEN** either export lacks a path of its tree — an `export-ignore` path — or `make -pn -r -w -d gate` or
  `make -n gate` fails in it — an included `.env`
- **THEN** each station halts, naming the side and the failure, and compares nothing in the working tree

### Requirement: No station deletes a findings file or the diff patch

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each forbid deleting, moving, renaming or
emptying a findings file or the diff patch; clearing them SHALL be the human's act.

#### Scenario: Both stations carry the rule
- **WHEN** `mf-converge` or `mf-release` ends, clean or on a halt
- **THEN** every findings file and the diff patch are still at their paths, unmoved and not emptied

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md`, `README.md`,
`CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and `docs/decisions.md`. A template's target path SHALL
be its path under `templates/` without the `.tmpl` suffix. The `Makefile` template's `gate` recipe SHALL run
`openspec validate --all --strict --no-interactive`.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and
  `docs/decisions.md` have templates

#### Scenario: The gate template validates the specs
- **WHEN** the `Makefile` template is read
- **THEN** it names `openspec validate --all --strict --no-interactive`

### Requirement: Every station closes in a few sentences and names the next act

`skills/mf-bootstrap/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-build/SKILL.md`,
`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each close a finished run with at most three
sentences — what happened, the gate's exit code, and anything the human must act on — and then a last line naming
the next act after `Next:`. A halt SHALL be reported in full, except a HUMAN phase's halt in `mf-build`, which is
its checklist.

#### Scenario: Each skill's report step carries the close-out rule
- **WHEN** bootstrap, cut, build, converge or release finishes a run
- **THEN** it reports in at most three sentences — what happened, the gate's exit code, and anything the human
  must act on
- **AND** its last line names the next act after `Next:`

#### Scenario: A station halts
- **WHEN** a station halts
- **THEN** it reports the halt in full, except `mf-build`'s halt on a HUMAN phase, which is its checklist

### Requirement: The cut commits without waiting, unless it adds a dependency

`skills/mf-cut-change/SKILL.md` SHALL commit the change once its self-check passes, without waiting for the human.
It SHALL wait for the human's OK before the commit only when `## Dependencies` is not `None.`, or when a
self-check item cannot be met. An edit after the commit SHALL be a further commit on the branch.

#### Scenario: The cut's show step commits without waiting
- **WHEN** the self-check passes and `## Dependencies` is `None.`
- **THEN** `mf-cut-change` shows the change and commits without waiting

#### Scenario: A dependency, or an unmet item
- **WHEN** `## Dependencies` is not `None.`, or a self-check item cannot be met
- **THEN** the cut waits for the human's OK before committing

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL halt before it folds, archives, commits or tags when the default branch is not an
ancestor of `HEAD`, naming the merge-in: `/mf-integrate`, then converge's catch-up round when converge ran, then the release
again. The default branch SHALL be the one `git symbolic-ref --short
refs/remotes/origin/HEAD` names after `origin/`, or `main`. It SHALL, after the tag, ask the person once whether to
merge and push. Given `merge=yes`, it SHALL NOT ask: `merge=yes` is the yes, given once by the person who started
`mf-ship`; and it SHALL halt before the merge when Step 2 flagged a hand-edit. When the release runs in a linked
worktree other than the primary, that one ask SHALL name the
worktree and the ignored paths it holds, listed by name without reading file contents. On yes it SHALL halt when the
default branch is not an ancestor of the branch, naming the person's
recovery — the tag deleted and the release commit reset, by the person — then merge with `--no-ff` in the worktree
that holds the default branch, halting when that worktree's tree is not clean, check that the merged tree equals the
branch's, and push the default branch and the tag to `origin`, except under `merge=yes`, where `conduct.py` pushes. After the merge it SHALL remove the worktree the ask
named, without `--force`, keeping its branch, except under `merge=yes`, where `conduct.py` removes it. A listing that fails SHALL be named in the ask, and the worktree
retained. A worktree that refuses removal is reported, not forced. Its close-out SHALL name the worktree removed,
kept or refused. It SHALL never force a push, never push
the version branch, and SHALL merge without pushing when there is no `origin`. On anything but yes it SHALL print
the commands and stop.

#### Scenario: The release names the merge and its guards
- **WHEN** the tag is made and the person answers yes to `Merge <branch> into <default-branch> and push?`
- **THEN** `mf-release` halts if the default branch is not an ancestor of the branch, merges with `--no-ff`,
  checks the merged tree equals the branch's, and pushes the default branch and the tag without `--force`

#### Scenario: The person says anything else, or there is no origin
- **WHEN** the answer is not yes
- **THEN** the release prints the merge and push commands and stops
- **AND WHEN** the answer is yes and there is no `origin`
- **THEN** it merges and does not push

#### Scenario: The base moved before the release
- **WHEN** the default branch has a commit the version branch lacks when the release starts
- **THEN** it halts before the fold, the commit and the tag, naming `/mf-integrate`, the catch-up round and the release
  again

#### Scenario: A release run in a linked worktree
- **WHEN** the version branch is checked out in a linked worktree and the primary holds the default branch
- **THEN** the release merges in the primary, never switching branches in the version's worktree
- **AND** it removes the version's worktree after the merge, the branch kept

#### Scenario: A version's worktree contains ignored local files
- **WHEN** the version's worktree holds ignored paths, such as `.venv/` and the test caches
- **THEN** the ask names each path without reading its contents, and on yes the release removes the worktree with
  them, without `--force`
- **AND WHEN** the listing fails
- **THEN** the ask names the failure, and the release retains the worktree

#### Scenario: The conductor gives the yes
- **WHEN** the release is run with `merge=yes` and Step 2 flagged nothing
- **THEN** it asks nothing, merges as on a yes, and `conduct.py` pushes and removes the worktree
- **AND WHEN** Step 2 flagged a hand-edit
- **THEN** it halts after the tag and before the merge, naming the flagged prose

#### Scenario: A release under mf-ship leaves its worktree to the conductor
- **WHEN** a release under `merge=yes` merges
- **THEN** it removes no worktree, and its close-out says `conduct.py` removes it

### Requirement: A HUMAN phase is handed over as a checklist of commands

The `I14` row of the `## Input contract` in `skills/mf-cut-change/SKILL.md` and `skills/mf-build/SKILL.md` SHALL
require a HUMAN phase's sub-tasks to be exact commands with real values. `skills/mf-build/SKILL.md` SHALL halt on
an unworked HUMAN phase with a checklist: one line per step, each command in an `sh` block, secrets by env-var
name, the closing checks, and `Next: /mf-build`.

#### Scenario: Both skills require commands, and the build prints them
- **WHEN** `mf-cut-change` writes a phase marked `**HUMAN`
- **THEN** each of its sub-tasks is exact commands with real values, or one line naming a file and its exact text

#### Scenario: The build meets an unworked HUMAN phase
- **WHEN** `mf-build` runs the phase's `Verify:` checks and one fails
- **THEN** it halts with the person's checklist: one line per step, each command in an `sh` block, secrets by
  env-var name, the closing checks, and `Next: /mf-build`

### Requirement: The build owns the rules for tests, and the cut and converge carry them

`skills/mf-build/SKILL.md` SHALL own the rules for tests: a `## Rules for tests` section whose table rows are the
rules, one per row, the first cell holding the rule's id in bold (`**T1**`). `skills/mf-cut-change/SKILL.md` and
`skills/mf-converge/SKILL.md` SHALL each carry a `## Rules for tests` section with a row for the same ids. The id
sets SHALL be equal, non-empty, and numbered from `T1` with no gap.

#### Scenario: The three skills carry the same test-rule ids
- **WHEN** the ids are read from the first cell of each table row in the `## Rules for tests` section of
  `mf-build`, `mf-cut-change` and `mf-converge`
- **THEN** each carrier's set equals `mf-build`'s, and none is empty
- **AND** each runs from `T1` upward with no number missing

### Requirement: A test is deleted or merged only as the design's table names it

`skills/mf-build/SKILL.md` SHALL treat a test deleted or merged as the change's `design.md` `## Tests` table names it
— each removed test mapped to the remaining test that carries its assertions and scenario ids, or to a decision
in force at the base that retires it — as consolidation, not as weakening the gate, and SHALL halt on a deletion outside that table.
`skills/mf-cut-change/SKILL.md` SHALL write that table for every test a change deletes or merges. The fix station
in `skills/mf-converge/SKILL.md` SHALL never delete or merge a test.

#### Scenario: The build names the table, and the fix station never deletes
- **WHEN** a phase deletes a test that `design.md`'s `## Tests` table maps to a decision in force at the base that retires it
- **THEN** `mf-build` treats the deletion as consolidation and does not halt

#### Scenario: A deletion outside the table
- **WHEN** a phase deletes a test the table does not name
- **THEN** `mf-build` halts: the gate would be weakened

#### Scenario: A fix pass meets a test
- **WHEN** the fix station clears a finding
- **THEN** it deletes and merges no test

### Requirement: Review judges test cost and traced coverage

The review station SHALL run a **test-cost pass** after its sections, carding each new end-to-end test that a lower
layer proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When
the freeze removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to
the test that runs it now, or to the decision, in force at the base, that the design's `## Tests` table names as retiring it. A
proof carried by neither SHALL be `blocking`. Each round SHALL run both passes over that round's freeze. The
station SHALL say in its Summary that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** a review findings file's Summary does not say the test-cost pass ran, or the coverage-trace pass ran or
  the freeze removed no test
- **THEN** `mf-converge` treats it as a scope failure and halts

#### Scenario: The freeze removes a test the table retires
- **WHEN** the freeze removes a test that the `## Tests` table maps to a decision in force at the base
- **THEN** the coverage-trace pass accepts the removal and cards nothing for it

#### Scenario: A proof carried by neither
- **WHEN** a removed assertion maps to no remaining test and to no retiring decision
- **THEN** review cards it `blocking`

### Requirement: The release records the gate's time

`skills/mf-release/SKILL.md` SHALL time precondition 1's gate run and SHALL write one `Gate:` line under the new
release heading in `CHANGELOG.md`: that time, CI's latest green run on the default branch read with `gh run list`
or `none`, and the previous release's `Gate:` line's times. Under `merge=yes` the CI part SHALL read `CI not read under
mf-ship`: the sandbox keeps `gh` from its config.

#### Scenario: The release names the line and the CI read
- **WHEN** `mf-release` renames `## [Unreleased]` to the release heading
- **THEN** it writes one `Gate:` line under it: precondition 1's timed run, CI's latest green run on the default
  branch from `gh run list` or `none`, and the previous release's `Gate:` times

#### Scenario: A release under mf-ship
- **WHEN** a release under `merge=yes` writes its `Gate:` line
- **THEN** the CI part reads `CI not read under mf-ship`, never `CI none`

### Requirement: The bootstrap's `AGENTS.md` states the rules for tests

`skills/mf-bootstrap/templates/AGENTS.md.tmpl` SHALL hold a `## Tests` section stating where a test goes, that a
step in an existing test comes before a new one, which engines a test runs on, and that a test is deleted or merged
only as a change's `## Tests` table names it.

#### Scenario: The template has the section
- **WHEN** `skills/mf-bootstrap/templates/AGENTS.md.tmpl` is read
- **THEN** one of its lines is `## Tests`

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards. The template SHALL
link `CODING_STANDARDS.md` and `CONTRIBUTING.md` as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`
as context for designing, building and reviewing; bootstrap SHALL halt when a `CODING_STANDARDS.md`,
`CODE_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md`, `ARCHITECTURE.md` or `docs/decisions.md` already exists.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
Build, and converge for every worker it dispatches, SHALL also read a root `CODING_STANDARDS.md`,
`CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name. A contradiction between those files SHALL
go to the person: review cards it as drift, and the build halts on one that decides its phase's code. No filename
SHALL take precedence over another.
Cut, build, and converge for every worker it dispatches, SHALL read the architecture decisions and the threat model —
the documents `AGENTS.md` names, else `docs/decisions.md`, `ARCHITECTURE.md`, `docs/adr/*.md` and `THREAT_MODEL.md`
when present. The build SHALL halt on a phase that contradicts a decision in force, unless a task of the change
amends that decision.
The root context SHALL explicitly direct reading of the shared principles and decisions rather than rely on
host-specific import syntax.

#### Scenario: A target has the agreed context
- **WHEN** a station starts on a target containing `AGENTS.md`
- **THEN** it reads that context and its mandatory linked context regardless of the host's automatic loader

#### Scenario: A target lacks the agreed context
- **WHEN** cut, build, converge or release starts without root `AGENTS.md`
- **THEN** it halts naming that missing file without substituting another context filename

#### Scenario: A new target is bootstrapped
- **WHEN** bootstrap writes a target with no collisions
- **THEN** it creates `AGENTS.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and
  `docs/decisions.md`, and retains the template's test policy
- **AND** `AGENTS.md` links both standards files as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`

#### Scenario: A standards file already exists
- **WHEN** bootstrap starts in a directory holding `CODE_STANDARDS.md` or `THREAT_MODEL.md`
- **THEN** it halts, naming that file, and writes nothing

#### Scenario: An existing repo has standards its AGENTS.md does not name
- **WHEN** the build starts on a repo whose root holds `CODE_STANDARDS.md` and whose `AGENTS.md` does not name it
- **THEN** the build reads it, and converge hands it to every worker

#### Scenario: A phase contradicts a decision in force
- **WHEN** a phase's tasks would break a decision in the repo's `docs/decisions.md`, and no task amends it
- **THEN** the build halts, naming the decision and the task
- **AND WHEN** a task of the change amends that decision
- **THEN** the build proceeds

### Requirement: Skills install into the shared user directory by default

The installer SHALL default to `~/.agents/skills`, preserve the `SKILLS_DIR` override and retain its existing
symlink, collision-refusal and checkout-specific uninstall behavior. It SHALL leave previous installations alone.

#### Scenario: The operator uses the default destination
- **WHEN** `make install-skills` runs without a destination override
- **THEN** it targets the shared user skills directory

#### Scenario: The operator supplies a destination
- **WHEN** `SKILLS_DIR` names a different destination
- **THEN** installation and uninstallation use that destination with their existing safeguards

### Requirement: Generic passes preserve the station boundaries

`mf-simplify` SHALL edit only the change's own lines, by its angles and closed edit kinds, inside the oracles its
skill names, before independent checking. The build SHALL retain its gate and separate simplify-commit ordering. Review SHALL check correctness, spec, standards, architecture and gate integrity in separate sections,
each citing its source document, including the existing stale-claim, test-cost and coverage-trace passes.

Security SHALL read the target's threat model first, then inspect changed behavior and relevant surrounding
context for concrete vulnerabilities, secrets exposure, unsafe permissions and trust-boundary failures, including
prompt, tool and model-output trust where relevant. A finding SHALL be introduced by the change, unless the
contract's passes or repeat rule name it or it is a contradiction between standards files, carry a concrete scenario
and the offending line quoted, and SHALL NOT be one the reference's do-not-flag list names unless the target's threat
model overrides it. A section whose source document is missing SHALL be marked `inconclusive`, never
read as a pass. Findings SHALL use the existing cards, severity, verdict, verification and release contracts. Review
and security SHALL edit their own findings files, leave code changes to the fix station, and keep findings local
rather than publish external comments.

#### Scenario: A generic pass receives a frozen change
- **WHEN** the station receives the explicit base and head, patch and change artifacts
- **THEN** it reads relevant source context and judges that range without requiring a GitHub remote or review plugin
- **AND** it reports the scope it actually inspected rather than declaring an uninspected change clean

#### Scenario: A generic worker verifies a fix
- **WHEN** fresh review and security workers receive their findings and the fix range
- **THEN** each promotes verified findings or reopens them under the existing contract
- **AND** review receives the design's test table and runs the required review passes

#### Scenario: A section lacks its source document
- **WHEN** the target has no threat model, or one whose sections read `Not written yet:`
- **THEN** the security file's threat-model section is `inconclusive`, its generic classes are still checked, and
  the verdict may still be `clean`

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins, and SHALL record `mode: parallel` or `mode: sequential`. The
station SHALL halt before work requiring an unavailable worker capability, naming that
capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

#### Scenario: A host runs one worker at a time
- **WHEN** converge runs on a host that cannot run workers in parallel
- **THEN** it runs the review worker, then the security worker, over the same frozen head, and the findings files record
  `mode: sequential`

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their role resources: converge's review and security references on every
executor, and `mf-simplify` in the build, whose link SHALL resolve from the build's installed package, not the
target's cwd; a missing target SHALL halt the build, naming it.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package, and the
build's link to `mf-simplify` to a nonempty file in that skill's package.
Missing, empty and escaping targets SHALL fail the gate's resource-integrity check.

#### Scenario: The generic instruction package is incomplete
- **WHEN** a referenced role resource is missing, empty or resolves outside its skill package
- **THEN** the resource-integrity check reports the referring skill and the invalid target

#### Scenario: The package contains valid role resources
- **WHEN** the shipped resource references resolve within their packages to nonempty files
- **THEN** the resource-integrity check passes without treating illustrative change-document links as resources

#### Scenario: The build cannot load mf-simplify
- **WHEN** the build's link to `mf-simplify` finds no file from its installed package
- **THEN** the build halts naming it, and takes no copy of that name from the target

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
It SHALL write the suggestion to `.minions/models/<change-id>.toml`, a table per station, as well as show it, and
SHALL never write it into the change. Authentication and provider configuration SHALL remain the operator's
responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

#### Scenario: The cut records its suggestion
- **WHEN** the cut commits a change
- **THEN** `.minions/models/<change-id>.toml` holds a `build`, a `converge` and a `release` table, each with its
  `model`, and nothing under `openspec/changes/<change-id>/` names a model

### Requirement: Compatibility claims identify their evidence

This migration SHALL include a live Codex smoke of the generic passes with findings on disk and fresh verification
after a fix, plus a hand review of Claude Code's native dispatch. Model calls SHALL stay outside CI.
A host SHALL be described as tested only when an actual run supplies that evidence; other hosts SHALL be
described by the capabilities they require, without a universal model-quality claim.

#### Scenario: A host is documented without a live run
- **WHEN** documentation describes a supported host's capabilities but has no run evidence
- **THEN** it does not label that host tested

#### Scenario: The generic smoke finishes
- **WHEN** the Codex smoke and native dispatch review meet the design's acceptance criteria
- **THEN** the migration records their actual outcomes and retains links to the evidence

### Requirement: A repository opts into metrics with a catalogue

A repository SHALL be measured only when it holds `metrics/catalogue.toml`. Without it, `mf-build` and
`mf-release` SHALL collect nothing, render nothing and check nothing, and each SHALL state `metrics: none — no
catalogue` in its report. No metric SHALL be measured for a repository that declares none.

#### Scenario: A repository without a catalogue
- **WHEN** the build or the release reaches its metrics step in a repository with no `metrics/catalogue.toml`
- **THEN** it writes no data file and no page
- **AND** its report states `metrics: none — no catalogue`

#### Scenario: A repository with a catalogue
- **WHEN** the build or the release reaches its metrics step and `metrics/catalogue.toml` exists
- **THEN** it collects a value, or `unavailable` with a reason, for every metric the catalogue declares

### Requirement: A metric is a Python script the collector runs without a shell

Each `[[metric]]` in `metrics/catalogue.toml` SHALL declare `id`, `title`, `group`, `unit` and `better`
(`lower` or `higher`), MAY declare `watch` and `noise`, and SHALL declare either `script` with `args` or
`source = "station"`. The collector SHALL run a metric's script as `uv run --script <script> <args>` from the
repository root, never through a shell, with a 300-second timeout. A run that exits 0 with a number on its last
stdout line SHALL record that number; any other outcome SHALL record `unavailable` with its reason. A failing
metric SHALL NOT fail the station. A catalogue that does not parse, lacks a required field, repeats an `id`, or
names a `script` that is not a path inside the repository — a URL, an absolute path, a path escaping the root, or
one starting with `-` — SHALL halt the station, naming the entry.

#### Scenario: A metric script prints its value
- **WHEN** a metric's script exits 0 and its last stdout line is a number
- **THEN** the data file records that number for the metric's `id`

#### Scenario: A metric script fails
- **WHEN** a metric's script exits non-zero, prints no number, or runs past its timeout
- **THEN** the data file records `unavailable` with the reason
- **AND** the station carries on with the other metrics

#### Scenario: The catalogue is broken
- **WHEN** the catalogue does not parse, an entry lacks a required field, two entries share an `id`, or a `script`
  is not a path inside the repository or starts with `-`
- **THEN** the station halts, naming the entry

### Requirement: The build collects a draft of the metrics after simplify

When the repository has a catalogue, `skills/mf-build/SKILL.md` SHALL, after its simplify commit, `lean already` or
`nothing kept`, collect the metrics into `.minions/metrics/<change-id>.json` and render
`.minions/metrics/<change-id>.html`, both gitignored. Its close-out SHALL name the page and the count of metrics that crossed their watch in this change or
moved the wrong way. The build SHALL NOT halt on a watch.

#### Scenario: A change crosses a watch
- **WHEN** a metric's value crosses its `watch` in this change
- **THEN** the build's close-out names the page and counts the metric
- **AND** the build stops as it always does, leaving the choice to the person

### Requirement: The release records the shipped metrics in its commit

When the repository has a catalogue, `skills/mf-release/SKILL.md` SHALL, after the version file and before its
final gate, collect the metrics on the release's own tree into `metrics/changes/<change-id>.json`, passing the
gate time of precondition 1, and SHALL stage that file into the release commit. A collector that crashes, rather
than recording a metric `unavailable`, SHALL halt the release.

#### Scenario: A release with a catalogue
- **WHEN** the release reaches its metrics step and the catalogue exists
- **THEN** `metrics/changes/<change-id>.json` is written on the folded, archived tree
- **AND** the final gate judges a tree that holds it, and the release commit contains it

### Requirement: The page classifies each metric against the previous release

The page SHALL compare each metric with the previous release — the tracked data file whose version is the highest
below this change's, or the highest of all for a change with no number yet — and classify it as steady (the change within `noise`), improved or worsened by `better`,
crossed here (the previous value on the good side of `watch`, this one past it), over (both past it), back under,
or new. It SHALL list crossed here, then worsened, then over, then the rest, before the charts. A chart SHALL show
an `unavailable` value as a gap, never as zero. The page SHALL be a self-contained HTML file with inline SVG, and
SHALL be renderable again from any change's data file.

#### Scenario: A metric already over its watch
- **WHEN** a metric was past its `watch` in the previous release and still is
- **THEN** the page classifies it as over, not as crossed here

#### Scenario: A metric with no value
- **WHEN** a metric is `unavailable` in a data file
- **THEN** its chart shows a gap at that version

### Requirement: A data file records where its values came from

Each data file SHALL record the change, its version, the base and the analyzed revisions, `measured_on`,
`mf_version`, `executor` and `model`. `mf_version` SHALL come from the collector's own package, or be `unknown`;
`executor` SHALL be what the station reported, worded as the build's *Executor* reports it; `model` SHALL be the
station's own report, or `unidentified`. None SHALL be guessed from a name.

#### Scenario: The collector runs from a frozen copy
- **WHEN** the collector's package is not inside a git checkout
- **THEN** the data file records `mf_version: unknown`

### Requirement: The plan station reads the target without moving it

`skills/mf-plan/SKILL.md` SHALL read the target repository only at a named commit of its default branch, through
`git show`, `git grep`, `git log`, `git ls-tree` and `git diff`, and SHALL read the working tree only for the
gitignored `.minions/backlog.md`. It SHALL NOT switch, check out, stash, reset, commit, branch or edit in the target,
nor run its gate or a metric collection. A helper it dispatches for facts SHALL be held to the same rule, and SHALL
return conclusions citing `path:line` at that commit.

#### Scenario: A build runs in the same checkout
- **WHEN** `mf-plan` gathers facts while another session builds a change on its version branch in that checkout
- **THEN** the checkout's branch, index and working tree are as they were before
- **AND** every fact cites `path:line` at the named commit of the default branch

### Requirement: The plan station checks the line's rules before its first round

Before its first round, `mf-plan` SHALL report as facts: the backlog cards whose trigger the version fires, proposed
for `backlog:`; a recommendation to pay down first when the backlog holds more than ten open cards; whether
the version's bump fits the repository's rule for a patch; the decisions in force the version touches, naming any overturn; a split
when one diff would be too large for review; re-measured facts when continuing a brief written against an older
commit; and, when the target holds `metrics/catalogue.toml`, the metrics past their watch in the latest tracked data
file.

#### Scenario: A version planned in a repo with metrics
- **WHEN** the target has a catalogue and a tracked data file with a metric past its watch
- **THEN** the first round lists that metric as a fact, read from the data file, with no collection run

#### Scenario: A brief continued against a newer commit
- **WHEN** `from=` names a brief whose facts cite an older commit than the default branch's
- **THEN** the station re-measures those facts before its first round

### Requirement: The plan station writes the brief after every round

`mf-plan` SHALL require `brief=<path>` and SHALL write the brief there after every round, with the sections: a title
naming the version, its form, its depth (`light` or `hard`) and the date; one bold line; `## Facts`, each with
`path:line` at a named commit; `## Decisions`, one row per settled question; `## Phases`; `## Not in this`;
`## Open`, the frontier still to ask; and `## For the cut`, filled when the frontier is empty. A hard brief SHALL end
on a settled table the person confirmed, with `## Open` removed. `from=<brief>` SHALL continue a brief. The station
SHALL NOT write the brief's path into the target.

#### Scenario: A thread ends mid-grilling
- **WHEN** a session ends after some rounds
- **THEN** the brief holds every settled decision and the open frontier
- **AND** a new session with `from=` continues from it

#### Scenario: No brief path
- **WHEN** `mf-plan` is started without `brief=`
- **THEN** it halts and asks for the path

### Requirement: The cut halts on a light brief

`skills/mf-cut-change/SKILL.md` SHALL halt when the `brief` it is given declares the `light` depth in its title, naming
the brief as not yet hard-grilled.

#### Scenario: A light brief given to the cut
- **WHEN** `mf-cut-change` is started with a `brief` whose title says `light`
- **THEN** it halts before its branch, and names `mf-plan` with `depth=hard` as the next act

### Requirement: A cut makes a worktree when the repository declares one

When root `AGENTS.md` declares `Worktrees:` with a path, `skills/mf-cut-change/SKILL.md` SHALL create the version's
branch with `git worktree add -b <change-id> <path>/<change-id> <default-branch>`, the path relative to
the primary checkout, and SHALL write and commit the change directory in that worktree, leaving the primary on the
default branch. When `AGENTS.md` also declares `Workspace setup:` with a command, the cut SHALL run it in the new
worktree, halting on a failure and naming it. A repository that declares no `Worktrees:` SHALL keep the branch
switch in place.

#### Scenario: A repository with worktrees declared
- **WHEN** the cut runs in the primary of a repository whose `AGENTS.md` declares `Worktrees: ../`
- **THEN** the change is committed in `../<change-id>`, a linked worktree on the new branch
- **AND** the primary is still on the default branch, its tree clean

#### Scenario: A repository with no worktrees declared
- **WHEN** `AGENTS.md` declares no `Worktrees:`
- **THEN** the cut switches to the new branch in place, as before

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/backlog.md` only while holding `.minions/backlog.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`backlog.lock` older than ten minutes before its first worker, and log it.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/backlog.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

#### Scenario: A dead worker left the lock
- **WHEN** a run starts and `.minions/backlog.lock` is older than ten minutes
- **THEN** the run removes it and logs the removal before its first worker
- **AND WHEN** the lock is younger
- **THEN** the run leaves it

### Requirement: The plan station checks which versions can run side by side

When the person names versions to run side by side, `skills/mf-plan/SKILL.md` SHALL compare their briefs' `## Facts`
paths and `## Phases` files, and SHALL warn of any pair that touches a file in common, suggesting `after:` when one needs the other's code. It SHALL
propose no order.

#### Scenario: Two versions that touch the same skill
- **WHEN** two briefs both name `skills/mf-release/SKILL.md`
- **THEN** `mf-plan` warns, naming the file, and proposes no order

### Requirement: The integrate station merges the default branch into the next version

`skills/mf-integrate/SKILL.md` SHALL, run in the primary checkout, take the version `change-id` names, or with none the
ready version with the lowest change id among the unmerged branches named by a change id that hold their change or a
release commit. It SHALL halt, naming the version, when the named one is not ready, or when none is: a phase unticked,
converge not clean, or an `after:` id missing from its tree. A named version whose merge is open with its note SHALL be
ready. It SHALL merge the default branch into that version's worktree, run `make gate` there, commit
the merge with the version's `Change:` trailer, and end with `Next: /mf-converge, then /mf-release`, or with
`Next: /mf-ship, in the primary.` for a version with an unticked phase. A red gate SHALL
halt with the merge open and write `.minions/integrate/<change-id>.red`, which the commit deletes. It SHALL NOT
release, tag, push or rebase.

#### Scenario: The next version is ready
- **WHEN** the version has every phase ticked and clean findings files
- **THEN** the station merges the default branch into its worktree, gates the result and commits the merge

#### Scenario: The next version is not ready
- **WHEN** `change-id` names a version with an unticked phase
- **THEN** the station halts, naming that version, and merges nothing

#### Scenario: The lowest open version is not ready, and no id is named
- **WHEN** the lowest-id open version has an unticked phase and a later one is ready
- **THEN** the station takes the later one

#### Scenario: The merged tree fails the gate
- **WHEN** `make gate` fails on the merged tree
- **THEN** the station halts with the merge open, and `.minions/integrate/<change-id>.red` exists

#### Scenario: A settled dependent has no build yet
- **WHEN** `/mf-integrate <change-id>` commits the merge of a version with an unticked phase
- **THEN** its last line is `Next: /mf-ship, in the primary.`

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines, renumber the branch's new decision to the next id free
on the default branch with its citations, and report each MODIFIED or REMOVED requirement title of the branch's delta
that the default branch changed since the branch's base. `.gitattributes` SHALL NOT set `merge=union`.

#### Scenario: Both sides added a decision
- **WHEN** the default branch took `D45` and the branch added its own `D45`
- **THEN** the branch's decision is renumbered `D46`, its citations with it

#### Scenario: Both sides changed a CHANGELOG
- **WHEN** the default branch cut a release section and the branch holds `[Unreleased]` entries
- **THEN** the entries stay above the release section, the blank lines intact

### Requirement: A semantic conflict is handed to the person with the merge open

When the delta check reports a changed requirement or git leaves a conflict the rules do not cover,
`skills/mf-integrate/SKILL.md` SHALL halt with the merge in progress in the version's worktree, write
`.minions/integrate/<change-id>.md` holding both intents and a proposed resolution, and continue from the open
merge on its next run.

#### Scenario: Both versions changed one requirement
- **WHEN** the branch's delta modifies a requirement the default branch also changed since the base
- **THEN** the merge stays open, the note names both changes, and the next run continues from `MERGE_HEAD`

### Requirement: The build's comment rules default to no explanatory comment

`skills/mf-build/SKILL.md` `C1` SHALL forbid an explanatory comment: names, types, structure and tests carry what
code does. `C2` SHALL name the exceptions: a short why or pointer for a constraint code cannot express, a contract
or required docstring, and a tool directive or header. A rule in the repo's coding standards that names a `C` rule
SHALL replace it. The rules SHALL apply to the comments a phase writes or changes and the comments next to them,
never to a whole file unasked.

#### Scenario: A phase writes an explanatory comment
- **WHEN** a phase adds a comment restating what the next line does
- **THEN** `C1` forbids it, and review may card it

#### Scenario: A project refines a comment rule
- **WHEN** the repo's `CODING_STANDARDS.md` holds a rule naming `C2`
- **THEN** that rule replaces `C2` for the repo, and the other `C` rules still apply

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL always run. Each station SHALL run as a fresh agent process of the executor the models
file names for it, or of the executor running `mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/models/<change-id>.toml`
names for it, or the executor's default. A worker SHALL run in an OS sandbox, Claude Code's or Codex's workspace-write, its writes reaching the primary and
each open worktree and nothing outside them, under `conduct.py`'s allowlist on Claude Code, extended by `AGENTS.md`'s `Ship
tools:` line, its prompt carrying the shell rules, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt a version by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run. `conduct.py` SHALL run its own git with hooks and `core.fsmonitor` off, so a hook a worker
plants does not run at the conductor's rights. At a run's start, a version whose branch holds nothing past its cut commit,
and whose base the default branch has passed, SHALL get the default branch merged in, as a dependent does; a version with
more, an unticked phase and no merge open SHALL halt when the default branch changed a gate makefile, `AGENTS.md`,
`CODING_STANDARDS.md` or `CONTRIBUTING.md` since its base, naming the files and `git -C <tree> merge <default>`; one
with an unticked phase and a merge open with no note SHALL halt, naming `git -C <tree> commit`, unless it is a
dependent whose merge `conduct.py` finishes; any other version SHALL go on from its stage. After a release's check passes, `conduct.py` SHALL
remove the version's worktree, without `--force`, keeping its branch, only when its path is `AGENTS.md`'s `Worktrees:`
path joined with the change id, logging the ignored paths it held, listed by name; a listing that fails SHALL keep the
worktree, logged, and a refusal SHALL be logged, never forced.

#### Scenario: A worker plants a hook
- **WHEN** a `post-commit` hook stands in the repo and `conduct.py` commits a dependent's merge
- **THEN** the hook does not run on that commit

#### Scenario: Two cut versions ship
- **WHEN** two versions are cut, each in its own worktree, and `mf-ship` runs to the end
- **THEN** both are released, merged and pushed, the first ready first, the other integrated and judged by a
  catch-up round first, and only the primary is left

#### Scenario: A ready version ships past a slow one
- **WHEN** two versions run and the lower id is still building when the higher is ready
- **THEN** the higher is released first, and takes the lower number

#### Scenario: A worker runs a command off the list
- **WHEN** a build worker's command is denied by the allowlist and the build's check still passes
- **THEN** the run goes on, and the report lists the denial
- **AND WHEN** the build's check fails
- **THEN** the version halts, and its `halt` line names the denial

#### Scenario: No worktrees are declared
- **WHEN** `mf-ship` starts in a repo whose `AGENTS.md` declares no `Worktrees:`
- **THEN** it halts, naming the missing declaration, and starts no worker

#### Scenario: A version cut before main moved
- **WHEN** a version's branch holds only its cut commit, and the default branch has moved since
- **THEN** the run merges the default branch into it before its first worker, and builds on the merge
- **AND WHEN** the version's build has begun, and the default branch changed `Makefile` since its base
- **THEN** that version halts before its next worker, naming `Makefile` and the merge to run
- **AND WHEN** every phase is ticked
- **THEN** the version goes on from its stage, and integrate merges the default branch in
- **AND WHEN** a phase is unticked and the merge is open in its worktree with no note
- **THEN** that version halts before its next worker, naming `git -C <tree> commit` to finish the merge
- **AND WHEN** the merge is open with its note
- **THEN** that version halts as `integrating`, naming the note

#### Scenario: A released worktree
- **WHEN** a release's check passes under `mf-ship`
- **THEN** the version's worktree is gone and its branch kept, and the run logs the ignored paths it held
- **AND WHEN** git's worktree entry names a path other than the `Worktrees:` path joined with the change id
- **THEN** nothing is removed, and the run logs it
- **AND WHEN** the worktree's ignored paths cannot be listed
- **THEN** nothing is removed, and the run logs it

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when the worker exits 0 and its check on disk passes — never on the worker's report. The converge
check SHALL need `done` as the newest run's latest status-log event. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt. The scratch
gate's recipe SHALL try a write to a file `conduct.py` made outside the worker's reach, and SHALL pass only when that write is
refused; `conduct.py` SHALL halt the run when the file changed, and SHALL remove it. The recipe SHALL also pass only
when the shell's `uname -m` is the host's native architecture, so a worker whose shell runs translated halts the run, naming
its executor.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

#### Scenario: A worker dies after clean findings
- **WHEN** a converge worker exits 1 with both findings files clean at `HEAD` and no `done` in its status log
- **THEN** the version halts, naming the exit, and nothing is released

#### Scenario: A probe worker runs unsandboxed
- **WHEN** the probe worker's write outside its reach lands
- **THEN** the run halts naming the probe's executor, no version starts a worker, and the file is gone

#### Scenario: A worker's shell runs translated
- **WHEN** the probe worker's shell reports `x86_64` on an `arm64` host
- **THEN** the run halts, naming the executor and both architectures, and no version starts a worker

### Requirement: A finding carries its evidence and verdict

Every card SHALL hold an `Evidence:` field — the offending line quoted, the rule or spec line it breaks, and whether
it was read, traced or ran — and a `Verdict:` field, `confirmed` or `plausible`, a plausible one saying what would
confirm it. Its Priority SHALL name a category. A candidate refuted by evidence SHALL be listed under `## Refuted` in
the findings file with its counter-evidence, never as a card.

#### Scenario: A candidate is refuted
- **WHEN** a checker finds the guard that defeats a candidate
- **THEN** the candidate appears under `## Refuted` with that guard quoted, and no card is written for it

### Requirement: Every station runs MF's own method

The build SHALL identify and report the executing agent from runtime evidence, not from its model, provider or
editor, and SHALL choose no engine by it: every station runs MF's own method on every executor. The build SHALL run
`mf-simplify` and no native `/simplify`; review and security SHALL run MF's method from the bundled references, and
converge SHALL invoke no native `/code-review` or `/security-review`.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code runs the build's simplify pass and native `/simplify` is invocable
- **THEN** the build runs `mf-simplify`, not the native command

#### Scenario: A native command is unavailable
- **WHEN** native `/simplify` is not invocable
- **THEN** the build runs `mf-simplify` as on any host, and nothing halts for it

#### Scenario: Claude Code converges
- **WHEN** converge runs on Claude Code
- **THEN** every review and security worker loads MF's references, and no native review command runs

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the build reports that executor and runs `mf-simplify`

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the build reports `unidentified` without guessing from the model name, and runs `mf-simplify`

### Requirement: mf-simplify simplifies a change inside its oracles

`skills/mf-simplify/SKILL.md` SHALL take the active change's `<merge-base>..HEAD` and edit only its lines, one angle
at a time — reuse, simplification, efficiency, altitude, conventions — each edit one of `delete`, `stdlib`, `native`,
`reuse`, `speculative` or `shrink`, by the kinds the skill gives its angle. It SHALL print the output of `make -n gate`
before its first gate run, and SHALL halt, naming the root `Makefile`, when that fails or prints no command. It SHALL
run `make gate` after each angle and revert that angle's edits when the gate is red or the angle adds net lines. It
SHALL never edit a test or the change's own record, `openspec/changes/<change-id>/` and `CHANGELOG.md`, and SHALL
never apply an edit that touches a spec requirement or scenario, a public interface, a seam the design names, a
control the threat model names, a decision in force, or that exceeds 20 lines; such edits SHALL be noted for review
instead. It SHALL commit what it applied as one `refactor(<change-id>): simplify` commit whose body names the edits
applied and skipped, the mode, and `net: -N lines`. With nothing to commit it SHALL commit nothing and report
`nothing kept` with the angles reverted, the skips and the notes, or `lean already` when there are none. It SHALL
write no findings file and hold no verdict.

#### Scenario: A trap is left alone
- **WHEN** the change holds a validation the threat model names, which looks redundant
- **THEN** `mf-simplify` leaves it, and its commit body, or its `nothing kept` report, notes it as skipped with the
  reason

#### Scenario: An angle turns the gate red
- **WHEN** an angle's edits fail `make gate`
- **THEN** `mf-simplify` reverts that angle's edits, keeps the angles that passed, and notes the reverted ones

#### Scenario: Nothing to simplify
- **WHEN** no angle finds a candidate, so nothing is reverted, skipped or noted
- **THEN** `mf-simplify` reports `lean already` and makes no commit

#### Scenario: Nothing is kept
- **WHEN** every edit is reverted or skipped, so nothing is staged
- **THEN** `mf-simplify` reports `nothing kept` with the angles reverted, the skips and the notes, and makes no commit

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/findings/` files without writing to any repo, parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. The page
SHALL hold a table per repo and per model, charts over changes drawn by `mf-build`'s `chart()`, and the list of
fields each repo lacked. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed

### Requirement: A cut reserves its id against every open version branch

`skills/mf-cut-change/SKILL.md` SHALL take a change id only when its number is higher than every id under
`openspec/changes/` and `openspec/changes/archive/` on the default branch and on every branch named by a change id and not merged
into it. It SHALL take `bump=minor|patch`, write `bump:` into `proposal.md`'s frontmatter, and assign no number.

#### Scenario: Two cuts while one change is open
- **WHEN** a version branch holding change `0040-x` is not yet merged, and a second cut is asked for id `0040-y`
- **THEN** the cut halts: the id is taken by an open branch

### Requirement: The release assigns the version

`skills/mf-release/SKILL.md` SHALL read `bump:` from the change's `proposal.md`, halting on anything but `minor` or
`patch`, and SHALL take `<tag>` from `skills/mf-release/scripts/next_tag.py`, which SHALL print the next tag after the
highest `vX.Y.Z` tag, or `v0.1.0` when there is none. It SHALL write `version:` into the proposal it archives, before
it collects metrics. `conduct.py` SHALL read a released version's tag from the branch tip's `chore(release): <tag>`,
SHALL pass the release check only when that tag's commit is the tip and, with an `origin`, origin's tag is on that
tip, and SHALL hold no number before it.

#### Scenario: A minor after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: minor`
- **THEN** the release tags `v0.41.0` and the archived proposal holds `version: v0.41`

#### Scenario: A patch after v0.40.0
- **WHEN** the highest tag is `v0.40.0` and the proposal says `bump: patch`
- **THEN** the release tags `v0.40.1` and the archived proposal holds `version: v0.40.1`

#### Scenario: A repository with no version tag
- **WHEN** no tag has the form `vX.Y.Z`
- **THEN** `next_tag.py` prints `v0.1.0`

#### Scenario: A draft page before the release
- **WHEN** the build draws its metrics page and `proposal.md` holds no `version:`
- **THEN** the page reads `unreleased`, and compares with the highest tracked release

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe and a conductor crash SHALL stop the run. A run with every open version at a halt stage or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs and the release ledger in the home folder: a re-run derives
every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, or a default-branch commit no ledger entry stands behind. A worker
stopped by a usage limit SHALL be halted with its reset time named.

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
- **WHEN** integrate halted on a semantic conflict or a red gate, with the merge open and its note under
  `.minions/integrate/`
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: A version declares what it builds on

`skills/mf-cut-change/SKILL.md` SHALL take `after=<id>[,<id>]`, halting unless each id is an open version with a lower
number, and SHALL write `after: [<ids>]` into `proposal.md`'s frontmatter. A name a design takes from an `after:`
change's design, and a MODIFIED title a delta takes from an `after:` change's delta, SHALL count as present at the cut.
`conduct.py` SHALL start a dependent only once each id has released,
and SHALL then merge the default branch into its cut-only branch, with no agent, running `integrate.py delta` on the open
merge and committing it when the check passes. A requirement the check names SHALL leave the merge open, with its note
under `.minions/integrate/`, and halt the version as `integrating`. `mf-build` and `mf-release` SHALL halt unless each id
has `openspec/changes/archive/<id>/` in `HEAD`. `conduct.py status` SHALL print `waiting` for a dependent whose dependency
has not released. An `after:` edited past the cut SHALL stop no other version: an unreleased id that is not lower SHALL
block its version, and an edit that leaves a running version `waiting` SHALL halt it.

#### Scenario: An edit makes a cycle
- **WHEN** two versions name each other in `after:`, or one names itself, and a third is free
- **THEN** the named versions block with no worker, the third ships, and the run closes

#### Scenario: A worker edits its own `after:`
- **WHEN** a build worker adds an unreleased id to its version's `after:`
- **THEN** that version halts on `waiting`, and every other version goes on

#### Scenario: A dependent waits
- **WHEN** a version names a lower open version in `after:`, and `mf-ship` runs
- **THEN** its build starts only after that version's release, on a tree that holds it
- **AND** unrelated versions run in parallel meanwhile

#### Scenario: A dependent's delta edits what its dependency changed
- **WHEN** a dependent's delta modifies a requirement the default branch changed since its base
- **THEN** the merge stays open, the note names both changes, and the version halts with no build
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` builds the version

#### Scenario: A cut names a dependency it cannot have
- **WHEN** `after=` names an id that is merged, unknown, or not lower than the change's
- **THEN** the cut halts, naming it

#### Scenario: A dependent built by hand
- **WHEN** `mf-build` starts on a change whose `after:` id is not in `HEAD`'s archive
- **THEN** it halts, naming `I17`

### Requirement: Converge continues an unfinished run

When the newest run of a status log ends on neither `halt` nor `done`, `conduct.py`'s stage SHALL be `converge`, whatever
the findings files say, and `skills/mf-converge/SKILL.md` SHALL continue that run from its latest event: no new `## Run`
heading, the round unchanged, and a pickup whose fix was never committed sent again. A run whose top line is a `halt` naming
`.minions/backlog.lock` SHALL be continued the same way, at Step 9, when both findings files are clean at `HEAD`.

#### Scenario: A usage limit stops converge mid-pickup
- **WHEN** a run's latest event is `pickup` and its findings files are clean at `HEAD`
- **THEN** a re-run of `mf-ship` spawns converge, not the release
- **AND** the same run sends the pickup, verifies, writes the backlog and ends on `done`, repeating no judged round

#### Scenario: A converge halted on the backlog lock
- **WHEN** a run's top line is a `halt` naming `.minions/backlog.lock`, and both findings files are clean at `HEAD`
- **THEN** a re-run of `mf-ship` spawns converge, which writes the backlog and ends on `done` in the same run, with no new round
- **AND WHEN** either findings file is not clean at `HEAD`
- **THEN** converge halts, naming it

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. A version with every phase ticked, no converge run begun, and no `.minions/build/<change-id>.done`
naming `HEAD` SHALL be stage `build`, its closing steps left, and SHALL fail the build check: `skills/mf-build/SKILL.md`
SHALL then run its simplify step and the metrics again, restoring first, saved to a patch under `.minions/build/`, a dirty
tree whose paths are all in the change's range while its `.minions/build/<change-id>.closing` mark names `HEAD`, halting and
restoring nothing on a path outside it, a dirty tree with no such mark, or a patch an earlier save left, and SHALL write that file, naming `HEAD` and
simplify's outcome, only once both are done. Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL restore a tree dirty with only its own fold and a staged
archive move to `HEAD`, then start over; a hand release SHALL keep its clean-tree halt. It SHALL re-enter at its merge after reading its preamble against the archived delta, halting on a flag under `merge=yes` and naming it beside the ask by hand,
tagging `HEAD` first when the tag is missing, when `HEAD` is its release commit, converge was clean at `HEAD~1` and the
default branch has not moved. `conduct.py` SHALL read that stage as `release` only when the run logs show the release
worker died and the person left no `.minions/release/<change-id>.held` mark, and as `released` for any other release tip. It SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of
a run, push the default branch and each merged tag `origin` lacks, only when every first-parent commit past `origin`'s default
branch, as `origin` lists it, is a merge of a tagged release holding that release's tree, whose release commit's parent is a
head the release ledger holds that is not yet on `origin`, and every such tag is on such a release commit, and SHALL else halt, naming the commit or the
tag; an `origin` it cannot read SHALL halt the push. It SHALL push the sha it checked, never force, a rejected push halting the
run; `status`
SHALL report that work, so a run starts for it. It SHALL make no remote call, merge nothing into a dependent, and read no
tree's status or diff, while the repo's own git config holds a key off its list of keys that name no program, with an
`origin` or without one. It SHALL make no remote call while `origin`'s
fetch or push URL is not a network URL. The claim
`.minions/runs/active` SHALL hold the conductor's pid with its start time, and each worker's process
group with its leader's start time: a pid at or below 1, a dead pid or one that lost its start time is a stale claim, whose
groups a run kills, each only while its leader keeps that start time and names an executor, before it clears the claim and
starts, and `status` SHALL name it. A group that keeps its start time and names no executor SHALL stop the run, naming the
group and keeping the claim, and a run SHALL clear a stale claim before it detaches, so that stop reaches its caller. A start
time SHALL read the same in any zone or locale. A pid `ps` cannot read that still runs is no stale claim: `status`, `run` and
`/mf-ship stop` SHALL exit 2, naming it, and signal nothing, and a run that cannot read its own start time SHALL stop.

#### Scenario: A release dies before its commit
- **WHEN** a release worker dies with its fold staged and the change's folder moved
- **THEN** a re-run reads the stage as `release`, restores the tree, and releases with one tag

#### Scenario: A release dies after its commit
- **WHEN** a release worker dies between its commit and its tag, and the default branch has not moved
- **THEN** a re-run reads the stage as `release`, tags `HEAD`, merges and pushes

#### Scenario: A release dies after its tag
- **WHEN** a release worker dies after its commit and tag, and the default branch has not moved
- **THEN** a re-run merges and pushes
- **AND WHEN** the default branch has moved
- **THEN** the stage is `released`, a halt naming the person's recovery

#### Scenario: A release stopped on purpose stays stopped
- **WHEN** a release tip's worker exited 0 before its merge, or a person ran the release and said no
- **THEN** the stage is `released`, a halt naming `/mf-release`, and a re-run merges nothing

#### Scenario: A tip forges a release
- **WHEN** a version's tip says `chore(release): <tag>` and the tag is on another commit
- **THEN** the stage is `released`, and a re-run merges nothing

#### Scenario: A hand release finds uncommitted edits
- **WHEN** a person runs `mf-release` with edits uncommitted under `openspec/` or in `CHANGELOG.md`
- **THEN** the clean-tree precondition halts, and nothing is restored

#### Scenario: A person takes a flagged release
- **WHEN** a person runs `mf-release` on a release tip whose preamble is flagged
- **THEN** it reads the flag, does not halt on it, and names it beside the ask before the merge

#### Scenario: A release dies before its push
- **WHEN** the default branch is ahead of `origin` with a run's release, and no version is open
- **THEN** `status` names the unpushed work, and a run pushes it and ends on `done`

#### Scenario: A hand release left unpushed
- **WHEN** the default branch holds a release a person merged by hand, and `origin` lacks it
- **THEN** a run halts naming the merge and `git push`, and pushes nothing

#### Scenario: The repo's config names a command
- **WHEN** the repo's own git config holds `remote.origin.uploadpack`, and `origin` exists
- **THEN** `status` exits 1 naming the key, a run halts, and the conductor makes no remote call

#### Scenario: The repo's config holds an unlisted key
- **WHEN** the repo's own git config holds a `hook.*` key, or any key off the list
- **THEN** `status` exits 1 naming the key, a run halts, and no hook runs on a push or a dependent's merge

#### Scenario: A worker plants a filter
- **WHEN** a worker leaves a `filter.*` key in the repo's config, over a stat-dirty tracked file
- **THEN** the check that follows halts its version naming the key, and the filter never runs

#### Scenario: A worker repoints origin at a local repo
- **WHEN** `origin`'s URL is a local path or a `file://` URL
- **THEN** `status` exits 1, a run halts, the conductor makes no remote call, and that repo's hooks do not run

#### Scenario: The conductor is killed
- **WHEN** `.minions/runs/active` holds a dead pid and a live worker group
- **THEN** `status` reads `stale`, and a run kills the group, clears the claim and starts

#### Scenario: A claim outlives a reboot
- **WHEN** a stale claim names a group whose leader's start time is not the one the entry holds
- **THEN** a run leaves that group alive, and clears the claim

#### Scenario: A claimed group names no executor
- **WHEN** a stale claim names a group that keeps its start time, and whose leader names no executor
- **THEN** a run, detached or not, kills the claim's executors, stops naming that group, and keeps the claim

#### Scenario: A running conductor cannot be read
- **WHEN** `ps` prints nothing for the claim's pid, and that process still runs
- **THEN** `status`, `run` and `/mf-ship stop` exit 2 naming the pid, nothing is signalled, and the claim stays

#### Scenario: The time zone changes during a run
- **WHEN** `TZ` differs between the run's write of its start time and a later read
- **THEN** `status` still reads `live`

#### Scenario: A person's local commit on the default branch
- **WHEN** `main` holds a commit that is no merge of a tagged release, and `origin` lacks it
- **THEN** a run halts naming the commit, and pushes nothing

#### Scenario: A merge a release check refused
- **WHEN** `main` holds a merge of a tagged release whose tree is not that release's, and `origin` lacks it
- **THEN** a run halts naming the merge, and pushes nothing

#### Scenario: A person's version-shaped tag
- **WHEN** `main` reaches a `vX.Y.Z` tag `origin` lacks, on no `chore(release): vX.Y.Z` commit
- **THEN** a run halts naming the tag, and pushes nothing

#### Scenario: A flagged release dies
- **WHEN** a release flags its preamble, commits and dies
- **THEN** a re-run halts on the flag before its merge

#### Scenario: A build dies in simplify
- **WHEN** a build worker ticks and commits every phase, marks its closing steps begun, then dies in simplify with an edit
  left uncommitted
- **THEN** a re-run reads the stage as `build`, closing steps left, and its worker saves the edit to a patch, restores it
  and runs simplify again
- **AND** the run converges only after `.minions/build/<change-id>.done` names `HEAD`

#### Scenario: A dirty tree the build did not mark
- **WHEN** every phase is ticked, no `.done` names `HEAD`, and the tree is dirty with no `.closing` mark naming `HEAD`
- **THEN** `mf-build` halts naming the dirty paths, and restores nothing

#### Scenario: A resume finds an earlier patch
- **WHEN** a resume finds the tree dirty while `.closing` names `HEAD`, and `.minions/build/<change-id>.discarded.patch`
  already exists
- **THEN** `mf-build` halts naming the dirty paths and the patch, restores nothing, and leaves the patch as it was

#### Scenario: A build exits without its marker
- **WHEN** a build worker exits 0 with every phase ticked and committed, and no `.done` names `HEAD`
- **THEN** the build check fails, the version halts, and no second build starts

#### Scenario: A build closed before this rule
- **WHEN** a version's phases are all ticked, its converge has begun, and no `.minions/build/<change-id>.done` exists
- **THEN** the stage is read from converge's status log, as before

### Requirement: A station's executor comes from the models file

`.minions/models/<change-id>.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own, and any failed probe SHALL stop the run.
A station on Codex SHALL report no denial, and converge's tokens SHALL read `unavailable`.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

### Requirement: A worker's reach stops at the repository

A Codex worker's writable roots and a Claude worker's `Edit` and `--add-dir` SHALL be the primary and each open worktree,
from `git worktree list`, and never the directory holding them. A listed worktree whose `.git` file does not point back to
an entry under the common directory SHALL be no worktree. `conduct.py` SHALL take the primary and its common directory once,
before the first worker, and SHALL never take a worker's reach from git's answer in a worktree. It SHALL refuse a run in a
checkout whose `.git` names another repository, and SHALL halt a Codex worker when the primary's `.git` no longer resolves to
that common directory. `conduct.py` SHALL load `integrate.py` once, before the
first worker, and SHALL halt a version's merge when the local git config or `info/attributes` changed since then.

#### Scenario: A sibling project
- **WHEN** a worker runs in a repository whose parent holds other projects
- **THEN** no writable root and no `--add-dir` names that parent

#### Scenario: A worker forges a worktree entry
- **WHEN** a worker adds an entry under the common directory's `worktrees/` naming a directory outside the repository
- **THEN** no writable root and no `--add-dir` names that directory, and no version runs in it

#### Scenario: A worker repoints a worktree
- **WHEN** a worker rewrites a worktree's `.git` file or its entry's `commondir` to name another repository
- **THEN** no writable root and no `--add-dir` of the next worker names that repository

#### Scenario: A worker plants git config
- **WHEN** a worker changes the common directory's config during a run
- **THEN** the conductor merges nothing for a dependent, and that version halts, naming the change

### Requirement: A person can stop a run

`/mf-ship stop` SHALL end the live run: the conductor, then each worker group in the claim, then a `halt — stopped by the
person` line in the run log, then the claim. A group it cannot end SHALL keep the claim, and it SHALL still write that line and
exit 2, naming the group. A re-run SHALL resume from disk, and `conduct.py log --verify` SHALL pass the stopped run. With no live
run it SHALL say so and exit 0.

#### Scenario: A run is stopped
- **WHEN** a person runs `/mf-ship stop` with a worker live
- **THEN** the worker's group is gone, the log's last line is the stop, and `.minions/runs/active` is gone

#### Scenario: A stop meets a group it cannot end
- **WHEN** a person runs `/mf-ship stop`, and a claimed group names no executor or refuses the kill
- **THEN** the conductor is gone, the log's last line is the stop, the command exits 2 naming the group, and the claim stays

#### Scenario: A claim names another process
- **WHEN** the claim's pid is at or below 1, or its process lacks the claim's start time
- **THEN** `status` reads `stale`, and `/mf-ship stop` says no run is live, signals nothing and leaves the claim

### Requirement: A person can grant one more round

`/mf-ship grant <change-id>` SHALL work only on a version whose status log halted at the cap. It SHALL record the grant and
start a run. `conduct.py` SHALL spend the grant when it spawns converge, with `grant=yes`. `skills/mf-converge/SKILL.md`
SHALL open a run marked as the grant, send the open blockers to a fixer, verify one round, and on clean write the rest to
the backlog with no pickup; a blocker left SHALL halt. The cap SHALL stay three.

#### Scenario: A grant on a version not at the cap
- **WHEN** a person grants a version at any other stage
- **THEN** it refuses, naming the stage, and no run starts

#### Scenario: A grant is spent once
- **WHEN** a granted round ends on a blocker
- **THEN** the stage is `converge-halted`, and a run spends no second round

### Requirement: A run needs its skills linked

At a run's start, `conduct.py` SHALL find each `skills/mf-*` beside itself linked where its executor looks,
`~/.claude/skills` for `claude` and `~/.agents/skills` for `codex`, and SHALL else stop, naming the skill and
`make install-skills`.

#### Scenario: A skill added by a release
- **WHEN** a release adds a skill and nobody installs it
- **THEN** the next run stops at its start, naming it

### Requirement: No hook runs in a run

Every worker SHALL run with `core.hooksPath` set to `/dev/null` and `core.fsmonitor` off through git's environment, as the
conductor's own git does. `make gate` SHALL be the only check. `core.hookspath` SHALL be allowed in a repo's own git config.
`lfs.repositoryformatversion` SHALL stay refused: with no hook, a run's push uploads no LFS object. Its halt SHALL say to keep
the key and release by hand.

#### Scenario: A repo with a pre-commit hook
- **WHEN** a repo's hook would run on a worker's `git commit`
- **THEN** it does not run, and a repo whose tooling set `core.hooksPath` does not halt

#### Scenario: An LFS repo
- **WHEN** the repo's own git config holds `lfs.repositoryformatversion`
- **THEN** `status` exits 1 naming the key and a hand release, and a run halts

### Requirement: Converge never ends a turn with a worker running

`skills/mf-converge/SKILL.md` SHALL dispatch its checkers and its fixer in the foreground, and SHALL NOT end a turn while one
runs.

#### Scenario: A long fix
- **WHEN** a fixer runs for longer than the host waits on background work
- **THEN** the converge worker stays until the fixer returns

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names, and its sandbox SHALL never have `allowLocalBinding`: it binds no
loopback port, in any repo. A Codex worker SHALL run with its network off, and SHALL
start with its working directory and every tree it reaches marked untrusted, whatever the operator's Codex config says, so a
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. Both SHALL keep `uv`'s cache
in the run directory, and neither SHALL inherit the conductor's `VIRTUAL_ENV`.

#### Scenario: A script tries to leave
- **WHEN** a worker or its subagent runs a script that writes outside its reach, reads `~/.ssh`, reads a credential variable and
  calls an unlisted domain, the npm registry among them
- **THEN** each fails, on Claude; on Codex the read may pass, and that is a stated gap

#### Scenario: A worker uses its Read tool on a credential
- **WHEN** a Claude worker or its subagent calls `Read` on a path under `~/.ssh`
- **THEN** the call is denied, and the report lists the denial

#### Scenario: A worker plants a start-up
- **WHEN** a worker leaves a `SessionStart` hook in `.claude/settings.local.json`, or a server in `.mcp.json`
- **THEN** neither runs at the next Claude start

#### Scenario: A worker plants a Codex project config
- **WHEN** a worker leaves an `[mcp_servers]` entry in `.codex/config.toml`, in a tree the operator's Codex config trusts
- **THEN** it does not run at the next Codex worker's start
- **AND** no Codex worker's start writes a trust entry to the operator's Codex config

#### Scenario: The sandbox cannot start
- **WHEN** a Claude worker starts on a machine where Claude Code's sandbox cannot start
- **THEN** the worker ends without running a command, and its version halts on the exit

#### Scenario: A repo's gate serves on loopback
- **WHEN** a Claude worker runs a gate that binds `127.0.0.1`
- **THEN** the bind is refused, and the worker's sandbox has no `allowLocalBinding`

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: No worker pushes

Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL stop after its merge in the primary, and `conduct.py` SHALL push, through
the tagged-merges rule, before it judges the release. A hand release SHALL push as today. `conduct.py` SHALL make each remote
call from a scratch git directory outside every worker's reach, reading no repo's config. Before a run's first worker it SHALL
keep `origin`'s URLs in the home folder, outside every worker's reach, a file that stands staying, and SHALL push only to them.
Before it starts a version's release worker, it SHALL record that version's head in a **release ledger** in the same folder, and
SHALL push a release only when its release commit's parent is a head the ledger holds that is not yet reachable from `origin`'s
default branch, as `origin` lists it. It SHALL judge that from the commits alone, reading no ref, replace ref, graft or `shallow`
file a worker writes. The default branch it pushes and judges against SHALL be the one `origin`'s own `HEAD` names, read
through the kept URLs and kept beside them at a repo's first read; a push SHALL halt when `origin`'s `HEAD` names another.
It SHALL log each entry in the run log, and no check SHALL read that copy.
It SHALL make no remote call, in a run or in `status`, `check` or `report`, while `origin` differs from the kept URLs, and only a
person SHALL clear that, repointing `origin` or removing the file. A run that read an `origin` SHALL halt, making no remote call,
when the repo's git config or `info/attributes` differs from its first read, naming the file and a key off the list naming itself.
`status`, `check`,
`report`, `stop` and `grant` SHALL halt, making no remote call, when git names a repo outside the folder they run in and no run
kept that repo's URLs. `status`, `check` and `report` SHALL make no remote call for a repo no run kept, wherever they run: a first
read SHALL be a run's alone. For such a repo with a merged version tag, `status` SHALL print `run · unread`, so a run starts for what
it cannot read, and a run past its first pushes SHALL keep the URLs, with a version or none. The git `conduct.py` runs itself SHALL
fetch no missing object from a promisor remote.

#### Scenario: A release under mf-ship
- **WHEN** a release worker merges under `merge=yes`
- **THEN** it pushes nothing, the conductor logs a `push` event, and the release check passes
- **AND** the ledger holds no entry for that version afterwards

#### Scenario: A worker forges a release
- **WHEN** a worker commits `chore(release): v9.9.9` on a side branch, tags it, and merges it into the default branch with the
  same tree
- **THEN** the run halts naming the merge, and `origin` receives nothing

#### Scenario: A worker moves the local remote ref
- **WHEN** a worker points `refs/remotes/origin/<default>` at a plain commit on the default branch
- **THEN** the run reads `origin`'s head from `origin`, halts naming that commit, and `origin` receives nothing

#### Scenario: A worker forges a release on a landed head
- **WHEN** a release landed on `origin` — pushed by a run, pushed by a person after a failed push, or finished by a person by
  hand — and a worker merges a forged release whose parent is that release's head
- **THEN** the run halts naming the merge, and `origin` receives nothing

#### Scenario: A worker points the default branch elsewhere
- **WHEN** a worker points `refs/remotes/origin/HEAD` at an older `origin` branch, and merges there a forged release on a head
  that landed on `origin`'s default branch
- **THEN** the run judges against the branch `origin`'s `HEAD` names, pushes only that branch, and exits clean, and `origin`
  receives nothing
- **AND WHEN** `origin`'s own `HEAD` names a branch other than the kept one
- **THEN** a push halts naming both, and `origin` receives nothing

#### Scenario: A worker rewrites local history
- **WHEN** a worker adds a replace ref, a graft or a `shallow` entry that gives a forged merge a ledger head as its parent
- **THEN** the run halts naming the merge, and `origin` receives nothing

#### Scenario: A worker repoints origin during a run
- **WHEN** a worker sets `remote.origin.url` to another network URL
- **THEN** the run halts naming the changed file, and that host receives nothing

#### Scenario: A release worker plants a key off the list
- **WHEN** a release worker leaves such a key in a repo with an `origin`
- **THEN** the run halts naming the key, and makes no remote call

#### Scenario: A repoint outlasts the run
- **WHEN** a run stopped with `origin` repointed, and `status`, `check`, `report` or a new run follows
- **THEN** each that would make a remote call halts naming the file that keeps the URLs, and that host receives nothing
- **AND WHEN** a person repoints `origin`, or removes that file
- **THEN** the next run goes on, and a removed file keeps what that run reads

#### Scenario: A worker redirects git to another repo
- **WHEN** a `commondir` file, or a swapped `.git`, leaves git naming a repo no run kept, outside the folder they run in, its
  `origin` on another host
- **THEN** `status`, `check` and `report` halt, and that host receives nothing
- **AND WHEN** a person removes the redirect
- **THEN** each reads the primary again
- **AND WHEN** a `commondir` file, a `.git` file, or a whole repo at `.git`, leaves git naming a repo inside a linked worktree
- **THEN** that host receives nothing

#### Scenario: No run kept the repo
- **WHEN** `status`, `check` or `report` runs in a repo with an `origin` no run kept
- **THEN** none makes a remote call: `status` names no tag, and `check` and `report` read a tag as not on `origin`
- **AND WHEN** a run starts there, even where the home folder refuses the file
- **THEN** it reads `origin` itself, for its pushes and its release check

#### Scenario: A tag alone in a repo no run kept
- **WHEN** `main` is level with `origin`, a merged tag is not on it, and no run kept the repo
- **THEN** `status` prints `run · unread`, and `mf-ship` starts a run, which pushes the tag and keeps the URLs
- **AND WHEN** `status` runs again
- **THEN** it reads `origin` itself, and prints no such line
- **AND WHEN** a repo with an `origin` no run kept holds no merged version tag
- **THEN** `status` prints `status: none — no open version`, and no run starts

#### Scenario: A worker sets a key after the refusal
- **WHEN** a key that names a program stands in the repo's config after the refusal read it clean
- **THEN** the conductor's remote calls and pushes do not run that program

#### Scenario: A worker plants a promisor remote
- **WHEN** a worker sets `remote.<name>.promisor`, and deletes a blob `conduct.py` reads
- **THEN** that read fails, and the remote's URL receives nothing
- **AND** the key halts the run where any key off the list does

### Requirement: A run's plan is read once

`conduct.py` SHALL read every open version's executors, models and efforts, and `AGENTS.md`'s `Ship network:` and `Ship tools:`
lines, once, before the first worker, and SHALL halt a
version whose models file later differs. An `AGENTS.md` that declares `Ship loopback:` SHALL halt the run, naming the line
as removed. It SHALL halt a version before
integrate when the default branch holds a first-parent commit past `origin` that merges no release.

#### Scenario: A worker edits the models file
- **WHEN** a worker changes a later station's `executor`
- **THEN** that version halts, and no worker starts on the new executor

#### Scenario: A person commits to main during a run
- **WHEN** the default branch gains a person's commit while a version builds
- **THEN** that version halts before integrate, naming the commit

#### Scenario: A repo declares loopback badly
- **WHEN** `AGENTS.md` declares `Ship loopback: yes`, `Ship loopback: maybe`, or any value
- **THEN** the run halts naming the removed line, and starts no worker

#### Scenario: A Codex station in a loopback repo
- **WHEN** a repo declares `Ship loopback:`, and a version's models file names `executor = "codex"` for a station
- **THEN** the run halts on the removed line before any worker, whatever the executor

#### Scenario: A run in a loopback repo
- **WHEN** a run starts in a repo that declares no `Ship loopback:`
- **THEN** its log holds no `loopback` event, and no worker's sandbox has `allowLocalBinding`

### Requirement: Converge runs one depth

`skills/mf-converge/SKILL.md` SHALL run one depth: each role's one fresh worker SHALL judge the change from a packet given up
front, reading beyond the diff only to trace a named angle, and SHALL run review's stale-claim, test-cost and coverage-trace
passes itself. It SHALL take no `tier=`, and SHALL halt, naming the parameter as removed, when one is given. The review and
security files' frontmatter SHALL record `mode`, `workers`, `model` and `packet`, and no tier. The cut SHALL write no `tier` into
`.minions/models/<change-id>.toml`; `mf-ship` SHALL read none from it, and SHALL pass none to converge.

#### Scenario: Converge runs
- **WHEN** converge runs
- **THEN** each role is one fresh worker, and the findings files and the status log record no tier

#### Scenario: A tier is given by hand
- **WHEN** a person runs `/mf-converge <change-id> tier=high`
- **THEN** converge halts, naming `tier` as removed, and dispatches no worker

#### Scenario: An old models file holds a tier
- **WHEN** a version's models file's `[converge]` table holds `tier = "high"`
- **THEN** `mf-ship` ignores it, and the converge prompt carries no tier

#### Scenario: A granted round
- **WHEN** the person grants a round past the cap
- **THEN** the converge prompt ends `and grant=yes`, with no tier clause

#### Scenario: A diff is large
- **WHEN** a change exceeds 1,500 changed lines
- **THEN** it is reviewed anyway, and each file's Summary says it is over the standard cap and to consider a split
