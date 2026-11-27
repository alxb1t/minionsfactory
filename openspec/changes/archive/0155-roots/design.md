# Roots — design

Each opener passes the primary as its root and `.minions` as a part, so a link there is refused; the riders and the record follow. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`statefile.folder(root, *parts)` and `statefile.open_folder(root, *parts)` follow `root` and refuse a link at each part. A caller passes the run directory or a folder below it, so `.minions` is followed; or passes the primary, so `.minions` is a part and is refused. The second form stands at the sites [D3](#d3) lists.

```
today     folder(<primary>/.minions, "changes", id)      .minions followed
after     folder(<primary>, ".minions", "changes", id)   .minions refused as a link
```

## Goals / Non-Goals

- Goal: every opener whose root holds `.minions` passes the primary, and the debt cards of `debt:` close by their premise.
- Goal: the riders' files follow no link, and the threat model and the recipe say what is true.
- Non-goal: any behaviour of a station beyond a link refused. A move changes no assert but the line by which a test reaches a name.
- Non-goal: the items of [the proposal's last section](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Each opener passes the primary as root and `.minions` as the first part; `statefile.folder` and `open_folder` stay as they are | one site at a time stays small, and a primary reached through a link is still followed | a check inside the helper: it would refuse that primary and leave the cards' sites open |
| [D2](#d2) | `claim`, `runlog` and `findings` hold a path below `.minions`: they split it with a new `layout.beneath` into the primary and the parts, and open from there | their callers pass a path, and a signature change reaches every caller of the claim and the run log | each takes the primary: it changes every caller and test of the claim and the run log |
| [D3](#d3) | The opens that pass the primary today, and `_hide_marks`, stay | they are refused already, or their root is git's common folder | moving them: no gain |
| [D4](#d4) | `release.py` has no edit | its marks go through `marks.py`, which D1 changes | an edit of `release.py`: it opens no folder since 0154 |
| [D5](#d5) | `marks.present` and `marks.mtime` stay plain paths; the threat model's sentence is reworded | they open no folder and read no content | opening the folder for a stand test |
| [D6](#d6) | The riders: the gate's record, the cut's notes, a grant and a reservation follow no link, `layout` names `runs/`, `cuts/` and `grants/`, one write wrapper, one open-page name | each is one script's own file or a second spelling of a name | leaving them: each is a link a worker can plant |
| [D7](#d7) | A phase pins, then moves, then turns the pins | a pin green on today's code proves the move changed only the link | moving first |
| [D8](#d8) | A `Verify:` that runs `pytest` over several files, or over `tests/test_conduct.py` alone, carries `-n auto` | the plan check stops a command at 600 s | none |

### D1

The root rule is one line at each site, and the swap cases of phase 1 in [tasks](tasks.md) hold it. A site that holds the run directory today holds the primary one level up: the re-stamp takes `runs.parent`, as its status-log path does.

### D2

`layout.beneath(path)` returns the root and the parts to open the folder `path` with: `<p>/.minions/runs` gives `<p>` and `(".minions", "runs")`. The nearest ancestor named `.minions` is the one taken; a path with none gives itself and no parts, which a test's bare temporary folder is. `claim.py` opens `active.parent`, `runlog.py` opens `runs` and `findings._staged` opens `folder.parent` through it, each adding the name it opens beside as its last part, so no caller or test of those modules changes.

### D3

The sites that stay: `_fresh_tmp`, `sandboxed`, `_scratch_folder` and `_fetch_npm` in `conduct.py`, `_write_debt` in `converge.py`, and `_hide_marks`. Their pins stand and are not turned.

### D4

Facts at the base: `release.py` has no `mkdir` of a change folder, no `unlink` of a mark and no `statefile.write` of a mark. Its marks reach the change folder through `marks.py`, so D1 gives it the root. Card 0152·S3 closes with the other cards.

### D5

The marks sentence of the threat model drops "but follow the `.minions` root" and keeps the stand test's and the time's clause.

### D6

The riders, each with its right side:

- A gate record with a bad byte or a link reads as none.
- `cut-notes.md` goes through `statefile`, and `context.md`, which refuses a link by its own check today, through the same staged write.
- A grant is made under the folder's descriptor.
- A reservation is a regular file read through no link; a link or a folder there fails the cut's check by name.
- `layout` names `runs/`, `cuts/` and `grants/`, and the conductor's sites call it.
- `bundle.py`'s and `open_cards.py`'s write is one `statefile` function each calls.
- Converge calls `layout.open_name`.

### D7

Phase 1 pins today's behaviour, each pin green. The riders' phase and the root's phase move the code and turn the pins they name to the refusal. Each task that turns a pin names it.

### D8

A card's own `Verify:` stays one command. `uv run pytest tests/test_conduct.py -n auto -q` is the form for a run over that file.

## Tests

Added, all unit tests of the lowest layer; end-to-end runs added: none, on no engine.

| file | what it adds | count, by |
|---|---|---|
| `tests/test_statefile.py` | a swap case for each of marks, models file, findings, claim and run log; the cases of `write_or_say` | `uv run pytest tests/test_statefile.py --collect-only -q` |
| `tests/test_conduct.py` and `tests/conduct_load.py` | swap cases for `_restamp`, `_free_log`, `migrate_layout`, a cut reservation and a grant, reached through the loader | `uv run pytest tests/test_conduct.py --collect-only -q` |
| `tests/test_converge.py` | a swap case for `_change_folder` | `uv run pytest tests/test_converge.py --collect-only -q` |
| `tests/test_gate_run.py`, `tests/test_cut_context.py`, `tests/test_facts.py`, `tests/test_cut_pre.py`, `tests/test_layout.py` | each rider's pin and its right side, and the cases of `layout.beneath` | `uv run pytest tests/test_layout.py --collect-only -q` and its siblings |

No test is deleted or merged. The tests of the claim, the run log and the findings keep their call forms and asserts.

## Dependencies

None.

## Risks / Trade-offs

- A path with no `.minions` above it is opened as it stands, so a bare folder of a test is no refusal; a path built by `layout` always holds one.
- An open refused for a link at `.minions` raises `OSError` at a site that raised one for any failed open before.
- A primary reached through a link is still followed: the threat model says so in its reworded sentences.
- `facts.py`, `cut_context.py` and `cut_pre.py` gain a load of `statefile.py`; the rows of `docs/modules.md` name it in the same phase, or the map rule fails.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin, the riders, the root, the record.
