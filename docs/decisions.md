# Decisions

The choices in force today, each with its reason. A decision states a choice that could have gone another way; a
rule whose breach is a defect is a [principle](principles.md). An entry is written in the present tense and holds
no history: when a change adds or overturns one, it edits this page in one of its phases, and its own
`design.md` keeps how that came about.

An id in force is never reused or renumbered. A new decision takes the next number, in the group it belongs to.

```
  grill ───▶ cut ───▶ build ───▶ converge ───▶ release
    └─ Planning ─┘       └─ The check loop and the release ─┘
       D5…D10, D38                   D11…D17, D40, D43, D49, D50

  The shape D1…D4 · The target repo D18, D46, D48 · Repo conventions D19…D23, D36, D37, D39, D41, D42, D44, D45, D47
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

**The stations are the skills. A person conducts them, or `mf-ship`'s script starts each as a fresh agent process
and checks it from disk (D47). No station is reimplemented: there is no third way to run the line.**

- **Why:** one source for what a station does. A second implementation of every station drifts from the first.
- **Rejected:** a runner that reimplements the stations · an LLM session waiting on long-running stations.

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

### D11 · Every station runs MF's own method

**Every station runs MF's own method on every executor: `mf-simplify` in the build, the review and security
references in converge. The build reports the executor from runtime evidence; it is recorded, never routed — model,
provider and editor names select nothing.**

- **Why:** one method on Claude, Codex or any capable host keeps every run comparable, and the metrics name the host.
- **Accepts:** no native command is used; the person runs them by hand to compare.
- **Rejected:** native engines in production — host-bound, and `/simplify` never runs the tests · silent native
  fallback · provider routing.

### D12 · Review, security and simplify are kept apart

**Review looks for too little, security for new exposure, simplify for too much. Each is its own pass.**

- **Why:** one reader asked to both add what is missing and cut what is surplus does neither well.

### D13 · Simplify runs inside the build and blocks nothing

**The build closes with a simplify pass that edits in place and re-runs the gate. Its edits are then inside the
frozen diff, so review judges them. It is `mf-simplify`. Simplify is a producer, not a checker: it holds no
verdict.**

- **Why:** run last, it would land unreviewed edits after the final check. Given a verdict, taste would spin the
  loop.
- **Rejected:** simplify as a third read-only station.

### D14 · Converge is optional, and a skip is stated

**A change may be released without the check loop. The release then writes `converge: skipped` into its report and
the release commit. The diff patch or either findings file means converge ran, and then both files must exist and
be clean.**

- **Why:** a prose-only change read by hand does not earn the check passes, and a silent skip would look like a
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
`.minions/backlog.md`: one file per repository, in the primary's `.minions/`, shared by every worktree and written
under `.minions/backlog.lock`. A card is a finding of the check loop, or of the hand read that stands in for it;
work with no finding behind it is planning, and lives outside the repo. The backlog never blocks a release; a
paydown change lists the cards it closes and its release deletes them.**

- **Why:** small fixes are cheapest while the context is fresh. A backlog that blocks would block every release, and
  one kept outside the repo cannot cite `path:line`.
- **Accepts:** the backlog is gitignored, so it lives on one machine. Reopen when a second person or a cloud run
  needs to read it.

### D17 · The release verifies, folds, archives, tags, and on the person's yes merges and pushes

**It re-runs the gate, folds the spec delta into `openspec/specs/`, archives the change, cuts the changelog with
one `Gate:` line of the gate's times, and tags. Then it asks once; on yes — or `merge=yes`, the yes the person
gave by starting `mf-ship` — it merges into the default branch with `--no-ff` and pushes the default branch and the
tag. It never forces, never pushes the version branch, never edits feature code. Fold and archive land in one
commit.**

- **Why:** the yes is the person's act; the commands typed after it added nothing. A fold without its archive
  leaves the spec tree and the change disagreeing.
- **Rejected:** `openspec archive` for the fold: the release does the same fold inside a gate-verified commit · a
  separate merge skill: one more invocation · a merge nobody said yes to: `merge=yes` comes only from a run the
  person started.

### D40 · Workers are fresh and observable

**A checker or verification worker is a new host subagent or fresh agent process receiving explicit task inputs,
without the build transcript. The conductor dispatches, waits and reads findings from shared disk; role identity
persists in that file. Dispatch prefers parallel; workers may run sequentially on one freeze.**

- **Why:** fresh context and observed output provide independence across hosts with different worker APIs.
- **Rejected:** inherited producer history, resumed verification conversations, inline self-review and
  unobservable sibling threads. Missing worker capability halts.

### D49 · One review method, two depths

**Converge runs MF's method at `tier=standard` — one fresh worker per role, from a packet given up front — or at
`tier=high` — per role, finders, a verifier per candidate, a gap sweep and a writer, all dispatched by converge.
`standard` is the default; the cut suggests `high` for changes to authentication, the gate, migrations, CI or the
review machinery. Both write the review and security files, recording the tier.**

- **Why:** most changes need a cheap review of the obvious; a few need many independent readers. The same
  checklist and finding bar at both depths keep the results comparable.
- **Rejected:** native review in production · `high` as the default · a third findings file · nested fan-out.

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

### D50 · Review metrics are read across repos and drawn on one page

**`mf-review-metrics` reads the findings files and status logs of the repos the operator's config names, leniently —
every unreadable field a gap — and writes one self-contained page: tables per repo and per tier × model, charts over
changes through `mf-build`'s chart. Numbers only; it writes into no repo and is no station of the line.**

- **Why:** choosing a review tier, and seeing what it costs, needs the record of every past converge in one place.
- **Rejected:** a recommendation on the page · reading inside a run · a copy of the chart code.

## The target repo

What the skills need from a repository they work on.

### D18 · The contract with a target repo is a layout on disk

**The skills need the layout below from a repo, and nothing else. `mf-bootstrap` writes it once into a new repo,
`.minions/` as a `.gitignore` line, with `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`
([D46](#d46--a-repos-own-rules-live-in-its-coding-standards-and-contribution-guide)), `THREAT_MODEL.md` and
`docs/decisions.md` ([D48](#d48--a-repos-architecture-decisions-and-threat-model-have-a-known-home)); the stations
install nothing ([D2](#d2--the-product-is-the-practice-and-its-skills)).**

```
<target>/
├── openspec/specs/      the living spec
├── openspec/changes/    the active change, and the archive
├── Makefile             with a `gate` target
├── AGENTS.md            what is true of this repo
└── .minions/            run output, gitignored
```

`.minions/` is the primary checkout's; `AGENTS.md` may declare `Worktrees:` and `Workspace setup:` ([D44](#d44--versions-run-side-by-side-in-worktrees-one-primary-merges-them)).

`metrics/` is optional: a repo that adopts holds its catalogue and its data files there
([D43](#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)); the bootstrap writes none.

- **Why:** what travels between repos is a layout a reader can find, not a tool.
- **Held in step by:** the layout scan in `tests/test_skills.py`: every entry of the tree has a template in
  `skills/mf-bootstrap/templates/`.

### D46 · A repo's own rules live in its coding standards and contribution guide

**`CODING_STANDARDS.md` holds a repo's coding rules, `CONTRIBUTING.md` how a change lands and the evidence it
carries; `AGENTS.md` names both mandatory context. `mf-build`'s rules are the portable default: a project rule that
names one replaces it. `mf-bootstrap` writes both; an existing repo adopts them by hand, and the build and converge
read a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` its `AGENTS.md` does not name.**

- **Why:** a rule needs one home every station reads; where none is written, an agent invents one.
- **Rejected:** one combined file · the rules in `AGENTS.md` · a precedence between the coding filenames ·
  migrating existing repos.

### D48 · A repo's architecture decisions and threat model have a known home

**Its architecture decisions live in `docs/decisions.md` — or `ARCHITECTURE.md`, `docs/adr/` — and its threat model
in `THREAT_MODEL.md`: named in `AGENTS.md`, else found by name. The cut designs within the decisions in force, the
build halts on a phase that breaks one unless the change amends it, and converge hands both to every worker.
`mf-bootstrap` writes `THREAT_MODEL.md` and an empty `docs/decisions.md`.**

- **Why:** a review judges against what is written down; without a threat model, security falls back on generic
  categories.
- **Rejected:** `SECURITY.md` — a reporting policy, another thing · an `ARCHITECTURE.md` template that goes stale ·
  plan and release reading them.

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

**`<digits>-<slug>`, never renamed once cut. The number is higher than every id on the default branch and on every
open version branch; the cut takes the id it is given; versions ship in cut order; a version is numbered at its cut,
so planned work carries a name, not a number.**

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
required capability; it suggests effort only when the host exposes that setting. The cut shows the suggestion and
writes it to `.minions/models/<change-id>.toml`, never into the change, for `mf-ship`; model selection and provider
setup stay with the operator.**

- **Why:** model menus and effort controls vary by host; invented choices cannot be acted on.
- **Rejected:** hardcoded model names, universal effort settings and automatic provider configuration.

### D42 · Skill prose is held by review, not by phrase scans

**A skill's rules are held by its own text, the spec and review. A test over skill text checks structure a
reader cannot see by eye — the shared id tables agreeing, the card's one owner, bundled references resolving,
the bootstrap templates — never that a sentence exists.**

- **Why:** a phrase scan proves a sentence exists, not that a station obeys it, and it freezes the wording: no
  sentence can be reworded without editing a test, so skill text only grows.
- **Gave up:** the gate failing when a rule's sentence is deleted. Review reads the diff for it.

### D44 · Versions run side by side in worktrees; one primary merges them

**A repo that declares `Worktrees:` in `AGENTS.md` gets a linked worktree per version, made by the cut from the
primary checkout, which stays on the default branch. Ids and versions are reserved at the cut against every open
version branch, and versions ship in cut order. Every worktree shares the primary's `.minions/`; the release merges
in the primary.**

- **Why:** two writers in one checkout collide; git holds a branch in one worktree only; open branches reserve ids
  without a lock file.
- **Rejected:** host-managed worktrees — places MF cannot name · rebasing a judged branch · a reservation file.

### D45 · One station merges the default branch into the next version

**`mf-integrate`, run in the primary, merges the default branch into the lowest-id open version's worktree,
applies fixed rules to the CHANGELOG, decision ids and spec delta, hands a semantic conflict to the person with the
merge open, gates, and commits the merge; converge's catch-up judges the merge by its remerge-diff.**

- **Why:** the merge-in a moved base needs conflicts on the same files every time; a clean merge adds nothing to
  read, and what the merge decided is exactly what review must see.
- **Rejected:** `merge=union` — it drops a blank line and hides the result from the remerge-diff · rebasing a judged
  branch · resolving silently against either design.

### D47 · `mf-ship` takes cut versions to the default branch unattended

**Run in the primary, `mf-ship` starts `conduct.py`, which builds and converges every open version in parallel,
then integrates, runs the catch-up round and releases each in cut order with `merge=yes`. Each station is a fresh
agent process under `conduct.py`'s allowlist — Claude Code — or the workspace-write sandbox — Codex — never with
prompts bypassed, and is judged by a check on disk; a failed check halts its version, a halt holds every version
behind it at the merge, a failed probe halts the run, and a re-run resumes from disk. Converge runs at the tier the
cut chose.**

- **Why:** once versions are planned and cut, what follows is the line's; the pilot ran it by hand in a dozen
  commands.
- **Rejected:** an LLM conductor waiting on the workers · `mfa-*` copies of the stations · a state file · workers that
  bypass permission prompts: the list blocks what is off it, though `make`, `uv` and `python3` still run any code.
