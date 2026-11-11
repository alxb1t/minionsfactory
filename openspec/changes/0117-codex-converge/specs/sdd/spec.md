## ADDED Requirements

### Requirement: A Codex fixer halts at a limit and never falls back

A fixer table naming `executor = "codex"` SHALL start its fixer as `codex exec`, through the run's fixer call, on the table's model and effort, within converge's remaining time. Before it spawns, `conduct.py` SHALL count Codex ready as *A Codex checker falls back to Claude while Codex is limited* does, waiting for a reset at most 15 minutes away inside converge's deadline. Codex not ready, or a Codex fixer that exits on a usage limit, SHALL halt the version `codex usage limit — the fixer · resets <time>`, naming ` · the <window> window` when a window at 90% or more held it, and SHALL start no Claude worker and retry nothing. A converge halt that line names SHALL get no rescue and no supervisor. A fixer on Claude SHALL be started as before.

#### Scenario: The fixer meets the limit
- **WHEN** a Codex fixer exits on a usage limit whose reset is two hours away
- **THEN** the version halts `codex usage limit — the fixer · resets <time>`, no Claude worker starts, and no rescue or supervisor runs

#### Scenario: The weekly window is spent
- **WHEN** the newest rollout shows the weekly window at 98% with its reset days away, and a Codex fixer is to run
- **THEN** no Codex worker starts, and the version halts naming the weekly window

#### Scenario: A checker beside the same limit
- **WHEN** the weekly window is at 98% and a Codex conformance checker is to run in the same converge
- **THEN** the checker runs on Claude, and only the fixer halts the version

### Requirement: A Codex fixer carries its own attribution and adds no package

A fixer's prompt SHALL name the `Co-Authored-By:` line its commit ends with: `Codex <model> <noreply@openai.com>` on Codex, and the attribution line its session names on Claude. `skills/mf-converge/references/fix.md` SHALL say a fixer adds no package: a dependency is the plan's, and a Codex fixer has no network.

#### Scenario: A Codex fixer's prompt
- **WHEN** converge starts a Codex fixer on `gpt-6.1-sol`
- **THEN** its prompt holds `Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>`

## MODIFIED Requirements

### Requirement: A station's executor comes from the models file

`.minions/changes/<change-id>/models.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor, and a fixer table naming none SHALL run on Claude, whatever `[converge]` names. Integrate SHALL use the
`[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own — each station's, each checker table's, the fixer's
and each shadow checker's under `shadow = true`; a failed probe at the start SHALL stop the run, and one for a joining version
SHALL halt only the versions on its executor; a probe a usage limit stopped SHALL halt only the versions with a station on its
executor.
A station on Codex SHALL report each denial, its usage limit with the reset time, its tokens and its priced cost from its JSON
event log, as a station on Claude does from its own; converge's per-role tokens SHALL be read from each converge worker's own
log, on either host.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its checkers run as `codex exec` unless a table names another executor, and its build, fixer and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A checker's executor is probed
- **WHEN** a run's only Codex table is a version's `[converge.adversarial]`
- **THEN** the run probes Codex before any station

#### Scenario: A fixer's executor is probed
- **WHEN** a run's only Codex table is a version's `[converge.fix]`
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
- **AND WHEN** the worker is the converge fixer
- **THEN** its version halts `codex usage limit — the fixer · resets <time>`, and no Claude worker starts

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort` and an `executor`; `[converge]` stays the
checkers' default, and MAY say `shadow = true`. `[converge]` MAY say `skip = true`, and a conformance or adversarial table MAY say
`skip = true`, with no model, effort or executor: only the value `true` skips. `conduct.py` SHALL read them once with the run's plan,
and SHALL read a skip from no other place in that run, a `stage_of` or `_unjudged` read of a version's converge skip included. A
checker table with no `executor` SHALL run on converge's, and a fixer table with none on Claude. It SHALL halt a version, before its worker starts, on an `executor` it does not know, a worker table naming `executor = "codex"` with a `claude-*` model, or a
`model` or `effort` holding anything but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later
differs, as for any station's table. `converge.py` SHALL take each worker's model from that plan, or from the hand command's
`conformance=`, `adversarial=` and `fix=`, each `<model>/<effort>` with `default` for none, and SHALL read no models file itself.
The fixer SHALL always run on `fix=`'s model, at its effort, `medium` when it names none, whatever card it is sent, on the
executor its table names. A verify worker
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
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a checker table naming no executor and a fixer table naming none
- **THEN** that checker runs on Codex, on its table's model and effort, else on `[converge]`'s, and the fixer runs on Claude

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
- **WHEN** `[converge.fix]` names `executor = "codex"` and `model = "gpt-6.1-sol"`
- **THEN** the fixer runs as `codex exec` on `gpt-6.1-sol`, and the run probes Codex before any station

#### Scenario: A fixer on Codex with a Claude model
- **WHEN** `[converge.fix]` names `executor = "codex"` and `model = "claude-sonnet-5-5"`
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

### Requirement: A Codex usage limit halts only what runs on Codex

A probe worker or probe checker on Codex that exits on a usage limit SHALL be no refusal: `conduct.py` SHALL log
`run · limited — codex limited until <time>`, SHALL leave Codex unprobed, and the run SHALL go on. The reset SHALL be read, in
order, from Codex's rollout file named by the worker log's `thread.started` `thread_id` — the latest `resets_at` of the
`rate_limits` windows at 100% or more, else of the window most used — then from the failed turn's `try again at <time>` text,
taken as its next occurrence; a reset neither names SHALL hold the limit to the run's end. While the limit holds, each open
version and each queued cut with a station on Codex still ahead of it — any table save conformance's and adversarial's, the
fixer and the cutter included, and neither a rescue nor a supervisor — SHALL halt alone, naming the limit, and SHALL get no
rescue; every other version SHALL go on. A station is ahead of a version unless the version's stage is past it: a version at
`converge` or `converge-halted` is past its build, one at `integrate` or `integrating` is past its converge, and one at `release`
is past its integrate. A version whose only Codex tables are checkers SHALL go on, its checkers falling back. Past the reset,
Codex SHALL be probed again before its first worker. A converge halt whose line names a usage limit SHALL get no rescue and no
supervisor.

#### Scenario: The probe meets the limit
- **WHEN** a run's Codex probe exits on a usage limit, its rollout's 5-hour window at 100% with a reset two hours away, and the
  run holds a Claude-only version, a version whose `[converge.adversarial]` names Codex and a version whose `[build]` names Codex
- **THEN** the run log holds `codex limited until <time>`, the Claude-only version and the checker version are taken and
  released, and the version with the Codex build halts alone, naming the limit

#### Scenario: A version past its Codex station
- **WHEN** Codex is limited and a version whose `[build]` names Codex stands at `release`
- **THEN** the version is not halted, and its release runs

#### Scenario: A reset only the text names
- **WHEN** a limited Codex log names a `thread_id` with no rollout file, and its failed turn says `Try again at 5:50 PM.`
- **THEN** the limit holds until the next 5:50 PM

#### Scenario: A converge halt names a usage limit
- **WHEN** a version's converge halts on a line naming `stopped by a usage limit`
- **THEN** no rescue and no supervisor starts for it, and the version stays halted for the person

### Requirement: A Codex checker falls back to Claude while Codex is limited

Before a converge checker on Codex spawns, `conduct.py` SHALL count Codex limited while a recorded limit holds, or while the
newest rollout file's last `rate_limits` shows the 5-hour window or the weekly window at 90% or more with its `resets_at` still
ahead. A limit whose
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
