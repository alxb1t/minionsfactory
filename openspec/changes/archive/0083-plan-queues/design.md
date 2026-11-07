# Plan queues — design

A bundled `brief_check.py` holds a hard brief to the shape the cut station needs; `mf-plan`'s hard close names the models
and the switch, runs it, asks once, and queues each change with [`0082-cut-station`](#context)'s `conduct.py cut`. Verdict at
the end: ready to build.

## Context

The brief's `At` sha is `f349aa8` (v0.66.0). `git diff --name-only f349aa8..HEAD --no-renames` prints the 0081-cut-awake
release's files; none of the facts this change reads sits on them, save `docs/decisions.md` and `tests/test_skills.py`, both
read again at HEAD `95dcad0`, their lines given below. This change builds `after: [0082-cut-station]`, whose design adds
`conduct.py cut` and D58 (`git show 0082-cut-station:openspec/changes/0082-cut-station/design.md`, D1 and D9).

- **F1. The plan never cuts:** its role line (`skills/mf-plan/SKILL.md:8-10`) and *Never* (`:152-157`); Step 6 closes on
  `Next: /mf-cut-change <id> <bump> brief=<path>` (`:108-119`); the brief's `## For the cut` is one free line (`:148-149`).
  Its parameters are `what`, `brief`, `depth` and `from` (`:23-28`).
- **F2. The shell rules:** `skills/mf-cut-change/scripts/verify_check.py` holds `SPAN` (`:31`), `commands` (`:149-173`),
  which skips a span after an output verb, `tokens` (`:176-183`), `masked` (`:186-204`) and `breaks` (`:207-224`), which
  names `$(…)`, a backtick, a shell variable, a loop and `cd`; `Unparsed` (`:87-88`) is its parse error.
- **F3. A bundled script reads another's:** `conduct.py` loads `integrate.py` with `runpy.run_path`
  (`skills/mf-ship/scripts/conduct.py:58`, `:2607`).
- **F4. Bundled scripts are named:** `_METRICS_SCRIPTS` (`tests/test_skills.py:466-480`) lists each skill's script, and
  `test_the_metrics_script_scan_reports_a_missing_script` (`:508-547`) expects one `not named` line per entry, in its order.
- **F5. The decisions:** *Planning* holds D5…D10 and D38 (`docs/decisions.md:63-132`), its ids in the diagram's Planning
  list (`:13`); `0082-cut-station` adds D58 there.
- **F6. A brief's Acceptance** is prose with spans: `0083-plan-queues`'s own names `` `$(…)` `` as a word, with no space, so a
  span is a command only when it holds a space.

## Goals / Non-Goals

**Goals:** a hard close that queues on one yes and returns to the chat; a brief the cutter rarely doubts.

**Non-Goals:** the cut station (`0082-cut-station`); a light close queuing anything; the cut re-running `brief_check.py`; the
roadmap row (P10).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `skills/mf-plan/scripts/brief_check.py <brief>`: the hard title, the `At` line, a filled `## For the cut`, plain Acceptance and `Verify:` commands, through `verify_check.py`'s own functions, and each item's head and models line | P11 | a copy of the shell rules; running the commands |
| [D2](#d2) | `## For the cut` names per change its slug, bump, `after`, `debt:`, `decide: recommended`, Acceptance and the models of the build, converge, release and cut station | P8, P18 | the models as a cut's suggestion; an `AGENTS.md` switch |
| [D3](#d3) | The hard close: `brief_check.py` to green, then "confirm, and queue it?" — yes or `then=ship` runs `conduct.py cut` per change in order; no ends on one `Next: /mf-cut-change` line per change | P4, P9, P19 | a cut in the person's session; a second question per change |
| [D4](#d4) | The role line and *Never* say the plan queues on a yes and never cuts; D59 records the close; `_METRICS_SCRIPTS` names both scripts | P4, P9 | — |

### D1

`skills/mf-plan/scripts/brief_check.py`, a `uv` script with standard-library imports alone: `brief_check.py <brief>`, by
`argparse`. `VERIFY_CHECK = Path(__file__).resolve().parents[2] / "mf-cut-change" / "scripts" / "verify_check.py"`, a module
constant read in `main()`, after the brief is read, and loaded there once per run with `runpy.run_path` (F3), its `SPAN`, `commands`, `tokens`, `masked`, `breaks` and `Unparsed` used as they stand.
`CONDUCT = Path(__file__).resolve().parents[2] / "mf-ship" / "scripts" / "conduct.py"` is loaded the same way, for its `SLUG`. It runs
no command it reads. Exits: 0 ready · 1 halt · 2 cannot check.

Each check prints its line, `brief: halt — …`, and the script goes on to the next:

| check | holds when | its line |
|---|---|---|
| depth | the first `# ` line's ` · `-parts hold `hard` | `brief: halt — the title says light: /mf-plan <what> depth=hard from=<brief>`, `<what>` and `<brief>` kept literal; or `brief: halt — the title names no depth` |
| `At` | a line fully matches `At ([0-9a-f]{7,40}), (\d{4}-\d{2}-\d{2})\.` | `brief: halt — no At <sha>, <YYYY-MM-DD>. line` |
| `## For the cut` | the section stands and holds a line that is not blank | `brief: halt — ## For the cut is empty` |
| commands | each command of each item in `## Decisions` and `## For the cut` has no break | `brief: halt — <the heading, with its ##>: I19 — <breaks, joined by " · ">: `<command>``, e.g. ``brief: halt — ## Decisions: I19 — `$(…)`: `grep -c $(cat f) x` `` |
| item head | each `<n>. ` item's slug and `after` entries match `conduct.py`'s `SLUG`, its bump is `minor` or `patch`, and it names `after:` | ``brief: halt — ## For the cut: item <n> — not a slug: `<slug>` ``; likewise `not a bump`, `not an after id` and `no after:` |
| models | each item's `- models:` line names the build, converge, release and cut station in order, each `<model> <effort>` of plain words | `brief: halt — ## For the cut: item <n> — the models line is not build · converge · release · cut, each <model> <effort>`; likewise `not a model or effort` and `no models line` |

- **A section** runs from its `## ` heading to the next.
- **An item** is a line opening, after its indent, with `- `, `<digits>. ` or `| `, with each following line indented
  deeper that opens none and is not blank.
- **Its commands:** the item's lines joined by a space; with its spans masked (`SPAN`), the first `**Acceptance:**` or
  `Verify:` label outside a span; `commands(<the text after it>)`; of those, each whose text holds a space. Its break is
  `breaks(text, tokens(masked(text)))`.
- An `Unparsed` → `brief: cannot check — <section>: <its message>`, exit 2; so does a brief that cannot be read
  (`brief: cannot check — <path>: <strerror>`), a missing `VERIFY_CHECK` (`brief: cannot check — no verify_check.py
  beside this skill`), and a missing `CONDUCT` (`brief: cannot check — no conduct.py beside this skill`).
- No line printed → `brief: ready for the cut`, exit 0; else exit 1.

```
# Background cut · a minor · hard · 2026-11-06     depth ✓
At f349aa8, 2026-11-06.                             At ✓
## For the cut
1. **`0083-plan-queues`** · `minor` …                     an item
   - **Acceptance:** `brief_check.py` fails a `$(…)` …    no span with a space: no command
   - Verify: `grep -c $(cat f) x` prints `1`               a command, `$(…)`: halt
```

### D2

The brief's template (`skills/mf-plan/SKILL.md:148-149`): `<the change id and bump proposed · `debt: [ids]` · the conditions
— filled when the frontier is empty>` → one item per change, in cut order:
`<n>. **<slug>** · <bump> · after: <ids, or the slug of an earlier item of this brief, or none> · debt: [<ids>] or none · decide: recommended`, then the indented lines
`- models: build <model> <effort> · converge <model> <effort> · release <model> <effort> · cut <model> <effort>` and
`- **Acceptance:** <commands>`. The models are proposed at the close from the session's menu, by `mf-cut-change`'s
*Suggesting models* table, the cut station's own by default the strongest tier · high (P18); `decide: recommended` stands when
the person delegates the cut's doubts (P8). The cut station writes `models.toml` from this line (0082's D7).

### D3

Step 6, the hard close, after "the person confirms it. Then remove `## Open` and fill `## For the cut`.":

1. **The models and the switch** are rows of the settled table the person confirms, per [D2](#d2).
2. **The check:** run `uv run --script scripts/brief_check.py <brief>`, `scripts/` resolved from this skill's package. Exit
   1 → fix each line it prints in the brief and run it again; exit 2 → **halt**, naming it.
3. **The question,** once, unless `then=ship` was given. First run `uv run --script ../mf-ship/scripts/conduct.py status` in
   the primary checkout; show each `## For the cut` item as the brief holds it, and what `status` prints. Then ask "confirm, and
   queue it?".
4. **Yes, or `then=ship`:** the executor from runtime evidence — Claude Code → `claude`; Codex → `codex`. For each change of
   `## For the cut`, in order, run in the primary checkout
   `uv run --script ../mf-ship/scripts/conduct.py cut <slug> <bump> brief=<the brief's absolute path> [after=<ids>] --executor <executor> --model
   <cut model> --effort <cut effort>`, `../mf-ship/` resolved from this skill's package; an `after` naming an earlier change
   of the brief takes the id its `cut` line printed (`cut: queued <id> · …`). Paste each line; an exit 2 stops the queue,
   reported in full. The yes is the person's to every merge and push in the run it joins or starts, as `mf-ship`'s is: each
   queued version, and each open version that run takes (P9).
5. **No:** queue nothing.

The close-out's last line: hard and queued → `Next: the run cuts and ships it; conduct.py status says where it stands.`; hard
and not queued → one `Next: /mf-cut-change <NNNN>-<slug> <bump> brief=<path>` line per change, in order; light → as today.

The *Parameters* table gains `` | `then` | no | `then=ship` — at a hard close, queue the cut without asking | ``.

### D4

- **The role line** (`:8-10`): "You do **not** cut, build, review, converge or release, and you never move the target's
  checkout" → "You do **not** cut, build, review, converge or release — on the person's yes at a hard close you queue the cut
  with `conduct.py cut`, and the run cuts it — and you never move the target's checkout". The diagram becomes:

  ```
    mf-plan ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
       │              ▲
       ├── brief ─────┘   written after every round
       └── on yes: conduct.py cut ──▶ the run's cut station
  ```
- **Step 2**'s *never* list stands; Step 6's `conduct.py cut` is its one exception, named there: it writes the run directory
  and the home folder's queue, never the checkout.
- **Never** gains: "Never queue a cut without the person's yes at a hard close, or `then=ship`; never queue a light brief."
- **`docs/decisions.md`** — **D59 · A hard plan closes on a checked brief, and queues its cut on the person's yes**, in
  *Planning*, its id added to the diagram's Planning list: at a hard close `mf-plan` names per change the models of the build,
  converge, release and cut station and the switch `decide: recommended`, runs `brief_check.py` until it passes, shows the
  `## For the cut` items and `conduct.py status`, and asks once, "confirm, and queue it?". Yes, or `then=ship`, runs
  `conduct.py cut` per change in order (D58), and is the person's yes to every merge and push in the run it joins or starts; no
  ends on `/mf-cut-change`. The plan never cuts. **Why:** a cut in the person's session kept
  the chat busy, and a brief out of shape is a cutter's doubt made at the plan. **Rejected:** the plan cutting · a light brief
  queued · a question per change. D5's opening "**`mf-plan` grills a version to settled decisions and writes the brief;"
  becomes "**`mf-plan` grills a version to settled decisions and writes the brief, and at a hard close queues its cut (D59);".
- **`tests/test_skills.py`** — `_METRICS_SCRIPTS` gains `("mf-plan", "scripts/brief_check.py")` and
  `("mf-plan", "../mf-ship/scripts/conduct.py")`, appended last, and each expected list of
  `test_the_metrics_script_scan_reports_a_missing_script` gains `skills/mf-plan/SKILL.md: scripts/brief_check.py: not named`
  and `skills/mf-plan/SKILL.md: ../mf-ship/scripts/conduct.py: not named`, last.

## Tests

`git grep -c '^def test_' HEAD -- tests/` totals 221 at the cut. Added, unit, in `tests/test_brief_check.py`, loading the
script with `importlib` as `tests/test_verify_check.py` loads its own, each brief written under `tmp_path`:

- `test_a_hard_brief_is_ready_for_the_cut` — a hard title, `At f349aa8, 2026-11-06.`, a `## Decisions` row whose Acceptance is
  `make gate`, and a `## For the cut` item whose `**Acceptance:**` names `` `$(…)` `` as a word and whose `Verify:` is
  `` `grep -n 'x' f` prints a line ``, wrapped onto a deeper-indented line of its own so the item joins it: exit 0, `brief: ready for the cut`. The script run as a command,
  `[sys.executable, <script>, <brief>]`, exits 0 the same, covering its `__main__` line.
- `test_a_brief_out_of_shape_halts` — one brief with a `light` title, `At --output=x, 2026-11-05.`, an empty
  `## For the cut`, a `## Decisions` `Verify:` of `` `grep -c $(cat f) x` `` and an Acceptance of `` `cd x && make gate` ``:
  exit 1, each line of [D1](#d1) printed — light, no `At`, the empty section, `$(…)`, `cd`; a title with no depth prints its
  own line. Items out of shape print the item-head halts — `not a slug`, `not a bump`, `not an after id`, `no after:` — and the
  models halts — `not a model or effort`, `the models line is not …`, `no models line`.
- `test_what_cannot_be_checked_exits_2` — a missing brief; a `Verify:` with an odd backtick; a `Verify:` with an unclosed quote;
  `CONDUCT`, then `VERIFY_CHECK`, set on the module to a missing path: each exits 2 with its `brief: cannot check — …` line.

Extended: `test_the_metrics_script_scan_reports_a_missing_script`, per [D4](#d4). No end-to-end test (`T1`); none deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A prose span with a space that is no command** → it is read as one; it breaks only on `$(…)`, a backtick, a variable, a
  loop word or `cd` first, and the halt names the span for the plan to rewrite.
- **A queued cut the person did not mean** → the close asks once, and `then=ship` is the person's own word up front.
- **`brief_check.py` reads `verify_check.py` from the cut's package** → both ship in one pinned release (D55); a missing one
  exits 2.

## Verdict

Ready to build.
