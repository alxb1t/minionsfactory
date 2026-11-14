# Card title — design

How a card's title is read, and how the build reads its tick back, both as a patch. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Every reader of cards matches a title as `^- \*\*(\S+) — `. A bold-led bullet that closes its bold after its first word, such as `- **stale-claim** — ran.`, matches with the id `stale-claim**`. `_cards` in `converge.py` opens a card on it and finds no `Amend:` line, so the file is malformed and a rewrite worker runs for a file whose cards were fine. `open_cards.py` stops on the same bullet with `card <id>: no Status`.

The build ticks a phase's box before it commits, and nothing reads the box back. `conduct.py` reads `## Progress` at `HEAD` alone, and a box left unticked halts the version with no answer: the rescue ticks no box, and the supervisor may not ([D61](../../../docs/decisions.md#d61--a-supervisor-answers-what-rescue-diagnoses), [D73](../../../docs/decisions.md#d73--a-build-runs-a-fresh-worker-per-phase)).

## Goals / Non-Goals

| goal | non-goal |
|---|---|
| One title rule, held by every reader of cards | A section rule for a findings file's body |
| A card's title as `worker.md` writes it | What a file reads as after its rewrite |
| The build prints the tick it claims, from `HEAD` | A tick by a script or by the supervisor |

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A card's title is a line `- **<id> — ` whose id holds no `*`: the bold is still open after the id | catches `- **stale-claim** — ran.` and `- **Spec** — none.`; no tracked contract names a `## Cards` or `## Passes` section | a rule by section: it would not catch a Summary bullet |
| [D2](#d2) | All the copies of the pattern take the rule | `open_cards.py` stops converge on the bullet and the others misread it silently; a line read two ways is the defect | fixing `converge.py` alone |
| [D3](#d3) | `worker.md` gains one sentence: no line outside a card starts with `- **` | the pattern still reads `- **Spec — none.**` as a card; the sentence keeps a checker from writing it | a longer rule for checkers' references |
| [D4](#d4) | After its phase commit `mf-build` prints the phase's `## Progress` line as `HEAD` holds it, by one named command, quotes it in the close-out, and ticks and commits a line still unticked | the worker of 0133 reported a tick `HEAD` did not hold | a tick by rule, by a script or the supervisor: it moves who owns the tick, amending D61 or D73, a minor |
| [D5](#d5) | A patch, with no paydown first and no `debt:` | both fixes correct what the line already does and add no decision or requirement; no card's trigger fires | a paydown version first |
| [D6](#d6) | The card title and the tick read are phases of their own, rated moderate | the person at the plan | one phase: the fixes share no file |
| [D7](#d7) | `_cards` in `conduct.py` takes the title rule too | the plan's list of copies misses `_cards` of `conduct.py`, which reads a debt heading's card ids from the same pattern; D2's reason holds. Decided by the cutter | leaving it: a closed-bold bullet under a debt heading would be listed as a card id |

### D1

The pattern becomes `^- \*\*([^\s*]+) — `, the capture kept where a copy has one. The id stops at the first space, and a `*` before the space ends the match: `- **stale-claim** — ran.` has `*` after `stale-claim`, and the ` — ` does not follow it.

```
- **0120·R4 — a title**        card   id 0120·R4
- **stale-claim** — ran.       no card
- **Spec — none.**             card, id Spec: D3 keeps a checker from writing it
```

### D2

The copies, each a one-line change, none moved to a shared module (each script is a stand-alone `uv` script):

| file | name |
|---|---|
| `skills/mf-converge/scripts/converge.py` | `TITLE`, `DEBT_TITLE` |
| `skills/mf-converge/scripts/open_cards.py` | `TITLE` |
| `skills/mf-converge/scripts/debt_match.py` | `TITLE` |
| `skills/mf-converge/scripts/overlap.py` | `TITLE` |
| `skills/mf-ship/scripts/conduct.py` | `CARD`, and [D7](#d7)'s `_cards` |
| `skills/mf-cut-change/scripts/cut_context.py` | `CARD_ID` |

`NAMED` in `open_cards.py` stays: it names the bold line above a stray `Status`, off the card's form or not. `review_metrics.py` keeps only a piece with a `Priority` line, and `tests/fake_worker.py`'s stand-in writes ids with no `*`; both stay.

### D3

The sentence goes in the paragraph of `worker.md` that opens "The body is a list of cards".

### D4

`mf-build` Step 2 gains an item after the commit: `git grep -n -e '^- \[.\] <N> — ' HEAD -- openspec/changes/<change-id>/tasks.md` prints the phase's `## Progress` line as `HEAD` holds it. A `[ ]` there is ticked, staged by name and committed `docs(<change-id>): tick phase <N>` with the trailer block, and the command runs again. Step 4's close-out quotes the line.

The pattern's ` — ` keeps a sub-task line `- [x] N.M` out of the output.

### D5

A patch: [AGENTS.md](../../../AGENTS.md) lets it fix what the line already does and modify a requirement to correct it. A title read as `worker.md` writes it is a defect's fix, and a read-back is a step of the build's prose. The open debt stands past the paydown line, and no card's trigger names the card reader, the tick or a file of this version.

### D6

The card title is the first phase and the tick read the second. Each is rated `moderate`: settled text and one-line edits, with a rule of a live skill written once.

### D7

The cutter took this under the brief's `decide: recommended`: the plan's list stands, and `_cards` of `conduct.py` joins it. Its `re.match(r"- \*\*(\S+) — ", line)` becomes `re.match(r"- \*\*([^\s*]+) — ", line)`.

## Tests

The tests below are unit tests, with no test removed and no end-to-end test added: the readers are pure functions of a file's text, so the lowest layer holds them (`T1`).

| test | layer | file | holds |
|---|---|---|---|
| `test_a_bold_bullet_is_no_card` | unit | `tests/test_converge.py` | `read_findings` with `- **stale-claim** — ran.` under `## Passes` and `- **Spec** — none.` in a Summary reads the real card alone; `DEBT_TITLE` skips the same bullets |
| `test_open_cards_leave_a_bold_bullet_out` | unit | `tests/test_open_cards.py` | `open_cards.main` on a file holding both bullets writes the real cards alone |

Counts, from `git grep -c "^def test_" -- tests/test_converge.py tests/test_open_cards.py` at the base: `tests/test_converge.py:32` and `tests/test_open_cards.py:2`. After the build the same command prints `33` and `3`.

No existing test turns red: at the base `git grep -n -F -e '** — ' -- tests` prints one line, a Status value in `tests/test_open_cards.py`, and no fixture holds a `*` inside a card's id.

`debt_match.py`, `overlap.py`, `conduct.py` and `cut_context.py` take a one-line change each and no new test: the gate's changed-line coverage holds, because each line runs on import or in a test that already reaches it. The tick read is skill text, held by review ([D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans)).

## Dependencies

None.

## Risks / Trade-offs

- A checker writing `- **Spec — none.**` is still read as a card with id `Spec`. [D3](#d3)'s sentence is the whole guard, and a file that breaks it is malformed as before, then rewritten once.
- The tick read runs after the commit, so a line found unticked costs a second commit on the phase. That is the price of a tick `HEAD` holds, and the run's phase check reads `HEAD` too.
- A worker may still skip the new item. The halt it leaves is the one that exists today, and a tick by rule stays a question for the rescue-routes version.

## Verdict

Ready to build: the card title in the first phase, the tick read in the second, each ending on a green `make check`, the second on a green gate.
