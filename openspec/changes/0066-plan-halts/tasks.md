# Plan halts — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The search script
- [x] 2 — The contract
- [x] 3 — The edited check
- [x] 4 — The cut
- [x] 5 — The record
- [ ] 6 — The calibration

## 1 — The search script

- [x] 1.1 Write `skills/mf-cut-change/scripts/verify_check.py` and `tests/test_verify_check.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_verify_check.py` reports no failure.

## 2 — The contract

- [x] 2.1 Add `I19` to the contract tables of `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`, and `I1 … I19` to the
  cut's diagram, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_skills.py -k same_contract_ids` reports `1 passed`.

## 3 — The edited check

- [x] 3.1 Add `--verify` and the comparison to `skills/mf-converge/scripts/gate_check.py`, and `test_an_edited_verify_halts` to
  `tests/test_gate_check.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_gate_check.py -k edited_verify_halts` reports `1 passed`.
- [x] 3.2 Run `gate_check.py --verify` before a phase's first `Verify:` in `skills/mf-build/SKILL.md` Step 2, per [D3](design.md#d3).
  Verify: `grep -n 'gate_check.py --verify' skills/mf-build/SKILL.md` prints a line.

## 4 — The cut

- [x] 4.1 In `skills/mf-cut-change/SKILL.md`: the standards in the reading list, the deletion grep in Step 3, `verify_check.py` in
  Step 8 in place of the gate, the plan review and its fixes, Step 9's decision doubt, the close-out's checks, and `I3` in both
  contract tables, per [D4](design.md#d4), [D5](design.md#d5) and [D6](design.md#d6).
  Verify: `grep -n 'verify_check.py' skills/mf-cut-change/SKILL.md` prints a line, and `grep -n 'make gate. is green' skills/mf-cut-change/SKILL.md` prints nothing.

## 5 — The record

- [x] 5.1 Amend D7, D40 and D46 in `docs/decisions.md`, and the self-check exception in `docs/principles.md`, per [D7](design.md#d7).
  Verify: `grep -n 'plan review' docs/decisions.md` prints a line, and `uv run pytest -q tests/test_principles.py` reports no failure.

## 6 — The calibration

- [ ] 6.1 Run the plan review as a fresh subagent on the three cuts [D8](design.md#d8) names, and record each doubt and its
  `path:line` in the phase's CHANGELOG entry, headed `plan review calibration`.
  Verify: `grep -n 'plan review calibration' CHANGELOG.md` prints a line.
