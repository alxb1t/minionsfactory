# 0013-how-the-builder-writes — tasks

**In one line:** three phases — the shared prose rules, then the truth and comment rules in `mf-build`, then the
planning rules in `mf-cut-change`. The text of every rule is in [design.md](design.md); tasks copy it.

## Progress

- [x] 1 — The shared prose rules
- [ ] 2 — `mf-build`'s truth and comment rules
- [ ] 3 — `mf-cut-change`'s planning rules

## 1 — The shared prose rules

`P` first, because `W4`, `C4` and `C10` cite it ([D9](design.md#d9)). The split is
[D3](design.md#d3--the-split-of-the-16-rows); the counts text is [D4](design.md#d4--the-text-that-changes-with-the-counts-rule).

- [x] 1.1 **HALT CHECK** — `mf-cut-change`'s style table still holds the rows D3 maps. Verify:
  `sed -n '/^## How the artifacts read/,/^## Never/p' skills/mf-cut-change/SKILL.md | grep -c '^| [0-9]* |'` prints `16`.
- [x] 1.2 Test first: in `tests/test_skills.py`, the section reader takes a heading and an id letter; add the prose
  scan and its twin, bound to `sdd:prose-rules:ids-agree`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming `## Prose rules`.
- [x] 1.3 `skills/mf-build/SKILL.md`: add `## Prose rules` after *Stop-conditions* — D3's `P` table, then D6's scope
  paragraph. Verify: `grep -c '^| \*\*P[0-9]*\*\* |' skills/mf-build/SKILL.md` prints `13`.
- [x] 1.4 `skills/mf-cut-change/SKILL.md`: `## How the artifacts read` becomes `## Prose rules` (the same `P` table, then
  the example task) and `## Rules for the artifacts` (`A1`…`A3`). Verify: `grep -c -e '^| \*\*P[0-9]*\*\* |' -e '^| \*\*A[0-9]*\*\* |' skills/mf-cut-change/SKILL.md` prints `16`.
- [x] 1.5 `I6`, in both skills, and the example task's *after* line, per D4. Verify:
  `grep -c -e 'any count shows the command' -e 'Seed the seven' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints `0` for both.
- [x] 1.6 `mf-cut-change` Step 6's link and Step 8's check list, per [D7](design.md#d7). Verify:
  `grep -c -e 'How the artifacts read' -e 'style rules 10, 13, 14' skills/mf-cut-change/SKILL.md` prints `0`.
- [x] 1.7 `mf-build` Step 2, item 4: the CHANGELOG entry follows `P` ([D6](design.md#d6--where-mf-build-states-the-scope)).
  Verify: `sed -n '/^## Step 2/,/^## Step 3/p' skills/mf-build/SKILL.md | grep -c 'following `P`'` prints `1`.
- [x] 1.8 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 2 — `mf-build`'s truth and comment rules

All edits are in `skills/mf-build/SKILL.md`: `W` is [D1](design.md#d1--the-w-table-as-mf-build-carries-it), `C` is
[D5](design.md#d5--the-c-table-as-mf-build-carries-it), the commit-body list is [D2](design.md#d2--the-retirement-list-in-the-commit-body).

- [ ] 2.1 Add `## Rules for what you write` before `## Prose rules`: D1's `W` table and its closing line.
  Verify: `grep -c '^| \*\*W[0-9]*\*\* |' skills/mf-build/SKILL.md` prints `6`.
- [ ] 2.2 Add `## Rules for code comments` after `## Prose rules`: D5's `C` table, then its before → after example.
  Verify: `grep -c '^| \*\*C[0-9]*\*\* |' skills/mf-build/SKILL.md` prints `12`.
- [ ] 2.3 Step 2: item 1 ends "Write to `W`, `P` and `C` below."; item 6 names `W2`'s list in D2's shape. Verify:
  `sed -n '/^## Step 2/,/^## Step 3/p' skills/mf-build/SKILL.md | grep -c -e 'Write to `W`, `P` and `C`' -e 'retired:'` prints `2`.
- [ ] 2.4 The rule sections sit between *Stop-conditions* and *What you must NOT do*, in the order `W`, `P`, `C`.
  Verify: `grep '^## ' skills/mf-build/SKILL.md | tail -5` prints those five headings in that order.

## 3 — `mf-cut-change`'s planning rules

- [ ] 3.1 `skills/mf-cut-change/SKILL.md`: add `A4`…`A6` to `## Rules for the artifacts`, per
  [D7](design.md#d7--the-a-table-as-mf-cut-change-carries-it). Verify: `grep -c '^| \*\*A[0-9]*\*\* |' skills/mf-cut-change/SKILL.md` prints `6`.
