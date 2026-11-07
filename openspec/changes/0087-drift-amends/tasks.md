# Drift amends — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — Converge halts on drift amends
- [x] 2 — The rescue's row and D15

## 1 — Converge halts on drift amends

- [x] 1.1 Add the amend card paragraph after the writing limits of `skills/mf-converge/references/worker.md`, per
  [D1](design.md#d1), and the kept `wontfix` to its Status diagram and its verify pass, per [D2](design.md#d2).
  Verify: `grep -n 'An amend card' skills/mf-converge/references/worker.md` prints a line.
- [x] 1.2 Rewrite the fixer's plan bullet in Step 6 of `skills/mf-converge/SKILL.md`, per [D3](design.md#d3), and add the
  *Amend cards first* paragraph above Step 9's lock, per [D4](design.md#d4).
  Verify: `grep -n 'Amend cards first' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.3 Edit the answered-halt paragraphs of *Resuming a run* in `skills/mf-converge/SKILL.md`, per [D5](design.md#d5), the
  words `findings files both still say` on one line.
  Verify: `grep -n 'findings files both still say' skills/mf-converge/SKILL.md` prints a line.
- [x] 1.4 Replace the taken-amend comment in `Run.rescue` and the grant comment in `Run.advance` of
  `skills/mf-ship/scripts/conduct.py`, as [D5](design.md#d5) quotes them.
  Verify: `grep -n 'converges afresh or catches up' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.5 Add `_drift_halt` and the `drift-halts` converge mode to `tests/fake_worker.py`, and
  `test_a_drift_amend_goes_on_by_rule` to `tests/test_conduct.py`, as the design's `## Tests` names them.
  Verify: `uv run pytest -q tests/test_conduct.py -k drift_amend_goes_on_by_rule` reports `1 passed`.

## 2 — The rescue's row and D15

- [x] 2.1 Rewrite the fix cell of the `amend needed` row in `skills/mf-rescue/SKILL.md`'s kind table, per [D6](design.md#d6).
  Verify: `grep -n 'open drift card' skills/mf-rescue/SKILL.md` prints a line.
- [x] 2.2 Rewrite D15's drift line and D16's debt sentence in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'save an amend card' docs/decisions.md` prints a line.
