# Lighter catch-up — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The gate record
- [x] 2 — The stations
- [x] 3 — Replay
- [x] 4 — The by-rule catch-up
- [x] 5 — The commit body
- [ ] 6 — The record

## 1 — The gate record

- [x] 1.1 Write `skills/mf-converge/scripts/gate_run.py` and `tests/test_gate_run.py`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_gate_run.py` reports no failure, and `grep -n -- '--fresh' skills/mf-converge/scripts/gate_run.py` prints a line.

## 2 — The stations

- [x] 2.1 Gate through `gate_run.py` in `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-integrate/SKILL.md`
  and `skills/mf-release/SKILL.md`, the release's Step 4.3 with `--fresh` and precondition 1's time from the run's line; add their
  checks to `tests/test_skills.py`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_skills.py` reports no failure, and `grep -n 'gate_run.py --fresh' skills/mf-release/SKILL.md` prints a line.

## 3 — Replay

- [x] 3.1 Add `replay` to `skills/mf-integrate/scripts/integrate.py`; add `test_replay_reproduces_a_rule_settled_merge` and
  `test_replay_refuses_a_judged_merge` to `tests/test_integrate.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_integrate.py -k replay` reports `2 passed`.

## 4 — The by-rule catch-up

- [x] 4.1 Add the by-rule path to *Catch-up round* in `skills/mf-converge/SKILL.md`; add a `by-rule` mode to `tests/fake_worker.py`
  and a step releasing a version caught up by rule to `test_a_ready_version_ships_past_a_slow_one` in `tests/test_conduct.py`, per
  [D4](design.md#d4).
  Verify: `grep -n '## By rule' skills/mf-converge/SKILL.md` prints a line, and
  `uv run pytest -q tests/test_conduct.py -k ready_version_ships_past_a_slow_one` reports `1 passed`.

## 5 — The commit body

- [x] 5.1 Write Step 4.3's body lines, the test-fixed rule and *Why a station* in `skills/mf-integrate/SKILL.md`, and the integrate
  line in `README.md`, per [D5](design.md#d5).
  Verify: `grep -n 'integrate.py changelog' skills/mf-integrate/SKILL.md` prints a line, and `grep -n 'test fixed —' skills/mf-integrate/SKILL.md` prints a line.

## 6 — The record

- [ ] 6.1 Amend *The gate is run, never summarized* and *Nothing reads as clean by being absent* in `docs/principles.md`, D45 in
  `docs/decisions.md`, and *Known gaps* in `THREAT_MODEL.md`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_principles.py` reports no failure, and `grep -n 'gate_run' docs/principles.md` prints a line.
