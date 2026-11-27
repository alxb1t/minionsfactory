---
bump: minor
version: v0.126
---

# Queue

The home queue's entry, its lock, its `briefs` and `supervised` records and its rejoin requests move into one home module, `skills/mflib/queue.py`, and are then read and written by one rule.

Reading map: [design](design.md) holds the module, the typed entry, the one read, the one write, the requests and the test cost, [tasks](tasks.md) holds the phases: the pin, the module, the stations, the fix, the record.

## Why

The queue's I/O sits in functions of `skills/mf-ship/scripts/conduct.py` that each read a broken shape their own way:

- A link at an entry is followed.
- A FIFO at an entry, at `briefs/<id>` or at `supervised/<id>` blocks the whole queue read.
- A deep JSON raises `RecursionError` out of the list of entries, and a wrong type is kept.
- A null `waits` is a wait to the conductor and none to the viewer.
- A failed write in `cut` or `rejoin` ends in a traceback and leaves the reservation.

The series moves code one region at a time, each with a pin first, then the move, then the fix ([D10](design.md#d10)). This version does it for the queue.

## What Changes

- **Pin:** the cases of the region's mutation run, written again at `HEAD`, each green as the code stands, and the pins of what no mutant reaches.
- **Module:** `skills/mflib/queue.py` holds the entry as one typed record, its keys named once, its write, read, list and removal, the lock's open, a request's make, take and test, the `briefs` and `supervised` write and read, and the cut halt's text. Each behaves as its copy does today. No script calls it yet.
- **Stations:** the conductor's reads, writes, lists and removals of an entry, its lock, its requests and its `briefs` and `supervised` sites go through the module. No assert changes.
- **Fix:** one read, one write, one meaning of `waits`, requests by name under the folder's descriptor; a failed write in `cut` and `rejoin` stops with exit 2.
- **Record:** the spec's sentence on what a run keeps in the home folder, the decisions and the threat model's sentences that name the queue, the module's map row.
- ADDED *The queue is read and written through one module*: the typed entry, the one read, the staged write, requests by name, and a failed write that stops `cut` and `rejoin`.
- MODIFIED *A halt stops only its version, and a re-run resumes*: its sentence on what the run keeps in the home folder names the queue's entries, `briefs`, `supervised` and the rejoin requests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *The queue is read and written through one module* is added. *A halt stops only its version, and a re-run resumes* is edited in one sentence.

## Impact

- **Code:** `skills/mflib/queue.py` (new), `skills/mflib/statefile.py`, `skills/mf-ship/scripts/conduct.py`.
- **Tests:** `tests/test_queue_pins.py` and `tests/test_queue.py` (new), `tests/test_statefile.py`, `tests/test_conduct.py`, `tests/test_claim.py`, `tests/test_viewer.py` and `tests/test_modelsfile.py`.
- **Record:** `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md` and `THREAT_MODEL.md`, and the living spec through the delta.
- **Behaviour:** a broken shape at an entry, `briefs/<id>`, `supervised/<id>` or a request reads as [D3](design.md#d3) says. A failed write in `cut` and `rejoin` exits 2.

## Not in this change

- **The kept files:** the kept origin, `.default`, the offline base, the release ledger, the gate approval, the live mark, `repos`, the pin's files, the probe mark and `ship.toml`. They are the next version's, `kept`.
- **The lock's extent and its wait with no limit,** and the queue's reads outside the lock: the line's behaviour, not the format's.
- **`pin.py`, `gate_check.py` and `cloud_setup.py`:** each holds no queue site.
- **The viewer's borrow of `_cuts`:** it stays by name, listed in `PRIVATE_REACH`, until the readers' version. `viewer.py` is not edited.
- **The viewer's fingerprint,** which stats the `cuts` folder through `layout.queue_cuts` and reads no entry.
- **A gate rule for the entry's keys:** the typed record and a round-trip case hold them.
- **`_next_id`, `_entries` and `reach`:** each stays the conductor's, and what an entry means to a run — the takers, the cap, rejoin's chain — stays the conductor's.
- **The debt file:** no task edits a card.
