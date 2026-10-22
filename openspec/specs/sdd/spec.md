# Capability: sdd

## Purpose

The rules the `mf-*` skills hold, each proved by a scan over the skill text.

## Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **WHEN** every `skills/*/SKILL.md` is scanned
- **THEN** no file names `minions.toml`
- **AND** `mf-build`, `mf-converge` and `mf-release` each name both `make gate` and `make -n gate`

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
- **WHEN** `mf-release` and `mf-converge` are scanned
- **THEN** `mf-release` names `converge: skipped — no findings files`
- **AND** `mf-release` does not name `A missing findings file is not clean`
- **AND** `mf-converge` names `A missing findings file is not clean`

#### Scenario: The release names both halts
- **WHEN** `mf-release` is scanned
- **THEN** it names `one file without the other is a halt`
- **AND** it names `The diff patch without a findings file is a halt`

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

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix to one file, `.minions/backlog.md`,
under a heading for its change. After both verdicts are clean, and only while a round remains under the cap, it
SHALL pick up this run's non-blocking cards whose fix is sized `one line` or `a test`, and every `drift` card, fix
them, and verify them in a normal round. It SHALL NOT name a per-version backlog file. It SHALL delete a backlog card
only when a verified repeat of it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `.minions/backlog.md`
- **AND** it names both pickup sizes, `one line` and `a test`
- **AND** it does not name `_backlog.md`

### Requirement: The release does not read the backlog

`skills/mf-release/SKILL.md` SHALL NOT hold a release on deferred work. It SHALL name no per-version backlog file.
A paydown change lists the card ids it closes under the `backlog:` key of its `proposal.md` frontmatter:
`skills/mf-cut-change/SKILL.md` SHALL write that key, and `mf-release` SHALL delete exactly those cards from
`.minions/backlog.md` after the fold.

#### Scenario: The release names no per-version backlog, and the paydown key is shared
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-cut-change/SKILL.md` are scanned
- **THEN** `mf-release` does not name `_backlog.md`
- **AND** `mf-release` names `.minions/backlog.md`
- **AND** `mf-release` and `mf-cut-change` each name `backlog:`

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
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, counted against the cap, with no
pickup.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-converge/SKILL.md` are scanned
- **THEN** `mf-release` names the check `HEAD equals the head:`
- **AND** `mf-converge` names `catch-up round`

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/SKILL.md` SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `blocking | drift | nit`
- **AND** it names each anchor: `data loss`, `spend`, `exposure`, `silent wrong output`

### Requirement: A repeated finding escalates

Each station SHALL read `.minions/backlog.md`. A finding that repeats a backlog card SHALL name that card's id in its
**Related** field as `repeat of <id>`, and SHALL go up one level: security by one step, a review `nit` or `drift` to
`blocking`.

#### Scenario: Converge names the repeat rule
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `repeat of`
- **AND** it names `up one level`

### Requirement: Review searches for stale claims

The review station SHALL run a **stale-claim pass** after its engine: every path, symbol, verb, route or count the
diff renames, deletes or changes is searched across the rest of the tree, and each mention the change made false is
carded as `drift`. The station SHALL say in its Summary that the pass ran, and `skills/mf-converge/SKILL.md` SHALL
check that it did.

#### Scenario: Converge names the stale-claim pass
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `stale-claim pass` at least twice: where the station runs it and where the conductor checks it

### Requirement: A fix's test fails without the fix

For a card whose fix size includes `a test`, the fix station SHALL paste the new or extended test's failing run from
before the fix into the card's **Status** note; an extended test's run is the existing test with the new step added.
The verify pass SHALL reopen the card when that run is missing, or when the test does not exercise the card's
**When you'd hit it** scenario. Fixes to docs only are exempt.

#### Scenario: Converge names the red run and the verifier's check
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `failing run from before the fix`
- **AND** it names `When you'd hit it` in the verify step

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `backlog`, `halt` and `done`, and a
run SHALL end on `halt` or `done`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `_status_log.md`
- **AND** it names `newest on top`
- **AND** it names each event: `start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`,
  `backlog`, `halt`, `done`

### Requirement: A skill infers the one active change

`skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL take `change-id`
from their parameter when one is given. When none is given, each SHALL take the candidates from
`git ls-files openspec/changes/`, without `archive/`: no candidate SHALL halt with `no active change`, several SHALL
halt listing them, and exactly one SHALL be used only if the current branch equals `v<version>_<slug>` built from
that change's `proposal.md` `version:` and its id, else halt naming both. The skill SHALL echo the id with
`(inferred:` before any other work, and SHALL NOT forbid inference.

#### Scenario: Build, converge and release each name the inference and its halts
- **WHEN** `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` are scanned
- **THEN** each names `git ls-files openspec/changes/`
- **AND** each names `no active change`
- **AND** each names `(inferred:`
- **AND** none names `Never infer it`

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
- **WHEN** the `## Step 8 — Self-check` section of `mf-cut-change` is scanned
- **THEN** it names `run none of them`

### Requirement: Converge and the release halt on a gate the cut did not plan

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each halt, before judging or releasing, when
`make -n gate` prints other than the dry run of the base's `Makefile`, and no task in `tasks.md` as the cut
commit holds it names the gate recipe. The cut commit SHALL be the one commit that adds the change's `design.md`;
more than one SHALL be a halt. When such a task names the recipe, each SHALL show the two dry runs' diff, and SHALL
halt on a command line the base's dry run prints and the branch's does not, unless that task names it.

#### Scenario: Both stations name the dry-run check
- **WHEN** `mf-converge` and `mf-release` are scanned
- **THEN** each names `changes the gate's dry run and no task at the cut names the gate recipe`

### Requirement: No station deletes a findings file or the diff patch

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each forbid deleting, moving, renaming or
emptying a findings file or the diff patch; clearing them SHALL be the human's act.

#### Scenario: Both stations carry the rule
- **WHEN** `mf-converge` and `mf-release` are scanned
- **THEN** each names `Never delete, move, rename or empty a findings file or the diff patch`

### Requirement: The bootstrap writes the target layout

`skills/mf-bootstrap/templates/` SHALL hold a template for every entry of the target layout that D18 in
`docs/decisions.md` draws: for a directory, a template under it; for a file, the file. `.minions/` SHALL be a line
of the `.gitignore` template, not a template under it. The templates SHALL also hold `CHANGELOG.md` and
`README.md`. A template's target path SHALL be its path under `templates/` without the `.tmpl` suffix. The
`Makefile` template's `gate` recipe SHALL run `openspec validate --all --strict --no-interactive`.

#### Scenario: Every entry of D18's tree has a template
- **WHEN** D18's tree is read from `docs/decisions.md` and the templates are listed
- **THEN** each directory entry other than `.minions/` has a template under it
- **AND** each file entry has a template
- **AND** the `.gitignore` template holds the line `.minions/`
- **AND** `CHANGELOG.md` and `README.md` have templates

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
- **WHEN** the `## Step` section whose heading names a report is read in each of these skills
- **THEN** it names `at most three sentences — what happened, the gate's exit code, and anything the human must act on`
- **AND** it names `Next:`

### Requirement: The cut commits without waiting, unless it adds a dependency

`skills/mf-cut-change/SKILL.md` SHALL commit the change once its self-check passes, without waiting for the human.
It SHALL wait for the human's OK before the commit only when `## Dependencies` is not `None.`, or when a
self-check item cannot be met. An edit after the commit SHALL be a further commit on the branch.

#### Scenario: The cut's show step commits without waiting
- **WHEN** the `## Step 9 — Show, then commit` section of `mf-cut-change` is scanned
- **THEN** it names `commit without waiting`
- **AND** it names `## Dependencies`

### Requirement: The release merges and pushes on the person's yes

`skills/mf-release/SKILL.md` SHALL, after the tag, ask the person once whether to merge and push. On yes it SHALL
halt when the default branch is not an ancestor of the branch, merge with `--no-ff`, check that the merged tree
equals the branch's, and push the default branch and the tag to `origin`. It SHALL never force a push, never push
the version branch, and SHALL merge without pushing when there is no `origin`. On anything but yes it SHALL print
the commands and stop.

#### Scenario: The release names the merge and its guards
- **WHEN** `mf-release` is scanned
- **THEN** it names `Merge <branch> into <default-branch> and push?`
- **AND** it names `git merge-base --is-ancestor <default-branch> HEAD`
- **AND** it names `git merge --no-ff`
- **AND** it names `git diff --quiet <branch> <default-branch>`
- **AND** it names ``never `--force` ``

### Requirement: A HUMAN phase is handed over as a checklist of commands

The `I14` row of the `## Input contract` in `skills/mf-cut-change/SKILL.md` and `skills/mf-build/SKILL.md` SHALL
require a HUMAN phase's sub-tasks to be exact commands with real values. `skills/mf-build/SKILL.md` SHALL halt on
an unworked HUMAN phase with a checklist: one line per step, each command in an `sh` block, secrets by env-var
name, the closing checks, and `Next: /mf-build`.

#### Scenario: Both skills require commands, and the build prints them
- **WHEN** the `## Input contract` section of `mf-cut-change` and of `mf-build` is scanned
- **THEN** each names `exact commands with real values`
- **AND WHEN** the `## Step 2 — The per-phase ritual` section of `mf-build` is scanned
- **THEN** it names `the person's checklist`, ```` ```sh ```` and `Next: /mf-build`

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
as consolidation, not as weakening the gate, and SHALL halt on a deletion outside that table. The fix station in
`skills/mf-converge/SKILL.md` SHALL never delete or merge a test.

#### Scenario: The build names the table, and the fix station never deletes
- **WHEN** `mf-build` and `mf-converge` are scanned
- **THEN** `mf-build`'s `## Step 2 — The per-phase ritual` names `` `## Tests` table ``
- **AND** `mf-converge`'s `## Step 6 — The fix station (a fresh worker, inside this loop)` names
  `never deletes or merges a test`

### Requirement: Review judges test cost and traced coverage

The review station SHALL run a **test-cost pass** after its engine, carding each new end-to-end test that a lower
layer proves, that re-opens a state another test reaches, or that runs on engines its outcome cannot depend on. When
the freeze removes a test, it SHALL run a **coverage-trace pass**, tracing each removed assertion and scenario id to
the test that runs it now against the design's `## Tests` table. Each round SHALL run both passes over that round's
freeze. The station SHALL say in its Summary that each pass ran, and `skills/mf-converge/SKILL.md` SHALL check that
it did.

#### Scenario: Converge names both passes where they run and where they are checked
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `test-cost pass` at least twice
- **AND** it names `coverage-trace pass` at least twice

### Requirement: The release records the gate's time

`skills/mf-release/SKILL.md` SHALL time precondition 1's gate run and SHALL write one `Gate:` line under the new
release heading in `CHANGELOG.md`: that time, CI's latest green run on the default branch read with `gh run list`
or `none`, and the previous release's `Gate:` line's times.

#### Scenario: The release names the line and the CI read
- **WHEN** `skills/mf-release/SKILL.md` is scanned
- **THEN** it names `Gate: local`
- **AND** it names `gh run list`

### Requirement: The bootstrap's `AGENTS.md` states the rules for tests

`skills/mf-bootstrap/templates/AGENTS.md.tmpl` SHALL hold a `## Tests` section stating where a test goes, that a
step in an existing test comes before a new one, which engines a test runs on, and that a test is deleted or merged
only as a change's `## Tests` table names it.

#### Scenario: The template has the section
- **WHEN** `skills/mf-bootstrap/templates/AGENTS.md.tmpl` is read
- **THEN** one of its lines is `## Tests`

### Requirement: The stations use AGENTS.md as target context

The stations SHALL use root `AGENTS.md` as the target-context file without a `CLAUDE.md` fallback.
Bootstrap SHALL write that file from its template and retain the existing collision safeguards.
Cut, build, converge and release SHALL explicitly read it and the mandatory context it identifies before work.
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
- **THEN** it creates `AGENTS.md` and retains the template's test policy

### Requirement: Skills install into the shared user directory by default

The installer SHALL default to `~/.agents/skills`, preserve the `SKILLS_DIR` override and retain its existing
symlink, collision-refusal and checkout-specific uninstall behavior. It SHALL leave previous installations alone.

#### Scenario: The operator uses the default destination
- **WHEN** `make install-skills` runs without a destination override
- **THEN** it targets the shared user skills directory

#### Scenario: The operator supplies a destination
- **WHEN** `SKILLS_DIR` names a different destination
- **THEN** installation and uninstallation use that destination with their existing safeguards

### Requirement: Engine selection follows the executor

Build and converge SHALL identify and report the executing agent from runtime evidence, not from its model,
provider or editor. Positively identified Claude Code SHALL retain native `/simplify`, `/code-review` and
`/security-review` invocation and the existing native engine restrictions. Other and unidentified executors
SHALL use the bundled generic instructions through the host's instruction-loading facilities.

#### Scenario: Claude Code has its native commands
- **WHEN** Claude Code executes a pass and its required native command is invocable
- **THEN** the station uses that native command without replacing its engine with generic instructions

#### Scenario: A native command is unavailable
- **WHEN** Claude Code cannot invoke the required native command
- **THEN** the station halts naming that command
- **AND** generic execution requires an explicit user instruction to switch that run

#### Scenario: A Claude model runs outside Claude Code
- **WHEN** a Claude model runs in another executor, including a Zed OpenRouter thread
- **THEN** the station uses the generic path

#### Scenario: The executor is unidentified
- **WHEN** the session exposes no reliable executor identity
- **THEN** the station reports and uses the generic path without guessing from the model name

### Requirement: Generic passes preserve the station boundaries

Generic simplify SHALL inspect the change for unnecessary complexity and duplication, preserve behavior and
apply improvements before independent checking. The build SHALL retain its gate and separate simplify-commit
ordering. Generic review SHALL check correctness, spec compliance, target standards and tests, including the
existing stale-claim, test-cost and coverage-trace passes.

Generic security SHALL inspect changed behavior and relevant surrounding context for concrete vulnerabilities,
secrets exposure, unsafe permissions and trust-boundary failures, including prompt and tool instructions where
relevant. Findings SHALL cite evidence and use the existing cards, severity, verdict, verification and release
contracts. Review and security SHALL edit their own findings files, leave code changes to the fix station, and
keep findings local rather than publish external comments.

#### Scenario: A generic pass receives a frozen change
- **WHEN** the station receives the explicit base and head, patch and change artifacts
- **THEN** it reads relevant source context and judges that range without requiring a GitHub remote or review plugin
- **AND** it reports the scope it actually inspected rather than declaring an uninspected change clean

#### Scenario: A generic worker verifies a fix
- **WHEN** fresh review and security workers receive their findings and the fix range
- **THEN** each promotes verified findings or reopens them under the existing contract
- **AND** review receives the design's test table and runs the required review passes

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Claude Code SHALL retain parallel review and security dispatch. The generic path SHALL prefer parallel dispatch
and permit sequential independent workers over the same frozen head, completing both before a fix begins.
The station SHALL halt before work requiring an unavailable worker capability, naming that capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their generic role resources when the generic branch executes.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package.
Missing, empty and escaping targets SHALL fail the gate's resource-integrity check.

#### Scenario: The generic instruction package is incomplete
- **WHEN** a referenced role resource is missing, empty or resolves outside its skill package
- **THEN** the resource-integrity check reports the referring skill and the invalid target

#### Scenario: The package contains valid role resources
- **WHEN** the shipped resource references resolve within their packages to nonempty files
- **THEN** the resource-integrity check passes without treating illustrative change-document links as resources

### Requirement: Model suggestions use exposed capabilities

The cut SHALL bound model suggestions by the target's declared menu or the models exposed in the session.
It SHALL suggest an effort setting only when that setting is supported. With no model menu it SHALL state the
needed capability without inventing model names; with no effort control it SHALL omit the effort setting.
Authentication and provider configuration SHALL remain the operator's responsibility.

#### Scenario: The session exposes no model menu or effort control
- **WHEN** the cut produces its station suggestions
- **THEN** it describes the required model capability and omits unsupported controls
- **AND** it does not change the session's selected model or provider configuration

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
