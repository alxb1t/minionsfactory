# Cut halts — design

The plan approves each package in the brief, the queue holds that approval, the station checks the cut against it, a cut
halt names its answer, and the brief check reads `## For the cut` by a strict grammar. Conductor code, a script, skill and
decision text. Verdict at the end: ready to build.

## Context

Read at `bb4cf51`, the brief's own sha and this cut's `HEAD`: every fact citing a path stands. `C` is
`skills/mf-ship/scripts/conduct.py`, `B` is `skills/mf-plan/scripts/brief_check.py`, `K` is `skills/mf-cut-change/SKILL.md`,
`P` is `skills/mf-plan/SKILL.md`, `T` is `tests/test_conduct.py`, `F` is `tests/fake_worker.py`. This change builds
`after: [0088-paydown-2, 0090-supervisor-merge]`; 0090 builds after 0089. `B` and `tests/test_brief_check.py` are read as 0088
leaves them (`git show 0088-paydown-2:<path>`), cited by symbol, and the build re-reads every line by symbol. See
[the proposal](proposal.md) for why.

- **F1. The cut's dependency rule.** Unattended, "a `## Dependencies` that is not `None.`" is always a halt (`K:42-43`), Step
  9's wait row is a halt (`K:224-228`), and *Never* forbids the commit (`K:396`); Step 6 writes the section, `None.` when empty
  (`K:163-164`). The build approves a package only as the cut commit lists it (`skills/mf-build/SKILL.md:286-291`). D38
  (`docs/decisions.md:125-134`); the spec's `:254-261`, `:404-423` and `:2865-2885`.
- **F2. The queue.** `cut` (`C:4613-4678`) writes the entry `{bump, brief, after, executor, model, effort, halt}`
  (`C:4662-4671`) to `_queue(primary)/cuts/<id>`, where no worker writes (`C:4533-4538`). `_cuts` reads an entry lacking one
  of `CUT_KEYS` (`C:70`) as unreadable (`C:4580-4581`). `rejoin` clears a queued cut's halt under the queue lock (`C:4720-4736`).
- **F3. The station.** `cutting` (`C:3643-3696`) runs `_check_cut` (`C:595-618`), which returns the cutter's `cut.halt` line
  first, read through no link (`C:600-609`), then the commit, folder, tree and models checks. A failure goes to `cut_halted`
  (`C:3698-3707`), which writes the halt into the entry and logs `cut-halted — <why>`; `cut_halts` logs each halted entry at a
  run's start (`C:3750-3754`). A branch that holds its change is checked, not cut again (`C:3661`). 0088 rewrites the
  kept-worktree line (its D2); 0090 records the brief in `briefs/<id>` at the pass (its D1).
- **F4. The answers.** `_needs` gives a cut halt `a fix` (`C:2990-3002`); `status` prints `<id> · cut-halted — <halt>`
  (`C:4935-4941`); `report` prints each halt line raw (`C:5065-5070`). `mf-ship`'s `cut-halted` row
  (`skills/mf-ship/SKILL.md:96`) and D58 (`docs/decisions.md:136-149`) answer a plan's halt with a re-plan and
  `conduct.py rejoin <id>`; 0088's row adds that a kept worktree is no plan's.
- **F5. The brief check.** 0088's `B` reads `## For the cut` with `items`, `fields`, `head` and `models`, holds a checked line's
  whitespace to spaces and tabs with `whitespace`, and keys each `## ` heading with its `isspace()` runs collapsed in
  `sections`. 0088's D5 leaves review R10 (a zero-width character in a head or heading), security S7 (a `| ` line split off
  as an item) and S8 (a *For the cut* heading in another Markdown form), and `0083·S3`, to this version. `B` loads `C` with
  `runpy` for `SLUG`. `tests/test_brief_check.py`'s `_READY` holds no `## Dependencies`.
- **F6. The plan.** Helpers (`P:62-64`); the checks (`P:71-82`); the rounds (`P:99-103`); the close (`P:121-136`); the template
  (`P:154-181`), with no `## Dependencies`.
- **F7. The hand cut.** Step 1 counts `.minions/cuts/` reservations and halts "not free" (`K:78-82`); a standing reservation
  is a queued or cut-halted version.
- **F8. 0082·S5.** The cutter has an edit rule for the whole brief (`C:2449`), while `THREAT_MODEL.md:49-50` says it writes
  two lines back; `THREAT_MODEL.md:67-69` is the cut-queue bullet.
- **F9. The tests.** `_queued` (`T:2743-2765`); `test_parallel_cuts_reserve_apart_and_start_one_run` asserts the entry whole
  (`T:2484-2493`) and its claimed-run `0006-d` entry (`T:2547-2558`); `test_a_queued_cut_is_cut_then_built`
  (`T:2769-2832`); `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`T:2836-3102`), its doubt line at `T:2851-2870`, its
  later steps using `0008-s` to `0018-v`; `_cut` writes no `design.md` (`F:258-282`).
- **F10. The principle.** *A new dependency halts for a person* says a package is "approved at the cut", held by
  `mf-cut-change` Step 9 (`docs/principles.md:200-208`).

## Goals / Non-Goals

**Goals:** the brief's Acceptance — `brief_check.py` halts on a hard brief with no `## Dependencies` and passes one reading
`None.`; it halts on a `## For the cut` heading or item in another Markdown form or holding a format character; with the
fake worker, a queued cut whose `design.md` lists only the approved packages passes, and one listing another is
`cut-halted` naming it; a cut-halted version's closing line names its brief and `conduct.py rejoin`; `make gate` green.

**Non-Goals:** notifications (`ui · control`); comparing constraints for looseness ([D4](#d4)); the rest of `0082·S5`'s reach
([D8](#d8)).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A hard brief's `## Dependencies`, between `## Decisions` and `## Phases`: `None.`, or rows `item · package · constraint · why`, `item` the `## For the cut` slug | W1, W3 | a nested line under the item, which the grammar refuses |
| [D2](#d2) | `brief_check.py` reads `## For the cut` by a line grammar, holds checked lines to `isprintable()`, and allows one form of each checked heading | Z1, W9 | another per-form fold |
| [D3](#d3) | `conduct.py` reads the table with `_rows`; `cut` copies the item's rows into the entry's `dependencies`; a `rejoin` keeps them and takes a row they lack only with `--yes <hash>` of the new rows — the person's decision on S1, option (a) | W2; C2; S1 | the brief read at cut time · a rejoin copying the brief's rows unconditionally · copying only after a plan-answered halt · the disk-fix route as an accepted risk |
| [D4](#d4) | The station halts a cut whose `design.md` lists a row outside the entry's, as written | W2, W4; C1 | a looseness comparison |
| [D5](#d5) | A halt the plan answers ends `· needs <id> its brief answered (…), then conduct.py rejoin <id>`; `_needs` reads it | W5; C3 | the answer on every cut halt |
| [D6](#d6) | The cut skill: unattended, a row the brief lists commits and any other halts; a hand cut halts on a queued id | W4, W6 | the cutter reading the queue |
| [D7](#d7) | `mf-plan`: the packages fact and round, the template's section, the close's rows, background helpers | W3, W10 | — |
| [D8](#d8) | The record: D62; D38 and D58 amended; the dependency principle; `mf-ship`'s row; `THREAT_MODEL.md` (`0082·S5`) | W4, W8 | — |

### D1

```markdown
## Dependencies
| item | package | constraint | why |
|---|---|---|---|
| first-call | livekit-client | ^2.5.0 | the browser's audio |
```

- **Required** in a hard brief, between `## Decisions` and `## Phases`; `None.` when the version adds no package.
- **`item`** is the slug of a `## For the cut` item — `conduct.py cut` is given the slug, never the item's number.
- **A row is the person's approval**, asked in a round ([D7](#d7)). A section of its own, not a nested line under the
  item: [D2](#d2)'s grammar refuses any line it does not name.

### D2

`B`'s rules over `## For the cut`, each halt under `brief: halt — `:

```
1. **slug** · minor · after: none · debt: none · decide: recommended   head: `<n>. ` + text, column 0
   - models: build a b · converge a b · release a b · cut a b          `- models: `, at the head's text column
   - **Acceptance:** `make gate` passes; Verify:                        `- **Acceptance:** `, the same column
     `grep -n x f` prints a line                                         continuation: 2+ further, right after
                                                                         blank: spaces alone
Cut 2026-11-07 as 0001-slug at 1a2b3c4.                                 the cut's line
```

- **The grammar.** Each line of `## For the cut`, split at `\n` alone, is a blank line, a head (`(\d+)\. \S` at column 0), a
  `- models: ` or `- **Acceptance:** ` line indented three spaces, as the template writes it, or `len("<n>. ")` spaces, a
  continuation (at least two spaces past its Acceptance line's indent, then text) directly after an Acceptance line or a
  continuation, or `Cut \d{4}-\d{2}-\d{2} as \d+-[a-z0-9-]+ at [0-9a-f]{7,40}\.`.
  Any other line halts ``## For the cut line <n>: outside the item grammar: `<line>` ``. S7's `   | · after: …`, a lazy
  line, a `*` or `- ` item and R10's zero-width-led head each halt here.
- **The fields.** `fields` reads each head from its own line with `head`, and each models line with `models`; their halts
  stand (`not a slug`, `not a bump`, `not an after id`, `no after:`, `more than one after:`, `no models line`,
  `more than one models line`, the models shape). `TOP`, `NESTED` and `MODELS_LINE` go; `items`, which `halts` reads for the
  commands, stays as 0088 leaves it, `MARKER` with it.
- **The printable rule.** A line of `## Decisions`, `## Dependencies` or `## For the cut` holding a character for which
  `str.isprintable()` is false — a tab, NBSP, U+3000, `\x0b`, `\x0c`, U+200B, U+2060 — halts
  `<section> line <n>: a character isprintable() refuses`. It replaces `whitespace`.
- **The heading rule.** For each of `## Decisions`, `## Dependencies` and `## For the cut`, a brief line that equals it once
  every character but `str.isalnum()` ones is dropped and both are case-folded, and is not it as written, halts
  ``line <n> reads as `<heading>` but is not written so``; a second line written so halts ``line <n>: a second `<heading>` ``.
  `<n>` counts the brief's lines from 1. S8's forms and R10's `## For the cut` + U+200B halt here, and a setext
  `For the cut` halts on its text line. `sections` keys a heading by its line as written.
- **The section.** No `## Dependencies` key in `sections` → `no ## Dependencies section`. `_rows` ([D3](#d3)), loaded from
  `C` with `SLUG`, returning None, or a first row other than `item · package · constraint · why`, halts
  `## Dependencies is neither None. nor a table of item · package · constraint · why`. Each body row `<n>`, from 1, whose
  item is no head's slug halts ``## Dependencies row <n> — not an item of ## For the cut: `<item>` ``; one with an empty
  package or constraint halts `## Dependencies row <n> — no package or constraint`.
- **The order.** The depth, `At` and empty halts; the heading rule, in line order; the section's halts; the printable rule,
  `## Decisions`, `## Dependencies`, then `## For the cut`, each in line order; the grammar, in line order; `fields`; then the
  commands, as now.
- **The docstring** names the grammar, and its why line ends `0091-cut-halts design D2`.

### D3

Module functions beside `_cuts`, with `DEPENDENCIES = "## Dependencies"` and `APPROVED = ["item", "package", "constraint",
"why"]`:

```python
def _rows(text: str, heading: str) -> list[list[str]] | None:
    """Return the table under `heading`, its header first, each cell stripped of spaces and backticks.

    Lines split at `\n` alone, as `brief_check.py` splits them. A line inside a fence — from a line opening ``` or
    ~~~ to the next — is never the heading, so a quoted example is not read. Blank lines are skipped. No such heading,
    or a section reading `None.` alone, is []. A section with no other line, one holding a line that is no
    `|`-bounded row, with no delimiter row second, or with a row whose cell count differs from the header's, is None.
    The section runs from the first line equal to `heading` to the next line opening `#`.
    e.g. "## D\n| a | b |\n|---|---|\n| `x` | y |\n" → [["a", "b"], ["x", "y"]]
    """


def _approved(text: str, slug: str) -> list[list[str]] | None:
    """Return `[package, constraint]` per `## Dependencies` row whose item is `slug`; None for a section out of shape."""
```

- **One read.** `_approval(path: Path, slug: str, command: str) -> list[list[str]]` reads the brief and returns
  `_approved(text, slug)`. One `except (OSError, UnicodeDecodeError)` raises
  `Stop(2, f"{command}: cannot run — the brief {path} cannot be read")`; None raises `Stop(2, f"{command}: cannot run — the brief's ## Dependencies is neither None.
  nor a table of item · package · constraint · why")`.
- **`cut`**, after `_brief_refused` and before the lock, takes `_approval(path.resolve(), slug, "cut")`, so a refusal reserves
  nothing. The entry gains `"dependencies": <the list>`. A brief with no section copies `[]`.
- **`rejoin`** of a queued cut, under the lock, takes `_approval(Path(entry["brief"]), <the id's slug>, "rejoin")`; a refusal
  stops 2 with the entry kept. The slug is `CHANGE_ID.fullmatch(change)[2]`. `queued` is `entry.get("dependencies", [])`, and
  `new` each brief row not in `queued`, in the brief's order:
  - **No `new` row** → it writes `{**entry, "halt": None}`: the queued rows stand, one the brief dropped included, and
    `--yes` is not read.
  - **A `new` row** → it writes `{**entry, "halt": None, "dependencies": queued + new}` only when `--yes` equals
    `_rows_hash(new)`, `hashlib.sha256(json.dumps(new).encode()).hexdigest()`. Without it, or with another hash, it stops 1,
    the entry and its halt kept and nothing requested:
    `rejoin: halted — the brief adds rows the queue does not hold: <package> <constraint>, …; the person's yes: conduct.py rejoin <id> --yes <hash>`,
    every new row in order and the hash written out.
  - **`--yes` on any other rejoin** — no id, or one naming no queued cut — stops 2:
    `rejoin: cannot run — --yes answers a queued cut's packages`.
  - **The parser** gives `rejoin` an optional `--yes`, metavar `hash`; the module docstring's usage line reads
    `conduct.py rejoin [<change-id>] [--yes <hash>]`, and `rejoin`'s docstring says the queued rows are kept and a new one
    taken only with the hash.
- **`mf-ship`'s rows**: the `rejoin` command row of `skills/mf-ship/SKILL.md` gains "`rejoin <change-id>` naming a queued cut
  keeps its queued packages; a brief row the queue does not hold exits 1 naming each row and
  `conduct.py rejoin <change-id> --yes <hash>`, the person's yes to those rows, which queues them; `--yes` on any other
  rejoin exits 2"; the `cut-halted` row reads as [D5](#d5) quotes it.
- **`CUT_KEYS` stands**: an entry queued before this change reads `entry.get("dependencies", [])`, so it approves nothing.
- **C2, the person's decision on S1 (2026-11-07), option (a).** A rejoin keeps the queue entry's already-queued rows, and
  takes a row it does not already hold only when given `--yes <hash>` of the new rows set, as `/mf-ship approve-gate` records
  the person's yes to an exact diff's hash; without it, a rejoin whose brief adds or widens a row halts naming the rows and
  the exact `conduct.py rejoin <id> --yes <hash>` command. A worker cannot forge the hash: the person runs the command. Why:
  security S1 — a rejoin after a disk fix, with no re-plan, as `mf-ship`'s `cut-halted` row prescribes, would otherwise queue
  a row a prompt-injected cutter planted in the brief, so the cutter's first answer, a rejoin copying the rows again
  unconditionally, goes. Rejected: copying only on a rejoin after a plan-answered halt; recording the disk-fix route as an
  accepted risk ([D8](#d8)).

### D4

`_unapproved(primary, change, approved) -> str | None` reads `_show(primary, change, "openspec/changes/<id>/design.md")`:

| `design.md`'s `## Dependencies` | returns |
|---|---|
| no file, no section, or `None.` | None |
| `_rows` None, or a header not opening `package · constraint` | `design.md's ## Dependencies is neither None. nor a table of package · constraint · why` |
| a row whose `[package, constraint]` is not in `approved` | `design.md adds what the brief did not approve: <package> <constraint>, …`, every such row, in order |
| else | None |

- **In `cutting`**, `why = _check_cut(...)`, then, when it is None, `why = _unapproved(primary, change,
  entry.get("dependencies", []))`; the check line and the halt read it as any check's. The brief is never read here.
- **C1, decided by the cutter.** A constraint is approved as written: `^2` is not `^2.0` nor `>=2,<3`. Judging which is looser
  needs each ecosystem's version grammar — a dependency — so any other constraint halts, looser or tighter.
- **A missing section adds nothing**: the build approves only what the cut commit's section lists, so no package gets in.

### D5

```python
def _cut_answer(change: str, brief: str) -> str:
    """Return the action a cut halt the plan answers needs.

    e.g. "0001-a", "/b.md" → "its brief answered (/mf-plan 0001-a depth=hard brief=/b.md from=/b.md),
    then conduct.py rejoin 0001-a". Why: 0091-cut-halts design D5.
    """
```

- **The halts it ends.** The cutter's own line — `_check_cut`'s return equal to `_cutter_halt(primary, change)`, its
  `cut.halt` read, factored out of `_check_cut` unchanged — and `_unapproved`'s `adds what the brief did not approve` line.
  `cutting` appends ` · needs <id> <_cut_answer(id, entry["brief"])>`, so the entry's halt, the logged `cut-halted —` line,
  `status`, `report` and `cut_halts` carry it with no edit of their own.
- **`_needs`**, before `on_disk`: a change whose queue entry holds a `str` halt and a `str` brief, the halt ending with
  `_cut_answer(change, entry["brief"])`, returns that action. A queued cut halted in the run with its entry's halt `None` —
  a probe's halt — and an unreadable entry, which holds no brief, fall through to `a fix`. The closing line then reads
  ` · needs 0001-a its brief answered (…), then conduct.py rejoin 0001-a`.
- **C3, decided by the cutter.** Every other cut halt keeps its line and `a fix`: a check on disk, the prose-section halt, a
  kept worktree — whose line 0088 makes name its own remedy, "no plan's" — a worker's exit, and `after <id> is cut-halted`,
  answered by that id's.
- **`mf-ship`'s `cut-halted` row** gains: "A line ending `· needs <change-id> its brief answered (…), then conduct.py rejoin
  <change-id>` names the command: a cutter's doubt, or a package the queued rows do not approve. A package is answered in
  the re-plan — its row approved in `## Dependencies`, then `conduct.py rejoin <change-id>`, which halts naming the row and
  `conduct.py rejoin <change-id> --yes <hash>`; the person runs that, the row is queued and the branch checked — or
  dropped, the branch and its worktree removed before the rejoin." The clause from "then `conduct.py rejoin`" is the
  person's decision on S1 ([D3](#d3)'s C2), built in phase 6.

### D6

`K`'s edits, before → after:

- **Unattended** (`K:42-43`): "a `## Dependencies` that is not `None.`," → "a `## Dependencies` row the brief's
  `## Dependencies` does not list for this change, package and constraint as written,"; a bullet after it: "- **A package the
  brief lists** — commits without a halt. The brief stays evidence: the run compares the committed rows with the copy it
  queued, never with the brief (D62)."
- **Step 1**, a bullet before "`change-id` is free": "- by hand, `.minions/cuts/<change-id>` does not stand; it stands →
  halt with `<change-id> is queued for the cut station: answer it in the brief, then conduct.py rejoin <change-id>`;"
- **Step 6** (`K:163-164`): "Each dependency names an exact package and a version constraint." → "Else a table
  `| package | constraint | why |`, a row per package, each an exact package name and a version constraint; unattended,
  each row one the brief's `## Dependencies` lists for this change's slug, as written."
- **Step 9** (`K:228`): "each waiting row is a halt." → "each waiting row is a halt, save a `## Dependencies` whose every row
  the brief lists for this change, which commits."
- **Never** (`K:396`): "before the human's OK." → "before the human's OK; unattended, before the brief's `## Dependencies`
  lists each row for this change, as written."

The cutter cannot read the home queue, so it halts by the brief's rows, which the queue copied; a planted row passes the
cutter and halts at [D4](#d4).

### D7

`P`'s edits:

- **The template** gains `## Dependencies` with D1's header row and delimiter between `## Decisions` and `## Phases`, and a
  paragraph after the template's: "`## Dependencies` is required in a hard brief: `None.`, or a row per package the person
  approved — `item` its `## For the cut` slug, the exact package, its version constraint, and why. `conduct.py cut` copies the
  item's rows into its queue entry, and the run halts a cut that adds any other. `brief_check.py` reads `## For the cut` by
  its grammar: a head at the line's start, its `- models:` and `- **Acceptance:**` lines under the head's text, the
  Acceptance's continuation two spaces further in, blanks, and the cut's `Cut` line."
- **Step 3** gains the row `| packages | each package the phases would add, by exact name and version constraint, read from
  the target's manifests at <ref> |`.
- **Step 4** gains the bullet "- A package is the person's: ask each in a round, `❓ Qn` approve `<package> <constraint>`?, and
  write each approved one as a `## Dependencies` row."
- **Step 6**: item 2's "it holds the commands and each item's slug, bump, `after` and models" → "it holds the commands, each
  item's slug, bump, `after` and models, `## For the cut`'s grammar and the `## Dependencies` table"; item 3's "its `models:`
  line and Acceptance included," → "its `models:` line and Acceptance included, each `## Dependencies` row,".
- **Step 2's Helpers** gains: "- **In the background.** Where the host runs helpers in the background, dispatch the
  fact-finding and Step 3's checks there and return to the chat at once: `gathering the facts`. When they report, write
  `## Facts` and post Round 1; a re-measure between rounds runs in the background too. The rounds, the answers and the
  brief's writes stay in this thread."

### D8

- **D62**, after D59, its id added to the map's Planning list (`docs/decisions.md:13`) after D59:

> ### D62 · A queued cut's packages are approved at the plan
>
> **A hard brief's `## Dependencies` holds a row per package the person approved in a round — item, package, constraint,
> why — or `None.`. `conduct.py cut` copies the item's rows into its home-queue entry, and a rejoin of a queued cut keeps
> them, taking a row they lack only with the person's `--yes <hash>` of the new rows; the cut station halts a cut whose `design.md` lists a package or constraint outside them, and never reads the
> brief for approval. A cut halt the plan answers names the brief and `conduct.py rejoin`; a hand cut halts on an id the
> queue holds.**
>
> - **Why:** a queued cut halted on packages approved in chat, where no station reads, its halt naming no answer, and the
>   planning thread then cut the queued id by hand.
> - **Rejected:** approval read from the brief at cut time, which the cutter can edit · a rejoin copying the brief's rows
>   again unconditionally, which takes a row a cutter planted after a disk fix (the person's decision on `0091·S1`) · a
>   nested line under the item · judging a looser constraint, which needs each ecosystem's version grammar.

- **D38**: "an unattended cut halts there instead ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station))." → "an
  unattended cut halts there instead ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)), save a `## Dependencies`
  whose rows its brief approves, which it commits and the run checks against its queued copy
  ([D62](#d62--a-queued-cuts-packages-are-approved-at-the-plan))."
- **D58**: "answered by a re-plan and `conduct.py rejoin <id>`." → "its line naming the answer: a re-plan and
  `conduct.py rejoin <id>`, which keeps the queued packages and takes a new one only with the person's `--yes <hash>`
  ([D62](#d62--a-queued-cuts-packages-are-approved-at-the-plan))."
- **The person's decision on S1** amends D62 and D58 as quoted above, after phase 5 landed their first text: phase 6
  rewrites "and a rejoin of a queued cut copies them again" in D62, adds its rejected clause, and rewrites "which copies the
  brief's approved packages again" in D58.
- **`THREAT_MODEL.md`**, *Entry points*: the brief bullet (`:49-50`) gains, after "rows back": ", through an edit rule for the
  whole file. No package's approval is read from the brief after the person's act: `conduct.py cut` copies the item's
  `## Dependencies` rows into the home queue, a `rejoin` keeps the queued rows and takes a row they lack only with
  `--yes <hash>` of the new rows, a command the person runs, and the station compares the committed `design.md` with that
  copy ([D62](docs/decisions.md#d62--a-queued-cuts-packages-are-approved-at-the-plan)). A switch or a decision row
  a cutter plants reaches a later cut only through the person's re-plan, whose close shows each `## For the cut` item and
  `## Dependencies` row before the yes (`0082·S5`)." The cut-queue bullet's "which names the brief a cutter writes," → "which
  names the brief a cutter writes and holds the packages its cut may add," and "so no worker names that brief." → "so no
  worker names that brief or widens that list." The rejoin clause, "a `rejoin` keeps … a command the person runs", is the
  person's decision on S1 ([D3](#d3)'s C2); phase 6 writes it in place of phase 5's "and a `rejoin` after a re-plan, copy".
- **`docs/principles.md`**, *A new dependency halts for a person*: "approved at the cut." → "approved by a person: at the
  cut, or for a queued cut at the plan, the run checking it against the queued rows
  ([D62](decisions.md#d62--a-queued-cuts-packages-are-approved-at-the-plan))."; its *Held by* gains, after "`mf-cut-change`
  Step 9;", "`conduct.py`'s cut check, held by
  `tests/test_conduct.py::test_a_cut_halt_is_shown_and_rejoin_cuts_again`;". The principle's force stands: a person approves
  every package.
- **The spec** — [the delta](specs/sdd/spec.md); the release folds it.

## Tests

`git grep -c '^def test_' HEAD -- tests/` sums to 241 at the cut; 0088 adds 2, 0089 6 and 0090 3, so the build starts from 252.
This change adds and removes none: each step extends the test that already reaches its state (`T2`), at the unit layer for
`brief_check.py` and through the fake worker for the station, the lowest that holds a cut's run (`T1`). No end-to-end test:
the repo has no browser layer.

| test | gains |
|---|---|
| `test_a_hard_brief_is_ready_for_the_cut` | `_READY` holds `## Dependencies\n\nNone.\n` after `## Decisions`; a step with a table row `\| 0083-plan-queues \| left-pad \| 1.3.0 \| a pad \|` is ready |
| `test_a_brief_out_of_shape_halts` | each step's expected lines follow [D2](#d2): in 1.2, `_OUT_OF_SHAPE` adds `no ## Dependencies section` and the section steps below go in; in 1.3, every other existing step — `heads`, `shapes`, `tabbed`, `unblank`, `hidden`, `second_list`, `spaced_heading`, `markers`, `spaced`, `twice` and any 0088 leaves beside them — expects the grammar, printable and heading halts; new steps: a prose `## Dependencies`, an empty one (its heading straight before the next), a table with no delimiter row, a row with a cell too many, a row naming no item and a row with an empty constraint; R10's U+200B-led head and `## For the cut` + U+200B heading; S7's `   \| · after: a;touch-q` under a head and after a models line; S8's ` ## For the cut`, `##\tFor the cut`, `## For the cut ##` and setext `For the cut` over `---`; and a second `## For the cut` |
| `test_what_cannot_be_checked_exits_2` | its `odd` and `unclosed` briefs write their `Verify:` as a continuation of `_READY`'s Acceptance, five spaces in, so the grammar passes them and the span parse still exits 2 |
| `test_parallel_cuts_reserve_apart_and_start_one_run` (`T:2439`) | the expected `entry` holds `"dependencies": []`; the claimed-run step's `alone` brief (`T:2549-2558`) holds a `## Dependencies` table with `d`'s rows `left-pad 1.3.0` and `right-pad ^2` and an `other` row, and `0006-d`'s expected entry gains `"dependencies": [["left-pad", "1.3.0"], ["right-pad", "^2"]]`; then a brief in a folder of its own whose `## Dependencies` is prose, queued with `refused`, exits 2 with D3's line and leaves `.minions/cuts/` as it was |
| `test_a_queued_cut_is_cut_then_built` (`T:2769`) | `0005-p`, queued approving `left-pad 1.3.0` and `right-pad ^2`, mode `cut-packages`: `check — cut · pass`, released |
| `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`T:2836`) | phase 2, right after the loop of checks (`T:2936-2950`), before the crash step: the loop gains `("0021-q", "cut-prose", <D4's prose line>)`; then `0020-p`, its own brief `packages.md` reading `# brief\n`, approving `left-pad 1.3.0` alone, mode `cut-packages`, halts `design.md adds what the brief did not approve: right-pad ^2`; a rejoin with `packages.md` removed, then holding a prose `## Dependencies`, exits 2 with D3's lines, the halt kept; `packages.md` then holds a `p` table of both rows: `rejoin 0020-p`, and then with a hash of 64 `0`s, exits 1 with D3's halt naming `right-pad ^2` and `conduct.py rejoin 0020-p --yes <hash>`, the entry's rows and halt kept; `rejoin 0020-p --yes <that hash>` queues `left-pad 1.3.0` then `right-pad ^2`, and a `rejoin` with `--yes` and no id exits 2 with D3's line; the next run checks the branch, passes and releases it; the later steps then find `0021-q` halted beside `0004-e` to `0007-x`, as they find those. Phase 4: the doubt and `right-pad` lines end D5's answer, `status` and `report` with them; the first run's last line holds ` · needs 0001-a its brief answered (/mf-plan 0001-a depth=hard brief=<brief> from=<brief>), then conduct.py rejoin 0001-a, 0002-b a fix`; the `0021-q` line holds no answer |

`_queued` (`T:2743`) gains `dependencies: tuple[tuple[str, str], ...] = ()`, written as the entry's `"dependencies"` lists. `_cut`
(`F:258`) gains mode `cut-packages`, committing `openspec/changes/<id>/design.md` that opens with a fenced example of
D1's brief table under its own `## Dependencies` line, so `_rows`' fence rule is run, then the section with rows `left-pad 1.3.0`
and `right-pad ^2` under `| package | constraint | why |` and its delimiter row `|---|---|---|`, and mode `cut-prose`, its
section `left-pad, any version`. These steps
cover every line the change adds, as the gate's diff coverage requires: `_rows`' cases run through `B`'s steps, and
`_approval`'s read error through the rejoin with `packages.md` removed. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **The grammar refuses a brief a person wrote another way** → each halt names the line, and the template is the grammar;
  the plan fixes the line, as Step 6 says.
- **The printable rule refuses a tab in a decision row** → it names the line; a tab there was already a form the old rules
  folded one at a time.
- **The heading rule refuses a prose line that reads `Decisions` alone** → it fails closed and names the line.
- **The rejoin reads a brief the cutter could have edited** → it keeps the queued rows and takes a row they lack only with
  the person's `--yes <hash>` of the new rows, which its halt names after showing each; a disk-fix rejoin with no re-plan
  queues nothing new. The person's decision on S1, option (a) ([D3](#d3)'s C2, [D8](#d8)).
- **A package halt on a branch that holds its change** is checked again, not cut again → the `mf-ship` row says to remove the
  branch for a package the person drops.
- **The merge with 0088, 0089 and 0090** meets `B`, `cutting`, `_needs`, the `mf-ship` row and `THREAT_MODEL.md` through their
  own lines, which this change edits after they merge in, per `after:`.

## Verdict

Ready to build.
