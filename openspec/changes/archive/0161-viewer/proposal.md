---
bump: minor
version: v0.131
---

# Viewer

5e1 of the state formats: the operator's live page, `skills/mf-ui/scripts/viewer.py`, reads the status log, the run log, a findings file, the queue and the home's `repos` through the home modules, which gain the parsers it held alone; converge writes its `verdicts` line through `statuslog`.

Reading map: [design](design.md) holds the decisions, where each thing lands, the cases and the readings, [tasks](tasks.md) holds the phases: the pin, the module, the readers, the fix and the record.

## Why

The viewer parses each state format with its own regexes and its own reads, beside the module that writes each. The two disagree on files of today's format, so the board shows an older run as the newest, takes a `verdicts` text from any line, and stops a whole project on a log named like no date. The series ends with one parser a format ([D13](design.md#d13)); the viewer is its first reader.

## What Changes

The phases, in order, each ending on a green `make check`:

```
1 the pin      the cases of the mutation run, each on today's side, in tests/test_viewer_pins.py
2 the module   the home gains the parsers; no script calls them
3 the readers  the viewer and converge call them; no assert changes
4 the fix      each turned reading takes the module's side
5 the record   spec, decisions, threat model, recipes
```

The requirements the delta touches, one line each:

- **MODIFIED** *The viewer projects every ship line, read-only*: the board's newest run, its mark and `fixing` come from the status log's runs, a `repos` that cannot be read shows one row that says so, a linked `.minions` and a relative line are no project; the load of `conduct.py` and `converge.py` stays.
- **MODIFIED** *One module writes and parses the run log*: the viewer's borrowed `EVENT` and `last_log` are removed, a name that is no real date is no log, and the module gives an event its moment and reads the cause.
- **MODIFIED** *The kept files are read and written through one module*: `kept.repos` reads the record and raises `Broken` where the viewer read nothing.
- **ADDED** *One module parses a status log's runs and its verdicts line*: `statuslog` gives every run and writes and reads the `verdicts` line, with the spent text converge wrote.
- **ADDED** *A reader's bounded stream of lines*: `statefile.lines` streams a regular file, each line cut at the caller's length.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above, in [the delta](specs/sdd/spec.md).

## Impact

- The viewer and its tests: `skills/mf-ui/scripts/viewer.py`, `tests/test_viewer.py`, `tests/test_viewer_pins.py`.
- The home: `skills/mflib/statuslog.py`, `skills/mflib/runlog.py`, `skills/mflib/statefile.py`, `skills/mflib/kept.py`, with `tests/test_statuslog.py`, `tests/test_runlog.py`, `tests/test_statefile.py`, `tests/test_kept.py` and `tests/test_kept_pins.py`.
- Converge: `skills/mf-converge/scripts/converge.py` writes its lines through `statuslog`.
- The gate's lists and the map: `tests/test_structure.py`, `docs/modules.md`.
- The record: `docs/decisions.md`, `THREAT_MODEL.md`, `docs/recipes.md`.

## Not in this change

- `stage_of`, the viewer's loads of `conduct.py` and `converge.py`, and its borrowed station logic, until the station table ([D3](design.md#d3), [D17](design.md#d17)).
- `scripts/metrics/run.py`, `scripts/metrics/debt.py`, `prices.toml`, `review_metrics.py` and `skills/mflib/eras.py`: later versions of the series ([D12](design.md#d12)).
- The status log's heading date and its events' clocks ([D41](design.md#d41)).
- A spawn's `model`, `effort` and `executor`, the phase, `limited until`, a worker log's stamp and `tasks.md`'s ticks stay in the viewer ([D23](design.md#d23)).
- `ui.toml`, `read_config` and the viewer's own state files ([D7](design.md#d7)).
- The conductor: nothing of `conduct.py` changes, and the page, the frame and `State` stay ([D31](design.md#d31), [D35](design.md#d35)).
- Debt: no open card is triggered by the region.
