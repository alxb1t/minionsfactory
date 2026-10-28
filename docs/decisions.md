# Decisions

The choices in force today, each with its reason. A decision states a choice that could have gone another way; a
rule whose breach is a defect is a [principle](principles.md). An entry is written in the present tense and holds
no history: when a change adds or overturns one, it edits this page in one of its phases, and its own
`design.md` keeps how that came about.

An id is never reused or renumbered. A new decision takes the next number, in the group it belongs to.

```
  grill ───▶ cut ───▶ build ───▶ converge ───▶ release
    └─ Planning ─┘       └─ The check loop and the release ─┘
       D5…D10, D38                   D11…D17, D40, D43

  The shape D1…D4 · The target repo D18 · Repo conventions D19…D23, D36, D37, D39, D41, D42
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
is not a framework. The stations install nothing into the repo they work on; `mf-bootstrap` writes a new
repo's starting files, once. A skill may bundle a standard-library script, run from its own package and never
copied into the target ([D43](#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)).**

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

### D5 · A change is planned with `mf-plan` and written with the OpenSpec CLI

**`mf-plan` grills a version to settled decisions and writes the brief; the OpenSpec CLI's `instructions` shape
each artifact, and its `validate --strict` is the check on a change. `mf-plan` takes its frontier rounds from the
adopted `grilling` skill it replaces.**

- **Why:** the line's practice must run on every executor, and a plugin one host carries cannot; the OpenSpec CLI
  is maintained elsewhere and stays adopted.
- **Rejected:** wrapping `grilling` — a plugin other hosts lack, text that moves upstream · `to-spec`, which
  collides with `openspec instructions` · `to-tickets`, which is redundant · a `docs/agents/` adapter, which has no
  reader.

### D6 · A change's artifacts are its record

**`proposal.md`, `design.md`, `tasks.md` and the spec delta are the whole record of a change; no planning document
is kept beside them. `design.md` carries the measurement behind each decision, not only the conclusion.**

- **Why:** a second copy drifts, and a reason kept nowhere is re-derived by the next change.

### D7 · The cut writes to the build's input contract

**`mf-build` owns the list of what a change must meet (`I1…`) and the prose rules (`P1…`); `mf-cut-change` carries
the same ids and checks them before it commits the change ([D38](#d38--the-cut-commits-without-waiting)).**

- **Why:** a change the build cannot run is cheapest to catch at the cut.
- **Held in step by:** the id scans in `tests/test_skills.py`.

### D8 · The OpenSpec CLI is recorded, not pinned, and stays out of this repo's gate

**Its version is written in `AGENTS.md`. This repo's `make gate` and CI never run it; the cut runs
`openspec validate`. A target's gate may: the one `mf-bootstrap` writes validates the specs.**

- **Why:** a moving CLI version can hand an author different instructions, but can never turn CI red.
- **Accepts:** a spec that drifts from OpenSpec's format is caught only at the next cut. Reopen if a release folds a
  spec `validate` rejects.
- **Why a target's gate may:** a new target has no CI to turn red, and its spec is all it has to check.

### D9 · Relax scope, never acceptance

**A change too big to build is split or rescoped. Its acceptance is never loosened: every requirement keeps a check
a test could express.**

- **Why:** a vague acceptance is what lets an unfinished change read as done.

### D10 · A change with no behaviour change says so

**It declares `skip_specs: true` and keeps an empty `specs/`. No requirement is invented to satisfy a validator, and
a deleted capability leaves no marker directory behind.**

- **Why:** an invented requirement corrupts the spec tree; a tombstone nothing checks blocks validation.

### D38 · The cut commits without waiting

**`mf-cut-change` commits the change once its self-check passes, and the person reads it after. A `## Dependencies`
that is not `None.`, and a self-check item the cut cannot meet, still wait for the person's OK. Starting
`/mf-build` is the OK for the `Verify:` commands.**

- **Why:** the cut is almost always right, and a wrong one costs one more commit; the wait cost a *"please commit"*
  every time.
- **Accepts:** an edit after the read is a further commit on the branch, before the build.

## The check loop and the release

What happens between the last phase and the tag.

```
  build ──▶ simplify, in place ──▶ freeze the diff ──▶ review ‖ security ──▶ all clean? ── yes ──▶ release
                                                            ▲                    │ no
                                                            └── verify ◀── fix ◀─┘
```

### D11 · Engines follow the executor

**Claude Code invokes native `/code-review`, `/security-review` and `/simplify`, keeping their scope and
restrictions. Other and unidentified executors load the bundled generic roles. The station reports the route
from executor evidence; model, provider and editor names do not select it.**

- **Why:** native engines stay useful while the instruction package travels between capable hosts.
- **Accepts:** a missing required native command halts; switching that run to generic needs explicit user choice.
  Native `/security-review` needs a remote; generic security judges the explicit range without one.
- **Rejected:** silent native fallback, provider routing and a new review-plugin dependency.

### D12 · Review, security and simplify are kept apart

**Review looks for too little, security for new exposure, simplify for too much. Each is its own pass.**

- **Why:** one reader asked to both add what is missing and cut what is surplus does neither well.

### D13 · Simplify runs inside the build and blocks nothing

**The build closes with a simplify pass that edits in place and re-runs the gate. Its edits are then inside the
frozen diff, so review judges them. Its engine follows [D11](#d11--engines-follow-the-executor). Simplify is a
producer, not a checker: it holds no verdict.**

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

**Once the loop is clean, converge fixes this run's small cards and its drift in one more round. Everything else
becomes a card — why, when, what, priority, fix and size, trigger, still true? — in the gitignored
`.minions/backlog.md`. A card is a finding of the check loop, or of the hand read that stands in for it; work with no
finding behind it is planning, and lives outside the repo. The backlog never blocks a release; a paydown change
lists the cards it closes and its release deletes them.**

- **Why:** small fixes are cheapest while the context is fresh. A backlog that blocks would block every release, and
  one kept outside the repo cannot cite `path:line`.
- **Accepts:** the backlog is gitignored, so it lives on one machine. Reopen when a second person or a cloud run
  needs to read it.

### D17 · The release verifies, folds, archives, tags, and on the person's yes merges and pushes

**It re-runs the gate, folds the spec delta into `openspec/specs/`, archives the change, cuts the changelog with
one `Gate:` line of the gate's times, and tags. Then it asks once; on yes it merges into the default branch with
`--no-ff` and pushes the default branch and the tag. It never forces, never pushes the version branch, never
edits feature code. Fold and archive land in one commit.**

- **Why:** the yes is the person's act; the commands typed after it added nothing. A fold without its archive
  leaves the spec tree and the change disagreeing.
- **Rejected:** `openspec archive` for the fold: the release does the same fold inside a gate-verified commit · a
  separate merge skill: one more invocation · a merge without asking.

### D40 · Workers are fresh and observable

**A checker or verification worker is a new host subagent or fresh agent process receiving explicit task inputs,
without the build transcript. The conductor dispatches, waits and reads findings from shared disk; role identity
persists in that file. Claude Code keeps parallel dispatch; generic workers may run sequentially on one freeze.**

- **Why:** fresh context and observed output provide independence across hosts with different worker APIs.
- **Rejected:** inherited producer history, resumed verification conversations, inline self-review and
  unobservable sibling threads. Missing worker capability halts.

### D43 · Project health is measured per change, from the repo's own catalogue

**A repo that adopts declares its metrics in `metrics/catalogue.toml`. The build collects a draft after simplify,
for the person to read before converge; the release collects on its final tree and commits
`metrics/changes/<change-id>.json`. One bundled script collects and renders; each metric is a Python script it
runs without a shell; the page is generated from the data, never tracked. No catalogue, no metrics, and the
station says so.**

- **Why:** the gate proves a project works, not where it is heading; every number comes from a command, never from
  an agent.
- **Rejected:** an analysis platform — the repo would report outward · a narrative report — a prose copy drifts ·
  a tracked page — a view is regenerable · metrics run on a repo that declared none.
- **Accepts:** a release's data file sits inside the commit it measures, so its `analyzed` names the last build
  commit, and its values are that commit's tree plus the release's staged fold, archive and changelog.

## The target repo

What the skills need from a repository they work on.

### D18 · The contract with a target repo is a layout on disk

**The skills need the layout below from a repo, and nothing else. `mf-bootstrap` writes it once into a new repo,
`.minions/` as a `.gitignore` line, with `CHANGELOG.md` and `README.md`; the stations install nothing
([D2](#d2--the-product-is-the-practice-and-its-skills)).**

```
<target>/
├── openspec/specs/      the living spec
├── openspec/changes/    the active change, and the archive
├── Makefile             with a `gate` target
├── AGENTS.md            what is true of this repo
└── .minions/            run output, gitignored
```

`metrics/` is optional: a repo that adopts holds its catalogue and its data files there
([D43](#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)); the bootstrap writes none.

- **Why:** what travels between repos is a layout a reader can find, not a tool.
- **Held in step by:** the layout scan in `tests/test_skills.py`: every entry of the tree has a template in
  `skills/mf-bootstrap/templates/`.

## Repo conventions

How versions, ids and commits are written, what happens to what is replaced, and what a spec and a test are held
to.

### D19 · One version line

**A change's declared version, the `CHANGELOG.md` release, the annotated tag and the project's version file are one
value. The changelog follows Keep a Changelog: each phase appends under `Unreleased`, the release cuts the
heading.**

```
proposal.md `version: vX.Y`    =  CHANGELOG `## [X.Y.0]`  =  tag `vX.Y.0`  =  the version file
proposal.md `version: vX.Y.Z`  =  CHANGELOG `## [X.Y.Z]`  =  tag `vX.Y.Z`  =  the version file
```

- **Why:** one source of version truth leaves nothing to reconcile.

### D20 · A change id is an identifier, numbered in ship order

**`<digits>-<slug>`, never renamed once cut. The number is higher than every id before it; the cut takes the id it
is given; a version is numbered at its cut, so planned work carries a name, not a number.**

Example: `0011-cut-and-gate`, on the branch `<version>_cut_and_gate`.

- **Why:** a renamed id splits a change across two trailer values. A number given before the cut is a number to
  change later.

### D21 · Every commit names its change

**A commit ends with `Change: <change-id>`, in the trailer block, contiguous with `Co-Authored-By:`. The
bootstrap commit, made before any change exists, is the one without it.**

```
Co-Authored-By: <the session's attribution line>
Change: 0011-cut-and-gate
```

- **Why:** from a commit you find the change; from a change, `git log --grep` finds every commit. A blank line
  inside the block silently breaks it.

### D22 · Authentication and deployment terms belong to the operator

**The operator selects and authenticates the host, model and provider, and checks their terms for the intended
local, scheduled or server deployment. The skills configure no provider and install no host integration.**

- **Why:** subscription and API terms differ by provider and deployment; a portable skill cannot choose them.
- **Accepts:** a missing execution or authentication capability halts instead of becoming an installation task.

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

### D39 · A test is placed by its cost

**A test goes to the lowest layer that can fail for it, as a step in an existing test before a new one, on the
engines its outcome depends on — `mf-build`'s `T1`…`T6`. A test is deleted or merged only as the change's
`## Tests` table names it, its proofs carried by a remaining test or retired by a decision in force at the base.
Review judges each new test's cost and traces each removed one's proofs.**

- **Why:** one browser test per scenario, on every engine, plus one per fix, took a target's CI from minutes to
  most of an hour, unseen; most runs proved nothing another test or a lower layer did not.
- **Rejected:** a coverage review as a third checker: a third findings file and release precondition for a pass
  only some changes need · a time estimate at the cut: setup dominates, so runs × an average misleads.

### D41 · Model suggestions use offered capabilities

**The cutter honors a target menu in `AGENTS.md` and the actual session menu. With no menu it describes the
required capability; it suggests effort only when the host exposes that setting. Suggestions stay in chat and
leave model selection and provider setup with the operator.**

- **Why:** model menus and effort controls vary by host; invented choices cannot be acted on.
- **Rejected:** hardcoded model names, universal effort settings and automatic provider configuration.

### D42 · Skill prose is held by review, not by phrase scans

**A skill's rules are held by its own text, the spec and review. A test over skill text checks structure a
reader cannot see by eye — the shared id tables agreeing, the card's one owner, bundled references resolving,
the bootstrap templates — never that a sentence exists.**

- **Why:** a phrase scan proves a sentence exists, not that a station obeys it, and it freezes the wording: no
  sentence can be reworded without editing a test, so skill text only grows.
- **Gave up:** the gate failing when a rule's sentence is deleted. Review reads the diff for it.
