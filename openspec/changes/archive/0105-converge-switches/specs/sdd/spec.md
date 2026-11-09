## MODIFIED Requirements

### Requirement: The ship station takes cut versions to the default branch

`skills/mf-ship/SKILL.md`, run in the primary checkout of a repo whose `AGENTS.md` declares `Worktrees:`, SHALL take
every open version to the default branch: build, then converge, for every open version at once; then, one version
at a time, in the order they are ready, integrate when its base moved, converge's catch-up round, and release with
`merge=yes`. Converge SHALL run for every version whose models file does not say `[converge] skip = true`. A version whose
models file says it SHALL go from its build to integrate, when its base moved, and to release, with no converge worker and no
catch-up round, and `conduct.py` SHALL log `converge skipped — plan` once for it. Each station SHALL run as a fresh agent process of the executor the models
file names for it, or of the executor running `mf-ship`, in the version's worktree — integrate in the primary — with the model `.minions/changes/<change-id>/models.toml`
names for it, or the executor's default. A worker SHALL run in an OS sandbox, Claude Code's or Codex's workspace-write, its writes reaching the primary and
each open worktree and nothing outside them, under `conduct.py`'s allowlist on Claude Code, extended by `AGENTS.md`'s `Ship
tools:` line, its prompt carrying the shell rules, and SHALL never run with permission prompts bypassed. A denial SHALL
not halt a version by itself: the station's check decides, and the report lists every denial. Starting `mf-ship` SHALL be the person's yes to every
merge and push of the run. `conduct.py` SHALL run its own git with hooks and `core.fsmonitor` off, so a hook a worker
plants does not run at the conductor's rights. At a run's start, a version whose branch holds nothing past its cut commit,
and whose base the default branch has passed, SHALL get the default branch merged in, as a dependent does; a version with
more, an unticked phase, no merge open and no `stacked-on`, whose base the default branch passed changing a gate makefile, `AGENTS.md`,
`CODING_STANDARDS.md` or `CONTRIBUTING.md`, SHALL get the default branch merged in when the merge is clean or its conflicts
are all paths `integrate.py`'s `changelog`, `decisions` and `delta` rules settle, and SHALL else halt, naming the files and
`git -C <tree> merge <default>`, or, when the merge is clean and its `decisions` rule halts, that halt and
`git -C <tree> merge --no-ff --no-commit <default>`; one
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

#### Scenario: A version whose plan skips converge
- **WHEN** a version's models file says `[converge] skip = true`, and its build is done
- **THEN** its stage is `integrate` while the default branch is not an ancestor of `HEAD`, else `release`, and no converge
  worker starts for it
- **AND** the run log holds `converge skipped — plan` for it once
- **AND WHEN** integrate's merge moves `HEAD`
- **THEN** the version goes on to release with no catch-up round

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
- **THEN** the run merges the default branch in when the merge is clean or conflicts only in `CHANGELOG.md`, and builds on
  the merge
- **AND WHEN** the merge conflicts in a path no rule settles
- **THEN** that version halts before its next worker, naming `Makefile` and the merge to run
- **AND WHEN** the merge is clean and its `decisions` rule halts
- **THEN** that version halts before its next worker, naming the rule's halt and
  `git -C <tree> merge --no-ff --no-commit <default>`
- **AND WHEN** every phase is ticked
- **THEN** the version goes on from its stage, and integrate merges the default branch in
- **AND WHEN** a phase is unticked and the merge is open in its worktree with no note
- **THEN** that version halts before its next worker, naming `git -C <tree> commit` to finish the merge
- **AND WHEN** the merge is open with its note
- **THEN** that version halts as `integrating`, naming the note
- **AND WHEN** the version's build has begun on its dependency's built head, `stacked-on` standing
- **THEN** the run merges nothing into it until its dependency releases

#### Scenario: A released worktree
- **WHEN** a release's check passes under `mf-ship`
- **THEN** the version's worktree is gone and its branch kept, and the run logs the ignored paths it held
- **AND WHEN** git's worktree entry names a path other than the `Worktrees:` path joined with the change id
- **THEN** nothing is removed, and the run logs it
- **AND WHEN** the worktree's ignored paths cannot be listed
- **THEN** nothing is removed, and the run logs it

### Requirement: A release may skip the check loop, and says so

`skills/mf-release/SKILL.md` SHALL release a change for which no findings file and no diff patch exist, and SHALL
state the skip as the line `converge: skipped — no findings files`, or `converge: skipped — by plan` when
`.minions/changes/<change-id>/models.toml` says `[converge] skip = true`. It SHALL state `<role>: skipped` in the report and
the release commit for each findings file whose frontmatter says `mode: skipped`. It SHALL halt when the diff patch exists
without a findings file, and when one findings file exists without the other. It SHALL NOT carry the rule that a
missing findings file is not clean; that rule SHALL stay in `skills/mf-converge/SKILL.md`, which judges its own
stations by it.

#### Scenario: The release names the skip, and the missing-file rule lives in converge only
- **WHEN** `mf-release` finds no findings file and no diff patch for the change
- **THEN** it releases, and states the skip as the line `converge: skipped — no findings files`
- **AND** it does not judge a missing findings file itself; `mf-converge` holds that rule for its own stations

#### Scenario: The release names a skip by plan
- **WHEN** `mf-release` finds no findings file and no diff patch, and the models file says `[converge] skip = true`
- **THEN** it releases, and states the line `converge: skipped — by plan` in the report and the release commit

#### Scenario: The release names a skipped checker
- **WHEN** `adversarial.md` says `mode: skipped` and `verdict: clean` at `HEAD`, and `conformance.md` is clean at `HEAD`
- **THEN** `mf-release` releases, and states `adversarial: skipped` in the report and the release commit

#### Scenario: The release names both halts
- **WHEN** `mf-release` finds the diff patch without a findings file, or one findings file without the other
- **THEN** it halts, naming what it found

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort`, and the conformance and adversarial tables an `executor`; `[converge]` stays the
conductor's, and MAY say `shadow = true`. `[converge]` MAY say `skip = true`, and a conformance or adversarial table MAY say
`skip = true`, with no model, effort or executor: only the value `true` skips. `conduct.py` SHALL read them once with the run's plan, save `[converge] skip`, which it also reads from the file at each stage
read. A `[converge]` naming no
model or effort SHALL run its conductor on Claude as `claude-sonnet-5-5` at `high`. A checker table with no
`executor` SHALL run on converge's. It SHALL halt a version, before its worker starts, on a fixer table that names an
`executor`, an `executor` it does not know, a checker table naming `executor = "codex"` with a `claude-*` model, or a `model` or
`effort` holding anything
but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later differs, as for any station's table.
It SHALL pass in the converge prompt, before any grant clause, for conformance, adversarial and the fixer in that order:
`and <role>=skip` for a checker whose table says `skip = true`, else
`and <role>=mailbox` for a checker whose executor differs from converge's, else `and <role>=<model>/<effort>` for a table that
names a model or an effort, `default` for the one absent, with converge on Claude; then `and shadow=yes` under `shadow = true`. Converge SHALL put each model on its
worker's call,
send each `mailbox` role through `conduct.py checker`, and SHALL NOT read the models file itself. A skipped checker SHALL name no
executor to probe, SHALL open no mailbox for itself, and SHALL be no mailbox role; a version whose models file says `[converge]
skip = true` SHALL name no executor of converge or of a worker table to probe. A fixer sent any blocking card
SHALL run on adversarial's model when adversarial runs on converge's host and is not skipped, and otherwise on the fixer's; the fixer SHALL run at
the fixer's effort, `medium` when `fix=` names none. A verify worker SHALL run on its role's model at `medium`. A role given
none, or a host whose worker call takes no model, SHALL run its worker on the conductor's model. The cut SHALL write the worker
tables from the brief's `conformance`, `adversarial` and `fix` parts, each host as `executor`, and else conformance on the mid
tier · high, adversarial on the strongest tier · high, the fixer on the mid tier · medium; `[converge]` on Sonnet 5.5 · high,
where the session offers it, unless the brief names converge's model; and `shadow = true` when the brief's line ends `shadow`,
each mapped to the offered models. A brief's `skip` part SHALL be written as `skip = true` under that table, with no model or
effort, and `converge skip` as `skip = true` under `[converge]`, with no worker table.

#### Scenario: The converge prompt names each worker's model
- **WHEN** a version's models file holds `[converge.adversarial]` with `model = "claude-opus-5-5"` and `effort = "high"`, and
  `[converge.fix]` with `model = "claude-sonnet-5-5"` and `effort = "high"`, and its converge runs on Claude
- **THEN** its converge prompt reads `Run the mf-converge skill for change <change-id> and adversarial=claude-opus-5-5/high and
  fix=claude-sonnet-5-5/high.`

#### Scenario: The conductor's default
- **WHEN** a version's `[converge]` names no model and no effort, and converge runs on Claude
- **THEN** its converge worker starts with `--model claude-sonnet-5-5` and `--effort high`
- **AND WHEN** `[converge]` names `model = "claude-opus-5-5"`
- **THEN** it starts on `claude-opus-5-5`

#### Scenario: Converge on Codex
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a worker table naming no executor
- **THEN** its converge prompt names no worker model, and every worker runs on the conductor's model

#### Scenario: A checker on another host
- **WHEN** `[converge.conformance]` names `executor = "codex"` and converge runs on Claude
- **THEN** its converge prompt holds `and conformance=mailbox`, and names no model for conformance

#### Scenario: A skipped checker
- **WHEN** `[converge.adversarial]` says `skip = true`, converge runs on Claude, and `[converge.conformance]` names
  `executor = "codex"`
- **THEN** its converge prompt holds `and conformance=mailbox and adversarial=skip`
- **AND WHEN** `[converge.conformance]` names no executor and `[converge.adversarial]` names `executor = "codex"` beside its `skip = true`
- **THEN** no Codex probe runs for the version, and its prompt opens no mailbox

#### Scenario: A plan that skips converge
- **WHEN** a version's `[converge]` says `skip = true` and its worker tables name `executor = "codex"`
- **THEN** no executor of that version is probed beyond the build's and release's, and no converge worker starts

#### Scenario: A worker table names an executor
- **WHEN** `[converge.fix]` names `executor = "codex"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A worker table changes during the run
- **WHEN** a worker changes `[converge.fix]`'s model after the run read its plan
- **THEN** that version halts, naming the models file as changed during the run

#### Scenario: The fixer by grade
- **WHEN** converge dispatches a fixer sent a blocking card, adversarial running on converge's host
- **THEN** the fixer runs on adversarial's model, at the fixer's effort
- **AND WHEN** it dispatches a fixer sent only non-blocking cards
- **THEN** the fixer runs on the fixer's model and effort
- **AND WHEN** adversarial is skipped
- **THEN** the fixer runs on the fixer's model and effort

### Requirement: Converge's checkers are conformance and adversarial

Converge SHALL run two checkers, save one a plan skips. **Conformance** SHALL judge the code against the change's own spec delta, design, tasks and
the decisions it cites, write `.minions/changes/<change-id>/conformance.md`, and grade `blocking` · `drift` · `nit`, its card
ids `R<n>`. **Adversarial** SHALL try to break the change — races, edge cases, exploits, security — write
`.minions/changes/<change-id>/adversarial.md`, and grade `critical` · `high` · `medium` · `low`, `high` a bug that would block,
its card ids `S<n>`. Each SHALL load its reference, `skills/mf-converge/references/generic-conformance.md` or
`skills/mf-converge/references/generic-adversarial.md`, whose `## The packet` table SHALL name what the conductor gives it:
conformance the range, `diff.patch`, the simplify commit's body, the change's `proposal.md`, `design.md`, `tasks.md` and spec
delta, its `bundle.md` and `debt-cards.md`, root `AGENTS.md` and the root standards files; adversarial the range,
`diff.patch`, the source and tests around the diff's hunks, `THREAT_MODEL.md`, root `AGENTS.md` and `debt-cards.md`.
Conformance SHALL read no code beyond the diff's hunks, save its stale-claim search. Each SHALL read `diff.patch` once, top to
bottom in slices, never a slice again, finding a hunk it needs again with `grep -n` on the patch, and run `git diff` or
`git show` only for a file's context the patch does not hold. A **security card** SHALL be an adversarial card whose
Priority's category is `security`.

#### Scenario: A converge round
- **WHEN** converge dispatches a round's checkers
- **THEN** conformance writes `conformance.md` and adversarial writes `adversarial.md`, and the release reads both

#### Scenario: A round with a skipped checker
- **WHEN** converge is given `adversarial=skip`
- **THEN** it dispatches conformance alone, and `adversarial.md` is its stub, written by `skip_stub.py`

#### Scenario: The packets
- **WHEN** the packet tables of the conformance and adversarial references are read
- **THEN** conformance's names the change's artifacts, `bundle.md`, `debt-cards.md` and `diff.patch`, and no source beyond
  the diff's hunks
- **AND** adversarial's names `THREAT_MODEL.md` and `debt-cards.md`, and no `bundle.md`

#### Scenario: A security card
- **WHEN** an adversarial card's Priority reads `high · adversarial · security`
- **THEN** it is a security card
- **AND WHEN** it reads `high · adversarial · stability`
- **THEN** it blocks, and is no security card

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

## ADDED Requirements

### Requirement: A converge conductor stubs a skipped checker

`skills/mf-converge/scripts/skip_stub.py <findings-file> <round>` SHALL write the findings file of a checker a plan skips as a
stub: the findings contract's frontmatter with `head:` the commit `git rev-parse HEAD` prints, `round:` as given, `reviewed:`
today, `open_blocking: 0`, `verdict: clean`, `mode: skipped`, `workers: 0`, `model: none`, `executor: none` and `packet:
skipped: all`, and no card. It SHALL print the line it wrote, exit 0, and exit 2 with `skip_stub: cannot stub — <why>` when the
path is a link, is not of the form `changes/<change-id>/conformance.md` or `changes/<change-id>/adversarial.md`, or no repository holds the working
directory. `skills/mf-converge/SKILL.md` SHALL dispatch no worker for a role it is given `<role>=skip` for, and SHALL run
`skip_stub.py` for that role after the freeze of round 1, each re-freeze, a catch-up round's freeze and its by-rule write, and before
its `done`, so that the stub's `head:` is `HEAD` whenever converge ends. Step 5 SHALL read a stub for `verdict: clean` and its
`head:` alone, with no `verdicts` line. The adversarial head by rule SHALL run no `surfaces.py` when adversarial is skipped. A pickup
check SHALL need the checker the plan did not skip. `conduct.py`'s readers of a findings file SHALL stay as they were: a
stub is clean at `HEAD`, holds no card, and bars no rescue or supervisor.

#### Scenario: A stub is written
- **WHEN** `skip_stub.py .minions/changes/0001-a/adversarial.md 1` runs in a repository whose `HEAD` is `abc1234…`
- **THEN** the file holds `head: abc1234…`, `verdict: clean`, `mode: skipped` and `workers: 0`, and the line it printed names the
  path

#### Scenario: A stub for a path it does not take
- **WHEN** the findings path is a link, or ends `review.md`
- **THEN** `skip_stub.py` exits 2, writes nothing, and prints `skip_stub: cannot stub — <why>`

#### Scenario: A version with adversarial skipped
- **WHEN** converge runs for a version whose prompt holds `adversarial=skip`, and conformance finds nothing
- **THEN** `conformance.md` and the stub of `adversarial.md` are both clean at `HEAD`, `conduct.py` reads the version as
  judged, and its rescue and supervisor are barred by no security card
- **AND** the release states `adversarial: skipped`

#### Scenario: A skipped converge writes no debt and no hand read
- **WHEN** a version's plan says `converge skip`
- **THEN** no findings file, no diff patch and no debt card is written for it, and no hand read is asked for

### Requirement: The plan and the cut take a repo's converge default

`skills/mf-plan/SKILL.md` SHALL, when root `AGENTS.md` holds a `**Converge:**` line whose value is `skip`, `conformance skip` or
`adversarial skip`, pre-fill each version's suggested models line with `converge skip`, `conformance skip` or `adversarial
skip` as the value says, for the person to confirm or change. `skills/mf-cut-change/SKILL.md` SHALL, when its source names no
models for the change and root `AGENTS.md` holds that line, write the matching `skip = true` into the change's `models.toml`.
Neither SHALL read the line for any other purpose, and `conduct.py` SHALL NOT read it: a run reads `models.toml` alone. The cut
SHALL warn, in its show and in `cut-notes.md`, when a change's models skip adversarial or converge and a file its tasks name
matches a glob of `THREAT_MODEL.md`'s `## Surfaces`. The release SHALL name the skip whether or not the cut warned.

#### Scenario: A repo defaults to a skip
- **WHEN** root `AGENTS.md` holds `**Converge:** skip` and `mf-plan` suggests models for a version
- **THEN** the suggested line reads `converge skip`, and the person may change it

#### Scenario: The cut warns
- **WHEN** a change's models skip adversarial, and a task names a file a `## Surfaces` glob matches
- **THEN** the cut's show and `cut-notes.md` carry a warning naming the file and the glob, and the cut commits as before

### Requirement: A converge worker's description names its role and round

`skills/mf-converge/SKILL.md` SHALL tell the conductor to give each Agent call a description opening with the worker's name:
`<role> round <N>` for a checker, `fix round <N>` for the fixer, `verify <role> round <N>` for a verify worker and `verify round
<N> · pickup` for a pickup check. `skills/mf-review-metrics/scripts/review_metrics.py`'s `WORKER` SHALL match a description
only at its start.

#### Scenario: A fixer is booked to the fixer
- **WHEN** a subagent's description reads `fix round 2 · adversarial cards`
- **THEN** `review_metrics.py` books it to the role `fix`, round 2

#### Scenario: A description that opens with a station word
- **WHEN** a subagent's description reads `Security station verify round 2`
- **THEN** `review_metrics.py` books it to no role, as a gap
