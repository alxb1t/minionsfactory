## ADDED Requirements

### Requirement: A Claude worker starts with its station's tools and nothing of the operator's

`conduct.py` SHALL start each Claude station worker with `--tools` naming its station's tools: the cut and converge
`Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Skill` and `Agent`; the probe `Bash` and `Read`; every other station,
a mailbox checker among them, `Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep` and `Skill`. Its `--settings` SHALL turn off
each plugin the operator's user settings enable, the operator's output style and auto-memory, and it SHALL start with
`--exclude-dynamic-system-prompt-sections`. The cut and converge SHALL start with the 1-hour prompt cache asked for, and
every other station with the 5-minute one forced. A worker whose log shows a call to a tool its station lacks SHALL halt its
version, naming the tool, whatever its exit. The run's probe SHALL name in its check line the context of its worker's first
turn: the input, cache-read and cache-write tokens of its first assistant event, or a Codex log's first turn's input tokens.

#### Scenario: Each station's command line
- **WHEN** a run on the fake hosts spawns a version's cut, build, converge and release on Claude
- **THEN** each command line holds `--tools` with its station's tools, `--settings` with the plugins, the output style and
  auto-memory off, and `--exclude-dynamic-system-prompt-sections`
- **AND** the cut's and converge's environment asks for the 1-hour cache, and the build's and the release's force the
  5-minute one

#### Scenario: The operator has a plugin and an output style
- **WHEN** the operator's user settings enable a plugin and name an output style
- **THEN** a Claude worker's `--settings` sets that plugin off and the default output style

#### Scenario: A worker calls a tool its station lacks
- **WHEN** a build worker's log holds a tool result `No such tool available: Agent`
- **THEN** the version halts, naming `Agent`

#### Scenario: The probe reports its first turn
- **WHEN** a Claude probe worker's first assistant event holds 3 input, 15000 cache-read and 4000 cache-write tokens
- **THEN** the probe's check line names a first turn of 19003 tokens

## MODIFIED Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge`, `mf-integrate` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root, through `skills/mf-converge/scripts/gate_run.py`, which records a green run in `.minions/gate/<tree>` — the tree, the
dry run's hash, the date and the seconds — and on a later call reuses it when the worktree is clean, its tree is that tree,
and `make -n gate` prints the same lines. A red run SHALL record nothing, and no record SHALL be written through a linked
`.minions/gate` or staged record, and `mf-release`'s gate after its fold SHALL run
fresh. `gate_run.py` SHALL run `make gate` and its dry run with no `VIRTUAL_ENV` in their environment. On a green run it
SHALL print its summary line alone, holding make's output back; on a red run it SHALL print make's output, then its summary
line. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
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

#### Scenario: A station reuses a green gate on the same tree
- **WHEN** a station's gate ran green on a tree, and a later station gates the same tree, clean, with the same dry run
- **THEN** the later station reuses the record and runs no `make gate`
- **AND WHEN** the tree, the dry run or a file in the worktree differs
- **THEN** it runs `make gate`
- **AND WHEN** `mf-release` gates the tree it folded
- **THEN** it runs `make gate`, whatever stands recorded

#### Scenario: A gate run from a uv environment
- **WHEN** `gate_run.py` runs with `VIRTUAL_ENV` set, and the gate's recipe echoes `VIRTUAL_ENV`
- **THEN** the recipe sees none
- **AND WHEN** the gate is green
- **THEN** `gate_run.py` prints one line, `gate: green — …`
- **AND WHEN** the gate is red
- **THEN** it prints make's output, then `gate: red — …`

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. One `stamp.py` call MAY write several events, each its
own line, inserted so the last given is on top; the conductor SHALL write in one call the events it has with no command
between them. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `shadow`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor, model and effort a mailbox checker's answer names, else the executor the conductor runs
on and the model and effort its worker was given, `default` where none, and `tokens` the worker's figure or `unavailable`. A
`shadow` line SHALL hold `overlap.py`'s line, or a shadow checker's failure. An adversarial head written by rule SHALL write one
`by rule` line, `no surface`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
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
- **WHEN** conformance ran through the mailbox and its answer reads `exit 0 · executor codex · model gpt-6.1-sol · effort high`
- **THEN** its `verdicts` line ends `executor codex · model gpt-6.1-sol · effort high · tokens unavailable`

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** `surfaces.py` exits 0 in a verify round
- **THEN** the log holds one `by rule` line, `no surface`, the round's `fan-out` names conformance alone, and its one
  `verdicts` line is conformance's

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards. The template SHALL
link `CODING_STANDARDS.md` and `CONTRIBUTING.md` as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`
as context for designing, building and reviewing; bootstrap SHALL halt when a `CODING_STANDARDS.md`,
`CODE_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md`, `ARCHITECTURE.md` or `docs/decisions.md` already exists.
Cut, build and release SHALL explicitly read it and the mandatory context it identifies before work; the converge conductor
SHALL read it and the change, and no other mandatory context.
Build, and converge for its conformance worker, SHALL also read a root `CODING_STANDARDS.md`,
`CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name. A contradiction between those files SHALL
go to the person: conformance cards it as drift, and the build halts on one that decides its phase's code. No filename
SHALL take precedence over another.
Cut and build SHALL read, of `docs/decisions.md`, the index `skills/mf-converge/scripts/bundle.py --decisions` prints and,
in full, each decision their source cites — the cut's brief, the build's change directory — and each other decision the
index shows their work touches; and other architecture documents — `ARCHITECTURE.md`, `docs/adr/*.md` — whole. They SHALL
read the principles and the threat model when a task of their work names the file. Converge SHALL hand its conformance
worker, in place of `docs/decisions.md`, the decisions the change cites, in full, and an index of all, as its bundle holds them,
and other architecture documents — `ARCHITECTURE.md`, `docs/adr/*.md` — whole; it SHALL hand its adversarial worker the threat
model. The build SHALL halt on a phase that contradicts a decision in force, unless a task of the change amends that decision.
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
- **THEN** the build reads it, and converge hands it to its conformance worker

#### Scenario: A converge worker's decisions
- **WHEN** converge dispatches its conformance worker in a repo whose `docs/decisions.md` has `### D` headings
- **THEN** the worker reads the decisions the change cites, in full, and the index from `bundle.md`, and not the whole file
- **AND** the adversarial worker reads `THREAT_MODEL.md`, and no decision

#### Scenario: The build's decisions
- **WHEN** `bundle.py --decisions` is given a change's proposal, design and tasks, which link D2 of a `docs/decisions.md`
  holding D1 and D2
- **THEN** it prints D2 in full and an index naming D1 and D2, and writes no file

#### Scenario: A phase contradicts a decision in force
- **WHEN** a phase's tasks would break a decision in the repo's `docs/decisions.md`, and no task amends it
- **THEN** the build halts, naming the decision and the task
- **AND WHEN** a task of the change amends that decision
- **THEN** the build proceeds

### Requirement: A worker's reach stops at the repository

A Codex worker's writable roots and a Claude worker's `Edit` and `--add-dir` SHALL be the primary and each open worktree,
from `git worktree list`, and never the directory holding them. An open worktree SHALL be the worktree of an open version —
a branch named by a change id, the default branch lacks, holding its change — or of a cut queued in the home folder's
queue; any other listed worktree SHALL be no reach. A listed worktree whose `.git` file does not point back to
an entry under the common directory SHALL be no worktree. `conduct.py` SHALL take the primary and its common directory once,
before the first worker, and SHALL never take a worker's reach from git's answer in a worktree. It SHALL refuse a run in a
checkout whose `.git` names another repository, and SHALL halt a Codex worker when the primary's `.git` no longer resolves to
that common directory. Directly before each Codex worker starts, `conduct.py` SHALL halt its version when any writable root
or its working directory is a link or no longer resolves to itself, naming the path. `conduct.py` SHALL load `integrate.py`
once, before the first worker, and SHALL halt a version's merge when the local git config or `info/attributes` changed since
then.

#### Scenario: A sibling project
- **WHEN** a worker runs in a repository whose parent holds other projects
- **THEN** no writable root and no `--add-dir` names that parent

#### Scenario: A released version's worktree
- **WHEN** a version's branch is merged into the default branch and its worktree is kept
- **THEN** no writable root and no `--add-dir` of a later worker names that worktree
- **AND WHEN** a cut is queued and its worktree made
- **THEN** a later worker's `--add-dir` names it

#### Scenario: A worker forges a worktree entry
- **WHEN** a worker adds an entry under the common directory's `worktrees/` naming a directory outside the repository
- **THEN** no writable root and no `--add-dir` names that directory, and no version runs in it

#### Scenario: A worker repoints a worktree
- **WHEN** a worker rewrites a worktree's `.git` file or its entry's `commondir` to name another repository
- **THEN** no writable root and no `--add-dir` of the next worker names that repository

#### Scenario: A worker plants git config
- **WHEN** a worker changes the common directory's config during a run
- **THEN** the conductor merges nothing for a dependent, and that version halts, naming the change

#### Scenario: A worker swaps a writable root for a link
- **WHEN** a worker moves a listed worktree aside and puts a link to a sibling project in its place, and the next station of
  a version runs on Codex
- **THEN** that version halts naming the link, and no Codex worker starts with the sibling among its writable roots

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort`, and the conformance and adversarial tables an `executor`; `[converge]` stays the
conductor's, and MAY say `shadow = true`. `conduct.py` SHALL read them once with the run's plan. A `[converge]` naming no
model or effort SHALL run its conductor on Claude as `claude-sonnet-5-5` at `high`. A checker table with no
`executor` SHALL run on converge's. It SHALL halt a version, before its worker starts, on a fixer table that names an
`executor`, an `executor` it does not know, a checker table naming `executor = "codex"` with a `claude-*` model, or a `model` or
`effort` holding anything
but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later differs, as for any station's table.
It SHALL pass in the converge prompt, before any grant clause, for conformance, adversarial and the fixer in that order:
`and <role>=mailbox` for a checker whose executor differs from converge's, else `and <role>=<model>/<effort>` for a table that
names a model or an effort, `default` for the one absent, with converge on Claude; then `and shadow=yes` under `shadow = true`. Converge SHALL put each model on its worker's call,
send each `mailbox` role through `conduct.py checker`, and SHALL NOT read the models file itself. A fixer sent any blocking card
SHALL run on adversarial's model when adversarial runs on converge's host, and otherwise on the fixer's; the fixer SHALL run at
the fixer's effort, `medium` when `fix=` names none. A verify worker SHALL run on its role's model at `medium`. A role given
none, or a host whose worker call takes no model, SHALL run its worker on the conductor's model. The cut SHALL write the worker
tables from the brief's `conformance`, `adversarial` and `fix` parts, each host as `executor`, and else conformance on the mid
tier · high, adversarial on the strongest tier · high, the fixer on the mid tier · medium; `[converge]` on Sonnet 5.5 · high,
where the session offers it, unless the brief names converge's model; and `shadow = true` when the brief's line ends `shadow`,
each mapped to the offered models.

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

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, and each repo
`conduct.py run` recorded in `~/.mf-ship-origin/repos` that still holds `.minions/`, once each; or those `--config` and
`--repo` name, a `--repo` reading no record; and SHALL halt naming the config path when none names a repo. It SHALL read each repo's
`.minions/changes/<change-id>/` files and its worker logs, `.minions/changes/<change>/logs/<stamp>-<station>.log` and
`<stamp>-<station>-<n>.log` — in a repo no run has moved, the old `.minions/findings/` and `.minions/runs/<stamp>/<change>_<station>.log`
and `-<n>.log` alike — and the operator's Codex sessions,
`~/.codex/sessions/**/*.jsonl`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. It SHALL read a change's
`conformance.md`, else its `review.md`, and its `adversarial.md`, else its `security.md`, and SHALL record each role by the name
its file or line carries, with its file's `executor:` and `model:`. The page
SHALL hold a table per repo and per role, executor and model, with each group's median duration and median tokens, a cost
table per repo — each change's stations, the cut, the supervisor and the mailbox's checkers among them, with their dollars,
turns, tokens, seconds and first-turn context — charts over changes drawn by `mf-build`'s `chart()`, and the
list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a Codex JSON log's tokens SHALL be the sum over its `turn.completed` events of their input and output tokens, its dollars those
tokens priced by `skills/mf-review-metrics/prices.toml` under the model its spawn line names, a gap with no such row, and its
turns and seconds gaps; a log's **first-turn context** SHALL be its first assistant event's input, cache-read and cache-write
tokens, or a Codex log's first `turn.completed` input tokens;
a station with no log and a log with neither result nor `turn.completed` event SHALL be a gap, and a station the run log shows spawned more times than
the logs read SHALL be marked `<read> of <spawns>`. A **worker** SHALL be each subagent a converge log's `task_started` event
names, with its role and round read from the event's description, `<role> round <N>`, a gap where it names none, and its
tokens, model and first-turn context from its assistant events, each counted once by message id; and each mailbox checker's
log. A worker's dollars SHALL be its tokens priced by `prices.toml` under its model — input, cache read at `cached_input`, the
5-minute cache write at `cache_write`, the 1-hour at `cache_write_1h`, output — a gap with no row or no price a token needs.
The status log's tokens SHALL be read per role, in every form a `verdicts` line
holds; a line naming both roles SHALL be recorded under the role `both`, credited to neither. A Codex worker's tokens SHALL be read from its session — the
last `token_count` event's totals, its model and effort from `turn_context` — matched to its round by its parent's `cwd` — the change's worktree, or the primary
when no other version's round overlaps — and the round's freeze-to-verdicts window, the guardian sessions left out, and never
into a round its line names `executor claude`. A role's executor SHALL be its file's `executor:`, else the one its round 1
`verdicts` line names. An **escape** SHALL be a card whose `repeat of` names an earlier change's card, traced to that change's
round 1 by the card's role and that role's executor. The shadow overlap SHALL be `overlap.py`'s count over each change's
round 1 and shadow files. It SHALL write `review-metrics.json`
beside the page: `records`, one per round and role, with its executor, model, effort, tokens, dollars — its workers' summed,
a gap when any is — and source; `workers`, one per worker; `stations`, one per change and station, with its dollars, turns,
tokens, seconds and first-turn context; `roles`, one per change
and role; `shadow`, one per change and role with a shadow file; `escapes`; and `headline`; a gap as `null`. The page and
`headline` SHALL show four numbers: each executor's share of the shadow rounds' distinct blockers that it alone caught; escapes
per version; dollars of converge per confirmed blocker, by the checkers' executor; and, per executor of the checker that raised
it, the share of cards whose first verify after `fixed` read `verified`. It SHALL read no tier, and SHALL count a file's
`inconclusive` sections only when the file holds `## Refuted`, the review method's mark. It SHALL give numbers, never a
recommendation. `conduct.py run` SHALL add its primary's path to `~/.mf-ship-origin/repos` at its start, when the file does not
hold it, and no worker SHALL write that file.

#### Scenario: No config
- **WHEN** the script runs with no config file, no `--repo` and no `~/.mf-ship-origin/repos`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Every repo a run started in
- **WHEN** the config names one repo and `~/.mf-ship-origin/repos` names it and another that holds `.minions/`
- **THEN** both repos are read, the first once
- **AND WHEN** `--repo` names a third
- **THEN** the third alone is read

#### Scenario: A repo of each layout
- **WHEN** one repo holds `.minions/changes/<id>/` and another the old `.minions/findings/` and `runs/<stamp>/` logs
- **THEN** both repos' changes are read, with their cost, and neither is written

#### Scenario: Both role names
- **WHEN** one change's folder holds `conformance.md` and `adversarial.md`, and another's `review.md` and `security.md`
- **THEN** both changes are read, each round recorded under the role names its files and lines carry

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: Cost from the run logs
- **WHEN** a repo's run directory holds a converge log with two result events, a build log with none, and a run log naming two
  converge spawns
- **THEN** the converge cell holds the last cumulative dollars and the summed turns, marked as one log of two, and the build cell
  is a gap

#### Scenario: The cut and the supervisor
- **WHEN** a change's logs hold a `cut` log and a `supervise` log, each with a result event
- **THEN** the cost table and `stations` hold a cut and a supervise entry with their dollars and first-turn context

#### Scenario: Cost per worker, round and role
- **WHEN** a converge log holds a subagent `conformance round 1` and one `adversarial round 1`, each with assistant events of
  a model `prices.toml` prices, and one `fix round 1` of a model it lacks
- **THEN** `workers` holds three records, each with its role, round, tokens and first-turn context, the fixer's dollars a gap
- **AND** round 1's conformance record holds its worker's dollars

#### Scenario: Cost from a Codex log
- **WHEN** a station's log is a Codex JSON log with two `turn.completed` events, and its spawn line names a model the price
  table holds
- **THEN** its cell holds the priced dollars and the summed tokens, its turns and seconds gaps
- **AND WHEN** the spawn line names a model the table lacks
- **THEN** its dollars are a gap and its tokens are read

#### Scenario: Tokens per role
- **WHEN** a status log holds `tokens review 45426, security 41346`, `tokens 128126 + 115356`, `tokens 115k (review 63k, security
  52k)` and a line naming one role with `tokens 97960`
- **THEN** each role's tokens are read from its own figure, and none is summed into the other

#### Scenario: A Codex worker
- **WHEN** a Codex session's parent ran in the repo's worktree inside a round's window, its path naming `conformance`
- **THEN** `review-metrics.json` holds that round's conformance record with the session's tokens, model and effort, `source:
  codex-session`

#### Scenario: Cross-model numbers
- **WHEN** a repo holds a change whose conformance ran on Codex with a Claude shadow, the shadow alone catching one blocker and
  both one, a later change carrying a card `repeat of` the first's, and a Codex card the Claude fixer fixed and a verify
  promoted to `verified`
- **THEN** `review-metrics.json` holds a `roles` record per role with its executor, a `shadow` record counting one shared and
  one shadow-alone blocker, an `escapes` record traced to the first change's conformance on Codex, and a `headline` holding the
  four numbers, and the page shows them

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per role, executor and model with its median duration and median
  tokens, and charts, and no repo has changed
