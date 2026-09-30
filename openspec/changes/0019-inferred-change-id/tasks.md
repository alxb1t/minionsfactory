# 0019-inferred-change-id — tasks

**In one line:** one phase — the inference rule, the branch check and the echo, in each skill's `## Parameter`
section. The text is in [design.md](design.md#the--parameter-section-before--after).

## Progress

- [ ] 1 — The skills infer the one active change

## 1 — The skills infer the one active change

One phase: the scan holds `mf-build`, `mf-converge` and `mf-release` at once ([D4](design.md#d4)).

- [ ] 1.1 **HALT CHECK** — `mf-build`, `mf-converge` and `mf-release` still forbid inference. Verify:
  `grep -l 'Never infer it' skills/mf-build/SKILL.md skills/mf-converge/SKILL.md skills/mf-release/SKILL.md | wc -l` prints `3`.
- [ ] 1.2 Test first: in `tests/test_skills.py`, add the inferred-id scan and its twin, bound to
  `sdd:inferred-change-id:one-active-change`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming
  `skills/mf-build/SKILL.md`.
- [ ] 1.3 `skills/mf-build/SKILL.md` `## Parameter`: the after-text of [D1](design.md#d1)–[D3](design.md#d3), keeping
  its reason. Verify: `grep -c '(inferred:' skills/mf-build/SKILL.md` prints `1`.
- [ ] 1.4 `skills/mf-converge/SKILL.md` `## Parameter`: the same, and the [D3](design.md#d3) status-log line on
  `start`. Verify: `grep -c '(inferred:' skills/mf-converge/SKILL.md` prints `1` or more.
- [ ] 1.5 `skills/mf-release/SKILL.md` `## Parameter`: the same, keeping its reason. Verify:
  `grep -c '(inferred:' skills/mf-release/SKILL.md` prints `1`.
- [ ] 1.6 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
