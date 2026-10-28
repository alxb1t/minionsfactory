# Release patches — tasks

Build the settled [design](design.md), one phase at a time. Each before → after is the design's, word for word.

## Progress

- [ ] 1 — Ship a patch as itself
- [ ] 2 — Retire a test only by a decision in force at the base
- [ ] 3 — Close the collector's gaps
- [ ] 4 — Fix the small text

## 1 — Ship a patch as itself

- [ ] 1.1 In `skills/mf-release/SKILL.md`, define `<tag>` at the version paragraph and use it wherever `<version>.0` stands, per [D1](design.md#d1).
  Verify: `grep -c '<version>\.0' skills/mf-release/SKILL.md` prints `1` — the definition's `<version>.0` for `vX.Y` — and `grep -c '<tag>' skills/mf-release/SKILL.md` prints at least `9`.
- [ ] 1.2 Give D19's diagram in `docs/decisions.md` its patch line, per [D1](design.md#d1).
  Verify: ``grep -c 'version: vX.Y.Z`  =  CHANGELOG `## \[X.Y.Z\]`' docs/decisions.md`` prints `1`.
- [ ] 1.3 Add the patch bullet to *The record* in `AGENTS.md`, per [D2](design.md#d2).
  Verify: ``grep -c '^- \*\*A patch\*\* (`vX.Y.Z`) fixes what the line already does' AGENTS.md`` prints `1`.

## 2 — Retire a test only by a decision in force at the base

- [ ] 2.1 Rewrite `I16` in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`, `T5` in those and `skills/mf-converge/SKILL.md`, and the coverage-trace row in `skills/mf-converge/SKILL.md`, per [D3](design.md#d3).
  Verify: `grep -c 'in force at the base' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md skills/mf-converge/SKILL.md` prints `skills/mf-build/SKILL.md:2`, `skills/mf-cut-change/SKILL.md:2` and `skills/mf-converge/SKILL.md:2`.
- [ ] 2.2 Rewrite D39 in `docs/decisions.md`, *Never weaken the gate to pass* in `docs/principles.md`, and the `## Tests` bullet of `skills/mf-bootstrap/templates/AGENTS.md.tmpl`, per [D3](design.md#d3).
  Verify: `grep -c 'named decision' docs/decisions.md docs/principles.md` prints `docs/decisions.md:0` and `docs/principles.md:0`, and `grep -c 'in force at the base that retires it' skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `1`.

## 3 — Close the collector's gaps

- [ ] 3.1 In `skills/mf-build/scripts/metrics.py`, make `_inside` refuse a `script` starting with `-`, and extend `test_a_broken_catalogue_exits_2_naming_the_entry` in `tests/test_metrics.py` with it, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_metrics.py -k broken_catalogue` reports `1 passed`, and `grep -c '"--quiet"' tests/test_metrics.py` prints `1`.
- [ ] 3.2 Give `_scrubbed` D4's pattern, and extend `test_a_failing_metric_is_unavailable_with_its_reason` with its `file://`, `(…)`, `HOME=…;` and trailing-`.` cases, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_metrics.py -k failing_metric` reports `1 passed`, and `grep -c 'file://' tests/test_metrics.py` prints at least `1`.

## 4 — Fix the small text

- [ ] 4.1 Name how `skills/mf-plan/SKILL.md`'s Step 1 finds the default branch, per [D5](design.md#d5).
  Verify: `grep -c 'git symbolic-ref --short refs/remotes/origin/HEAD' skills/mf-plan/SKILL.md` prints `1`.
- [ ] 4.2 Point `README.md`'s smoke-record link at the archived 0027 design, per [D5](design.md#d5).
  Verify: `grep -c 'openspec/changes/archive/0027-migrate-to-agents/design.md#smoke-evidence' README.md` prints `1`, and `uv run --script scripts/metrics/references.py` prints `0`.
