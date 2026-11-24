---
bump: minor
version: 0.121
---

# Run fields

The run log names a build's phase, the load, a halt's cause and each gate's start and seconds, and its readers show them.

Reading map: [design](design.md) holds each field's reach and the test cost, [tasks](tasks.md) holds the phases: the phase, the load, the cause, the gates' lines, the readers and the record.

## Why

Every measurement of a run read these facts by hand: the phase from a worker's first prompt, a halt's cause from its free text, the load from nowhere. The viewer shows nothing while the conductor's gate runs, so a person read an active run as idle. Converge's own gates leave only an exit in a command log.

## What Changes

- A build worker's spawn line carries its phase right after the station word: `build · phase 3 · model …`, `build · close · …`, `build · repair · …`.
- Every spawn and finish line the conductor writes ends ` · load <n>`, the 1-minute load to one decimal.
- Every halt line ends ` · cause <word>`, from a fixed list; the run's closing line carries none.
- The conductor logs `check — gate · start` before each gate it runs; converge logs each gate it runs, with its seconds, through a new method of its host.
- The viewer shows the phase, a running gate and the cause; review metrics books a build's cost by phase; the metrics script reads the new suffixes unchanged.
- A new decision, D90, records the fields where decisions live.
- ADDED requirement: `The run log's lines carry a build's phase, the load and a halt's cause`.
- ADDED requirement: `The conductor and converge log each gate they run`.
- ADDED requirement: `The viewer shows a build's phase, a running gate and a halt's cause`.
- ADDED requirement: `Review metrics books a build's cost by its phase`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above are added; none is modified or removed.

## Impact

- `skills/mf-ship/scripts/conduct.py`, `skills/mflib/runlog.py` and `skills/mf-converge/scripts/converge.py` write the fields.
- `skills/mf-ui/scripts/viewer.py`, `skills/mf-ui/page/index.html` and `skills/mf-review-metrics/scripts/review_metrics.py` read them; the metrics script reads the suffixes as it stands.
- `tests/test_conduct.py`, `tests/test_claim.py`, `tests/test_converge.py`, `tests/test_runlog.py`, `tests/test_viewer.py`, `tests/test_review_metrics.py` and `tests/test_metric_scripts.py` follow.
- `docs/decisions.md` gains D90; `skills/mf-review-metrics/SKILL.md` names the new data key.

## Not in this change

- The budgets kept across runs.
- The repair worker that did not turn a gate green.
- A paydown of the debt list.
- A catalogue metric over causes or phases: the data is read, no measure is set.
- A price for a Codex window share.
