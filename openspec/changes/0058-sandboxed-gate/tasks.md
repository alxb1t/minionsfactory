# Sandboxed gate — tasks

Build the settled [design](design.md), one phase at a time, by hand.

## Progress

- [x] 1 — The fake ps
- [x] 2 — The proof

## 1 — The fake ps

- [x] 1.1 Add the autouse `ps` fixture, its fake `ps` and `_register` to `tests/test_conduct.py`, and register the group
  stand-ins in the stale-claim, reboot and no-executor tests, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -c 'autouse=True' tests/test_conduct.py` prints a number above `0`, and `uv run pytest -q tests/test_conduct.py`
  exits 0.

## 2 — The proof

- [x] 2.1 **HALT CHECK** Run D3's command in this worktree, and write the worker's report to
  `openspec/changes/0058-sandboxed-gate/evidence/gate.md`, per [D3](design.md#d3).
  Verify: `grep -c -E 'exit (code )?0' openspec/changes/0058-sandboxed-gate/evidence/gate.md` prints a number above `0`.
