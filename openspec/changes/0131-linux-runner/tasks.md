# Linux runner — tasks

The phases follow [design](design.md): the side, the Linux side, the callers, the names, the real proof, the record, the private folders. Each task names its files and links the decision it follows.

## Progress

- [x] 1 — The side · moderate
- [x] 2 — The Linux side · hard
- [x] 3 — The callers · moderate
- [x] 4 — The names · hard
- [x] 5 — The real proof · moderate
- [x] 6 — The record · moderate
- [ ] 7 — The private folders · hard

## 1 — The side

- [x] 1.1 In `skills/mflib/platform.py` add `import sys`, `side(system: str) -> str` returning `"linux"` for a name that starts with `linux` and `"macos"` for any other, and, after the constants, `OS = side(sys.platform)`. Its docstring ends `Why: 0131-linux-runner design D7` ([D7](design.md#d7)).
  Verify: `git grep -n -e "^def side" -e "^OS = side(sys.platform)" -- skills/mflib/platform.py` prints both lines.
- [x] 1.2 In `tests/test_platform.py` add `test_the_side_names_linux_and_else_macos`: `platform.side` of `linux` and `linux2` is `linux`, of `darwin` and `freebsd` is `macos` ([D7](design.md#d7)).
  Verify: `uv run pytest tests/test_platform.py -q -k side_names` passes.
- [x] 1.3 In `tests/conftest.py` import `from mflib import platform`, add `HOST = platform.OS` after the imports, a session fixture `host` returning `HOST`, and the autouse fixture `macos_side(monkeypatch)` that sets `platform.OS` to `"macos"` ([D7](design.md#d7)).
  Verify: `git grep -n -e "^HOST = platform.OS" -e "^def host" -e "^def macos_side" -- tests/conftest.py` prints a line holding each.
- [x] 1.4 In `tests/test_sandboxed.py` rename `_require_seatbelt` to `_require_sandbox`, the switch `MF_REQUIRE_SEATBELT` to the new `MF_REQUIRE_SANDBOX`, and `test_a_required_seatbelt_that_cannot_apply_fails_and_else_skips` to `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips`. Make `real_sandbox` take `host`, `macos_side` and `monkeypatch`, set `platform.OS` to `host`, then call `_require_sandbox()` ([D5](design.md#d5), [D7](design.md#d7)).
  Verify: `git grep -n -e MF_REQUIRE_SEATBELT -e _require_seatbelt -- tests` prints nothing.
- [x] 1.5 In `.github/workflows/ci.yml` rename `MF_REQUIRE_SEATBELT` in the macOS job to the new `MF_REQUIRE_SANDBOX` ([D5](design.md#d5)).
  Verify: `git grep -n MF_REQUIRE_SEATBELT -- .github` prints nothing.

## 2 — The Linux side

- [x] 2.1 In `tests/conftest.py` add the fixture `fake_bwrap(tmp_path, monkeypatch) -> Path` beside `fake_sandbox_exec`: a `bwrap` first on `PATH` that writes its arguments one a line to `bwrap-argv.txt` in `tmp_path`, appends a line to `bwrap-calls.txt` there, drops every argument up to the first `--` and runs the rest; it returns the argv file ([D7](design.md#d7)).
  Verify: `git grep -n "^def fake_bwrap" -- tests/conftest.py` prints the line.
- [x] 2.2 In `skills/mflib/platform.py` replace `REFUSAL` with the new `REFUSALS = {"macos": "Operation not permitted", "linux": "Read-only file system"}` and make `refused(text)` read `REFUSALS[OS]` ([D9](design.md#d9)).
  Verify: `git grep -n -w REFUSAL -- skills tests` prints nothing.
- [x] 2.3 In `tests/test_platform.py` add `test_a_refusal_is_read_on_its_own_side`: each text is a refusal on its own `OS` and none on the other, `OS` set with `monkeypatch.setattr(platform, "OS", …)` ([D9](design.md#d9)).
  Verify: `uv run pytest tests/test_platform.py -q -k refusal_is_read` passes.
- [x] 2.4 In `skills/mflib/platform.py` add `BWRAP = "bwrap"` and `_bwrap(policy: Policy, tool: str) -> list[str]` returning the prefix of [D3](design.md#d3), each path resolved as `profile` resolves it, a root or a denied path that does not exist left out. Make `confine` return `_bwrap(policy, shutil.which(BWRAP) or BWRAP)` when `OS` is `linux`; its macOS branch and `profile` stay as they are ([D3](design.md#d3), [D7](design.md#d7)).
  Verify: `git grep -n -e '^BWRAP = "bwrap"' -e "^def _bwrap" -- skills/mflib/platform.py` prints both lines.
- [x] 2.5 In `tests/test_platform.py` add `test_the_bwrap_command_follows_the_policy` on `OS` `linux`: the exact prefix for a policy with roots, a temp folder, a denied folder, a denied file and a denied path that is absent; the network open and shut; no temp folder; a root that is absent ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_platform.py -q -k bwrap_command` passes.
- [x] 2.6 In `skills/mflib/platform.py` add `_applies(tool: str) -> bool`, cached with `functools.cache`, which runs `[*_bwrap(Policy((), ()), tool), "true"]` under `TIMEOUT` and is true on exit 0, false on `OSError`, a timeout or another exit. Make `has_sandbox` on `linux` return whether `shutil.which(BWRAP)` finds a tool and `_applies` of it is true; on `macos` it stays the `PATH` check ([D8](design.md#d8)).
  Verify: `git grep -n -e "^def _applies" -e "functools.cache" -- skills/mflib/platform.py` prints both lines.
- [x] 2.7 In `tests/test_platform.py` add `test_the_sandbox_stands_on_linux_when_bwrap_applies_one`: no `bwrap` on `PATH`, one that exits 1, one that exits 0, and repeated asks of the passing one that run it once, counted in its calls file ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_platform.py -q -k sandbox_stands` passes.
- [x] 2.8 In `tests/test_sandboxed.py` add `test_a_command_runs_under_bwrap_on_linux` and `test_a_linux_denial_gets_the_line`, both on `OS` `linux` with `fake_bwrap`: one reads the argv file for the prefix of [D3](design.md#d3) before the command and sees the command run; the other prints `Read-only file system` with exit 1 and sees `_DENIAL`, then the macOS text and sees none ([D3](design.md#d3), [D9](design.md#d9)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k "under_bwrap or linux_denial"` passes.

## 3 — The callers

- [x] 3.1 In `skills/mflib/platform.py` add `no_sandbox() -> str` and `no_hold() -> str` as [D8](design.md#d8) and [D4](design.md#d4) say, with the literals `sandbox-exec is not on PATH` and `caffeinate not on PATH` on `macos` whatever `CAFFEINATE` and `SANDBOX` hold, and make `has_hold()` return false on `linux` before it looks at `PATH` ([D4](design.md#d4), [D8](design.md#d8)).
  Verify: `git grep -n -e "^def no_sandbox" -e "^def no_hold" -- skills/mflib/platform.py` prints both lines.
- [x] 3.2 In `tests/test_platform.py` add `test_the_reasons_are_the_ports`: `no_sandbox` on `macos`, on `linux` with no `bwrap` and on `linux` with a `bwrap` that cannot apply; `no_hold` on both sides; `has_hold` false on `linux` with a `caffeinate` on `PATH` ([D4](design.md#d4), [D8](design.md#d8)).
  Verify: `uv run pytest tests/test_platform.py -q -k reasons_are` passes.
- [x] 3.3 In `skills/mf-ship/scripts/conduct.py` delete `NO_SANDBOX`, add `_no_sandbox() -> Stop` returning `Stop(2, f"conduct: cannot run — no OS sandbox: {mflib.platform.no_sandbox()}")`, and `raise _no_sandbox()` at both sites. Make `_hold_awake` return `f"awake: not held — {mflib.platform.no_hold()}"` where it returned `awake: not held — caffeinate not on PATH` ([D8](design.md#d8)).
  Verify: `git grep -n -e NO_SANDBOX -e "caffeinate not on PATH" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.4 In `skills/mf-cut-change/scripts/awake.py` make `_start` return `f"awake: not held — {mflib.platform.no_hold()}"` where it returned `awake: not held — caffeinate not on PATH` ([D8](design.md#d8)).
  Verify: `git grep -n "caffeinate not on PATH" -- skills/mf-cut-change/scripts/awake.py` prints nothing.
- [x] 3.5 In `tests/test_sandboxed.py` add `test_no_bwrap_stops_with_2` on `OS` `linux`: with no `bwrap` on `PATH`, and with a `bwrap` that exits 1, `sandboxed` raises `Stop` code 2 whose text holds `no OS sandbox` and `bwrap`, and runs nothing ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k no_bwrap` passes.
- [x] 3.6 In `tests/test_awake.py` add `test_a_cut_on_linux_says_it_holds_nothing`: on `OS` `linux`, with a fake `caffeinate` on `PATH`, `start` prints `awake: not held — no hold on Linux`, records nothing, starts no `caffeinate` and exits 0 ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_awake.py -q -k cut_on_linux` passes.
- [x] 3.7 In `tests/test_conduct.py` add `test_a_run_on_linux_holds_nothing_and_says_so`, shaped on `test_a_run_holds_the_machine_awake` and marked `slow` as it is: on `OS` `linux` with a fake `caffeinate` present, `_hold_awake(4242)` returns `awake: not held — no hold on Linux` and the run's `start` line ends with it ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py -q -k on_linux_holds_nothing` passes.
- [x] 3.8 In `tests/test_structure.py` change `_OS_WORDS` to `sandbox-exec|bwrap|caffeinate|sysctl|ps` and add `test_check_os_fails_on_bwrap_in_an_unlisted_file`, shaped on the `caffeinate` one ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_structure.py -q -k bwrap` passes.
- [x] 3.9 In `tests/test_structure.py` delete from `OS_NAMES` the pairs `("awake.py", "caffeinate")`, `("conduct.py", "caffeinate")` and `("conduct.py", "sandbox-exec")`; the pair `("conduct.py", "ps")` stays ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_structure.py -q -k check_os` passes.

## 4 — The names

- [x] 4.1 **HALT CHECK** The run's first clean-tree check is the one in `preconditions` of `skills/mf-ship/scripts/conduct.py`, `if not _config_held(primary) and _dirty(primary):`, which `_hide_marks` will precede ([D2](design.md#d2)).
  Verify: `git grep -n -F "if not _config_held(primary) and _dirty(primary):" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 4.2 In `skills/mflib/platform.py` add `MARKS` holding `.bash_profile`, `.bashrc`, `.claude`, `.gitconfig`, `.gitmodules`, `.idea`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode`, `.zprofile` and `.zshrc`, and `marks() -> tuple[str, ...]` returning `MARKS` on `linux` and `()` on `macos` ([D2](design.md#d2)).
  Verify: `git grep -n -e "^MARKS" -e "^def marks" -- skills/mflib/platform.py` prints both lines.
- [x] 4.3 In `tests/test_platform.py` add `test_the_marks_are_the_linux_sandboxs`: on `linux` `marks()` equals the names of 4.2 in that order, on `macos` it is empty ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_platform.py -q -k marks_are` passes.
- [x] 4.4 In `skills/mf-ship/scripts/conduct.py` add `_hide_marks(common: Path)` as [D2](design.md#d2) describes, raising `Stop(2, f"run: cannot run — .git/info/exclude: {error}")` on an `OSError`, and call `_hide_marks(common)` in `preconditions` immediately before the `_config_held` and `_dirty` check. With no marks it returns before it opens anything ([D2](design.md#d2)).
  Verify: `git grep -n -e "^def _hide_marks" -e "_hide_marks(common)" -- skills/mf-ship/scripts/conduct.py` prints both lines.
- [x] 4.5 In `tests/test_conduct.py` add `test_a_start_on_linux_writes_the_marks_into_the_exclude` and its cases, shaped on `test_a_run_without_betterleaks_stops_at_start` with `SCANNER` absent so the run stops after the tree check: `.git/info/exclude` absent, holding one mark, holding all, ending without a newline, a link at `exclude`, a link at `info`; the stop holds `is not on PATH` and not `tree is not clean` beside an untracked `.bashrc` on `linux`, and holds `the primary's tree is not clean` on `macos`, where the file is not written ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py -q -k writes_the_marks` passes.

## 5 — The real proof

- [x] 5.1 In `tests/test_sandboxed.py` give `_require_sandbox` a `host` argument, pass it from `real_sandbox` and pass `"macos"` in each call of `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips`, and make it pass on `linux` when `platform.has_sandbox()` is true, with the reason `bwrap cannot apply a sandbox here`; on `macos` it keeps the `_seatbelt()` probe and its reason ([D5](design.md#d5)).
  Verify: `git grep -n -e "def _require_sandbox(host" -e "bwrap cannot apply a sandbox here" -- tests/test_sandboxed.py` prints both lines.
- [x] 5.2 In `tests/test_sandboxed.py`, in `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips`, add the `linux` side, setting `platform.OS` to `linux` before each call: a `bwrap` that exits 1 fails it with the switch and skips it without, one that exits 0 passes ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k required_sandbox` passes.
- [x] 5.3 In `tests/test_sandboxed.py`, in `test_a_signal_to_a_process_outside_is_denied`, expect on each line `Operation not permitted` where `platform.OS` is `macos` and `No such process` where it is `linux` ([D3](design.md#d3)).
  Verify: `git grep -n "No such process" -- tests/test_sandboxed.py` prints the line.
- [x] 5.4 In `tests/test_sandboxed.py`, in `test_a_secret_read_is_denied`, run the reads with an `io.StringIO` as `out`, add a file secret `isolated_home / ".netrc"` holding `machine x`, and assert that the output of reading either secret holds neither `key` nor `machine`; the exit-code assertion stays for the `.ssh` read alone ([D3](design.md#d3)).
  Verify: `git grep -n "machine x" -- tests/test_sandboxed.py` prints the line.
- [x] 5.5 In `.github/workflows/ci.yml`, in the `gate` job between its `Install Betterleaks` step and its `Gate` step, add the steps and the `Gate` step's env that [D5](design.md#d5) shows.
  Verify: `git grep -n -e bubblewrap -e bwrap -e apparmor_restrict_unprivileged_userns -- .github/workflows/ci.yml` prints a line holding each.

## 6 — The record

- [x] 6.1 In `docs/decisions.md`, D51: write "macOS Seatbelt or Linux bubblewrap" where the first paragraph says "macOS Seatbelt", and, for the last Accepts clause "Linux has no runner until a run starts there", write "on Linux a denied secret reads as empty or missing, not as an error, with the network off loopback is private to the command, not refused, a signal to a process outside fails as no such process, and an untracked file named as Claude Code's Linux sandbox marks is unseen by the clean-tree checks" ([D2](design.md#d2), [D3](design.md#d3)).
  Verify: `git grep -n -i bubblewrap -- docs/decisions.md` prints a line.
- [x] 6.2 In `docs/decisions.md`, D78: delete " · a macOS-only converge until Linux has a runner" from its Accepts, so the line ends "moot." ([D3](design.md#d3)).
  Verify: `git grep -n "macOS-only converge" -- docs/decisions.md` prints nothing.
- [x] 6.3 In `THREAT_MODEL.md` Known gaps, write "A gate that serves on loopback cannot run in a Mac's sandbox, which refuses loopback; under bubblewrap the command has a loopback of its own, so it runs." for the line on a gate that serves on loopback, and "WSL2 is unproven. On Linux the sandbox is bubblewrap, proved by CI's real-sandbox tests; a denied secret reads as empty or missing, and an untracked file named as Claude Code's Linux sandbox marks is unseen by the clean-tree checks." for the line "Linux and WSL2 are unproven" ([D3](design.md#d3)).
  Verify: `git grep -n -i bubblewrap -- THREAT_MODEL.md` prints a line.
- [x] 6.4 In `docs/recipes.md`, the `An OS` recipe: write "A platform other than macOS or Linux." for "A platform other than macOS.", add `bwrap` to its list of OS commands, and add to the port's row `OS` and `side`, the Linux `confine` and `has_sandbox`, `no_sandbox`, `refused` per `OS`, `no_hold`, and `marks`, the worker sandbox's names ([D7](design.md#d7)).
  Verify: `git grep -n bwrap -- docs/recipes.md` prints a line.
- [x] 6.5 In `skills/mf-ship/SKILL.md`, the `sandboxed -- <cmd>` row: write ``under the host's OS sandbox, macOS Seatbelt or Linux bubblewrap,`` for ``under macOS Seatbelt``, and ``when the OS sandbox does not stand (no `sandbox-exec` or `bwrap` on `PATH`, or a `bwrap` that cannot apply one)`` for ``when `sandbox-exec` is not on `PATH` `` ([D3](design.md#d3), [D8](design.md#d8)).
  Verify: `git grep -n -F "Linux bubblewrap" -- skills/mf-ship/SKILL.md` prints the line.
- [x] 6.6 In `skills/mf-ship/SKILL.md` Step 1, after item 2's clause on `git status --porcelain` add "On Linux the run first writes the names Claude Code's sandbox mounts into a worktree to .git/info/exclude." ([D2](design.md#d2)).
  Verify: `git grep -n -F ".git/info/exclude" -- skills/mf-ship/SKILL.md` prints the line.
- [x] 6.7 In `skills/mf-ship/SKILL.md` and `skills/mf-cut-change/SKILL.md`, after "unless it is in clamshell mode." add " Linux has no hold." ([D4](design.md#d4)).
  Verify: `git grep -n -F "Linux has no hold" -- skills/mf-ship/SKILL.md skills/mf-cut-change/SKILL.md` prints a line of each file.
- [x] 6.8 In `skills/mf-ship/scripts/conduct.py` reword these docstrings: "under macOS Seatbelt" of `sandboxed` to "under the host's OS sandbox"; "under Seatbelt with the network open" of the npm runner to "under the OS sandbox with the network open"; "No `sandbox-exec` on `PATH` stops with 2." to "No OS sandbox stops with 2." ([D8](design.md#d8)).
  Verify: `git grep -n -e Seatbelt -e sandbox-exec -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 6.9 In `preconditions` of `skills/mf-ship/scripts/conduct.py` make the scanner's halt `run: cannot run — {SCANNER} is not on PATH`, without the `: brew install {SCANNER}` it ends with today, in `tests/test_conduct.py`, in `test_a_run_without_betterleaks_stops_at_start`, expect `run: cannot run — betterleaks-absent is not on PATH`, and in `skills/mf-ship/SKILL.md` Step 1 item 4 write `betterleaks` for the span `brew install betterleaks` ([D12](design.md#d12)).
  Verify: `git grep -n brew -- skills/mf-ship/SKILL.md skills/mf-ship/scripts/conduct.py tests/test_conduct.py` prints nothing.

## 7 — The private folders

- [ ] 7.1 In `skills/mflib/platform.py` add, after `BWRAP`, `PRIVATE = ("/run", "/tmp")` and `RESOLVER = "/etc/resolv.conf"`, and make `_bwrap` return the prefix of [D3](design.md#d3) as it now stands: after `--proc /proc` a `--tmpfs` for each private folder — each name of `PRIVATE`, resolved, that is a folder and that no root of the policy equals, the temp folder counted as a root —; then, with the network open, a `--ro-bind` of the resolved `RESOLVER` onto itself when it is a file inside a private folder; the roots and the masks as they are; and after the last mask a `--remount-ro` for each private folder, in the same order. `_bwrap` reads `PRIVATE` and `RESOLVER` when it is called, and its docstring's `Why:` gains D21 ([D21](design.md#d21)).
  Verify: `git grep -n -e '^PRIVATE = ("/run", "/tmp")' -e '^RESOLVER = "/etc/resolv.conf"' -e "--remount-ro" -- skills/mflib/platform.py` prints a line holding each.
- [ ] 7.2 In `tests/test_platform.py`, in `test_the_bwrap_command_follows_the_policy`, set `platform.PRIVATE` to two folders the test makes under `tmp_path` and a third name that is absent, and `platform.RESOLVER` to a link whose target is a file inside the first. Expect in every prefix the two `--tmpfs` lines after `--proc /proc` and the two `--remount-ro` lines after the masks, and the resolver's `--ro-bind` after the `--tmpfs` lines in the open-network prefix alone. Add these cases: a policy whose root is the second private folder has no `--tmpfs` and no `--remount-ro` for it; a policy whose temp folder is that folder, the same; a root inside the first is bound after its `--tmpfs`; with the network open, a `RESOLVER` that names a file outside every private folder, and one that is absent, add no line ([D21](design.md#d21), [D22](design.md#d22)).
  Verify: `uv run pytest tests/test_platform.py -q -k bwrap_command` passes.
- [ ] 7.3 In `tests/test_sandboxed.py`, in `test_a_command_runs_under_bwrap_on_linux`, set `platform.PRIVATE` to one folder the test makes under `tmp_path`, and expect its `--tmpfs` after `--proc /proc` and its `--remount-ro` after the `--tmpfs` of the keys ([D21](design.md#d21)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k under_bwrap` passes.
- [ ] 7.4 In `tests/test_sandboxed.py` give `_require_sandbox` a `tmp_path` argument after `host`: on `linux`, where the sandbox stands and `tmp_path` resolved lies inside a resolved folder of `platform.PRIVATE`, it fails with the switch and skips without, as for no sandbox, with the reason `the test folder is in a private folder: set TMPDIR outside /tmp`. Make `real_sandbox` take `tmp_path` and pass it on, and pass `tmp_path` in each call of `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips`, whose `linux` cases set `platform.PRIVATE` to `()`. Add to that test: with `platform.PRIVATE` set to the parent of `tmp_path` and a `bwrap` that exits 0, it fails with the switch and skips without ([D21](design.md#d21)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k required_sandbox` passes.
- [ ] 7.5 In `.github/workflows/ci.yml`, in the `gate` job's `Gate` step, add to its `env` the line that sets `TMPDIR` to the runner's temp folder, written as the expression `runner.temp` in the workflow's double braces ([D21](design.md#d21)).
  Verify: `git grep -n -e "TMPDIR: " -- .github/workflows/ci.yml` prints the line.
- [ ] 7.6 In `tests/test_sandboxed.py` add `test_a_host_socket_is_out_of_reach`, taking `tmp_path` and `real_sandbox`: a Unix listener with a one-second timeout, bound to a path in a fresh folder made by `tempfile.mkdtemp(dir="/tmp")` and removed at the end; a command run through `sandboxed` that connects a Unix socket to that path exits non-zero, and the listener's `accept` then times out. It runs on both sides ([D21](design.md#d21)).
  Verify: `git grep -n "def test_a_host_socket_is_out_of_reach" -- tests/test_sandboxed.py` prints the line.
- [ ] 7.7 In `tests/test_sandboxed.py` add `test_the_private_folders_are_the_commands_own`, taking `tmp_path` and `real_sandbox`, which calls `pytest.skip` where `platform.OS` is `macos`. Through `sandboxed`: a command that prints `os.listdir` of `/run` prints an empty list and exits 0; a command that writes a file in `/tmp` exits non-zero with `Read-only file system` in its output. Then, run with `subprocess.run` behind `platform.confine` of a policy with the first tree as its root, no denied path and the network open: a command that prints what `/etc/resolv.conf` holds exits 0 and prints what the host's file holds, and a command that connects to a Unix listener made as in 7.6 exits non-zero ([D21](design.md#d21)).
  Verify: `git grep -n "def test_the_private_folders_are_the_commands_own" -- tests/test_sandboxed.py` prints the line.
- [ ] 7.8 In `docs/decisions.md`, D51's Accepts, after "is unseen by the clean-tree checks" and before the full stop, add ", the command has a `/run` and a `/tmp` of its own, so a file the host holds there outside the trees is unseen while a host socket elsewhere on disk stays reachable, and a credential created at a denied path after a command starts is readable by it until it ends". In `THREAT_MODEL.md` Known gaps, after the bullet that starts "WSL2 is unproven", add the bullet "Under bubblewrap a command has a `/run` and a `/tmp` of its own, so a host socket there is out of reach; one elsewhere on disk is not. A credential created at a denied path after a command starts is readable by that command until it ends: bubblewrap masks only what exists at the start." ([D21](design.md#d21), [D22](design.md#d22)).
  Verify: `git grep -n -w socket -- THREAT_MODEL.md docs/decisions.md` prints a line of each file.
