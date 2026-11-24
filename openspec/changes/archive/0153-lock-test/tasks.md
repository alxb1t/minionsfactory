# The lock test names its interpreter — tasks

One phase: the lock test sets `UV_PYTHON_PREFERENCE` and `UV_PYTHON` before its `uv lock`, per [D1](design.md#d1).

## Progress

- [x] 1 — The lock test names its interpreter · moderate

## 1 — The lock test names its interpreter

- [x] 1.1 In `tests/test_release.py`, give `test_finish_bumps_the_version_file_and_its_lock` the parameter `monkeypatch: pytest.MonkeyPatch`. Before its `subprocess.run(["uv", "lock", "--offline"], ...)` line, add `monkeypatch.setenv("UV_PYTHON_PREFERENCE", "only-managed")` and `monkeypatch.setenv("UV_PYTHON", sys.executable)`.
  Verify: `git grep -l -F -e UV_PYTHON_PREFERENCE -- tests/test_release.py` prints `tests/test_release.py`.
- [x] 1.2 Above those `setenv` lines in `tests/test_release.py`, add the comment `# Why: 0153-lock-test design D1 — a moved home finds no managed Python.`, in the form of the suite's other `# Why:` comments.
  Verify: `git grep -l -F -e "0153-lock-test design D1" -- tests/test_release.py` prints `tests/test_release.py`.
- [x] 1.3 Run the edited test with the other tests of `tests/test_release.py`.
  Verify: `uv run pytest tests/test_release.py -q` exits `0`.
