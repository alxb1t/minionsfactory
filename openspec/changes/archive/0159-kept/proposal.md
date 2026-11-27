---
bump: minor
version: v0.129
---

# Kept

Move the conductor's and `gate_check.py`'s kept files — the kept origin, `.default`, the offline base, the release ledger, the gate approval, the live mark, `repos` and the probe mark — into `skills/mflib/kept.py`, as `queue` moved the queue's.

Reading map: [design](design.md) holds the module, the stations, the fix and the cases, [tasks](tasks.md) its phases.

## Why

Each kept file's writer sits in one script and its parser in another, and the files are written in forms that differ. A broken kept file ends a command in a traceback, or reads as its permissive answer: a link at the kept origin counts as kept, a FIFO blocks a read, a bad byte in a ledger entry, an approval or `.default` raises past an `except`. No test plants a broken file at any of them.

## What Changes

- **Phase 1:** the cases of the region's mutation run, and the shapes no mutant reaches, in `tests/test_kept_pins.py`, green on today's code.
- **Phase 2:** `skills/mflib/kept.py`, called by no script, with its unit cases and its row in `docs/modules.md`.
- **Phase 3:** the conductor, `pin.py` and `gate_check.py` go through it; a move changes no assert.
- **Phase 4:** the right sides: one read, one write, the stops, and `.default` written with a newline.
- **Phase 5:** the decisions, the threat model and the recipes name the module.
- **Requirement added:** *The kept files are read and written through one module*, the rules of the read, the write and the stops.
- **Requirement modified:** *A halt stops only its version, and a re-run resumes*, its sentence of what a run keeps in the home folder gaining `.default`, the live mark, `repos` and the probe mark.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the kept files' module, and the list of what a run keeps in the home folder.

## Impact

- `skills/mflib/kept.py` — new.
- `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/scripts/pin.py` and `skills/mf-converge/scripts/gate_check.py` — go through it.
- `tests/test_kept_pins.py` and `tests/test_kept.py` — new; `tests/test_conduct.py`, `tests/test_pin.py`, `tests/test_claim.py`, `tests/test_gate_check.py` and `tests/test_structure.py` change the line by which a test reaches a name, plants a file or lists an entry.
- `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md` and `THREAT_MODEL.md` — name the module and its rules.

## Not in this change

- `pins`: the pin's files `source`, `pending`, `hold` and `checkout` and their readers and writers in `pin.py`; `ship.toml`'s read in the conductor and its write in `cloud_setup.py`; the stop of exit 2 for a pin file and `ship.toml`; `describe`, `move` and `install`.
- The cycle between `pin.py` and the conductor and `CYCLE_FILES`: the conductor's load of `pin.py` for `trees`, `describe` and `move`, and `pin.py`'s load for `_scratch`, `SSH_COMMAND` and `GIT_TIMEOUT`, stay, `_scratch` a `PRIVATE_REACH` entry.
- `cloud_setup.py` and its `ship.toml` text, until the cloud machine's Python is known.
- The process probe, of which only the mark moves; the viewer's `projects` and the metrics script's `_recorded_repos`, until a later version; `ui.toml`, `review-metrics.toml` and `prices.toml`; the home scratch folder; the queue lock and the reads outside it.
- Any gate rule for the home's names, and any card of `.minions/debt.md`: none is triggered here.
