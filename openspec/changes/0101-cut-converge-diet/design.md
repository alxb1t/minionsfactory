# Cut and converge diet — design

How the cut's reviews and helpers, converge's pickup, its bundle and the release read less.
**Verdict:** settled; build the phases in order — plan reviews, helpers and notes, the pickup check, the bundle, the
release and the record.

## Context

What the line holds at `ed7298f`, with `0100-worker-diet` merged before the build ([proposal](proposal.md) `after:`). Each
line number is `ed7298f`'s: 0100 moves some, so the build finds a cited line by its quoted text. `X` is
`skills/mf-cut-change/SKILL.md`, `V` is `skills/mf-converge/SKILL.md`. Each cost is the brief's ledger (0096-codex-ready
$31.96, 0097-cross-model $55.44); each count the command named.

- **F1. Plan reviews.** `X:204-227`: a fresh worker on the session's model gets the change directory, `HEAD` and the
  question, with no bound. The second review, `X:215`, is given the same and re-reads everything. 0097's took 66 and
  72 turns at 158–185k median context ($4.12 + $4.64); both caught real defects. `tests/test_skills.py`'s
  `test_the_cut_holds_its_plan_review_and_moderate_build` reads the table: each row's last cell starts `a fresh worker`,
  the second's runs cell `only when`.
- **F2. The cut commit.** `conduct.py`'s `_check_cut` (`skills/mf-ship/scripts/conduct.py:684`) wants
  `docs(<id>): land the change directory` at the branch's tip, and `gate_check.py`'s `check_verify`
  (`skills/mf-converge/scripts/gate_check.py:305-316`) reads the plan at the cut commit: no commit can come between
  the reviews.
- **F3. Helpers.** `X:118-123`: at most four read-only helpers, naming no model, answering in the cut's thread. 0097's helpers
  cost $3.60, 0096's $2.98, on Opus; 75–77% of each cut's reads repeated a file another worker of the cut had read.
  D40 (`docs/decisions.md:297-298`) has a helper write no file.
- **F4. Pickup.** `V:431-444`: once both verdicts are clean, pickup fixes the small and `drift` cards, then verifies in a
  normal Step 7 round, which counts against the cap (`V:425`). 0096's round 3 verified only R1, S2 and S3, all
  non-blocking: $1.6–1.9. Step 7 (`V:393-421`) re-runs the gate and `gate_check.py`, runs `surfaces.py` and `open_cards.py`,
  and dispatches one verify worker per role. No code reads a `pickup` or `verify` status-log event; a round
  number is read only by `conduct.py status`, which prints conformance's `round:` (`conduct.py:6247`), and by the metrics
  from `verdicts` lines (`review_metrics.py:431-465`). `conduct.py` judges both files' `verdict` and `head:` (`_unjudged`,
  `conduct.py:1026-1040`). `worker.md:45` says `round:` is "bumped by each verify pass"; `verify.md:40-41` lets a verify
  worker edit its own findings file alone; Step 6 names "the pickup round" (`V:354`).
- **F5. The bundle.** `skills/mf-converge/scripts/bundle.py:122-133` writes each modified or removed living requirement in
  full: 66.6k (0095), 79.0k (0096), 25.9k (0097) chars, largely the delta conformance also reads.
  `skills/mf-converge/scripts/debt_match.py:77-87` appends the debt cards to the bundle as a section, which adversarial
  reads alone (`skills/mf-converge/references/generic-adversarial.md:28`), and all of it.
- **F6. The patch.** Both packet rows say `diff.patch` is "read once" (`generic-conformance.md:25`,
  `generic-adversarial.md:24`); checkers read it 11 times, 183k chars, and `worker.md` 5 times.
- **F7. The release.** `skills/mf-release/SKILL.md:86-97`, `:112-116` and `:133` read both findings files whole — 48k
  chars — for `verdict`, `head:` and each blocking card's Status; `:302-303` names each `inconclusive` section from them.
- **F8. Debt.** `0095·R3`: `skills/mf-converge/references/worker.md:22` gives the full plan to both roles in an amend
  round. `0095·S5`: `THREAT_MODEL.md`'s `## Surfaces` (`:89-130`) lacks `references/verify.md`.
- **F9. The tests.** `grep -c "^def test_"` prints `2` for `tests/test_bundle.py` (`3` once `0100-worker-diet` adds
  `test_decisions_print_what_the_files_cite`), `2` for `tests/test_debt_match.py` and `21` for `tests/test_skills.py`.
- **F10. The fixer's bound.** `V:369-371`: the fixer never edits the change's `tasks.md` or `design.md`; a card whose fix
  needs one is `wontfix`, an amend card (`skills/mf-converge/references/worker.md:162-164`), and halts `amend needed`. D53
  (`docs/decisions.md:709`) says the same. 0098 (`c5bb4ce`) and 0100 (`b29a016`) each paid a round and a rescue for a
  `design.md` drift line. `conduct.py`'s `_decisions` (`skills/mf-ship/scripts/conduct.py:2477-2489`) reads a design's
  `## ` headings and its `## Decisions` section as its decisions, for a rescue's decided amend.

## Goals / Non-Goals

**Goals:** the acceptance of the brief's item 2 — a plan review's prompt carries the packet and the 40-turn budget, a review
reaching it returns `budget reached`, a second review judges only the change since the first; the helpers on Sonnet ·
medium and the cut's notes file; a pickup checked by one verify pass at medium on its own diff, no round 3; requirement
diffs and the debt cards' own file; `diff.patch` read once; the release reading frontmatter and card lines; the fixer
correcting the `design.md` prose a `drift` card names; a green gate.

**Non-Goals:** the savings themselves, judged in the ledger; a scripted spec fold; one build worker per phase; `0095·R6`.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C7 | a second review judges the change directory's diff since a **review tree** the cut records by staging the directory and running `git write-tree` before the first review | no commit can come between the reviews (F2) |
| C8 | the cut writes the helpers' answers to `.minions/changes/<change-id>/cut-notes.md`; a helper stays read-only and writes no file | D40 keeps a helper writing no file; the acceptance has the cut write and read the notes |
| C9 | the pickup check is one fresh worker over both findings files, on adversarial's model when a picked card is adversarial's or `surfaces.py` exits 1 over the pickup's range, else conformance's, at `medium`; a role it needs being a mailbox role, the pickup is verified in a normal round, counted; it sets both files' `head:`, never `round:`; a blocker it leaves goes to a fix and a counted round | T8's one pass; D64 rejects an adversarial verify skipped by the conductor's judgment, so the model follows the cards and the surfaces; D68 sends a checker on another host through the mailbox |
| C10 | the release reads each findings file's frontmatter and, by one `grep`, its cards' title, Priority and Status lines and its `inconclusive` lines | preconditions 2 and 3 need each blocking card `verified`, which no frontmatter key shows; `0095·S1` names precondition 3 as the last guard |
| C11 | the debt cards go to `.minions/changes/<change-id>/debt-cards.md`, which `debt_match.py` writes whole; conformance reads it beside the bundle, adversarial in its place | T11 names no file |
| C12 | "read `diff.patch` once" is a rule on how: top to bottom in slices of at most 2000 lines, never a slice again, a hunk needed again found with `grep -n` on the patch | the packet already names the patch once (F6); the reads were slices and re-reads |
| C13 | the pickup check is one checker for both files: the principles' *Checker* and *`fixed` is a claim*, `worker.md`'s Status flow and converge's *Never* say so | those lines say each station alone promotes its own file's cards |
| C14 | the pickup check's model follows `surfaces.py`'s exit over the pickup's range, which also exits 1 on an adversarial card not `verified` or `accepted` | "touches a surface" was narrower than the rule the skill runs |
| C15 | while a pickup check is due, every way a resumed converge reaches Step 7 goes to the pickup check | the resume table alone missed Step 6's and a verify round's paths |
| C16 | the reviewer opens a cited path or `path:line`; the cited line numbers are `ed7298f`'s; `surfaces.py`'s exit 0 writes nothing by rule in a pickup check; `diffed` takes the living spec and the delta's block; the living scenario naming "the pickup round's fixer" is modified | one reading each |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The review packet, the budget and the review tree | T3, T19, C7 | a commit between the reviews — F2 |
| [D2](#d2) | Helpers on Sonnet 5.5 · medium; the cut's notes | T4, C8 | helpers writing the notes — D40 |
| [D3](#d3) | The pickup check | T8, C9 | the pickup verified in a full round; one verify worker per role |
| [D4](#d4) | Requirement diffs, `debt-cards.md`, the patch in slices | T11, C11, C12 | the debt cards kept in the bundle |
| [D5](#d5) | The release reads frontmatter and card lines | T12, C10 | the frontmatter alone — a `fixed` blocker would pass |
| [D6](#d6) | D71; D16, D40, D57, D64, D66 and a principle amended; the surfaces | — | — |
| [D7](#d7) | The fixer corrects the `design.md` prose a `drift` card names, never a decision | T24 | the fixer kept off `design.md` — 0098 and 0100 each paid a round and a rescue (F10) |

### D1

`X`'s `## Step 8.5 — Plan review`:

- **The opening paragraph** — "Give it the change directory and `HEAD`'s sha, and one question" becomes "Give it the
  **review packet** — the change directory, `HEAD`'s sha, `.minions/changes/<change-id>/cut-notes.md` and one question";
  after "save a `**HALT CHECK**`, which should hold?" it gains "It starts from the packet, opening another file only at a
  path or `path:line` the change or the notes cite."
- **The budget** — a paragraph after it: "**The budget.** The prompt gives the reviewer 40 turns, which it counts as its
  tool calls: at the 40th it stops and returns its doubts so far, its first line `budget reached`. Take each as a doubt
  still standing after the second review." No host caps a subagent's turns; the reviewer counts its own.
- **The review tree** — a paragraph after the review table: "**The review tree.** Before the first review, run
  `git add openspec/changes/<change-id>/`, then `git write-tree`; the sha it prints is the review tree. Before a second,
  run the same `git add`; the second reviewer gets its packet and the review tree, runs
  `git diff --cached <review tree> -- openspec/changes/<change-id>/`, and judges that diff, and each
  task that cites a decision or a path the diff changes."
- **The table** — the second row's reviewer cell "a fresh worker, never a message to the first" gains ", judging the diff
  since the first". Each row's last cell still starts `a fresh worker`, and the second's runs cell `only when`.
- **"Each review is a new worker given the change directory, `HEAD`'s sha and the question"** becomes "Each review is a new
  worker given its packet".

### D2

`X`'s Step 2:

- **Helpers** — "dispatch at once at most four read-only helpers in all, the areas grouped to fit" becomes "dispatch at
  once at most four read-only helpers in all, each on Sonnet 5.5 · medium where the host offers it — on Claude Code the
  Agent tool's `model: sonnet` and `effort: medium` — the areas grouped to fit".
- **The notes** — a paragraph after *Helpers*: "**The notes.** `mkdir -p .minions/changes/<change-id>`, then write
  `.minions/changes/<change-id>/cut-notes.md` afresh: a `# <change-id> — cut notes` title, then one line per helper
  answer and one per fact you read for the design, each `<fact or question> — <answer> · <path:line>`, as it comes. Read
  the notes, not the file again, for a fact they hold. A helper writes no file: you write its answer."
- **The source is evidence** — "it and every file it points to, or a helper's answer" becomes "it and every file it points
  to, a helper's answer or the notes".

### D3

`skills/mf-converge/references/verify.md`:

- **The opening line** — "A verify round re-judges the cards a fix touched, by the checker that wrote them." gains ", save
  a [pickup check](#the-pickup-check)".
- **`## The pickup check`** — a section before *What you do*: "A **pickup check** verifies a pickup's fix once no blocker
  is open: one worker for both files. You get both `<role>.open.md`, `diff.patch` — the pickup's own diff — both findings
  paths and the design's `## Tests` section. Judge each open card of both files as below, and run conformance's passes
  over the diff. A regression is a new card in the file whose role would find it — a broken spec, plan, doc or test rule
  in conformance's, any other in adversarial's — on that file's scale. In each file rewrite `head`, `reviewed`,
  `open_blocking` and `verdict`, and never `round`: a pickup check is no round. Edit both files by the rule below."
- **The closing rule** — "Edit only your open cards' **Status** lines, the frontmatter, the Summary and the `## Resolution
  log`, and add a card for a regression: nothing else in your findings file, and no other file." gains, after "no other
  file", "— in a pickup check, both findings files, by the same rule".

`skills/mf-converge/references/worker.md`: the frontmatter's `round: <int, bumped by each verify pass>` becomes
`round: <int, bumped by each verify round, never by a pickup check>`; the Status diagram's "verify pass, the same checker:"
becomes "verify pass, the checker or a pickup check:".

`V`:

- **The diagram** — its bottom-left loop becomes
  `5 ◀── 7 verify ◀── 6 fix ◀── a blocker left ── 8 pickup: 6 fix, one check`, the edge below reading
  `│ none picked, or clean`.
- **The events table** — the `pickup` row's detail becomes "the picked ids, or `none`; after the pickup check's read,
  `checked`, then each file's `verdict` and `open_blocking`, and the worker's `executor`, `model`, `effort` and `tokens`".
- **Resuming a run** — before the table, "**A pickup check is due** when this run's latest `pickup` line names ids and no
  `checked` line follows it: while one is due, every way to Step 7 — the table's, a verify round's, Step 6's — goes to
  Step 8 item 5." The `pickup` row becomes "`none` → Step 9;
  `checked` → Step 8 item 6; else Step 8 item 4, the same ids".
- **Step 6** — "in the pickup round, exactly the cards Step 8 names" becomes "in a pickup, exactly the cards Step 8 names".
- **Never** — "The stations own their files; you read them." becomes "The stations, and a pickup check, own their files;
  you read them."
- **Step 7** — "**The cap is three rounds, and the pickup round counts.**" becomes "**The cap is three rounds; the pickup
  check is no round.**"; "naming the pickup round if one ran" becomes "naming the pickup if one ran".
- **Step 8** — item 4 becomes "**Send them by id to the Step 6 fix station.** Its re-freeze is the pickup's own diff." Item
  5, new: "**The pickup check** — re-run the gate and `gate_check.py`, and write `verify`, as Step 7 does; run
  `open_cards.py` for both files, and `surfaces.py` over the re-freeze's range, halting on its exit 2 as Step 7 says; its
  exit 0 writes nothing by rule here, for the check sets both heads; a fixer that committed nothing runs no `surfaces.py`,
  as in Step 7, and counts as exit 1. The check **needs** adversarial when a picked
  card is adversarial's or `surfaces.py` exits 1, else conformance. A role it needs is a mailbox role → verify in a normal
  Step 7 round instead, counted. Else dispatch one fresh worker, its description `verify round <N> · pickup`, `<N>` the
  last judged round, on the needed role's model at effort `medium`. Give it [verify](references/verify.md), both
  `<role>.open.md`, `diff.patch`, both findings paths and the design's `## Tests` section." Item 6, new: "**Read both
  files** under Step 5's table, writing no `verdicts` line, and write `pickup` with `checked`. Both `clean` → Step 9. A
  blocking card open → Step 6 with it, then a Step 7 round, counted. A card first found in the check is not picked: one
  pickup per run."

### D4

- **`bundle.py`** — `diffed(living: str | None, block: str, title: str)` takes the living spec's text, `None` when there is
  none, and the delta's block for the title, `""` for a REMOVED title; it returns the requirement's unified diff,
  `difflib.unified_diff` over the lines of `_requirement(living, title)` and of `block`, with `fromfile="living"`, `tofile="delta"` and
  `lineterm=""`, in a fenced `diff` block; a title the living spec lacks keeps "- `<title>` — not in the living spec".
  `bundle` calls `_requirements` once per section, which stays `integrate.py`'s copy, so a MODIFIED title diffs against
  its delta block and a REMOVED one against nothing.
  The section heading becomes `Requirements the delta modifies or removes, as diffs`; `REPLACES` and the module docstring
  say "each requirement its delta modifies or removes, as a diff from the living spec"; the docstring's *Why* gains
  `0101-cut-converge-diet design D4`. The printed line is as now.
- **`debt_match.py`** — the third argument is the cards file, written whole: `HEADING = "# Debt cards on the diff's files"`;
  `page(found)` returns the heading, a blank line, then the cards or `None.`; `main` reads the debt and the patch alone and
  writes `page(found)`; `section` goes. The usage line names `<debt-cards.md>`, the docstring "writes the debt cards on the
  diff's files to their own file", and `write`'s docstring "the cards file".
- **`V` Step 2 item 4** — the bundle "and the living requirements its delta modifies or removes" becomes "and each
  requirement its delta modifies or removes, as a diff"; "Then append the debt cards on the diff's files" becomes "Then
  write the debt cards on the diff's files", the command's last path `.minions/changes/<change-id>/debt-cards.md`.
- **`generic-conformance.md`** — the `bundle.md` row becomes "the decisions the change cites, in full, an index of all, and
  each requirement the delta modifies or removes as a diff from the living spec, in place of `docs/decisions.md` and the
  living specs"; a `debt-cards.md` row follows it, "the debt cards on the diff's files, in place of the debt, for the
  contract's repeat rule"; *Spec*'s "the bundle's living requirements" becomes "the bundle's requirement diffs"; "check
  repeats against the bundle's debt cards" becomes "check repeats against `debt-cards.md`".
- **`generic-adversarial.md`** — the `bundle.md` row becomes `debt-cards.md`, "the debt cards on the diff's files, for the
  contract's repeat rule".
- **The patch rows** — in both references, "read once;" becomes "read once — top to bottom, in slices of at most 2000
  lines, never a slice again, a hunk you need again found with `grep -n` on the patch;"; `verify.md`'s `diff.patch` row
  "read once" gains the same.
- **`worker.md`** — the repeat rule's "a debt card in the bundle's `## Debt cards on the diff's files` holds" becomes "a
  debt card in `debt-cards.md` holds"; *Scoping*'s "An **amend round** judges its whole range with the full plan in its
  reading set." becomes "In an **amend round**, conformance judges its whole range with the full plan in its reading set."
  (`0095·R3`).

### D5

`skills/mf-release/SKILL.md`, Step 1, after "precondition 4 says what absence means.": "**Read each findings file in two
reads, never whole:** its frontmatter, its first 20 lines — `Read` with a limit, or `sed -n 1,20p <file>` — to the
closing `---`; then its cards' lines,
`grep -n -i -e '^- \*\*' -e 'Priority:' -e 'Status:' -e 'inconclusive' <file>`. Preconditions 2, 3 and 7, and the report's
`inconclusive` sections, are judged from those reads alone." The close-out's "each `inconclusive` section, from the
findings files' frontmatter and Summaries" becomes "each `inconclusive` section, from the `grep`'s `inconclusive` lines".

### D6

- **D71**, in `docs/decisions.md` after D68's block, and `D71` after `D68` on the map's check-loop line:

### D71 · The cut and converge read what changed

**The cut's plan reviewer starts from a packet — the change directory, `HEAD`, the cut's notes and the question — with a
budget of 40 turns, and a second review judges only the change directory's diff since the first. The cut's helpers run on
Sonnet 5.5 · medium, and the cut writes their answers to `cut-notes.md`. Once no blocker is open, a pickup's fix is checked
by one verify worker at medium, which is no round. The bundle holds each changed requirement as a diff, the debt cards on
the diff's files have their own file, and the release reads the findings files' frontmatter and card lines alone.**

- **Why:** 0097's cut spent $8.76 on two reviews that re-read everything and $3.60 on Opus helpers whose reads repeated
  75–77%; 0096's round 3 verified only pickups, $1.6–1.9; bundles of 26–79k chars repeated the delta; the release read 48k
  chars for two verdicts.
- **Accepts:** a budget the reviewer counts itself, and a review that reaches it leaves the rest unread, its doubts the
  person's or the switch's · a pickup check on conformance's model moves adversarial's head when `surfaces.py` exits 0 and
  no adversarial card was picked, as the head by rule does · a pickup whose check needs a mailbox role verifies in a
  counted round.
- **Rejected:** plan reviews on Sonnet — both of 0097's caught real defects · a commit between the reviews · the pickup
  verified in a full round · the release reading the frontmatter alone — a `fixed` blocker would pass.

- **D16** — "converge fixes this run's small cards and its drift in one more round." becomes "converge fixes this run's
  small cards and its drift, checked by one verify pass that is no round
  ([D71](#d71--the-cut-and-converge-read-what-changed))."
- **D40** — "answering in the cut's thread and writing no file." becomes "answering in the cut's thread and writing no
  file: the cut writes their answers to its notes."
- **D57** — "`diff.patch`, `bundle.md`, `models.toml`" becomes "`diff.patch`, `bundle.md`, `debt-cards.md`, `models.toml`";
  "the cutter's `cut.halt`" becomes "the cutter's `cut.halt` and `cut-notes.md`".
- **D64** — "and the living requirements the delta modifies or removes" becomes "and each requirement the delta modifies or
  removes, as a diff from the living spec".
- **D66** — "`debt_match.py` bundles the debt cards on the diff's files" becomes "`debt_match.py` writes the debt cards on
  the diff's files to `debt-cards.md`".
- **`docs/principles.md`, *Every edit opens a round*** — "**A fix is followed by a fresh verify pass, counted." becomes
  "**A fix is followed by a fresh verify pass, counted — a pickup's by one pass outside the cap."
- **`docs/principles.md`, *Checker*** — "a station that judges and edits nothing but its own findings file: conformance,
  adversarial." gains " A pickup check is one checker for both files."
- **`docs/principles.md`, *`fixed` is a claim*** — "The same station, on its verify pass, promotes it to `verified` or
  reopens it." becomes "The same station on its verify pass, or a pickup check, promotes it to `verified` or reopens it."
- **`THREAT_MODEL.md` `## Surfaces`** — after the `worker.md` line, "- `skills/mf-converge/references/verify.md` — how a
  checker promotes a fixed card, a security card's among them, and the pickup check." (`0095·S5`); the intro gains, after
  "is on it.", "A pickup's fix is checked by one worker, on adversarial's model when `surfaces.py` exits 1 over it or a
  picked card is adversarial's."

### D7

A decision is what `conduct.py`'s `_decisions` reads for a rescue's decided amend (F10): `design.md`'s `## Decisions`
section — its table's rows and each decision by its D-id — and its `## ` headings. The rest of `design.md` is prose, which
the fixer corrects when a `drift` card names it; a decision stays an amend, the person's or a rescue's. The settling reason
is the brief's T24: 0098 and 0100 each paid a round and a rescue for a `design.md` drift line the fixer could not touch.

- **`V` Step 6** — the fixer's bullet "**never edits the change's `tasks.md` or `design.md`**: a card whose fix needs one is
  `wontfix`, naming the amend the person commits by its path." becomes "**never edits the change's `tasks.md`, nor
  `design.md` save the prose a `drift` card names** outside its `## Decisions` section — never that section, a row of its
  table, a decision's D-id or a `## ` heading: a card whose fix needs one of those is `wontfix`, naming the amend the person
  commits by its path." The rest of the bullet stays.
- **`worker.md`'s *An amend card*** — "names the change's `tasks.md` or `design.md` by its path,
  `openspec/changes/<change-id>/design.md`. The fixer never edits those files, and converge halts on such a card." becomes
  "names the change's `tasks.md` or `design.md` by its path, `openspec/changes/<change-id>/design.md`, save a `drift` card's
  naming `design.md` prose outside its `## Decisions` section, which the fixer corrects. The fixer never edits `tasks.md`,
  nor that section, a row of its table, a decision's D-id or a `## ` heading, and converge halts on such a card."
- **D53** in `docs/decisions.md` — "The converge fixer edits no plan: a card whose fix needs one halts `amend needed`."
  becomes "The converge fixer edits no plan, save the `design.md` prose a `drift` card names outside its `## Decisions`
  section: a card whose fix needs any other plan edit halts `amend needed`."; its *Why* ends, after the D63 link's
  sentence, "The fixer corrects a design's prose: 0098 and 0100 each paid a round and a rescue for a drift line in it the
  fixer could not touch."

## Tests

The tests the change edits, all at the unit layer of `pytest`; no end-to-end test, so no engine runs (`T1`). Skill text is
held by review, per D42.

| file | before | after | counted by |
|---|---|---|---|
| `tests/test_bundle.py` | 3 | 3 | `grep -c "^def test_" tests/test_bundle.py`, once `0100-worker-diet` is merged |
| `tests/test_debt_match.py` | 2 | 2 | `grep -c "^def test_" tests/test_debt_match.py` |
| `tests/test_skills.py` | 21 | 21 | `grep -c "^def test_" tests/test_skills.py` |

- **Added:** none.
- **Edited:** `test_a_bundle_holds_what_the_change_cites` — the requirements section holds a fenced `diff` with
  `-A's text.` and `+New A.`, B's every line marked `-`, and no `C's text.` (D4);
  `test_debt_match_bundles_the_cards_on_the_diffs_files` — the cards file reads `# Debt cards on the diff's files`, then
  `_A` and `_X`; a second run writes the same; a stale file is replaced whole; no debt file gives `None.` (D4);
  `test_debt_match_refuses_what_it_cannot_read` — a link refused, a missing cards file written, a missing patch and an
  unreadable debt refused with the cards file as it stood (D4); `test_the_packets_hold_what_each_role_reads` — conformance's
  list gains `debt-cards.md` after `bundle.md`, and adversarial's holds `THREAT_MODEL.md` and `debt-cards.md` and no
  `bundle.md` (D4).
- **Removed:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[A review stops at its budget before reaching a defect]** → its doubts go to the person or the switch, and the build's
  Step 1, converge and the person's read still check the plan; 40 turns is ~60% of 0097's reviews.
- **[A second review misses a defect the fix made outside its diff]** → it judges the tasks the diff touches, and a fix
  that changes a decision already calls it.
- **[The pickup check on conformance's model misjudges an adversarial head]** → it runs there only when no adversarial card
  was picked and `surfaces.py` exits 0, the case adversarial's head by rule already takes.
- **[A diff hides a requirement's unchanged context a checker needs]** → three lines of context, and the delta holds the
  new requirement whole.
- **[A fixer's prose fix changes what a decision means]** → it edits nothing in `## Decisions`, and the verify pass judges
  the fix diff against the design as any other.
- **[A forged card line passes the release's `grep`]** → the checker writes the file, as before; *Out of scope* already
  accepts a worker steering through what it writes.

## Verdict

Settled: plan reviews, helpers and notes, the pickup check, the bundle, then the release and the record, each phase ending
on a green `make check`, the last on the gate.
