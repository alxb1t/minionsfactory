# Sandbox runner — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [x] 1 — The sandboxed function · hard
- [x] 2 — The command and the record · hard

## 1 — The sandboxed function

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def worker_settings(' -e '^SECRETS = (' -e '^TOKENS = (' -e '^CODEX_DENIAL = ' -e '^def reach(' -e '^def primary_of(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.2 Add `tests/test_sandboxed.py` with the fixture that puts a fake `sandbox-exec` first on `PATH` — it writes its
  profile argument to a file, then runs the rest of its arguments — and `test_the_profile_confines_writes_reads_and_network`,
  `test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment`, `test_the_exit_passes_through`,
  `test_no_sandbox_exec_stops_with_2` and `test_a_denial_in_the_output_gets_a_line`, per [the Tests table](design.md#tests).
  Then `_profile` and `sandboxed` in `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_sandboxed.py` exits 0; `git grep -n -e '^def _profile(' -e '^def sandboxed(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.3 Add `_seatbelt`, the probe that runs `sandbox-exec -p "(version 1)(allow default)" /usr/bin/true`, and the three
  real-Seatbelt tests `test_a_write_outside_the_trees_is_denied`, `test_a_secret_read_is_denied` and
  `test_a_network_connect_is_denied` to `tests/test_sandboxed.py`, each skipping when `_seatbelt()` is false, per
  [D5](design.md#d5) and [the Tests section](design.md#tests). They test the code of 1.2 and use no fake `sandbox-exec`; no
  red run is asked of them beyond `no tests ran`.
  Verify: `uv run pytest -q -rs tests/test_sandboxed.py -k "write_outside_the_trees or secret_read or network_connect"` exits 0; `grep -n -e 'def _seatbelt(' -e 'def test_a_network_connect_is_denied(' tests/test_sandboxed.py` prints a line for each.

## 2 — The command and the record

- [x] 2.1 Add `test_the_command_runs_a_command_in_the_cwd` and `test_the_command_exits_2_with_no_os_sandbox` to
  `tests/test_sandboxed.py`, the second with `PATH` set as [the Tests section](design.md#tests) says; then the `sandboxed` subparser, its branch in `main` and the line
  `conduct.py sandboxed -- <cmd>` in the module docstring of `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_sandboxed.py` exits 0; `git grep -n -e 'conduct.py sandboxed -- <cmd>' -e 'args.command == "sandboxed"' -- skills/mf-ship/scripts/conduct.py` prints a line for each; `git grep -c '^def test_' -- tests/test_sandboxed.py` prints `tests/test_sandboxed.py:10`.
- [x] 2.2 Add the `sandboxed -- <cmd>` row after the `anchor` row of the command table in `skills/mf-ship/SKILL.md`: what it
  runs, its trees, no credential read, no network, its exit, the `sandboxed: denied —` line, and exit 2 with `no OS
  sandbox`, per [D3](design.md#d3).
  Verify: `git grep -n -e '^| .sandboxed -- <cmd>. |' -e 'no OS sandbox' -- skills/mf-ship/SKILL.md` prints a line for each.
- [x] 2.3 Edit D51 in `docs/decisions.md` as [D4](design.md#d4) says: its headline, its **Accepts** list and its **Rejected**
  list.
  Verify: `git grep -n -e 'runs under .sandboxed().' -e 'a plain command run bare where no OS sandbox stands' -- docs/decisions.md` prints a line for each.
