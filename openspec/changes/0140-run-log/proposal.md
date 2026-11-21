---
bump: minor
debt: [0137·S1, 0137·S2]
---

# Run log

The run log and the claim each get one module that writes and parses them, and the conductor reads and writes both through it.

Reading map: [design](design.md) holds the decisions, the pin's cases and the test cost, [tasks](tasks.md) holds the phases: the pin, the modules, the stations, the fix and the rule with the record.

## Why

The run log has its writer and its readers in `conduct.py`, and the claim has its reads, writes and removals there too. None goes through `skills/mflib/statefile.py`: the append follows a link at the log's name, most readers raise on a bad byte, and a pipe at a log blocks the conductor. `wait` follows a worker-planted newer log and reads the whole file at each poll, which debt cards 0137·S1 and 0137·S2 name. The refactoring series gives each state format one module that writes and parses it, and this is the third format after the status log and the findings and debt files.

## What Changes

- `skills/mflib/runlog.py` is new: the log's title, event line and its one pattern, the event list, the order of logs, the newest log, the verify, the stop line, the readers of the release's death and of the rescue, and `wait`'s tail.
- `skills/mflib/claim.py` is new: the claim's entries, written and read.
- `skills/mflib/statefile.py` gains an append under a folder's descriptor and an offset on its bounded read.
- `skills/mf-ship/scripts/conduct.py` reads and writes the run log and the claim through the modules. It keeps the names the viewer borrows.
- The pin first: `tests/test_runlog.py` and `tests/test_claim.py` hold each case of the region's mutants, green on the code as it stands, and `tests/test_conduct.py` names its hand-typed logs as stamps.
- The fix, in a phase of its own: `sync` and `codex` are known events, the log's lock folder is gone, the stop line has one writer, every write holds the folder's descriptor, every read follows no link, and a claim that is no folder halts.
- The gate's format rule in `tests/test_structure.py` gains the run log's names. `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md`, `THREAT_MODEL.md` and `skills/mf-ship/SKILL.md` follow.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the delta below, each line one requirement.
  - ADDED *One module writes and parses the run log*: the title, the event line, the event list, the order, the verify, the stop line, and the reads that follow no link.
  - ADDED *One module writes and parses the claim*: its entries, its reads by a bound, and a claim that is no folder.
  - MODIFIED *A person can stop a run*: a claim that is no folder is a halt that kills nothing.
  - MODIFIED *`conduct.py wait` blocks until the run ends*: a poll reads a bounded span from its offset and prints whole lines.
  - MODIFIED *The gate holds the structure rules*: the format rule gains the run log's title and clock.

## Impact

- `skills/mf-ship/scripts/conduct.py`, `skills/mflib/statefile.py`, `skills/mflib/runlog.py`, `skills/mflib/claim.py`.
- `tests/test_conduct.py`, `tests/test_runlog.py`, `tests/test_claim.py`, `tests/test_statefile.py`, `tests/test_structure.py`.
- `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md`, `THREAT_MODEL.md`, `skills/mf-ship/SKILL.md`.
- Debt cards 0137·S1 and 0137·S2 are closed by the fix. The release deletes them; no task edits the debt file.

## Not in this change

- The viewer's and the metrics' readers of the run log and the claim stay as they are, listed on the gate's rule until the readers' version.
- The kill of a group, `ps` and what a stale claim means to a run stay the conductor's.
- The run directory's generic entries, the models file and the marks of a change folder: their own versions.
- A worker's instant between its start and its claim entry, a converge by hand whose own log becomes the newest beside a live run, and a held event's clock, which its flush sets.
- The export of a version's portable record.
