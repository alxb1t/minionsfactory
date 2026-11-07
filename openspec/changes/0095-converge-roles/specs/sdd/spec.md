## ADDED Requirements

### Requirement: Converge's checkers are conformance and adversarial

Converge SHALL run two checkers. **Conformance** SHALL judge the code against the change's own spec delta, design, tasks and
the decisions it cites, write `.minions/changes/<change-id>/conformance.md`, and grade `blocking` · `drift` · `nit`, its card
ids `R<n>`. **Adversarial** SHALL try to break the change — races, edge cases, exploits, security — write
`.minions/changes/<change-id>/adversarial.md`, and grade `critical` · `high` · `medium` · `low`, `high` a bug that would block,
its card ids `S<n>`. Each SHALL load its reference, `skills/mf-converge/references/generic-conformance.md` or
`skills/mf-converge/references/generic-adversarial.md`, whose `## The packet` table SHALL name what the conductor gives it:
conformance the range, `diff.patch`, the simplify commit's body, the change's `proposal.md`, `design.md`, `tasks.md` and spec
delta, its `bundle.md`, root `AGENTS.md` and the root standards files; adversarial the range, `diff.patch`, the source and tests
around the diff's hunks, `THREAT_MODEL.md`, root `AGENTS.md` and the bundle's debt cards. Conformance SHALL read no code beyond
the diff's hunks, save its stale-claim search. Each SHALL read `diff.patch` once, and run `git diff` or `git show` only for a
file's context the patch does not hold. A **security card** SHALL be an adversarial card whose Priority's category is
`security`.

#### Scenario: A converge round
- **WHEN** converge dispatches a round's checkers
- **THEN** conformance writes `conformance.md` and adversarial writes `adversarial.md`, and the release reads both

#### Scenario: The packets
- **WHEN** the packet tables of the conformance and adversarial references are read
- **THEN** conformance's names the change's artifacts, `bundle.md` and `diff.patch`, and no source beyond the diff's hunks
- **AND** adversarial's names `THREAT_MODEL.md`

#### Scenario: A security card
- **WHEN** an adversarial card's Priority reads `high · adversarial · security`
- **THEN** it is a security card
- **AND WHEN** it reads `high · adversarial · stability`
- **THEN** it blocks, and is no security card

### Requirement: A run moves the old findings files to the checkers' names

At its start, under its claim, before any worker, `conduct.py run` SHALL move each `.minions/changes/<change-id>/review.md` to
`conformance.md` and each `security.md` to `adversarial.md`, and an old layout's `.minions/findings/<change-id>_review.md` and
`_security.md` straight to the new names, by the old-layout move's rules: a link at an old file or its folder, an old file
beside its new one, or two old files naming one new path SHALL halt with nothing moved, and a second start SHALL move nothing.
`gate_check.py`, `integrate.py`, `conduct.py grant`, and a hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`,
finding a change's `review.md` or `security.md` in its folder, SHALL halt naming `/mf-ship`; `conduct.py status` and `report`
SHALL name such a change `old layout`; `run.py` SHALL read the new names alone, its role metrics a gap without them. A models file's `[converge.review]` and `[converge.security]` SHALL be read
as `[converge.conformance]` and `[converge.adversarial]` when the new table is absent.

#### Scenario: A run moves the old names
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `security.md`
- **THEN** they move to `conformance.md` and `adversarial.md`, the version's stage reads as before, and a second start moves
  nothing

#### Scenario: Both names stand
- **WHEN** a run starts beside `.minions/changes/<id>/review.md` and `conformance.md`
- **THEN** the run halts, naming both, and moves nothing

#### Scenario: A hand-run converge on the old names
- **WHEN** `mf-converge` runs by hand for a change whose folder holds `review.md`
- **THEN** it halts, naming the file and `/mf-ship`, and writes no status log

#### Scenario: An old worker table
- **WHEN** a version's models file holds `[converge.review]` and no `[converge.conformance]`
- **THEN** conformance's worker takes `[converge.review]`'s model and effort

### Requirement: Converge bundles the debt cards on the diff's files

At each freeze, after `bundle.py`, converge SHALL run `skills/mf-converge/scripts/debt_match.py`, which appends to `bundle.md` a
`## Debt cards on the diff's files` section: each card of `.minions/debt.md`, in full, whose **What it affects** field names in
backticks a path the frozen patch changes, a `:<line>` suffix dropped; `None.` when no card matches, or no debt file stands. No
worker SHALL read `.minions/debt.md`; the repeat rule SHALL match the bundled cards. `debt_match.py` SHALL refuse to write
through a link, and SHALL exit 2, writing nothing, when the bundle or the patch cannot be read.

#### Scenario: A card on a file the diff touches
- **WHEN** the debt holds a card whose **What it affects** names `` `src/a.py:12` `` and another naming `` `src/b.py` ``, and the
  patch changes `src/a.py` alone
- **THEN** the bundle holds the first card in full and not the second

#### Scenario: No debt file
- **WHEN** no `.minions/debt.md` stands
- **THEN** the bundle's debt section reads `None.`

#### Scenario: A bundle that is a link
- **WHEN** `bundle.md` is a link
- **THEN** `debt_match.py` exits 2 naming it, and the link's target is unchanged

### Requirement: A verify worker reads its open cards and the fix diff

In a Step 7 round after a Step 6 fix, converge SHALL run `skills/mf-converge/scripts/open_cards.py` for each checker it
dispatches, which writes `.minions/changes/<change-id>/<role>.open.md`: each card of the findings file whose Status is `open`,
`fixed` or `wontfix`, verbatim, and no other. The verify worker SHALL receive that file, the fix diff, its findings path and
`skills/mf-converge/references/verify.md`, in place of its role reference and the worker reference, and SHALL edit only those
cards' Status lines, the frontmatter, the Summary, the `## Resolution log`, and a new card for a regression the fix introduced.
Conformance's verify SHALL also run its stale-claim, test-cost and coverage-trace passes over the fix diff, given the design's
`## Tests` section. A catch-up's judge round SHALL dispatch the role references, as round 1 does. `open_cards.py` SHALL refuse to
write through a link, and SHALL exit 2, writing nothing, on a findings file it cannot read.

#### Scenario: The open cards
- **WHEN** a findings file holds cards whose Status is `open`, `fixed`, `wontfix`, `verified` and `accepted`
- **THEN** `open_cards.py` writes the `open`, `fixed` and `wontfix` cards alone

#### Scenario: A verify round
- **WHEN** converge dispatches a Step 7 round after a fix commit
- **THEN** each checker's worker gets its open cards, the fix diff, its findings path and `references/verify.md`, and not its
  role reference

#### Scenario: A catch-up's judge round
- **WHEN** a catch-up round dispatches its checkers over late commits
- **THEN** each loads its role reference, as in round 1

### Requirement: Conformance searches for stale claims

The conformance station SHALL run a **stale-claim pass** after its sections: every path, symbol, verb, route or count the diff
renames, deletes or changes is searched across the rest of the tree, the living spec and the decisions included, and each
mention the change made false is carded as `drift`. The station SHALL say in its Summary that the pass ran, and
`skills/mf-converge/SKILL.md` SHALL check that it did.

#### Scenario: Converge names the stale-claim pass
- **WHEN** the frozen diff renames a path that a file outside the diff still names
- **THEN** conformance cards that mention as `drift`, and its Summary says the stale-claim pass ran

#### Scenario: A conformance file without the pass
- **WHEN** a conformance findings file's Summary does not say the stale-claim pass ran
- **THEN** `mf-converge` treats it as a scope failure and halts

### Requirement: Conformance judges test cost and traced coverage

The conformance station SHALL run a **test-cost pass** after its sections, carding each new end-to-end test that a lower layer
proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When the freeze
removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to the test that runs it
now, or to the decision, in force at the base, that the design's `## Tests` table names as retiring it. A proof carried by
neither SHALL be `blocking`. Each round SHALL run both passes over that round's freeze. The station SHALL say in its Summary
that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** a conformance findings file's Summary does not say the test-cost pass ran, or the coverage-trace pass ran or the
  freeze removed no test
- **THEN** `mf-converge` treats it as a scope failure and halts

#### Scenario: The freeze removes a test the table retires
- **WHEN** the freeze removes a test that the `## Tests` table maps to a decision in force at the base
- **THEN** the coverage-trace pass accepts the removal and cards nothing for it

#### Scenario: A proof carried by neither
- **WHEN** a removed assertion maps to no remaining test and to no retiring decision
- **THEN** conformance cards it `blocking`

### Requirement: A fix that reaches no surface takes its adversarial head by recomputation

`THREAT_MODEL.md` MAY hold `## Surfaces`, one ``- `<glob>` `` line per path a fix reaches security through, and the
bootstrap's template SHALL hold the section unwritten. In a Step 7 round after a fix commit, converge SHALL run
`skills/mf-converge/scripts/surfaces.py` over the fix range. It SHALL print `surfaces: no surface` and exit 0 when the
adversarial file says `verdict: clean`, holds no card whose Status is other than `verified` or `accepted`, and the range
touches no path a glob listed at its start matches; otherwise it SHALL print `surfaces: verify — <reason>` and exit 1, a threat model with no listed
glob among the reasons. On exit 0 converge SHALL write the adversarial file's `head:` to the fix head by rule, with
`mode: by-rule` and `workers: 0`, and dispatch conformance alone; on exit 1 it SHALL dispatch both. A catch-up run, its fix
round included, SHALL dispatch both, as before.

#### Scenario: A fix reaches no surface
- **WHEN** a fix touches no listed path, and the adversarial file is clean with every card `verified` or `accepted`
- **THEN** `surfaces.py` exits 0, the adversarial file's `head:` is the fix head with `mode: by-rule`, and no adversarial worker
  runs

#### Scenario: A fix touches a surface
- **WHEN** a fix touches a path a listed glob matches
- **THEN** `surfaces.py` exits 1 naming the path and its glob, and adversarial verifies the fix

#### Scenario: An adversarial card awaits its checker
- **WHEN** the adversarial file holds a card whose Status is `fixed`
- **THEN** `surfaces.py` exits 1 naming the card, and adversarial verifies the fix

#### Scenario: A threat model lists no surface
- **WHEN** `THREAT_MODEL.md` has no `## Surfaces` glob, or no `THREAT_MODEL.md` exists
- **THEN** `surfaces.py` exits 1, and adversarial verifies the fix

## MODIFIED Requirements

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/references/worker.md`, converge's worker reference, SHALL name the **anchors** — data loss or an
irreversible delete, spend, exposure of personal data or secrets, silent wrong output — and SHALL grade an anchored finding
`blocking` in conformance and at least `high` in adversarial, save a route adversarial finds in a class the threat model's *Out of
scope* accepts by name, which is carded and does not block, anchors included. Conformance SHALL grade `blocking | drift | nit`, where `drift`
is docs, comments, README or CHANGELOG text the code contradicts; `drift` SHALL NOT block, save an amend card, on which converge
halts at Step 9. A spec scenario the code contradicts SHALL stay `blocking`. Adversarial SHALL grade
`critical | high | medium | low`, `high` a bug that would block.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **WHEN** conformance or adversarial finds data loss or an irreversible delete, spend, exposure of personal data or secrets,
  or silent wrong output
- **THEN** conformance grades it `blocking` and adversarial at least `high`, so the loop fixes it

#### Scenario: Prose the code contradicts
- **WHEN** conformance finds docs, comments, README or CHANGELOG text the code contradicts
- **THEN** it grades the finding `drift`, which does not block, save an amend card, on which converge halts at Step 9
- **AND** a spec scenario the code contradicts stays `blocking`

#### Scenario: A route in the accepted class
- **WHEN** adversarial finds a route in a class the threat model's *Out of scope* accepts by name, with an anchored harm
- **THEN** it cards the route, and the card does not block

### Requirement: A repeated finding escalates

Each station SHALL read the debt cards its bundle holds, `bundle.md`'s `## Debt cards on the diff's files`. A finding that
repeats a debt card SHALL name that card's id in its **Related** field as `repeat of <id>`, and SHALL go up one level:
adversarial by one step, a conformance `nit` or `drift` to `blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** a station's finding describes a defect a debt card in its bundle already holds
- **THEN** its **Related** field names `repeat of <id>`
- **AND** it goes up one level: adversarial by one step, a conformance `nit` or `drift` to `blocking`

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/changes/<change-id>/status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, each line and run heading written by
`skills/mf-converge/scripts/stamp.py`, which takes the clock's time. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `by rule`, `debt`, `halt` and
`done`, and a run SHALL end on `halt` or `done`. Each `verdicts` line SHALL name one role and end `executor <x> · model <m> ·
effort <e> · tokens <n>`: the executor the conductor runs on, the model and effort its worker was given, `default` where none,
and `tokens` the worker's figure or `unavailable`. An adversarial head written by rule SHALL write one `by rule` line,
`no surface`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `mf-converge` dispatches, receives or decides
- **THEN** it inserts one line for that event under the latest `## Run N` heading, written by
  `skills/mf-converge/scripts/stamp.py`, which takes the clock's time
- **AND** the newest run and the newest line are on top, and no earlier line changes

#### Scenario: A round's verdicts
- **WHEN** a round's conformance and adversarial files are read, each written by its worker
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
- **THEN** the log holds one `by rule` line, `no surface`, the round's `fan-out` names conformance alone, and its one
  `verdicts` line is conformance's

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards. The template SHALL
link `CODING_STANDARDS.md` and `CONTRIBUTING.md` as mandatory context, and `docs/decisions.md` and `THREAT_MODEL.md`
as context for designing, building and reviewing; bootstrap SHALL halt when a `CODING_STANDARDS.md`,
`CODE_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md`, `ARCHITECTURE.md` or `docs/decisions.md` already exists.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
Build, and converge for its conformance worker, SHALL also read a root `CODING_STANDARDS.md`,
`CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name. A contradiction between those files SHALL
go to the person: conformance cards it as drift, and the build halts on one that decides its phase's code. No filename
SHALL take precedence over another.
Cut and build SHALL read the architecture decisions and the threat model — the documents `AGENTS.md` names, else
`docs/decisions.md`, `ARCHITECTURE.md`, `docs/adr/*.md` and `THREAT_MODEL.md` when present. Converge SHALL hand its conformance
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

#### Scenario: A phase contradicts a decision in force
- **WHEN** a phase's tasks would break a decision in the repo's `docs/decisions.md`, and no task amends it
- **THEN** the build halts, naming the decision and the task
- **AND WHEN** a task of the change amends that decision
- **THEN** the build proceeds

### Requirement: Generic passes preserve the station boundaries

`mf-simplify` SHALL edit only the change's own lines, by its angles and closed edit kinds, inside the oracles its
skill names, before independent checking. The build SHALL retain its gate and separate simplify-commit ordering. Conformance
SHALL check spec, plan, architecture, standards and gate integrity in separate sections, each citing its source document,
including the existing stale-claim, test-cost and coverage-trace passes.

Adversarial SHALL read the target's threat model first, then try to break the changed behaviour and its surrounding context —
races, boundary and malformed input, partial failure, ordering, a removed guard — and inspect it for concrete
vulnerabilities, secrets exposure, unsafe permissions and trust-boundary failures, including prompt, tool and model-output
trust where relevant. A finding SHALL be introduced by the change, unless the contract's passes or repeat rule name it or it is
a contradiction between standards files, carry a concrete scenario and the offending line quoted, and SHALL NOT be one the
reference's do-not-flag list names unless the target's threat model overrides it. A section whose source document is missing
SHALL be marked `inconclusive`, never read as a pass. Findings SHALL use the existing cards, severity, verdict, verification and
release contracts. Conformance and adversarial SHALL edit their own findings files, leave code changes to the fix station, and
keep findings local rather than publish external comments.

#### Scenario: A generic pass receives a frozen change
- **WHEN** the station receives the explicit base and head, patch and the packet its reference names
- **THEN** it judges that range without requiring a GitHub remote or review plugin
- **AND** it reports the scope it actually inspected rather than declaring an uninspected change clean

#### Scenario: A generic worker verifies a fix
- **WHEN** fresh conformance and adversarial workers receive their open cards and the fix range
- **THEN** each promotes verified findings or reopens them under the existing contract
- **AND** conformance receives the design's test table and runs the required passes

#### Scenario: A section lacks its source document
- **WHEN** the target has no threat model, or one whose sections read `Not written yet:`
- **THEN** the adversarial file's threat-model section is `inconclusive`, its generic classes are still checked, and
  the verdict may still be `clean`

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins, and SHALL record `mode: parallel` or `mode: sequential`,
or `mode: by-rule` with `workers: 0` for a by-rule catch-up, which dispatches no worker. The
station SHALL halt before work requiring an unavailable worker capability, naming that
capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** conformance completes before a fresh adversarial worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

#### Scenario: A host runs one worker at a time
- **WHEN** converge runs on a host that cannot run workers in parallel
- **THEN** it runs the conformance worker, then the adversarial worker, over the same frozen head, and the findings files
  record `mode: sequential`

#### Scenario: A by-rule catch-up records no worker
- **WHEN** every merge of a catch-up replays by the fixed rules
- **THEN** both findings files record `mode: by-rule` and `workers: 0`
- **AND** `review_metrics.py` reads that change's workers as a gap, never a zero

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their role resources: converge's conformance, adversarial, verify and worker
references on every executor, and `mf-simplify` in the build, whose link SHALL resolve from the build's installed package, not
the target's cwd; a missing target SHALL halt the build, naming it.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package, a
`#section` after a target ignored by the check, and the
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

### Requirement: Every worktree shares the primary's run directory

Every station and bundled script SHALL resolve the run directory as `.minions/` beside the primary checkout's git
directory — `git rev-parse --path-format=absolute --git-common-dir`, its parent — from any worktree of the
repository. `conduct.py` alone SHALL halt on that answer outside the repo it names until a run has kept that repo's URLs: a worker
can write what steers it. Converge and the release SHALL write `.minions/debt.md` only while holding `.minions/debt.lock`,
created with `mkdir`, halting after two minutes of waiting and naming the lock. A run holding the claim SHALL remove a
`debt.lock` older than ten minutes before its first worker, and log it. A run SHALL move an old `.minions/backlog.md` to `debt.md`, and remove a stale `backlog.lock`, at its start, under its
claim, and halt naming them when both files stand, or when beside the old file the old lock is a file or younger than
ten minutes; with no old file, no old lock halts. An old file that is a link SHALL halt, naming it, and the move SHALL NOT
follow it. The move SHALL hold `.minions/debt.lock`, created with `mkdir`, halting naming it when it is held, and naming it a
file, not a lock, when a file or a link stands there; it SHALL NOT replace a `debt.md`. Everything about one change SHALL live in `.minions/changes/<change-id>/` — its conformance, adversarial and status
log files, its diff patch, its models file, the cutter's `cut.halt`, integrate's notes, build's marks, rescue's diagnosis, release's `held`, its gate-check
export and its worker logs — each script finding it through one `_change_dir(primary, id)`; `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/`, `cuts/` and `debt.md` stay generic. A run SHALL move an old layout's files into it at its start, under its claim,
before any worker, idempotently, leaving every file it does not name; a link at `changes/`, `changes/<change-id>/` or an old file
SHALL halt, naming it, and so SHALL an old file beside its new one. `integrate.py`, `gate_check.py`, `run.py`, `conduct.py grant`, and a
hand-run `mf-release`, `mf-integrate`, `mf-converge` or `mf-build`, finding a file of its change at its old path, SHALL halt, naming
`/mf-ship` to move it, before writing a file at a new path;
`conduct.py status` and `report` SHALL name such a change `old layout`, reading no stage; `review_metrics.py` SHALL read both
layouts.

#### Scenario: A release in a linked worktree after a converge in another
- **WHEN** converge ran in one worktree of a change and the release runs in another worktree of the same repository
- **THEN** the release reads the same findings files, and does not read converge as skipped

#### Scenario: Two converges write the backlog
- **WHEN** a converge reaches Step 9 while another holds `.minions/debt.lock`
- **THEN** it waits, writes once the lock is free, and removes the lock after its write

#### Scenario: A dead worker left the lock
- **WHEN** a run starts and `.minions/debt.lock` is older than ten minutes
- **THEN** the run removes it and logs the removal before its first worker
- **AND WHEN** the lock is younger
- **THEN** the run leaves it

#### Scenario: A run moves an old backlog
- **WHEN** a run starts beside a `.minions/backlog.md` and no `.minions/debt.md`
- **THEN** it moves the file, removes any stale `backlog.lock`, logs both, and a second start moves nothing
- **AND WHEN** both files stand, the old file is a link, or beside it a `backlog.lock` that is a file or younger than ten
  minutes, or a `debt.lock` younger than ten minutes
- **THEN** the run halts, naming them, and starts no worker
- **AND WHEN** beside the old file `.minions/debt.lock` is a plain file
- **THEN** the run halts, naming `.minions/debt.lock` a file, not a lock, and starts no worker
- **AND WHEN** no old file stands beside a young `backlog.lock`, or a file there
- **THEN** the run goes on

#### Scenario: A run moves an old layout
- **WHEN** a run starts beside `.minions/findings/<id>_review.md`, `models/<id>.toml`, `build/<id>.done` and a stray `findings/notes.txt`
- **THEN** each moves into `.minions/changes/<id>/`, the findings file as `conformance.md`, the stray stays, the version's stage
  reads as before, and a second start moves nothing

#### Scenario: A hand-run release on an old layout
- **WHEN** `mf-release` runs by hand for a change whose findings sit in `.minions/findings/`
- **THEN** it halts, naming `/mf-ship`, and releases nothing

### Requirement: Every station runs MF's own method

The build SHALL identify and report the executing agent from runtime evidence, not from its model, provider or
editor, and SHALL choose no engine by it: every station runs MF's own method on every executor. The build SHALL run
`mf-simplify` and no native `/simplify`; conformance and adversarial SHALL run MF's method from the bundled references, and
converge SHALL invoke no native `/code-review` or `/security-review`.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code runs the build's simplify pass and native `/simplify` is invocable
- **THEN** the build runs `mf-simplify`, not the native command

#### Scenario: A native command is unavailable
- **WHEN** native `/simplify` is not invocable
- **THEN** the build runs `mf-simplify` as on any host, and nothing halts for it

#### Scenario: Claude Code converges
- **WHEN** converge runs on Claude Code
- **THEN** every conformance and adversarial worker loads MF's references, and no native review command runs

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the build reports that executor and runs `mf-simplify`

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the build reports `unidentified` without guessing from the model name, and runs `mf-simplify`

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/changes/<change-id>/` files and its worker logs, `.minions/changes/<change>/logs/<stamp>-<station>.log` and
`<stamp>-<station>-<n>.log` — in a repo no run has moved, the old `.minions/findings/` and `.minions/runs/<stamp>/<change>_<station>.log`
and `-<n>.log` alike — and the operator's Codex sessions,
`~/.codex/sessions/**/*.jsonl`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. It SHALL read a change's
`conformance.md`, else its `review.md`, and its `adversarial.md`, else its `security.md`, and SHALL record each role by the name
its file or line carries. The page
SHALL hold a table per repo and per model, a cost table per repo — each change's stations with their dollars, turns, tokens and
seconds — charts over changes drawn by `mf-build`'s `chart()`, and the list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a station with no log and a log with no result event SHALL be a gap, and a station the run log shows spawned more times than
the logs read SHALL be marked `<read> of <spawns>`. The status log's tokens SHALL be read per role, in every form a `verdicts` line
holds; a line naming both roles SHALL be recorded under the role `both`, credited to neither. A Codex worker's tokens SHALL be read from its session — the
last `token_count` event's totals, its model and effort from `turn_context` — matched to its round by its parent's `cwd` — the change's worktree, or the primary
when no other version's round overlaps — and the round's freeze-to-verdicts window, the guardian sessions left out, and never
into a round its line names `executor claude`. It SHALL write `review-metrics.json`
beside the page: one record per round and role, with its executor, model, effort, tokens and source, a gap as `null`. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

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

#### Scenario: Tokens per role
- **WHEN** a status log holds `tokens review 45426, security 41346`, `tokens 128126 + 115356`, `tokens 115k (review 63k, security
  52k)` and a line naming one role with `tokens 97960`
- **THEN** each role's tokens are read from its own figure, and none is summed into the other

#### Scenario: A Codex worker
- **WHEN** a Codex session's parent ran in the repo's worktree inside a round's window, its path naming `conformance`
- **THEN** `review-metrics.json` holds that round's conformance record with the session's tokens, model and effort, `source:
  codex-session`

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed

### Requirement: Converge runs one depth

`skills/mf-converge/SKILL.md`, with its worker reference `skills/mf-converge/references/worker.md`, SHALL run one depth: each
role's one fresh worker SHALL judge the change from the packet its reference names, given up front, conformance's decisions and
living requirements from the change's bundle, reading beyond the diff only to trace a named angle, and conformance SHALL run its
stale-claim, test-cost and coverage-trace passes itself. It SHALL take no `tier=`, and SHALL halt, naming the parameter as
removed, when one is given. The conformance and adversarial files' frontmatter SHALL record `mode`, `workers`, `model` and
`packet`, and no tier. The cut SHALL write no `tier` into `.minions/changes/<change-id>/models.toml`; `mf-ship` SHALL read none
from it, and SHALL pass none to converge. The converge prompt SHALL carry the worker models, when any, before a grant clause.

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

### Requirement: A catch-up over a merge the fixed rules reproduce is clean by recomputation

`skills/mf-integrate/scripts/integrate.py replay <merge>` SHALL rebuild the merge from its parents in a scratch worktree, settle
a conflicted `CHANGELOG.md` with the `changelog` rule, run the `decisions` rule on every merge, conflicted or clean, run the
`delta` rule, and exit 0 when `delta` names no requirement and the rebuilt tree equals the merge's tree, else 1. Its line SHALL
name each path a rule settled: one git left unmerged, and `docs/decisions.md` when the `decisions` rule renumbered. Its git SHALL
run no hook and fetch no missing object.
It SHALL exit 2, rebuilding nothing, for a commit without two parents or whose second parent the default branch does not hold.
`skills/mf-converge/SKILL.md`'s catch-up round SHALL first run *Catch-up scope*'s ancestry and parent checks, halting when one
fails, then run `replay` for each merge in its selection; when every merge replays and the selection holds nothing else, it SHALL
write both findings files `head: HEAD` and `verdict: clean` with a `## By rule` section naming each merge's paths, log
`round N · by rule — clean, <paths>`, dispatch no worker, and count the round within the merges-and-amends count. A selection
holding an amend — the person's, the rescue's or the supervisor's — and a run after an answered halt SHALL take the catch-up round
as before.

#### Scenario: A changelog the rule settled
- **WHEN** the integrate merge conflicted in `CHANGELOG.md` alone, settled by `integrate.py changelog`
- **THEN** the catch-up replays it, writes both findings files clean with `## By rule`, dispatches no worker, and the release
  passes its preconditions

#### Scenario: A decision renumbered in a cleanly merged file
- **WHEN** git merged `docs/decisions.md` with no conflict, and the integrate merge's `decisions` rule renumbered the branch's id
- **THEN** replay prints `replay: by rule — docs/decisions.md` and exits 0

#### Scenario: A merge and the person's amend
- **WHEN** the selection is a merge that replays and the person's amend of the change directory, and Step 1 passes
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches conformance and adversarial over the selection

#### Scenario: A merge and the rescue's amend
- **WHEN** the selection is a merge that replays and the rescue's amend of the change directory, carrying its `Rescue:` trailer
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches conformance and adversarial over the selection

#### Scenario: A merge and the supervisor's amend
- **WHEN** the selection is a merge that replays and the supervisor's amend of the change directory, carrying its `Supervisor:`
  trailer
- **THEN** the catch-up writes no `## By rule`, and one Step 7 round dispatches conformance and adversarial over the selection

#### Scenario: A merge someone judged
- **WHEN** the merge holds a hunk the integrator resolved as a union, a person's resolution, a test edited, or a requirement
  the delta edits that the default branch changed, the delta changing or removing a line of the default branch's block
- **THEN** replay exits 1, and the catch-up round dispatches conformance and adversarial as before

#### Scenario: A merge of a commit the default branch does not hold
- **WHEN** the merge's second parent is not an ancestor of the default branch, though git merged it with no conflict
- **THEN** replay exits 2, and the catch-up halts, naming the merge, with no findings file written clean

### Requirement: A halted version is rescued in its run

When a version halts on its build check, a converge halt — its cap the run does not grant, or `amend needed` among them — or integrate's red gate or note, `conduct.py` SHALL spawn the
`mf-rescue` station in that version's thread, unless its models file's `[rescue]` table says `skip = true`; the station SHALL run on
the `[rescue]` table's executor and model, the `[build]` table's when there is none. `skills/mf-build/SKILL.md` SHALL write
`.minions/changes/<id>/build.halt` on every halt — the sub-task, the stop condition, one line of evidence. `skills/mf-rescue/SKILL.md` SHALL
fix a build halt on a `Verify:` that cannot pass, a reader a deletion missed, a task two readings would build differently, or an
`Verify:` that is not one plain command — a `$(…)`, a shell variable, a loop or a `cd` — and a converge `amend needed` halt with the
amend its cards name — each `wontfix` card's, and each `open` `drift` card's **Fix** — with one `docs(<id>): amend the change directory` commit touching only `openspec/changes/<id>/tasks.md` and `design.md`,
never `design.md`'s decisions table without the version's switch, carrying a `Rescue:` trailer; every other halt it SHALL diagnose in `.minions/changes/<id>/rescue.md`.
An `amend needed` halt naming a security card of `critical` or `high` severity SHALL get a diagnosis alone, whatever the
switch. The rescue SHALL be offered its amend whether the version halted in this run or before it, at the run's start.
`conduct.py` SHALL halt the version when the commit touches any other path, and otherwise clear its halt and go on in the same run, an
`amend needed` halt to its amend round, a catch-up run marked `· amend` whose one Step 7 round judges the rescue's amend. A version whose
rescue at a converge or integrate halt leaves its stage on disk no halt SHALL stay halted for the run, a rejoin request taking it
back none, the halt naming that stage and a moved `HEAD`: whatever answers the halt on disk while the rescue runs, or before
the run reads its outcome, SHALL count as the rescue's answer and wait for a re-run — save the person's
`docs(<id>): amend the change directory` commits, none carrying a `Rescue:` or `Supervisor:` trailer, which answer an
`amend needed`, `verify: halt` or clean catch-up or amend-run halt
by amends alone: the version SHALL go on in the run, logged `rescue — <id>: amended · <commit>`. A version SHALL
get at most `RESCUES = 3` rescues in a run, and none for a sub-task it rescued before; a timeout, a usage limit and D47's halts that
need the person SHALL get none. The run SHALL log `rescue — <id>: fixed · <sub-task> · <commit>`, `rescue — <id>: decided ·
<sub-task> · <commit>` or `rescue — <id>: diagnosed · <file>`, and `report` SHALL print each. The rejoin folder and the grants folder SHALL be read and emptied through a directory file
descriptor opened without following a link. A sub-task an amend adds — the rescue's, the supervisor's or the person's — SHALL go
in a new unticked phase after the last, with its `## Progress` line, never under a ticked phase, whose sub-tasks no build reads.

#### Scenario: A check that cannot pass
- **WHEN** a build halts on a `Verify:` whose search matches a line no task touches
- **THEN** the rescue amends `tasks.md`, the run logs `rescue — fixed`, and the version builds on and releases in the same run

#### Scenario: A decision halt
- **WHEN** a build halts on a design premise the code rules out, with no switch
- **THEN** the rescue writes `.minions/changes/<id>/rescue.md`, and the version stays halted, its halt naming the file

#### Scenario: A rescue outside the plan
- **WHEN** a rescue's commit touches a file outside `tasks.md` and `design.md`
- **THEN** the version halts, naming the file

#### Scenario: A rescue at amend needed
- **WHEN** converge halts `amend needed` on a conformance card whose fix names a `design.md` prose amend, in the run or before it
- **THEN** the rescue commits that amend, and the version converges again in the same run, in a catch-up run marked `· amend`,
  with no new round 1
- **AND WHEN** the card is a security card of `high` severity
- **THEN** the rescue diagnoses, and the version stays halted

#### Scenario: A rescue at a drift halt
- **WHEN** converge's Step 9 halts `amend needed` on an `open` `drift` card whose **Fix** names a `design.md` amend, both findings
  files clean, and the version's models file says `decide = "recommended"`
- **THEN** the rescue commits that amend with its `Rescue:` trailer, and the version goes on in the same run through its amend
  round, whose one Step 7 round reads the amend, with no new round 1, and releases

#### Scenario: An amend lands during a rescue
- **WHEN** the person commits `docs(<id>): amend the change directory` while the rescue of its `amend needed` halt runs
- **THEN** the version goes on in the same run, and the run logs `rescue — <id>: amended`

#### Scenario: A worker's amend is no person's
- **WHEN** an amend of the change directory carrying a `Supervisor:` trailer follows a converge halt's head, and the supervisor's
  check refused it
- **THEN** the version stays halted for the run, as when the rescue answered it

#### Scenario: A rescue that answers its cap
- **WHEN** a rescue at a converge cap writes a grant and a rejoin request
- **THEN** the run starts no further converge round, and logs the version still halted

#### Scenario: The same sub-task again
- **WHEN** a version halts again on a sub-task it was rescued from
- **THEN** no rescue runs, and the halt names both

#### Scenario: A sub-task added after its phase is ticked
- **WHEN** an amend at a converge halt adds a sub-task the build must make, and every phase of `## Progress` is ticked
- **THEN** the amend adds it in a new unticked phase after the last, and the version builds that phase before it converges

#### Scenario: A link at the rejoin folder
- **WHEN** a worker swaps the rejoin folder for a link to another directory after the run lists it
- **THEN** nothing in that directory is deleted

### Requirement: A run grants one round at a small cap, and halts a large one for a re-plan

When a version's converge halts with `cap reached` in a run, `conduct.py` SHALL read the open blocking findings in its
conformance and adversarial findings files — conformance's `blocking`, adversarial's `critical` and `high`, each
`Status: open` — and, when every one's fix is
sized `one line`, `a test` or `one line and a test`, no granted round reached the cap — its converge run is not marked `· grant`,
and the run has not granted the version already — and its models
file's `[converge]` table does not say `auto_grant = false`, SHALL spawn converge with `grant=yes` itself, writing no grant file and
starting no rescue, log `grant — <id>: automatic · <ids>`, and check the round as it checks a person's grant's. Otherwise — a blocker sized `a design change`, no open blocking card read, a granted
round's cap, automatic or a person's, in this run or an earlier one, a second cap in the run, or `auto_grant = false` — the run SHALL write the version a last halt line, `re-plan: <ids>`, and the version's rescue SHALL
diagnose it, naming `/mf-plan` with the version's brief as the way back. A person's grant SHALL still spend a round on a re-plan
halt. `mf-converge` run by hand grants nothing on its own.

#### Scenario: A small cap
- **WHEN** a version caps with open blockers sized `one line` and `a test`
- **THEN** the run logs `grant — <id>: automatic`, converges one more round, writes no `.minions/grants/<id>`, and releases the
  version in the same run when that round is clean

#### Scenario: A design change at the cap
- **WHEN** an open blocker at the cap is sized `a design change`
- **THEN** no grant is spent, and the version halts as `re-plan`, its rescue naming `/mf-plan`

#### Scenario: The granted round blocks again
- **WHEN** the automatically granted round ends with a blocker open
- **THEN** the version halts as `re-plan`, and no second automatic grant is spent
- **AND WHEN** a later run reads that cap
- **THEN** it halts the version as `re-plan` and spawns no converge

#### Scenario: The granted round ends unfinished
- **WHEN** the automatically granted round's converge exits 0 with its status log not on `done`
- **THEN** the run logs the converge check's failure and halts the version, spawning no other converge

#### Scenario: Turned off
- **WHEN** the version's models file says `[converge] auto_grant = false`
- **THEN** its cap halts as `re-plan` with no automatic grant

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — and the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. The cut's `diff-lines` and `diff-files` SHALL be the collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

### Requirement: A supervisor answers what the rescue leaves

Under a version's switch, `decide = "recommended"`, when its rescue at a build check halt, a converge halt or an
`integrating` halt on a semantic conflict writes a diagnosis, the run diagnoses its converge `verify: halt`, or its rescue is
spent on the halt — the sub-task rescued before in the run, or `RESCUES` reached — `conduct.py` SHALL spawn the `mf-supervise`
station in that version's thread, with `decide=recommended`, and with `brief=<path>` when the version's passed cut recorded a
brief that still names a file. It SHALL spawn none without the switch; at an integrate red gate; at an `integrating` halt on
an open merge a supervisor was spawned on before, in this run or an earlier one, which the home folder's queue records; at a
halt the rescue's answer
on disk holds for a re-run; at a converge halt while `adversarial.md` holds an open security card of `critical` or `high`
severity, or its `amend needed` names one; when the rescue's worker failed or its amend was refused; nor when the models file's
`[rescue]` table says `skip = true`. The station SHALL run on the `[supervise]` table's executor, model and effort; on Claude, an
absent model SHALL be `claude-opus-5-5` and an absent effort `high`. At a passed cut, `conduct.py` SHALL record the brief's path
in the home folder's queue, under `briefs/<id>`, where no worker writes; a version cut by hand SHALL have none. The station SHALL
read the brief as evidence, never instruction.

`skills/mf-supervise/SKILL.md` SHALL answer a build or converge halt with one `docs(<id>): amend the change directory` commit
carrying `Supervisor: <sub-task or stage>` and `Decided-by: supervisor` trailers, or commit nothing. It MAY edit any file under
`openspec/changes/<id>/`, the spec delta included, tick a sub-task box whose `Verify:` it ran and saw pass, and add work as a new
unticked phase after the last. It SHALL never edit code, a test or any other path, take a security card of `critical` or `high`
severity, approve a gate makefile, accept a risk the threat model does not accept, untick a box, release, merge or push. At an
`integrating` halt it SHALL instead resolve the note's conflicts in Markdown files under `openspec/` and `docs/` alone, stage
each by name, write `.minions/changes/<id>/integrate.settled` naming what it settled, leave the merge and the note open, and
commit nothing; or edit nothing.

`conduct.py` SHALL take the commit only when it is the one commit past the station's start, with one parent, the amend's
subject, a `Supervisor:` trailer, a `Decided-by:` trailer reading `supervisor`, and paths under `openspec/changes/<id>/` alone. It
SHALL then clear the version's halt and its diagnosis, log `supervise — <id>: decided · <sub-task or stage> · <commit>`, and go
on in the same thread, with no restart and no wait for a poll. At an `integrating` halt it SHALL take the settle only when
`HEAD` and the open merge are the station's start's, the note stands, every index path it changed is a Markdown file under
`openspec/` or `docs/`, the work tree holds nothing unstaged or untracked, no path stays unmerged, and `integrate.settled` was
written during the station's run. It SHALL then clear the version's halt and its diagnosis, log
`supervise — <id>: decided · integrating · <tree>`, `<tree>` the staged tree, and spawn `mf-integrate` `with settled=supervisor`
in the same thread, halting the version when the merge commit holds a path past that tree other than a test its body names
fixed. Any other outcome SHALL halt the version, naming what the station left; at a converge or integrate halt, an answer on
disk SHALL then hold the version for a re-run as the rescue's does, the halt reading `supervisor answered its halt`, and the
person's amends alone, none carrying a `Rescue:` or `Supervisor:` trailer, SHALL go on. A version SHALL get one supervisor try
per halt and at most `SUPERVISES = 2` in a run; a halt the supervisor tried before SHALL name ` · supervised <sub-tasks>`. A
grant SHALL be refused while the station runs, as while the rescue runs. `report` SHALL print
`<id> · supervised <sub-task or stage> · <commit>` for each taken amend or settle, the run's closing line and its `done` line
SHALL name ` · supervised <ids>`, and the run's metrics SHALL count them as `supervisor-decided`.

#### Scenario: A diagnosed halt under the switch
- **WHEN** a build halts, its rescue writes a diagnosis, and the version's models file says `decide = "recommended"`
- **THEN** the supervisor runs, its amend of the spec delta with both trailers is taken, the run logs
  `supervise — <id>: decided`, and the version builds on and releases in the same run
- **AND** `report` prints `<id> · supervised 1.1 · <commit>`, and the `done` line names ` · supervised <id>`

#### Scenario: No switch
- **WHEN** the models file has no `decide`, and the rescue diagnoses the halt
- **THEN** no supervisor runs, and the version stays halted, its halt naming the diagnosis

#### Scenario: An amend touching a test
- **WHEN** the supervisor's commit touches a file under `tests/`
- **THEN** the version halts, naming the file, and the run logs no `supervise —` line

#### Scenario: A spent rescue
- **WHEN** under the switch a version halts again on a sub-task its rescue amended before in the run
- **THEN** the supervisor runs once, with no rescue
- **AND WHEN** the version halts on that sub-task again
- **THEN** no worker runs, and the halt names ` · rescued 1.1 · supervised 1.1`

#### Scenario: A refused amend at a converge halt
- **WHEN** the supervisor at an `amend needed` halt commits an amend of the change directory with no `Decided-by: supervisor`
  trailer
- **THEN** the version stays halted for the run, its halt reading `supervisor answered its halt`, and the closing line names
  `a re-run` as its need

#### Scenario: A blocking security card
- **WHEN** converge halts `amend needed` naming a security card of `high` severity, under the switch
- **THEN** the rescue diagnoses, no supervisor runs, and the version stays halted

#### Scenario: A blocking adversarial card outside security
- **WHEN** a converge cap leaves an open adversarial card of `high` severity whose category is `stability`, under the switch,
  and the rescue diagnoses the halt
- **THEN** the supervisor runs

#### Scenario: The brief kept at a passed cut
- **WHEN** a queued cut passes its check
- **THEN** the home folder's queue holds `briefs/<id>`, naming the brief's path, after the cut's queue entry is gone
- **AND WHEN** that version's supervisor runs under the switch
- **THEN** its prompt names `brief=<path>`
- **AND WHEN** a version cut by hand has its supervisor run
- **THEN** its prompt names no brief

#### Scenario: A note the supervisor settles
- **WHEN** under the switch a dependent's delta halts `integrating` on a semantic conflict, the rescue diagnoses it, and the
  supervisor stages its resolution of the version's delta and writes `integrate.settled`
- **THEN** the run logs `supervise — <id>: decided · integrating · <tree>`, spawns `mf-integrate` `with settled=supervisor`,
  whose merge commit holds that tree and names the note's heading as `the supervisor`, and the version builds on and releases
  in the same run

#### Scenario: A settle outside the text
- **WHEN** the supervisor at an `integrating` halt stages a file outside `openspec/` and `docs/` Markdown
- **THEN** the version halts, naming the file, the merge and the note stay open, and the run logs no `supervise —` line
- **AND WHEN** a later run meets the same open merge's halt
- **THEN** its rescue runs, no supervisor runs, and the version stays halted for the person

### Requirement: Converge's workers take their models from the models file

`.minions/changes/<change-id>/models.toml` MAY hold `[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`,
each with a `model` and an `effort`; `[converge]` stays the conductor's. `conduct.py` SHALL read them once with the run's plan.
It SHALL halt a version, before its worker starts, on a worker table that names an `executor`, or a `model` or `effort` holding
anything but letters, digits, `.`, `_` and `-`, and SHALL halt a version whose worker table later differs, as for any station's
table. It SHALL pass each worker table that names a model or an effort in the converge prompt as `and <role>=<model>/<effort>`,
`default` for the one absent, before any grant clause; with converge on Codex it SHALL pass none. Converge SHALL put each on its
worker's call and SHALL NOT read the models file itself. A fixer sent any blocking card SHALL run on adversarial's model and
effort, and otherwise on the fixer's. A role given none, or a host whose worker call takes no model, SHALL run its worker on the
conductor's model. The cut SHALL write the worker tables: conformance on the mid tier · high, adversarial on the strongest
tier · high, the fixer on the mid tier · high, and `[converge]` on the mid tier · medium unless the brief names converge's model,
each mapped to the offered models.

#### Scenario: The converge prompt names each worker's model
- **WHEN** a version's models file holds `[converge.adversarial]` with `model = "claude-opus-5-5"` and `effort = "high"`, and
  `[converge.fix]` with `model = "claude-sonnet-5-5"` and `effort = "high"`, and its converge runs on Claude
- **THEN** its converge prompt reads `Run the mf-converge skill for change <change-id> and adversarial=claude-opus-5-5/high and
  fix=claude-sonnet-5-5/high.`

#### Scenario: Converge on Codex
- **WHEN** a version's `[converge]` names `executor = "codex"` and its models file holds a worker table
- **THEN** its converge prompt names no worker model, and every worker runs on the conductor's model

#### Scenario: A worker table names an executor
- **WHEN** `[converge.conformance]` names `executor = "codex"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A worker table changes during the run
- **WHEN** a worker changes `[converge.fix]`'s model after the run read its plan
- **THEN** that version halts, naming the models file as changed during the run

#### Scenario: The fixer by grade
- **WHEN** converge dispatches a fixer sent a blocking card
- **THEN** the fixer runs on adversarial's model and effort
- **AND WHEN** it dispatches a fixer sent only non-blocking cards
- **THEN** the fixer runs on the fixer's model and effort

### Requirement: Converge hands each worker a bundle of what the change cites

At each freeze, converge SHALL run `skills/mf-converge/scripts/bundle.py`, which writes
`.minions/changes/<change-id>/bundle.md`: each repo decision the change's proposal, design, tasks or spec delta cites — by a
`decisions.md#d<n>` link, or by `D<n> · ` and that decision's title — in full; an index, each `### D` heading of
`docs/decisions.md`; and each living requirement the delta modifies or removes, in full. A decisions file with no `### D`
heading SHALL go into the bundle whole. A design's own decision ids SHALL cite no repo decision. Conformance SHALL read the
bundle in place of the decisions file and the living spec, opening a decision the index names only to trace its architecture
section; adversarial SHALL read the bundle's debt cards alone. `bundle.py` SHALL refuse to write through a link, and SHALL exit
2, writing nothing, on a file it cannot read.

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

### Requirement: An answered converge halt gets one amend round

Every converge `halt` line SHALL end `· head <sha>`, the `HEAD` it halted at. A converge halt other than the debt lock's, or an
older backlog lock's, SHALL be **answered** when `HEAD` is past its head, a descendant that is not it, and either both findings
files' `head:` is that head, or a commit past it is an **amend**: one parent, the subject `docs(<id>): amend the change
directory`, and paths under `openspec/changes/<id>/` alone — the person's, the rescue's or the supervisor's. `conduct.py`'s stage
SHALL then be `converge`, with no grant, and its converge check SHALL not read the old halt. A **halt before round 1** — a halt
other than a `verify: halt` in a run with no `start` line, not marked `· grant` — SHALL be void when `HEAD` is past its head, by
any commit, and SHALL be re-run when `HEAD` is its head: `conduct.py`'s stage SHALL be `converge` in both, and it SHALL start no
rescue for it. A run SHALL re-run a version once at the same head: one that halts before round 1 again SHALL stay out for the
rest of that run, a rejoin logging it still halted. Any other halt, and one whose head is no ancestor of `HEAD`, SHALL stand.

`skills/mf-converge/SKILL.md`, finding an answered halt, SHALL open a catch-up run marked `· amend` and run its catch-up round over
`<judged head>..HEAD`, the judged head being both findings files' `head:`, whatever their verdicts: the amend, the build's code
for a phase it added, and converge's own unverified fix. It SHALL open no new round 1 for it. Before the run's `start` line it
SHALL run each `Verify:` line the range adds to `tasks.md`, a ticked task's included, and halt `verify failed — <sub-task ids>`
when one fails. The run SHALL count its own rounds: one judge round and at most one fix round, `round:` carrying on past three;
a blocking finding open at its end SHALL halt `cap reached`. Conformance SHALL keep the full plan in its reading set, and its
stale-claim pass SHALL search the whole tree for each claim the amend changes. Finding a halt before round 1, it SHALL open a
plain new run, with no mark, as a fresh invocation does, save after a catch-up run, where a new run of the same mark runs the
catch-up round again. A run marked `· grant` that resumes SHALL stay a granted round.

#### Scenario: A gate red before round 1
- **WHEN** converge halts on a red gate before round 1 at head H, writing no `start` line, and the person asks a live run to take
  it back with no new commit
- **THEN** the run takes it back, and converge runs again in a plain new run
- **AND WHEN** it halts before round 1 again in that run
- **THEN** it stays out for the rest of the run, and a rejoin logs it still halted
- **AND WHEN** a commit past H follows
- **THEN** its stage is `converge`

#### Scenario: A two-line amend after a halt
- **WHEN** converge halted `amend needed`, and the person commits a two-line amend of the change directory
- **THEN** a run converges it in a catch-up run marked `· amend`, with no grant, judging `<judged head>..HEAD` in one round
- **AND** no run restarts at `round: 1`, and the version releases in the same run

#### Scenario: A fix after a cap halt
- **WHEN** a version halted at the cap, and the person commits a fix on its branch
- **THEN** a run converges it in a catch-up run marked `· amend` over `<judged head>..HEAD`, with no grant and no new round 1

#### Scenario: A cap halt with no fix
- **WHEN** a version halted at the cap, and `HEAD` is the findings files' `head:`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the person rewrote the history, so the halted head is no ancestor of `HEAD`
- **THEN** its stage stays `converge-halted`
- **AND WHEN** the cap is a granted round's, in a run with no `start` line, and `HEAD` is its head
- **THEN** its stage stays `converge-halted`, and it is no halt before round 1

#### Scenario: A halt past the judged head
- **WHEN** converge halts after its own fix commit, so its head is not the findings files' `head:`, and an amend follows
- **THEN** its stage is `converge`, and the amend round's range starts at the files' `head:`, the fix in it
- **AND WHEN** only a commit other than an amend follows
- **THEN** its stage stays `converge-halted`

#### Scenario: An amend adding a phase
- **WHEN** an amend answering a converge halt adds an unticked phase after the last
- **THEN** the version builds that phase, and the amend round's range holds the build's commits

#### Scenario: An amended Verify that fails
- **WHEN** the range adds a `Verify:` line to a ticked task, and the command fails
- **THEN** converge halts `verify failed — <sub-task id>` before its `start` line, and any commit past that head answers it

#### Scenario: A granted round resumes
- **WHEN** a granted round dies after its `fix` line, and a re-run resumes it
- **THEN** it verifies and ends with no pickup

## REMOVED Requirements

### Requirement: Review searches for stale claims

**Reason**: The review checker is renamed conformance.

**Migration**: *Conformance searches for stale claims* holds the same pass, over the living spec and decisions too.

### Requirement: Review judges test cost and traced coverage

**Reason**: The review checker is renamed conformance.

**Migration**: *Conformance judges test cost and traced coverage* holds the same passes.

### Requirement: A fix that reaches no surface takes its security head by recomputation

**Reason**: The security checker is renamed adversarial.

**Migration**: *A fix that reaches no surface takes its adversarial head by recomputation* holds the same rule over
`adversarial.md`.
