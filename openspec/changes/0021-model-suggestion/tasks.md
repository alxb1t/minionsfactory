# 0021-model-suggestion — tasks

**In one line:** one phase — the section, the sentence in Step 11, the line in `## Never`. The text is in
[design.md](design.md#the-text-the-skill-gains).

## Progress

- [ ] 1 — The suggestion

## 1 — The suggestion

All three edits are in `skills/mf-cut-change/SKILL.md`.

- [ ] 1.1 **HALT CHECK** — Step 11 still reads as [design.md](design.md#step-11-before--after) quotes it. Verify:
  `grep -c 'Next: `/mf-build <change-id>`,' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.2 Add [the section](design.md#the-section) between `## Rules for the artifacts` and `## Never`
  ([D2](design.md#d2)–[D5](design.md#d5)). Verify: `grep -c '^## Suggesting models$' skills/mf-cut-change/SKILL.md`
  prints `1`.
- [ ] 1.3 Step 11: the after-text of [design.md](design.md#step-11-before--after) ([D1](design.md#d1)). Verify:
  `grep -c 'Then suggest models, as' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.4 `## Never`: add [the line](design.md#never-one-line-added). Verify:
  `grep -c 'Never write the model suggestion' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.5 The shared tables are untouched. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
