# Release on a moved base — tasks

Build the settled [design](design.md), one phase at a time. The station text is the design's, word for word.

## Progress

- [x] 1 — Check the base before the release tags
- [ ] 2 — Name the default branch in every station

## 1 — Check the base before the release tags

- [x] 1.1 Append precondition 9 to Step 1 of `skills/mf-release/SKILL.md`, per [D1](design.md#d1).
  Verify: `grep -c '^9\. \*\*The base has not moved' skills/mf-release/SKILL.md` prints `1`, and `grep -c 'git merge <default-branch>' skills/mf-release/SKILL.md` prints at least `1`.
- [x] 1.2 Give Step 5.1 of `skills/mf-release/SKILL.md` its recovery, per [D2](design.md#d2).
  Verify: `grep -c 'git tag -d <tag>' skills/mf-release/SKILL.md` prints `1`.

## 2 — Name the default branch in every station

- [ ] 2.1 Add [D3](design.md#d3)'s line to `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-cut-change/SKILL.md` and `skills/mf-release/SKILL.md`, and drop converge's "usually `main`".
  Verify: `grep -l 'git symbolic-ref --short refs/remotes/origin/HEAD' skills/mf-build/SKILL.md skills/mf-converge/SKILL.md skills/mf-cut-change/SKILL.md skills/mf-release/SKILL.md | wc -l` prints `4`, and ``grep -c 'usually `main`' skills/mf-converge/SKILL.md`` prints `0`.
