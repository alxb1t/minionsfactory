---
bump: minor
version: v0.130
debt: [0159·R3]
---

# Pins

Move the pin's files — `source`, `pending`, `hold` and `checkout` — with their reads, writes and removes in `pin.py`, and the conductor's read of the operator's `ship.toml`, into `skills/mflib/kept.py`, beside the kept files `0159-kept` moved there.

Reading map: [design](design.md) holds the decisions, the test cost, the readings and the cases; [tasks](tasks.md) holds the phases: the pin, the module, the stations, the fix, the record.

## Why

The pin's files and the `ship.toml` read are the last kept files with their format in the scripts: `pin.py` reads and writes the pin's files in place, with no bound, no link guard and a bad byte that ends a run in a traceback. The conductor reads `ship.toml` by path: it follows a link, blocks on a FIFO and lets a deeply nested file through as a traceback. `kept.py` already holds the read and the staged write for the rest of the home folder (`0159-kept`); this change puts the pin's files and `ship.toml` behind the same read and write, then turns the broken shapes into a stop that names the file.

## What Changes

The moves keep today's behaviour until phase 4, which alone turns a right side (Q26).

- `tests/test_pinfiles_pins.py` pins the region on today's side: the cases of the mutation run, and a link, a FIFO, a folder, a bad byte, an empty file and an oversize file at each pin file and at `ship.toml`.
- `skills/mflib/kept.py` gains one reader and one writer for each pin file, a clear for `pending` and `hold`, and the `ship.toml` read with its cap and tags checks; `Broken` can name a path under the config folder.
- `describe`, `move` and `install` of `pin.py` call `kept`, and the reader and writer of `pin.py` go; `_ship_file`, `_cap` and `_pushes_tags` of `conduct.py` call `kept`.
- The pin's files are read through no link, without blocking, bounded and strict; written staged at 0600 in a folder of 0700; removed by name under the folder's descriptor. A broken one stops the command, exit 2, naming it; at `move` it is named and nothing moves.
- An empty `source` reads as none.
- `ship.toml` is read by `kept.py`'s read: a link, a FIFO, a folder, a file over 65,536 bytes, a bad byte, a TOML error and a too deep nesting stop the command, exit 2, naming the file.
- Card `0159·R3` is paid: one real-byte test of `tests/test_kept_pins.py` carries the live-mark assertion and the patched twin goes.

Requirements the delta touches, one line each:

- MODIFIED `A halt stops only its version, and a re-run resumes` — what the run keeps in the home folder names the pin's files.
- MODIFIED `The kept files are read and written through one module` — the module holds the pin's files and the `ship.toml` read, with the same read and write for them.
- ADDED `The pin's files are read and written through kept.py` — the broken-file stops of `describe`, `move` and `install`, the staged write, the empty `source`.
- ADDED `A ship.toml that cannot be read stops the command` — the shapes the one read refuses, and the frame of the stop.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` — the requirements above.

## Impact

- Code: `skills/mflib/kept.py`, `skills/mf-ship/scripts/pin.py`, `skills/mf-ship/scripts/conduct.py`.
- Tests: new `tests/test_pinfiles_pins.py` and `tests/test_kept_pinfiles.py`, which import helpers of `tests/test_pin.py` and read `tests/conduct_load.py`; `tests/test_kept_pins.py` loses a test and gains an assertion.
- Docs: `docs/decisions.md` (D55, D84), `THREAT_MODEL.md`, `docs/principles.md`, `docs/recipes.md`.
- A `ship.toml` that is a link now stops the command; the changelog says so. A pin file that is a link, a folder or a FIFO now stops `describe`; `install` stops on a folder alone and replaces a link or a FIFO at the name.

## Not in this change

- `cloud_setup.py` and its `ship.toml` text stay as they are (Q261): that script runs under the machine's own `python3`. `write_ship_toml` is listed in [design](design.md#d12).
- What `0159-kept` moved to `kept.py` keeps its behaviour; only `Broken` changes.
- The reads of `ship.toml` at `run`'s start, for the cap and again for the tags, stay.
- The cycle between `pin.py` and the conductor and `CYCLE_FILES` stay (Q260): `_scratch`, `SSH_COMMAND` and `GIT_TIMEOUT` one way, `trees`, `describe` and `move` the other.
- The rest of `pin.py`: `_link`, `_export`, `_fetch`, `trees` and `uninstall` read or write no pin file.
- `ui.toml`, `review-metrics.toml`, `prices.toml` and the viewer's `read_config`.
- The swallow of a `kept.Broken` of the kept origin at the end of `describe`: it is `kept`'s read.
- Debt `0152·S2`, `0156·S1` and `0157·S2`: the region does not trigger them.
- A hard link at a pin file reads as the file; no test plants one (Q265).
