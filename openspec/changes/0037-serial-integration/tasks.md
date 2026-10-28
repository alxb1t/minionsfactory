# Serial integration — tasks

Build the settled [design](design.md), one phase at a time. The station text and the script's rules are the
design's, word for word.

## Progress

- [ ] 1 — Write the integration script
- [ ] 2 — Write the station and correct converge and the release
- [ ] 3 — Record the integration

## 1 — Write the integration script

- [ ] 1.1 Write `skills/mf-integrate/scripts/integrate.py` per [D2](design.md#d2), its PEP 723 header pinning `>=3.12`.
  Verify: `uv run --script skills/mf-integrate/scripts/integrate.py --help` exits 0.
- [ ] 1.2 Write `tests/test_integrate.py` with the tests the [Tests](design.md#tests) table names for it.
  Verify: `uv run pytest -q tests/test_integrate.py` reports `4 passed`.

## 2 — Write the station and correct converge and the release

- [ ] 2.1 Write `skills/mf-integrate/SKILL.md` per [D1](design.md#d1) and [D4](design.md#d4), with `name: mf-integrate`.
  Verify: `grep -c '^name: mf-integrate$' skills/mf-integrate/SKILL.md` prints `1`, and `grep -c 'MERGE_HEAD' skills/mf-integrate/SKILL.md` prints at least `1`.
- [ ] 2.2 Rewrite the catch-up round's step 3 in `skills/mf-converge/SKILL.md`, per [D3](design.md#d3).
  Verify: `grep -c 'remerge-diff' skills/mf-converge/SKILL.md` prints at least `1`.
- [ ] 2.3 Rewrite release precondition 9's halt in `skills/mf-release/SKILL.md` to name the station, per [D1](design.md#d1).
  Verify: `grep -c '/mf-integrate' skills/mf-release/SKILL.md` prints at least `1`.
- [ ] 2.4 Add the station's pair to `_METRICS_SCRIPTS` and `test_mf_integrate_runs_its_script` in `tests/test_skills.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_skills.py -k mf_integrate_runs_its_script` reports `1 passed`.

## 3 — Record the integration

- [ ] 3.1 Add D45 and reword line 8 of `docs/decisions.md`, and extend the overview line, per [D5](design.md#d5).
  Verify: `grep -c '^### D45 · One station merges the default branch into the next version$' docs/decisions.md` prints `1`, and `grep -c 'An id in force is never reused or renumbered' docs/decisions.md` prints `1`.
- [ ] 3.2 Name `mf-integrate` in `AGENTS.md`'s skills line and `README.md`'s skill table, and add the move's steps to README's runbook, per [D5](design.md#d5).
  Verify: `grep -l 'mf-integrate' AGENTS.md README.md | wc -l` prints `2`, and `grep -c 'SKILLS_DIR=' README.md` prints at least `1`.
- [ ] 3.3 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `58 tests collected`.
