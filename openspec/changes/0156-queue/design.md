# Queue — design

The queue's entry, lock, `briefs`, `supervised` and rejoin requests move into `skills/mflib/queue.py`, then take one read and one write. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The home folder's queue is `~/.mf-ship-origin/<digest>.queue/`. It holds `lock`, `cuts/` (one JSON entry per queued cut), `rejoin/` (empty files, one per request), `briefs/` and `supervised/` (one line each). `skills/mflib/layout.py` names the paths; no string outside it spells them, save `"rejoin"` in the request functions of `skills/mf-ship/scripts/conduct.py`.

The queue's I/O is a set of functions of the conductor, named in [D8](#d8). Their callers are in `Run.cutting`, `Run.supervise`, `Run.cut_halted`, `Run.wait_cut`, `Run.unwait`, `Run.take_requests`, `Run.in_flight`, `Run.ship`, `Run._needs`, `Run.hold_limited`, `cut`, `rejoin`, `grant` and `status`. The viewer reads the entries through the loaded conductor's `_cuts`, and takes its fingerprint from `layout.queue_cuts`.

The sibling versions did the same for the status log, findings, debt file, run log, claim, models file and marks: a pin of today's behaviour, a module that behaves as the copies do, the stations' move, then the fix. The evidence is the series' queue checks: the mutants of the region, each pinned by the suite or by a new case, and the readings no rule states, each settled.

## Goals / Non-Goals

**Goals**

- One home for the queue's format and its I/O, on `layout.py` and `statefile.py` alone.
- One read and one write, held by cases that fail on the old side.
- A broken shape never blocks, never raises out of a read, and never reads as a valid entry.

**Non-Goals**

- The kept files, the lock's extent and wait, the reads outside the lock, a gate rule for the keys, and the viewer's own structure. See [proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `skills/mflib/queue.py`, a `home` module on `layout.py` and `statefile.py`, holds the queue's I/O | the format and its writer sit in different scripts today | a module per folder · the module on the conductor |
| [D2](#d2) | The entry is one typed record, its keys named once | its keys are read with no type check, and some sit outside the old key list | a gate rule per key |
| [D3](#d3) | One read: no link, no block, a regular file, a bound, a strict decode | a link is followed, a FIFO blocks, a deep JSON raises | `statefile.read`, which replaces a bad byte |
| [D4](#d4) | One write: staged, 0600, no link followed, an entry over its bound refused | the writes differ by site today | the old `mkstemp` write |
| [D5](#d5) | A request is made by its name under the `rejoin` folder's descriptor, and a stray name is removed | a staged name stranded there would read as a request | the staged write for a request |
| [D6](#d6) | A failed queue write stops `cut` and `rejoin`, exit 2, and `cut` removes its reservation | both end in a traceback and `cut` leaves the reservation | halting the run on it |
| [D7](#d7) | The cut halt's text is the module's; `_cuts` stays the conductor's, by name | the text is spelled twice and the viewer borrows `_cuts` by name | moving `_cuts` and editing the viewer |
| [D8](#d8) | The conductor keeps `_queue_lock`, `_cuts`, `_brief_of`, `_requests` and `_request` as short calls; `_write_cut`, `_requested` and `_merge_tried` are deleted | a test patches `_queue_lock` and `_requests` by name; `Stop` stays the conductor's | deleting every name |
| [D9](#d9) | The pin phase writes the mutation run's cases and the pins of what no mutant reaches, in `tests/test_queue_pins.py` | the series moves no code without a pin | the pin inside `tests/test_conduct.py` |
| [D10](#d10) | In a move phase no assert changes, only the line by which a test reaches a name or plants an entry | an unchanged assert over moved code proves the move | one split of `tests/test_conduct.py` |
| [D11](#d11) | The readings no rule states are settled on the side nearest today's behaviour | none contradicts a decision | opening a round for each |
| [D12](#d12) | No gate rule for the keys; the record edits the decisions, the threat model and the map where they live | the keys are common words, and the home's names need none | a rule for the keys |

### D1

The module is `skills/mflib/queue.py`, layer `home`, its `names` cell `layout.py, statefile.py`. It holds:

- the entry's keys and types, its write, read, list and removal;
- the lock's open, and a request's make, take and test;
- the `briefs` and `supervised` write and read, and the cut halt's text.

It imports no conductor class: a failure the conductor words as a `Stop` is a `Refused` or an `Unwritten`, an `OSError` of the same words, and the conductor's caller keeps the `Stop` (C26 of the brief). `conduct.py` already holds the seed line before its first `mflib` import, so no seed line is added.

### D2

The record has the required keys `bump`, `brief`, `executor`, `after`, `halt`, `model` and `effort`, and the optional `dependencies`, `models`, `beside` and `waits`. `bump`, `brief` and `executor` are strings, `after` and `beside` lists of strings, `dependencies` a list, `halt`, `model`, `effort` and `models` a string or null, `waits` a string. `model` and `effort` are null when `conduct.py cut` gets no flag, so a required string would make that entry unreadable (C23 of the brief).

A wrong type at the read is the unreadable entry. `waits` is a wait when it is a non-empty string: the conductor's `unwait` and `_cut_line` and the viewer's `queue_row` read it so, and `viewer.py` is not edited.

### D3

The one read decodes strictly through `statefile.read_bytes` under the folder's descriptor, which the module opens and never makes. An entry is bounded at 262,144 bytes, `briefs/<id>` and `supervised/<id>` at 65,536.

A link, a FIFO, a folder, an entry over its bound, a wrong type, a bad byte, a JSON no object, a JSON too deep and a missing required key are each the unreadable entry, `{"halt": "the queue entry is unreadable"}`. A record that fails reads as none. The list of the `cuts` folder keeps its answer: a linked, missing or file-shaped folder lists nothing, and a name that is no change id is skipped.

### D4

A write of an entry is `statefile.write` mode 0600 under the `cuts` folder's descriptor. The module makes `cuts` alone, mode 0700 with no parents, and a linked `cuts` folder is a failed write. A link at an entry's name is replaced by the rename and its target left.

A write of a `briefs` or `supervised` record is the same staged write, replacing a link without following it. An entry's bytes stay compact JSON in insertion order. A write of an entry over its bound is refused, and the entry that stands is left.

### D5

A request is an empty file, mode 0600, made by `statefile.touch` of its name under the descriptor of the `rejoin` folder, which `statefile.folder` makes with its parents, mode 0700, and opens with no link followed (C27 of the brief). A request is not staged.

The taker unlinks every name it can, a file, a link or a FIFO by its own name, leaves a subfolder, and returns the names that are a change id or `all`. The test `requested` unlinks nothing and counts a regular file named a change id or `all`.

### D6

`conduct.py cut` and `conduct.py rejoin` turn a failed entry write, and a failed request write, into `Stop(2, …)` naming the file; `cut` also removes the reservation it made. In a run — `cut_halted`, `wait_cut`, `unwait`, `take_requests` and the writes of `briefs` and `supervised` — the failure rises as an `OSError` rose, and stays the halt line it is. A failed write part-way down `rejoin`'s chain leaves the entries already cleared cleared.

### D7

`Run.cutting` writes the halt `after <name> is cut-halted` through `queue.halted_text(name)`, and `_halted_after` matches through it. `_cuts` stays in the conductor under its name and returns the module's list, for the viewer's reads; `("viewer.py", "_cuts")` stays in `PRIVATE_REACH` until the readers' version.

### D8

A name stays in the conductor where a test patches it or the viewer borrows it. `_queue_lock` keeps the `Stop` of today's words, `_cuts` the viewer's borrow, `_requests` and `_request` the patch point of the poll's tests, and `_brief_of` its `is_file` test. `_halted_after` and `_cut_line` stay: what an entry means to a run, and how `status` shows it, is the conductor's.

`_write_cut`, `_requested` and `_merge_tried` are deleted; their callers call `queue.write`, `queue.requested` and `queue.merge_tried` (C24 of the brief).

### D9

The pin phase writes the cases of the series' queue checks again at `HEAD`, each green as the code stands and red on the mutants it claims. It adds the pins of what no mutant reaches: each broken shape at an entry, at `briefs/<id>`, at `supervised/<id>` and at a request; a link at the `cuts` and `rejoin` folders; a failed write in `cut`, `rejoin`, `cut_halted`, `wait_cut`, `unwait` and the writes of `briefs` and `supervised`.

It adds each form of `waits` and the cut halt's text written and matched. The run-level cases start no worker. The cases go in `tests/test_queue_pins.py` and the module's own unit cases in `tests/test_queue.py` (C25 of the brief).

### D10

The move phases change no assert. A test may change the line by which it reaches a name — `conduct["_write_cut"]` to the module's `write` — or plants an entry, and nothing else. The conformance check holds it on each phase's diff.

### D11

The settled readings are the series' queue checks' section on them. Most stay as today through every phase, and some stay until the fix phase, where a decision of the person's turns them. Where no decision speaks, today's side stands:

- the entry's write makes `cuts` alone, and its bytes stay compact JSON in insertion order;
- a failed write's staged name is `statefile`'s and no entry to the list;
- a link at an entry's name is replaced by the rename;
- `requested` unlinks nothing;
- a failed write part-way down `rejoin`'s chain leaves the cleared entries cleared.

The write refuses a linked `cuts` folder in the fix phase.

### D12

No gate rule holds the entry's keys: the typed record and a round-trip case do. `docs/modules.md` gains the module's row, and the conductor's `names` cell gains `queue.py`. The record's edits stand where each lives: D58, D62, D47, D84 and D61 in `docs/decisions.md`, the threat model's sentences on the rejoin requests and the cut queue, the format line of `docs/recipes.md`, and the spec's one sentence.

## Tests

The change adds unit and run-level tests and no end-to-end test, and it deletes or merges none.

| layer | added | command | reason |
|---|---|---|---|
| unit | the module's cases and the record's round-trip case, in `tests/test_queue.py`; the new helpers' cases, in `tests/test_statefile.py` | `uv run pytest tests/test_queue.py --collect-only -q` | the lowest layer that can fail for the format |
| run-level, no worker | the pin cases and pins of [D9](#d9), in `tests/test_queue_pins.py` | `uv run pytest tests/test_queue_pins.py --collect-only -q` | each fails on the survivor it pins |
| structure | the module's map row, held by the map test | `uv run pytest tests/test_structure.py -n auto -q` | [D83](../../../docs/decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate) holds each new script |
| end-to-end | none | none | no browser or engine runs |

Tests that reach a queue function by its private name change their line, not their assert, in the stations phase ([D10](#d10)): `tests/test_conduct.py`, `tests/test_claim.py`, `tests/test_viewer.py` and `tests/test_modelsfile.py`. In the fix phase the pins and cases that held today's side turn to the one side, named in each task.

## Dependencies

None.

## Risks / Trade-offs

- **A pin hangs a mutant.** A case that plants a FIFO runs the read in a child process with a timeout, as the series' pins do. The pin phase says so.
- **The module's name sits beside the standard library's `queue`.** Only `skills/` is on the path, and no script imports the standard library's, so `mflib.queue` resolves as `mflib/platform.py` does.
- **A lock case watches a stub.** A pin that stubs `_queue_lock` shows the lock is taken around a write, not that it excludes another process; the module's own test holds the `flock`.
- **A deep JSON in the entry** costs the parser's recursion. The read catches `RecursionError` at the decode.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin, the module, the stations, the fix, the record.
