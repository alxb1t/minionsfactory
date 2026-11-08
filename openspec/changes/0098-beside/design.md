# Beside — design

A `## For the cut` head may name `beside:` ids; `conduct.py cut` queues them in an optional key, the cutter writes them into
the proposal's frontmatter, and nothing waits on them. The plan proposes `after:` only for real code need. The brief check
pays `0091·R3` and `0091·S3`. A script, conductor code, skill and decision text. Verdict at the end: ready to build.

## Context

Read at `ed7298f`, the brief's own sha and this cut's `HEAD`: every fact citing a path stands. `B` is
`skills/mf-plan/scripts/brief_check.py`, `C` is `skills/mf-ship/scripts/conduct.py`, `K` is `skills/mf-cut-change/SKILL.md`,
`P` is `skills/mf-plan/SKILL.md`, `TB` is `tests/test_brief_check.py`, `T` is `tests/test_conduct.py`, `F` is
`tests/fake_worker.py`. See [the proposal](proposal.md) for why.

- **F1. `after:` today.** The plan's head carries `· after:` (`P:191`), held by `head()` (`B:143-165`); the close pastes it into
  `conduct.py cut … [after=<ids>]` (`P:141-143`). `cut()` (`C:5750-5818`) takes `after` as an optional positional
  (`C:6311`), checks each id against the open versions and queued cuts, and writes the entry (`C:5801-5810`). `_cuts`
  (`C:5587-5605`) reads an entry lacking one of `CUT_KEYS` (`C:77`) as unreadable. `Run.cutting` formats
  `PROMPTS["cut"]` (`C:217-220`) with ` after=<ids>` (`C:4573-4576`); the cutter writes `after: [<ids>]` (`K:162`). At run
  time `_after` (`C:447-453`) reads `^after:` alone, and `stage_of` prints `waiting` for an unreleased id (`C:1227-1233`).
- **F2. The parallel-with check** warns of a file in common and suggests `after:` "when one needs the other's code"
  (`P:87`; `openspec/specs/sdd/spec.md:1025-1033`).
- **F3. The brief check's gaps.** `grammar()` (`B:257-284`) starts `column = 3`, so a `- models: ` or Acceptance line three
  spaces in passes before any head (`0091·R3`). `fold()` (`B:300-305`) keeps letters and digits, so `<h2>For the cut</h2>`
  folds to `h2forthecuth2` and `## Fоr the cut`, a Cyrillic `о`, keeps a letter `forthecut` lacks; `headings()`
  (`B:308-326`) halts neither (`0091·S3`). Probed at `HEAD`: both return `[]`.
- **F4. Already held.** `0088·S9`'s `   | · after: …` line halts in `grammar()`, and `0088·S10`'s ` ## For the cut` halts in
  `headings()`; `TB`'s `split` (`TB:404-416`) and `forms` (`TB:417-432`) steps hold both. Probed at `HEAD`: `grammar` names
  the `| ` line, `headings` names line 4. Their cards stay open only because 0091's `debt:` left them out (`0091·R2`).
- **F5. The tests.** `_version` (`T:56-67`) writes `after:` alone; `test_after_waits_for_its_dependency` (`T:838`) asserts
  `0002-marks · waiting`; `test_parallel_cuts_reserve_apart_and_start_one_run` (`T:2957`) calls `cut` directly with `None`
  for `after` (`T:2985`) and expects `expected after=<ids>` for a bare `0001-todo` (`T:3025`); `_queued` (`T:3277-3301`);
  `test_a_queued_cut_is_cut_then_built` (`T:3305`); `_cut` reads ` after=` from the prompt (`F:359-361`), and the fake
  release moves the change to `openspec/changes/archive/<id>/` on the default branch.
- **F6. Decisions.** D69 is the next free id (D67, D68 taken). D47's "a halt blocks only what names it in `after:`" and
  D44/D45's merge-in stay true as written.

## Goals / Non-Goals

**Goals:** the brief's Acceptance — `brief_check.py` accepts `· beside: <ids>` and refuses a `beside:` id that is not a slug;
`conduct.py cut b minor brief=b.md beside=a` writes an optional `beside` key, an entry without it still reads, and the
cutter's prompt carries it into `proposal.md` as `beside: [<id>]`; a `beside:` version is never `waiting`; the
parallel-with check proposes `after:` only for a symbol, decision or requirement the other adds; `grep -n "### D69"
docs/decisions.md` prints a line; `make gate` green.

**Non-Goals:** stacked builds; any run-time reader of `beside:` ([D4](#d4)); `conduct.py`'s own `_headed` fold.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `head()` takes one optional `beside:` part, each id held to `SLUG`, `none` allowed | E6; Acceptance | a required `beside:` — every old brief would halt |
| [D2](#d2) | `grammar()` takes a models or Acceptance line only under a head; `fold()` drops HTML heading tags and `headings()` reads a non-ASCII letter or digit as any one letter, with an ASCII letter left | E16; `0091·R3`, `0091·S3` | halting every heading with a non-ASCII character — the title's `·` would halt |
| [D3](#d3) | `cut` takes `after=` and `beside=` as trailing arguments in any order, each once; a `beside` id is a change id, never checked for existence; the entry gains `beside` only when given | E6 | a check that the id is open — a released one is still a true record · always writing the key — every existing entry assertion would change |
| [D4](#d4) | The cutter's prompt carries ` beside=<ids>`; `mf-cut-change` writes `beside: [<ids>]`; nothing reads it at run time | E2, E6 | a stage, an order or a merge driven by `beside:` |
| [D5](#d5) | `mf-plan`: the parallel-with row, the template's head, Step 6's check and command; `mf-ship`'s `cut` row | E7, E2 | `after:` as the default for overlap |
| [D6](#d6) | The record: D69 in the Planning group, quoted below | E2, E7 | amending D47 — its `after:` sentence stays true |

### D1

```
1. **slug** · minor · after: none · beside: 0097-cross-model · debt: none · decide: recommended
```

- **The part** — a head's ` · `-split part opening `beside:`; its value stripped of `[] \``, as `after:` is.
- **The halts**, after the slug, bump and `after` halts: two parts → ``item <n> — more than one beside:``; else each
  `,`-split entry, stripped of `` ` `` and spaces, that `SLUG` refuses → ``item <n> — not a beside id: `<entry>` ``.
  `none` halts nothing. No part halts nothing.
- **The early returns** in `head()` (no `after:`, more than one, `after: none`) no longer skip the `beside` halts.

### D2

- **`0091·R3`** — `grammar()` sets a local `seen_head = True` on its first head; a `- models: ` or `- **Acceptance:** ` line
  while it is false falls to ``## For the cut line <n>: outside the item grammar: `<line>` ``. Its continuation then halts
  the same way, as no Acceptance line was taken.
- **`0091·S3`, the fold** — `fold()` first drops each match of a new module constant
  `HEADING_TAG = re.compile(r"</?h[1-6][^>]*>", re.IGNORECASE)` — an `<h1>`…`<h6>` tag, opening or closing, with any
  attributes — then keeps letters and digits, case-folded. `<h2>For the cut</h2>` folds to `forthecut`.
- **`0091·S3`, the match** — a new `alike(line: str, heading: str) -> bool`, given both folds, is true when they have one
  length, hold at least one ASCII letter in `line`, and differ only where `line`'s character is not ASCII. `headings()` halts
  ``line <n> reads as `<heading>` but is not written so`` when a line is not the heading as written and `alike` holds for
  their folds. `## Fоr the cut` halts; `Результат` alone, as long as `decisions` and with no ASCII letter, does not.
- **`0088·S9`, `0088·S10`** — held at `HEAD` ([F4](#context)); this change lists them under `debt:` and adds no code for
  them.
- **The docstrings** — the module docstring of `B` names `beside` beside `after`; `head()`'s says its slug and each `after`
  and `beside` entry match `slug`; those of `grammar`, `fold` and `headings`, and the module's why line, cite
  `0098-beside design D1, D2`. In `C`, `_headed`'s docstring drops `, as `brief_check.py`'s `fold` reads one`, which
  `fold`'s tag drop and `alike` make untrue; `_headed`'s code stays.

### D3

| `conduct.py cut … <links>` | result |
|---|---|
| none | as today |
| `after=<ids>` | as today |
| `beside=<ids>` | each id fullmatches `CHANGE_ID`, else exit 2 `cut: cannot run — beside=<id> is not a change id` |
| both, either order | both, as above |
| a link opening neither, or a kind twice | exit 2 `cut: cannot run — expected after=<ids> or beside=<ids>: <link>` |

- **The parser** — `cutting`'s `after` positional (`C:6311`) becomes `links`, `nargs="*"`, metavar
  `[after=<ids>] [beside=<ids>]`; `main` passes `args.links`. `cut()`'s `after: str | None` becomes `links: list[str]`.
- **The order** — the link checks run where the `after=` prefix check runs today; the `beside` shape check before the queue
  lock, so a refusal reserves nothing.
- **The entry** — `"beside": <ids>` is added only when `beside=` is given. `CUT_KEYS` stays as it is, so an entry without
  it reads, and every entry already queued reads as naming none.
- **The usage line** (`C:11`) reads `conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] [beside=<id>[,<id>]]`;
  `cut()`'s why line cites `0098-beside design D3`.

### D4

- **The prompt** — `PROMPTS["cut"]` reads `` `{change} {bump} brief={brief}{after}{beside} unattended=yes` ``; `Run.cutting`
  fills `beside` with ` beside=<ids>` from `entry.get("beside")`, else `""`.
- **The cut skill** — `K`'s parameter table gains, after `after`:
  `` | `beside` | no | `beside=<id>[,<id>]` — the versions this one only shares files with; nothing waits on them | ``.
  Step 6 gains, after the `after` bullet: ``- A version cut with `beside` also lists them: `beside: [0047-x]`.``
- **No reader** — `_after` keeps its `^after:` pattern, so `stage_of`, `_dependencies`, integrate's `unready`, `I17` and
  release precondition 10 never see `beside:`. A test holds the stage ([Tests](#tests)).

### D5

- **`P:87`**, the row's how → `when the person names versions to run side by side: their briefs' `## Facts` paths and
  `## Phases` files compared; a pair touching a file in common is warned of, naming the file; `after:` is proposed only when
  one needs a symbol, decision or requirement the other adds, else `beside:`, the default (D69)`.
- **`P:132`** — "each item's slug, bump, `after` and models" → "each item's slug, bump, `after`, `beside` and models".
- **`P:141-142`** — the command gains ` [beside=<ids>]` after `[after=<ids>]`; "An `after` naming an earlier change" → "An
  `after` or `beside` naming an earlier change".
- **`P:191`** — the head gains ` · beside: <ids, or the slug of an earlier item>` after its `after:` part; the paragraph
  opening "`## For the cut` is filled when the frontier is empty" (`P:196-200`) gains, at its end: "`beside:` is optional:
  the versions this one only shares files with, which nothing waits on (D69)."
- **`skills/mf-ship/SKILL.md:57`**, the `cut` row — the command gains ` [beside=<id>[,<id>]]` after `[after=<id>[,<id>]]`, and
  "a brief or an `after` id it refuses" → "a brief, an `after` id or a `beside` id it refuses".

### D6

Added to `docs/decisions.md` after D65, and `, D69` after `D65` in the map's Planning list:

```markdown
### D69 · A version names what it builds beside

**A version that only shares files with another names it in `beside:` and builds in parallel from the default branch;
`after:` is kept for a symbol, decision or requirement the other adds, and holds the build until that one releases. The
plan's parallel-with check proposes which, `beside:` by default. `conduct.py cut` and the cut carry it into the proposal's
frontmatter, and nothing waits on it: integrate, and under the switch the supervisor, settle the overlap as they settle any
moved base.**

- **Why:** of 0081–0095's 14 `after:` links, 8 only avoided file overlap, each holding a build through the other's converge
  and release, while integrate already merges a moved base in.
- **Accepts:** an overlap settled at integrate — a supervisor's spend, or a person's halt — where `after:` would have waited.
- **Rejected:** `after:` for overlap — a wait the merge makes needless · a run-time reader of `beside:` — nothing it would
  order.
```

- **The spec** — [the delta](specs/sdd/spec.md); the release folds it.

## Evidence

What [D6](#d6)'s why rests on.

| measure | value | source |
|---|---|---|
| `after:` ids in the proposals of 0081–0095 | 14 | `git grep -n "^after:" HEAD -- openspec/changes/archive/`, the `proposal.md` lines of 0083 to 0095 |
| of them: file overlap only · real code need · borderline | 8 · 5 · 1 | the plan's read of each pair, recorded in its brief at `ed7298f` |

## Tests

`git grep -c '^def test_' HEAD -- tests/` sums to 278 at the cut; this change adds 1, so the build ends at 279. Each other
step extends the test that already reaches its state (`T2`): the unit layer for `brief_check.py` and `cut()`, the fake
worker for the cutter's prompt, the lowest layer that holds a cut's run (`T1`). No end-to-end test: the repo has no browser
layer, so no end-to-end run is added.

| test | gains |
|---|---|
| `test_a_hard_brief_is_ready_for_the_cut` | a step whose head carries ` · beside: [0097-cross-model, 0096-codex-ready]` after `after: none`, ready; a step adding a line `Результат` under the bold line, ready ([D2](#d2)'s ASCII-letter rule) |
| `test_a_brief_out_of_shape_halts` | `besides`: item 2's head `· beside: a;touch-q` and item 3's `· beside: none · beside: x`, each with a models line, halt [D1](#d1)'s `not a beside id` and `more than one beside:`; `headless`: `_READY` with its head line removed halts its models, Acceptance and continuation lines as outside the item grammar ([D2](#d2), `0091·R3`); `html`: `_READY` plus `\n## Notes\n<h2>For the cut</h2>\n## Fоr the cut\n`, a Cyrillic `о`, halts both lines as reading `## For the cut` ([D2](#d2), `0091·S3`) |
| `test_beside_waits_on_nothing` (new, `T`) | `0001-todo` and `0002-near`, its proposal `beside: [0001-todo]`, both open: `conduct.py status` prints exactly `0001-todo · build` and `0002-near · build` ([D4](#d4)) |
| `test_parallel_cuts_reserve_apart_and_start_one_run` (`T:2957`) | the direct `cut` calls pass `[]` for `links`; the bare `0001-todo` refusal (`T:3025`) expects `expected after=<ids> or beside=<ids>: 0001-todo`; new refusals: `beside=x` → `beside=x is not a change id`, and `after=0001-todo after=0001-todo` → `expected after=<ids> or beside=<ids>: after=0001-todo`; the `0006-d` step also passes `beside=0001-todo`, and its expected entry gains `"beside": ["0001-todo"]` ([D3](#d3)) |
| `test_a_queued_cut_is_cut_then_built` (`T:3305`) | after the `0005-p` step, `calls.unlink()` and a fresh `fake()`, so no `cut-packages` mode remains; then `0006-s` queued with `beside=("0005-p",)` is cut and released, and `main:openspec/changes/archive/0006-s/proposal.md` holds `beside: [0005-p]` ([D4](#d4)) |

`_version` (`T:56`) gains `beside: str = ""`, written as `beside: [<beside>]` after the `after:` line. `_queued` (`T:3277`)
gains `beside: tuple[str, ...] = ()`, written as the entry's `"beside"` list only when given, so every other queued entry
stays without the key and proves an old entry reads. `_cut` (`F:349`) reads an optional ` beside=(\S+)` after ` after=`
in the prompt and writes `beside: [<ids>]` into the proposal. No test is deleted or merged.

**Guards.** The `Результат` step and `test_beside_waits_on_nothing` hold behaviour the base already has — no non-ASCII line
reads as a heading without an ASCII letter, and `_after` reads `^after:` alone — so both are green before their code; every
other step goes red first.

## Dependencies

None.

## Risks / Trade-offs

- **An overlap marked `beside:` that is really a code need** → the dependent builds without the symbol and halts at its
  build or at integrate; the rescue, or the person, re-plans it as `after:`. The parallel-with check names the symbol test.
- **The heading match halts a prose line that spells a checked heading with a non-ASCII letter** → it fails closed and names
  the line; the plan fixes it.
- **Dropping HTML heading tags makes `<h3>Decisions</h3>` halt** → that is the form `0091·S3` asks to halt.
- **A `beside` id that names no version** → nothing reads it; it is a record, held to the change-id shape.

## Verdict

Ready to build.
