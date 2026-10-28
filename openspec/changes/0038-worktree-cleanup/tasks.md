# Worktree cleanup — tasks

Build the settled [design](design.md), one phase at a time. The station text is the design's, word for word.

## Progress

- [x] 1 — Name and remove the worktree in the release
- [ ] 2 — Correct the records

## 1 — Name and remove the worktree in the release

- [x] 1.1 Add [D1](design.md#d1)'s paragraph after Step 5's ask in `skills/mf-release/SKILL.md`.
  Verify: `grep -c 'goes too, with:' skills/mf-release/SKILL.md` prints `1`, and `grep -c 'exclude-standard --directory' skills/mf-release/SKILL.md` prints `1`.
- [x] 1.2 Replace item 6 of Step 5 in `skills/mf-release/SKILL.md` with [D1](design.md#d1)'s after text.
  Verify: `grep -c 'Any ignored path' skills/mf-release/SKILL.md` prints `0`, and `grep -c 'when the ask said it goes' skills/mf-release/SKILL.md` prints `1`.

## 2 — Correct the records

- [ ] 2.1 Rename the primary in `README.md`'s tree and runbook, per [D2](design.md#d2).
  Verify: `grep -cE 'main/|/main' README.md` prints `0`, and `grep -c '<repo>/<repo>' README.md` prints `1`.
- [ ] 2.2 Correct `openspec/changes/archive/0034-gate-recipe-hardening/proposal.md:8-9` and the `[0.31.2]` phase-1 entry in `CHANGELOG.md`, per [D3](design.md#d3).
  Verify: `grep -c 'every route' openspec/changes/archive/0034-gate-recipe-hardening/proposal.md` prints `0`, and `grep -c 'certify its own weakened gate' CHANGELOG.md` prints `0`.
