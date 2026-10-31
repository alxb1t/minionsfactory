---
version: v0.40
backlog: [0040·R6]
---

# Ship halts

A halt in one version stops that version, not the `mf-ship` run, and a merge never runs a version out of rounds.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The runs of `0044-simplify` and `0045-review-metrics` failed the same way: one version's trouble cost the other.

- `0045` halted at build, and `0044`, build passed, never started converge. `advance` loops on a list every version
  shares.
- `0045` was clean at round 2, an optional pickup took round 3, and `0044` then moved `main`. The catch-up for the
  integrate merge would have been round 4, so a one-file CHANGELOG merge halted a converged version. Many runs end at
  round 3, so a parallel run will meet this again.

## What Changes

- **Per-version halts** — in build and converge, a halt stops only its version. A failed probe and a conductor crash
  still stop the run.
- **Cut order at the merge** — a halt holds every version behind it, named in the closing line and the report.
- **A halt is logged when it happens**, and a run with a halt closes on one line naming what halted, what is held and
  what released.
- **`report` prints every halt**, and marks a held version.
- **A catch-up over merges only has its own count** — one judge round and at most one fix round. The main cap stays
  three, and a late non-merge commit stays under it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The release ships only a reviewed head* — MODIFIED: the catch-up's count.
  - *The ship station takes cut versions to the default branch* — MODIFIED: a denial and a failed check halt a version.
  - *The ship station judges every station from disk* — MODIFIED: a failed check halts the version.
  - *A halt stops the ship run, and a re-run resumes* — REMOVED, replaced by *A halt stops its version, and a re-run
    resumes*.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md`,
`docs/decisions.md`, `docs/principles.md` and `tests/test_conduct.py`. Amends D47.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Merging in ready order, version numbers assigned at the merge, and declared dependencies between versions; retries;
`conduct.py stop`; a deny list parsed from argv.
