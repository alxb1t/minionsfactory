## ADDED Requirements

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
`inconclusive`, and each card's `Amend:` field, in place of the prose the conductor read before; a file without them SHALL be
malformed. The status log's events and their text SHALL stay as before.

The script SHALL go on where it can: a worker that exits non-zero or leaves no file SHALL get one fresh retry; a malformed
findings file SHALL get one rewrite worker, then a debt card for it, and the run SHALL go on; a fixer whose gate is red or whose tree
is dirty SHALL get one more fix pass, then the halt `cap reached`; `debt_match.py` or `replay` exiting 2 SHALL leave an empty
`debt-cards.md` or send a worker round; the debt lock SHALL be waited for 10 minutes. The environment, a loop outcome, a gate that
stays red and a security card SHALL still halt.

#### Scenario: A version converges with no conducting worker
- **WHEN** a run takes a built version to converge on the fake hosts
- **THEN** the hosts see no converge station call, and each worker's log is
  `.minions/changes/<change-id>/logs/<stamp>-converge-<role>-r<N>.log`
- **AND** the status log holds the same events, in the same text, as a converge by the skill held

#### Scenario: A malformed findings file
- **WHEN** a checker's findings file lacks `passes`, or holds a card with no `Amend:` field
- **THEN** one rewrite worker is started for it, and a file still malformed becomes one debt card and no halt

#### Scenario: A worker exits 1
- **WHEN** a checker exits 1 or leaves no findings file
- **THEN** one fresh worker is started for that role, and a second failure halts the version, naming the role

#### Scenario: A prose check
- **WHEN** a non-blocking card's **Still true?** holds no command in backticks
- **THEN** the card goes to the debt unchecked, and no command runs for it

#### Scenario: A check command writes outside the trees
- **WHEN** a card's **Still true?** command tries to write a file outside the worktrees
- **THEN** the sandbox denies it, the card goes to the debt unchecked, and nothing is written outside

#### Scenario: By hand
- **WHEN** a person runs `conduct.py converge <change-id> fix=claude-sonnet-5-5/medium` in a version's worktree
- **THEN** the same script runs, the fixer on that model, and the exit is the version's converge check

### Requirement: A converge worker is booked by its log name

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL book each log named `<stamp>-converge-<role>-r<N>.log`, or
`<stamp>-converge-<role>-r<N>-<n>.log` for a repeat of the spawn, with `<role>`
one of `conformance`, `adversarial`, `fix`, `verify-conformance`, `verify-adversarial` and `verify-pickup`, as one worker of that
role and round `N`, its tokens the log's, and SHALL keep booking an older converge log's subagents by their descriptions. A log name
of another form SHALL be booked to no role, as a gap.

#### Scenario: A fixer is booked to the fixer
- **WHEN** a change's logs hold `20261109-101500-converge-fix-r2.log`
- **THEN** `review_metrics.py` books one worker to the role `fix`, round 2, its tokens read from the log

#### Scenario: A log of another form
- **WHEN** a log is named `20261109-101500-converge-extra.log`
- **THEN** it is booked to no role, as a gap

## MODIFIED Requirements

### Requirement: Converge keeps a status log

`skills/mf-converge/scripts/converge.py` SHALL write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. One `stamp.py` call MAY write several events, each its
own line, inserted so the last given is on top; the script SHALL write in one call the events it has with no command
between them. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `shadow`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor, model and effort the checker's spawn names, `default` where none, and `tokens` its log's
figure or `unavailable`, then ` · fallback: codex usage limit` when the checker fell back. A
`shadow` line SHALL hold `overlap.py`'s line, or a shadow checker's failure. The log SHALL NOT be a findings file: no station writes
it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `converge.py` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: Several events in one call
- **WHEN** `stamp.py` is given the events `round 1 · verdicts — conformance …` and `round 1 · verdicts — adversarial …`
- **THEN** the log holds both lines under the latest heading, adversarial's on top, each with the clock's time

#### Scenario: A round's verdicts
- **WHEN** a round's conformance and adversarial files are read, each written by its worker
- **THEN** the log holds one `verdicts` line for each role, each naming the executor, and the model and effort that role's
  worker was given

#### Scenario: A mailbox checker's verdicts
- **WHEN** conformance ran as a Codex checker the run started itself, no mailbox standing, `gpt-6.1-sol` at `high`
- **THEN** its `verdicts` line ends `executor codex · model gpt-6.1-sol · effort high` and its log's tokens

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** a verify round follows a fix that touched no path of the threat model's `## Surfaces`
- **THEN** the round's `fan-out` names both checkers, and the log holds one `verdicts` line for each, and no `by rule` line

### Requirement: A station's executor comes from the models file

`.minions/changes/<change-id>/models.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own — each station's, each checker table's, and
each shadow checker's under `shadow = true`; a failed probe at the start SHALL stop the run, and one for a joining version
SHALL halt only the versions on its executor; a probe a usage limit stopped SHALL halt only the versions with a station on its
executor.
A station on Codex SHALL report each denial, its usage limit with the reset time, its tokens and its priced cost from its JSON
event log, as a station on Claude does from its own; converge's per-role tokens SHALL be read from each converge worker's own
log, on either host.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its checkers run as `codex exec` unless a table names another executor, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A checker's executor is probed
- **WHEN** a run's only Codex table is a version's `[converge.adversarial]`
- **THEN** the run probes Codex before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A Codex worker is refused a command
- **WHEN** a Codex worker's command fails with the sandbox's `Operation not permitted`
- **THEN** the run log holds a `denied` line naming the command, and the report lists it

#### Scenario: A Codex worker meets its usage limit
- **WHEN** a Codex station's worker exits 1 after a failed turn whose error names its usage limit and a time to try again
- **THEN** its version halts with `stopped by a usage limit · resets <time>`
- **AND WHEN** the worker is a converge checker
- **THEN** it runs again on Claude, and its version does not halt

### Requirement: The converge fixer leaves the plan to the person

The converge fixer, whose rules `skills/mf-converge/references/fix.md` holds, SHALL NOT edit the change's `tasks.md`, nor its
`design.md` save the prose a `drift` card names outside the `## Decisions`, `## Tests` and `## Dependencies` sections, which it
SHALL correct; it SHALL NOT edit those sections, a row of their tables, a decision's D-id or a `## ` heading, save one line it MAY
append as the last line of a `### D<n>` entry of the decisions section,
`Fix note (<YYYY-MM-DD>, <card id>): <one line>`, recording how the code now implements that decision, the entry's other lines
untouched. A card whose fix that line records SHALL be no amend card, and converge's close-out SHALL name each fix note the run
appended, by its D-id and card. A card whose fix needs any other edit of those SHALL be set `wontfix`, naming the amend the
person commits by the file's path: an **amend card**, which a checker marks `Amend: yes` and any other card `Amend: no`. A
checker SHALL mark `Amend: yes` a card whose **Fix** names the change's `tasks.md` or `design.md` by path, save a `drift` card's
naming that prose or a fix note. A blocking amend card SHALL halt the round `amend needed — <card ids>` after the fix pass. The
verify pass SHALL keep an amend card's `wontfix` whose justification holds, and SHALL NOT turn it `accepted`; in an amend
round, it SHALL turn an amend card the amend settled, its **Still true?** check showing the defect gone, `verified`, its note
naming the amend. At the debt write,
before the debt lock, every non-blocking amend card left `wontfix`, or `open` and `drift`, whose **Still true?** command still shows
the defect, SHALL halt the run `amend needed — <card ids>`, writing nothing to the debt, save one *Converge keeps deferred work
in one repository debt file* lets go on; a card whose **Still true?** holds no command SHALL go to the debt unchecked. The person's
amend answers either halt.
The fixer SHALL run `plan_check.py` after its gate, as *A plan check holds the plan to the built tree* says, and SHALL write
`.minions/changes/<change-id>/fix.md` with a last line `plan check left: <subjects>` or `plan check left: none`, which
`converge.py` reads in place of the fixer's report. A verify round and the pickup check SHALL run `gate_check.py` after the gate,
and a verify round SHALL then run `plan_check.py`.

#### Scenario: A fix that needs a `Verify:` changed
- **WHEN** a blocking card's fix needs a task's `Verify:` edited
- **THEN** the fixer edits neither file, sets the card `wontfix` naming the amend, the card reads `Amend: yes`, and the round halts
  `amend needed`

#### Scenario: Drift in the design's prose
- **WHEN** the pickup picks a `drift` card whose **Fix** names a line of the change's `design.md` outside its `## Decisions`,
  `## Tests` and `## Dependencies` sections
- **THEN** the fixer corrects that line and sets the card `fixed`; it reads `Amend: no`, and the debt write halts on nothing for it

#### Scenario: Drift in the design's tests section
- **WHEN** a `drift` card's **Fix** names a row of the change's `design.md` `## Tests` table
- **THEN** the fixer edits no row of it, sets the card `wontfix` naming the amend, and the card reads `Amend: yes`

#### Scenario: A fix that changes how a decision is built
- **WHEN** a card's fix changes how the code implements the change's D3, and D3's own words still hold
- **THEN** the fixer appends `Fix note (<date>, <card id>): <how the code now does it>` as the last line of D3's entry, edits no
  other line of it, and sets the card `fixed`
- **AND** converge's close-out names D3 and the card

#### Scenario: Drift that needs the design amended
- **WHEN** the pickup's fixer sets a `drift` card `wontfix`, naming an amend of a decision in the change's `design.md`
- **THEN** the pickup check keeps it `wontfix`, and the debt write halts `amend needed — <its id>`, writing no card to the debt
- **AND WHEN** a `drift` card found after the pickup names the same amend in its **Fix**
- **THEN** the debt write halts on it too

#### Scenario: An amend card the check shows gone
- **WHEN** an amend card's **Still true?** command shows the defect gone at the debt write
- **THEN** it is moot, and halts nothing

#### Scenario: An amend card the amend settled
- **WHEN** a blocking amend card halted `amend needed`, and the person's amend makes its **Still true?** check show the defect gone
- **THEN** the amend round's verify pass turns it `verified`, naming the amend, and the round can end clean

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version), and the time a dependent waits on its `after:` ids (each `wait` event of the version until its next event in
the same run, a version with none 0); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. A Codex station's tokens SHALL be the sum over its log's `turn.completed` events of their input and output tokens, and
its dollars those tokens priced by `skills/mf-review-metrics/prices.toml` under the model its log's spawn line names; a model
with no row there, or no model named, SHALL make the cost metrics a gap naming it, and SHALL leave the token metrics read. A
converge worker's log, `<stamp>-converge-<role>-r<N>.log` — a checker's, the fixer's or a verify worker's — SHALL count in the cost
and tokens of the converge stage, never in its minutes, which the run log's `converge` spawn and finish hold, and a checker's log's
tokens in that role's. The cut's `diff-lines` and `diff-files` SHALL be the
collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: A dependent's wait
- **WHEN** a version's run log holds `wait — after 0001-x` at `09:08:30` and its build spawn at `09:09:00`
- **THEN** `after-wait-minutes` reads `0.5`
- **AND WHEN** a version's run log holds no `wait` event
- **THEN** `after-wait-minutes` reads `0`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

#### Scenario: A converge on Codex
- **WHEN** a version's converge checker logs are Codex JSON logs whose spawn lines name a model the price table holds
- **THEN** `cost-usd-converge` holds their priced dollars and `tokens-converge` their summed tokens
- **AND WHEN** the price table holds no row for that model
- **THEN** `cost-usd-converge` is a gap naming the model, and `tokens-converge` is read

#### Scenario: A checker through the mailbox
- **WHEN** a version's logs hold `<stamp>-converge-conformance-r1.log`, a priced Codex log, no mailbox standing
- **THEN** `cost-usd-converge` and `tokens-converge` hold that log's dollars and tokens,
  `conformance-tokens-per-confirmed` counts its tokens, and `minutes-converge` is the run log's

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort`, and the conformance and adversarial tables an `executor`; `[converge]` stays the
checkers' default, and MAY say `shadow = true`. `[converge]` MAY say `skip = true`, and a conformance or adversarial table MAY say
`skip = true`, with no model, effort or executor: only the value `true` skips. `conduct.py` SHALL read them once with the run's plan,
and SHALL read a skip from no other place in that run, a `stage_of` or `_unjudged` read of a version's converge skip included. A
checker table with no `executor` SHALL run on converge's. It SHALL halt a version, before its worker starts, on a fixer table that
names an `executor`, an `executor` it does not know, a checker table naming `executor = "codex"` with a `claude-*` model, or a
`model` or `effort` holding anything but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later
differs, as for any station's table. `converge.py` SHALL take each worker's model from that plan, or from the hand command's
`conformance=`, `adversarial=` and `fix=`, each `<model>/<effort>` with `default` for none, and SHALL read no models file itself.
The fixer SHALL always run on `fix=`'s model, at its effort, `medium` when it names none, whatever card it is sent. A verify worker
SHALL run on its role's model at `medium`. A pickup check SHALL run on adversarial's model when a card it picks is adversarial's,
else conformance's. A role with no model SHALL run on the checkers' default, `[converge]`'s, and a skipped checker SHALL start no
worker and name no executor to probe; a version whose models file says `[converge] skip = true` SHALL name no executor of
converge or of a worker table to probe. No converge model SHALL start for a conductor: `[converge]`'s model is the checkers'
default alone. The cut SHALL write the worker
tables from the brief's `conformance`, `adversarial` and `fix` parts, each host as `executor`, and else conformance on the mid
tier · high, adversarial on the strongest tier · high, the fixer on the mid tier · medium; `[converge]` on Sonnet 5.5 · high,
where the session offers it, unless the brief names converge's model; and `shadow = true` when the brief's line ends `shadow`,
each mapped to the offered models. A brief's `skip` part SHALL be written as `skip = true` under that table, with no model or
effort, and `converge skip` as `skip = true` under `[converge]`, with no worker table.

#### Scenario: The converge prompt names each worker's model
- **WHEN** a version's models file holds `[converge.adversarial]` with `model = "claude-opus-5-5"` and `effort = "high"`, and
  `[converge.fix]` with `model = "claude-sonnet-5-5"` and `effort = "high"`, and its converge runs on Claude
- **THEN** no converge prompt names a model: the adversarial worker starts with `--model claude-opus-5-5` and `--effort high`, and
  the fixer with `--model claude-sonnet-5-5` and `--effort high`

#### Scenario: The conductor's default
- **WHEN** a version's `[converge]` names no model and no effort, a checker's table names none, and converge runs on Claude
- **THEN** the checker starts with `--model claude-sonnet-5-5` and `--effort high`, and no conducting worker starts
- **AND WHEN** `[converge]` names `model = "claude-opus-5-5"`
- **THEN** the checker starts on `claude-opus-5-5`

#### Scenario: Converge on Codex
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a worker table naming no executor
- **THEN** that worker runs on Codex, on its table's model and effort, else on `[converge]`'s

#### Scenario: A checker on another host
- **WHEN** `[converge.conformance]` names `executor = "codex"` and converge runs on Claude
- **THEN** conformance runs as `codex exec` with its table's model and effort, and the fixer runs on Claude

#### Scenario: A skipped checker
- **WHEN** `[converge.adversarial]` says `skip = true`, and `[converge.conformance]` names `executor = "codex"`
- **THEN** no adversarial worker starts, its findings file is the stub, and conformance runs on Codex
- **AND WHEN** `[converge.conformance]` names no executor and `[converge.adversarial]` names `executor = "codex"` beside its `skip = true`
- **THEN** no Codex probe runs for the version

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
- **WHEN** converge sends the fixer a blocking card, adversarial running on Claude
- **THEN** the fixer runs on `[converge.fix]`'s model, at its effort
- **AND WHEN** it sends the fixer only non-blocking cards
- **THEN** the fixer runs on the same model and effort

#### Scenario: A planted skip waits for the next run
- **WHEN** a worker writes `skip = true` under `[converge]` after the run read its plan
- **THEN** that run's stage reads of the version ignore it, and it takes effect at the next run

### Requirement: A shadow round 1 runs the other host's checkers

Under `[converge] shadow = true`, round 1 of a converge run that is neither catch-up nor amend SHALL also run
`shadow-conformance` and `shadow-adversarial` through the run's checker call, on the same freeze, each with its role's packet and
reference. Each SHALL run on the executor its role's checker does not, with `[converge]`'s model and effort when converge runs on
that executor, else that executor's default, and SHALL write `.minions/changes/<change-id>/shadow-<role>.md`. A shadow file
SHALL drive no fix, no verdict, no debt card and no release check, and a shadow checker that fails SHALL halt nothing.
`skills/mf-converge/scripts/overlap.py <change-folder>` SHALL match round 1's cards of each role with its shadow's by the
`path:line` spans of their **What it affects**, and print each role's shared cards, each side's own and the blockers among
them; `converge.py` SHALL write its line as the round's `shadow` event.

#### Scenario: A shadow round
- **WHEN** a version's models file says `shadow = true` and its checkers run on Codex
- **THEN** round 1 writes `shadow-conformance.md` and `shadow-adversarial.md`, each `executor: claude`, and the status log
  holds a `shadow` line counting shared and unique catches
- **AND WHEN** a shadow file holds an open blocking card
- **THEN** no fixer is sent it, and the version's converge check passes on its clean conformance and adversarial files

#### Scenario: Two catches of one line
- **WHEN** a conformance card names `total.py:12` and a shadow conformance card names `total.py:14`, and another shadow card
  names `README.md`
- **THEN** `overlap.py` counts one shared card and one card the shadow alone caught

### Requirement: A Claude worker starts with its station's tools and nothing of the operator's

`conduct.py` SHALL start each Claude station worker with `--tools` naming its station's tools: the cut `Bash`, `Read`, `Edit`,
`Write`, `Glob`, `Grep`, `Skill` and `Agent`; the probe `Bash` and `Read`; every other station, a converge worker among them,
`Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep` and `Skill`. Its `--settings` SHALL turn off
each plugin the operator's user settings enable, the operator's output style and auto-memory, and it SHALL start with
`--exclude-dynamic-system-prompt-sections`. The cut SHALL start with the 1-hour prompt cache asked for, and
every other station with the 5-minute one forced. A worker whose log shows a call to a tool its station lacks SHALL halt its
version, naming the tool, whatever its exit. The run's probe SHALL name in its check line the context of its worker's first
turn: the input, cache-read and cache-write tokens of its first assistant event, or a Codex log's first turn's input tokens.

#### Scenario: Each station's command line
- **WHEN** a run on the fake hosts spawns a version's cut, build and release on Claude, and its converge workers
- **THEN** each command line holds `--tools` with its station's tools, `--settings` with the plugins, the output style and
  auto-memory off, and `--exclude-dynamic-system-prompt-sections`
- **AND** the cut's environment asks for the 1-hour cache, and every other station's forces the 5-minute one

#### Scenario: The operator has a plugin and an output style
- **WHEN** the operator's user settings enable a plugin and name an output style
- **THEN** a Claude worker's `--settings` sets that plugin off and the default output style

#### Scenario: A worker calls a tool its station lacks
- **WHEN** a build worker's log holds a tool result `No such tool available: Agent`
- **THEN** the version halts, naming `Agent`

#### Scenario: The probe reports its first turn
- **WHEN** a Claude probe worker's first assistant event holds 3 input, 15000 cache-read and 4000 cache-write tokens
- **THEN** the probe's check line names a first turn of 19003 tokens

### Requirement: A converge conductor stubs a skipped checker

`skills/mf-converge/scripts/skip_stub.py <findings-file> <round>` SHALL write the findings file of a checker a plan skips as a
stub: the findings contract's frontmatter with `head:` the commit `git rev-parse HEAD` prints, `round:` as given, `reviewed:`
today, `open_blocking: 0`, `verdict: clean`, `mode: skipped`, `workers: 0`, `model: none`, `executor: none` and `packet:
skipped: all`, and no card. It SHALL print the line it wrote, exit 0, and exit 2 with `skip_stub: cannot stub — <why>` when the
path is a link, is not of the form `changes/<change-id>/conformance.md` or `changes/<change-id>/adversarial.md`, no repository
holds the working directory, or the path holds a checker's file that is not clean or holds a card other than `verified`. `converge.py`
SHALL start no worker for a role it is given `<role>=skip` for, and SHALL run `skip_stub.py` for that role after the freeze of
round 1, each re-freeze, a catch-up round's freeze and its by-rule write, and before its `done`, so that the stub's `head:` is
`HEAD` whenever converge ends. The script SHALL read a stub for `verdict: clean` and its `head:` alone, with no `verdicts` line. A
pickup check SHALL need the checker the plan did not skip. `conduct.py`'s readers of a findings file SHALL stay as they were: a
stub is clean at `HEAD`, holds no card, and bars no rescue or supervisor.

#### Scenario: A stub is written
- **WHEN** `skip_stub.py .minions/changes/0001-a/adversarial.md 1` runs in a repository whose `HEAD` is `abc1234…`
- **THEN** the file holds `head: abc1234…`, `verdict: clean`, `mode: skipped` and `workers: 0`, and the line it printed names the
  path

#### Scenario: A stub for a path it does not take
- **WHEN** the findings path is a link, or ends `review.md`
- **THEN** `skip_stub.py` exits 2, writes nothing, and prints `skip_stub: cannot stub — <why>`

#### Scenario: A stub over a judged file
- **WHEN** the findings path holds a checker's file that is not clean, or holds a card whose Status is not `verified`
- **THEN** `skip_stub.py` exits 2, the file is kept, and the line names what it holds

#### Scenario: A version with adversarial skipped
- **WHEN** converge runs for a version whose plan skips adversarial, and conformance finds nothing
- **THEN** `conformance.md` and the stub of `adversarial.md` are both clean at `HEAD`, `conduct.py` reads the version as
  judged, and its rescue and supervisor are barred by no security card
- **AND** the release states `adversarial: skipped`

#### Scenario: A skipped converge writes no debt and no hand read
- **WHEN** a version's plan says `converge skip`
- **THEN** no findings file, no diff patch and no debt card is written for it, and no hand read is asked for

### Requirement: A Codex checker falls back to Claude while Codex is limited

Before a converge checker on Codex spawns, `conduct.py` SHALL count Codex limited while a recorded limit holds, or while the
newest rollout file's last `rate_limits` shows the primary window at 90% or more with its `resets_at` still ahead. A limit whose
reset is at most 15 minutes away and before converge's deadline SHALL be waited for, then Codex probed if it is unprobed, and
the checker run on Codex; any other limit SHALL run the checker on Claude with converge's model and effort, starting no Codex
worker. A Codex checker that exits on a usage limit SHALL record the limit and go through the same rule once more, ending on
Claude when it does not wait. A fallen-back checker's result SHALL name `fallback: codex usage limit`, and `converge.py` SHALL
copy that into the role's `verdicts` line. A shadow checker
on Codex SHALL not fall back: while Codex is limited it SHALL result exit 1 naming the limit, start no worker and halt nothing.

#### Scenario: A checker meets the limit
- **WHEN** a converge conformance checker on Codex exits on a usage limit whose reset is two hours away
- **THEN** `conduct.py` runs it again on Claude with converge's model and effort, its `verdicts` line names
  `executor claude` and `fallback: codex usage limit`, and the version does not halt

#### Scenario: The window is nearly spent
- **WHEN** the newest rollout shows the primary window at 92% with its reset two hours away, and a Codex checker is to run
- **THEN** the checker runs on Claude, and no Codex worker starts
- **AND WHEN** that reset is ten minutes away
- **THEN** `conduct.py` waits for it, then runs the checker on Codex

#### Scenario: A shadow while Codex is limited
- **WHEN** a shadow checker on Codex is to run while Codex is limited
- **THEN** it results exit 1 naming the limit, no worker starts, and converge goes on

### Requirement: A Codex spawn records its share of the plan's windows

Each Codex worker's log SHALL end, once the worker exits, with one `mf.quota` line `conduct.py` appends, following no link:
the share of the 5-hour and the weekly window the spawn used, in percent, read from the newest rollout file before the spawn
and the spawn's own rollout after it, a window whose reset moved counting its whole use after. A spawn with no rollout SHALL
get no line. A converge checker's findings file SHALL have its `model:` stamped with the model it ran on and a `tokens:` key
with its log's tokens, written by `conduct.py` following no link. `run.py` SHALL sum a version's Codex shares as
`codex-window-5h` and `codex-window-week`, a gap when no Codex spawn of the version holds the line, and SHALL count a Codex log
with no `turn.completed` as no tokens and no dollars. `skills/mf-review-metrics/prices.toml` SHALL hold rows for
`claude-opus-5-5` and `claude-sonnet-5-5`, and a Claude converge worker SHALL be priced from them.

#### Scenario: A Codex checker's spawn
- **WHEN** a converge checker on Codex runs, the primary window at 40% before it and 43% after, the weekly at 10% and 11%
- **THEN** its log ends with an `mf.quota` line naming 3 and 1, its findings file names the plan's model and the log's tokens,
  and `codex-window-5h` reads 3 at the release

#### Scenario: A Claude worker priced
- **WHEN** a converge worker on `claude-sonnet-5-5` reads one million input tokens and writes one million output tokens
- **THEN** the review metrics price it at 12 dollars from `prices.toml`

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
`skills/mf-build/SKILL.md` SHALL run it at the build's close, after the metrics and before `build.done`, and SHALL halt on any
other exit than 0, writing no `build.done`. Converge's fixer SHALL run it after its gate and before its commit, clearing each
problem as a blocking card of the same pass, or setting it `wontfix` naming the amend; converge's Step 7 SHALL run it after
`gate_check.py`, and on exit 1 SHALL send its lines to the fixer again before any verify worker, counting no round; a line
the last fixer reported leaving, or one Step 7 already sent back, SHALL instead halt the run `amend needed — plan check:
<subjects>`, naming each line's sub-task, `path:line` or test name and never the command it quotes. `skills/mf-rescue/SKILL.md`
SHALL take that halt as a fix of the lines `plan_check.py` prints, in `tasks.md` and `design.md`'s prose.

#### Scenario: A ticked check that no longer holds
- **WHEN** at the build's close a ticked sub-task's `Verify:` command exits 1
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command, and the build halts with no `build.done`

#### Scenario: A ticked check that exits 0 with other output
- **WHEN** a ticked sub-task's `Verify:` says a search prints nothing and the search finds a match, or says `printf 1` prints
  `2`
- **THEN** `plan_check.py` exits 1, naming the sub-task and the command
- **AND WHEN** its `Verify:` says `printf 1` prints `1`, or says a `grep -c` that finds nothing prints `0`
- **THEN** that check halts nothing

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

### Requirement: A station keeps a log per spawn

`conduct.py` SHALL write each spawn's worker log to `.minions/changes/<change-id>/logs/<stamp>-<station>.log` for a change, and to
`.minions/runs/<stamp>/run_<station>.log` for the run's own probe, and a later spawn of the same station in the same stamp to
`-<n>.log`, `n` from 2, so no spawn's log overwrites another's; the newest is read by its stamp and `n`, never by the name's sort.

#### Scenario: A converge spawned twice in a run
- **WHEN** a version's converge fixer of round 1 fails and is spawned again in the same run
- **THEN** the change's `logs/` holds `<stamp>-converge-fix-r1.log` and `<stamp>-converge-fix-r1-2.log`

### Requirement: Converge keeps deferred work in one repository debt file

`skills/mf-converge/scripts/converge.py` SHALL write every non-blocking card it does not fix, whose **Still true?** check still
shows the defect, to one file, `.minions/debt.md`, under a heading for its change — save an amend card that halts, as *The
converge fixer leaves the plan to the person* says; an amend card whose id an answered `amend needed` halt logged
since the newest `round 1 · start` line named, or whose qualified id already stands in the debt, SHALL go on as every
other card. After both verdicts are
clean, and only while a round remains under the cap, it SHALL pick up this run's non-blocking cards whose fix is
sized `one line`, `a test` or `one line and a test`, and every `drift` card, and fix them. When round 1 of a run that is no
catch-up run leaves a blocking card open, its fix pass SHALL take those same cards with the blocking ones — the **round-1
pickup** — and round 2's verify round SHALL judge them all; pickup SHALL then not run again in that run. One fresh worker, the
**pickup check**, SHALL verify a pickup's fix at `medium` effort, given both findings files' open cards and the fix's own diff: on
adversarial's table when a picked card is adversarial's, else on conformance's. A pickup whose fixer commits nothing SHALL get
no pickup check. The pickup check SHALL be no round: it SHALL set both
findings files' `head:` and leave their
`round:` as it stands, and a blocking card it leaves open SHALL go to a fix and a verify round counted against the cap. It
SHALL NOT name a per-version debt file. It SHALL delete a debt card only when a verified repeat of
it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one debt file and the pickup sizes
- **WHEN** both verdicts are clean, a round remains under the cap, pickup has not run in this run, the run is not a
  catch-up round, and open non-blocking cards are sized `one line`, `a test` or `one line and a test`, or are `drift`
- **THEN** converge fixes exactly those cards and checks the fix by one pickup check

#### Scenario: A pickup check
- **WHEN** round 2 reads both files clean, and pickup picks a conformance `drift` card and an adversarial `medium` card
- **THEN** one fresh worker, on adversarial's table at `medium` effort, judges both cards against the pickup's diff
- **AND** both files' `head:` is `HEAD`, their `round:` stays 2, and no round 3 runs
- **AND WHEN** the pickup check leaves a blocking card open
- **THEN** converge sends it to a fix, and verifies in round 3

#### Scenario: Converge writes the debt
- **WHEN** the loop ends clean with non-blocking cards still not `verified`
- **THEN** converge writes each one whose **Still true?** check still shows the defect, and whose id is not yet in
  the debt, to `.minions/debt.md` under its change's heading, and to no per-version file
- **AND** it names each moot card, whose check shows the defect gone, in its report
- **AND** it deletes an older card only when a verified repeat of it fixed the defect and its **Still true?**
  check shows the defect gone

#### Scenario: An amend card after its amend
- **WHEN** Step 9 finds an amend card whose **Still true?** check still shows the defect, and an answered `amend needed` halt
  logged since the newest `round 1 · start` line named its id, or its qualified id already stands in the debt
- **THEN** converge writes it to the debt unless its id is there already, and halts nothing
- **AND WHEN** a catch-up run's Step 9 finds an amend card still true that no answered halt logged since the newest
  `round 1 · start` line named and the debt does not hold
- **THEN** it halts `amend needed — <its id>`

#### Scenario: A round-1 pickup
- **WHEN** round 1 leaves one blocking card open and two non-blocking cards sized `one line`
- **THEN** one fix pass takes all three, and round 2's verify round judges all three
- **AND WHEN** round 2 reads both files clean
- **THEN** no pickup runs, and converge goes on to the debt

#### Scenario: A pickup that commits nothing
- **WHEN** the pickup's fixer sets every picked card `wontfix` and commits nothing
- **THEN** no pickup check runs, and converge goes on to the debt

## REMOVED Requirements

### Requirement: A fix that reaches no surface takes its adversarial head by recomputation

**Reason**: the adversarial head by rule never fired — 0 of 25 rounds — and its recomputation was the conductor's. Every fix is
verified by the checkers the plan keeps.

**Migration**: none. `THREAT_MODEL.md`'s `## Surfaces` stays for the cut's warning, and `skills/mf-converge/scripts/surfaces.py`
is deleted.

### Requirement: A converge checker on another host runs through the mailbox

**Reason**: the mailbox existed because a sandboxed LLM conductor could not start Codex. The conductor is a script outside any
sandbox and starts each checker itself.

**Migration**: see *Converge's conductor is a script* and *Converge's workers take their models from the models file*; a checker's
findings file still names its `executor:`, and the fixer runs on `fix=`'s model.

### Requirement: A converge worker's description names its role and round

**Reason**: no converge Agent call is left to describe: each worker is a spawn whose log names its role and round.

**Migration**: see *A converge worker is booked by its log name*.
