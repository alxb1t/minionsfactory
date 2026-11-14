---
bump: patch
---

# Card title

A bold-led bullet that is no card is read as no card by every reader of cards, and the build reads its `## Progress` tick back before it reports it.

Reading map: [design](design.md) the decisions, the tests and the risks, [tasks](tasks.md) the card title and the tick read.

## Why

Defects of what the line already does, both met in isekai's run of 2026-11-12/13.

- **A bullet read as a card.** Every reader takes a card's title as `- **`, a run of non-space, ` — `. The run takes a closing `**`, so a checker's `- **stale-claim** — ran.` under `## Passes`, or `- **Spec** — none.` in a Summary, is the card `stale-claim**`. It has no `Amend:` line, the file is malformed, and a rewrite worker is spent on a file whose cards were fine.
- **A tick claimed and not made.** The phase worker of 0133 reported its box ticked; `HEAD` held it unticked. The halt `build check fail — phase 4 unticked` has no answer: the rescue ticks no box, and the supervisor may not tick a `## Progress` box.

## What Changes

- A card's title is a line `- **<id> — ` whose id holds no `*`, in `TITLE` and `DEBT_TITLE` of `converge.py`, `open_cards.py`, `debt_match.py`, `overlap.py`, `CARD` and `_cards` of `conduct.py`, and `cut_context.py`'s `CARD_ID` ([D1](design.md#d1), [D2](design.md#d2), [D7](design.md#d7)).
- `worker.md` says that no line outside a card starts with `- **` ([D3](design.md#d3)).
- `skills/mf-build/SKILL.md` prints the phase's `## Progress` line as `HEAD` holds it after the phase commit, quotes it in the close-out, and ticks and commits a line still unticked ([D4](design.md#d4)).
- Requirement **Converge's conductor is a script** (MODIFIED): names the title a card's line takes, and a bold-led bullet that is no card.
- Requirement **The build runs a fresh worker per phase** (MODIFIED): the build reads the phase's tick back at `HEAD`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

- Scripts: `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/scripts/open_cards.py`, `skills/mf-converge/scripts/debt_match.py`, `skills/mf-converge/scripts/overlap.py`, `skills/mf-ship/scripts/conduct.py` and `skills/mf-cut-change/scripts/cut_context.py`.
- Skill text: `skills/mf-converge/references/worker.md`, `skills/mf-build/SKILL.md`.
- Tests: `tests/test_converge.py`, `tests/test_open_cards.py`.
- No decision is added or amended, and no package.

## Not in this change

- Ship fixes 5's second version, run-survives.
- What a file still malformed after its rewrite reads as: a clean verdict, by the spec.
- A tick by rule, by a script or by the supervisor: it moves who owns the tick, amending [D61 or D73](design.md#d4), a minor, and belongs to the rescue-routes version.
- A section rule for a findings file's body: no `## Cards` heading is prescribed.
- The person's test after the release: an isekai converge on the new pin.
