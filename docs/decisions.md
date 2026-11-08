# Decisions

The choices in force today, each with its reason. A decision states a choice that could have gone another way; a
rule whose breach is a defect is a [principle](principles.md). An entry is written in the present tense and holds
no history: when a change adds or overturns one, it edits this page in one of its phases, and its own
`design.md` keeps how that came about.

An id in force is never reused or renumbered. A new decision takes the next number, in the group it belongs to.

```
  plan ────▶ cut ───▶ build ───▶ converge ───▶ release
    └─ Planning ─┘       └─ The check loop and the release ─┘
     D5…D10, D38, D58, D59, D62, D65, D69  D11…D17, D40, D43, D49, D50, D63, D64, D66, D68, D71, D73

  The shape D1…D4, D52 · The target repo D18, D46, D48 · Repo conventions D19…D23, D36, D37, D39, D41, D42, D44, D45, D47, D51, D53, D55, D56, D57, D60, D61, D67, D70, D72
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

**`uv` · `ruff` · `ty` · `pytest`, behind `make gate`; a tool off PyPI is operator tooling (D52). The skills assume
only the `gate` target, so a target repo may use any toolchain.**

- **Why:** a working gate beats a generic abstraction, and the `Makefile` target is the whole interface.

### D52 · A gate tool off PyPI is operator tooling

**A gate step whose tool PyPI does not ship runs from `PATH`. Its version is written in `AGENTS.md`, and CI installs
that exact version, checked against the release's checksum. Betterleaks, the gate's secret scan, is one.**

- **Why:** uv pins what PyPI ships, and a scanner with no PyPI build still needs one version everywhere; the checksum
  keeps CI's copy the one `AGENTS.md` names.
- **Accepts:** a local gate runs the version on `PATH`, and fails where the tool is missing.

## Planning

How an idea becomes a change the build can run.

### D5 · A change is planned with `mf-plan` and written with the OpenSpec CLI

**`mf-plan` grills a version to settled decisions and writes the brief, and at a hard close queues its cut
([D59](#d59--a-hard-plan-closes-on-a-checked-brief-and-queues-its-cut-on-the-persons-yes)); the OpenSpec CLI's `instructions` shape
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
the same ids and checks them before it commits the change ([D38](#d38--the-cut-commits-without-waiting)). It
re-checks the facts whose files moved since the brief's `At` line, and its helpers read them. It runs each `Verify:`
search's pattern at `HEAD` through `verify_check.py`, and a fresh worker's plan review asks whether each task can be
built as written, a second review only after a fix that changes a decision or a task
([D65](#d65--a-lighter-plan-review-and-build)); it runs no gate.**

- **Why:** a change the build cannot run is cheapest to catch at the cut. A check read and never run, or a plan
  read only by its writer, lets a plan the code cannot satisfy reach the build; a gate on the base plus a change
  directory re-proves the base.
- **Rejected:** the cut reading its own plan · the full gate at the cut.
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
that is not `None.`, a self-check item the cut cannot meet, and a plan-review doubt left to the person still wait for
the person's OK; an unattended cut halts there instead ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)),
save a `## Dependencies` whose rows its brief approves, which it commits and the run checks
against its queued copy ([D62](#d62--a-queued-cuts-packages-are-approved-at-the-plan)). Starting `/mf-build` is the OK for
the `Verify:` commands.**

- **Why:** the cut is almost always right, and a wrong one costs one more commit; the wait cost a *"please commit"*
  every time.
- **Accepts:** an edit after the read is a further commit on the branch, before the build.

### D58 · A settled brief is cut by a conductor station

**`conduct.py cut <slug> <bump> brief=<path>` queues a settled brief under the queue lock in the home folder, reserving
its number in `.minions/cuts/<id>`. The run makes the branch and worktree, runs `mf-cut-change unattended=yes` sandboxed
to that worktree, the run directory and the brief, checks the cut on disk and builds it. Unattended, the brief's switch
`decide: recommended` takes the recommended option, logged in the brief; every other doubt halts at `cut-halted`, with no
rescue, its line naming the answer: a re-plan and `conduct.py rejoin <id>`, which keeps the queued packages and takes a new
one only with the person's `--yes <hash>` ([D62](#d62--a-queued-cuts-packages-are-approved-at-the-plan)). Queuing a cut is the person's yes to cut, run, merge and push
it.**

- **Why:** the person's chat stayed busy with cuts, and two cutters raced for one id.
- **Rejected:** a background subagent in the person's session · the id given at dispatch · an `AGENTS.md` switch · a
  rescue for a cut halt · the parameters in `.minions/`, where a worker writes.
- **Accepts:** a Codex cutter's root is its brief's folder, so `cut` and the station refuse a Codex brief that does not
  stand alone in its folder: the person's other notes stay out of its reach.

### D59 · A hard plan closes on a checked brief, and queues its cut on the person's yes

**At a hard close `mf-plan` names per change the models of the build, converge, release and cut station and the switch
`decide: recommended`, runs `brief_check.py` until it passes, shows the `## For the cut` items and `conduct.py status`, and
asks once, "confirm, and queue it?". Yes, or `then=ship`, runs `conduct.py cut` per change in order
([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)), and is the person's yes to every merge and push in the run it
joins or starts; no ends on `/mf-cut-change`. The plan never cuts.**

- **Why:** a cut in the person's session kept the chat busy, and a brief out of shape is a cutter's doubt made at the
  plan.
- **Rejected:** the plan cutting · a light brief queued · a question per change.

### D62 · A queued cut's packages are approved at the plan

**A hard brief's `## Dependencies` holds a row per package the person approved in a round — item, package, constraint,
why — or `None.`. `conduct.py cut` copies the item's rows into its home-queue entry, and a rejoin of a queued cut keeps
them, taking a row they lack only with the person's `--yes <hash>` of the new rows; the cut station halts a cut whose
`design.md` lists a package or constraint outside them, and never reads the brief for approval. A cut halt the plan answers names the brief and `conduct.py rejoin`; a hand cut halts on an id the
queue holds.**

- **Why:** a queued cut halted on packages approved in chat, where no station reads, its halt naming no answer, and the
  planning thread then cut the queued id by hand.
- **Rejected:** approval read from the brief at cut time, which the cutter can edit · a rejoin copying the brief's rows
  again unconditionally, which takes a row a cutter planted after a disk fix (the person's decision on `0091·S1`) · a
  nested line under the item · judging a looser constraint, which needs each ecosystem's version grammar.

### D65 · A lighter plan review and build

**The cut's plan review runs once; a second, by a new worker, runs only when a fix after the first changes a `design.md`
decision or a brief's `## Decisions` row, a `C` row included, or adds or removes a task. Every plan review is a fresh worker
([D40](#d40--workers-are-fresh-and-observable)). A change whose highest row of *Suggesting models* is the moderate one is
suggested Sonnet 5.5 · high for its whole build, where the session offers it: one `[build]` model a change.**

- **Why:** a second review on every cut put reviews at 18–52% of a cut's cost, and the run now repairs a wrong plan — rescue, the supervisor, the amend
  round — at about $3 a time; a Sonnet build costs about half per line, and a fresh session per phase saved about $1 a build.
- **Rejected:** a second review after every fix · resuming a reviewer by a message.

### D69 · A version names what it builds beside

**A version that only shares files with another names it in `beside:` and builds in parallel from the default branch;
`after:` is kept for a symbol, decision or requirement the other adds, and holds the build until that one releases. The
plan's parallel-with check proposes which, `beside:` by default. `conduct.py cut` and the cut carry it into the proposal's
frontmatter, and nothing waits on it: integrate, and under the switch the supervisor, settle the overlap as they settle any
moved base.**

- **Why:** most of 0081–0095's `after:` links only avoided file overlap, each holding a build through the other's
  converge and release, while integrate already merges a moved base in.
- **Accepts:** an overlap settled at integrate — a supervisor's spend, or a person's halt — where `after:` would have waited.
- **Rejected:** `after:` for overlap — a wait the merge makes needless · a run-time reader of `beside:` — nothing it would
  order.

## The check loop and the release

What happens between the last phase and the tag.

```
  build ──▶ simplify, in place ──▶ freeze the diff ──▶ conformance ‖ adversarial ──▶ all clean? ── yes ──▶ release
                                                            ▲                            │ no
                                                            └── verify ◀────────── fix ◀─┘
```

### D11 · Every station runs MF's own method

**Every station runs MF's own method on every executor: `mf-simplify` in the build, the conformance and adversarial
references in converge. The build reports the executor from runtime evidence; model, provider and editor names select
nothing. Workers follow the host, or the models file's `executor`; converge's take their model and effort from its worker
tables ([D64](#d64--converge-spends-where-judgment-is)),
a checker its executor too ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it)).**

- **Why:** one method on Claude, Codex or any capable host keeps every run comparable, and the metrics name the host.
- **Accepts:** no native command is used; the person runs them by hand to compare.
- **Rejected:** native engines in production — host-bound, and `/simplify` never runs the tests · silent native
  fallback · routing by a model or provider name.

### D12 · Conformance, adversarial and simplify are kept apart

**Conformance looks for what the plan asks and the code lacks, adversarial for what breaks it, simplify for too much.
Each is its own pass.**

- **Why:** one reader asked to both add what is missing and cut what is surplus does neither well.

### D13 · Simplify runs inside the build and blocks nothing

**The build closes with a simplify pass, its own worker under `mf-ship`, that edits in place and re-runs the gate. Its edits are then inside the
frozen diff, so converge's checkers judge them. It is `mf-simplify`. Simplify is a producer, not a checker: it holds no
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
| conformance | `blocking` · `drift` · `nit` | `blocking` |
| adversarial | `critical` · `high` · `medium` · `low` | `critical` · `high` |

- **The anchors always block:** data loss, spend, exposure of personal data or secrets, silent wrong output.
  Save one class: a route in a class the threat model's *Out of scope* accepts by name is carded, anchors included.
- **Drift never blocks:** prose the code contradicts — save an amend card, one naming the plan's amend: converge halts
  `amend needed` on it at the debt write, and the person's amend, the rescue's or the supervisor's
  answers it, in one amend round ([D63](#d63--an-answered-amend-gets-one-round-over-its-range)).
- **A repeat goes up one level:** a finding that repeats a debt card.
- **Why:** left to judgement, a costly defect is graded a nit and a typo blocking. The anchors fix the floor; the
  drift tier keeps prose out of the loop.

### D16 · Deferred work is a card in the repo's debt file

**Once the loop is clean, converge fixes this run's small cards and its drift,
checked by one verify pass that is no round ([D71](#d71--the-cut-and-converge-read-what-changed)). Everything else,
save an amend card ([D15](#d15--anchored-harms-block-drift-never-does)), becomes a card — why, when, what,
priority, fix and size, trigger, still true? — in the gitignored `.minions/debt.md`: one file per repository, in
the primary's `.minions/`, shared by every worktree and written under `.minions/debt.lock`. A card is a finding of
the check loop, or of the hand read that stands in for it; work with no finding behind it is planning, and lives
outside the repo. The debt never blocks a release; a paydown change lists the cards it closes and its release
deletes them.**

- **Why:** small fixes are cheapest while the context is fresh. A debt that blocks would block every release, and
  one kept outside the repo cannot cite `path:line`.
- **Accepts:** the debt file is gitignored, so it lives on one machine. Reopen when a second person or a cloud run
  needs to read it.

### D17 · The release verifies, folds, archives, tags, and on the person's yes merges and pushes

**It re-runs the gate, folds the spec delta into `openspec/specs/`, archives the change, cuts the changelog with
one `Gate:` line of the gate's times, and tags. Then it asks once; on yes — or `merge=yes`, the yes the person
gave by starting `mf-ship` — it merges into the default branch with `--no-ff` and pushes the default branch and the
tag; under `merge=yes`, `conduct.py` pushes. It never forces, never pushes the version branch, never edits feature
code. Fold and archive land in one commit.**

- **Why:** the yes is the person's act; the commands typed after it added nothing. A fold without its archive
  leaves the spec tree and the change disagreeing.
- **Rejected:** `openspec archive` for the fold: the release does the same fold inside a gate-verified commit · a
  separate merge skill: one more invocation · a merge nobody said yes to: `merge=yes` comes only from a run the
  person started.

### D40 · Workers are fresh and observable

**A checker, a verification worker or the cut's plan reviewer is a new host subagent or fresh agent process
receiving explicit task inputs, without the producer's transcript. The conductor dispatches, waits and reads findings
from shared disk; role identity persists in that file. Dispatch prefers parallel; workers may run sequentially on one
freeze. The plan reviewer answers the cut with its doubts, each with its `path:line`, and writes no findings file.
Each plan review is a new worker, never a message to the reviewer before it. The cut's helpers are fresh read-only
workers, as its plan reviewer is, answering in the cut's thread and writing no file:
the cut writes their answers to its notes. A checker on another host than its
conductor's is a fresh agent process `conduct.py`
starts on the conductor's request ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it)).**

- **Why:** fresh context and observed output provide independence across hosts with different worker APIs.
- **Rejected:** inherited producer history, resumed verification conversations, inline self-review and
  unobservable sibling threads. Missing worker capability halts.

### D64 · Converge spends where judgment is

**Converge's conductor runs on Sonnet 5.5 · high, its conformance worker on the mid tier · high,
its adversarial worker on the strongest tier · high, and its fixer on the mid tier · medium, on adversarial's model,
adversarial running on converge's host, when a card it is sent blocks: the models file's `[converge]`,
`[converge.conformance]`, `[converge.adversarial]` and `[converge.fix]`, which `conduct.py` reads once and passes in the
converge prompt. Verify runs at medium. Conformance reads `bundle.md` — the
decisions the change cites, in full, an index of all, and each requirement the delta modifies or removes,
as a diff from the living spec — in place of the decisions file and the living spec. A fix that touches no `## Surfaces` path of `THREAT_MODEL.md`, with no
adversarial card awaiting its checker, takes its adversarial head by recomputation.**

- **Why:** converge was most of a run's spend, its conductor judges nothing, and the decisions file was 47% of a worker's
  reading set.
- **Accepts:** on Codex every worker on the conductor's host runs on the conductor's model; a decision the change does not
  cite is read by its index line alone; the build's model is `[build]`'s, a moderate phase's `[build.moderate]`'s.
- **Rejected:** a mid-tier conductor alone — every worker follows it · the skill reading the models file — a worker can write
  it · an adversarial verify skipped by the conductor's judgment.

### D66 · Two checkers: conformance and adversarial

**Converge runs two checkers. Conformance judges the code against the change's own spec, design, tasks and the decisions it
cites, from the change's artifacts, its bundle and the diff, reading no code beyond the diff's hunks; it grades `blocking` ·
`drift` · `nit`, on the mid tier. Adversarial tries to break the change — races, edge cases, exploits, security — from the diff,
the source and tests around it and the threat model; it grades `critical` · `high` · `medium` · `low`, `high` a bug that would
block, on the strongest tier. Each reads `diff.patch` once. `debt_match.py` writes the debt cards on
the diff's files to `debt-cards.md`, and no worker reads `.minions/debt.md`. A verify round after a fix reads its open cards, the fix diff and `references/verify.md`.**

- **Why:** of 0072–0089's blockers, spec conformance as text caught 29% and adversarial correctness 60%; review and security
  found 11 issues twice; the debt was 11.4% of a round-1 review's reads, cited by no blocker; a verify spent 40–50% re-reading
  its file and the method.
- **Accepts:** conformance misses every race and parser edge, which adversarial owns · a security card is known by its
  category, which the checker writes.
- **Rejected:** four checkers — two earn their cost · a checker judging the deterministic checks — the gate, `gate_check.py`,
  the `Verify:` lines and coverage stay scripts · the old names: "security" read as security only.

### D68 · Converge's checkers may run on another host, and a shadow round measures it

**A conformance or adversarial table may name its executor, and the models line its host. A checker on another host than
converge's runs through the checker mailbox, in the home folder's queue: the conductor writes the request, `conduct.py` spawns
the checker on the plan's model and effort, and the conductor reads its findings from disk. The fixer stays on converge's host.
Under `[converge] shadow = true`, round 1 also runs the other host's checkers on the same freeze, into shadow files that drive
nothing, and `overlap.py` counts what each side alone caught. The review metrics read per role and executor.**

- **Why:** a sandboxed Claude conductor cannot start Codex, and the person wanted Codex's review with Claude's fix, and the
  numbers first.
- **Accepts:** a mailbox the converge worker writes, bounded to `CHECKER_SPAWNS` a spawn · checkers served one at a time ·
  a shadow pair's spend each round 1 it is on.
- **Rejected:** `.minions/` as the mailbox — every worker writes it · a checker's model from its request · a fixer on another
  host · a shadow on every round.

### D71 · The cut and converge read what changed

**The cut's plan reviewer starts from a packet — the change directory, `HEAD`, the cut's notes and the question — with a
budget of 40 turns, and a second review judges only the change directory's diff since the first. The cut's helpers run on
Sonnet 5.5 · medium, and the cut writes their answers to `cut-notes.md`. Once no blocker is open, a pickup's fix is checked
by one verify worker at medium, which is no round. The bundle holds each changed requirement as a diff, the debt cards on
the diff's files have their own file, and the release reads the findings files' frontmatter and card lines alone.**

- **Why:** 0097's plan reviews re-read everything, and its helpers, on the strongest model, re-read what another worker of
  the cut had read; 0096's last round verified only pickups; the bundles repeated the delta; the release read both findings
  files whole for their verdicts.
- **Accepts:** a budget the reviewer counts itself, and a review that reaches it leaves the rest unread, its doubts the
  person's or the switch's · a pickup check on conformance's model moves adversarial's head when `surfaces.py` exits 0 and
  no adversarial card was picked, as the head by rule does · a pickup whose check needs a mailbox role verifies in a
  counted round.
- **Rejected:** plan reviews on Sonnet — both of 0097's caught real defects · a commit between the reviews · the pickup
  verified in a full round · the release reading the frontmatter alone — a `fixed` blocker would pass.

### D49 · One review method, one depth

**Converge runs MF's method at one depth — one fresh worker per role, from a packet given up front, its decisions and
the requirements its delta changes, as diffs, in a bundle of what the change cites. The conformance and adversarial files are the same for every
change.**

- **Why:** one fresh reader per role, with the same checklist and finding bar, found what many readers found, at a
  fraction of the cost.
- **Rejected:** native review in production · `high` as the default · a third findings file
  — a shadow file drives nothing ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it))
  · nested fan-out · a high tier: 5 of 5 at both depths, 89 workers and 55.6 M tokens against 2 and 4.2 M.

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

**`mf-review-metrics` reads the findings files, status logs and run logs of the repos the operator's config names,
and every repo a run started in, and the operator's Codex sessions, leniently — every unreadable field a gap — and
writes one self-contained page and its data, `review-metrics.json`, beside it: tables
per repo and per role, executor and model, the cost per worker, round, role and station, with first-turn context, four
headline numbers, charts over changes through `mf-build`'s chart, and a record per round and role. Numbers only; it
writes into no repo and is no station of the line.**

- **Why:** choosing a review model, and seeing what it costs, needs the record of every past converge in one place.
- **Rejected:** a recommendation on the page · reading inside a run · a copy of the chart code.

### D63 · An answered amend gets one round over its range

**A converge halt answered past its head — by any commit when both findings files judged that head, else by an amend of the
change directory, the person's, the rescue's or the supervisor's — opens one amend round: a catch-up run marked `· amend` over
`<judged head>..HEAD`, holding the amend, the build's code for a phase it added and converge's own unverified fix. Before its
`start` it runs each `Verify:` the range adds to `tasks.md`; then one judge round and at most one fix round, a blocker left
`cap reached` ([D56](#d56--the-cap-policy)). No amend passes by rule. Conformance keeps the full plan, and the stale-claim pass
searches the whole tree for each claim the amend changes.**

- **Why:** an amended run restarted at round 1 over the whole change with a fresh cap of three: 24% of converge's spend, a
  two-line amend buying a 13-file round, and 0087's and 0088's loops. A scoped round would have missed one nit; the
  stale-claim pass and the `Verify:` re-run catch what an amend breaks outside its diff.
- **Accepts:** code an amend contradicts outside the range, which only the stale-claim pass searches · a decision or
  spec-delta amend judged in one round.
- **Rejected:** a full reopen after a decision amend · a fresh cap of three per amend · by rule for the person's amends.

### D73 · A build runs a fresh worker per phase

**Under `mf-ship`, the build station spawns `mf-build` once per unticked phase, `phase=<N>`, and once for the close,
`phase=close`: simplify, the metrics and `build.done`. A phase spawn passes only on its phase ticked at `HEAD` on a clean
tree, so none runs twice without an amend between. Phases hand over through `.minions/changes/<id>/build-notes.md`, of
which the conductor keeps 40 lines a phase. The cut rates each phase `moderate` or `hard`; a moderate one runs on
`[build.moderate]` when the models file names it.**

- **Why:** one session carried every phase's reads to its end, most at the last phase; a fresh worker per phase
  simulated cheaper on the largest build and level on the smaller, per the change's design Evidence table.
- **Accepts:** each phase re-reads its base · a note the conductor cuts at 40 lines.
- **Rejected:** a per-phase worker only on big changes — one behaviour is simpler · a tracked notes file — D6 keeps the
  record to four artifacts · a host per phase.

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

`.minions/` is the primary checkout's, save the gate's own junit report, which sits in the checkout that ran it; `AGENTS.md` may declare `Worktrees:` and `Workspace setup:` ([D44](#d44--versions-run-side-by-side-in-worktrees-one-primary-merges-them)).

`metrics/` is optional: a repo that adopts holds its catalogue and its data files there
([D43](#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)); the bootstrap writes none.

- **Why:** what travels between repos is a layout a reader can find, not a tool.
- **Held in step by:** the layout scan in `tests/test_skills.py`: every entry of the tree has a template in
  `skills/mf-bootstrap/templates/`.

### D46 · A repo's own rules live in its coding standards and contribution guide

**`CODING_STANDARDS.md` holds a repo's coding rules, `CONTRIBUTING.md` how a change lands and the evidence it
carries; `AGENTS.md` names both mandatory context. `mf-build`'s rules are the portable default: a project rule that
names one replaces it. `mf-bootstrap` writes both; an existing repo adopts them by hand, and the cut, the build and
converge read a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` its `AGENTS.md` does not name.**

- **Why:** a rule needs one home every station reads; where none is written, an agent invents one.
- **Rejected:** one combined file · the rules in `AGENTS.md` · a precedence between the coding filenames ·
  migrating existing repos.

### D48 · A repo's architecture decisions and threat model have a known home

**Its architecture decisions live in `docs/decisions.md` — or `ARCHITECTURE.md`, `docs/adr/` — and its threat model
in `THREAT_MODEL.md`: named in `AGENTS.md`, else found by name. The cut designs within the decisions in force,
reading those it cites and an index, the build halts on a phase that breaks one unless the change amends it, and converge
hands its conformance worker its bundle — of the decisions, those the change cites, in full, and an index of all — and
its adversarial worker the threat model. `mf-bootstrap` writes `THREAT_MODEL.md` and an empty `docs/decisions.md`.**

- **Why:** a review judges against what is written down; without a threat model, adversarial falls back on generic
  categories.
- **Rejected:** `SECURITY.md` — a reporting policy, another thing · an `ARCHITECTURE.md` template that goes stale ·
  plan and release reading them.

## Repo conventions

How versions, ids and commits are written, what happens to what is replaced, and what a spec and a test are held
to.

### D19 · One version line

**A change's version, assigned at its release, the `CHANGELOG.md` release, the annotated tag and the project's version
file are one value. The changelog follows Keep a Changelog: each phase appends under `Unreleased`, the release cuts
the heading.**

```
proposal.md `version: vX.Y`    =  CHANGELOG `## [X.Y.0]`  =  tag `vX.Y.0`  =  the version file
proposal.md `version: vX.Y.Z`  =  CHANGELOG `## [X.Y.Z]`  =  tag `vX.Y.Z`  =  the version file
```

The cut declares `bump: minor` or `bump: patch`; `next_tag.py` computes the tag, and the release writes `version:` into
the proposal it archives.

- **Why:** one source of version truth leaves nothing to reconcile.

### D20 · A change id is an identifier, numbered in cut order

**`<digits>-<slug>`, never renamed once cut, and the name of its branch. The number is higher than every id on the
default branch and on every open version branch, and than every reservation in `.minions/cuts/`; the cut takes the id
it is given, and `conduct.py cut` gives the next free one under its lock
([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)); a version is numbered at its release, so work carries a
name, then an id, and a number last.**

Example: `0011-cut-and-gate`, on the branch `0011-cut-and-gate`.

- **Why:** a renamed id splits a change across two trailer values. A number given before the release is a number to
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

**A scenario says what proves it in prose; conformance judges whether a test proves it. No marker ties a test to a
scenario, and the gate does not check the binding.**

- **Why:** a binding checker is per-language code no target repo can run, and it made every spec carry keys only it
  read.
- **Gave up:** the gate failing on a requirement with no test.

### D37 · Tests hold what is true now; nothing tests an absence

**A test asserts a behaviour or a rule the repo holds today. A retired name leaves the tree in the commit that
retires it, checked once by that change's acceptance. A scan may name what a live rule forbids; it never lists
retired names.**

- **Why:** a scan for retired words grows with every retirement, and tests a history rather than the system.
- **Gave up:** a reintroduced name turning the gate red. Conformance's stale-claim pass looks for it instead.

### D39 · A test is placed by its cost

**A test goes to the lowest layer that can fail for it, as a step in an existing test before a new one, on the
engines its outcome depends on — `mf-build`'s `T1`…`T6`. A test is deleted or merged only as the change's
`## Tests` table names it, its proofs carried by a remaining test or retired by a decision in force at the base.
Conformance judges each new test's cost and traces each removed one's proofs.**

- **Why:** one browser test per scenario, on every engine, plus one per fix, took a target's CI from minutes to
  most of an hour, unseen; most runs proved nothing another test or a lower layer did not.
- **Rejected:** a coverage review as a third checker: a third findings file and release precondition for a pass
  only some changes need · a time estimate at the cut: setup dominates, so runs × an average misleads.

### D41 · Model suggestions use offered capabilities

**The cutter honors a target menu in `AGENTS.md` and the actual session menu. With no menu it describes the
required capability; it suggests effort only when the host exposes that setting. The cut shows the suggestion and
writes it to `.minions/changes/<change-id>/models.toml`, converge's worker tables on
[D64](#d64--converge-spends-where-judgment-is)'s tiers among it, each host the brief names as its `executor`, never into
the change, for `mf-ship`; model selection
and provider setup stay with the operator. Models the brief names are the person's, chosen at the plan's close: the cut
writes those ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)).**

- **Why:** model menus and effort controls vary by host; invented choices cannot be acted on.
- **Rejected:** hardcoded model names, universal effort settings and automatic provider configuration.
- **Names one model:** *Suggesting models*' moderate row, Sonnet 5.5 · high, taken only where the session offers it
  ([D65](#d65--a-lighter-plan-review-and-build)).

### D42 · Skill prose is held by review, not by phrase scans

**A skill's rules are held by its own text, the spec and review. A test over skill text checks structure a
reader cannot see by eye — the shared id tables agreeing, the card's one owner, bundled references resolving,
the bootstrap templates — never that a sentence exists.**

- **Why:** a phrase scan proves a sentence exists, not that a station obeys it, and it freezes the wording: no
  sentence can be reworded without editing a test, so skill text only grows.
- **Gave up:** the gate failing when a rule's sentence is deleted. Review reads the diff for it.
- **Accepts:** the plan-review scan of `tests/test_skills.py`, which reads the opening words of cells in the cut's review
  table and *Suggesting models*: the Acceptance of [D65](#d65--a-lighter-plan-review-and-build) asked for it.

### D44 · Versions run side by side in worktrees; one primary merges them

**A repo that declares `Worktrees:` in `AGENTS.md` gets a linked worktree per version, made by the cut from the
primary checkout, which stays on the default branch. Ids are reserved at the cut against every open version branch and
every reservation `conduct.py cut` wrote under its lock ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)).
A stacked dependent takes its dependency's built head by a merge
([D72](#d72--a-dependent-builds-on-its-dependencys-built-head)). Every worktree shares the primary's `.minions/`, save the
gate's own junit report, which sits in the checkout that ran it; the release merges in the primary.**

- **Why:** two writers in one checkout collide; git holds a branch in one worktree only; an open branch reserves its id
  once its change is committed, and a queued cut's reservation before.
- **Rejected:** host-managed worktrees — places MF cannot name · rebasing a judged branch.

### D45 · One station merges the default branch into the next version

**`mf-integrate`, run in the primary, merges the default branch into a version's worktree,
applies fixed rules to the CHANGELOG, decision ids — the plan's planned ones too — and spec delta, resolves a hunk both sides only add, hands a semantic
conflict to the person with the merge open — under a version's switch to its supervisor first,
whose settle of spec and docs text it commits ([D61](#d61--a-supervisor-answers-what-rescue-diagnoses)) — and commits
the merge, its body naming every path it settled: a rule, the union, the person, the supervisor, a test fixed. It gates the committed merge in its worktree; a red gate halts with `.red` naming
the merge. Converge's catch-up judges the merge by its remerge-diff, unless
`integrate.py replay` rebuilds it by the fixed rules alone: then it is clean by recomputation, with no worker. `conduct.py` alone merges it into a cut-only branch — a dependent's, or
one the default branch passed before its first worker — and into a started one whose base the default branch passed changing
its gate, save a stacked one; it also merges a dependency's built head into its stacked dependent
([D72](#d72--a-dependent-builds-on-its-dependencys-built-head)). It settles a conflict in `CHANGELOG.md` or
`docs/decisions.md`, and a stacked branch's `CHANGELOG.md` on any merge, by `integrate.py`'s rules, runs the `decisions` rule on every merge, halts on any other conflict, runs
`integrate.py delta` on the open merge, commits when that passes, and else leaves the merge open with its note.**

- **Why:** the merge-in a moved base needs conflicts on the same files every time; a clean merge adds nothing to
  read, and what the merge decided is exactly what review must see. A merge the rules rebuild decided nothing, and
  replay recomputes it rather than trusting the commit body.
- **Rejected:** `merge=union` — it drops a blank line and hides the result from the remerge-diff · rebasing a judged
  branch · resolving silently against either design.

### D47 · `mf-ship` takes cut versions to the default branch unattended

**Run in the primary, `mf-ship` starts `conduct.py`, which builds and converges every open version in parallel,
a dependent building on its dependency's built head ([D72](#d72--a-dependent-builds-on-its-dependencys-built-head)),
then integrates, runs the catch-up round and releases each as it is ready, one at a time, with `merge=yes`. Each
station is a fresh agent process in an OS sandbox, Claude Code's or Codex's, never with prompts bypassed, and is
judged by its exit and a check on disk; a failed check halts its version, a halt blocks only what names it in
`after:`, a failed probe at the start halts the run, and one in a live run only the versions on its executor. A run takes
each queued cut ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)) at its start and each poll, and its close,
under the queue lock, starts the next run on a request or a cut it never read. A live run takes a rejoin request, in the
home folder's queue, `~/.mf-ship-origin/<digest>.queue/rejoin/`, where no worker writes, a mailbox that holds no state,
and, at each poll, every halt answered on disk ([D60](#d60--a-run-heals-its-own-halts)):
it takes back each requested version whose stage on disk is
no longer a halt, a version cut since its start included, and none whose models file changed since the run read it, nor one
whose converge or integrate halt was answered while its rescue ran, the person's own fix included, save by the person's
amends alone, which waits for a re-run.
A version taken back brings each version it blocked. A converge halt followed by an amend of the change directory, or by
any commit when the findings files judged its head, is answered, and gets one amend round
([D63](#d63--an-answered-amend-gets-one-round-over-its-range)). A re-run resumes from
disk: only a stage left in `HALTS`, a git config key or `origin` URL the run refuses, a git config that changed during the
run, a default-branch commit or version tag no release made, a claimed group it cannot kill, an `origin` it cannot read with no
offline base, or a precondition it stops on, a skill with no link among them, needs the person. A version halt's first
step is its rescue ([D53](#d53--a-rescue-amends-the-plan-never-the-code-or-a-decision)): a stage in `HALTS` needs the
person once a rescue, where one runs, and under the switch its supervisor
([D61](#d61--a-supervisor-answers-what-rescue-diagnoses)), has left it halted. A converge cap of small cards is the run's to grant, never
past a granted round, and a `re-plan` halt needs the person ([D56](#d56--the-cap-policy)).**

- **Why:** once versions are planned and cut, what follows is the line's; the pilot ran it by hand in a dozen
  commands.
- **Executors:** the models file names a station's executor, absent meaning the run's, and a checker's,
  absent meaning converge's.
  One probe runs per executor, Codex's with a checker on a fixture, at the start or before a joining version's first worker
  on it, and a
  worker reaches the primary and the open worktrees alone,
  and a converge worker its checker mailbox. A mixed run's Codex station hands its writes to the next station's
  sandbox, never to its start: a Claude worker loads no project settings.
- **Origin down:** a failed read of `origin` waits, whatever its error, and so does a failed push a re-read cannot follow;
  a push `origin` refuses halts. Past `RETRIES` at the start, the run builds, converges and releases locally, judged against
  the **offline base**, and each release and the close push what is pending. The first offline base needs the person:
  `conduct.py anchor`, in their session.
- **Accepts:** what a command `Ship tools:` names runs, inside the sandbox.
- **Rejected:** an LLM conductor waiting on the workers — the supervisor is a station a halt starts
  ([D61](#d61--a-supervisor-answers-what-rescue-diagnoses)) · `mfa-*` copies of the stations · a state file · workers that
  bypass permission prompts: the list blocks what is off it · telling an auth failure of `origin` from a network one · a
  version held until `origin` answers.

### D72 · A dependent builds on its dependency's built head

**Once a version's one unreleased `after:` dependency passes its build check, with no halt, and its built head holds the
version's base, `conduct.py` merges that head into the version with no agent, writes its sha to
`.minions/changes/<id>/stacked-on`, and the version builds. Built, it waits as `stacked`; once the dependency releases, the
run merges the default branch in, removes `stacked-on`, and converge runs round 1. While `stacked-on` stands, the build's gate
check and metrics, `mf-simplify`'s range and the gate's diff coverage take it as their base. An amend of the dependency's
change directory past that head that changes a decision resets the version to its cut commit, until the merge back, even
once the dependency released; it stacks again on the dependency's next build, or, the dependency released, builds again on
the default branch.**

- **Why:** a dependent waited through its dependency's converge, about 45 minutes, which rarely changes the code it builds on.
- **Accepts:** a dependent built on code its dependency's converge has not judged — it never converges or releases before
  that converge and release · a reset that drops the dependent's build and any amend of its own · a forged `stacked-on`,
  which narrows the build's gate check and diff coverage alone: the run removes it before converge and the release.
- **Rejected:** rebasing the dependent onto the built head (D44, D45) · stacking on two dependencies, or on a head that lacks
  the dependent's base · stopping a running build at a re-plan.

### D51 · A worker runs in an OS sandbox, and no worker pushes

**Every worker runs in its host's OS sandbox: it writes to the repo and its worktrees alone, a cutter to its worktree,
the run directory and its brief alone ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)) — a Codex cutter to
the brief's folder, which then holds the brief alone, and a brief or `.minions` that is a link starts no cutter — and its scripts
reach no unlisted domain. A Claude worker whose sandbox cannot start does not run, and each run's probe proves a write out
refused, and on Codex one checker. `conduct.py` holds the push: its remote calls read no repo's config, and go only to the URLs a run kept in the home folder.
It pushes only a release a run took to its release, by a ledger there. The threat is a confused or prompt-injected agent; a
hostile repo needs a container.**

- **Why:** measured, a script deleted a file in `~` under the allowlist and under auto mode, and the sandbox refused it. The
  conductor runs outside the sandbox, so what a worker wrote must steer none of its remote calls, and a repo's config outlasts
  the run that wrote it, so the URLs stand where no worker writes.
- **Offline base:** beside the kept URLs stands `<digest>.pushed`, the default-branch sha a run last saw on `origin`,
  written after every good read and default-branch push. It judges the default branch while `origin` cannot be read, where
  no worker writes.
- **Accepts:** a Codex worker can read `~`, with its network off · a repo's `.claude/` settings, skills and `.mcp.json` reach no
  worker · a Claude worker starts no MCP server, the operator's own included ·
  a Codex worker loads no user config ([D67](#d67--a-codex-worker-starts-on-mfs-settings-logs-json-and-is-proved-by-a-checker))
  · a domain `Ship network:` lists · a release forged on a head before that head lands on `origin`.
- **Rejected:** auto mode · a deny list for Codex · a container, until a repo is hostile · loopback per repo: on macOS it
  reaches every local service.

### D67 · A Codex worker starts on MF's settings, logs JSON and is proved by a checker

**A Codex worker starts with `--ignore-user-config` and `--json`: the operator's Codex config sets nothing, and its log reads
as a Claude log does — denials, usage limit, tokens, and dollars priced by `skills/mf-review-metrics/prices.toml`. A writable
root that is a link halts the next Codex spawn, and no Codex worker has `/tmp`. A run's Codex probe, past its scratch edit,
runs one conformance checker on a fixture, passing on a findings file to the contract and a log with a usage event.**

- **Why:** no station had run on Codex; a worker loaded the operator's MCP servers and plugins, and its plain log read as
  nothing.
- **Accepts:** a priced cost only for a model the table holds · the checker's verdict unjudged · a swap after the check, while
  Codex starts.
- **Rejected:** an MF-written Codex profile · judging the checker's verdict · list prices written by the cut.

### D70 · A worker starts lean

**A Claude worker starts with its station's tools alone — the cut and converge `Agent` too, the probe `Bash` and `Read` —
with the operator's plugins, output style and auto-memory off and the dynamic prompt sections moved out, and reaches only the
worktrees of open versions and queued cuts. The cut and converge ask for the 1-hour cache, every other station the 5-minute
one. A tool its station lacks halts the version. The cut and the build read the decisions they cite and an index; the
converge conductor reads no mandatory context.**

- **Why:** a worker's first turn was ~28.6k tokens before any work, re-read every turn; build carried all 55 decisions for
  206 turns; only the cut's and converge's waits outlast 5 minutes.
- **Accepts:** a station that needs a new tool halts until its row changes · a decision the build does not cite is read by
  its index line alone.
- **Rejected:** `Agent` for every station · `--setting-sources` without user settings · 1h for every station.

### D53 · A rescue amends the plan, never the code or a decision

**On a build check halt, a converge `amend needed` halt, a converge cap the run does not grant ([D56](#d56--the-cap-policy)) or an integrate halt,
`conduct.py` runs `mf-rescue` in the halted version's thread. It may fix a build halt or an `amend needed` halt with one `docs(<id>): amend the change directory` commit, carrying a `Rescue:` trailer and touching the
change's `tasks.md` and `design.md` alone, never `design.md`'s decisions table, save under
[D60](#d60--a-run-heals-its-own-halts)'s switch; the run then clears the halt and builds or converges on. Every other halt it
diagnoses in `.minions/changes/<id>/rescue.md`, and the version stays halted, the halt naming the file, save what its
supervisor answers under the switch ([D61](#d61--a-supervisor-answers-what-rescue-diagnoses));
a commit at any other converge or integrate halt keeps the halt, and such a halt answered on disk while its rescue runs — a commit,
a settled merge, a removed note, a grant — counts as the rescue's answer, whoever wrote it, save the person's amends, which
let the version go on, and stands for the run, no rejoin
taking the version back; a person's grant is refused while that rescue runs, and the person's own fix then, or a grant landing as it
ends, waits for a re-run. A version gets at most `RESCUES = 3` a run, and none for a
sub-task rescued before; `[rescue]` in the models file, else `[build]`, picks its model, and `skip = true` there runs
none. A converge `verify: halt` is the run's to diagnose, with no worker and no rescue counted, its proposal naming the
command the run takes back. The converge fixer edits no plan, save the `design.md` prose a `drift` card names outside its
`## Decisions` section: a card whose fix needs any other plan edit halts `amend needed`. A
timeout, a usage limit, a failed worker, a `**HUMAN` phase and a stopped release get none: they need the person.**

- **Why:** most cut-side halts were an amend a fresh reader could write — a `Verify:` that could not pass, a file a task
  missed — and each waited hours for the person. The path check keeps the amend to the plan, and converge judges the
  amend and every claim it changes ([D63](#d63--an-answered-amend-gets-one-round-over-its-range)).
  The fixer corrects a design's prose: 0098 and 0100 each paid a round and a rescue for a drift line in it the fixer
  could not touch.
- **Accepts:** a wrong amend that passes the path check, which converge then reads · what a rescue leaves uncommitted,
  which the path check never reads and the next build pass takes as its own · a rescue's spend, bounded per version · the
  person's own fix landing while a converge or integrate rescue runs, which the run cannot tell from the rescue's and holds
  for a re-run, save the person's amends alone, which go on ([D60](#d60--a-run-heals-its-own-halts)) · a rescue amend
  with no `Rescue:` trailer, which reads as the person's ([D60](#d60--a-run-heals-its-own-halts)).
- **Rejected:** reading the build worker's output for the halt — `mf-build` writes `.minions/changes/<id>/build.halt` · a prompt in
  `conduct.py` — the station is a skill · a rejoin request · one rescue a version · a station in `STATIONS` · a rescue
  that changes a decision with no switch · counting only what a rescue did in the tree as its answer — a grant it writes would take the
  version back.

### D60 · A run heals its own halts

**The rescue amends the plan at converge's `amend needed` halt, as at a build halt, and diagnoses one whose cards include a
security `critical` or `high`. Under a version's `decide = "recommended"`, at the top of its models file and read once with
the plan, a rescue at a build or `amend needed` halt takes the fix a card's **Fix** or the plan proposes as its decision: it
may edit `proposal.md` and `design.md`'s `## Decisions` too, its commit carrying `Decided-by: rescue`, and the run logs it
`decided`. It never edits the spec delta, code or a test, takes a security `critical` or `high` card, approves a gate
makefile, settles an integrate conflict, releases, merges, pushes or answers a run-wide halt. The person's amends during a
rescue let the version go on. At each poll the run takes back every halted version whose stage or `HEAD` changed on disk,
read the same at two polls, with no request. The run ends when nothing can move, its close naming each halted version's
need and each version a rescue decided for.**

- **Why:** a supervising chat answered every halt of 2026-11-05/06, about 70% of them the line's own gaps, and most of the
  rest a prose amend a fresh reader could write.
- **Accepts:** a decided amend that passes the path and trailer checks is a worker's decision: converge judges the amend and
  every claim it changes, and the close and `report` name it · a rescue amend with no `Rescue:` trailer reads as the person's, and goes on.
- **Rejected:** `[rescue] decide` · an `AGENTS.md` switch ([D56](#d56--the-cap-policy)) · a request the run writes itself ·
  a push notification.

### D61 · A supervisor answers what rescue diagnoses

**Under a version's `decide = "recommended"`, when its rescue diagnoses a build, converge or
integrate semantic-conflict halt or is spent on it — the sub-task rescued before, or `RESCUES` reached — `conduct.py` runs
`mf-supervise` in the version's thread. It may amend anything under `openspec/changes/<id>/`, the spec delta included, and tick
a sub-task whose `Verify:` it ran green; it never edits code or a test, takes a security `critical` or `high` card, approves a
gate makefile, accepts a threat-model risk, answers an integrate red gate, releases, merges or pushes. The run takes one commit with the amend's subject, `Supervisor:` and `Decided-by: supervisor`
trailers and paths under the change directory alone, logs it `decided`, clears the halt and goes on in the thread; anything else
halts the version for the person. One try a halt, at most `SUPERVISES = 2` a version a run; `[supervise]` picks its model,
`claude-opus-5-5` at `high` on Claude when it names none. The close and `report` name each.**

- **New work:** a sub-task an amend adds — the supervisor's, the rescue's or the person's — goes in a new unticked phase after
  the last, never under a ticked one: the build reads `## Progress` boxes alone.
- **An integrate note:** it stages its resolution in Markdown under `openspec/` and `docs/` alone and writes
  `integrate.settled`, leaving the merge and the note open; the run checks the index and the work tree, then runs
  `mf-integrate` `with settled=supervisor`, which commits the merge naming `the supervisor`. One try an open merge, across
  runs: the home queue's `supervised/<id>` records it.
- **The brief:** a passed cut records its brief's path in the home queue's `briefs/<id>`, and the supervisor's prompt names
  it, read as evidence.
- **Why:** a supervising chat answered most of 0087's halts and 0085's integrate flag, none with code, each a judgment the
  rescue may not make, and each a restart.
- **Accepts:** a decided amend that passes the check is a worker's decision, the spec delta included: converge reads it in a
  round, never by rule · its spend, bounded per version · a supervisor amend with no trailer, which reads as the person's and
  converge judges in an amend round, as every amend ([D60](#d60--a-run-heals-its-own-halts)) · its answer to a converge `verify: halt`, whose amend
  `gate_check.py` then takes as the plan, a `Verify:` a worker edited included.
- **Rejected:** a watcher running all night ([D47](#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended)) ·
  widening the rescue · a supervisor without the switch · the supervisor committing the merge, which stays integrate's.

### D55 · One pinned MF release per machine

**`make install-skills` exports a release's `skills/` tree into `$XDG_DATA_HOME/minionsfactory/<tag>/`, with a `VERSION`,
and links every `mf-*` on `~/.claude/skills` and `~/.agents/skills` into it; bare, it takes the newest tag the kept `origin`
holds, from a scratch clone, and `TAG=<tag>` or `TAG=live` holds the links. Each conductor marks itself live in
`~/.mf-ship-origin/live/`, an install under a live run writes `pending`, and the links move only at the last live run's
end or at an install with none live, to the pending release or a newer tag `origin` holds. Every tree is kept.**

- **Why:** links into the live checkout let every MF release change the skills another repo's workers read mid-run. A
  conductor already loaded would read new skills with old code, so no link moves at a run's start. A scratch clone shares
  no object with the primary, so nothing planted there reaches the export.
- **Accepts:** a station run by hand leaves no live mark, so the links can move under it · a `TAG=<tag>` install trusts
  the checkout · a tag only the local repo holds is skipped, and the `start` line names it · after a reboot or a killed
  run, a pending release waits for the next run's end or install.
- **Rejected:** a Python package or a plugin · `SKILLS_DIR`, which names one host · a waiter process · a move at a run's
  start · an `After release:` command · a pin per project.

### D56 · The cap policy

**At a converge cap, `conduct.py` reads the open blocking cards — conformance's `blocking`, adversarial's `critical`
and `high` — and their fix sizes; when each is `one line`, `a test` or `one line and a test`, the run spawns converge with
`grant=yes` itself, with no grant file and no rescue, and checks that round as a person's grant's. Any other cap — a
blocker sized `a design change`, no card read, a granted round's, automatic or a person's, in this run or an earlier
one, a second cap in the run, or `[converge] auto_grant = false` in the models file — writes the version a last halt
line, `re-plan: <ids>`, and its rescue names `/mf-plan … from=` as the way back; a person's grant still buys a round.**

- **Why:** a cap of small cards is a grant's job, and it waited a night for the person; a cap that recurs is the plan's,
  each grant fixing one edge of a design and finding the next.
- **Accepts:** a card sized small that is not, which costs one round: the size is the checker's word.
- **Rejected:** the rescue judging the cap · a grant file the run writes · a new stage for the re-plan · an `AGENTS.md`
  line for the setting · tracking a function across caps.

### D57 · One folder per change in `.minions/`

**Everything about one change lives in `.minions/changes/<change-id>/`: `conformance.md`, `adversarial.md`,
`status_log.md`, `diff.patch`, `bundle.md`, `debt-cards.md`, `models.toml`, the cutter's `cut.halt` and `cut-notes.md`,
`integrate.{md,red,resolved,settled}`,
`build.{done,halt,closing,discarded.patch}`, `build-notes.md`, `stacked-on`, `rescue.md`, `release.held`, `gate-check/` and
`logs/<stamp>-<station>[-<n>].log`, each script finding it through its own `_change_dir`. `grants/`, `runs/`, `gate/`,
`replay/`, `metrics/`, `awake/`, `cuts/` and `debt.md` stay generic, the run's probe logging to
`runs/<stamp>/`. `conduct.py run` moves an old layout in at its start, under the claim, before any worker — a folder's
old `review.md` and `security.md` among it — and a file beside its new one or a link halts it; a hand-run station or
script on an old layout halts, naming `/mf-ship`, and `review_metrics.py` reads both.**

- **Why:** a person, or a viewer, reading one version opens one folder, not seven by kind and one per run.
- **Accepts:** a repo no run has moved halts its hand-run stations until a run moves it · a file the move does not name
  stays where it is.
- **Rejected:** keeping `<id>_` prefixes · a shared helper module · reading both layouts in the stage machine · a
  one-off migration of other repos · the probe's log in a change's folder.
