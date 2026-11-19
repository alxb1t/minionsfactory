---
bump: minor
version: 0.108
debt: [0109·S1]
---

# Status log

The staged write, the no-follow read and the status log each get one writer and one parser in the shared home, and no station's behaviour changes but the named fixes.

Reading map: [design](design.md) holds the modules, the differences between copies, the pin and the tests, [tasks](tasks.md) its phases.

## Why

The status log is written by `stamp.py` and by converge's `open_run`, and parsed by the conductor, converge, the viewer, the review metrics and `run.py`. Each copy disagrees with the others on where a run ends, what a mark is, what an event is and what a halt on the debt lock is.

The staged write stands in `stamp.py`, `bundle.py`, `debt_match.py`, `open_cards.py`, `skip_stub.py`, `gate_run.py` and `plan_check.py`, which disagree on a link at the target and on a `.tmp` left behind. The no-follow read stands in `stamp.py`, converge, the conductor and the viewer, each with its own bound, and a FIFO at the log hangs the conductor.

Card 0109·S1 names the cost: converge's stamps run in the conductor's process and write a change's folder by pathname, so a folder swapped for a link redirects them. One writer that holds a folder descriptor pays it.

## What Changes

- `skills/mflib/statefile.py` writes a staged file and reads a regular file, following no link; `skills/mflib/statuslog.py` writes and parses the status log; `skills/mflib/layout.py` names its path.
- `stamp.py` becomes a command over `statuslog.py`; converge's `open_run`, `stamp`, `Event`, `Run` and `latest`, and the conductor's readers and `_restamp`, take the module.
- The staged writes of `bundle.py`, `debt_match.py`, `open_cards.py`, `skip_stub.py`, `gate_run.py` and `plan_check.py` and the reads of converge, the conductor, the viewer and `skip_stub.py` take `statefile.py`.
- Each copy is fixed to one side: the staged file is removed on any failure; a link at the target is refused for the change-folder writers, `stamp.py`, `bundle.py`, `debt_match.py`, `open_cards.py` and `skip_stub.py`; a green gate whose record cannot be written is green and unrecorded; a run is its heading to the next heading; the conductor's readers follow no link; a detail's line breaks are flattened.
- The sixth structure rule gains a third kind: outside `skills/mflib/` no string constant equals `status_log.md` or contains `## Run`, unless `FORMAT_SITES` lists it.
- D78, D83 and D57 are amended, and the threat model, the map, the recipe and `mf-converge`'s text agree.
- Requirement *Converge keeps a status log* names the module as its writer, and adds the descriptor, the link, the bad byte and the flattened detail.
- Requirement *The skills run the repository's `make gate`* adds the green and unrecorded run.
- Requirement *The gate holds the structure rules* adds the format rule.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements named above.

## Impact

- New files: `skills/mflib/statefile.py`, `skills/mflib/statuslog.py` and the tests `tests/test_staged_writes.py`, `tests/test_log_reads.py`, `tests/test_status_log_copies.py`, `tests/test_statefile.py` and `tests/test_statuslog.py`.
- Edited scripts: `skills/mflib/layout.py`, `skills/mf-converge/scripts/stamp.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/scripts/bundle.py`, `skills/mf-converge/scripts/debt_match.py`, `skills/mf-converge/scripts/open_cards.py`, `skills/mf-converge/scripts/skip_stub.py`, `skills/mf-converge/scripts/gate_run.py`, `skills/mf-converge/scripts/plan_check.py`, `skills/mf-ship/scripts/conduct.py` and `skills/mf-ui/scripts/viewer.py`.
- Edited tests: `tests/test_layout.py`, `tests/test_stamp.py`, `tests/test_converge.py`, `tests/test_conduct.py`, `tests/test_gate_run.py`, `tests/test_plan_check.py`, `tests/test_skip_stub.py` and `tests/test_structure.py`.
- Edited record: `docs/decisions.md`, `docs/modules.md`, `docs/recipes.md`, `THREAT_MODEL.md`, `skills/mf-converge/SKILL.md`, and the sdd spec.
- Card 0109·S1 is paid; the release clears it from `debt:`.

## Not in this change

- The viewer's, the review metrics' and `scripts/metrics/run.py`'s parsers of the status log: when the readers of state formats are moved.
- The card, the findings files and the debt file: when their formats move, with their own module.
- The run log, the claim, the marks and the home files.
- The conductor's bound on a read of the log, which is card 0120·S4's: when the viewer's reads are designed with the conductor's.
- The survivors in converge's consumers of events: when the version that moves `go_on`, `cap_of`, `frozen_of` and `answered_amends` is planned, and the debt event's word when the debt's format moves.
- A refusal of a link at the gate's or the plan check's store: when evidence shows a planted link there.
