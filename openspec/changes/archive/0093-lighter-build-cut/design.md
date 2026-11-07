# Lighter build and cut — design

The cut's second plan review becomes conditional and every review a fresh worker; the moderate row of *Suggesting models*
names one cheaper model for a whole build. Verdict at the end: ready to build.

## Context

Read at `a2f9428` (v0.71.1). See [proposal](proposal.md) — Why.

- **F1. The plan review:** Step 8.5 re-runs the review after any doubt the cut fixes itself
  (`skills/mf-cut-change/SKILL.md:208`); a doubt changing a decision goes to the person or the switch (`:209`); its question and
  inputs are `:200-204`. Nothing says a later review must be a new worker.
- **F2. The cost:** every cut 0086–0091 ran a first and a second review, none conditional; 0086, 0088 and 0090 continued the first reviewer by a
  message; reviews were 18–52% of a cut ($8.4–16.9). 0074 D4 kept the second review on evidence from 0071 and 0072 and rejected
  a conditional one (`openspec/changes/archive/0074-lighter-cut/design.md:40`).
- **F3. The run's repairs:** rescue (D53, D60), the supervisor (0089) and the amend round (0092): one round about $3, against a
  reopen of about $8.5.
- **F4. *Suggesting models*:** a row per capability, and "the highest row any phase matches decides" (`skills/mf-cut-change/SKILL.md:356-363`);
  the moderate row is `| prose written fresh; moderate logic | the strongest tier · medium |` (`:360`). `mf-plan`'s models come
  from that table (`skills/mf-plan/SKILL.md:183-186`).
- **F5. The record:** D7 (`docs/decisions.md:87-99`), D40 (`:257-268`, rejecting "resumed verification conversations"), D41
  (`:450-459`, rejecting "hardcoded model names"), D42 (`:461-469`, no phrase scan); the map's Planning list (`:13`).
- **F6. The spec:** *A fresh worker reviews the plan before the cut commits* (`openspec/specs/sdd/spec.md:2397`), *An
  unattended cut decides by the brief's switch* (`:2873`), *Model suggestions use exposed capabilities* (`:718`).
- **F7. The overlap:** `0091-cut-halts` edits the cut skill's Unattended paragraph, Step 1, Step 6, Step 9 and *Never*, D38 and
  D58, adds D62 after D59, and MODIFIES *An unattended cut decides by the brief's switch* (its delta, `git show
  0091-cut-halts:openspec/changes/0091-cut-halts/specs/sdd/spec.md`). This change touches Step 8.5 and *Suggesting models*.

## Goals / Non-Goals

**Goals:** a cut pays for a second review only when its plan changed in substance; no review resumes another; a moderate
build runs on the cheaper model.

**Non-Goals:** a build session per phase; a model per phase; a change to the reviewer's question or inputs.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | Step 8.5 gains a review table: a **first** review always, a **second** only on a changed decision or task, each a fresh worker | B3, B4 | a second review after every fix · a message to the first reviewer |
| [D2](#d2) | The doubts table points at the review table | B3 | — |
| [D3](#d3) | The moderate row names Sonnet 5.5 · high, where the session offers it | B2 | a model per phase · a new fifth row |
| [D4](#d4) | `mf-plan`'s models line follows the moderate row | B2 | — |
| [D5](#d5) | The Acceptance's skills test reads table rows and the opening words of their cells, D42's one accepted scan | B6, C1 | a free sentence scan · dropping the Acceptance's test |
| [D6](#d6) | The record: D65; D7, D40, D41 noted; D42 names the scan it accepts | B5, C1 | — |
| [D7](#d7) | The delta: the model, plan-review and unattended requirements, the last on 0091's text | B2, B3, C2 | — |

### D1

In `skills/mf-cut-change/SKILL.md`'s Step 8.5, after "It answers with doubts, each with its `path:line`.", insert:

```markdown
| review | runs | reviewer |
|---|---|---|
| **first** | always, after the self-check | a fresh worker |
| **second** | only when a fix after the first — yours, the person's or the switch's — changes a `design.md` decision or a brief's `## Decisions` row, a `C` row included, or adds or removes a task | a fresh worker, never a message to the first |

Each review is a new worker given the change directory, `HEAD`'s sha and the question: a reviewer resumed by a message
reads its own doubts as settled. A simple fix is not reviewed again.
```

The question, its inputs and the no-fresh-worker paragraph stay. Reverses 0074 D4: the run's repairs (F3) catch what a second
review of a simple fix would, at about $3 against a review's share of a cut (F2).

### D2

In Step 8.5's doubts table:

- row 1's cell: "fix it without asking; then run the search script and the review once more" → "fix it without asking; then
  run the search script once more, and the **second** review when the fix meets its row".
- row 2's cell: "wait for the person, in Step 9's table; unattended, the [switch](#parameters)'s rule" → "wait for the person,
  in Step 9's table; unattended, the [switch](#parameters)'s rule, its `C` row calling the **second** review".

Row 3 stays. The Unattended paragraph's "survives the second review (Step 8.5)" stays: it holds when a second review runs, and
0091 edits the bullets beside it (F7).

### D3

In *Suggesting models*, the moderate row: `| prose written fresh; moderate logic | the strongest tier · medium |` →
`| prose written fresh; moderate logic — **moderate** | Sonnet 5.5 · high, where the session offers it; else the strongest tier · medium |`.
After "The highest row any phase matches decides the capability; map it to the offered models and supported controls." add:
"A build whose highest row is the moderate one runs whole on Sonnet 5.5 · high: one model a change, never one per phase."

A build is **moderate** when the moderate row is the highest any of its phases matches; a lighter phase beside it does not
change that. A build whose phases all sit in the lower rows keeps the mid tier those rows name. Editing the row, not adding one,
keeps one row per capability under "the highest row decides".

### D4

`skills/mf-plan/SKILL.md`, *The brief*'s closing paragraph: "by `mf-cut-change`'s *Suggesting models* table; the cut station's
own" → "by `mf-cut-change`'s *Suggesting models* table — Sonnet 5.5 · high for a build whose highest row is the moderate one; the
cut station's own", the phrase `Sonnet 5.5 · high for a build` on one line.

### D5

The Acceptance asks for a skills test of Step 8.5 and the moderate row. D42 keeps sentence scans out of `tests/test_skills.py`,
so the test reads table rows by their labels, as `_section_labels` and `_plan_problems` already do — but it also checks the
opening words of the **first** and **second** rows' reviewer cells, the **second** row's condition cell and the moderate row's
model cell, which D42 rules out. The Acceptance is the person's, so it stands, and D42 names this scan as the
one it accepts ([D6](#d6), C1). In `tests/test_skills.py`, after the plan station's block, add:

- constants `_CUT = "mf-cut-change"`, `_REVIEW = "## Step 8.5 — Plan review"`, `_MODELS = "## Suggesting models"`, under a
  comment naming this design's D5;
- `_section_rows(path: Path, heading: str) -> list[list[str]]` — the stripped cells of each `| … |` row in `heading`'s
  section, up to the next `## ` heading;
- `_cut_review_problems(base: Path) -> list[str]`, `<prefix>` being `skills/mf-cut-change/SKILL.md`, returning in this order:
  - `<prefix>: does not exist`, alone, when the file is missing;
  - per label `first`, then `second`: `` <prefix>: `## Step 8.5 — Plan review` has no **<label>** row `` when no row's first
    cell is `**<label>**`; else `<prefix>: the **<label>** review is not a fresh worker` when its last cell does not open
    `a fresh worker`; and, for `second` alone, `<prefix>: the **second** review is not conditional` when its second cell does
    not open `only when`;
  - `` <prefix>: `## Suggesting models` names no Sonnet 5.5 · high build `` when no row of `_MODELS` has a last cell opening
    `Sonnet 5.5 · high`.

The tests:

- `test_the_cut_holds_its_plan_review_and_moderate_build` — `_cut_review_problems(_REPO) == []`.
- `test_the_plan_review_scan_reports_each_breach(tmp_path)` — first plants, through `_plant`, a Step 8.5 table with
  `| **first** | always | the cutter |` and `| **second** | always | a message to the first |` and a *Suggesting models* table
  with `| prose | the strongest tier · medium |`, and asserts the first-not-fresh, second-not-fresh, second-not-conditional and
  no-Sonnet lines, in that order. It then plants the Step 8.5 and *Suggesting models* headings with no rows, a `| **second** | only when | a fresh worker |` row
  under `## Step 9` and a `| x | Sonnet 5.5 · high |` row under `## Never`, and asserts the no-first-row, no-second-row and
  no-Sonnet lines.

### D6

`docs/decisions.md`:

- **D65**, the last decision of *Planning*, before `## The check loop and the release`, and `D65` the last id of the map's
  Planning list. The build's base holds `0091-cut-halts`'s D62 there (`after:`), so the list reads `D58, D59, D62, D65` or,
  with other versions merged first, more ids between. The check-loop ids on that line move right to keep two spaces after the
  Planning list; the diagram's line above stays:

  ```markdown
  ### D65 · A lighter plan review and build

  **The cut's plan review runs once; a second, by a new worker, runs only when a fix after the first changes a `design.md`
  decision or a brief's `## Decisions` row, a `C` row included, or adds or removes a task. Every plan review is a fresh worker
  ([D40](#d40--workers-are-fresh-and-observable)). A change whose highest row of *Suggesting models* is the moderate one is
  suggested Sonnet 5.5 · high for its whole build, where the session offers it: one model a change, and one build session.**

  - **Why:** a second review on every cut put reviews at 18–52% of a cut's cost, and the run now repairs a wrong plan — rescue, the supervisor, the amend
    round — at about $3 a time; a Sonnet build costs about half per line, and a fresh session per phase saved about $1 a build.
  - **Rejected:** a second review after every fix · resuming a reviewer by a message · a build session per phase, which needs a
    guard against re-spawning without end · a model per phase.
  ```

- **D7**'s bold text: "built as written; it runs no gate.**" → "built as written, a second review only after a fix that changes
  a decision or a task ([D65](#d65--a-lighter-plan-review-and-build)); it runs no gate.**", the phrase `a second review only
  after a fix` on one line.
- **D40**'s bold text: after "and writes no findings file." insert "Each plan review is a new worker, never a message to the
  reviewer before it.", the phrase `never a message to the reviewer before it` on one line.
- **D41**: after its **Rejected** bullet, add "- **Names one model:** *Suggesting models*' moderate row, Sonnet 5.5 · high, taken
  only where the session offers it ([D65](#d65--a-lighter-plan-review-and-build))."
- **D42**: after its **Gave up** bullet, add "- **Accepts:** the plan-review scan of `tests/test_skills.py`, which reads the
  opening words of cells in the cut's review table and *Suggesting models*: the Acceptance of
  [D65](#d65--a-lighter-plan-review-and-build) asked for it.", the phrase `the plan-review scan of` on one line.

0074 D4 lives in an archived design and is not edited: D65 is what holds.

### D7

[The delta](specs/sdd/spec.md) MODIFIES:

- *Model suggestions use exposed capabilities* — the moderate build, and a scenario. Its scenario *The cut records its
  suggestion* reads "no file under `openspec/changes/<change-id>/` holds the suggestion for its own stations" for "nothing …
  names a model": this change must name the model the skill gains (C2).
- *A fresh worker reviews the plan before the cut commits* — the conditional second review, the new worker, and the scenarios *A simple fix* and *A fix that adds a task*.
- *An unattended cut decides by the brief's switch* — a `decided by the cutter` row calls a second review. The text is
  `0091-cut-halts`'s delta for it, plus that sentence: 0091 releases first (`after:`), so the fold keeps its edit.

## Tests

`git grep -c '^def test_' a2f9428 -- tests/test_skills.py` prints `18` at the cut. Added, unit, under `T1`: the tests of
[D5](#d5), `test_the_cut_holds_its_plan_review_and_moderate_build` and `test_the_plan_review_scan_reports_each_breach`, reading text alone, under 5 s. No end-to-end run; none deleted or merged. The rest of the skill prose is held by
review (D42).

## Dependencies

None.

## Risks / Trade-offs

- **A simple fix that was wrong** → no second review sees it; the build's Step 1, the `Verify:` refusal and the run's rescue and
  amend round catch it, at about $3 (F3).
- **A named model in a skill a target runs** → taken only where the session offers it, the strongest tier · medium otherwise
  (D41's bound kept).
- **0091 touches the same skill and requirement** → this change's hunks sit apart from 0091's (F7); `mf-integrate` merges the
  rest.

## Verdict

Ready to build.
