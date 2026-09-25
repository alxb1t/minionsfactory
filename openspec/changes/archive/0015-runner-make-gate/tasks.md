# 0015-runner-make-gate — tasks

**In one line:** the runner runs `make gate` first; then the toml is deleted and its name retired. The why of each
task is in [design.md](design.md).

## Progress

- [x] 1 — The runner runs `make gate`
- [x] 2 — The toml and its name retire

## 1 — The runner runs `make gate`

The runner changes while the toml still exists, so the new gate is proven before the old file goes
([D6](design.md#d6)). The shape is [D1–D3](design.md#d1d3--the-runner-before--after).

- [x] 1.1 **HALT CHECK** — no skill reads the toml, so the runner is its last reader.
  Verify: `test -z "$(grep -rl 'minions.toml' skills/)"` exits 0.
- [x] 1.2 Test first: `tests/test_gate.py` moves to a `Makefile` fixture and a faked dry run, and binds the
  `gate:make-gate:*` keys ([Seams](design.md#seams--what-the-tests-hold)). Verify: `uv run pytest tests/test_gate.py -q` fails.
- [x] 1.3 `orchestrator/gate.py`: resolve the gate to `["make gate"]` behind the dry run, per D1–D3.
  Verify: `grep -c -e 'tomllib' -e 'read_gate_commands' -e 'minions.toml' orchestrator/gate.py` prints `0`.
- [x] 1.4 `docs/modules/gate.md`: rewrite it for the new resolver. Verify: `grep -c 'minions.toml' docs/modules/gate.md`
  prints `0`, and `grep -c 'make -n gate' docs/modules/gate.md` prints `1` or more.
- [x] 1.5 The gate tests pass. Verify: `uv run pytest tests/test_gate.py -q` exits 0.

## 2 — The toml and its name retire

Every file is listed in [D5](design.md#d5--where-the-name-leaves), with what it says after.

- [x] 2.1 Test first: in `tests/test_conventions.py`, add `minions.toml` as a retired needle with its own scan and
  twin over `_SCANNED`, bound to `sdd:retired-gate-config:named-nowhere`. Verify: `uv run pytest tests/test_conventions.py -q` fails.
- [x] 2.2 Delete `.minions/minions.toml`; `.gitignore` becomes `.minions/`, with its comment updated.
  Verify: `test ! -e .minions/minions.toml` exits 0; `grep -c 'minions.toml' .gitignore` prints `0`.
- [x] 2.3 `Makefile`, `CLAUDE.md`, `README.md`: the D5 rows. Verify:
  `grep -c 'minions.toml' Makefile CLAUDE.md README.md` prints `0` for each file.
- [x] 2.4 `docs/architecture.md`, `docs/modules/main.md`, `prompts/coder.md`: the D5 rows. Verify:
  `grep -c 'minions.toml' docs/architecture.md docs/modules/main.md prompts/coder.md` prints `0` for each file.
- [x] 2.5 `tests/test_conventions.py`: the tracked-but-unscanned comment drops the name; it stays only as the quoted
  needle. Verify: `grep -c 'minions.toml' tests/test_conventions.py` prints `1`, and `grep -c '"minions.toml"' tests/test_conventions.py` prints `1`.
- [x] 2.6 No live mention remains. Verify:
  `git grep -l 'minions.toml' -- . ':!openspec' ':!CHANGELOG.md' ':!tests'` prints nothing.
- [x] 2.7 The scans pass. Verify: `uv run pytest tests/test_conventions.py -q` exits 0.
