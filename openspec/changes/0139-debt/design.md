# The debt file module — design

One module writes and parses `.minions/debt.md`, and the scripts that touch it go through it: pin what they do, move it, then make the copies agree. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The debt file has a writer in converge, one in the conductor's migration and one in the release's prose, and parsers in converge, `debt_match.py`, `cut_context.py` and the conductor. Each parser spells the card's title, its extent, its heading and its read in its own way, and the rules of the lock live in more than one place.

The findings module, `skills/mflib/findings.py`, already parses a card, and `skills/mflib/statefile.py` already stages a write and reads with no link followed. The structure rules of [D83](../../../docs/decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate) hold the home, the map and the seed.

```
today                                   after
converge.py  ─ own title, extent, lock  converge.py ┐
debt_match.py ─ own title, extent, read  debt_match.py ┤
cut_context.py ─ debt_match's, loaded    cut_context.py ┼─▶ skills/mflib/debtfile.py ─▶ findings.py, statefile.py
conduct.py ─ own title, lock             conduct.py ┘
```

## Goals / Non-Goals

- **Goals:** each debt rule has one home; the station scripts hold none; the pin holds today's behaviour before it moves and the fix turns one row at a time.
- **Non-Goals:** the metrics' readers of the debt, the prose of the plan, the cut and the release, the migration's link-then-unlink, any edit of a card.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The phases are the pin, the move and the fix. A move changes no assert, only the line by which a test reaches a name | a checker can judge a pure move; a move mixed with a fix it cannot (Q4, Q25, Q26) | fixing a copy while it moves |
| [D2](#d2) | The module is `skills/mflib/debtfile.py`, on `statefile.py` and `findings.py` | a home module named `debt.py` would share a base name with `scripts/metrics/debt.py`, which the map refuses (Q128) | `skills/mflib/debt.py` |
| [D3](#d3) | Where the copies disagree, the module holds each copy's behaviour as it stands, a function or an argument for each, until the fix keeps one | a move changes no assert; one function cannot be every copy's today (C9) | one function that fixes while it moves |
| [D4](#d4) | A debt card is a title with a qualified id, its extent the card's, and one count of the file or of a heading; a heading is the writer's exact form, trailing blanks forgiven on the read | the title patterns count different things today, and the extents cut different cards (Q129, Q130, Q152) | a count per reader |
| [D5](#d5) | The read is converge's everywhere: no link followed, a bad byte replaced, a link a halt; the freeze halts on a debt it may not read | a bad byte stops `debt_match.py` today, the freeze writes `None.` and the repeat rule is off with no halt (Q131, Q147) | the freeze writing `None.` |
| [D6](#d6) | One lock function in the module: `mkdir`, a wait the caller gives, a halt that names it. The lock holds its holder's token, renews its time, and is released only by that holder; the stale break goes through the module | the release removes whatever stands at the name, and a break under a live hold deletes a second holder's lock (Q149, Q150, C6, C10) | a wait of ten minutes for the migration |
| [D7](#d7) | Converge's debt write holds the folder it opens from the primary, `.minions` a part it does not follow | `statefile.folder` follows its root; 0136·S3 and 0138·S2 are that root followed (Q104, Q145) | a write by pathname |
| [D8](#d8) | A `backlog.md` that is no regular file halts the migration at a run's start, naming it. `migrate_debt`'s link-then-unlink stays | today the migration passes it in silence and converge halts on it at every run (Q151, Q148) | fixing the link-then-unlink |
| [D9](#d9) | `report` names a debt it may not read in that change's line and goes on | a bad byte raises out of the whole report today, and a folder reads as no card (Q153) | a halt of the report |
| [D10](#d10) | The module checks a qualified id itself and never asks whether a debt file is a well-formed findings file | `findings.TITLE` takes any id and `findings.malformed` only `R<n>` and `S<n>` (Q146) | `findings.malformed` on a debt |
| [D11](#d11) | A site leaves a structure rule's list in the phase that moves it: `debt_match.py`'s and converge's pairs of the format kind, and `cut_context.py`'s pair of the loads | a listed pair the tree no longer holds fails the test, and every phase ends green (Q86, Q144, C7) | the record phase |
| [D12](#d12) | The release's clear is a function of the module, which no script calls yet | the release's debt deletion gets a writer in the module; the prose that writes it by hand is replaced by a later version (Q98) | a script for the release |
| [D13](#d13) | No task edits a debt card; the cards that cite a moved line are re-pointed by converge | `.minions/debt.md` is written under its lock by converge and the release alone (Q148, C8) | a task that edits the card |

### D1

The pin comes first: each case is seen red under the change named for it, then green on the code as it stands, so the move that follows is judged by an assert that did not change. The fix phase turns the cases of [D4](#d4) to [D9](#d9) one row at a time; a case it does not name stays.

### D2

`debtfile.py` is a home module: standard library, `findings.py` and `statefile.py` only, and it names no state path. Its paths and its lock arrive as arguments, found by the caller through `layout.py`. The map row is `skills/mflib/debtfile.py | home | findings.py, statefile.py`.

### D3

The surface of the move, with the copy each function is today's:

| function | holds | today's copy |
|---|---|---|
| `read(path)` | `""` when missing, a bad byte replaced, `Unreadable(reason)` on a link, a folder or a pipe | converge's `_debt_text` |
| `ids(text, change=None)` | every title id of the text, or of the section `## <change>`, any id | converge's title pattern, the conductor's `_cards` |
| `blocks(text)`, `card_id(block)` | each card as `debt_match.py` cuts it, to the next title or `#` line; the id a block opens with | `debt_match.cards`, `cut_context.py`'s card id |
| `paths(patch)`, `matched(block, changed)`, `page(found)` | the patch's paths, the match on **What it affects**, the cards file's text | `debt_match.py` |
| `filed(text, change, cards)`, `unfiled(text, ident)`, `clear(text, ids)` | file cards under `## <change>`; take one card out and its heading when left empty; take each id out | converge's `_filed`, its take-out of one card, `_section_end` |
| `spoiled(number, index, role, why, round_, change, where)` | the text of a spoiled card, `where` the path the caller names | converge's `spoiled` |
| `qualify(lines, ident, qualified)` | a card's lines, each ended by a newline, its title's id replaced | converge's `debt()` title line |
| `lock(path, wait=0)` | `mkdir`, polls every `LOCK_POLL` seconds up to `wait`, raises `Held`, `rmdir` at the end | converge's `debt_lock`, the migration's lock |
| `write(path, text, folder=None)` | the staged write of `statefile.py`, a link refused | `debt_match.write` |

`PREAMBLE` and `LOCK_POLL` move with them. The callers word every halt: the module raises `Unreadable`, `Held` or `statefile.WriteFailed` and holds no message of a state path. In the move a caller passes the argument that keeps its behaviour, and no assert changes.

### D4

After the fix there is one title, `<4 digits>·<id>` with an id of no blank or `*`; one card, its extent `findings.cards`'s, a blank line not ending it; one count, of the file or under a heading. A heading is `## <change>` as the writer writes it; trailing blanks on the read are forgiven, and a section ends at the next `## ` line alone. The writer's own lookup of a heading is a read, so a heading with trailing blanks is found and no second one is written.

### D5

`read` is the one read of the module: `debt_match.py` takes it, `cut_context.py` takes it and stops on `Unreadable`, and converge's freeze halts on a non-zero exit of `debt_match.py`, where it wrote `None.`.

### D6

```
lock(path, wait)
  take    mkdir path                       held ─▶ poll up to wait, then Held
  token   write path/owner = a fresh token
  renew   touch path after each Still true? command
  release read path/owner; if it is this token, remove owner, rmdir path
          gone or another's: no error
  break   (conductor, a run's start) older than LOCK_STALE: remove owner, rmdir
```

Converge waits 600 seconds by 5; the migration waits none and halts at once on a held lock, as it does. A stale break under a live hold is accepted where the command runs past the renewal: the renewal after each check narrows it, and the break runs only at a run's start. The release's prose keeps taking its lock by `mkdir` and releasing it by `rmdir`; a lock with no `owner` file is the prose's, and is broken as any other.

### D7

`debt()` in converge opens `mflib.statefile.folder(primary, mflib.layout.MINIONS)` and writes `debt.md` through it with `folder=`. A link at `.minions` raises there, where the pathname write followed it.

### D8

The migration's halt for a `backlog.md` that is no regular file — a dangling link, a folder — names the file and starts no worker. The migration's other halts, its lock check and its link-then-unlink are as they were; the threat model's sentence names `migrate_debt` beside `migrate_layout`.

### D9

`report` reads each change's debt through the module and, on `Unreadable`, puts `debt unreadable: <reason>` in that change's line and goes on to the next.

### D10

The module's id check is its own pattern. A debt card whose id is `M<n>`, a spoiled card's, passes; so does any `<4 digits>·<id>` the file holds today.

### D11

After the move, `tests/test_structure.py` no longer lists `("debt_match.py", "- **")` and `("converge.py", "- **")` in `FORMAT_SITES`, nor `("cut_context.py", "debt_match.py")` in `LOADS_OUTSIDE`. The conductor's, `cut_context.py`'s and `scripts/metrics/debt.py`'s pairs of the format kind stay, each for a constant that is no card or for the readers' version.

### D12

`clear(text, ids)` is `unfiled` over each id, in the order given, an unknown id raising as `unfiled` does. Its unit cases are the module's.

### D13

The card that `report` or converge's lock halt names is converge's to re-point. A task of this change that writes `.minions/debt.md` is a defect of the plan.

## Tests

The change adds tests at the lowest layer that can fail for the behaviour (T1): unit cases of the module in a new file, and the pin's cases in the files that already hold each script's tests. It adds no end-to-end test and no run on an engine, because no behaviour here needs a browser or a second host; a pin that needs a conductor reaches it through the helper that already compiles `conduct.py` once.

| layer | adds | removes | counted by |
|---|---|---|---|
| unit, `tests/test_debtfile.py` | a case per function and per right side of [D4](#d4) to [D9](#d9) | none | `uv run pytest tests/test_debtfile.py --collect-only -q` |
| unit, `tests/test_converge.py`, `tests/test_debt_match.py`, `tests/test_cut_context.py` | the pin's cases | none | `uv run pytest tests/test_converge.py tests/test_debt_match.py tests/test_cut_context.py --collect-only -q -k debt_pin` |
| integration, `tests/test_conduct.py` | the pin's cases for the conductor's debt functions and the migration | none | `uv run pytest tests/test_conduct.py --collect-only -q -k debt_pin` |
| unit, `tests/test_structure.py` | none; its lists lose the moved sites, and its map holds the new row | none | `uv run pytest tests/test_structure.py --collect-only -q` |
| end-to-end | none | none | — |

No test is deleted or merged, so the table of removed tests is empty. A pin case is seen red under the change named for it before it is kept ([D1](#d1)); the build's worker runs that change in its own tree and reverts it. `tests/test_staged_writes.py` and `tests/test_converge.py` change the line by which they reach `debt_match.write` and `DEBT_TITLE`, and no assert.

## Dependencies

None.

## Risks / Trade-offs

- **The title's right side is held on no file of the repository.** The debt is gitignored; the module's id pattern is the spec's form, and `<id>` is any run of no blank or `*`, so a card of today's debt is counted. A card with an unqualified title in a person's debt stops being counted by every reader, which converge's freeze then does not match to a diff.
- **A lock that knows its holder.** A holder that dies leaves `owner` inside the lock, which only the stale break removes; the break goes through the module for that reason ([D6](#d6)).
- **The migration's single lock wait.** The migration waits none, so a run's start halts at once on a held lock, as today.
- **Size.** The move touches converge, `debt_match.py`, `cut_context.py`, the conductor and their tests; the phases keep each commit one kind of edit.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin on today's code, the module with no caller, the stations through it with no assert changed, the fix one row at a time, then the record.
