---
bump: minor
version: v0.123
---

# Release script

The release's fixed steps become a script, `release.py`, run before and after the worker's fold; the worker no longer commits, tags or merges.

Reading map: [design](design.md) holds the script's decisions and the test cost, [tasks](tasks.md) its phases: `pre`, `finish`, a release run again, `merge` with the conductor, then the skill and the record.

## Why

A worker's release halted on a hand-step: a lock file left out of the commit, a tag move the sandbox denied, a stranded release that waited nine hours for a person's `git tag -d` and `git reset --hard`. Each step those halts came from is a fixed command over files and git. The build's close has been a script since [D87](../../../docs/decisions.md#d87--the-conductor-runs-the-gate); the release takes the same shape: script, worker, script.

## What Changes

- `skills/mf-release/scripts/release.py` is new. Its `pre` checks the preconditions, prints the tag and restores a dead release's derived work. Its `finish` takes the worker's files, archives, cuts the changelog, bumps the version file with its lock, collects the metrics, runs the fresh gate, commits once, tags and clears the paid cards. Its `merge` merges into the default branch.
- The release worker folds the spec delta, reads the capability preamble and corrects prose that states the version. It never commits, tags or merges.
- `finish` commits only what the worker left under `openspec/specs/` or in a Markdown file, and halts naming any other path.
- A tag of this release on an orphan commit is moved by the script; a tag origin or the default branch holds halts.
- A release commit the default branch moved past is dropped by the script, tag and commit, and the version goes back to integrate.
- `conduct.py` runs `pre`, the worker, `finish` and `merge` in the version's thread, then pushes and checks as today. A script's exit 1 is the version's halt.
- `mflib.runlog.release_died` reads the script's own log lines, so a death of `finish` or `merge` is a death of the release.
- A new mark, `release.flag`, holds the preamble's flag; its presence stops the script before the merge.
- A requirement is added: the release's fixed steps are `release.py`'s.
- A requirement is modified: *The release merges and pushes on the person's yes*, the merge now `release.py merge`'s.
- A requirement is modified: *The release assigns the version*, the tag now printed by `release.py pre`.
- A requirement is modified: *A re-run recovers what a dead station left*, the release's resume now the script's and a stranded release dropped.
- [D17](../../../docs/decisions.md#d17--the-release-verifies-folds-archives-tags-and-on-the-persons-yes-merges-and-pushes) and [D19](../../../docs/decisions.md#d19--one-version-line) are reworded; `release.flag` joins [D57](../../../docs/decisions.md#d57--one-folder-per-change-in-minions)'s marks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *The release's fixed steps are a script's* is added; *The release merges and pushes on the person's yes*, *The release assigns the version* and *A re-run recovers what a dead station left* are modified; see [the delta](specs/sdd/spec.md).

## Impact

- New: `skills/mf-release/scripts/release.py`, `tests/test_release.py`, `tests/fake_release.py`.
- Edited: `skills/mflib/runlog.py`, `tests/test_runlog.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-release/SKILL.md`, `tests/fake_worker.py`, `tests/test_conduct.py`, `tests/test_skills.py`, `scripts/corpus.toml`, `docs/modules.md`, `docs/decisions.md`.
- Read and written by `finish` in a target repository: `CHANGELOG.md`, `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, `metrics/catalogue.toml`, `metrics/changes/` and `openspec/specs/`.
- The worker's release work shrinks to the fold; the release commit and the merge lose the worker's `Co-Authored-By` trailer and carry `Change:` alone.

## Not in this change

- A plan halt of any class; the build's box tick, commit subjects and trailers, a card's `Amend:`, the fixer's `plan check left:` and the `Plan-text:` trailer.
- A script for the spec fold, or a check of the worker's fold against the delta: a hand-written value a script then refuses is the class this change removes.
- The attended push and the worktree's removal, which stay the skill's by hand.
- The rescue routes and the run-survives fixes of the earlier ship-fixes round; the refactoring's riders.
- A new metric for versions in flight over the cap.
