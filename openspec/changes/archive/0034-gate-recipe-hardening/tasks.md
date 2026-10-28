# Gate-recipe hardening — tasks

Build the settled [design](design.md), one phase at a time. The script's rules, exit codes and the stations'
text are the design's, word for word.

## Progress

- [x] 1 — Write the gate check
- [x] 2 — Make the stations call it
- [x] 3 — Quote removed lines, and claim only what the check reads

## 1 — Write the gate check

- [x] 1.1 **HALT CHECK** `make -pn -r gate` prints a `MAKEFILE_LIST :=` line, the premise of [D2](design.md#d2).
  Verify: `make -pn -r gate 2>/dev/null | grep -c '^MAKEFILE_LIST :='` prints at least `1`.
- [x] 1.2 Write `skills/mf-converge/scripts/gate_check.py` per [D1](design.md#d1) through [D4](design.md#d4), its PEP 723 header pinning `>=3.12`.
  Verify: `uv run --script skills/mf-converge/scripts/gate_check.py --help` exits 0.
- [x] 1.3 Write `tests/test_gate_check.py` with the tests the [Tests](design.md#tests) table names for it.
  Verify: `uv run pytest -q tests/test_gate_check.py` reports `11 passed`.
- [x] 1.4 MF's own gate passes the check on this branch, the recipe untouched.
  Verify: `uv run --script skills/mf-converge/scripts/gate_check.py --change 0034-gate-recipe-hardening --base 8d7383e` exits 0, and `ls .minions/gate-check 2>/dev/null | wc -l` prints `0`.

## 2 — Make the stations call it

- [x] 2.1 Replace converge's precondition 6 in `skills/mf-converge/SKILL.md` and the release's precondition 8 in `skills/mf-release/SKILL.md` with [D5](design.md#d5)'s text.
  Verify: `grep -c 'gate_check.py' skills/mf-converge/SKILL.md skills/mf-release/SKILL.md` prints `skills/mf-converge/SKILL.md:1` and `skills/mf-release/SKILL.md:1`, and `grep -c 'make -n -f - gate' skills/mf-converge/SKILL.md skills/mf-release/SKILL.md` prints `skills/mf-converge/SKILL.md:0` and `skills/mf-release/SKILL.md:0`.
- [x] 2.2 Name the script in the *Held by:* of *Never weaken the gate to pass* in `docs/principles.md`, per [D5](design.md#d5).
  Verify: `grep -c 'skills/mf-converge/scripts/gate_check.py' docs/principles.md` prints `1`.
- [x] 2.3 Turn `_METRICS_SCRIPTS` in `tests/test_skills.py` into a list of station and script pairs holding the gate check's, and extend the twin, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`, and `grep -c 'gate_check.py' tests/test_skills.py` prints at least `2`.
- [x] 2.4 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `49 tests collected`.

## 3 — Quote removed lines, and claim only what the check reads

- [x] 3.1 In `skills/mf-converge/scripts/gate_check.py`, make the planned scan halt on every non-blank gate-makefile line the branch removes, as it does for one it adds, and add `test_a_planned_change_that_removes_an_unquoted_line_halts` to `tests/test_gate_check.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_gate_check.py -k removes_an_unquoted_line` reports `1 passed`.
- [x] 3.2 Make exit 0 print `gate: no unplanned change` in place of `gate: the base's`, and the script's docstring claim no more, in `skills/mf-converge/scripts/gate_check.py` and `test_an_unchanged_gate_passes`, per [D4](design.md#d4) and [D7](design.md#d7).
  Verify: `grep -c "gate: the base's" skills/mf-converge/scripts/gate_check.py tests/test_gate_check.py` prints `skills/mf-converge/scripts/gate_check.py:0` and `tests/test_gate_check.py:0`, and `grep -c "gate is the base's" skills/mf-converge/scripts/gate_check.py` prints `0`.
- [x] 3.3 Retitle converge's precondition 6 and the release's precondition 8 **The gate changes only as the cut planned.**, per [D7](design.md#d7).
  Verify: `grep -c 'The gate changes only as the cut planned' skills/mf-converge/SKILL.md skills/mf-release/SKILL.md` prints `skills/mf-converge/SKILL.md:1` and `skills/mf-release/SKILL.md:1`.
- [x] 3.4 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `50 tests collected`.
