---
bump: minor
---

# Marks

The marks of a change folder get one module, `skills/mflib/marks.py`, which names each mark once, writes its text and reads it, and the conductor, `integrate.py`, `converge.py` and `release.py` go through it.

Reading map: [design](design.md) holds the module, the one `head:` rule, the one read, the one write, the cases that pin today's behaviour and the rule; [tasks](tasks.md) holds its phases: the pin, the module, the stations, the fix, the rule and the record.

## Why

A mark is a small file in `.minions/changes/<change-id>/` that tells the run what a station did. Today the conductor and `release.py` each read, write and remove marks their own way. No two agree on a link, a pipe, a bad byte, a size bound or what a `head:` line is.

- A pipe at `cut.halt` hangs a cut's thread.
- `build.done` takes `head: HEAD` as a head.
- `stacked-on` is written through a hard link.

This is the marks' version of the architecture refactoring: the series' third home for a state format, after the run log with the claim and the models file.

## What Changes

A move first, then a fix, each behind a pin, as in the series (no assert changes in the move):

- **The pin.** The cases the marks' mutants left, the readings no rule states, and the cases of the run's loop, each green on the code as it stands.
- **The module.** `skills/mflib/marks.py` names `build.done`, `build.halt`, `build.closing`, `build.simplified`, `build-notes.md`, `stacked-on`, `cut.halt`, `cut.red`, `integrate.md`, `integrate.red`, `integrate.settled`, `integrate.resolved`, `release.held`, `release.flag`, `release.pre`, `release.discarded.<n>.patch`, `rescue.md`, `replan.mark`, `plan-check.txt` and `gate.red`, once each, with each text's writer and each parser or stand test.
- **The stations.** The conductor, `integrate.py`, `converge.py` and `release.py` read, test, write and remove a mark through the module. What a mark means to a run stays the conductor's.
- **The fix.** One `head:` rule; one read, whose broken stop mark halts its version and whose broken pass mark is absent; one staged write; `release.py`'s writes and removals under the folder's descriptor.
- **The rule and the record.** The format kind of the structure rule gains the marks' names; D57, the module map, the threat model and the requirements say what stands.

Requirements the delta touches, one line each:

- ADDED `One module writes and parses the marks of a change folder` — the module, its names, the `head:` rule, the read, the classes of mark, the write and the removal.
- MODIFIED `The gate holds the structure rules` — the format rule counts a mark's name by equality, its list `run.py` alone.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the module of the marks and the structure rule over their names.

## Impact

- New: `skills/mflib/marks.py`, `tests/test_marks.py`, `tests/test_mark_pins.py`.
- Edited: `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-release/scripts/release.py`, `tests/test_structure.py`, `tests/test_conduct.py` (the line by which a test reaches a name), `docs/modules.md`, `docs/decisions.md`, `THREAT_MODEL.md`.
- Behaviour that changes in the fix phase, each named in [design](design.md): a stop mark that stands as a link, a pipe, a folder, a file over the bound or a file with a bad byte halts its version; a `head:` is 7 to 40 lower-case hex digits on one line, else none; the marks the conductor writes in place are written staged; a failed write of `stacked-on` halts its version, not the run.

## Not in this change

- The thin command that writes the marks an agent writes by hand: it waits for the version whose prose first calls it.
- `run.py`'s own read of `build.done` and the viewer's borrow of the halt's reader: version 5e moves them, and the format rule lists `run.py`.
- The gate's Makefile read of `stacked-on`, `integrate.md`'s forms, the conductor's note and the agent's, and the parsers of `build.closing` and `integrate.resolved`, which have none.
- `build.discarded.patch`, which only the build agent writes.
- The home's folder opens refusing a link at `.minions`, the gate's record, `cut-notes.md`, `context.md`, a grant and a reservation: version `roots`, after this one.
- The debt cards: this version closes none.
