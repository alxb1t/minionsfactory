## MODIFIED Requirements

### Requirement: A rescue decides by the version's switch

A version's models file MAY say `decide = "recommended"` at its top, before its tables: the **switch**, which the cut writes
from the brief. `conduct.py` SHALL read it once a run, with the version's plan, and pass it to the rescue as `decide=recommended`.
Under the switch, `skills/mf-rescue/SKILL.md` SHALL take the fix a card or the plan itself proposes as its own decision, at a build
halt and an `amend needed` halt: it MAY edit `proposal.md` and `design.md`'s `## Decisions` besides `tasks.md` and
`design.md`'s prose, and its commit SHALL carry a `Decided-by: rescue` trailer. It SHALL never edit the spec delta, code or a
test, take a security card of `critical` or `high` severity, approve a gate makefile, settle an integrate conflict, release,
merge or push, or answer a run-wide halt. `conduct.py` SHALL take an amend that touches `proposal.md` or changes `design.md`'s
`## Decisions` section only under the switch, with the trailer or without it, logging `rescue — <id>: decided · <sub-task> · <commit>`;
without the switch it SHALL refuse it, naming the decision, and, when the tree was clean at the rescue's start and is clean at the reset, and every commit
past it carries a `Rescue:` trailer, SHALL reset the branch to the commit before them and log `reset — rescue commit <sha7> dropped: <why>`.
A commit with no `Rescue:` trailer SHALL stay, as the person's. Lines of the form `Fix note (<YYYY-MM-DD>, <card id>): <text>` that
end a `### D<n>` entry, added or edited, SHALL be no change to that section; any other edit of the entry, its `### D<n>` body included, SHALL be one, each run of
whitespace read as one space, so a re-indented or re-wrapped line is no change and a reworded one is. The
run's closing line, and its `done` line, SHALL name
` · decided <ids>` when a rescue decided, `report` SHALL print a line for each decision, and the run's metrics SHALL count them as `rescues-decided`.

#### Scenario: A decided amend
- **WHEN** a version's models file says `decide = "recommended"`, and its rescue at `amend needed` commits an edit to a row of
  `design.md`'s `## Decisions` with `Decided-by: rescue`
- **THEN** the run takes it, logs `rescue — <id>: decided`, the version converges again, and `report` and the closing line name it

#### Scenario: A decided amend with no trailer
- **WHEN** the models file says `decide = "recommended"`, and the rescue commits an edit to a row of `design.md`'s `## Decisions`
  with a `Rescue:` trailer and no `Decided-by: rescue`
- **THEN** the run takes it, logs `rescue — <id>: decided`, and the version goes on

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue commits the same amend
- **THEN** the run refuses it, naming the decision, the refused commit is no longer at `HEAD`, the run logs `reset`, and the
  version stays halted

#### Scenario: No switch and a person's amend
- **WHEN** the models file has no `decide`, and a commit with no `Rescue:` trailer lands past the rescue's start
- **THEN** the run resets nothing, and the commit goes on as the person's

#### Scenario: No switch and a tree with other changes
- **WHEN** the models file has no `decide`, the tree held a change of the build's before the rescue started, and the rescue
  commits a refused amend
- **THEN** the run refuses it, naming the decision, resets nothing, and the version stays halted

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

### Requirement: The conductor runs the gate of a build

`conduct.py` SHALL run the full gate, as `skills/mf-converge/scripts/gate_run.py` under the sandbox runner over the version's trees, after the last phase's check passes and in the close, and SHALL log each gate it runs as a `check` event of the run log: `check — gate · pass · <n>s`, or `check — gate · fail — <why>`. A red gate after the last phase SHALL write the gate's output to `.minions/changes/<change-id>/gate.red` and start one build worker, once a run, naming `phase=repair`, on the last phase's models; the gate SHALL then run again, and a second red SHALL halt the version `gate red after the repair`, writing `build.halt` with `sub-task: repair`. `gate_run.py` SHALL read a gate that runs past its limit as red: it SHALL print `gate: red — past its limit · <seconds>s` and exit 124, never a traceback. A repository with no `check` target SHALL keep its workers on the gate through `gate_run.py`, and the conductor's gate SHALL take that record on the same tree.

A conductor gate that is red while the 1-minute load, read at once, is at or over the machine's core count SHALL wait: it SHALL log `wait — gate · load <n> over <cores> cores`, poll the load, and when it falls under the core count, or after `1,800` seconds, log `wait — gate · load <n> · <seconds>s` and run the gate once more. A rerun that is green SHALL be the gate's result; a rerun that is red, and a load that never fell, SHALL leave the red it was. Each gate run the conductor makes SHALL wait at most once, apart from the repair's rerun and the rerun after a dropped simplify commit, and a machine that gives no load SHALL read as a load of none.

#### Scenario: A gate red after the last phase, green after the repair
- **WHEN** the last phase's check passes and the conductor's gate is red, and the repair worker commits a fix
- **THEN** `gate.red` holds the gate's output, one worker naming `phase=repair` runs on the last phase's models, and the gate runs again green

#### Scenario: A gate red twice
- **WHEN** the gate is red after the repair worker's commit
- **THEN** the version halts `gate red after the repair`, `build.halt` names `sub-task: repair`, and no second repair worker starts

#### Scenario: A gate past its limit
- **WHEN** `make gate` runs past `GATE_SECONDS`
- **THEN** `gate_run.py` prints `gate: red — past its limit · <seconds>s` and exits 124

#### Scenario: A gate red under load, green after the wait
- **WHEN** the conductor's gate is red, the load is over the core count, and it falls before `1,800` seconds
- **THEN** the run logs the wait's two lines, runs the gate once more, and the gate's result is the rerun's green

#### Scenario: A gate red twice under load
- **WHEN** the rerun after the wait is red
- **THEN** the gate is red, and the repair worker or the halt follows as for any red gate

#### Scenario: A gate red under a low load
- **WHEN** the conductor's gate is red and the load is under the core count
- **THEN** no wait is logged and no rerun runs

#### Scenario: A load that never falls
- **WHEN** the conductor's gate is red and the load stays over the core count for `1,800` seconds
- **THEN** the run logs the wait's second line, runs no rerun, and the gate is red

### Requirement: A Codex checker falls back to Claude while Codex is limited

Before a converge checker on Codex spawns, `conduct.py` SHALL count Codex limited while a recorded limit holds, or while the
newest rollout file's last `rate_limits` shows the 5-hour window or the weekly window at 90% or more with its `resets_at` still
ahead. A limit whose
reset is at most 15 minutes away and before converge's deadline SHALL be waited for, then Codex probed if it is unprobed, and
the checker run on Codex; any other limit SHALL run the checker on Claude with converge's model and effort, starting no Codex
worker. A Codex checker that exits on a usage limit SHALL record the limit and go through the same rule once more, ending on
Claude when it does not wait. A Codex checker that exits non-zero before a completed turn, whatever the reason — a refused model, a failed start or an
expired subscription among them — SHALL run once more, and a second such exit SHALL run it on Claude with converge's model and effort; the checker call counts
those exits and tells no usage limit from another failure. A fallen-back checker's result SHALL name `fallback: codex usage limit` when a run of it ended on a limit and
`fallback: codex failed` otherwise, and `converge.py` SHALL copy that into the role's `verdicts` line. A shadow checker
on Codex SHALL not fall back: while Codex is limited it SHALL result exit 1 naming the limit, start no worker and halt nothing, and after two failures it SHALL result exit 1 naming
the failure.

#### Scenario: A checker meets the limit
- **WHEN** a converge conformance checker on Codex exits on a usage limit whose reset is two hours away
- **THEN** `conduct.py` runs it again on Claude with converge's model and effort, its `verdicts` line names
  `executor claude` and `fallback: codex usage limit`, and the version does not halt

#### Scenario: A checker fails twice
- **WHEN** a converge conformance checker on Codex exits non-zero twice, each before a completed turn, for a reason that is no usage limit
- **THEN** `conduct.py` runs it on Claude with converge's model and effort, its `verdicts` line names `executor claude` and
  `fallback: codex failed`, and the version does not halt

#### Scenario: A checker fails once
- **WHEN** a converge conformance checker on Codex exits non-zero once, and its second run completes a turn
- **THEN** the checker's result is the second run's, on Codex, and names no fallback

#### Scenario: The window is nearly spent
- **WHEN** the newest rollout shows the 5-hour window at 92% with its reset two hours away, and a Codex checker is to run
- **THEN** the checker runs on Claude, and no Codex worker starts
- **AND WHEN** that reset is ten minutes away
- **THEN** `conduct.py` waits for it, then runs the checker on Codex

#### Scenario: The weekly window is nearly spent
- **WHEN** the newest rollout shows the weekly window at 98% with its reset days away and the 5-hour window at 10%, and a Codex checker is to run
- **THEN** the checker runs on Claude, and no Codex worker starts

#### Scenario: A shadow while Codex is limited
- **WHEN** a shadow checker on Codex is to run while Codex is limited
- **THEN** it results exit 1 naming the limit, no worker starts, and converge goes on

### Requirement: The integrate station resolves mechanical conflicts by fixed rules

`skills/mf-integrate/scripts/integrate.py` SHALL keep the branch's own `## [Unreleased]` entries of `CHANGELOG.md` above
the default branch's released sections with their blank lines — those past the base's entries, which a stacked branch's base
holds and the default branch has released. A base entry the branch's entries do not lead with SHALL be dropped from where
the branch holds it when a released section of the default branch holds the same line, and held by none; a base entry that no
released section of the default branch holds, and that the branch's entries do not lead with, SHALL halt the rule. It SHALL
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

#### Scenario: A stacked branch that lost the base's entries
- **WHEN** a stacked branch's `[Unreleased]` entries lack the base's entries, and the default branch released them
- **THEN** `changelog` keeps the branch's own entries above the release section, and exits 0

#### Scenario: A base entry the default branch never released
- **WHEN** a stacked branch's `[Unreleased]` entries lack an entry of the base that no released section of the default branch holds
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

### Requirement: `conduct.py wait` blocks until the run ends

`conduct.py wait` SHALL print `wait: none — no run is live` and exit 0 when no claim is live. With a live claim it SHALL poll the claim every `WAIT_SECONDS` seconds, make no read of `origin` at a poll, and print at each poll the whole lines the newest run log gained since the wait began or the previous poll, read from its offset through the log kept open across the polls of one log, at most `262,144` bytes a poll, then `wait: live · +<n> lines`, `<n>` the lines it just printed, 0 for none. A line longer than that SHALL be passed over whole, nothing of it printed, its tail included. A newer log SHALL be read from its start, and a link or a file that is no regular file SHALL never be read. When the claim is gone or stale it SHALL print `wait: ended` and `status`'s lines, and exit 0, whatever the run's close: a run that halted ends the wait as a run that is done does.

`conduct.py wait --halt` SHALL end at the first poll that prints a line `<id> · halt — final — needs <action> · <reason>`, which a version's thread writes when it ends with a halt standing, no rescue or supervisor left to start: it SHALL print `wait: halt — <id> · <reason>` and `status`'s lines, and exit 1. A run that ends with no such line SHALL end the wait as without the flag, exit 0.

#### Scenario: No run
- **WHEN** no run is live
- **THEN** `wait` prints `wait: none — no run is live` and exits 0

#### Scenario: A run that ends
- **WHEN** a run is live at the first poll, its log gains two lines, and its claim is gone at the next
- **THEN** `wait` prints the two lines, `wait: live · +2 lines`, then `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A run that halts
- **WHEN** a run's log ends in a halt and its claim is gone
- **THEN** `wait` prints `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A halt nothing answers
- **WHEN** `wait --halt` polls a live run whose log gains `<id> · halt — final — needs a fix · <reason>`
- **THEN** it prints the line, `wait: halt — <id> · <reason>` and `status`'s lines, and exits 1 with the run still live

#### Scenario: A halt a rescue still answers
- **WHEN** `wait --halt` polls a live run whose log gains a version's `halt` line with no `final` in it
- **THEN** it prints `wait: live · +<n> lines` and goes on

#### Scenario: A run that ends under the flag
- **WHEN** `wait --halt` polls a run that ends with no `final` line
- **THEN** it prints `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A poll with no new line
- **WHEN** the run's log gains nothing between two polls
- **THEN** `wait` prints `wait: live · +0 lines` at the second

#### Scenario: A poll reads no origin
- **WHEN** `wait` polls a live run
- **THEN** no remote git call is made until the one `status` makes at the end

#### Scenario: A newer log that is a link
- **WHEN** a worker plants a newer `<stamp>.md` that is a link during a live wait
- **THEN** `wait` prints nothing from it

#### Scenario: A log grown past the bound
- **WHEN** the run log gains more than `262,144` bytes between two polls
- **THEN** each poll prints the whole lines of at most that many bytes, and the rest is printed at the next polls

#### Scenario: A line past the bound
- **WHEN** the run log gains a line longer than `262,144` bytes with no newline
- **THEN** `wait` prints nothing of that line, its tail included, and prints the lines that follow it

## ADDED Requirements

### Requirement: A failed Codex checker probe leaves the checkers on Claude

When the probe of Codex for a version whose plan gives Codex to its checkers alone fails — the checker probe wrote no findings file, a file that breaks its contract, or no usage event — `conduct.py` SHALL halt nothing, SHALL run the probe no second time, SHALL mark Codex not ready for that version, and SHALL log `codex — <id>: probe failed · its checkers run on Claude`. Every checker of that version SHALL then start on Claude, with converge's model and effort, and name `fallback: codex failed`. A version with a station other than a checker on Codex SHALL halt on a failed probe as before.

#### Scenario: A checker probe that writes no file
- **WHEN** a version's checkers are on Codex, no other station is, and the checker probe leaves no `conformance.md`
- **THEN** the version does not halt, the run logs `codex — <id>: probe failed`, no second probe runs, and each checker of the version starts on Claude

#### Scenario: A Codex station
- **WHEN** a version's build is on Codex and its probe fails
- **THEN** the version halts, as before

### Requirement: A converge halt no verdict followed is run again

A converge halt that a worker's exit or timeout caused — the reason names `worker exit <code>` or `timed out after` — in a run whose status log holds no `verdicts` line, with `HEAD` at the halt's head, SHALL read as a halt before round 1: `conduct.py`'s stage SHALL be `converge`, and the run SHALL start converge again once at that head. A second such halt in the same run SHALL stay a halt, which a new run, or `rejoin`, SHALL read as a rerun again. A halt with a `verdicts` line, a `verify: halt`, a grant's halt and a usage limit's halt SHALL stand as they do.

#### Scenario: A checker's exit
- **WHEN** converge halts `converge-conformance-r1 worker exit 1` before any `verdicts` line, at the head `HEAD` still is
- **THEN** the run's stage for the version is `converge`, converge starts again once, and the version goes on when it is clean

#### Scenario: A second exit
- **WHEN** the rerun halts on a worker's exit at the same head
- **THEN** the version stays halted for the run
- **AND WHEN** a new run reads it
- **THEN** its stage is `converge` again

#### Scenario: A halt after a verdict
- **WHEN** converge halts on a worker's exit in a run whose status log holds a `verdicts` line
- **THEN** the stage stays `converge-halted`

### Requirement: A verdict that misses the freeze's scope is sent out once more

A findings file whose `files` or `commits` is under the freeze's SHALL send that checker out once more, on the same station and prompt, before it halts: converge SHALL stamp `fan-out — rescope — <role>: <why>` and read the file again. A second miss SHALL halt `<file> is not clean: its scope resolved <counts> of the freeze's <counts>`, as before.

#### Scenario: A scope that misses once
- **WHEN** a checker's findings file resolves 9 files of the freeze's 10, and its second run resolves all 10
- **THEN** converge stamps `fan-out — rescope`, reads the second file, and goes on

#### Scenario: A scope that misses twice
- **WHEN** the second file resolves 9 files of 10 too
- **THEN** converge halts, naming the scope

### Requirement: A converge by hand reads the models file

`conduct.py converge <change-id>` SHALL read the version's models file for each checker's and the fixer's models, and for a checker's skip, as a run reads it, and SHALL let each `<role>=<model>/<effort>` and `<checker>=skip` argument replace the file's value for that role. With no models file, or none for a role, it SHALL take the executor's default as before.

#### Scenario: A models file
- **WHEN** the version's models file names `claude-sonnet-5-5` for `[converge.conformance]` and no argument names conformance
- **THEN** the hand converge's conformance checker runs on `claude-sonnet-5-5`

#### Scenario: An argument over the file
- **WHEN** the file names `claude-sonnet-5-5` for conformance and the command line says `conformance=claude-opus-5-5/high`
- **THEN** the checker runs on `claude-opus-5-5` at `high`

#### Scenario: No file
- **WHEN** the version has no models file
- **THEN** each role takes the executor's default, as before

### Requirement: A supervisor re-plans a design-sized cap once

Under a version's switch, when its converge halts `cap reached` and its last halt line reads `re-plan: <ids>` with an open blocker sized `a design change`, and the version has no `replan.mark` in its folder of the run directory, `conduct.py` SHALL start the supervisor after the rescue's diagnosis, with `replan=yes` in its prompt. The supervisor MAY amend `design.md`'s `## Decisions` and `proposal.md` besides the rest of the change directory, its commit carrying the `Supervisor:` and `Decided-by: supervisor` trailers, and the run SHALL write `replan.mark` when it takes the commit, log `supervise — <id>: decided · converge-halted · <commit> · re-plan`, and let one amend round follow, with no grant spent. A cap with the mark standing, a cap whose blockers include a security card of `critical` or `high` severity, and a second cap SHALL be the person's. The run's closing line, and its `done` line, SHALL name ` · re-planned <ids>`.

#### Scenario: A design-sized cap under the switch
- **WHEN** a version caps with a blocker sized `a design change`, its rescue diagnoses the halt, and the supervisor commits an amend of `design.md`'s `## Decisions` with both trailers
- **THEN** the run writes `replan.mark`, logs `re-plan`, converge runs one amend round, and the closing line names ` · re-planned <id>`

#### Scenario: A second cap
- **WHEN** the amend round caps again with a blocker sized `a design change`
- **THEN** no supervisor starts, and the version stays halted for the person

#### Scenario: No switch
- **WHEN** the models file has no `decide` and a version caps with a blocker sized `a design change`
- **THEN** no supervisor starts and no mark is written

#### Scenario: The mark from an earlier run
- **WHEN** a new run meets a design-sized cap of a version whose folder holds `replan.mark`
- **THEN** no supervisor starts
