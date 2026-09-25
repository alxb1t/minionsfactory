# 0014-backlog-cards — tasks

**In one line:** one phase — the card lands in `mf-converge` and `mf-backlog-export` together, with a scan that
holds their fields equal. The text is in [design.md](design.md); tasks copy it.

## Progress

- [ ] 1 — Findings become cards

## 1 — Findings become cards

One phase, so no commit has converge writing cards the export flattens ([D7](design.md#d7)).

- [ ] 1.1 **HALT CHECK** — `mf-release` still blocks on any list line, so a card blocks ([D5](design.md#d5)).
  Verify: `grep -c 'no list line at all' skills/mf-release/SKILL.md` prints `1`.
- [ ] 1.2 Test first: in `tests/test_skills.py`, add a label reader beside `_section_ids`, the card scan and its twin,
  bound to `sdd:backlog-cards:fields-agree`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming `## The card`.
- [ ] 1.3 `skills/mf-converge/SKILL.md`: add `## The card` before `## Never` — the table, the writing limits and the
  example from [D1](design.md#d1--the-card). Verify: `grep -c "^| \*\*Why it's a problem\*\* |" skills/mf-converge/SKILL.md` prints `1`.
- [ ] 1.4 `mf-converge` Steps 3, 4, 5 and 6, per [D2–D3](design.md#d2d3--mf-converge-before--after). Verify:
  `grep -c -e 'the defect · the suggested fix' -e 'flips each addressed finding' skills/mf-converge/SKILL.md` prints `0`.
- [ ] 1.5 `skills/mf-backlog-export/SKILL.md`: add `## The card` before `## Never`, the same rows as 1.3.
  Verify: `grep -c "^| \*\*Still true?\*\* |" skills/mf-backlog-export/SKILL.md` prints `1`.
- [ ] 1.6 `mf-backlog-export` Steps 1, 2 and 3, per [D4](design.md#d4--mf-backlog-export-before--after). Verify:
  `grep -c -e 'all six of' -e 'Every \*\*list line\*\*' skills/mf-backlog-export/SKILL.md` prints `0`.
- [ ] 1.7 `mf-release` is not touched ([D5](design.md#d5)). Verify: `git diff main -- skills/mf-release/SKILL.md` prints nothing.
- [ ] 1.8 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
