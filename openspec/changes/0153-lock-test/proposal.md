---
bump: patch
---

# The lock test names its interpreter

`test_finish_bumps_the_version_file_and_its_lock` names the Python its `uv lock` uses, so it finds one on the Linux runner.

Reading map: [design](design.md) holds the cause, the one decision and the test cost, [tasks](tasks.md) holds the one phase.

## Why

CI's `gate` job (Linux) is red on `main` at v0.123.0 on the lock test, which runs `uv lock --offline` under the suite's temporary `HOME`. On the runner, uv's managed Python lives under the real home, so a moved home finds no interpreter. A host with a Python on `PATH` passes, which hid the fault.

## What Changes

- `test_finish_bumps_the_version_file_and_its_lock` in `tests/test_release.py` sets `UV_PYTHON_PREFERENCE` to `only-managed` and `UV_PYTHON` to `sys.executable`, through `monkeypatch`, before its own `uv lock`. `release.py`'s lock inside the test reads the same environment.

No requirement of the spec is added, changed or removed: the change edits a test and no behaviour.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change carries `skip_specs: true` and `specs/.gitkeep`.

## Impact

- `tests/test_release.py`: `test_finish_bumps_the_version_file_and_its_lock` gains the `monkeypatch` parameter and its `UV_PYTHON_PREFERENCE` and `UV_PYTHON` settings.
- The Linux job's `gate` run passes where it failed on this test. The proof is the gate job of this release's CI run.

## Not in this change

- A change to `release.py`'s lock, to `conftest.py`'s isolated home or to `.github/workflows/ci.yml`.
- `test_finish_halts_when_uv_lock_fails`, which plants its own `uv`.
- Any other test of `tests/test_release.py`: none else runs a real `uv lock`.
