---
bump: minor
version: 0.113
debt: [0111·S1]
---

# Models

One module, `skills/mflib/modelsfile.py`, writes and parses a change's `models.toml`; the conductor and `brief_check.py` go through it, and the copies of its rules that disagree are made to agree.

Reading map: [design](design.md) holds the module, the one read and the cases it is pinned by, [tasks](tasks.md) its phases: the pin, the module, the move, the fix and the record.

## Why

The models file has two writers and prose, and one parser in the conductor whose reads differ by caller. A bad byte in it halts the whole run where bad TOML halts one version, a link or a pipe reads as no table at all, and the token rule covers some tables and leaves the rest to reach a worker's argv. Card 0111·S1 is that last gap: a `[build]` model that is no token reaches a cleanup that deletes a folder.

It is the next format to get one module, after the status log, the findings, the debt and the run log.

## What Changes

- `skills/mflib/modelsfile.py` is born: the map of the file's tables and keys, the text `brief_check.py --models` prints, the parser, each key's reader, the token rule, the hash and the write.
- `brief_check.py` and `conduct.py` go through it; the conductor keeps each station's defaults and its child run of `brief_check.py`. A phase pins the code first, a phase moves it with no assert changed, and a phase of its own fixes the disagreements.
- One read: no link, no block, a regular file, 65,536 bytes, decoded strictly. A broken file halts its version alone, and `conduct.py status` names it.
- One map and one token rule: `[converge.review]` and `[converge.security]` are read no more; every table's words are checked at the read, which pays 0111·S1.
- The write is the staged write, refusing a link. `brief_check.py --models <brief> <slug> --write <change-id>` writes the file for the attended cut.
- `skills/mflib/statefile.py` gains a folder open that makes nothing; the claim's own open moves onto it.
- The record agrees: D57, D77 and D41, the threat model, the module map and the recipe.

Requirements:

- ADDED **One module writes and parses the models file**: the module, the map, the token rule, the one read, the broken file's scopes, the write and `--write`.
- MODIFIED **A run moves the old findings files to the checkers' names**: the old worker tables are read no more.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: one added requirement and one modified.

## Impact

- New: `skills/mflib/modelsfile.py`, `tests/test_modelsfile.py`.
- Edited: `skills/mflib/statefile.py`, `skills/mflib/layout.py`, `skills/mflib/claim.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-plan/scripts/brief_check.py`, `skills/mf-ship/SKILL.md`.
- Tests re-pointed or turned: `tests/test_conduct.py`, `tests/test_claim.py`, `tests/test_statefile.py`, `tests/test_layout.py`, `tests/test_brief_check.py`.
- Record: `docs/decisions.md`, `docs/modules.md`, `docs/recipes.md`, `THREAT_MODEL.md`, and the spec through the delta of this change.

## Not in this change

- The models line's grammar and `brief_check.py`'s parse of it: the brief module's version.
- The prose that writes the file by hand, `mf-cut-change`'s and `mf-release`'s: the release and preamble scripts' version. No prose calls `--write`.
- A format kind for the models file in the gate's rule: its table names are common words. A round-trip case holds the one map instead.
- The conductor's station map and its defaults: the supervisor's, the checkers' and the executor fallbacks.
- A byte bound on the other worker files, debt card 0120·S4.
- The marks of a change folder: the next region's version.
- Debt cards 0140·S1 and 0140·S3: neither trigger is a models site.
