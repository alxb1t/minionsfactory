---
bump: minor
backlog: [0057·R4]
---

# Conflict resolve

`mf-integrate` resolves a conflict where both sides add and neither changes the other's intent, names each resolution in the
merge commit, and still hands every other conflict to the person.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

MF's own parallel run, 2026-11-03: `0057-run-fixes`' integrate halted on two hunks, a tuple both sides edited and a paragraph
both sides extended. The note's proposal was right for each, and a person was needed only to stage it. Both hunks overlapped
on a line, so git could not merge them, but each side's change was additive as list items and sentences.

## What Changes

- **The integrator resolves an additive hunk**: one whose union keeps every addition and every removal of both sides and
  changes nothing else, at the level its edits separate, lines, list items or sentences.
- **A merged test the union breaks is fixed** when the fix keeps both sides' intent.
- **The merge commit names each resolved hunk**: the file, both sides' intent, the union. The note is still written.
- **Every other conflict halts as today**, with the merge open: one side editing what the other removed, two values for one
  thing, designs that disagree, a choice between behaviours.
- **`conduct.py`'s own merge into a cut-only branch is unchanged**, and the record says which cut-only branches it merges
  (`0057·R4`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The integrate station merges the default branch into the next version* — MODIFIED: it resolves an additive hunk and
    names it in the merge commit.
  - *A semantic conflict is handed to the person with the merge open* — MODIFIED: only a conflict that is not additive.

## Impact

Changes `skills/mf-integrate/SKILL.md` and `docs/decisions.md`. Amends D45.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

`conduct.py`'s own `merge_in` resolving anything; a deterministic resolver in `integrate.py`; a test over the rule's wording,
which D42 rules out.
