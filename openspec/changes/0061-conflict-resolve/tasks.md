# Conflict resolve — tasks

Build the settled [design](design.md), one phase at a time. The skill and decision text is the design's, word for word.

## Progress

- [x] 1 — The rule
- [ ] 2 — The record

## 1 — The rule

- [x] 1.1 Add *Resolve what both sides add* to `skills/mf-integrate/SKILL.md` Step 3, and name what is not additive in its
  semantic-conflict item, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -c 'Resolve what both sides add' skills/mf-integrate/SKILL.md` prints `1`.
- [x] 1.2 Add the `## Resolved` section to the note and the commit body to Step 4 in `skills/mf-integrate/SKILL.md`, per
  [D3](design.md#d3).
  Verify: `grep -c '## Resolved' skills/mf-integrate/SKILL.md` prints `1`.

## 2 — The record

- [ ] 2.1 Amend `skills/mf-integrate/SKILL.md`'s Never line and D45 in `docs/decisions.md`, and reword `0057·R4`'s sentences in
  both, per [D4](design.md#d4).
  Verify: `grep -c 'name each resolved hunk' skills/mf-integrate/SKILL.md` prints `1`,
  `grep -c 'resolves a hunk' docs/decisions.md` prints `1`, and
  `git grep -n "dependent's cut-only branch\|opens a dependent's merge" -- docs skills` prints nothing.
