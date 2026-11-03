# Loopback removal — tasks

Build the settled [design](design.md), one phase at a time. The decision, threat-model and skill text is the design's, word
for word.

## Progress

- [x] 1 — The code
- [ ] 2 — The drill
- [ ] 3 — The record

## 1 — The code

- [x] 1.1 Remove the reader, the setting, the Codex refusal, the listeners and the event from
  `skills/mf-ship/scripts/conduct.py`, and halt on a declared line, per [D1](design.md#d1) and [D2](design.md#d2); edit
  `test_the_plan_is_read_once` and `test_a_claude_worker_starts_in_the_sandbox`.
  Verify: `grep -c -E 'allowLocalBinding|_loopback_listeners|NEEDS_CLAUDE' skills/mf-ship/scripts/conduct.py` prints `0`, and
  `uv run pytest -q tests/test_conduct.py -k 'plan_is_read_once or starts_in_the_sandbox'` reports `2 passed`.

## 2 — The drill

- [ ] 2.1 Remove the loopback row from `tests/escape_drill.py`, and reword the comment in `tests/test_escape_drill.py`, per
  [D3](design.md#d3).
  Verify: `grep -c -E 'LOOPBACK_PROMPT|def _loopback' tests/escape_drill.py` prints `0`, `uv run --script tests/escape_drill.py --help`
  exits 0, and `uv run pytest -q tests/test_escape_drill.py` passes.

## 3 — The record

- [ ] 3.1 Amend D51 in `docs/decisions.md`, and edit `THREAT_MODEL.md` and `skills/mf-ship/SKILL.md` Step 3, per
  [D4](design.md#d4).
  Verify: `git grep -c 'Ship loopback' -- docs/decisions.md THREAT_MODEL.md skills/mf-ship/SKILL.md` prints nothing, and
  `grep -c 'loopback per repo' docs/decisions.md` prints `1`.
