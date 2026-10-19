# 0026-test-cost — tasks

**In one line:** the rules for tests; consolidation per the design's table; review's test-cost and coverage-trace
passes; the release's `Gate:` line; D39 and the bootstrap template. The text is in [design.md](design.md). A wrapped
line is checked joined: `tr -s '\n ' ' ' < <file>` turns the file into one line.

## Progress

- [x] 1 — The rules for tests
- [x] 2 — Consolidation
- [x] 3 — The review passes
- [x] 4 — The clock
- [ ] 5 — The record

## 1 — The rules for tests

[The rules for tests](design.md#the-rules-for-tests) and [the build](design.md#the-build), word for word
([B1](design.md#b1)–[B3](design.md#b3)), then the shared-id scan.

- [x] 1.1 **HALT CHECK** — the build reads as design quotes it. Verify:
  `grep -c 'Test-first where there is logic: write the failing test for the phase.s acceptance,$' skills/mf-build/SKILL.md`
  and `grep -c 'showing the test fails when the guard is gone |$' skills/mf-build/SKILL.md` each print `1`.
- [x] 1.2 `skills/mf-build/SKILL.md`: `## Rules for tests` between `## Rules for what you write` and `## Prose rules`.
  Verify: `grep -c '^## Rules for tests$' skills/mf-build/SKILL.md` prints `1`, and
  `grep -c '^| \*\*T[1-6]\*\* |' skills/mf-build/SKILL.md` prints `6`.
- [x] 1.3 `skills/mf-build/SKILL.md`: Step 2 item 1, the item 6 paragraph, and `W5`. Verify:
  `tr -s '\n ' ' ' < skills/mf-build/SKILL.md | grep -c 'as a step in an existing test where `T2` finds one'`,
  `tr -s '\n ' ' ' < skills/mf-build/SKILL.md | grep -c 'Write to `W`, `T`, `P` and `C` below.'`,
  `grep -c 'new e2e: <test>' skills/mf-build/SKILL.md` and `grep -c 'placed per `T6` |$' skills/mf-build/SKILL.md`
  each print `1`.
- [x] 1.4 `skills/mf-cut-change/SKILL.md` and `skills/mf-converge/SKILL.md`: `## Rules for tests` where
  [the rules for tests](design.md#the-rules-for-tests) places each, with its opening. Verify:
  `grep -c '^| \*\*T[1-6]\*\* |' skills/mf-cut-change/SKILL.md skills/mf-converge/SKILL.md` prints
  `skills/mf-cut-change/SKILL.md:6` and `skills/mf-converge/SKILL.md:6`.
- [x] 1.5 `tests/test_skills.py`: the `owners` parameter on `_shared_label_problems` and `_shared_id_problems`, and
  the test-rule scan, its test and its planted twin, both named with `test_rule`, per
  [the scans](design.md#the-scans). Verify:
  `uv run pytest tests/test_skills.py -q -k test_rule | tail -1 | grep -c '^2 passed'` and
  `uv run pytest tests/test_skills.py -q -k 'contract or prose' | tail -1 | grep -c '^4 passed'` each print `1`.

## 2 — Consolidation

[Consolidation](design.md#consolidation) and the build's Step 2 item 3 and stop-condition 5 from
[the build](design.md#the-build), word for word ([B4](design.md#b4)–[B6](design.md#b6),
[B11](design.md#b11)), then the scan.

- [x] 2.1 **HALT CHECK** — the fix station and stop-condition 5 read as design quotes them. Verify:
  `grep -c 'loosened config, no deleted test. That is exactly what the review station checks for;' skills/mf-converge/SKILL.md`
  and `grep -c '^5. \*\*A gate that only goes green by weakening it\*\*' skills/mf-build/SKILL.md` each print `1`.
- [x] 2.2 `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`: `I16`; the cut's diagram and Step 8.
  Verify: `grep -c '^| \*\*I16\*\* |' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints
  `skills/mf-build/SKILL.md:1` and `skills/mf-cut-change/SKILL.md:1`, and
  `grep -c 'I1 … I16' skills/mf-cut-change/SKILL.md` and `grep -c 'I1`…`I16' skills/mf-cut-change/SKILL.md` each
  print `1`.
- [x] 2.3 `skills/mf-build/SKILL.md`: Step 2 item 3 and stop-condition 5. Verify:
  `tr -s '\n ' ' ' < skills/mf-build/SKILL.md | grep -c '(`I16`, `T5`) is not weakening; one outside the table is.'`
  and `tr -s '\n ' ' ' < skills/mf-build/SKILL.md | grep -c 'is the plan, not a weakening.'` each print `1`.
- [x] 2.4 `skills/mf-cut-change/SKILL.md`: `A8` after `A7`, and Step 6. Verify:
  `grep -c '^| \*\*A8\*\* |' skills/mf-cut-change/SKILL.md` and
  `grep -c 'always has `## Tests` (`A8`)' skills/mf-cut-change/SKILL.md` each print `1`.
- [x] 2.5 `skills/mf-converge/SKILL.md`: Step 6's fix-station bullets and *Never*. Verify:
  `grep -c 'never deletes or merges a test' skills/mf-converge/SKILL.md` prints `1`,
  `grep -c 'no deleted test' skills/mf-converge/SKILL.md` prints `0`, and
  `tr -s '\n ' ' ' < skills/mf-converge/SKILL.md | grep -c 'pastes the new or extended test.s failing run from before the fix'`
  and `tr -s '\n ' ' ' < skills/mf-converge/SKILL.md | grep -c 'names it is not a weakening.'` each print `1`.
- [x] 2.6 `docs/principles.md`: *Never weaken the gate to pass*, its bold paragraph and *Held by*. Verify:
  `tr -s '\n ' ' ' < docs/principles.md | grep -c 'is consolidation, not weakening.'` and
  `tr -s '\n ' ' ' < docs/principles.md | grep -c 'review.s coverage-trace pass, for consolidation;'` each print `1`.
- [x] 2.7 `tests/test_skills.py`: `_consolidation_problems`, its test and its planted twin, both named with
  `consolidation`. Verify:
  `uv run pytest tests/test_skills.py -q -k consolidation | tail -1 | grep -c '^2 passed'` prints `1`.

## 3 — The review passes

[The review passes](design.md#the-review-passes), word for word ([B7](design.md#b7)–[B9](design.md#b9)), then the
scan.

- [x] 3.1 **HALT CHECK** — the stale-claim pass reads as design quotes it. Verify:
  `grep -c '^\*\*Review runs a stale-claim pass after its engine.\*\*' skills/mf-converge/SKILL.md` and
  `grep -c '^- \*\*A review without its stale-claim pass is not clean.\*\*' skills/mf-converge/SKILL.md` each print
  `1`.
- [x] 3.2 `skills/mf-converge/SKILL.md`: Step 3's passes and its dispatch bullet. Verify:
  `grep -c '^\*\*Review runs a test-cost pass after its engine.\*\*' skills/mf-converge/SKILL.md`,
  `grep -c '^\*\*Review runs a coverage-trace pass when the freeze removes a test\*\*' skills/mf-converge/SKILL.md`
  and `tr -s '\n ' ' ' < skills/mf-converge/SKILL.md | grep -c 'whose `## Tests` section the coverage-trace pass reads'`
  each print `1`.
- [x] 3.3 `skills/mf-converge/SKILL.md`: Step 5's bullet and Step 7's sentence. Verify:
  `grep -c '^- \*\*A review without its test-cost pass or its coverage-trace pass is not clean.\*\*' skills/mf-converge/SKILL.md`
  and `tr -s '\n ' ' ' < skills/mf-converge/SKILL.md | grep -c 'so a fix.s new test is judged like the build.s.'`
  each print `1`.
- [x] 3.4 `tests/test_skills.py`: `_review_pass_problems`, its test and its planted twin, both named with
  `review_pass`. Verify:
  `uv run pytest tests/test_skills.py -q -k review_pass | tail -1 | grep -c '^2 passed'` prints `1`.

## 4 — The clock

[The clock](design.md#the-clock), word for word ([B10](design.md#b10), [B11](design.md#b11),
[B12](design.md#b12)), then the scan.

- [x] 4.1 **HALT CHECK** — the release and the principle read as design quotes them. Verify:
  `grep -c 'Write no new changelog prose here.' skills/mf-release/SKILL.md` and
  `tr -s '\n ' ' ' < docs/principles.md | grep -c 'Everything a station reads or writes is inside the repository it works on.'`
  each print `1`.
- [x] 4.2 `skills/mf-release/SKILL.md`: precondition 1, Step 4.1 and Step 6's sentences. Verify:
  `grep -c 'Gate: local' skills/mf-release/SKILL.md` prints `2`, and
  `grep -c 'Write no other changelog prose here.' skills/mf-release/SKILL.md`,
  `grep -cF 's=$(date +%s); make gate' skills/mf-release/SKILL.md`,
  `grep -c 'gh run list --branch <default-branch> --status success' skills/mf-release/SKILL.md` and
  `tr -s '\n ' ' ' < skills/mf-release/SKILL.md | grep -c 'exit code, and the `Gate:` line;'` each print `1`.
- [x] 4.3 `docs/principles.md`: *The repo reaches nothing outside itself*; `docs/decisions.md`: D17. Verify:
  `tr -s '\n ' ' ' < docs/principles.md | grep -c 'reads the remote.s CI runs, read-only'` and
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'cuts the changelog with one `Gate:` line'` each print `1`.
- [x] 4.4 `tests/test_skills.py`: `_gate_clock_problems`, its test and its planted twin, both named with
  `gate_clock`. Verify:
  `uv run pytest tests/test_skills.py -q -k gate_clock | tail -1 | grep -c '^2 passed'` prints `1`.

## 5 — The record

[The record](design.md#the-record), word for word ([B12](design.md#b12), [B13](design.md#b13)), then the scan.

- [ ] 5.1 `docs/decisions.md`: D39 after D37, and the map. Verify:
  `grep -c '^### D39 · A test is placed by its cost$' docs/decisions.md` and
  `grep -c 'D36, D37, D39' docs/decisions.md` each print `1`.
- [ ] 5.2 `skills/mf-bootstrap/templates/CLAUDE.md.tmpl`: `## Tests`, and the guardrail. Verify:
  `grep -c '^## Tests$' skills/mf-bootstrap/templates/CLAUDE.md.tmpl` and
  `tr -s '\n ' ' ' < skills/mf-bootstrap/templates/CLAUDE.md.tmpl | grep -c 'names it is not a weakening.'` each
  print `1`.
- [ ] 5.3 `tests/test_skills.py`: `_template_tests_problems`, its test and its planted twin, both named with
  `template_tests`. Verify:
  `uv run pytest tests/test_skills.py -q -k template_tests | tail -1 | grep -c '^2 passed'` prints `1`.
