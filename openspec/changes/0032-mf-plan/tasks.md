# mf-plan — tasks

Build the settled [design](design.md), one phase at a time. The station's sections, its commands and the brief's
template are the design's, word for word.

## Progress

- [x] 1 — Write the plan station
- [x] 2 — Make the cut halt on a light brief
- [ ] 3 — Record the station in the decisions, the principle and the docs

## 1 — Write the plan station

- [x] 1.1 Write `skills/mf-plan/SKILL.md` per [D1](design.md#d1) through [D5](design.md#d5), with `name: mf-plan` and a `description:` that says when to use it.
  Verify: `grep -c '^## ' skills/mf-plan/SKILL.md` prints `9`, and `grep -c '^name: mf-plan$' skills/mf-plan/SKILL.md` prints `1`.
- [x] 1.2 Add `test_mf_plan_holds_its_parameters_and_never` and `test_the_plan_scan_reports_a_missing_section` to `tests/test_skills.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_skills.py -k plan` reports `2 passed`.

## 2 — Make the cut halt on a light brief

- [x] 2.1 In `skills/mf-cut-change/SKILL.md`, add the light-brief halt to Step 2 and start the diagram at `mf-plan`, per [D5](design.md#d5) and [D6](design.md#d6).
  Verify: `grep -q 'depth=hard from=' skills/mf-cut-change/SKILL.md` exits 0, and `grep -c 'grilling ──▶ mf-cut-change' skills/mf-cut-change/SKILL.md` prints `0`.

## 3 — Record the station in the decisions, the principle and the docs

- [ ] 3.1 Rewrite D5 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: ``grep -c '^### D5 · A change is planned with `mf-plan` and written with the OpenSpec CLI$' docs/decisions.md`` prints `1`.
- [ ] 3.2 Rewrite the bold paragraph of *The repo reaches nothing outside itself* in `docs/principles.md`, per [D6](design.md#d6), closing `0030·R3`.
  Verify: ``grep -c "save \`mf-release\`'s read-only remote CI lookup" docs/principles.md`` prints `0`, and `grep -c "the operator's brief" docs/principles.md` prints `1`.
- [ ] 3.3 Name `mf-plan` in `AGENTS.md`'s skills line, and in `README.md`'s and `docs/README.md`'s diagrams and `README.md`'s skill table, per [D6](design.md#d6).
  Verify: `grep -l 'mf-plan' README.md docs/README.md | wc -l` prints `2`, `grep -c 'plan, bootstrap, cut, build, converge, release' AGENTS.md` prints `1`, and ``grep -c '`grilling`' README.md docs/README.md`` prints `README.md:0` and `docs/README.md:0`.
- [ ] 3.4 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `38 tests collected`.
