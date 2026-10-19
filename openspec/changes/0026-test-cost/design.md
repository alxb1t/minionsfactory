# 0026-test-cost — design

**In one line:** `mf-build` owns rules for tests (`T1`…`T6`) that the cut and converge carry; a deletion per the
design's `## Tests` table is consolidation, not weakening; review gains a test-cost pass and a coverage-trace pass;
the release writes the gate's time. Skill prose, docs and scans. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the evidence, the decisions and the text to
place, word for word.

## Context

- **The build writes a new test:** Step 2 item 1, *"Test-first where there is logic: write the failing test for the
  phase's acceptance"* (`skills/mf-build/SKILL.md:117-119`) — no look for an existing test, no layer. `W5`: *"A test
  that holds a guard ships with a twin"* (`:210`).
- **Weakening covers consolidation:** *"deleting or skipping a test … the move is to halt"* (`skills/mf-build/SKILL.md:126-128`);
  stop-condition 5 (`:197`); the fix station's *"no deleted test"* (`skills/mf-converge/SKILL.md:281-282`) and
  *Never* (`:422`); the principle *Never weaken the gate to pass* (`docs/principles.md:97-105`); the bootstrap
  template's guardrail (`skills/mf-bootstrap/templates/CLAUDE.md.tmpl:28`).
- **The red run assumes a new test:** *"it pastes the new test's failing run from before the fix"*
  (`skills/mf-converge/SKILL.md:284-285`); `tests/test_skills.py` holds the needle `failing run from before the fix`
  (`:482`).
- **Review is an adopted engine plus added passes:** `/code-review` unmodified (D11); the conductor adds the
  stale-claim pass (`skills/mf-converge/SKILL.md:181-183`) and checks its Summary (`:262-263`). Step 7 dispatches the
  same roles each verify round (`:312-316`).
- **The release adds no changelog prose:** Step 4.1 (`skills/mf-release/SKILL.md:131-134`). Precondition 1 runs the
  full gate (`:63-65`); Step 4.4 commits exactly the tree Step 4.3 gated, so nothing is written after 4.3.
- **The shared-id scan has two owners:** `_SHARED_OWNERS = ("mf-build", "mf-cut-change")` (`tests/test_skills.py:18`);
  `_shared_label_problems` compares the first with the second (`:105-125`); `_shared_id_problems` checks the run of
  ids (`:128-138`). `_section_lines` ends a section at any line starting `## ` (`:71-80`); `_needle_problems` joins a
  section's lines with `\n`, so a needle sits on one line (`:235-259`).
- **The record:** D17 (`docs/decisions.md:190-200`); D37 is the last *Repo conventions* entry (`:290-297`); the map
  lists `D19…D23, D36, D37` (`:14`). The principle *The repo reaches nothing outside itself* (`docs/principles.md:128-136`).
- **`gh run list --json workflowName,headSha,startedAt,updatedAt`** runs here; a run's time is `updatedAt − startedAt`.

### The evidence

A client target repo built under the line, before and after a cut built with `mf-build` and checked with
`mf-converge`. Counts from that repo's CI logs and its e2e audit.

| measure | before | after | source |
|---|---|---|---|
| CI time | 6 min, eleven releases earlier → 54 min | 13m23s | CI run time on the default branch |
| browser-test runs | 64 → 1 002 | 174 | Playwright's test count per run |
| one href check / its whole test | 351 ms / 458 ms | — | the per-test log timings |
| tests with no scenario | 39 | — | the audit's scan |
| … of those from fix commits | 21 | — | `git log` on each test's first commit |
| gaps a read-only coverage review found before converge | — | 6 | the coverage review |
| issues converge's review found, given the design's deletions as context | — | 10 | the findings files |

The causes: a new browser test per scenario, each with its own page load, where a step in an open test would do;
every test on four engines; a new regression browser test per converge finding; and nothing that merged a test or
showed the clock. Converge's real findings were client tests pinned to one engine, merged steps leaning on an earlier
step, and a scenario moved onto a test of another code path.

### Terms

| term | means |
|---|---|
| **the rules for tests** | `T1`…`T6`, the `## Rules for tests` table `mf-build` owns |
| **the `## Tests` table** | the consolidation table in a change's `design.md` `## Tests` section: each removed test → the test carrying its proofs |
| **the cost line** | the counts in a change's `## Tests` section ([A8](#b5)) |
| **the `Gate:` line** | the one line the release writes under its changelog heading |

## Goals / Non-Goals

**Goals**

- A change adds a browser run only when no lower layer and no existing test can carry the proof, and says so.
- Consolidation is planned at the cut and traced by review, never improvised and never forbidden.
- Every release shows the gate's time beside the last one.

**Non-Goals**

- When the gate runs: a fast phase gate is the next change.
- Binding scenarios to tests (D36).
- A CI template, a time estimate, a threshold.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="b1"></a>**B1** | **`mf-build` owns `## Rules for tests`, `T1`…`T6`** ([the table](#the-rules-for-tests)): lowest layer · extend before adding · a step stands alone · engines only where they differ · delete or merge only per the table · a twin at the lowest layer | each cause in [the evidence](#the-evidence) is a rule the build broke by default | rules in `W`: `W` is for all text, these are for tests |
| <a id="b2"></a>**B2** | **`mf-cut-change` and `mf-converge` carry the same table**; the shared-id scan takes a list of carriers, the first the owner | the fix station runs in a target repo and cannot be told to read `mf-build`; a copy a scan holds does not drift | converge citing `mf-build` by name |
| <a id="b3"></a>**B3** | **The build cites them:** Step 2 item 1 places the failing test per `T1` and `T2`; `W5` places the twin per `T6`; a phase that adds an end-to-end test writes `T2`'s reason in its commit body | the rule is read where the test is written | — |
| <a id="b4"></a>**B4** | **`I16`:** a change that deletes or merges a test names each in the `## Tests` table. The build's Step 2 item 3 and stop-condition 5 say a deletion per the table is not weakening; one outside it still is | the build deleted per the design without halting, against its own text | a deletion judged in the build |
| <a id="b5"></a>**B5** | **`A8`:** `design.md` has a `## Tests` section — the cost line (tests added and removed by layer, end-to-end runs added, each count with its command), a reason per new end-to-end test, and the `I16` table when a test goes. Cut Step 6 names it | growth is decided at the grilling, not found in CI | minutes estimated from an average run: setup dominates |
| <a id="b6"></a>**B6** | **The fix station follows `T1` and `T2`**, never deletes or merges a test, and its red run may be an extended test's | 21 tests with no scenario came from fix commits | consolidation in a fix pass: unplanned, untraced |
| <a id="b7"></a>**B7** | **Review's test-cost pass:** a new end-to-end test a lower layer proves (`T1`), that re-opens a state another test reaches (`T2`), or on engines its outcome cannot depend on (`T4`) is a `nit` sized `a test`; Step 8's pickup fixes it; a repeat escalates by the existing rule | fixed in the same run without spinning the loop | `blocking`: the loop would spin on taste |
| <a id="b8"></a>**B8** | **Review's coverage-trace pass**, when the freeze removes a test: each removed assertion and scenario id traced against the `## Tests` table, handed over at dispatch. A proof carried by nothing, a scenario on another code path, client behaviour on one engine, a step leaning on an earlier one: `blocking`. Both passes checked in the Summary, fail-closed | the read-only trace found gaps converge would have needed a hand-written prompt to see | a third station: a third findings file, a release precondition and a catch-up case for a pass only some changes need |
| <a id="b9"></a>**B9** | **Every round runs both passes** over its own freeze | a fix's new test is judged like the build's | round 1 only |
| <a id="b10"></a>**B10** | **The `Gate:` line:** precondition 1's `make gate`, timed; CI's longest workflow among the latest green runs on the default branch, by `gh`, or `CI none`; the previous release's times, from its line. Step 4.1 writes it, the one exception to *no new changelog prose*; the close-out names it. No threshold | the clock is seen at every release with no step to remember; Step 4.4 commits exactly the tree 4.3 gated, so the line cannot follow 4.3 | timing Step 4.3 · the line in the commit body · waiting for the release's own CI |
| <a id="b11"></a>**B11** | **Two principles amended:** *Never weaken the gate to pass* names consolidation per the table; *The repo reaches nothing outside itself* allows one read — the release reads the remote's CI, read-only | A7 for principles: what holds is edited where it lives | — |
| <a id="b12"></a>**B12** | **D39 · A test is placed by its cost**, after D37; **D17** names the `Gate:` line | A7 | — |
| <a id="b13"></a>**B13** | **The bootstrap's `CLAUDE.md.tmpl`** gets `## Tests`, and its guardrail names the table | a new repo starts under the rules | a CI template: its own feature |

## The rules for tests

**`skills/mf-build/SKILL.md`**, a new section between `## Rules for what you write` and `## Prose rules`:

```markdown
## Rules for tests

This skill owns this list. `mf-cut-change` and `mf-converge` carry the same ids; `tests/test_skills.py` fails if
they differ. A test is paid for on every gate run, on every engine it runs on: the cheapest proof adds no run.

| id | rule | example / why |
|---|---|---|
| **T1** | **Lowest layer first** — a test goes to the lowest layer that can fail for the behaviour: unit, then integration, then end-to-end only for what a browser alone shows. A repo with no lower layer tests at the lowest it has | a price rule is a unit test; the price on the page is one step in a page test |
| **T2** | **Extend before adding** — before a new end-to-end test, find one that already reaches the same state (page, record, fixture) and add a step there. A new one says in the commit body why none fits | most of a browser test's time is its setup |
| **T3** | **A step stands alone** — an added step asserts nothing an earlier step's change set up, unless the test's flow is that sequence | a step leaning on an earlier one passes for the wrong reason |
| **T4** | **Engines only where they differ** — a test runs on more than one browser or engine only when its outcome can depend on it. Client behaviour — script, layout, input — runs on each; server-rendered output runs on one | a status code, a header or `<head>` text is the same on every engine |
| **T5** | **Delete or merge only per the design's table** — a test is deleted or merged only as `design.md`'s `## Tests` table names it, each removed test mapped to the remaining test that carries its assertions and scenario ids | a deletion outside the table weakens the gate |
| **T6** | **A twin at the lowest layer** — `W5`'s twin is a unit test of the guard or a step in the guard's own test, never a new end-to-end test. Where neither fits, the guard test's red run with the guard removed goes in the commit body | a twin that boots a browser is a test of the test kit |
```

**`skills/mf-cut-change/SKILL.md`**, a new section between `## Prose rules` and `## Rules for the artifacts`: the same
table, under this opening:

```markdown
## Rules for tests

`mf-build` owns this list. The ids here are the same set; `tests/test_skills.py` fails if they differ. The cut plans
to them in `design.md`'s `## Tests` section (`A8`).
```

**`skills/mf-converge/SKILL.md`**, a new section between `## The card` and `## Never`: the same table, under this
opening:

```markdown
## Rules for tests

`mf-build` owns this list. The ids here are the same set; `tests/test_skills.py` fails if they differ. The fix
station writes tests to them, and review's test-cost pass judges by them.
```

## The build

**`skills/mf-build/SKILL.md`:**

- Step 2 item 1, before → after: *"write the failing test for the phase's acceptance, then implement to green."* →
  *"write the failing test for the phase's acceptance — at the layer `T1` names, as a step in an existing test where
  `T2` finds one — then implement to green."*; and *"Write to `W`, `P` and `C` below."* → *"Write to `W`, `T`, `P`
  and `C` below."*
- Step 2 item 3, after *"(see *Stop-conditions*)."*, add: *"A test deleted or merged as `design.md`'s `## Tests`
  table names it (`I16`, `T5`) is not weakening; one outside the table is."* The needle `` `## Tests` table `` sits
  on one line.
- Step 2 item 6, after the `retired:` example block, a paragraph:

```markdown
   A phase that adds an end-to-end test carries `T2`'s reason in its commit body, one line per test, as its own
   paragraph before the trailer block: `new e2e: <test> — <why no existing test reaches the state>`.
```

- Stop-condition 5, after *"not a coding shortcut."*, add: *"A deletion the `## Tests` table names is the plan, not
  a weakening."*
- `W5`, before → after: *"showing the test fails when the guard is gone"* → *"showing the test fails when the guard
  is gone, placed per `T6`"*.

## Consolidation

**`I16`, in both skills' `## Input contract`, after `I15`:**

- `mf-build`: `| **I16** | name, in `design.md`'s `## Tests` table, every test the change deletes or merges, each mapped to the remaining test that carries its assertions and scenario ids | — (stop-condition 5) |`
- `mf-cut-change`: the same middle cell; the last cell *"reading each task that deletes or merges a test, and
  finding the test in the table"*.

`mf-cut-change`'s diagram, before → after: `I1 … I15` → `I1 … I16`; Step 8, before → after: *"each of `I1`…`I15`"*
→ *"each of `I1`…`I16`"*.

**`A8`, in `mf-cut-change`'s `## Rules for the artifacts`, after `A7`:**

```markdown
| **A8** | **`design.md` states the test cost** — a `## Tests` section after the decisions: the tests the change adds and removes by layer and the end-to-end runs it adds (tests × the engines each runs on), each count with the command that produced it; a reason per new end-to-end test (`T1`, `T2`); and the `I16` table when it removes a test | growth is decided at the grilling, not found in CI |
```

`mf-cut-change` Step 6, before → after: *"`design.md` always has `## Dependencies`, saying `None.` when empty."* →
*"`design.md` always has `## Tests` (`A8`) and `## Dependencies`, the latter saying `None.` when empty."*

**`skills/mf-converge/SKILL.md` Step 6**, the first and third fix-station bullets replaced by:

```markdown
- fixes test-first where there is logic, writing each test to the [rules for tests](#rules-for-tests): a
  finding's regression test at the lowest layer that reproduces it (`T1`), as a step in an existing test where one
  reaches the state (`T2`);
- **never weakens the gate** — no new blanket suppression, no loosened config — and it
  **never deletes or merges a test**: consolidation is planned at the cut (`T5`), never in a fix. That is exactly
  what the review station checks for;
```

```markdown
- **proves red before green** — for a card whose **Fix** size includes `a test`, it pastes the new or extended
  test's failing run from before the fix into the **Status** note; an extended test's run is the existing test with
  the new step added. A fix to docs alone is exempt;
```

The needles `never deletes or merges a test` and `failing run from before the fix` each sit on one line.

**`mf-converge` *Never***, after *"because a check was loosened."*, add: *"A test deleted or merged as `design.md`'s
`## Tests` table names it is not a weakening."*

**`docs/principles.md`, *Never weaken the gate to pass*:**

- the bold paragraph, after *"halt and say so."*, add: *"A test deleted or merged as the change's `## Tests` table
  names it, its proofs carried by a named remaining test, is consolidation, not weakening."*
- *Held by*, after *"review reads the diff for it;"*, add *"`I16`, `T5` and review's coverage-trace pass, for
  consolidation;"*.

## The review passes

**`skills/mf-converge/SKILL.md` Step 3**, after the stale-claim paragraph:

```markdown
**Review runs a test-cost pass after its engine.** For every test the diff adds, it applies the
[rules for tests](#rules-for-tests): an end-to-end test that a lower layer already proves (`T1`), that re-opens a
state another test reaches (`T2`), or that runs on engines its outcome cannot depend on (`T4`), is a card graded
`nit`, its **Fix** sized `a test`, so Step 8's pickup fixes it. Its Summary says the pass ran.

**Review runs a coverage-trace pass when the freeze removes a test** — a deleted test file, or a test case gone
from one. It traces every removed assertion and scenario id to the test that runs it now, against `design.md`'s
`## Tests` table. A proof carried by nothing, a scenario moved onto a test of another code path, client behaviour on
one engine (`T4`), or a merged step leaning on an earlier one (`T3`), is `blocking`. Its Summary says the pass ran,
or that the freeze removed no test.
```

Step 3's dispatch list, after the findings-path bullet: *"- for review, the change's
`openspec/changes/<change-id>/design.md`, whose `## Tests` section the coverage-trace pass reads;"*

**Step 5**, after the stale-claim bullet:

```markdown
- **A review without its test-cost pass or its coverage-trace pass is not clean.** The review file's Summary must
  say each ran, or that the freeze removed no test. It does not → a scope failure: halt on it.
```

**Step 7**, after *"…and declaring a verdict."*: *"Review runs its test-cost pass and its coverage-trace pass over
this round's freeze, so a fix's new test is judged like the build's."*

## The clock

**`skills/mf-release/SKILL.md`:**

- Precondition 1, after *"Red → halt; the build owns it."*, add:

```markdown
   **Time this run** for Step 4.1's `Gate:` line, in one shell command:
   `s=$(date +%s); make gate; e=$?; echo "gate: $(( $(date +%s) - s ))s, exit $e"`.
```

- Step 4.1, after *"seed a fresh **empty** `## [Unreleased]` above it."*, and *"Write no new changelog prose
  here."* → *"Write no other changelog prose here."*:

````markdown
   Under the renamed heading, before its entries, write **the `Gate:` line** — the one line a release adds:

       Gate: local <precondition 1's time> · CI <time> (<workflow> at <short sha>) · <previous version>: <its times>

   e.g. `Gate: local 0m41s · CI 0m12s (CI at d5162e4) · 0.25.0: none`. Times are `XmYs`. **CI** is
   `gh run list --branch <default-branch> --status success --limit 50 --json workflowName,headSha,startedAt,updatedAt`:
   the latest run of each workflow, timed `updatedAt − startedAt`, and the longest of them. It is the default branch
   before this release, named by its commit. `gh` failing, no `origin`, or no run → `CI none`. **The previous** is
   the `Gate:` line under the previous release heading, its times copied; no line there → `<previous version>: none`.
````

- Step 6's sentences, before → after: *"with the Step 4.3 gate's exit code;"* → *"with the Step 4.3 gate's exit
  code, and the `Gate:` line;"*.

**`docs/principles.md`, *The repo reaches nothing outside itself*,** the bold paragraph's first sentence, before →
after: *"Everything a station reads or writes is inside the repository it works on."* → *"Everything a station writes
is inside the repository it works on, and so is everything it reads, save one: `mf-release` reads the remote's CI
runs, read-only, for its `Gate:` line."* A bullet after *Why*: *"- **Accepts:** without `gh` or a remote, the line
says `CI none`."*

**`docs/decisions.md`, D17's bold paragraph,** before → after: *"cuts the changelog and tags."* → *"cuts the
changelog with one `Gate:` line of the gate's times, and tags."*

## The record

**`docs/decisions.md`**, after D37, the last entry of *Repo conventions*:

```markdown
### D39 · A test is placed by its cost

**A test goes to the lowest layer that can fail for it, as a step in an existing test before a new one, on the
engines its outcome depends on — `mf-build`'s `T1`…`T6`. A test is deleted or merged only as the change's
`## Tests` table names it. Review judges each new test's cost and traces each removed one's proofs.**

- **Why:** one browser test per scenario, on every engine, plus one per fix, took a target's CI from minutes to
  most of an hour, unseen; most runs proved nothing another test or a lower layer did not.
- **Rejected:** a coverage review as a third checker: a third findings file and release precondition for a pass
  only some changes need · a time estimate at the cut: setup dominates, so runs × an average misleads.
```

The map, before → after: `Repo conventions D19…D23, D36, D37` → `Repo conventions D19…D23, D36, D37, D39`.

**`skills/mf-bootstrap/templates/CLAUDE.md.tmpl`**, a section between the quality-gate section and
`## How a change is cut here`:

```markdown
## Tests

A test is placed by its cost: every gate run pays for it again.

- **The lowest layer that can fail for it** — unit, then integration, then end-to-end only for what a browser
  alone shows.
- **A step in an existing test before a new one** — one that already reaches the page, record or fixture.
- **Engines only where they differ** — client behaviour on each engine; server-rendered output on one.
- **Deleted or merged only as a change's `## Tests` table names it** — each removed test mapped to the test that
  carries its proofs.
```

Its guardrail, after *"halt and say so."*, add: *"A test deleted or merged as the change's `## Tests` table names it
is not a weakening."*

## The scans

In `tests/test_skills.py`, each a function returning one line per breach, a test that `_REPO` gives `[]`, and a
planted twin that gives every breach:

| scan | holds | the twin plants | `-k` |
|---|---|---|---|
| `_shared_label_problems`, `_shared_id_problems` | take an `owners` tuple, default `_SHARED_OWNERS`, and compare each carrier with the first, one `labels differ` line per carrier; the existing twins' output is unchanged | — | — |
| the test-rule ids | `_shared_id_problems(base, "## Rules for tests", "T", _TEST_RULE_CARRIERS)`, the carriers `mf-build`, `mf-cut-change`, `mf-converge` | a build with `T1`–`T3`, a cut with `T1` and `T3`, a converge with `T1`–`T2` | `test_rule` |
| `_consolidation_problems` | `` `## Tests` table `` in `mf-build`'s `## Step 2 — The per-phase ritual`; `never deletes or merges a test` in `mf-converge`'s `## Step 6 — The fix station (one subagent, inside this loop)` | both needles outside their sections | `consolidation` |
| `_review_pass_problems` | `mf-converge` names `test-cost pass` and `coverage-trace pass` at least twice each | a converge naming each once | `review_pass` |
| `_gate_clock_problems` | `mf-release` names `Gate: local` and `gh run list` | a release naming neither | `gate_clock` |
| `_template_tests_problems` | `skills/mf-bootstrap/templates/CLAUDE.md.tmpl` has the line `## Tests` | a template with `### Tests` | `template_tests` |

Each scan carries a comment naming its decision: `# Why: 0026-test-cost design B<n>.`

## Tests

This change edits skill text and adds scans; it adds no end-to-end test and runs on no browser.

| layer | added | removed |
|---|---|---|
| unit (`tests/test_skills.py`) | a `_REPO` test and a planted twin per new scan in [the scans](#the-scans) | none |
| end-to-end | none | none |

No test is deleted or merged, so there is no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- **[A `T` rule read as a ban]** → each has its way out: no lower layer (`T1`), a reason in the commit (`T2`), the
  commit body for a twin (`T6`).
- **[The test-cost pass grades taste]** → `nit` only; pickup fixes it, the loop does not spin on it ([B7](#b7)).
- **[The CI time lags a release]** → it names its commit; the local time is this release's.
- **[`gh` reads outside the repo]** → read-only, stated `none` when absent; the principle names it ([B11](#b11)).
- **[The next change moves precondition 1 to a fast gate]** → that change's grilling keeps precondition 1 the full
  gate, timed, for this line.
- **[This change edits the skills that build it]** → the skills are symlinked, so later phases run the edited text;
  no phase depends on a rule an earlier phase adds.

## Verdict

**Feasible.** Every edit is skill or doc text at a cited line, plus a scan per rule in an existing file; no code
path, no dependency.
