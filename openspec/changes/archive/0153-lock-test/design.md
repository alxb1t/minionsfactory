# The lock test names its interpreter — design

One test sets `UV_PYTHON_PREFERENCE` and `UV_PYTHON` so its `uv lock` finds the suite's Python on any host. Verdict: ready to build, in the phase of [tasks](tasks.md).

## Context

`test_finish_bumps_the_version_file_and_its_lock` runs `uv lock --offline` in the fixture repository, then `Repo.finish`, which calls `release.py`'s `main` in the test's own process. `release.py` locks again through `_exec`, which passes no environment of its own, so both locks read the test's environment.

```
test process env  ──▶  subprocess uv lock   (the test's own line)
        │
        └──────────▶  release.py main ──▶ _exec ──▶ uv lock --offline
```

`tests/conftest.py` moves `HOME` and the XDG folders under each test's temporary folder. On the Linux job, `astral-sh/setup-uv` installs a uv-managed Python 3.12 under the real home, which a moved home does not find, and no other Python is on `PATH`. A macOS host or a developer machine has a Python on `PATH`, so the test passes there.

## Goals / Non-Goals

- Goal: the lock test passes on the Linux runner, and fails on any host if it names no interpreter.
- Non-goal: any change to `release.py`, `tests/conftest.py` or `.github/workflows/ci.yml`. A real release runs `release.py` under the real home, where uv finds its Python.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The test sets `UV_PYTHON_PREFERENCE=only-managed` and `UV_PYTHON=<sys.executable>` through `monkeypatch`, before its `uv lock`. | Measured in a scratch folder: under a moved home with `only-managed`, `uv lock --offline` finds no interpreter, as on the runner; with `UV_PYTHON` a path it locks, for a managed, a system and a venv interpreter alike. | `UV_PYTHON` alone: a host with a Python on `PATH` would pass without it, so the test would not prove the fix. |
| [D2](#d2) | `release.py`, `conftest.py`, `ci.yml` and `test_finish_halts_when_uv_lock_fails` stay as they are. | The fault is the test's environment, not the shipped skill's. The halt test plants its own `uv` and never reaches uv's search. | Pass an environment in `release.py`'s `_exec`, or keep the real home in `conftest.py`: a line of shipped code changed to fit one test. |

### D1

The `setenv` lines go before the test's own `subprocess.run(["uv", "lock", "--offline"], ...)`, so `finish`'s lock inside the same test reads them too:

```python
monkeypatch.setenv("UV_PYTHON_PREFERENCE", "only-managed")
monkeypatch.setenv("UV_PYTHON", sys.executable)
```

`monkeypatch` restores both after the test. The test file already imports `sys` and `pytest`, and the `repo` fixture takes the same `monkeypatch`.

The case, red before and green after: with the preference set and no interpreter named, the test is red on any host, as on the runner. With the suite's interpreter named, it is green. The Linux proof is the gate job of this release's CI run.

### D2

`git grep` finds `uv lock` called in `tests/` only by the lock test's own line, so no other test needs the `setenv` lines.

## Tests

The change adds and removes no test and adds no end-to-end run. It edits one test.

| layer | added | removed | command |
|---|---|---|---|
| unit, `tests/test_release.py` | 0 | 0 | `uv run pytest tests/test_release.py --collect-only -q` prints the same count before and after |
| end-to-end | 0 | 0 | none: the change adds no run on any engine |

No `Verify:` shows the red state on a host with a Python on `PATH`: the edited test is a regression check there, and the Linux runner's gate job is the red-to-green proof. No test is deleted or merged, so no `I16` table. The test stays at its layer per `T1`; the edit adds no step, so `T2` and `T3` hold.

## Dependencies

None.

## Risks / Trade-offs

- `UV_PYTHON=<sys.executable>` pins the venv's interpreter, so the fixture's `requires-python = ">=3.12"` must hold for it. The gate's Python is 3.12 or later by [coding standards](../../../CODING_STANDARDS.md).
- This is the first version `release.py` releases. A release halt the script causes is answered by moving the pin back to v0.122.0, per the brief.

## Verdict

Ready to build: one moderate phase, one test edited, no shipped line changed.
