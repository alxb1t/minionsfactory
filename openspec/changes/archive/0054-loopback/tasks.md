# Loopback — tasks

Build the settled [design](design.md), one phase at a time, by hand per [D7](design.md#d7). The skill, decision and
threat-model text is the design's, word for word.

## Progress

- [x] 1 — The line
- [x] 2 — The log
- [x] 3 — The environment
- [x] 4 — The record
- [x] 5 — The proof

## 1 — The line

- [x] 1.1 Read `Ship loopback:` into `ShipLines` with `_agents_flag`, and set `allowLocalBinding` in `worker_settings`, in
  `skills/mf-ship/scripts/conduct.py`; edit `test_a_claude_worker_starts_in_the_sandbox`, per [D1](design.md#d1).
  Verify: `grep -c 'allowLocalBinding' skills/mf-ship/scripts/conduct.py` prints a number above `0`, and
  `uv run pytest -q tests/test_conduct.py -k starts_in_the_sandbox` reports `1 passed`.
- [x] 1.2 Halt a version with a Codex station in a loopback repo, in `read_plan` and `take`; edit `test_the_plan_is_read_once`,
  per [D2](design.md#d2).
  Verify: `grep -c 'Ship loopback needs Claude workers' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k plan_is_read_once` reports `1 passed`.

## 2 — The log

- [x] 2.1 Add `_loopback_listeners`, the `loopback` event and `loopback` in `EVENTS`, and its step in
  `test_the_plan_is_read_once`, per [D3](design.md#d3).
  Verify: `grep -c 'def _loopback_listeners' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k plan_is_read_once` reports `1 passed`.

## 3 — The environment

- [x] 3.1 Start both executors with `env -u VIRTUAL_ENV` in `argv`, and add its step to
  `test_a_claude_worker_starts_in_the_sandbox`, per [D4](design.md#d4).
  Verify: `grep -c '"-u", "VIRTUAL_ENV"' skills/mf-ship/scripts/conduct.py` prints a number above `0`, and
  `uv run pytest -q tests/test_conduct.py -k starts_in_the_sandbox` reports `1 passed`.

## 4 — The record

- [x] 4.1 Amend D51 and D15 in `docs/decisions.md`, per [D5](design.md#d5).
  Verify: `grep -c 'Ship loopback: yes' docs/decisions.md` prints `1`, and `grep -c 'Save one class' docs/decisions.md` prints `1`.
- [x] 4.2 Edit `THREAT_MODEL.md` and `skills/mf-ship/SKILL.md` Step 3, per [D5](design.md#d5).
  Verify: `grep -c 'Ship loopback' THREAT_MODEL.md` prints `2`, and `grep -c 'Ship loopback: yes' skills/mf-ship/SKILL.md` prints `1`.

## 5 — The proof

- [x] 5.1 Add the loopback row and `_codex_held` to `tests/escape_drill.py`, and add `tests/test_escape_drill.py`, per
  [D6](design.md#d6).
  Verify: `grep -c 'claude loopback' tests/escape_drill.py` prints a number above `0`, and
  `uv run pytest -q tests/test_escape_drill.py` reports `1 passed`.
- [x] 5.2 **HALT CHECK** Run `uv run --script tests/escape_drill.py`, and write its output to
  `openspec/changes/0054-loopback/evidence/escape.md`, per [D6](design.md#d6).
  Verify: `grep -c -E '^(claude loopback: bound|codex trust written: no)' openspec/changes/0054-loopback/evidence/escape.md`
  prints `2`.
