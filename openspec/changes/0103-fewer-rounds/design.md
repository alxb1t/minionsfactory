# Fewer rounds — design

Converge's extra rounds are cut at their causes: round 1's fix takes the pickup, a fixer records a decision's new build in a
fix note, `plan_check.py` and `make corpus` find blockers before a reviewer, and the Markdown readers read as CommonMark does.
Skill text, the plan check and the corpus runner, the conductor's readers and decision text. Verdict at the end: ready to build.

## Context

Read at `HEAD` `048246b`; the brief's sha is `ed7298f`. Since it, `skills/mf-converge/`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-plan/`, `skills/mf-ship/scripts/conduct.py` and `skills/mf-build/SKILL.md` moved (0098, 0100, 0101): every line
below is `048246b`'s. 0102-build-per-phase moves `conduct.py`, `brief_check.py`, `skills/mf-build/SKILL.md`,
`skills/mf-cut-change/SKILL.md` and `skills/mf-plan/SKILL.md` again before this build: the build finds each by its name.

`V` is `skills/mf-converge/SKILL.md`, `W` `skills/mf-converge/references/worker.md`, `C` `skills/mf-ship/scripts/conduct.py`,
`B` `skills/mf-plan/scripts/brief_check.py`, `M` `skills/mf-build/SKILL.md`, `K` `skills/mf-cut-change/SKILL.md`, `P`
`skills/mf-plan/SKILL.md`, `T` `tests/test_conduct.py`, `TB` `tests/test_brief_check.py`. See [the proposal](proposal.md) for
why.

- **F1. The pickup.** Step 8 runs once a run, after both files read clean, while a round remains: it picks every open small
  card and every open `drift` card, Step 6 fixes them, and one verify worker checks the fix, which is no round (`V:439-462`,
  `V:433`). Round 1's fix takes blocking cards alone (`V:360-361`). A pickup check is due while the latest `pickup` line
  names ids and no `checked` follows (`V:192-193`); the resume row for `pickup` is `V:204`. No script reads a `pickup` line:
  `git grep -n pickup` over `skills/*/scripts` and `scripts` prints nothing.
- **F2. A fixer that committed nothing.** It writes `fix` with `nothing committed` and the verify pass re-judges each
  `wontfix` (`V:386-388`); the pickup check counts it as `surfaces.py`'s exit 1 (`V:454-455`).
- **F3. The fixer's bound.** Never `tasks.md`, nor `design.md` save drift prose outside `## Decisions`; never that section, a
  row, a D-id or a `## ` heading (`V:375-379`); the amend card (`W:163-167`).
- **F4. The decision reading.** `_decisions` (`C:2494-2506`) returns every `## ` heading and the whole `## Decisions` body;
  `_amend` (`C:2509-2552`) calls a changed body a decision. No Dn split exists.
- **F5. The repeat.** "A repeat is a finding that describes a defect a debt card in `debt-cards.md` holds", graded up one level
  (`W:8-11`, `W:152`, `W:157`).
- **F6. The cut station's readers.** `_unapproved` (`C:708-727`) reads `design.md` with `_show(primary, change, …)`
  (`C:715`), a bare rev; `_check_cut` reads `_subject(primary, change)` (`C:697`); `_holds` reads `_show(primary, change, …)`
  (`C:541-545`). `_headed` (`C:5786`) and `_rows` (`C:5810`) split at `\n` and end a section at any line opening `#`; the
  backtick-fence helper beside them (`C:5771`) opens on any rest of the line, and this change deletes it. `brief_check.py`
  reads `_rows` for the brief's packages (`B:257`).
- **F7. The brief check.** `headed` (`B:74-87`) opens a section on any line starting `## `, fenced or not; `headings`
  (`B:355-374`) folds every line, fenced or not.
- **F8. Where the scripts are loaded.** In-process: `runpy.run_path` for `C` (`T:37`), `importlib` for `B` (`TB:18-26`), in
  pytest's venv. A script header's package is not in that venv: the suite imports `markdown_it` only from the dev group.
  `C` is also loaded by `runpy` in scripts whose header names no package: `skills/mf-ship/scripts/pin.py:46`, which
  `make install-skills` runs, and `tests/escape_drill.py:313`; so `C` must import nothing beyond the standard library at load.
- **F9. The build's close.** Step 3 simplify, Step 3.5 metrics, Step 3.6 `build.done` (`M:207-256`); its base is
  `git merge-base <default-branch> HEAD` (`M:232`). The task parsers to copy: `SUBTASK` (`skills/mf-cut-change/scripts/verify_check.py:30`),
  `subtasks()` (`:134`), `commands()` (`:149`), `tokens()` (`:176`), the argv runner `_spawn` (`:111-116`).
- **F10. The readers of run data.** `review_metrics.py` (findings files, status logs, run logs, Codex sessions; `--config`,
  `--repo`, `--out`, a missing config read as empty), `open_cards.py <findings> <out>`, `debt_match.py <debt> <patch> <cards>`
  (`skills/mf-review-metrics/scripts/review_metrics.py:163-207`, `:1710-1749`;
  `skills/mf-converge/scripts/open_cards.py:83-100`; `skills/mf-converge/scripts/debt_match.py:104-122`). No corpus exists.
- **F11. The plan review and the cut default.** "the host's subagent, on the session's model" (`K:219`); "the cut station's
  own is the strongest tier · high by default" (`P:198-199`).
- **F12. Decisions in force.** D2 lets a skill bundle "a standard-library script" (`docs/decisions.md:33-35`); D53 bounds the
  fixer (`:759-760`); D65 makes every plan review a fresh worker (`:183-186`); D71 checks a pickup by one worker
  (`:376`). Brief F1–F13 settle the change; C1–C4 are the cutter's readings of them.

## Goals / Non-Goals

**Goals:** the brief's Acceptance — a round 1 with one blocker and two non-blocking cards fixes all three in one pass, round 2
verifies them, and no pickup runs after; a pickup fix that commits nothing gets no pickup check; a mechanism repeat names
`repeat of <card>`; an appended fix note is no decision change to `conduct.py`, an edit of the entry's words still one;
`plan_check.py` fails on each problem it names and passes on this change; `make corpus` exits 0 over this repo's run
data; `brief_check.py` reads a `## For the cut` in an HTML heading, a homoglyph heading and a fenced block as CommonMark does,
and the fuzz corpus diff is empty; the plan review runs on Opus 5.5 · high and `mf-plan` suggests `cut claude-sonnet-5-5
high`; `make gate` green.

**Non-Goals:** a scenario-test check; coverage of removed tests beyond the base-test rule; widening the fixer's bound beyond
the fix note; `make corpus` in the gate or CI; a lockfile for a script header; a fake-host test of converge's prose
([C3](#c-rows)).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | Round 1, no catch-up, a blocker open: its fix pass takes Step 8's pick too, logged `pickup — <ids> · with the fix`; round 2 verifies all; Step 8 then finds pickup ran. A pickup whose fixer commits nothing gets no pickup check | F1, C2 | a pickup in every fix pass — a later round's fix is narrow by design · skipping the verify of a fix pass with a blocking `wontfix` — the verify round is the only check on a fixer that rejects a blocker |
| [D2](#d2) | A finding whose mechanism a debt card holds names `repeat of <id>`, its grade kept | F12 | grading a mechanism repeat up — it adds blockers, the rounds this change cuts |
| [D3](#d3) | The fixer may append `Fix note (<YYYY-MM-DD>, <card id>): <one line>` as a `### D<n>` entry's last line; `_decisions` drops each entry's closing run of notes; the close-out names each note | F2, F9 | a note anywhere in the entry — a decision could hide among notes · a note in the table row — the table is the decision |
| [D4](#d4) | `skills/mf-converge/scripts/plan_check.py`: ticked `Verify:` re-run, boxes, removed names, the base's tests; the build's close, the fixer and Step 7 run it; a line a fix pass was sent and left halts `amend needed` | F3, F7 | a model check — its checks need none · a halt at Step 7's first failure — a broken check is the fixer's to clear first, as a red gate is · sending a line back without end — a line only the plan can clear never clears |
| [D5](#d5) | `make corpus` runs `scripts/corpus.py` over `scripts/corpus.toml`'s cases; the cut marks `**CORPUS**`; the build runs it after a marked sub-task; the plan check finds the case | F4, F8 | in `make gate` — real data is the operator's and slow · fixtures of real data — they age, and hold personal paths |
| [D6](#d6) | `C`'s `_headed`, `_rows` and `B`'s `headed`, `headings` read `markdown-it-py` tokens; the backtick-fence helper is deleted; the cut path reads `refs/heads/<id>`; a deterministic fuzz corpus diffs the readings with the rendered page | F5, F10, C1 | patching each form — 0088's ten rounds did · the package as a project dependency — the runtime stays empty |
| [D7](#d7) | `K`'s plan reviews name Opus 5.5 · high; `P`'s default cut model is Sonnet 5.5 · high | F13 | the reviewer on the session's model — it would follow the cut onto Sonnet |
| [D8](#d8) | The record: a new decision; D2, D53, D65 and D71 edited; `CODING_STANDARDS.md`, `AGENTS.md` and the threat model | F1–F13 | leaving D2's "standard-library script" standing |

### C rows

The cutter's readings, each added to the brief's `## Decisions` under `decide: recommended`:

| id | reading | because |
|---|---|---|
| C1 | `markdown-it-py >=3,<4` also enters `pyproject.toml`'s dev group | the suite loads `B` and `C` in pytest's venv ([F8](#context)); the runtime's `dependencies = []` stays |
| C2 | Of F1's "a verify round is skipped when the fixer committed nothing", the pickup's check alone is skipped | a blocking `wontfix` that names no amend is judged only by its verify round; one that names an amend halts already |
| C3 | Phase 1's round behaviour is converge's prose, which the fake hosts do not run: its acceptance is held by the delta's scenarios and converge's review ([D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans)) | `conduct.py` launches converge as one station and runs no round (`C:62`, `V:433`) |
| C4 | A line the fixer leaves halts `amend needed — plan check: <subjects>`; `mf-rescue` amends what the plan check prints; 5.7 guards the lazy import | the plan reviews: a line only the plan can clear would loop Step 6 and 7; a quoted `Verify:` could put a card id in the halt (`C:2439`); `pin.py` loads `C` with no package |

### D1

- **Step 6** (`V:357-362`): "It clears every **open blocking** finding across both files — in a pickup, exactly the cards
  Step 8 names —" → "It clears every **open blocking** finding across both files, and in a round-1 pickup the cards Step 8
  would pick — in a pickup, exactly the cards Step 8 names —".
- **The round-1 pickup** — a new paragraph after Step 6's dispatch paragraph: "**The round-1 pickup.** In round 1 of a run
  that is no catch-up run, with a blocking card open, pick by Step 8 items 2 and 3 before you dispatch: print the ids and
  write `pickup` with `<ids> · with the fix`. Send them with the blocking cards. Round 2's verify round judges them all, and
  Step 8 finds pickup ran."
- **Nothing committed** (`V:386-388`) — appended: "In a pickup Step 8 sent, run no pickup check: write `pickup` with
  `checked — nothing committed`, and go to Step 8 item 6." A round-1 pickup's pass is no such pickup: it goes on as above.
- **Step 8** — item 1's "Pickup already ran" → "Pickup already ran, a round-1 pickup's included"; item 5's "a fixer that
  committed nothing runs no `surfaces.py`, as in Step 7, and counts as exit 1" → "a fixer that committed nothing runs no
  check, as Step 6 says".
- **The due rule** (`V:192`) — "names ids and no `checked` line follows it" → "names ids, does not end `with the fix`, and no
  `checked` line follows it".
- **The resume row** (`V:204`) — "`checked` → Step 8 item 6; else Step 8 item 4, the same ids" → "`checked` → Step 8 item 6;
  `with the fix` → Step 6, the blocking cards and those ids; else Step 8 item 4, the same ids".
- **The events row** (`V:95`) — "Step 8" → "Step 8, and Step 6's round-1 pickup"; its detail gains "`· with the fix` for a
  round-1 pickup".
- **The diagram** (`V:21`) — `┌───────────── not clean ────────────────┤ both clean` →
  `┌──── not clean · round 1: + pickup ─────┤ both clean`, the same width.
- **Blocking `wontfix`** — Step 6's nothing-committed rule for a pass with blocking cards stays as it is (C2).

### D2

- **`W:8-11`** — after "…a debt card in `debt-cards.md` holds." add: "A finding whose mechanism a card holds in another form —
  the same code misreading the same kind of input — names `repeat of <id>` too, and keeps its grade: its **Priority** says it
  repeats that card's mechanism."
- **`W:152`** — "a repeat says `repeat of <id>` and that it went up one level" → "a repeat says `repeat of <id>` and that it
  went up one level, a mechanism repeat that it kept its grade".
- **`W:157`** — "`repeat of <id>` for a repeat" → "`repeat of <id>` for a repeat or a mechanism repeat".

### D3

- **The note** — `Fix note (<YYYY-MM-DD>, <card id>): <one line>`, the last line of a `### D<n>` entry in `design.md`'s
  `## Decisions`, after a blank line; several cards' notes stand one under another. It records how the code now implements the
  decision; the decision's own words stand.
- **`V`'s fixer bullet** (`V:375-379`) — "never that section, a row of its table, a decision's D-id or a `## ` heading" →
  "never another line of that section, a row of its table, a decision's D-id or a `## ` heading, save a **fix note**: when
  its fix changes how the code implements a decision whose words still hold, it may append
  `Fix note (<YYYY-MM-DD>, <card id>): <one line>` as the last line of that `### D<n>` entry".
- **`V`'s Step 10** — its sentences gain, after "each blocking finding's end state, by id;": "each fix note the run's fixers
  appended, by its D-id and card, for the person to read;".
- **`W`'s amend card** (`W:163-167`) — "save a `drift` card's naming `design.md` prose outside its `## Decisions` section,
  which the fixer corrects" → "save a `drift` card's naming `design.md` prose outside its `## Decisions` section, which the
  fixer corrects, and a card whose fix a fix note records".
- **`C`** — a new `FIX_NOTE = re.compile(r"Fix note \(\d{4}-\d{2}-\d{2}, [RS]\d+\): \S.*")`. `_decisions` splits the
  section's body at each line opening `### `, and drops from each part that opens `### D<digits>` its closing run of blank
  lines — a line of `\r` alone counts as blank — and lines that `FIX_NOTE.fullmatch` once a closing `\r` is stripped; every
  other part, the headings and the rest stay. So a note added or edited at an
  entry's end changes nothing, and a note followed by any other line is kept and compared. `_amend`'s docstring names it. Why
  lines cite `0103-fewer-rounds design D3`.

### D4

`skills/mf-converge/scripts/plan_check.py`, a `uv` script, `dependencies = []`:

```
plan_check.py --change <id> --base <rev>
  merge base = git merge-base <rev> HEAD          reads the working tree, so it runs before or after a commit
  1 ticked Verify     each ticked N.M's commands, argv, no shell, cwd the root, 600 s each
  2 boxes             each N.M unticked under a ticked ## Progress phase
  3 removed names     each removed name still named in openspec/specs/ or the change directory
  4 the base's tests  each def test_ name at the merge base gone from tests/
  5 corpus            each **CORPUS** `<case>` missing from scripts/corpus.toml        (phase 4)
exit 0 "plan: clean" · 1 one "plan: …" line per problem · 2 cannot read tasks.md, the base or git
```

- **The tasks** — `openspec/changes/<id>/tasks.md` from disk. `## Progress` lines `- [x] N — …`; sub-tasks by `SUBTASK` and
  `subtasks()`, copied from `verify_check.py` with `commands()` and `tokens()`, the commands those read in a `Verify:`.
- **Check 1** — a ticked sub-task's commands run in order. A command exits 0 to pass; a search — `grep`, or `git grep` — also
  passes on exit 1 with no output when its `Verify:` says `prints nothing` or `` prints `0` ``. Not run: a `**HALT CHECK**`
  sub-task, a sub-task of a `**HUMAN` phase, and a command naming `plan_check.py`. A failure prints
  `plan: <N.M> — `<command>` exited <code>`, then at most 5 lines of its output, each `  | <line>`; a timeout reads `timed out`.
  A span `tokens()` cannot split exits 2.
- **Check 2** — `plan: <N.M> — unticked under the ticked phase <N>`.
- **Check 3** — removed names: from `git diff --unified=0 --no-renames <merge base> -- '*.py'`, each `-` line's `def <name>`
  or `class <name>`, indented or not, and each unindented `<UPPER_NAME> =` or `<UPPER_NAME>:`; and the base name of each file
  `git diff --name-only --diff-filter=D --no-renames <merge base>` prints. A name is removed when
  `git grep --untracked -q -w -F <name> -- . ':(exclude)openspec'` exits 1. For each, `git grep --untracked -n -w -F <name> --
  openspec/specs openspec/changes/<id>` hits outside `tasks.md` and outside `design.md`'s `## Tests` section, on a line holding no
  word of removal — `(?i)delet|remov|renam|retir|drop|replac`, `→`, `REMOVED`, `**Reason**` or `**Migration**` — each print
  `plan: <path>:<line> names <name>, which the diff removes`.
- **Check 4** — `def test_` names, indented or not, `async` or not, under `tests/` at the merge base
  (`git grep -h -E <pattern> <merge base> -- tests/`) and in the tree (`git grep --untracked -h -E <pattern> -- tests/`); each
  base name gone, unless `design.md`'s `## Tests` section names it as a word, prints `plan: <name> is gone since the base`.
- **The build** — `M`'s Step 3.6 opens: "Before writing it, run `uv run --script ../mf-converge/scripts/plan_check.py
  --change <change-id> --base <default-branch>`, resolved as in Step 1. Exit 1 → **halt**, `stop: plan check`, copying what it
  prints, and write no `build.done`; exit 2, or `uv` missing → **halt**, naming it." Under 0102 the close worker runs it.
- **The fixer** — a new bullet in `V`'s Step 6 after the gate-weakening one: "runs `plan_check.py --change <change-id> --base
  <base>` after its gate and before its commit; each line it prints is a blocking card of this pass: fix it, or set it
  `wontfix` naming the amend, as for a card".
- **The fixer's bound** — a line it cannot clear without editing `tasks.md` or `design.md` it leaves, listing it in its report
  under `plan check left:`, as it names an amend card's amend.
- **Step 7** — after `gate_check.py`: "Then run `plan_check.py` as the fixer does. Exit 1 → back to Step 6 with its lines as
  the cards to clear, dispatching no verify worker and counting no round; but when a line it prints is one the last fixer
  listed under `plan check left:`, or one Step 7 already sent back → **halt** `amend needed — plan check: <subjects>`; exit 2,
  or `uv` missing → **halt**, naming it." `<subjects>` is each such line's subject alone — its sub-task id, its `path:line`, or
  its test name — joined by `, `, never the command it quotes, so `conduct.py`'s id read (`C:2439`, `C:2466`) finds no card
  a quoted `Verify:` holds, and the rescue may amend, as at any `amend needed`.
- **The rescue** — `skills/mf-rescue/SKILL.md`'s Step 2 table gains a row above converge's `amend needed` row:
  "| converge's `amend needed — plan check` | fix | each line `plan_check.py --change <change-id> --base <default-branch>`
  prints, cleared in `tasks.md` and `design.md`'s prose: a `Verify:` the task's own result passes, a stale claim of a removed
  name dropped |"; the trailer sentence below it gains "; a plan-check halt's names `Rescue: plan check`".
- **Recursion** — a `Verify:` that runs `plan_check.py` itself is never re-run, so 7.7's check on this change ends.

### D5

- **`scripts/corpus.py`**, a `uv` script, `dependencies = []`: `corpus.py [--cases <toml>] [--minions <dir>]`, defaults
  `scripts/corpus.toml` and the run directory (`git rev-parse --path-format=absolute --git-common-dir`, its parent's
  `.minions`). The primary checkout is the run directory's parent.
- **A case** — `[[case]]` with `name` (`[a-z0-9-]+`), `reads` (prose), `argv` (a non-empty list of strings) and optional `each`
  (a list of globs under the run directory, none absolute or holding `..`). Placeholders: `{minions}`, `{primary}`, `{input}`
  (each match), `{out}` (a fresh `<minions>/corpus/<name>/<n>/`). A case with no match prints `corpus: <name> · no input`.
- **A run** — argv, no shell, cwd the repository root, 300 s. Each non-zero exit or timeout prints
  `corpus: <name> · <input, or once> · exit <code>` and at most 5 lines of its stderr, `  | <line>`; each case ends
  `corpus: <name> · <k> runs · pass` when none failed. Exit 1 on any failure; 2 on a cases file that does not parse or breaks
  the schema, naming it, or a run directory or `corpus/` that is a link.
- **`scripts/corpus.toml`** — its cases:

| name | each | argv after `uv run --script` |
|---|---|---|
| `review-metrics` | — | `skills/mf-review-metrics/scripts/review_metrics.py --config {out}/none.toml --repo {primary} --out {out}/review-metrics.html` |
| `open-cards` | `changes/*/conformance.md`, `changes/*/adversarial.md` | `skills/mf-converge/scripts/open_cards.py {input} {out}/open.md` |
| `debt-match` | `changes/*/diff.patch` | `skills/mf-converge/scripts/debt_match.py {minions}/debt.md {input} {out}/debt-cards.md` |

- **`Makefile`** — `.PHONY` gains `corpus`, and a `corpus` target after `check`, outside `gate` and `check` (tasks 4.3).
- **`K`'s Step 6** — a bullet: "A sub-task that adds or alters code reading the run directory (`.minions/`), run logs or Codex
  sessions, in a repo whose root `Makefile` has a `corpus` target, carries `` **CORPUS** `<case>` ``, `<case>` a case of
  `scripts/corpus.toml` it or an earlier sub-task adds. `plan_check.py` fails a marked sub-task whose case is missing."
- **`M`'s Step 2 item 2** — after "Never change code to make it pass.": "A `**CORPUS**` sub-task: once its check passes, run
  `make corpus`; any other exit than 0 is a **halt**, naming the case and what it printed."
- **`plan_check.py`** — check 5: a ticked or unticked sub-task whose text holds `` **CORPUS** `<case>` `` and whose case
  `tomllib` does not find as a `name` in `scripts/corpus.toml` prints `plan: <N.M> — no case <case> in scripts/corpus.toml`.
- **This change** — `scripts/corpus.py` is the corpus's runner, not a reader: no sub-task here carries the mark. Task 4.6
  runs `make corpus` once as a `**HALT CHECK**`, so the plan check never runs it again at the close or in a fix loop.

### D6

- **The parser** — `MarkdownIt("commonmark").enable("table")`; each of `B`'s and `C`'s headers reads
  `# dependencies = ["markdown-it-py>=3,<4"]`. `B` imports it at the top. `C` imports it inside a new `_markdown()`, cached
  with `functools.cache`, which `_headed` and `_rows` call: loading `C` stays standard-library, as `pin.py` and the escape
  drill need ([F8](#context)). `uv add --dev "markdown-it-py>=3,<4"` puts it in the dev group and `uv.lock` (C1).
- **A boundary** — a heading token of level one or two, ATX or setext, or an `html_block` whose content opens `<h1` or `<h2`.
  A line inside a `fence` or `code_block` token is never a boundary, a heading or a checked line.
- **`C`'s `_headed(text, heading)`** — True when exactly one heading token is an ATX `h2` whose source line is `heading` as
  written, and no other heading token, `html_block` line or line holding an inline `<h1>`…`<h6>` folds, as today, to
  `heading`'s letters. An unclosed fence makes the rest code, so a heading inside it is none and `_headed` is False.
- **`C`'s `_rows(text, heading)`** — no such heading → `[]`; the section's top-level blocks, from the heading to the next
  boundary: one paragraph `None.` → `[]`; exactly one `table` → its rows, header first, each cell's inline content stripped of
  spaces and backticks, as GFM renders them; anything else, an empty section included → None. Source lines split at
  `\r\n`, `\r` or `\n`, as CommonMark's.
- **The deletion** — `C:5771`'s backtick-fence helper is deleted, its callers replaced by the token walk.
- **`refs/heads/<id>`** — `_unapproved` reads `_show(primary, f"refs/heads/{change}", …)`, `_check_cut` reads
  `_subject(primary, f"refs/heads/{change}")`, `_holds` reads `_show(primary, f"refs/heads/{change}", …)`, and `_tag_of`, which
  `_holds` calls, reads `_subject(primary, f"refs/heads/{change}")` (`0091·S4`). `_dependencies` (`C:548-551`) is off the cut
  path and keeps its bare rev.
- **`B`'s `headed(brief)`** — a section per boundary, keyed by its source line as written, holding the source lines to the next
  boundary. `sections` and `main` read it unchanged.
- **`B`'s `headings(brief)`** — the checked lines are each source line of a heading token, of an `html_block`, or of a paragraph
  whose inline children hold an `html_inline` opening `<h1>`…`<h6>`. A checked line that is an ATX `h2` written as a
  `HEADINGS` entry counts it, a second time halting `line <n>: a second `<heading>``; any other checked line whose fold is
  `alike` halts `line <n> reads as `<heading>` but is not written so`.
- **A lone CR** — `B` halts `line <n>: a carriage return not before a newline` per such line, and parses the brief with each
  such `\r` read as a space, so token lines and `brief.split("\n")` agree.
- **The fuzz corpus** — `tests/test_markdown_corpus.py`, its documents every combination of a prefix, a heading form, a body
  and a line ending, for `## Dependencies` and `## For the cut`; prefixes: none, `` ```x` ``, a closed backtick fence, a
  tilde fence holding the heading, `<h2>` of the heading, a homoglyph heading, an indented code line, a blockquote heading,
  `#- note`; heading forms: ATX, one space in, a closing `##`, setext `---`, a tab; bodies: `None.`, an approved table, a table
  with a `#- note` row, a table then an open fence; line endings: `\n`, `\r\n`, `\r`. The oracle renders each with the same
  `MarkdownIt` and reads it with `html.parser.HTMLParser`: each `<h2>`'s text and the table rows before the next `<h1>` or
  `<h2>`. A document **agrees** when `C`'s reading fails closed (`_headed` False, or `_rows` None) or `_rows` equals the
  oracle's rows under the `<h2>` reading `Dependencies`; and when `B` halts — `headings` returns a line, or the document
  holds a carriage return not before a newline — or the ATX sections `headed` keys equal the oracle's `<h2>` texts folding to
  a checked heading. A document is no brief, so the test calls `C`'s and `B`'s functions, never `main`. It asserts the list of
  documents that disagree is empty.
- **`CODING_STANDARDS.md`** — "`dependencies = []`" → "`dependencies = []`, save the CommonMark parser `markdown-it-py>=3,<4`
  in the scripts that read Markdown, `brief_check.py` and `conduct.py`" (phase 7).

### D7

- **`K:219`** — "the host's subagent, on the session's model." → "the host's subagent, on Opus 5.5 · high where the host
  offers it, whatever the session's model — on Claude Code the Agent tool's `model: opus` and `effort: high` — else the
  session's model." The review table's reviewer cells keep "a fresh worker" (`tests/test_skills.py:694`).
- **`P:198-199`** — "the cut station's own is the strongest tier · high by default" → "the cut station's own is Sonnet 5.5 ·
  high by default, where the session offers it, else the strongest tier · high: the plan holds the judgment, and the cut's
  plan reviews run on Opus 5.5 · high whatever the cut runs on".

### D8

The decision, added to `docs/decisions.md`'s *The check loop and the release* group, its id one above the highest at the
build's `HEAD`, and named in the map's list for that group:

```markdown
### D<n> · Converge's rounds are cut at their causes

**Round 1's fix pass takes the pickup with its blockers, and a pickup fix that commits nothing gets no check. The fixer
records how the code now builds a decision in a `Fix note` closing its entry, which the run reads as no decision change.
`plan_check.py` re-runs each ticked `Verify:` and finds unticked boxes, removed names the plan still claims and the base's
tests gone, at the build's close and after each fix. `make corpus` runs the readers of run data over the repo's own, outside
the gate. The Markdown readers parse with `markdown-it-py`. Plan reviews run on Opus 5.5 · high; the cut's default model is
Sonnet 5.5 · high.**

- **Why:** across 0080–0100, most rounds past the first were a pickup alone or grew from one, an amend round over plan prose
  a fix left stale, or a blocker a deterministic check could have found.
- **Accepts:** a fix note the person reads after the run · a corpus that reads only what this machine's run directory holds ·
  a header range `uv` resolves at run time.
- **Rejected:** a pickup in every fix pass · grading a mechanism repeat up · `make corpus` in the gate · a hand-split reader
  patched form by form.
```

- **D2** — "A skill may bundle a standard-library script" → "A skill may bundle a standard-library script, or one whose PEP
  723 header names a package the person approved".
- **D53** — "The converge fixer edits no plan, save the `design.md` prose a `drift` card names outside its `## Decisions`
  section" → "The converge fixer edits no plan, save the `design.md` prose a `drift` card names outside its `## Decisions`
  section and a `Fix note` closing a decision's entry, which the run reads as no decision change".
- **D65** — "Every plan review is a fresh worker" → "Every plan review is a fresh worker on Opus 5.5 · high".
- **D71** — "Once no blocker is open, a pickup's fix is checked by one verify worker at medium, which is no round." →
  "Round 1's fix pass takes the pickup with its blockers; once no blocker is open, a pickup's fix is checked by one verify
  worker at medium, which is no round."
- **`AGENTS.md`** — after "**`make check`** runs its fast steps, no `slow` test, between build phases.": "**`make corpus`**
  runs the readers of run data over this checkout's run directory and Codex sessions; no gate runs it."
- **`THREAT_MODEL.md`'s *Entry points*** — the findings-files bullet gains: "A design's `Fix note` lines, which the converge
  fixer appends and the run reads as no decision change: a note can misstate the code, and the verify round and the person
  read it." A new bullet: "`tasks.md`'s `Verify:` commands, which `plan_check.py` runs again at the build's close and after
  each converge fix, argv with no shell, as the build ran them; and `make corpus`, an operator target outside the gate, which
  runs the readers over the run directory and the operator's Codex sessions and writes only under `.minions/corpus/`."
- **The spec** — [the delta](specs/sdd/spec.md); the release folds it.

## Evidence

What [D8](#d8)'s why and [the Tests](#tests) rest on.

| measure | value | source |
|---|---|---|
| rounds past the first, 0080–0100 (0099 out) | 64: pickup 20 · re-verified blocker 18 · amend 16 · wrong fix 5 · catch-up 5 | the brief's *Facts*, classified from the status logs, findings and amend commits |
| amend rounds that were drift | about 11 of 16; 16 of 19 amend commits touched a Dn entry | the same |
| blockers a deterministic check could find | about 25 of 44, up to 31 | the same |
| `def test_` lines in `tests/` at the cut | 287 | `git grep -c "^def test_" HEAD -- tests/`, its counts summed |
| of them in `tests/test_conduct.py` · `tests/test_brief_check.py` | 145 · 3 | the same command |

## Tests

`tests/test_plan_check.py`, `tests/test_corpus.py` and `tests/test_markdown_corpus.py` are new: no test reaches a new script
or the readers' agreement. Every other step extends a test that reaches its state (`T2`), at the unit layer (`T1`). No
end-to-end test: the repo has no browser layer. Phase 1 adds none ([C3](#c-rows)).

| test | gains |
|---|---|
| `test_a_rescue_decides_under_the_switch` (`T`) | after its `_decisions` steps: `## Decisions\n\n### D1\n\nRead the branch.\n\n## Tests\n` and the same with `\nFix note (2026-11-08, R2): reads refs/heads.\n` after its words read equal through `_decisions`, CRLF too; the note with `Read the branch` → `Read the tag` reads unequal; a note followed by a line of words reads unequal; and an amend without the switch that appends a note, through `_amend`, is `(sha, "", False)` ([D3](#d3)) |
| `test_a_plan_check_finds_what_the_plan_left` (new, `tests/test_plan_check.py`) | a repo under `tmp_path` with a change directory and a merge base: a ticked `Verify:` exiting 1 → exit 1 naming it; a `prints nothing` search exiting 1 → passes; a `**HALT CHECK**`, a `**HUMAN` phase's and a `plan_check.py` command are not run; a command past a lowered timeout reads `timed out`; an unticked box under a ticked phase; a removed `def _gone` named in `openspec/specs/` → exit 1, on a line saying it is removed → passes, in `tasks.md` → passes; a removed file's base name; a base test gone → exit 1, named in `## Tests` → passes; a clean plan → `plan: clean` ([D4](#d4)); a `**CORPUS**` case missing and present ([D5](#d5)) |
| `test_what_the_plan_check_cannot_read_exits_2` (new, `tests/test_plan_check.py`) | no `tasks.md`; a `--base` naming no commit; a span `tokens()` cannot split ([D4](#d4)) |
| `test_the_corpus_runs_each_case` (new, `tests/test_corpus.py`) | a run directory under `tmp_path`, cases running `sys.executable -c` readers: a pass per input, `no input`, a reader exiting 1 → exit 1 naming the case and input, a timeout, `{out}` under `corpus/`; a run with no `--minions` from a repo under `tmp_path` finds its run directory from git ([D5](#d5)) |
| `test_a_corpus_it_cannot_read_exits_2` (new, `tests/test_corpus.py`) | a cases file that does not parse, a case with no `argv`, an `each` holding `..`, a run directory that is a link ([D5](#d5)) |
| `test_the_markdown_readers_agree_with_the_rendered_page` (new, `tests/test_markdown_corpus.py`) | the fuzz corpus of [D6](#d6): the disagreeing list is empty; carries `slow` only when it runs over 5 s |
| `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`T`, its `_unapproved` cases, `T:3602-3619`) | the CRLF case reads `UNAPPROVED: evil 1`, as GFM renders it; new cases `` ```x` `` above the table and lone `\r` line ends, each `UNAPPROVED: evil 1`, and a `#- note` line before the `evil` row, whose halt opens `UNAPPROVED: ` and names `evil 1` (`0091·R4`, `0091·S5`); after the `cut-packages` halt, a tag `0020-p` at the default branch's tip leaves `_unapproved(root, "0020-p", [])` reading the branch's `right-pad ^2`, and the tag is deleted after that assertion (`0091·S4`) ([D6](#d6)) |
| `test_a_brief_out_of_shape_halts` (`TB`) | the forms step (`TB:448-463`) prints the four `reads as` lines alone: ` ## For the cut` now ends the section, as CommonMark reads it; a step with a fenced `## For the cut` between the `## Decisions` table and `## Dependencies` exits 0, ready; a step with `note\rmore` before `## Decisions` halts `line 7: a carriage return not before a newline` alone ([D6](#d6)) |

Every line of `plan_check.py` and `corpus.py` is reached by these steps, as the gate's diff coverage needs.

**Guards.** `plan_check.py`'s recursion guard is held by the `plan_check.py` step of the new test, its twin the same step run
with the guard removed in the commit body (`W5`, `T6`). Task 5.7's check guards `C`'s lazy import: it holds before 5.4 and
must hold after, so a simplify that moves the import to the top turns it red at the close; its twin is the same command exiting
1 with a top-level `import markdown_it`, in the commit body. No test is deleted or merged.

## Dependencies

| package | constraint | why |
|---|---|---|
| markdown-it-py | >=3,<4 | the CommonMark parser for `brief_check.py` and the cut station's checks (brief F5, F10) |

## Risks / Trade-offs

- **A re-run `Verify:` is slow** → each runs once at the close and once per fix pass, with no model; 600 s bounds each.
- **A removed name the plan names on purpose** → a line saying so carries a word of removal; `tasks.md` and `## Tests` are out.
- **A fix note misstates the code** → the verify round reads the fix and the note, and the close-out names the note.
- **`markdown-it-py` resolves a new release in range** → `uv run --script` resolves within `>=3,<4`; a lockfile waits for a break.
- **The corpus reads only this machine's data** → it proves the readers on what exists; a reader of a new file adds a case.
- **0102 moves the files first** → the build finds each section by its name, and halts on a contradiction.

## Verdict

Ready to build.
