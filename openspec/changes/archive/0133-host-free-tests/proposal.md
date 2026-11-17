---
bump: patch
version: 0.105.1
---

# Host-free tests

Make the suite's host-bound tests pass on a host with no Codex CLI and under coverage, so CI's Linux gate is green.

Reading map: [design](design.md) holds the causes, the fixes and the test cost, [tasks](tasks.md) holds its phase, in `tests/` alone.

## Why

CI's Linux gate has been red since v0.105.0: tests of `tests/test_sandboxed.py` and `tests/test_conduct.py` fail there and pass on the operator's Mac. The host leaks into a test by coverage and by `PATH`, each reproduced in a scratch clone:

- **Coverage in a sandboxed child.** The gate runs `coverage run` with `patch = ["subprocess"]`, so `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG` reach a command the conductor sandboxes. The child's coverage cannot write its data file, and its traceback joins the output that `test_a_secret_read_is_denied`, `test_the_private_folders_are_the_commands_own`, `test_a_signal_to_a_process_outside_is_denied` and `test_a_signal_between_siblings_is_delivered` compare whole.
- **Codex on the host.** `test_a_checker_on_another_host_is_planned_and_probed` and `test_a_checker_falls_back_when_the_weekly_window_is_spent` expect Codex planned and ready, and read it from the host's `PATH`. CI's `PATH` holds no `codex`.

No run saw either: the Mac's gate runs inside the build's sandbox, where the real-sandbox tests skip, and the Mac has Codex.

## What Changes

- `tests/test_sandboxed.py`: a helper `_clear_coverage` drops `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG`; the `real_sandbox` fixture calls it; one test holds it.
- `tests/test_conduct.py`: `test_a_checker_on_another_host_is_planned_and_probed` and `test_a_checker_falls_back_when_the_weekly_window_is_spent` take the `fake_codex` fixture.
- No file under `skills/` or `scripts/` changes. The conductor's environment for a sandboxed command stays as it is.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Tests only: `skip_specs: true`.

## Impact

- Files: `tests/test_sandboxed.py`, `tests/test_conduct.py`.
- The gate's tests run on every core with the same result on a host with no real sandbox and no `codex`.
- No other file changes.

## Not in this change

- A change to the conductor's environment for a sandboxed command: production's variables stay.
- A change to `.github/workflows/ci.yml`, to the `fake_codex` fixture, or to the macOS job's plain `pytest`.
- Any other red test of CI: a second patch follows when CI's run, read after the push, shows one.
