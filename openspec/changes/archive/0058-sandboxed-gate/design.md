# Sandboxed gate — design

How MF's tests get a `ps` inside a worker's sandbox, and how a real worker proves the gate passes there. Verdict at the end:
ready to build.

## Context

Read at `f33a6b3` (v0.47.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- `_ps(pid, field)` runs `ps -o <field> -p <pid>` (`conduct.py:1721`). The conductor asks `lstart=` for its own pid at a run's
  start (`:2245`, the halt `:2246`), `lstart=` for a worker group (`:1625`, `:1748`), and `comm=` for a stale group's leader
  (`:1796`).
- `tests/test_conduct.py` has `_lstart` (`:76`), which runs `ps` itself, `_no_ps` (`:81`), a `ps` that prints nothing, used at
  `:2385` and `:2670`, and the `fake` fixture (`:102`).
- Under a Claude worker's sandbox, from the three build workers' logs, run `20261103-100733`: 26 tests fail, each an
  integration test that starts `conduct.py run`, each on `run: cannot run — ps cannot read this run's start time`. No other
  refusal shows.

## Goals / Non-Goals

**Goals:** `make gate` passes inside a worker's sandbox and outside it, with the same assertions.

**Non-Goals:** the conductor's own `ps` reads; any repo but MF.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | An autouse fixture puts a fake `ps` first on `PATH` | `PATH` reaches the conductors tests start as subprocesses | a patch of `_ps` in-process |
| [D2](#d2) | The fake reads a registry a test writes for the processes it starts | a stale claim's tests need a real leader's name and start time | the real `ps` |
| [D3](#d3) | A real sandboxed worker runs `make gate` | the fake worker holds no sandbox | — |

### D1

`tests/test_conduct.py` gains an autouse fixture, `ps`, that writes `<tmp>/ps-bin/ps`, a Python script, and puts its folder
first on `PATH`. It answers `ps -o <field> -p <pid>`:

- `lstart=`: `<registry>/<pid>.lstart` when present; else, for a live pid (`os.kill(pid, 0)` succeeds), the fixed
  `Mon Nov  3 10:00:00 2026`; for a dead one, nothing, exit 1.
- `comm=`: `<registry>/<pid>.comm` when present; else, for a live pid, `python3`; for a dead one, nothing, exit 1.

`_lstart` reads through the same fake. A test that sets `_no_ps` puts its folder first, ahead of the fixture's, as today.

### D2

The fixture exposes the registry, `<tmp>/ps-registry`, through `FAKE_PS_REGISTRY` in the environment, and a helper,
`_register(pid, comm, lstart)`, writes both files. The tests that start a process standing for a worker group — the stale
claim, the reboot, the group that names no executor — register it with the name and start time they assert on.

### D3

`uv run --script skills/mf-ship/scripts/conduct.py agent --executor claude "Run make gate in this directory, once, and report
its exit code and the last line of its output."`, run in this worktree from a session with network, writes its report to
`openspec/changes/0058-sandboxed-gate/evidence/gate.md`: the worker's exit code for `make gate`, and its last line.

## Tests

Counted at `f33a6b3`: `uv run pytest --collect-only -q | tail -1` prints `101 tests collected`. No test is added, deleted or
merged; the tests that start a worker group stand-in gain `_register` calls.

| test | change | holds |
|---|---|---|
| every test in `tests/test_conduct.py` | edited, by the autouse fixture | D1: each passes with the fake `ps` first on `PATH` |
| the stale-claim, reboot and no-executor tests | edited | D2: each registers its group's leader |

## Dependencies

None.

## Risks / Trade-offs

- **The fake can drift from the real `ps`'s output.** The fields are the two `conduct.py` asks, in the format `_ps`'s `LC_ALL=C`
  and `TZ=UTC0` give; a test outside the sandbox still runs the conductor's code against the fake, never the real `ps`.

## Verdict

Ready to build.
