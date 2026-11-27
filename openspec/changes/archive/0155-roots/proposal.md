---
bump: minor
version: v0.125
debt: [0136·S3, 0138·S2, 0140·S3, 0142·S2, 0152·S3]
---

# Roots — the home's folder opens refuse a link at `.minions`

Each folder the state modules open starts at the primary checkout and refuses a link at `.minions`; the riders and the threat model's sentences follow.

Reading map: [design](design.md) holds the roots, the riders and the tests, [tasks](tasks.md) holds the phases: the pin, the riders, the root and the record.

## Why

`statefile.folder` and `statefile.open_folder` follow their root, and the marks, the models file, the findings' stamp, the claim, the run log and the re-stamp pass `.minions`, `runs/` or `changes/` as that root. A link planted there redirects their writes: cards 0136·S3, 0138·S2, 0140·S3, 0142·S2 and 0152·S3 name this one mechanism. The threat model says "no link" in each of those places and is true only at each file's own name.

## What Changes

- Each folder open of the marks, the models file, the findings, the claim, the run log and the conductor's and converge's change folder passes the primary as root and `.minions` as a part, refused as a link.
- Riders: the gate's record, `cut-notes.md`, `context.md`, a grant and a cut reservation are read and written through no link; `layout` names `cuts/` and `grants/`; converge's write wrappers are one; converge names an open page through `layout.open_name`.
- `THREAT_MODEL.md` and `docs/recipes.md` say what is true; `docs/modules.md` rows name the new loads.
- Requirement added: A state module opens `.minions` from the primary and refuses a link there.
- Requirement added: The gate's record, the cut's notes and reservation and a grant follow no link.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` — requirements added, in [the delta](specs/sdd/spec.md).

## Impact

- Code: `skills/mflib/layout.py`, `skills/mflib/statefile.py`, `skills/mflib/marks.py`, `skills/mflib/modelsfile.py`, `skills/mflib/findings.py`, `skills/mflib/claim.py`, `skills/mflib/runlog.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/scripts/bundle.py`, `skills/mf-converge/scripts/open_cards.py`, `skills/mf-converge/scripts/gate_run.py`, `skills/mf-cut-change/scripts/cut_pre.py`, `skills/mf-cut-change/scripts/cut_context.py`, `skills/mf-cut-change/scripts/facts.py`; `skills/mf-release/scripts/release.py` is checked and not edited.
- Tests: `tests/test_statefile.py`, `tests/test_conduct.py`, `tests/conduct_load.py`, `tests/test_converge.py`, `tests/test_gate_run.py`, `tests/test_cut_context.py`, `tests/test_facts.py`, `tests/test_cut_pre.py`, and `tests/test_layout.py`.
- Docs: `THREAT_MODEL.md`, `docs/recipes.md`, `docs/modules.md`. The debt file is untouched: the release deletes the cards.

## Not in this change

- `release.py`'s `lexists` tests of `release.flag`, the findings files and `diff.patch`, and the debt's writes by plain path in `release.py` and `debt_match.py`: when a card repeats the mechanism.
- The opens whose root is the primary today — `_fresh_tmp`, `sandboxed`, `_scratch_folder`, `_fetch_npm` and converge's `_write_debt` — and `_hide_marks`, whose root is git's common folder.
- The conductor's reads of `grants/` and `cuts/`, which take their names from `layout` and keep their paths, and the `mkdir` of `write_record` and of `cut_context._mkdir`: their parents are followed until a card names them.
- The awake record's and the tracked data file's uncaught errors.
- The queue's entries, the briefs and the rejoin requests: when the queue's format moves into the home.
- A gate rule for the root: the sixth rule of `tests/test_structure.py` is untouched.
