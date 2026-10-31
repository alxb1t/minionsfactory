---
bump: minor
backlog: [0040·R5]
---

# Ship resume

A halt that is not about the spec recovers with `/mf-ship` alone.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

A usage limit killed `0048-merge-queue`'s converge after a clean round. The worker exited 1, its check passed on clean
findings, and only the same limit stopped a release that had skipped the pickup and the backlog. Recovery took a
hand-written prompt. A dead integrate, release or conductor is worse: some need the person, and a merged, unpushed release
is silent. A halt with no decision in it should need no person.

## What Changes

- **A non-zero worker exit halts its version**, and the converge check needs `done`.
- **An unfinished converge run is stage `converge`**, and `mf-converge` continues it from its latest event.
- **A no-note open merge is stage `integrate`**, not a halt.
- **`mf-release` recovers itself** — it restores its own half-done fold, and re-enters at its merge after its tag.
- **`tasks.md` is read from `HEAD`.**
- **A run pushes what a release left**, and `status` reports it.
- **The claim holds the conductor's pid and worker groups**, so a killed conductor clears itself. Pays `0040·R5`.
- **A usage limit is named in the halt**, with its reset time.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station judges every station from disk* — MODIFIED: the exit code and `done`.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: what needs the person.
  - *Converge continues an unfinished run* — ADDED.
  - *A re-run recovers what a dead station left* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, the `mf-ship`, `mf-converge` and `mf-release` skills, `docs/decisions.md` and
`tests/test_conduct.py`. Amends D47.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Waiting out a usage limit; retries inside a run; a Codex usage limit's wording; `conduct.py stop`.
