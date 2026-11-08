---
bump: minor
debt: [0091·R3, 0091·S3, 0088·S9, 0088·S10]
---

# Beside

A version that only shares files with another names it in `beside:` and builds in parallel from the default branch;
`after:` is kept for real code need, and nothing waits on `beside:`.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`after:` holds a dependent's build until its dependency releases. Most of 0081–0095's `after:` links only avoided file
overlap ([evidence](design.md#evidence)). Integrate already merges the default branch in, and the supervisor settles a text
conflict in spec or docs, so an overlap needs no wait. The plan has no word for "shares files, needs no code".

## What Changes

- **The brief** — a `## For the cut` head may carry `· beside: <ids>`, once; `brief_check.py` holds each id to `SLUG`.
- **The queue** — `conduct.py cut` takes `beside=<ids>` beside `after=<ids>`, each id a change id, and writes an optional
  `beside` key into the queue entry; an entry without it still reads.
- **The cut** — the cutter's prompt carries `beside=<ids>`, and `mf-cut-change` writes `beside: [<ids>]` into
  `proposal.md`'s frontmatter. Nothing at run time reads it: a `beside:` version is never `waiting`.
- **The plan** — the parallel-with check proposes `after:` only when one version needs a symbol, decision or requirement the
  other adds; file overlap alone gets `beside:`, the default. The close passes `beside=` to `conduct.py cut`.
- **The debt** — `brief_check.py` takes a models or Acceptance line only under a head (`0091·R3`), and reads an HTML
  heading and a heading with a non-ASCII letter as the checked heading they spell (`0091·S3`). `0088·S9` and `0088·S10` are
  already held at the base; this change lists them so the release clears them.
- **The record** — D69 in `docs/decisions.md`; `mf-ship`'s `cut` row.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A version names what it builds beside* — ADDED: `beside=` on the cut, `beside: [<ids>]` in the frontmatter, carried
    by the queue and the cutter's prompt; nothing waits on it.
  - *The plan station checks which versions can run side by side* — MODIFIED: `after:` only for real code need, else
    `beside:`.
  - *The plan station writes the brief after every round* — MODIFIED: a `## For the cut` item may name `beside` ids.
  - *A settled brief is queued for a cut* — MODIFIED: `beside=<ids>`, each a change id, kept in an optional entry key.
  - *A hard brief is checked before it is queued* — MODIFIED: the `beside:` field, a models or Acceptance line only under a
    head, and the heading rule's HTML and non-ASCII forms.
  - *The plan's close queues the cut on the person's yes* — MODIFIED: the command carries `beside=<ids>`.

## Impact

Changes `skills/mf-plan/scripts/brief_check.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-plan/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`, `tests/test_brief_check.py`,
`tests/test_conduct.py` and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Stacked builds — a dependent built on its dependency's built head — the next version, `stacked-builds`.
- A run-time reader of `beside:`: nothing orders, blocks or merges by it ([D4](design.md#d4)).
- A check that a `beside` id names an open version: a released one is still a true record ([D3](design.md#d3)).
- `conduct.py`'s `_headed`, which folds `design.md`'s `## Dependencies` heading on its own rule: the cut station's check,
  not the brief's.
