## ADDED Requirements

### Requirement: The conductor runs the gate of a build

`conduct.py` SHALL run the full gate, as `skills/mf-converge/scripts/gate_run.py` under the sandbox runner over the version's trees, after the last phase's check passes and in the close, and SHALL log each gate it runs as a `check` event of the run log: `check — gate · pass · <n>s`, or `check — gate · fail — <why>`. A red gate after the last phase SHALL write the gate's output to `.minions/changes/<change-id>/gate.red` and start one build worker, once a run, naming `phase=repair`, on the last phase's models; the gate SHALL then run again, and a second red SHALL halt the version `gate red after the repair`, writing `build.halt` with `sub-task: repair`. `gate_run.py` SHALL read a gate that runs past its limit as red: it SHALL print `gate: red — past its limit · <seconds>s` and exit 124, never a traceback. A repository with no `check` target SHALL keep its workers on the gate through `gate_run.py`, and the conductor's gate SHALL take that record on the same tree.

#### Scenario: A gate red after the last phase, green after the repair
- **WHEN** the last phase's check passes and the conductor's gate is red, and the repair worker commits a fix
- **THEN** `gate.red` holds the gate's output, one worker naming `phase=repair` runs on the last phase's models, and the gate runs again green

#### Scenario: A gate red twice
- **WHEN** the gate is red after the repair worker's commit
- **THEN** the version halts `gate red after the repair`, `build.halt` names `sub-task: repair`, and no second repair worker starts

#### Scenario: A gate past its limit
- **WHEN** `make gate` runs past `GATE_SECONDS`
- **THEN** `gate_run.py` prints `gate: red — past its limit · <seconds>s` and exits 124

### Requirement: A close command ends a build

`conduct.py close <change-id>` SHALL run, in the version's worktree, the gate through `gate_run.py`, then the metrics where `metrics/catalogue.toml` stands, then `plan_check.py --change <change-id> --base <base>`, and then write `.minions/changes/<change-id>/build.done` as `head: <the full sha of HEAD>` and `simplify: <sha>` — the newest `refactor(<change-id>): simplify` commit of the range — or `simplify: none`, and remove `build.closing`. It SHALL print `close: done` and exit 0, print `close: fail — <why>` and exit 1, or print `close: cannot run — <why>` and exit 2 for a missing version. It SHALL fail on an unticked `## Progress` box or a dirty tree. On a red gate it SHALL write `gate.red`, and on a red gate, a metrics halt or a plan-check failure it SHALL write `build.halt` with `sub-task: close`, `stop:`, `evidence:` and `head:`, so the rescue's key reads on. It SHALL keep the plan check's printed lines in `plan-check.txt` beside `build.halt`. A red gate with a `refactor(<change-id>): simplify` commit at `HEAD` SHALL reset the branch to the commit before it, print `reset — simplify dropped`, and run the steps once more. A hand build with no `phase=` and a run SHALL run this command and no other close.

#### Scenario: A green close
- **WHEN** `conduct.py close 0001-a` runs on a version with every box ticked, a clean tree, a green gate and a clean plan check
- **THEN** it prints `close: done`, exits 0, and `build.done` names `HEAD` and the simplify commit or `none`

#### Scenario: A red gate with no simplify commit
- **WHEN** the gate is red and `HEAD` is not a simplify commit
- **THEN** `gate.red` and `build.halt` are written, and the command prints `close: fail — <why>` and exits 1

#### Scenario: A red gate with a simplify commit
- **WHEN** the gate is red and `HEAD` is a `refactor(<change-id>): simplify` commit
- **THEN** the branch is reset to the commit before it, `reset — simplify dropped` is printed, and the steps run again

#### Scenario: A version that is not there
- **WHEN** no version branch holds the change id
- **THEN** the command prints `close: cannot run — <why>` and exits 2

## MODIFIED Requirements

### Requirement: The build runs a fresh worker per phase

Under `mf-ship`, `conduct.py` SHALL spawn one build worker for the first unticked `## Progress` phase that is not a
`**HUMAN` one, its prompt naming `phase=<N>`, and, once every phase is ticked and the gate after the last phase is green, one build worker for the close, its prompt naming `phase=close`, when no `.minions/changes/<change-id>/build.done`
names `HEAD` — right after the last phase's spawn passes, too,
when converge has already run. A phase worker's check SHALL pass only when its
phase is ticked at `HEAD` and the tree is clean; any other outcome SHALL halt the version as a build check does, so a phase is
spawned again only after a rescue's or a supervisor's taken amend. The close worker's check SHALL be every box ticked and a clean tree, and asks for no `build.done`: after it passes, the conductor SHALL write `.minions/changes/<change-id>/build.simplified` with `head: <the full sha of HEAD>`, run `conduct.py close`, and then hold the build check. A close whose every commit past `build.simplified`'s head is a `docs(<change-id>): amend the change directory` commit touching the change directory alone SHALL run `conduct.py close` with no worker. The close worker SHALL run on `[build.close]`, else `[build.moderate]`, else `[build]`.
`skills/mf-build/SKILL.md` SHALL build the named phase alone under `phase=<N>`, halting when it is not the first unticked one,
SHALL run simplify alone under `phase=close`, halting on an unticked phase, SHALL repair the gate's red output in `gate.red` under `phase=repair`, and SHALL build every
phase, simplify, and run `conduct.py close` once when given none. After each phase's commit it SHALL print the phase's `## Progress` line as `HEAD` holds it,
quote that line in its close-out, and tick and commit a line still unticked before it ends. Each phase SHALL append what the next phase needs to
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

#### Scenario: A phase's tick is read back
- **WHEN** a build worker has committed a phase whose `## Progress` line `HEAD` still holds unticked
- **THEN** the worker ticks the box, commits it, and prints the line again before its close-out
- **AND** its close-out quotes the line it printed

#### Scenario: A stacked dependent is reset
- **WHEN** a stacked dependent's dependency changes a decision, and the dependent is reset to its cut commit
- **THEN** its `build-notes.md` is gone, and its build starts again at phase 1

#### Scenario: An amend after a close halted
- **WHEN** the close halted on its plan check, and the rescue's amend of the change directory is taken
- **THEN** the run holds `conduct.py close` again with no worker, and a second simplify does not run

#### Scenario: A commit that moves code after a close halted
- **WHEN** a commit that touches code stands past `build.simplified`'s head
- **THEN** the next spawn is a worker naming `phase=close`

### Requirement: A moderate phase builds on its own model

`skills/mf-cut-change/SKILL.md` SHALL end each `## Progress` line but a `**HUMAN` one with ` · moderate` or ` · hard`: `hard`
when the phase matches the strongest-tier row of its *Suggesting models* table, `moderate` otherwise. `conduct.py` SHALL run a
phase whose line ends ` · moderate` on the models file's `[build.moderate]` model and effort, on `[build]`'s executor, when
that table names a model or an effort; every other phase, and a phase with no rating among them, SHALL run on
`[build]`'s. The close SHALL run on the models file's `[build.close]` model and effort, else `[build.moderate]`'s, else `[build]`'s, each key from the first table that names it, on `[build]`'s executor; the brief's models line SHALL take the part `build-close <model> <effort>` after `build-moderate`, with no host. A `[build.moderate]` or `[build.close]` naming an `executor`, a model or effort outside `[A-Za-z0-9._-]`, or a `claude-*` model on a
Codex build SHALL halt the version before its worker starts. The run SHALL read `[build.moderate]` and `[build.close]` once with its plan.

#### Scenario: A moderate and a hard phase
- **WHEN** a version's models file holds `[build]` with `claude-opus-5-5` and `[build.moderate]` with `claude-sonnet-5-5` at
  `high`, phase 1 ends ` · moderate` and phase 2 ` · hard`
- **THEN** phase 1's worker runs on `claude-sonnet-5-5` at `high`, and phase 2's on `claude-opus-5-5`

#### Scenario: No moderate table
- **WHEN** the models file holds no `[build.moderate]`
- **THEN** every build worker but the close runs on `[build]`'s model

#### Scenario: A moderate table names a host
- **WHEN** `[build.moderate]` names `executor = "codex"`
- **THEN** the version halts naming the table, and no worker starts for it

#### Scenario: A close table
- **WHEN** the models file holds `[build]` with `claude-opus-5-5`, `[build.moderate]` with `claude-sonnet-5-5` at `medium`, and `[build.close]` with `claude-sonnet-5-5` at `high`
- **THEN** the close's worker runs on `claude-sonnet-5-5` at `high`, and without `[build.close]` at `medium`, and with neither on `claude-opus-5-5`

#### Scenario: A close table names a host
- **WHEN** `[build.close]` names `executor = "codex"`, or the brief's models line writes `build-close codex/m high`
- **THEN** the version halts naming the table, or the brief check fails, and no worker starts for it

### Requirement: The build runs a quick check between phases

`skills/mf-build/SKILL.md` SHALL end each phase, the last included, on a green `make check` when `make -n check` exits 0, and on a green
gate otherwise; the conductor SHALL run the full gate after the last phase. The input contract's `I8` SHALL read "each phase ends on a green
`make check`, the build on a green gate", in `mf-build` and in `mf-cut-change`.

#### Scenario: A repo with a check target
- **WHEN** a target's `Makefile` has a `check` target, and a change has three phases
- **THEN** the build runs `make check` after phases 1, 2 and 3, and the conductor runs the gate after phase 3

#### Scenario: A repo without one
- **WHEN** `make -n check` exits non-zero
- **THEN** the build runs the gate after every phase, as before

### Requirement: The build collects a draft of the metrics after simplify

When the repository has a catalogue, `conduct.py close` SHALL, after its gate, collect the metrics into `.minions/metrics/<change-id>.json` and render
`.minions/metrics/<change-id>.html`, both gitignored, and print the counts of the metrics that crossed their watch in this change or
moved the wrong way. The close SHALL NOT halt on a watch; an exit of the collector other than 0 and 3 SHALL halt it with `stop: metrics`.

#### Scenario: A change crosses a watch
- **WHEN** a metric's value crosses its `watch` in this change
- **THEN** the close prints the page and counts the metric
- **AND** the close goes on to the plan check, leaving the choice to the person

#### Scenario: No catalogue
- **WHEN** the repository holds no `metrics/catalogue.toml`
- **THEN** the close prints `metrics: none — no catalogue` and goes on

### Requirement: mf-simplify simplifies a change inside its oracles

`skills/mf-simplify/SKILL.md` SHALL take the active change's `<merge-base>..HEAD` and edit only its lines, one angle
at a time — reuse, simplification, efficiency, altitude, conventions — each edit one of `delete`, `stdlib`, `native`,
`reuse`, `speculative` or `shrink`, by the kinds the skill gives its angle. It SHALL print the output of `make -n check`
before its first check run, and SHALL halt, naming the root `Makefile`, when that fails or prints no command; a repository with no `check` target SHALL keep it on `make gate`. It SHALL
run `make check` after each angle and revert that angle's edits when the check is red or the angle adds net lines. It
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
- **WHEN** an angle's edits fail `make check`, the check of its angle
- **THEN** `mf-simplify` reverts that angle's edits, keeps the angles that passed, and notes the reverted ones

#### Scenario: Nothing to simplify
- **WHEN** no angle finds a candidate, so nothing is reverted, skipped or noted
- **THEN** `mf-simplify` reports `lean already` and makes no commit

#### Scenario: Nothing is kept
- **WHEN** every edit is reverted or skipped, so nothing is staged
- **THEN** `mf-simplify` reports `nothing kept` with the angles reverted, the skips and the notes, and makes no commit

### Requirement: Converge writes the evidence of each freeze

At every freeze — round 1, each re-freeze after a fix, a catch-up — after `debt-cards.md` and before any dispatch, converge
SHALL write `.minions/changes/<change-id>/evidence.md` whole, from tools alone, and hand its path to every worker it starts
through the placeholder `{evidence}` of each reference's `## Prompt`. The file SHALL hold four sections, each a list of lines
or `None.`: **Gate integrity** — one line for each suppression, skip, removed test, removed assertion, edit to the gate's
configuration or swallowed error the frozen patch holds, by `skills/mf-converge/scripts/gate_integrity.py`; **Plan check** —
the whole output of `plan_check.py` for the freeze, a command past its limit shown as timed out, never as failed, or, when `.minions/changes/<change-id>/build.done` names the frozen head, the lines of `plan-check.txt` the close kept, with no `plan_check.py` run;
**Stale-claim candidates** — each name the patch renames or deletes with
its `git grep` mentions outside the patch; **Test cost** — each test the patch adds with its seconds from the gate's junit
report, each `slow` marker and end-to-end `run` boot it adds, and each test it removes against the design's `## Tests`
section. Each line SHALL name a file by its path as Git names it, unquoted, and SHALL time a test by its module, its class
and its name. Converge SHALL judge nothing in it, and SHALL run each command under the sandbox runner. A line that says a command
timed out SHALL raise no card by itself, from the fixer, a checker or Step 7.

#### Scenario: Round 1 writes the evidence
- **WHEN** converge freezes a range in round 1
- **THEN** `evidence.md` stands beside `diff.patch`, `bundle.md` and `debt-cards.md`, before the first checker starts

#### Scenario: A fix is re-frozen
- **WHEN** a fix commit is re-frozen
- **THEN** `evidence.md` is rewritten for the new range, and each worker of the next round is given it

#### Scenario: A new suppression
- **WHEN** the frozen patch adds a line holding `# noqa`, `# type: ignore`, `# ty: ignore` or `# pragma: no cover`
- **THEN** the Gate integrity section holds a line naming its path and line

#### Scenario: A removed test the design names
- **WHEN** the patch removes `def test_a` and the design's `## Tests` section names `test_a`
- **THEN** the Test cost section says the removed test is named in it

#### Scenario: A path Git spaces or quotes
- **WHEN** the frozen patch changes `tests/a b/x.py`, or `café.py`, which Git quotes
- **THEN** each line names the file by that path, whichever file comes before it in the patch

#### Scenario: One test name in two classes
- **WHEN** the patch adds `TestFast.test_main`, 0.1 s in the report, and the report holds `TestSlow.test_main` of the same module at 9.0 s
- **THEN** the Test cost section gives the added test 0.10 s

#### Scenario: Nothing found
- **WHEN** a tool finds nothing for a section
- **THEN** the section reads `None.`

#### Scenario: A command past its limit at the freeze
- **WHEN** the freeze's plan check prints `plan: 1.2 — `<command>` timed out` and no other line
- **THEN** the Plan check section holds that line, Step 7 sends nothing back and raises no card, and the run goes on
- **AND WHEN** the plan check prints a timed-out line and a failed one
- **THEN** only the failed line is sent back

#### Scenario: A freeze at the head the build closed
- **WHEN** `build.done` names the frozen head and the close kept `plan-check.txt`
- **THEN** the Plan check section holds the file's lines and converge runs no `plan_check.py`
- **AND WHEN** `build.done` names another head
- **THEN** converge runs the plan check as before

### Requirement: A re-run recovers what a dead station left

A re-run of `mf-ship` SHALL finish what a dead worker or conductor left. An open merge with no note SHALL be stage
`integrate`. A version with every phase ticked, no converge run begun, and no `.minions/changes/<change-id>/build.done`
naming `HEAD` SHALL be stage `build`, its closing steps left, and SHALL fail the build check: `skills/mf-build/SKILL.md`
SHALL then run its simplify step again, restoring first, saved to a patch under `.minions/changes/<change-id>/`, a dirty
tree whose paths are all in the change's range while its `.minions/changes/<change-id>/build.closing` mark names `HEAD`, halting and
restoring nothing on a path outside it, a dirty tree with no such mark, or a patch an earlier save left; `conduct.py close` SHALL then run the gate, the metrics and the plan check again, and SHALL write `build.done`, naming `HEAD` and
simplify's outcome, only once they are done. Under `merge=yes`, `skills/mf-release/SKILL.md` SHALL restore a tree dirty with only its own fold and a staged
archive move to `HEAD`, then start over; a hand release SHALL keep its clean-tree halt. It SHALL re-enter at its merge after reading its preamble against the archived delta, halting on a flag under `merge=yes` and naming it beside the ask by hand,
tagging `HEAD` first when the tag is missing, when `HEAD` is its release commit, converge was clean at `HEAD~1` and the
default branch has not moved. `conduct.py` SHALL read that stage as `release` only when the run logs show the release
worker died and the person left no `.minions/changes/<change-id>/release.held` mark, and as `released` for any other release tip. It SHALL read `tasks.md` from `HEAD`. It SHALL, at the start of
a run, push the default branch and each merged tag `origin` lacks, only when every first-parent commit past `origin`'s default
branch, as `origin` lists it, is a merge of a tagged release holding that release's tree, whose release commit's parent is a
head the release ledger holds that is not yet on `origin`, and every such tag is on such a release commit, and SHALL else halt, naming the commit or the
tag; an `origin` it cannot read SHALL leave the push waiting, as *A run goes on while origin cannot be reached* says. It
SHALL push the sha it checked, never force, a rejected push halting the run; `status`
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
- **AND** the run converges only after `.minions/changes/<change-id>/build.done` names `HEAD`

#### Scenario: A dirty tree the build did not mark
- **WHEN** every phase is ticked, no `.done` names `HEAD`, and the tree is dirty with no `.closing` mark naming `HEAD`
- **THEN** `mf-build` halts naming the dirty paths, and restores nothing

#### Scenario: A resume finds an earlier patch
- **WHEN** a resume finds the tree dirty while `.closing` names `HEAD`, and `.minions/changes/<change-id>/build.discarded.patch`
  already exists
- **THEN** `mf-build` halts naming the dirty paths and the patch, restores nothing, and leaves the patch as it was

#### Scenario: A build exits without its marker
- **WHEN** a build worker exits 0 with every phase ticked and committed, and no `.done` names `HEAD`
- **THEN** the build check fails, the version halts, and no second build starts

#### Scenario: A build closed before this rule
- **WHEN** a version's phases are all ticked, its converge has begun, and no `.minions/changes/<change-id>/build.done` exists
- **THEN** the stage is read from converge's status log, as before

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
marked `**CORPUS**` names a case `scripts/corpus.toml` does not hold. Without `--only` it SHALL NOT run again a `**HALT CHECK**`
sub-task's command; with or without it, it SHALL NOT run again a command of a `**HUMAN` phase, or a command one of whose words has
the file name `plan_check.py`, and SHALL run no command with a shell. It SHALL exit 0 printing `plan: clean` when none holds, and
2 when it cannot read `tasks.md`, the base or git, or when `--only` names a sub-task outside a `**HUMAN` phase whose `Verify:`
holds no command.

It SHALL read a `Verify:`'s spans as follows: a span whose word right before it is an output verb — `prints`, `exits` and the
like — is output, never a command, and so is each later span until a `then`, a `;`, the sentence's end or a `Verify:` label; a
`, and` or `, or` before a span that a verb follows opens a new command. No other word SHALL open output: a span with words
between an output verb and it, and no span between them, is a command. A command whose `Verify:` says it
`` exits `<N>` `` SHALL pass only on exit `<N>`, and on the output the `Verify:` says; the search that passes on exit 1 is the one
whose `Verify:` names no exit. It SHALL run each command without `VIRTUAL_ENV` in its environment, SHALL compare a command's stdout
alone with what the `Verify:` says, keeping its stderr apart, and SHALL show the first lines of both on a failure.
`skills/mf-cut-change/scripts/verify_check.py` SHALL read a `Verify:`'s commands through this script's parser, loaded
from it, and keep no parser of its own.

It SHALL run each distinct command once a check, whatever the number of sub-tasks that name it, and hold the one result to each
sub-task's own words. It SHALL run the commands side by side, one slot for each core the machine has, and print the lines in
task order, then command order, whatever order they finish in: a `pytest` with `-n` takes every slot and runs alone, a `make`
runs one at a time, and every `pytest` starts with `-p no:cacheprovider` in its `PYTEST_ADDOPTS`. It SHALL start a command only
while the machine's 1-minute load is under its core count, and SHALL start one whatever the load when no command runs. A command
past its limit — the integer after `**Verify timeout:**` in the root `AGENTS.md`, in seconds and at most a day, else 600 — SHALL lose its whole
process group and print `plan: <sub-task> — `<command>` timed out`; ended by SIGTERM, the check SHALL end the
process group of each command then running. A `pytest` command — one whose argv starts `pytest`, `uv run pytest` or `python -m pytest` — whose `Verify:` says nothing of its
output beyond that it exits 0, and whose words after its pytest prefix are only `-q`, `-v`, `-x` or `-s` flags and test paths
and `::` nodes that exist, SHALL pass unrun when `gate_run.py` holds a green record for the same tree and the same dry run of
`make -n gate` and the command's own collection finds a test; one that says what it prints, selects with `-k`, `-m` or `--deselect`, or carries another option still runs. On a settled tree the check SHALL keep each finished result — its exit, stdout and stderr — in
`.minions/plan-check/<tree>/`, named by the command, `HEAD` and every ref, and SHALL read it again on the same tree while
`HEAD` and every ref stand, whatever the command's words; a timed-out command SHALL be kept by no one, a result kept without its
stderr SHALL be read as none kept, and an unsettled tree
SHALL keep and read none. With
`--only <sub-task ids>` it SHALL run the `Verify:` commands of those sub-tasks alone, ticked or not, a `**HALT CHECK**` sub-task
it names included, with the other skips, print only their lines and check nothing else.

`conduct.py close` SHALL run it at the build's close, after the metrics and before `build.done`, its `--base` the sha `stacked-on` names while it stands and else the merge base of the default branch
and `HEAD`, and SHALL halt on any other exit than 0, writing no `build.done`. Converge's fixer SHALL run it in the foreground after
its gate and before its commit, clearing each problem as a blocking card of the same pass, or setting it `wontfix` naming the
amend; converge's Step 7 SHALL run it after `gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any
verify worker, counting no round, save a line that says a command timed out, which it SHALL send back to no one; a line the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the
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

#### Scenario: Words between the verb and the span
- **WHEN** a ticked `Verify:` says that `printf 1` prints one integer, a space and `pyproject.toml`
- **THEN** `printf 1` and `pyproject.toml` are both commands, and `plan_check.py` reports the second
- **AND WHEN** it says that `printf 1` exits `0`, and `printf 2` prints `2`
- **THEN** both commands run
- **AND WHEN** it says that `printf 1` exits `0`, then the test that holds the guard, `printf 2`, exits `0`
- **THEN** both commands run

#### Scenario: A warning on stderr
- **WHEN** a ticked `Verify:` says a command prints `1`, and the command prints `1` on stdout and a warning on stderr
- **THEN** `plan_check.py` prints no line for it
- **AND WHEN** that command exits 1
- **THEN** the line shows its stdout and its stderr

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

#### Scenario: A load over the cores
- **WHEN** the 1-minute load is over the core count and a command runs
- **THEN** the next command waits
- **AND WHEN** the load is over the core count and no command runs
- **THEN** the next command starts

#### Scenario: A limit the repository sets
- **WHEN** the root `AGENTS.md` holds `**Verify timeout:** 1800`
- **THEN** a command is ended at 1800 s
- **AND WHEN** no such line stands, or it holds `-30`
- **THEN** a command is ended at 600 s
- **AND WHEN** it holds `3000000`
- **THEN** a command is ended at a day

#### Scenario: A timed-out command's group
- **WHEN** a command starts a child, outlives its limit, and `plan_check.py` kills it
- **THEN** the child is gone too, and the line says the command timed out

#### Scenario: Only the named sub-tasks
- **WHEN** `plan_check.py --only 1.1 2.3` runs and `1.1` is unticked and `2.3` is a `**HALT CHECK**`
- **THEN** it runs the commands of `1.1` and of `2.3`, and prints a `plan: ` line for each only if it fails
- **AND WHEN** a plain check names `2.3` in no `--only`
- **THEN** the command of `2.3` does not run
- **AND WHEN** `--only 1.6` names a sub-task whose `Verify:` holds no backticked command
- **THEN** it exits 2, naming `1.6`

#### Scenario: A test file named for the script
- **WHEN** a ticked `Verify:` runs `pytest tests/test_plan_check.py`
- **THEN** the command runs, as only a command with a word of the file name `plan_check.py` is skipped

#### Scenario: A stacked close
- **WHEN** the build's close runs while `stacked-on` names a commit
- **THEN** the plan check's `--base` is that sha, and a test the dependency deleted is no test gone since the base

