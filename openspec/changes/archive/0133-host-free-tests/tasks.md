# Host-free tests — tasks

One phase, in `tests/` alone: the real-sandbox fixture clears coverage's variables, and two Codex tests take the fake `codex`.

## Progress

- [x] 1 — The host-free tests · moderate

## 1 — The host-free tests

- [x] 1.1 **HALT CHECK** `_executor_missing` still asks the host's `PATH` for the executor, as [design](design.md#context) reads it.
  Verify: `git grep -n -F "shutil.which(executor) is None" -- skills/mf-ship/scripts/conduct.py` prints the line of `_executor_missing`.
- [x] 1.2 In `tests/test_sandboxed.py`, add before `real_sandbox` a function `_clear_coverage(monkeypatch: pytest.MonkeyPatch) -> None` per [D1](design.md#d1).
  It calls `monkeypatch.delenv(name, raising=False)` for `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG`; its docstring ends `Why: 0133-host-free-tests design D1.`
  Verify: `git grep -n -F "_clear_coverage(monkeypatch: pytest.MonkeyPatch)" -- tests/test_sandboxed.py` prints the definition.
- [x] 1.3 In the `real_sandbox` fixture of `tests/test_sandboxed.py`, call `_clear_coverage(monkeypatch)` between `monkeypatch.setattr(platform, "OS", host)` and `_require_sandbox(host, tmp_path)`.
  Verify: `git grep -n -F "_clear_coverage(monkeypatch)" -- tests/test_sandboxed.py` prints the fixture's call.
- [x] 1.4 In `tests/test_sandboxed.py`, add after `real_sandbox` the test `test_a_real_sandbox_child_starts_no_coverage(name, monkeypatch)` per [D3](design.md#d3).
  Parametrize `name` over `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG`; set `name` and `COVERAGE_FILE`, call `_clear_coverage(monkeypatch)`, assert `name` is not in `os.environ` and `COVERAGE_FILE` is.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k a_real_sandbox_child_starts_no_coverage` passes.
- [x] 1.5 In `tests/test_conduct.py`, put `@pytest.mark.usefixtures("fake_codex")` above `test_a_checker_on_another_host_is_planned_and_probed` and `test_a_checker_falls_back_when_the_weekly_window_is_spent`, per [D2](design.md#d2).
  Verify: `git grep -n -F "usefixtures(\"fake_codex\")" -- tests/test_conduct.py` prints the mark's lines.
