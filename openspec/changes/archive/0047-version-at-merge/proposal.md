---
version: v0.41
backlog: [0046·R3]
---

# Version at merge

A version's identity is its change id, and its number is assigned when it is released.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The cut fixes a version's number long before it ships, and the branch carries that number. Nothing needs it so early:
the change id is already unique, never renamed, and keys `.minions/`, the models file and the `Change:` trailer. A number
fixed at the cut also stands in the way of merging versions in the order they finish, since tags would land out of
order.

## What Changes

- **The branch is the change id** — `0048-x`, in `../0048-x`. Open versions are found by that shape, not by `v*`.
- **The cut takes a bump** — `bump=minor|patch`, written to `proposal.md` as `bump:`, and no number.
- **The release assigns the number** — `next_tag.py` prints the next tag, and the release writes `version:` into the
  proposal it archives.
- **`conduct.py` holds no number** — it reads a released version's tag from the branch tip.
- **`status` prints `<change-id> · <stage>`.**
- **A draft metrics page reads `unreleased`.**
- **`plan:` in a findings file is the change id**, and `0046·R3` is paid.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A skill infers the one active change* — MODIFIED: the branch is the change id.
  - *A cut makes a worktree when the repository declares one* — MODIFIED: the branch and the path are the change id.
  - *The integrate station merges the default branch into the next version* — MODIFIED: it reads branches named by a
    change id.
  - *The plan station checks the line's rules before its first round* — MODIFIED: the bump, not the version's form.
  - *The page classifies each metric against the previous release* — MODIFIED: a change with no number yet.
  - *A cut reserves its id and version against every open version branch* — REMOVED, replaced by *A cut reserves its id
    against every open version branch*.
  - *The release assigns the version* — ADDED.

## Impact

Adds `skills/mf-release/scripts/next_tag.py` and `tests/test_next_tag.py`. Changes `skills/mf-ship/scripts/conduct.py`,
`skills/mf-integrate/scripts/integrate.py`, `skills/mf-build/scripts/metrics.py`, the `mf-cut-change`, `mf-build`,
`mf-converge`, `mf-simplify`, `mf-release`, `mf-plan`, `mf-integrate` and `mf-ship` skills, `docs/decisions.md`,
`openspec/config.yaml`, `README.md`, and `tests/test_conduct.py`, `tests/test_integrate.py`, `tests/test_metrics.py`,
`tests/test_skills.py`. Amends D19, D20 and D44.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Merging in ready order; `after:` dependencies; a `major` bump; a ticket id. This change ships under the rules it replaces.
