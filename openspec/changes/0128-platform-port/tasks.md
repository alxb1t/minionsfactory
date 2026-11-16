# Platform port — tasks

The pin on today's code, the home with its first tenant, the move of the rest, and the fix of `0107·S1`; each phase ends green.

## Progress

- [x] 1 — The pin · moderate
- [ ] 2 — The home · hard
- [ ] 3 — The move · hard
- [ ] 4 — The fix · hard

## 1 — The pin

Cases on today's code, per [D7](design.md#d7). Each is applied red first: make the change its task names, see the case fail, restore the line.

- [x] 1.1 **HALT CHECK** The pin reads today's call sites: `skills/mf-ship/scripts/conduct.py` names `ps`, `sysctl`, `caffeinate` and `sandbox-exec` as strings.
  Verify: `grep -c -E '"(ps|sysctl|caffeinate|sandbox-exec)"' skills/mf-ship/scripts/conduct.py` prints `4`.
- [x] 1.2 Create `tests/test_platform.py`, `_conduct` taken `from conduct_load import conduct as _conduct`, with `test_the_native_architecture_reads_sysctl_past_a_translated_process`: a fake `sysctl` on `PATH` prints `1`, then `0`, with `os.uname` patched to `x86_64`; call `_conduct()["_native"]()`. Red under `== "1"` → `!= "1"` in `_native`.
  Verify: `uv run pytest tests/test_platform.py -q -k reads_sysctl_past_a_translated_process` exits 0.
- [x] 1.3 In `tests/test_platform.py` add `test_the_native_architecture_falls_back_to_uname`: a `PATH` with no `sysctl`, then `subprocess.run` raising `TimeoutExpired`; each gives `os.uname().machine`. Red under `return os.uname().machine` → `return ""` in `_native`'s `except`.
  Verify: `uv run pytest tests/test_platform.py -q -k native_architecture_falls_back` exits 0.
- [x] 1.4 In `tests/test_platform.py` add `test_ps_reads_nothing_when_it_cannot_run`: `_conduct()["_ps"](os.getpid(), "lstart=")` is `""` on a `PATH` with no `ps` and when `subprocess.run` raises `TimeoutExpired`. Red under `return ""` → `raise` in `_ps`'s `except`.
  Verify: `uv run pytest tests/test_platform.py -q -k ps_reads_nothing_when_it_cannot_run` exits 0.
- [x] 1.5 In `tests/conftest.py` make `fake_sandbox_exec` print a line to stderr and exit 64 when `"$1" != "-p"`, before it writes the profile.
  Verify: `git grep -n -F '"$1" != "-p"' -- tests/conftest.py` prints the check.
- [x] 1.6 In `tests/test_conduct.py` add `test_the_fetch_command_starts_sandbox_exec_with_dash_p`: `_fetch_run(["sh", "-c", "echo fetched"], cwd, [writes], env, 10)` under `fake_sandbox_exec` returns `returncode` 0 and `stdout` `fetched\n`, and the fake's profile file holds a profile with no `(deny network*)`. Red under `"-p"` → `"-f"` at `_fetch_run`, and under `capture_output=True` → `False`; the same `"-p"` → `"-f"` at `sandboxed`'s `Popen` turns the existing `sandboxed` tests red under 1.5's fake.
  Verify: `uv run pytest tests/test_conduct.py -q -k fetch_command_starts_sandbox_exec_with_dash_p` exits 0.
- [x] 1.7 In `tests/test_platform.py` add `test_the_conductors_hold_runs_in_a_session_of_its_own`: a fake `caffeinate` written in Python records `os.getsid(0)` and `os.getpid()`; after `_conduct()["_hold_awake"](4242)` and a poll of up to 10 s for the record, they are equal and differ from the test's session. Red under `start_new_session=True` → `False` in `_hold_awake`.
  Verify: `uv run pytest tests/test_platform.py -q -k conductors_hold_runs_in_a_session_of_its_own` exits 0.
- [x] 1.8 In `tests/test_awake.py` add `test_the_cuts_hold_runs_in_a_session_of_its_own`, built as 1.7 on `awake.main(["start", …])`, its record awaited with `_wait`. Red under `start_new_session=True` → `False` in `awake.py`'s `_start`.
  Verify: `uv run pytest tests/test_awake.py -q -k cuts_hold_runs_in_a_session_of_its_own` exits 0.
- [x] 1.9 In `tests/test_awake.py` add `test_the_walk_stops_before_pid_1`: with the fake `caffeinate` of `_fake_caffeinate` on `PATH`, pid 1 registered as `launchd` and the chain `[(9011, "zsh")]` ending at 1, `awake.main` gives `awake: not held — no host process`. Red under `while pid > 1` → `while pid >= 1` in `_host`.
  Verify: `uv run pytest tests/test_awake.py -q -k walk_stops_before_pid_1` exits 0.
- [x] 1.10 In `tests/test_awake.py` add `test_both_tools_missing_prints_the_caffeinate_line_first`: `CAFFEINATE` set to an absent name through `vars(awake)`, as the existing test of the missing tool does, and a parent chain with no host print `awake: not held — caffeinate not on PATH`. Red under swapping `_start`'s `which` check with its `_host()` check.
  Verify: `uv run pytest tests/test_awake.py -q -k both_tools_missing` exits 0.
- [x] 1.11 In `tests/test_conduct.py` extend `test_a_stale_claim_is_cleared`: its `pytest.raises(conduct["Stop"], match=…survives)` is bound `as stopped` and asserts `stopped.value.code == 2`. Red under `2` → `3` in the `Stop(` of `_clear` whose message ends `survives:`.
  Verify: `uv run pytest tests/test_conduct.py -q -k a_stale_claim_is_cleared` exits 0.
- [x] 1.12 In `tests/test_conduct.py` add `test_the_liveness_probe_sends_signal_zero`: with a fake `ps` first on `PATH` that prints nothing and `os.kill` recorded, `_started(pid)` records `(pid, 0)`, returns `""` on `ProcessLookupError` and stops with 2 on success and on `PermissionError`. Red under `os.kill(pid, 0)` → `os.kill(pid, 1)`.
  Verify: `uv run pytest tests/test_conduct.py -q -k liveness_probe_sends_signal_zero` exits 0.
- [x] 1.13 In `tests/test_viewer.py` add `test_run_ps_reads_a_failing_ps_as_nothing`: a fake `ps` first on `PATH` exits 1 and prints nothing, and `run_ps(os.getpid())` is `""`. Red under `check=False` → `check=True` in `run_ps`.
  Verify: `uv run pytest tests/test_viewer.py -q -k run_ps_reads_a_failing_ps_as_nothing` exits 0.
- [x] 1.14 In `tests/test_sandboxed.py` add `test_the_profile_text_is_held_byte_for_byte`: a literal template of today's text, its resolved paths filled in, for a closed and an open network. Red under swapping the `(deny file-write*)` line with the `(allow file-write* …)` line in `_profile`.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k profile_text_is_held_byte_for_byte` exits 0.
- [x] 1.15 In `tests/test_sandboxed.py` make the `real_sandbox` fixture call `_require_seatbelt()`, which fails when `MF_REQUIRE_SEATBELT` is set and the profile cannot apply, and skips otherwise; add `test_a_required_seatbelt_that_cannot_apply_fails_and_else_skips`. Red under swapping `pytest.fail` and `pytest.skip`.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k required_seatbelt_that_cannot_apply` exits 0.
- [x] 1.16 In `.github/workflows/ci.yml` add the job `macos` on `macos-latest` with `timeout-minutes: 20`: the gate job's checkout and `setup-uv` steps, as pinned there, then `uv sync --locked` and `uv run pytest tests/test_sandboxed.py -q` with `MF_REQUIRE_SEATBELT: "1"` in its `env`, per [D12](design.md#d12).
  Verify: `git grep -n -F "macos-latest" -- .github/workflows/ci.yml` prints the runner line.
- [x] 1.17 Keep the workflow clean under the gate's linter: fix any finding the new job draws.
  Verify: `uv run zizmor .github/workflows/ci.yml` exits 0.

## 2 — The home

`skills/mflib/` is born with the native-architecture read, per [D1](design.md#d1) and [D2](design.md#d2); the rules and the record that hold it land with it.

- [ ] 2.1 In `pyproject.toml` add `[tool.ty.environment]` with `extra-paths = ["skills"]`, and `pythonpath = ["skills"]` under pytest's settings, each with a comment naming `mflib`.
  Verify: `git grep -n -F 'extra-paths = ["skills"]' -- pyproject.toml` prints the line.
- [ ] 2.2 Create `skills/mflib/__init__.py` (a docstring only) and `skills/mflib/platform.py` holding `arch()`, `_native`'s body and docstring, with the `sysctl` call's timeout as `TIMEOUT = 60`, per [D4](design.md#d4).
  Verify: `grep -n -E "^def arch\(" skills/mflib/platform.py` prints the line.
- [ ] 2.3 In `skills/mf-ship/scripts/conduct.py` add the seed and `import mflib.platform` after the imports, delete `_native`, and make its readers, `check_probe` and the line that writes the probe's gate file, call `mflib.platform.arch()`.
  Verify: `grep -c -F "mflib.platform.arch()" skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 2.4 In `tests/conduct_load.py` restore `sys.path` after each run of the conductor, per [D2](design.md#d2).
  Verify: `git grep -n "sys.path" -- tests/conduct_load.py` prints the restore.
- [ ] 2.5 In `tests/test_platform.py` and in `tests/test_conduct.py` replace each `_conduct()["_native"]()` and `conduct["_native"]()` by `platform.arch()`, `platform` imported `from mflib import platform`.
  Verify: `grep -c -F "platform.arch()" tests/test_conduct.py` prints `2`.
- [ ] 2.6 In `THREAT_MODEL.md` add to `## Surfaces` the line ``- `skills/mflib/*` — the shared home: the port to the OS, loaded by the scripts that run on the operator's machine.``
  Verify: `git grep -n -F "skills/mflib/*" -- THREAT_MODEL.md` prints the line.
- [ ] 2.7 In `tests/test_structure.py` add `check_surfaces(root)`: it reads the globs of `## Surfaces` in `THREAT_MODEL.md` and fails `f"{path}: matches no surface of THREAT_MODEL.md"` for each Python file under `skills/` that `fnmatch` leaves unmatched. Add `test_check_surfaces_holds_on_the_tree` and planted-breach twins that fail and pass.
  Verify: `uv run pytest tests/test_structure.py -q -k check_surfaces` exits 0.
- [ ] 2.8 In `tests/test_structure.py` add `SEED` and `check_seed(root)`: a script under `skills/`, outside `skills/mflib/`, whose first top-level `mflib` import has no statement before it that `ast.unparse` gives as `SEED` fails `f"{path}: imports mflib with no seed line before it"`. Add the tree test and twins: no seed, a wrong seed, the seed, a file of `skills/mflib/`.
  Verify: `uv run pytest tests/test_structure.py -q -k check_seed` exits 0.
- [ ] 2.9 In `tests/test_structure.py` make `check_os` skip `skills/mflib/platform.py`, drop `("conduct.py", "sysctl")` from `OS_NAMES`, and write `test_check_os_passes_the_port_file` and `test_check_os_fails_on_a_file_that_is_no_port`: the port naming `caffeinate` passes, another file naming it fails.
  Verify: `uv run pytest tests/test_structure.py -q -k check_os_passes_the_port_file` exits 0.
- [ ] 2.10 In `docs/modules.md` add the `home` rows for `skills/mflib/__init__.py` and `skills/mflib/platform.py`, add `platform.py` to the names cell of `conduct.py`, and drop `no row until it exists` from the `home` bullet.
  Verify: `uv run pytest tests/test_structure.py -q -k check_map` exits 0.
- [ ] 2.11 In `docs/recipes.md` `## An OS` add the row `skills/mflib/platform.py`, `arch`, and take `_native` out of the conductor's row.
  Verify: `git grep -n -F "skills/mflib/platform.py" -- docs/recipes.md` prints the row.
- [ ] 2.12 In `docs/decisions.md` D83 name `skills/mflib/platform.py` as the platform seam's file and say the gate also holds the seed and the surfaces, per [D10](design.md#d10).
  Verify: `git grep -n -F "skills/mflib/platform.py" -- docs/decisions.md` prints the line.

## 3 — The move

The rest of the port follows into `skills/mflib/platform.py`, per [D3](design.md#d3), [D4](design.md#d4), [D6](design.md#d6) and [D8](design.md#d8). No assert of a test changes, only the line by which a test reaches a name.

- [ ] 3.1 **HALT CHECK** Among the scripts only `skills/mf-ship/scripts/conduct.py` names `_profile`, `_sandbox_exec` and `CODEX_DENIAL`.
  Verify: `git grep -l -w -e "_profile" -e "_sandbox_exec" -e "CODEX_DENIAL" -- skills` prints `skills/mf-ship/scripts/conduct.py`.
- [ ] 3.2 In `skills/mflib/platform.py` add `Policy`, `profile`, `has_sandbox`, `confine`, `refused`, `process`, `has_hold`, `hold_awake` and `CAFFEINATE`, as [D3](design.md#d3), [D4](design.md#d4) and [D5](design.md#d5) say. `profile` renders `_profile`'s text unchanged.
  Verify: `grep -c -E "^def (profile|has_sandbox|confine|refused|process|has_hold|hold_awake)\(" skills/mflib/platform.py` prints `7`.
- [ ] 3.3 In `skills/mf-ship/scripts/conduct.py` add `_policy(trees, home, network=False, tmp=None)` and delete `_profile` and `_sandbox_exec`. `sandboxed` asks `mflib.platform.has_sandbox()` where `_sandbox_exec()` was, and `_fetch_run` asks it after its policy is built; each stops with 2 and the same line. Each runs `[*mflib.platform.confine(policy), *argv]`.
  Verify: `grep -c -F "mflib.platform.confine(" skills/mf-ship/scripts/conduct.py` prints `2`.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` delete `CODEX_DENIAL`; `sandboxed`, `_codex_denied` and `denials` call `mflib.platform.refused(`, `denials` reading `refused(line) or any(key in line for key in ('"tool_use"', '"is_error"'))`.
  Verify: `grep -c -F "mflib.platform.refused(" skills/mf-ship/scripts/conduct.py` prints `3`.
- [ ] 3.5 In `skills/mf-ship/scripts/conduct.py` delete `_ps` and `CAFFEINATE`; its readers call `mflib.platform.process(` with `"lstart"` in `work`, `_started` and `run`, and with `"comm"` in `_clear`; `_hold_awake` asks `has_hold()` and calls `hold_awake(pid)`.
  Verify: `grep -c -F "mflib.platform.process(" skills/mf-ship/scripts/conduct.py` prints `4`.
- [ ] 3.6 In `skills/mf-cut-change/scripts/awake.py` add the seed and `import mflib.platform`; delete `_ps` and `CAFFEINATE`; `_name` and `_host` call `process`; `_release` compares with `mflib.platform.CAFFEINATE`; `_start` asks `mflib.platform.has_hold()` before `_host()`, then calls `hold_awake(host, HOLD_SECONDS)`.
  Verify: `grep -c -F "mflib.platform.has_hold()" skills/mf-cut-change/scripts/awake.py` prints `1`.
- [ ] 3.7 In `skills/mf-ui/scripts/viewer.py` add the seed and `import mflib.platform`; `run_ps` returns `mflib.platform.process(pid, "command")`, and no `"ps"` string remains.
  Verify: `git grep -n -F '"ps"' -- skills/mf-ui/scripts/viewer.py` prints nothing.
- [ ] 3.8 Re-point the tests: `conduct["_profile"](a, b)` is replaced by `platform.profile(conduct["_policy"](a, b))` in `tests/test_sandboxed.py` and `tests/test_conduct.py`; `conduct["_ps"](pid, "lstart=")` by `platform.process(pid, "lstart")` in `tests/test_conduct.py` and `tests/test_platform.py`; each `CAFFEINATE` set through `__globals__` or `vars(awake)` by `monkeypatch.setattr(platform, "CAFFEINATE", …)` in `tests/test_conduct.py` and `tests/test_awake.py`.
  Verify: `git grep -n -E 'conduct(\(\))?\["(_profile|_ps)"\]|__globals__\["CAFFEINATE"\]|vars\(awake\)' -- tests` prints nothing.
- [ ] 3.9 In `tests/test_structure.py` drop `("awake.py", "ps")` and `("viewer.py", "ps")` from `OS_NAMES`.
  Verify: `git grep -n -F '("awake.py", "ps")' -- tests/test_structure.py` prints nothing.
- [ ] 3.10 In `docs/modules.md` set the names cells: `conduct.py` gains `platform.py`, `awake.py` is `platform.py`, `viewer.py` is `conduct.py, converge.py, platform.py`.
  Verify: `uv run pytest tests/test_structure.py -q -k check_map` exits 0.
- [ ] 3.11 In `docs/recipes.md` `## An OS` list the port's members under `skills/mflib/platform.py`, drop the rows of `conduct.py`, `awake.py` and `viewer.py` and the paragraph that opens `Until the home holds the platform port`.
  Verify: `git grep -n -F "Until the home holds the platform port" -- docs/recipes.md` prints nothing.

## 4 — The fix

`0107·S1`: the profile stops a command from signalling a process outside its sandbox, per [D11](design.md#d11).

- [ ] 4.1 In `skills/mflib/platform.py` add to `profile`, after the `(allow file-write* …)` line and before the `(deny file-read* file-write* …)` line, `(deny signal)` then `(allow signal (target same-sandbox))`.
  Verify: `git grep -n -F "(deny signal)" -- skills/mflib/platform.py` prints the rule.
- [ ] 4.2 In `tests/test_sandboxed.py` carry `(deny signal)` and `(allow signal (target same-sandbox))` into both templates of `test_the_profile_text_is_held_byte_for_byte`, and write `test_the_profile_denies_a_signal_outside_the_sandbox`: both stand between the write allow and the read deny, with the network closed and open.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k profile_denies_a_signal_outside` exits 0.
- [ ] 4.3 In `tests/test_sandboxed.py` add, under `real_sandbox`, `test_a_signal_to_a_process_outside_is_denied`: a `sleep` the test starts is sent SIGTERM and signal 0 by a sandboxed command; each fails with `Operation not permitted` and the `sleep` still runs.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k signal_to_a_process_outside_is_denied` exits 0.
- [ ] 4.4 In `tests/test_sandboxed.py` add, under `real_sandbox`, `test_a_signal_to_the_commands_own_child_is_delivered`: a sandboxed command starts a `sleep` and sends it SIGTERM, and exits 0.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k signal_to_the_commands_own_child` exits 0.
- [ ] 4.5 In `tests/test_sandboxed.py` add, under `real_sandbox`, `test_the_cuts_hold_is_released_under_the_rule`: one sandboxed command runs `awake.py start` then `awake.py stop` in a scratch repository and prints `awake: held (2 h at most)` then `awake: released`.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k cuts_hold_is_released_under_the_rule` exits 0.
