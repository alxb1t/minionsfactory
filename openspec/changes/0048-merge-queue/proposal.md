---
bump: minor
---

# Merge queue

The first version ready is the first merged, and a declared dependency is the only order.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

`mf-ship` merges in cut order, so a fast version waits for a slow one, and a halted version holds every version behind
it. Nothing needs that order: versions cut from one base cannot use each other's code, the integrate merge settles the
CHANGELOG and the decision ids, and a number is now assigned at the release. Where one version does need another, the line
has no way to say so.

## What Changes

- **One thread per version** — build, converge, then a lock around integrate, catch-up and release. A version takes the
  lock when it is ready.
- **`after: [<ids>]`** — the cut takes `after=<id>[,<id>]`, and a dependent starts only once each id has released.
- **`conduct.py` merges the default branch into a cut-only dependent**, with no agent: the merge cannot conflict in git,
  and `integrate.py delta` holds a requirement both sides changed open for the person.
- **`status` shows `waiting`, and a halted dependency blocks** — `blocked — by <id>`, down a chain. `held` goes.
- **`mf-integrate` takes a `change-id`**; run bare, it picks the lowest-id ready version, and every hand-over names the
  version. "Never skip ahead" goes.
- **`I17` replaces release precondition 10** — `mf-build` and `mf-release` halt unless each `after:` id is in `HEAD`.
- **`I10` counts a name an `after:` change's design adds.**
- **`mf-plan`'s *parallel with* warns**, and proposes no order.
- **The cut's last line is `Next: /mf-ship, in the primary.`** in a repo that declares `Worktrees:`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A cut reserves its id against every open version branch* — MODIFIED: no ship order.
  - *The plan station checks which versions can run side by side* — MODIFIED: it warns.
  - *The integrate station merges the default branch into the next version* — MODIFIED: a named version, or the lowest
    ready.
  - *The ship station takes cut versions to the default branch* — MODIFIED: the order they are ready.
  - *A halt stops its version, and a re-run resumes* — REMOVED, replaced by *A halt stops only its version, and a re-run
    resumes*: blocked replaces held.
  - *A version declares what it builds on* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`, the `mf-cut-change`, `mf-build`,
`mf-integrate`, `mf-release`, `mf-plan` and `mf-ship` skills, `docs/decisions.md`, `tests/test_conduct.py` and
`tests/test_integrate.py`. Amends D20, D44, D45 and D47.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

An order among versions waiting for the lock; a `major` bump; `conduct.py stop`; removing the high tier.
