## ADDED Requirements

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.review]`, `[converge.security]` and `[converge.fix]`, each with a
`model` and an `effort`; `[converge]` stays the conductor's. `conduct.py` SHALL read them once with the run's plan. It SHALL halt
a version, before its worker starts, on a worker table that names an `executor`, or a `model` or `effort` holding anything but
letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later differs, as for any station's table. It
SHALL pass each worker table that names a model or an effort in the converge prompt as `and <role>=<model>/<effort>`, `default`
for the one absent, before any grant clause; with converge on Codex it SHALL pass none. Converge SHALL put each on its worker's
call and SHALL NOT read the models file itself. A fixer sent any blocking card SHALL run on review's model and effort, and
otherwise on the fixer's. A role given none, or a host whose worker call takes no model, SHALL run its worker on the
conductor's model. The cut SHALL write the worker tables: review and security on the strongest tier · high, the fixer on the
mid tier · high, and `[converge]` on the mid tier · medium unless the brief names converge's model, each mapped to the offered
models.

#### Scenario: The converge prompt names each worker's model
- **WHEN** a version's models file holds `[converge.review]` with `model = "claude-opus-5-5"` and `effort = "high"`, and
  `[converge.fix]` with `model = "claude-sonnet-5-5"` and `effort = "high"`, and its converge runs on Claude
- **THEN** its converge prompt reads `Run the mf-converge skill for change <change-id> and review=claude-opus-5-5/high and
  fix=claude-sonnet-5-5/high.`

#### Scenario: Converge on Codex
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a worker table
- **THEN** its converge prompt names no worker model, and every worker runs on the conductor's model

#### Scenario: A worker table names an executor
- **WHEN** `[converge.review]` names `executor = "codex"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A worker table changes during the run
- **WHEN** a worker changes `[converge.fix]`'s model after the run read its plan
- **THEN** that version halts, naming the models file as changed during the run

#### Scenario: The fixer by grade
- **WHEN** converge dispatches a fixer sent a blocking card
- **THEN** the fixer runs on review's model and effort
- **AND WHEN** it dispatches a fixer sent only non-blocking cards
- **THEN** the fixer runs on the fixer's model and effort

### Requirement: Converge hands each worker a bundle of what the change cites

At each freeze, converge SHALL run `skills/mf-converge/scripts/bundle.py`, which writes
`.minions/changes/<change-id>/bundle.md`: each repo decision the change's proposal, design, tasks or spec delta cites — by a
`decisions.md#d<n>` link, or by `D<n> · ` and that decision's title — in full; an index, each `### D` heading of
`docs/decisions.md`; and each living requirement the delta modifies or removes, in full. A decisions file with no `### D`
heading SHALL go into the bundle whole. A design's own decision ids SHALL cite no repo decision. Each worker SHALL read the
bundle in place of the decisions file and the living spec, opening a decision the index names only to trace review's
architecture angle. `bundle.py` SHALL refuse to write through a link, and SHALL exit 2, writing nothing, on a file it cannot
read.

#### Scenario: A change cites a decision
- **WHEN** a change's design links `docs/decisions.md#d48--…` and names a `D3` of its own
- **THEN** `bundle.md` holds D48 in full and every decision's heading in its index
- **AND** it holds no other decision's body

#### Scenario: A delta modifies a requirement
- **WHEN** a change's delta modifies a living requirement
- **THEN** `bundle.md` holds that requirement as the living spec states it, in full

#### Scenario: A decisions file with no headings
- **WHEN** a target's `docs/decisions.md` holds no `### D` heading
- **THEN** `bundle.md` holds the whole file

### Requirement: A fix that reaches no surface takes its security head by recomputation

`THREAT_MODEL.md` MAY hold `## Surfaces`, one ``- `<glob>` `` line per path a fix reaches security through, and the
bootstrap's template SHALL hold the section unwritten. In a Step 7 round after a fix commit, converge SHALL run
`skills/mf-converge/scripts/surfaces.py` over the fix range. It SHALL print `surfaces: no surface` and exit 0 when the security
file says `verdict: clean`, holds no card whose Status is other than `verified` or `accepted`, and the range touches no path a
glob listed at its start matches; otherwise it SHALL print `surfaces: verify — <reason>` and exit 1, a threat model with no listed glob among the
reasons. On exit 0 converge SHALL write the security file's `head:` to the fix head by rule, with `mode: by-rule` and
`workers: 0`, and dispatch review alone; on exit 1 it SHALL dispatch both. A catch-up run, its fix round included, SHALL
dispatch both, as before.

#### Scenario: A fix reaches no surface
- **WHEN** a fix touches no listed path, and the security file is clean with every card `verified` or `accepted`
- **THEN** `surfaces.py` exits 0, the security file's `head:` is the fix head with `mode: by-rule`, and no security worker runs

#### Scenario: A fix touches a surface
- **WHEN** a fix touches a path a listed glob matches
- **THEN** `surfaces.py` exits 1 naming the path and its glob, and security verifies the fix

#### Scenario: A security card awaits its checker
- **WHEN** the security file holds a card whose Status is `fixed`
- **THEN** `surfaces.py` exits 1 naming the card, and security verifies the fix

#### Scenario: A threat model lists no surface
- **WHEN** `THREAT_MODEL.md` has no `## Surfaces` glob, or no `THREAT_MODEL.md` exists
- **THEN** `surfaces.py` exits 1, and security verifies the fix

## MODIFIED Requirements

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor the conductor runs on, the model and effort its worker was given, `default` where none,
and `tokens` the worker's figure or `unavailable`. A security head written by rule SHALL write one `by rule` line,
`no surface`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's review and security files are read, each written by its worker
- **THEN** the log holds one `verdicts` line for each role, each naming the executor, and the model and effort that role's
  worker was given

#### Scenario: A converge run stops
- **WHEN** the run halts or finishes
- **THEN** its last event is `halt`, with the reason, or `done`

#### Scenario: A catch-up by rule
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** the log holds one `by rule` line, `clean` and each merge's paths, and no `fan-out` or `verdicts` line for the round

#### Scenario: A security head by rule
- **WHEN** `surfaces.py` exits 0 in a verify round
- **THEN** the log holds one `by rule` line, `no surface`, the round's `fan-out` names review alone, and its one `verdicts`
  line is review's

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
Cut and build SHALL read the architecture decisions and the threat model — the documents `AGENTS.md` names, else
`docs/decisions.md`, `ARCHITECTURE.md`, `docs/adr/*.md` and `THREAT_MODEL.md` when present. Converge SHALL hand every worker
the threat model and, in place of `docs/decisions.md`, the decisions the change cites, in full, and an index of all, as its
bundle holds them; other architecture documents go to every worker whole. The build SHALL halt on a phase that contradicts a
decision in force, unless a task of the change amends that decision.
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

#### Scenario: A converge worker's decisions
- **WHEN** converge dispatches a worker in a repo whose `docs/decisions.md` has `### D` headings
- **THEN** the worker reads the decisions the change cites, in full, and the index from `bundle.md`, and not the whole file

#### Scenario: A phase contradicts a decision in force
- **WHEN** a phase's tasks would break a decision in the repo's `docs/decisions.md`, and no task amends it
- **THEN** the build halts, naming the decision and the task
- **AND WHEN** a task of the change amends that decision
- **THEN** the build proceeds

### Requirement: Converge runs one depth

`skills/mf-converge/SKILL.md`, with its worker reference `skills/mf-converge/references/worker.md`, SHALL run one depth: each role's one fresh worker SHALL judge the change from a packet given up
front, its decisions and living requirements from the change's bundle, reading beyond the diff only to trace a named angle,
and SHALL run review's stale-claim, test-cost and coverage-trace
passes itself. It SHALL take no `tier=`, and SHALL halt, naming the parameter as removed, when one is given. The review and
security files' frontmatter SHALL record `mode`, `workers`, `model` and `packet`, and no tier. The cut SHALL write no `tier` into
`.minions/changes/<change-id>/models.toml`; `mf-ship` SHALL read none from it, and SHALL pass none to converge. The converge
prompt SHALL carry the worker models, when any, before a grant clause.

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
