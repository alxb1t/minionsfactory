# Decisions

The choices in force today, each with its reason. A decision states a choice that could have gone another way; a
rule whose breach is a defect is a [principle](principles.md). An entry is written in the present tense and holds
no history: when a change overturns one, it edits this page, and its own `design.md` keeps how that came about.

An id is never reused or renumbered. A new decision takes the next number, in the group it belongs to.

```
  grill ───▶ cut ───▶ build ───▶ converge ───▶ release
    └─ Planning ─┘       └─ The check loop and the release ─┘
       D5…D10                        D11…D17

  The shape D1…D4 · The target repo D18 · Repo conventions D19…D23, D36, D37 · The autonomous line D24…D35
```

## The shape

What MinionsFactory is, and what it is not.

### D1 · One feature is one change, one version, one release

**A change is the unit of work and of release: one small feature, its own branch, its own version, its own tag. A
minor delivers one feature; a patch delivers none. The phase count is not bounded: phases may be many when they are
all about one thing.**

- **Why:** small is what makes acceptance testable and a release revertable.

### D2 · The product is the practice and its skills

**What MinionsFactory ships is a way of working — grill, cut, build, converge, release — as installable skills. It
is not a framework, and it installs nothing into the repo it works on.**

- **Why:** a tool installed per repo is a copy of the contract in every target.

### D3 · One line of stations, conducted by a person or by an LLM

**The stations are the skills. A person conducts them today; an LLM conductor, held by deterministic checks, is
designed to run the same skills unattended. There is no third way to run the line.**

- **Why:** one source for what a station does. A second implementation of every station drifts from the first.
- **Rejected:** a deterministic runner: no judgement for a thin brief, and a second copy of every station as a role
  prompt.

### D4 · This repo's own gate is Python on uv

**`uv` · `ruff` · `ty` · `pytest`, behind `make gate`. The skills assume only the `gate` target, so a target repo
may use any toolchain.**

- **Why:** a working gate beats a generic abstraction, and the `Makefile` target is the whole interface.

## Planning

How an idea becomes a change the build can run.

### D5 · The planning line is adopted, not built

**A change is grilled with the `grilling` skill and written with the OpenSpec CLI: its `instructions` shape each
artifact, its `validate --strict` is the check on a change. MinionsFactory adds only the conducting.**

- **Why:** both tools are maintained elsewhere; a planning line of our own is a surface to maintain.
- **Rejected:** `to-spec`, which collides with `openspec instructions` · `to-tickets`, which is redundant · a
  `docs/agents/` adapter, which has no reader.

### D6 · A change's artifacts are its record

**`proposal.md`, `design.md`, `tasks.md` and the spec delta are the whole record of a change; no planning document
is kept beside them. `design.md` carries the measurement behind each decision, not only the conclusion. This page
holds what is in force; a change that overturns an entry edits it, and its `design.md` keeps the history.**

- **Why:** a second copy drifts, and a reason kept nowhere is re-derived by the next change.

### D7 · The cut writes to the build's input contract

**`mf-build` owns the list of what a change must meet (`I1…`) and the prose rules (`P1…`); `mf-cut-change` carries
the same ids and checks them before a person reads the change. The person's OK precedes the commit.**

- **Why:** a change the build cannot run is cheapest to catch at the cut.
- **Held in step by:** the id scans in `tests/test_skills.py`.

### D8 · The OpenSpec CLI is recorded, not pinned, and stays out of the gate

**Its version is written in `CLAUDE.md`; nothing in `make gate` or CI runs it. The cut runs `openspec validate`; the
gate does not.**

- **Why:** a moving CLI version can hand an author different instructions, but can never turn CI red.
- **Accepts:** a spec that drifts from OpenSpec's format is caught only at the next cut. Reopen if a release folds a
  spec `validate` rejects.

### D9 · Relax scope, never acceptance

**A change too big to build is split or rescoped. Its acceptance is never loosened: every requirement keeps a check
a test could express.**

- **Why:** a vague acceptance is what lets an unfinished change read as done.

### D10 · A change with no behaviour change says so

**It declares `skip_specs: true` and keeps an empty `specs/`. No requirement is invented to satisfy a validator, and
a deleted capability leaves no marker directory behind.**

- **Why:** an invented requirement corrupts the spec tree; a tombstone nothing checks blocks validation.

## The check loop and the release

What happens between the last phase and the tag.

```
  build ──▶ simplify, in place ──▶ freeze the diff ──▶ review ‖ security ──▶ all clean? ── yes ──▶ release
                                                            ▲                    │ no
                                                            └── verify ◀── fix ◀─┘
```

### D11 · The checkers are adopted engines

**Review, security and simplify are the community skills `/code-review`, `/security-review` and `/simplify`, run
unmodified. MinionsFactory writes only the conducting: the freeze, the dispatch, the findings contract, the
rounds.**

- **Why:** a review engine is someone else's maintained work; the conducting is what was missing.
- **Accepts:** an engine's assumptions become ours. `/security-review` reads `origin/HEAD` and does not load in a
  repo with no remote. Reopen when a target has no remote, or an engine changes its inputs.

### D12 · Review, security and simplify are kept apart

**Review looks for too little, security for new exposure, simplify for too much. Each is its own pass.**

- **Why:** one reader asked to both add what is missing and cut what is surplus does neither well.

### D13 · Simplify runs inside the build and blocks nothing

**The build closes with a simplify pass that edits in place and re-runs the gate. Its edits are then inside the
frozen diff, so review judges them. Simplify is a producer, not a checker: it holds no verdict.**

- **Why:** run last, it would land unreviewed edits after the final check. Given a verdict, taste would spin the
  loop.
- **Rejected:** simplify as a third read-only station.

### D14 · Converge is optional, and a skip is stated

**A change may be released without the check loop. The release then writes `converge: skipped` into its report and
the release commit. The diff patch or either findings file means converge ran, and then both files must exist and
be clean.**

- **Why:** a prose-only change read by hand does not earn the engine passes, and a silent skip would look like a
  pass.
- **Accepts:** a checkout that lost `.minions/` reads as skipped, and the skip line is its only record. Reopen
  when an unattended run releases from a fresh checkout.

### D15 · Anchored harms block; drift never does

**Each checker grades on its own scale, and the anchors set the floor.**

| checker | grades | blocks on |
|---|---|---|
| review | `blocking` · `drift` · `nit` | `blocking` |
| security | `critical` · `high` · `medium` · `low` | `critical` · `high` |

- **The anchors always block:** data loss, spend, exposure of personal data or secrets, silent wrong output.
- **Drift never blocks:** prose the code contradicts.
- **A repeat goes up one level:** a finding that repeats a backlog card.
- **Why:** left to judgement, a costly defect is graded a nit and a typo blocking. The anchors fix the floor; the
  drift tier keeps prose out of the loop.

### D16 · Deferred work is a card in the repo's backlog

**Once the loop is clean, converge fixes this run's small cards and its drift in one more round.
A card is a finding of the check loop, or of the hand read that stands in for it; work with no finding behind it is
planning, and lives outside the repo. Everything else becomes a card — why, when, what, priority, fix and size,
trigger, still true? — in the gitignored `.minions/backlog.md`. The backlog never blocks a release; a paydown
change lists the cards it closes and its release deletes them.**

- **Why:** small fixes are cheapest while the context is fresh. A backlog that blocks would block every release, and
  one kept outside the repo cannot cite `path:line`.
- **Accepts:** the backlog is gitignored, so it lives on one machine. Reopen when a second person or a cloud run
  needs to read it.

### D17 · The release verifies, folds, archives, tags, and stops

**It re-runs the gate, folds the spec delta into `openspec/specs/`, archives the change, cuts the changelog and tags
— locally. It never merges, never pushes, never edits feature code. Fold and archive land in one commit.**

- **Why:** merging and publishing are a person's acts. A fold without its archive leaves the spec tree and the
  change disagreeing.
- **Rejected:** `openspec archive` for the fold: the release does the same fold inside a gate-verified commit.

## The target repo

What the skills need from a repository they work on.

### D18 · The contract with a target repo is a layout on disk

**The skills need the layout below from a repo, and nothing else. They install nothing into it.**

```
<target>/
├── openspec/specs/      the living spec
├── openspec/changes/    the active change, and the archive
├── Makefile             with a `gate` target
├── CLAUDE.md            what is true of this repo
└── .minions/            run output, gitignored
```

- **Why:** what travels between repos is a layout a reader can find, not a tool.

## Repo conventions

How versions, ids and commits are written, what happens to what is replaced, and what a spec and a test are held
to.

### D19 · One version line

**A change's declared version, the `CHANGELOG.md` release, the annotated tag and the project's version file are one
value. The changelog follows Keep a Changelog: each phase appends under `Unreleased`, the release cuts the
heading.**

```
proposal.md `version: vX.Y`  =  CHANGELOG `## [X.Y.0]`  =  tag `vX.Y.0`  =  the version file
```

- **Why:** one source of version truth leaves nothing to reconcile.

### D20 · A change id is an identifier, numbered in ship order

**`<digits>-<slug>`, never renamed once cut. The number is higher than every id before it; the cut takes the id it
is given; a version is numbered at its cut, so planned work carries a name, not a number.**

Example: `0011-cut-and-gate`, on the branch `<version>_cut_and_gate`.

- **Why:** a renamed id splits a change across two trailer values. A number given before the cut is a number to
  change later.

### D21 · Every commit names its change

**A commit ends with `Change: <change-id>`, in the trailer block, contiguous with `Co-Authored-By:`.**

```
Co-Authored-By: <the session's attribution line>
Change: 0011-cut-and-gate
```

- **Why:** from a commit you find the change; from a change, `git log --grep` finds every commit. A blank line
  inside the block silently breaks it.

### D22 · Subscription for a person's local run, an API key for a server

**A run a person starts on their own machine uses their Claude Code subscription. Anything always-on, scheduled or
in CI uses an API key.**

- **Why:** the terms draw the line between personal local use and a server, not between a human and a script.
- **Accepts:** the autonomous line's cloud and nightly runs sit on the server side of that line. Reopen at the
  change that schedules a run.

### D23 · Superseded is deleted, harvested first

**A file, a skill or a page that is replaced is deleted, not archived or bannered. Before it goes, what it alone
held is moved to a live file. Git keeps the old text; `openspec/changes/archive/` is the only archive.**

- **Why:** a second place for the truth drifts, and a stale page is read as current.

### D36 · Specs are bound by review, not by a checker

**A scenario says what proves it in prose; review judges whether a test proves it. No marker ties a test to a
scenario, and the gate does not check the binding.**

- **Why:** a binding checker is per-language code no target repo can run, and it made every spec carry keys only it
  read.
- **Gave up:** the gate failing on a requirement with no test.

### D37 · Tests hold what is true now; nothing tests an absence

**A test asserts a behaviour or a rule the repo holds today. A retired name leaves the tree in the commit that
retires it, checked once by that change's acceptance. A scan may name what a live rule forbids; it never lists
retired names.**

- **Why:** a scan for retired words grows with every retirement, and tests a history rather than the system.
- **Gave up:** a reintroduced name turning the gate red. Review's stale-claim pass looks for it instead.

## The autonomous line

**Designed, not built.** Each entry is the design in force; the change that builds one removes nothing here unless
it overturns it. The design itself is [autonomous](autonomous.md).

```
  LLM conductor ──▶ a stage, in a fresh subagent ──▶ mfa_check.py: exit code = verdict ──▶ mfa_log.py
        ▲                                                   │ exit ≠ 0 ──▶ halt
        └──────────────── next stage ◀──────────────────────┘
```

### D24 · An LLM conducts; scripts decide whether it happened

**The conductor is an LLM that picks what runs next. A deterministic script judges each stage from disk, its exit
code the verdict, and another writes the run log. A non-zero exit halts the run, whatever the conductor thinks.**

- **Why:** judgement is needed for a thin brief; "done" from a model is only a claim, and a log is not the model's
  to forget.
- **Rejected:** a deterministic driver · an LLM alone.
- **Accepts:** judgement between one check and the next is unchecked. The `assumed` marks and a person's morning
  read catch it.
- **Accepts:** harness permissions are not a boundary: `Bash(git commit:*)` did not block `git commit -am`. Reopen
  before an unattended run on a repo someone else wrote.

### D25 · Each stage runs in a fresh subagent

**The conductor dispatches each skill as a new subagent and judges it from disk, never from its report.**

- **Why:** [no station verifies its own work](principles.md#no-station-verifies-its-own-work), applied to the
  conductor; and its own context stays short across a night of versions.
- **Rejected:** running the skills inline in the conductor.

### D26 · The autonomous line leaves the `mf-*` skills untouched

**Its skills live in `autonomous/skills/`, outside `skills/`: `make install-skills` and the scans do not see them.
Building the autonomous line edits no `mf-*` skill.**

- **Why:** the `mf-*` skills work; an experiment must not change them.
- **Accepts:** a second set of stations while the experiment runs, which
  [D3](#d3--one-line-of-stations-conducted-by-a-person-or-by-an-llm) forbids as an end state. Reopen when the autonomous line has run a
  target end to end.

### D27 · A branch and a worktree per version, outside the repo

**The default branch is never touched. The main checkout holds the loop branch; each version gets its own branch and
its own worktree in a sibling directory.**

- **Why:** no branch switching; a crash leaves its files where they were; versions cannot see each other's
  uncommitted work; nothing run in the repo sees a worktree.
- **Rejected:** switching branches in one checkout · worktrees inside the repo.

### D28 · A version branch writes no shared file

**It writes its own change directory, the code, and fragments. The spec fold, the archive, `CHANGELOG.md`, the
version bump, the release commit and the backlog are written at integration, one version at a time.**

- **Why:** the only conflicts left between versions are real code conflicts.
- **Rejected:** resolving changelog and spec conflicts at merge.

### D29 · Integration merges in, then fast-forwards

**The loop branch is merged into the version branch; if the base moved, a catch-up round and the gate run; the
release runs; then the loop branch fast-forwards.**

- **Why:** the judged head stays an ancestor, so the catch-up round judges exactly what the merge brought.
- **Rejected:** rebase, which rewrites the commits converge judged.

### D30 · Run state is derived, never stored

**Where each version stands is computed from git, the worktrees and the change files. There is no state file.**

- **Why:** [state lives on disk](principles.md#state-lives-on-disk), applied: a stored state is a second truth that
  drifts when a subagent dies between its work and its write.
- **Rejected:** `state.json`.

### D31 · One state directory for a run

**Every autonomous stage and both scripts take `state-dir`: the main checkout's `.minions/`, absolute. Findings, the
run log and backlog fragments live there, not in a worktree.**

- **Why:** a worktree is removed after integration; its evidence must not go with it.
- **Rejected:** each worktree's own `.minions/`.

### D32 · One run log, written only by a script

**Every level of a run logs to one file through `mfa_log.py`: insert-only, newest on top, a fixed event list,
`spawn` and `finish` in pairs carrying outcome, duration and tokens, a lock per insert. It is copied into the
tracked run record once, at the end or at a halt.**

- **Why:** the log is the only witness of a night run; its clock and its format are not the model's to forget.
- **Rejected:** prose logging · a tracked log written as it runs, which dirties the tree and commits after the
  judged head.

### D33 · A run's input is in the target repo

**`roadmap/roadmap.md` gives each version its change id and its `after:` list; `roadmap/briefs/` carries every human
decision. A question the brief does not settle takes the recommendation, marked `assumed`.**

- **Why:** a cloud session sees only the repo, and ids assigned by the roadmap cannot collide when versions run side
  by side.
- **Rejected:** ids as highest-plus-one · reading the plan from outside the repo.
- **Accepts:** an `assumed` answer is a decision no person made. The morning read is its only check.

### D34 · Stop at the first halt; resume from disk

**A failed check ends the run. On resume, build keeps a dirty tree; every other stage stashes it, popped only by
message, and restarts; converge restarts at round one.**

- **Why:** a re-run is then always safe. The stash is shared across worktrees, so a bare pop can take another
  version's.
- **Rejected:** for now, retry and remedy by the conductor.

### D35 · Sequential is parallel at width one

**Branches, worktrees, fragments, roadmap-assigned ids and serial integration are the parallel path. A run today
uses it with one version at a time; only the width changes later.**

- **Why:** parallelism becomes a count, not a rewrite of every skill.
- **Rejected:** a sequential design retrofitted later.
