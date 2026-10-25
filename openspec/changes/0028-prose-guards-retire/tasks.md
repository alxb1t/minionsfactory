# Prose guards retire — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — Make a retirement legal
- [x] 2 — Retire the phrase scans
- [x] 3 — Delete the autonomous line from the repo

## 1 — Make a retirement legal

- [x] 1.1 Add D42 to `docs/decisions.md` after D41, as [D2](design.md#d2) writes it, and add `D42` to the overview
  line's *Repo conventions*.
  Verify: `grep -c '^### D42 · Skill prose is held by review, not by phrase scans$' docs/decisions.md` prints `1`.
- [x] 1.2 Extend `I16` in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`, and `T5` in those two and
  `skills/mf-converge/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -c 'or to the decision that retires it' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md skills/mf-converge/SKILL.md` prints `skills/mf-build/SKILL.md:2`,
  `skills/mf-cut-change/SKILL.md:2` and `skills/mf-converge/SKILL.md:1`.
- [x] 1.3 Rewrite the coverage-trace sentence in `skills/mf-converge/SKILL.md` Step 3 and the trace sentence in
  `skills/mf-converge/references/generic-review.md`, per [D2](design.md#d2).
  Verify: `grep -c 'carried by neither' skills/mf-converge/SKILL.md` prints `1`, and
  `grep -c 'retiring decision' skills/mf-converge/references/generic-review.md` prints `1`.
- [x] 1.4 Edit D39 in `docs/decisions.md` and *Never weaken the gate to pass* in `docs/principles.md`, per
  [D2](design.md#d2).
  Verify: `grep -c 'retired by a named decision' docs/decisions.md docs/principles.md` prints `docs/decisions.md:1` and
  `docs/principles.md:1`.
- [x] 1.5 Scope `W3` in `skills/mf-build/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -c 'in a claim of fact about code without a named test' skills/mf-build/SKILL.md` prints `1`.

## 2 — Retire the phrase scans

- [x] 2.1 Delete from `tests/test_skills.py` every test the [Tests](design.md#tests) table names, and each helper
  and constant only they use, per [D1](design.md#d1).
  Verify: `uv run pytest -q --collect-only | tail -1` prints `18 tests collected`; `uv run ruff check tests` exits 0.
- [x] 2.2 **HALT CHECK** The kept structural tests still pass, unchanged.
  Verify: `uv run pytest -q tests/test_skills.py -k 'contract_ids or prose_rule_ids or test_rule_ids or carries_the_card or template_tests_section or target_layout or role_references_resolve'` reports `7 passed`.
- [x] 2.3 Repoint the *Held by:* lines in `docs/principles.md`, per the table in [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_principles.py` exits 0, and `grep -c 'tests/test_skills.py::' docs/principles.md` prints `1`.
- [x] 2.4 Rewrite the Purpose line of `openspec/specs/sdd/spec.md`, per [D3](design.md#d3).
  Verify: `grep -c 'each proved by a scan over the skill text' openspec/specs/sdd/spec.md` prints `0`, and
  `grep -c 'A scan proves the structure a reader cannot check by eye' openspec/specs/sdd/spec.md` prints `1`.

## 3 — Delete the autonomous line from the repo

- [x] 3.1 Delete `## The autonomous line` to the end of `docs/decisions.md`, and its entry in the overview line,
  per [D4](design.md#d4).
  Verify: `grep -cE '^### D(2[4-9]|3[0-5]) ' docs/decisions.md` prints `0`, and `grep -c 'autonomous' docs/decisions.md` prints `0`.
- [x] 3.2 Delete `docs/autonomous.md` with `git rm`.
  Verify: `test ! -e docs/autonomous.md` exits 0.
- [x] 3.3 Edit `AGENTS.md`, `README.md`, `docs/README.md` and `docs/principles.md`, per [D4](design.md#d4).
  Verify: `git grep -n -i -E 'autonomous|D2[4-9]\b|D3[0-5]\b' -- AGENTS.md README.md docs` prints nothing.
