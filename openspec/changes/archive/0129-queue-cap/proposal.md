---
bump: minor
version: v0.103
---

# Queue cap

A queued cut waits while the line is at its cap of versions in flight, a setting of the machine: with a cap of 1 the versions stand in the queue and run one at a time, each after the release of the one before.

Reading map: [design](design.md) holds the setting, the count, the gate and what is shown, [tasks](tasks.md) its phases: the setting, the gate, what is shown, the record.

## Why

The person runs this repo's line and another repo's line on one laptop, each one version at a time, to save the CPU. Today a run takes every queued cut at once, so the plan queues the next version by hand after each release. With `in_flight = 1` in the operator's `ship.toml`, the versions stand in the queue and the run takes the next one when a slot frees.

## What Changes

- **ADDED** `A queued cut waits while the line is at its cap`: the setting, what counts as in flight, the gate at the start and at each poll, the waiting cut's life in the run, and where it is shown.
- **MODIFIED** `A run cuts each queued brief in a station of its own`: a run takes a cut only while the line has room under its cap.
- **MODIFIED** `A settled brief is queued for a cut`: `conduct.py cut` names the cap in its line, and a run's close starts no run for a cut that only waits.
- **MODIFIED** `A cut halt is the plan's, answered by a re-plan and a rejoin`: `status` prints a waiting cut as `<id> · cut — waits: <n> in flight, cap <N>`.
- **Code:** `skills/mf-ship/scripts/conduct.py` reads the setting, counts versions in flight and gates the cuts; `skills/mf-ui/scripts/viewer.py` shows the state `queued`.
- **Docs:** [D47](../../../docs/decisions.md#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended) is amended, D84 is new ([D6](design.md#d6)), the principles' closed list gains `ship.toml`, and `mf-ship`'s flow, `status` and `cut` rows and `mf-plan`'s close say the run cuts the item when a slot frees.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: one requirement added for the cap, three modified where a run takes a cut, where `conduct.py cut` and the close speak of the queue, and where `status` prints a cut.

## Impact

- `skills/mf-ship/scripts/conduct.py` — `_cap`, `Run.in_flight`, `Run.room`, `Run.wait_cut`, `Run.unwait`, and the start, the poll, the close and `status` that use them.
- `skills/mf-ui/scripts/viewer.py` and `skills/mf-ui/page/index.html` — the state `queued` and the reason.
- `skills/mf-ship/SKILL.md` and `skills/mf-plan/SKILL.md` — the flow, the `status` and `cut` rows, the plan's close.
- `docs/decisions.md` and `docs/principles.md` — D47 amended, D84 added, `ship.toml` in the closed list.
- `tests/test_conduct.py` and `tests/test_viewer.py` — the cap's cases and the viewer's queue shape.

## Not in this change

- A count across the machine's lines, or a read of the CPU load.
- Pausing a version in flight.
- A new meaning for `after:` or `beside:`.
- A cap on versions already cut when a run starts.
- A config for anything but the cap.
