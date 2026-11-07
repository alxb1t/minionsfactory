# Drift amends — design

A drift card that needs the plan amended halts converge at the debt write; the rescue's amend answers it, and converge passes
the amend by rule. Skill text and a test; `conduct.py` already takes the halt. Verdict at the end: ready to build.

## Context

Read at `5650ab1` (v0.70.0), the brief's own sha: every fact citing a path stands. `S` is `skills/mf-converge/SKILL.md`, `W` is
`skills/mf-converge/references/worker.md`, `R` is `skills/mf-rescue/SKILL.md`, `C` is `skills/mf-ship/scripts/conduct.py`, `F` is
`tests/fake_worker.py`, `T` is `tests/test_conduct.py`.

- **F1. The fixer.** It never edits the change's `tasks.md` or `design.md`: such a card is `wontfix`, naming the amend, "and the
  round halts `amend needed — <card ids>`" (`S:343-344`). Pickup sends every `open` `drift` card to it (`S:385-390`).
- **F2. The verify pass.** `wontfix → accepted`, or reopened (`W:67-73`); the pass itself (`W:94-102`). The card's fields
  (`W:135-149`) and its writing limits (`W:151-152`).
- **F3. The debt.** Step 9 takes every non-blocking card not `verified`, runs its **Still true?** check, and writes the rest
  under `.minions/debt.lock` (`S:392-413`). A drift card found after the pickup is `open` there. D15: "drift never blocks"
  (`docs/decisions.md:211-225`, the line `:222`).
- **F4. The answered halt.** A person's commit past a halt both files judged opens `· amended` from round 1 (`S:151-154`); the
  person's amends answer a clean catch-up halt, a `verify: halt` and an `amend needed` halt, and only the catch-up one runs the
  catch-up round again (`S:156-161`). Amends alone pass by rule (`S:203-209`, `S:222-233`).
- **F5. The run.** `_amendable` takes every `amend needed` halt (`C:817-831`); `_amended_only` (`C:834-856`) and `_answered`
  (`C:859-891`) void it past amends alone, the stage `converge`, `AMENDED` (`C:82`). `_rescue_amends` gives the rescue `AMENDS`, and
  `proposal.md` under the switch, save a blocking security card (`C:2124-2155`). The grant comment reads "An amended run starts from
  round 1" (`C:3346`).
- **F6. The rescue.** Its row: "the amend its `wontfix` cards name" (`R:67`); a `## Decisions` edit is a diagnosis save under the
  switch (`R:82-84`).
- **F7. The fake.** `_amend_needed` writes a blocking `wontfix` card and a halt after `start` (`F:90-114`); the converge branch
  checks `amend-halts` (`F:440-442`) before `by-rule` (`F:457-459`); `_by_rule` passes a selection of the person's amends
  (`F:133-167`). `rescue-decides` commits a `design.md` prose amend and a decision with `Decided-by: rescue` (`F:226-236`).

## Goals / Non-Goals

**Goals:** a run of fake workers that meets the brief's Acceptance: a drift card naming the person's amend ends the round
`amend needed`, not in the debt; under `decide = "recommended"` the rescue's amend answers it, and the version goes on with no
new round 1.

**Non-Goals:** a change to `conduct.py`'s logic (F5 takes the halt); a `nit` naming an amend found after the pickup; the archives
already released stale.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | An **amend card** names `openspec/changes/<change-id>/tasks.md` or `design.md` in its **Fix** or its `wontfix` note | Q5 | the conductor judging which card "wants" an amend: it judges nothing |
| [D2](#d2) | The verify pass keeps an amend card's `wontfix` | Q5 | `accepted`, as today |
| [D3](#d3) | A blocking amend card halts after the fix pass; a non-blocking one goes on to verify | Q5 | halting the pickup round at its fix pass |
| [D4](#d4) | Step 9 halts on a non-blocking amend card, `wontfix` or `open` `drift`, still true, before the lock; in the catch-up its amend opened, it goes on | Q5 | a halt on every re-run |
| [D5](#d5) | An answered `amend needed` halt with both files clean runs the catch-up round again | Q5 | `· amended` from round 1 |
| [D6](#d6) | The rescue amends what the cards name; D15 and D16's debt line amended | Q5, Q8 | — |

### D1

A card whose fix needs the change's `tasks.md` or `design.md` names that file by its path in its **Fix**, e.g.
`` amend `openspec/changes/0087-drift-amends/design.md`'s D3 · size: one line ``. W gains, between the writing limits
(`W:151-152`) and the example card (`W:154`):

> **An amend card** is one whose **Fix**, or whose `wontfix` **Status** note, names the change's `tasks.md` or `design.md` by its
> path, `openspec/changes/<change-id>/design.md`. The fixer never edits those files, and converge halts on such a card.

The test is the path in the text: mechanical, as converge's pick by size is.

### D2

W's diagram (`W:69-73`) becomes, the amend's line taking the `└` row and `either → open again` moving below it:

```
  open ──fix pass──▶ fixed ───────────────────┬─▶ verify pass, the same checker:
    │                                         │     fixed → verified · wontfix → accepted
    └──fix pass──▶ wontfix + justification ───┘     an amend card's wontfix stays wontfix
                                                    either → open again, with a one-line reason
```

The verify pass (`W:94-102`) gains a paragraph:

> An amend card's `wontfix` stays `wontfix` when its justification holds, never `accepted`: converge's Step 9 halts on it. A
> justification that does not hold reopens it, as any `wontfix`.

`open_blocking` counts `open` cards alone, as today.

### D3

S's fixer bullet (`S:343-344`) becomes:

> **never edits the change's `tasks.md` or `design.md`**: a card whose fix needs one is `wontfix`, naming the amend the person
> commits by its path. A blocking card's halts the round `amend needed — <card ids>` after the fix pass; a non-blocking card's
> is verified, and halts at Step 9;

A halt at the pickup's fix pass would leave the fixer's other fixes unjudged and its head past the judged head (F4); at Step 9 the
round is verified and the halt's head is both files' `head:`.

### D4

S's Step 9 gains a paragraph above the lock (`S:396`):

> **Amend cards first**, before the lock. Take every non-blocking [amend card](references/worker.md#the-card) that is `wontfix`,
> or `open` and `drift`, and run its **Still true?** check: one the check shows gone is moot, as in item 2. Any left → halt
> `amend needed — <card ids>`, writing nothing to the debt. In a catch-up run whose selection holds the person's amend, they go
> on as every other card.

```
  Step 9 ─▶ amend cards still true? ── none ─▶ lock ─▶ items 1–7
                 │ some
                 ▼
       catch-up over the person's amend? ── yes ─▶ lock ─▶ items 1–7 (to the debt)
                 │ no
                 ▼
       halt amend needed — <ids> ─▶ rescue's amend ─▶ catch-up by rule (D5) ─▶ Step 9
```

The exception keeps a loop out: a run rescues a halted stage once (`Run.rescued`, `C:3084-3093`), so a second halt at the same
cards would wait for the person over an amend already made.

### D5

S's amends paragraph (`S:156-161`): "The answered catch-up halt runs the [Catch-up round](#catch-up-round) again" → "The answered
catch-up halt, and an answered `amend needed` halt whose findings files both still say `verdict: clean`, run the
[Catch-up round](#catch-up-round) again", the words `findings files both still say` on one line. The paragraph above it
(`S:151-154`) ends: "No grant is needed, and the catch-up round does not apply." → "No grant is needed, and the catch-up round
does not apply, save to the person's amends, as the next paragraph says."

A Step 9 halt leaves both files clean and judged at its head (D3), so the catch-up round applies (`S:183-184`); a selection of
amends alone passes by rule (`S:208-209`), then Step 9 (D4). The run needs no change: F5 voids the halt past amends alone and
spawns converge, which picks the catch-up from disk. A comment in `Run.rescue` and one in `Run.advance` go stale, and become, at
their own indents:

```
before (C:3146):  # A taken amend is the rescue's answer: converge opens its amended run.
after:            # A taken amend is the rescue's answer: converge picks its run from disk.

before (C:3346):  # An amended run starts from round 1: the grant goes unspent.
after:            # An answered halt converges afresh or catches up:
                  # the grant goes unspent.
```

The second wraps to keep ruff's E501 (88 columns) at its indent.

### D6

R's `amend needed` row (`R:67`) keeps its first cells; its fix cell becomes:

> the amend its cards name — a `wontfix` card's note, or an open drift card's **Fix** — in `tasks.md` and `design.md`'s prose

Without the switch a `## Decisions` edit stays a diagnosis (`R:82-84`), and waits for the person.

D15's drift line (`docs/decisions.md:222`) becomes:

> - **Drift never blocks:** prose the code contradicts — save an amend card, one naming the plan's amend: converge halts
>   `amend needed` on it at the debt write, and the person's amend or the rescue's answers it.

The heading stays, so its anchor holds. D16 (`docs/decisions.md:229-230`) says the same of the debt: "Everything else becomes a
card" → "Everything else, save an amend card ([D15](#d15--anchored-harms-block-drift-never-does)), becomes a card".

## Tests

`git grep -c '^def test_' -- tests/` totals 235 at the cut, 116 in `tests/test_conduct.py`. Added: one integration test of the
conductor, a run of `tests/fake_worker.py`, marked `slow` as `test_a_rescue_decides_under_the_switch` is (`T1`). No end-to-end
test. `T2`: the rescue tests
(`T:1546-1776`) reach `amend needed` with a blocking card and a `changes-requested` file alone. `conduct.py` reads no difference
between the halts (`_amendable`, `C:823`): what differs is the state on disk and the converge run that follows it, and a step in
`test_a_rescue_decides_under_the_switch` would need its own primary, the whole setup of a new test.

- `test_a_drift_amend_goes_on_by_rule` — the fake's new `drift-halts` converge mode, checked right after `amend-halts`
  (`F:440-442`) and while no prose amend stands, writes both findings files `verdict: clean` at `HEAD`, review holding an `open`
  card R6, its **Priority** `drift · review · maintainability` and its **Fix** naming `openspec/changes/<id>/design.md`, and a
  status log whose run holds `halt — amend needed — R6 · head <HEAD>` above its `start` line, newest first, as `_amend_needed`
  writes them (`F:110-114`), through a new `_drift_halt` beside `_amend_needed`.
  With `decide = "recommended"` atop the models file and the `rescue-decides` and
  `by-rule` modes: the calls are probe, build, converge, `rescue … with decide=recommended`, converge, release; the log holds
  `rescue — 0001-todo: decided · converge-halted · <sha7>`; the status log opens `## Run 2 — d · catch-up`, with no `· amended`;
  the run ends `done — released v0.1.0 · decided 0001-todo`.

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A worker that names an amend in a card forces a halt and a rescue's amend: worker steering, the class `THREAT_MODEL.md`
  accepts; the amend's paths are checked (D53), and the catch-up's gate and `gate_check.py` judge it.
- An amend that misses the card's defect sends the card to the debt in the catch-up run (D4): it is carded, as today, not lost.
- A card that names the path for an edit the fixer could make elsewhere halts once: the rescue reads it, and diagnoses when
  nothing in the plan is to amend.
- The fake writes the Step 9 halt and the catch-up itself: the test proves the run's half; the skill text is held by review
  (D42).
- A Step 9 halt leaves both findings files `verdict: clean` at `HEAD`, and `mf-release`'s preconditions read the files, not the
  status log (`skills/mf-release/SKILL.md:111-135`): a release run by hand after the halt would pass them. Under `mf-ship` the
  stage stays halted (`stage_of`). Left out by the cutter (the brief's C1): a release precondition on the status log is a rule
  the brief did not settle.

## Verdict

Ready to build.
