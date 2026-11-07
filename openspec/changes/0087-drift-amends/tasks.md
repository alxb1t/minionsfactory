# Drift amends — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — Converge halts on drift amends
- [x] 2 — The rescue's row and D15
- [x] 3 — Amend cards keyed on the card, the rescue's amend read

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
- [x] 1.5 Add `test_a_drift_amend_goes_on_by_rule` to `tests/test_conduct.py`, unmarked, a direct call of
  `conduct["_answered"]` on a Step 9 `amend needed — R6` halt with both findings files clean at its head, as the design's
  `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k drift_amend_goes_on_by_rule` reports `1 passed`.

## 2 — The rescue's row and D15

- [x] 2.1 Rewrite the fix cell of the `amend needed` row in `skills/mf-rescue/SKILL.md`'s kind table, per [D6](design.md#d6).
  Verify: `grep -n 'open drift card' skills/mf-rescue/SKILL.md` prints a line.
- [x] 2.2 Rewrite D15's drift line and D16's debt sentence in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -n 'save an amend card' docs/decisions.md` prints a line.

## 3 — Amend cards keyed on the card, the rescue's amend read

- [x] 3.1 Rewrite the last sentence of *Amend cards first* in Step 9 of `skills/mf-converge/SKILL.md` to the card-keyed rule,
  per [D4](design.md#d4), the words `already stands in the debt` on one line.
  Verify: `grep -n 'already stands in the debt' skills/mf-converge/SKILL.md` prints a line.
- [x] 3.2 Add the rescue's amend to the amends paragraph of *Resuming a run* in `skills/mf-converge/SKILL.md`, per
  [D5](design.md#d5), the words `never by rule` on one line.
  Verify: `grep -n 'never by rule' skills/mf-converge/SKILL.md` prints a line.
- [x] 3.3 Send a selection holding a rescue's amend past By rule in *Catch-up round* item 4 of
  `skills/mf-converge/SKILL.md`, per [D5](design.md#d5), the words `skips By rule` on one line.
  Verify: `grep -n 'skips By rule' skills/mf-converge/SKILL.md` prints a line.
- [x] 3.4 Put the rescue's amend past the halt's head in `test_a_drift_amend_goes_on_by_rule` of `tests/test_conduct.py`,
  one `docs(<id>): amend the change directory` commit of `design.md` alone carrying a `Rescue: R6` trailer, as the design's
  `## Tests` names it.
  Verify: `uv run pytest -q tests/test_conduct.py -k drift_amend_goes_on_by_rule` reports `1 passed`.
- [x] 3.5 Assert in `test_a_drift_amend_goes_on_by_rule` of `tests/test_conduct.py` that `conduct["_answered"]` returns
  true on the halt with the rescue's amend past its head, and false at the head itself, with no assertion on a fake's
  output, as the design's `## Tests` names them.
  Verify: `uv run pytest -q tests/test_conduct.py -k drift_amend_goes_on_by_rule` reports `1 passed`.
- [x] 3.6 Rework `test_a_drift_amend_goes_on_by_rule` in `tests/test_conduct.py` to the design's `## Tests`: drop its
  `slow` mark, its fake-worker run and its assertions on the fake's `## Run 2 — d · catch-up` log, and call
  `conduct["_answered"]` directly, per 1.5, 3.4 and 3.5. In `tests/fake_worker.py`, drop this change's `drift-halts` mode with
  `_drift_halt`, and its rescue-amend branch with `_write_catch_up` and `_rescued`, each only if no other test uses it.
  Verify: `grep -L -F 'startswith("# t\n\n## Run 2 — d · catch-up' tests/test_conduct.py` prints `tests/test_conduct.py`.
