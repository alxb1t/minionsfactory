# Linux runner — design

The port gets a Linux side beside Seatbelt, its callers word no OS tool, a run on Linux hides the sandbox's marks, and CI proves real `bwrap`. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`skills/mflib/platform.py` is the one file that names an OS tool, since `0128-platform-port`. Its sandbox side is Seatbelt alone, so `sandboxed()` and the npm fetch stop with exit 2 on Linux, and converge's first command cannot run. A probe in the cloud ran the line to the tag push under a stand-in `bwrap`; this change makes that stand-in the port's own side and proves it in CI.

**after** [0130-small-fixes](../0130-small-fixes/design.md): it replaces the real-sandbox case of the cut's hold with `test_a_signal_between_siblings_is_delivered`, which phase 5 here runs under `bwrap`. The real-sandbox tests of `tests/test_sandboxed.py` are, after it, the write, the secret, the network, the signal outside, the signal to the command's own child and the signal between siblings.

```
conduct.py / awake.py            skills/mflib/platform.py
  confine(policy) ───────────▶   OS = "macos"  → sandbox-exec -p <profile>
  has_sandbox / no_sandbox ──▶   OS = "linux"  → bwrap <mounts> <namespaces> --
  refused(text)  ────────────▶   one name, read once; every test sets it
  has_hold / no_hold ────────▶
  marks()        ────────────▶   the names Claude Code's Linux sandbox mounts
```

## Goals / Non-Goals

- **Goals:** `sandboxed()` and the npm fetch run on Linux under `bwrap`; no caller names an OS tool for a reason the port words; a run's clean-tree checks pass beside the Linux sandbox's marks; CI's Linux job runs the real-sandbox tests.
- **Non-Goals:** the cloud's steps, Codex's Linux sandbox, an awake hold on Linux, a container, WSL2, a second port file. See [the proposal](proposal.md#not-in-this-change).

## Decisions

`D<n>` here is the brief's `Q<n>`. `D12` is the cut's, for a hint the brief names and does not word. The brief's `C` rows are the cut's plan-review fixes of tasks; they add no design decision.

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The cloud is usable right after this version: one version a session, every station on Claude, on a session setup script — `gc.auto` in the global config, signing off, MF installed at its tag, uv at the repo's version, the poll that keeps the VM up — and the tag made and pushed from the MacBook by hand at each release | the person: the cloud as soon as possible | — |
| [D2](#d2) | The names of Claude Code's Linux sandbox are this version's: on Linux a run writes the missing ones into the clone's `.git/info/exclude` before its first clean-tree check. Accepted: on Linux an untracked file of those names is unseen by the clean-tree checks. Nothing is written on macOS | every cut on Linux halts on them, in the cloud or not; one write covers the scripts' checks and the skills' prose alike | a global excludes file: it hides the names in every repository on the machine |
| [D3](#d3) | The Linux sandbox holds the policy by other means, and these differences are accepted: a denied secret reads as empty or missing, not as an error; with the network off, loopback is private to the command, not refused; a signal to a process outside fails as no such process | the same protection — no content read, nothing outside reached, nothing outside signalled — with another error | — |
| [D4](#d4) | No awake hold on Linux; the run's start line and the cut's say `awake: not held — no hold on Linux` | a cloud VM pauses when its session idles, which a hold cannot stop; a hold matters on a laptop | `systemd-inhibit` |
| [D5](#d5) | The proof is real `bwrap` in CI's Linux job — the real-sandbox tests fail there when they skip — then probe 4 in a cloud session after the release, started by the person from a prepared prompt | no worker's gate runs a real sandbox; the port's own lesson | a fake `bwrap` as the proof |
| [D6](#d6) | A minor, built on Opus 5.5 high with both Codex checkers, chained `after: 0130-small-fixes` | the sandbox is the line's security boundary | — |
| [D7](#d7) | The Linux side lives in `skills/mflib/platform.py`; the port reads the host's OS once, into one name, and every test sets that name — none reads the host's | the structure rules pass as written and D83 names one file; the gate's 100% of a change's lines must hold on both systems | a second port file |
| [D8](#d8) | On Linux the sandbox check passes only when `bwrap` applies a trivial sandbox, probed once a process. The reasons "no sandbox" and "not held" are the port's to word, so the conductor and the cut's hold name no OS tool for them | a `bwrap` that cannot make a namespace must stop a run as "no sandbox", not read as a red gate; the OS rule's list shrinks | `bwrap` on `PATH` as the check |
| [D9](#d9) | The refusal's texts are per OS: on Linux a write outside reads `Read-only file system` | the denied line and its test rest on the text | — |
| [D10](#d10) | Out: a stale claim whose leader's name is `node`, and a cut by hand on Linux outside a run | the cloud's `claude` reads as `claude`; a queued cut passes through a run's start | — |
| [D11](#d11) | The table is confirmed, and this version is queued chained after `0130-small-fixes` | the person, 2026-11-16 | — |
| [D12](#d12) | The scanner's halt at a run's start names the tool and no package manager | `brew` is a Mac's; the pinned version is `AGENTS.md`'s | a hint per OS |

### D1

A statement of scope, with no task. After this version a cloud session ships one version on its setup script; the tag push, `gc.auto` and the fetch stay the session's and the person's, and the next version removes them.

### D2

`MARKS` in the port holds `.bash_profile`, `.bashrc`, `.claude`, `.gitconfig`, `.gitmodules`, `.idea`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode`, `.zprofile` and `.zshrc`, each a bare name, as the probe wrote them. `marks()` returns them on Linux and none on macOS.

`conduct.py` gains `_hide_marks(common)`, called in `preconditions` before its first `_dirty`. It opens `info/` under the common git directory through `_folder_fd` and `exclude` with `O_RDWR | O_CREAT | O_NOFOLLOW`. It reads the lines and appends each mark no line equals, a newline first when the file does not end with one; with every mark present it writes nothing.

A link at `info` or at `exclude` stops the run with exit 2: the conductor runs outside the sandbox, and a worker can write the common directory.

### D3

On Linux `confine` returns this prefix; the caller appends the command. Each path is resolved as the profile resolves it, a root or a denied path that does not exist is left out, and a denied path that is a folder is masked by `--tmpfs`, any other by `--ro-bind /dev/null`.

```
<bwrap> --ro-bind / / --dev /dev --proc /proc
        --bind <root> <root> …              each writable root, then the temp folder, in order
        --tmpfs <dir> | --ro-bind /dev/null <file>   …   each denied path, last
        --unshare-pid  [--unshare-net]  --die-with-parent  --new-session  --
```

`--unshare-net` is absent when the policy opens the network. The disk is read-only, so a write outside the roots fails with `Read-only file system`. The PID namespace makes a process outside unseen: a signal to it fails with `No such process`, which is card `0107·S1`'s equal.

### D4

`has_hold()` is false on Linux whatever is on `PATH`, and `no_hold()` returns `no hold on Linux`; on macOS it returns the literal `caffeinate not on PATH`, whatever `CAFFEINATE` holds, as the tests that set the tool absent expect. `hold_awake` is not reached on Linux: both callers test `has_hold()` first.

### D5

`MF_REQUIRE_SEATBELT` becomes `MF_REQUIRE_SANDBOX`, set by CI's macOS job and its Linux job. The Linux job installs `bubblewrap`, opens user namespaces and sets the switch for the gate step, so the real-sandbox tests run inside `make gate` and fail when `bwrap` cannot apply a sandbox. The person starts probe 4 after the release; it is no task.

```diff
+      - name: Install bubblewrap
+        run: sudo apt-get update && sudo apt-get install -y bubblewrap
+
+      - name: Allow user namespaces for bwrap
+        run: sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
+
       - name: Gate
+        env:
+          MF_REQUIRE_SANDBOX: "1"
         run: make gate DIFF_BASE=origin/main
```

### D6

The models of this version are `models.toml`'s, not a task. The build, converge and checkers are those the brief names.

### D7

`side(system)` returns `linux` for a name starting `linux` and `macos` for any other, and `OS = side(sys.platform)` is the only read of the host. Each port function reads `OS` when it is called. `tests/conftest.py` holds `HOST = platform.OS` from its import, an autouse fixture sets `OS` to `macos` for every test, and a test of the Linux side sets `linux`.

The fixture `real_sandbox` is the one place a test takes the host's name: it sets `OS` to `HOST`, so a real-sandbox test runs the side its host has. Every other test runs the same on either host, with a fake `sandbox-exec` or a fake `bwrap` first on `PATH`. A gate on a Mac and a gate on Linux therefore cover the same lines of the port.

### D8

`has_sandbox()` on Linux runs the prefix `confine` builds for an empty policy, ended with `true`, under a timeout; it is true on exit 0. It is read through `functools.cache` keyed on the `bwrap` path, so a process probes once and a test with its own fake path probes afresh. On macOS it stays a `PATH` check.

`no_sandbox()` returns the text after `no OS sandbox:` — `sandbox-exec is not on PATH` on macOS; on Linux `bwrap is not on PATH` when none is found, else `bwrap cannot apply a sandbox here`. The conductor's `_no_sandbox()` builds the `Stop` from it for both its sites. `no_hold()` is D4's.

### D9

`REFUSALS` maps `macos` to `Operation not permitted` and `linux` to `Read-only file system`, and `refused(text)` reads the entry of `OS`. The text `Operation not permitted` is not a refusal on Linux, and the Linux text is none on macOS.

### D10

A statement of scope, with no task.

### D11

A statement of the plan's close, with no task.

### D12

`preconditions` halts `run: cannot run — betterleaks is not on PATH`, and `skills/mf-ship/SKILL.md` says to halt naming `betterleaks`. The pinned version is in `AGENTS.md`.

## Tests

Each test sits at the lowest layer that can fail. The Linux lines of the port run on any host under a fake `bwrap`; the real ones run in CI's macOS and Linux jobs. No test boots a browser, and no end-to-end test is added.

| test | file | layer | holds |
|---|---|---|---|
| the fixtures `host`, `macos_side` and `fake_bwrap` | `tests/conftest.py` | fixture | the host's name once, the macOS side under every test, a `bwrap` that records its arguments and runs the command |
| `test_the_side_names_linux_and_else_macos` | `tests/test_platform.py` | unit | `side` of `linux` and `linux2` is `linux`; of `darwin` and `freebsd`, `macos` |
| `test_the_bwrap_command_follows_the_policy` | `tests/test_platform.py` | unit | the order of [D3](#d3): roots then the folder, a denied folder, file and absent path, the network open and shut, no folder, an absent root |
| `test_the_sandbox_stands_on_linux_when_bwrap_applies_one` | `tests/test_platform.py` | unit | no `bwrap`, one exiting non-zero, one passing, and a probe run once however often it is asked |
| `test_a_refusal_is_read_on_its_own_side` | `tests/test_platform.py` | unit | each text on its OS and not on the other |
| `test_the_reasons_are_the_ports` | `tests/test_platform.py` | unit | `no_sandbox` on both sides and both Linux causes, `no_hold`, and `has_hold` false on Linux with a `caffeinate` present |
| `test_the_marks_are_the_linux_sandboxs` | `tests/test_platform.py` | unit | the names of [D2](#d2) on Linux, none on macOS |
| `test_a_command_runs_under_bwrap_on_linux` | `tests/test_sandboxed.py` | integration | `sandboxed` puts the prefix of [D3](#d3) before the command, which runs |
| `test_no_bwrap_stops_with_2` | `tests/test_sandboxed.py` | integration | exit 2, `no OS sandbox` and `bwrap`, nothing run |
| `test_a_linux_denial_gets_the_line` | `tests/test_sandboxed.py` | integration | `Read-only file system` with a failing exit prints the denied line; the macOS text does not |
| `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips` | `tests/test_sandboxed.py` | integration | the switch on both sides |
| the real-sandbox tests | `tests/test_sandboxed.py` | integration | made OS-aware: the refusal text, the signal text and the secret's content per side |
| `test_a_cut_on_linux_says_it_holds_nothing` | `tests/test_awake.py` | integration | `awake: not held — no hold on Linux`, nothing recorded, exit 0 |
| `test_a_run_on_linux_holds_nothing_and_says_so` | `tests/test_conduct.py` | integration | `_hold_awake` and the run's `start` line |
| `test_a_start_on_linux_writes_the_marks_into_the_exclude` and its cases | `tests/test_conduct.py` | integration | the file absent, partly written, whole, without a final newline, a link at `info` and at `exclude`, macOS writing nothing, and the clean-tree check passing beside `.bashrc` |
| `test_check_os_fails_on_bwrap_in_an_unlisted_file` | `tests/test_structure.py` | unit | `bwrap` is an OS word |

- **Counted by** `git diff 0130-small-fixes --stat -- tests`: the table's rows.
- **End to end:** none added. T1: each case is at the lowest layer that fails. T2: the real-sandbox tests exist; the Linux job runs them, and no new end-to-end state is made.
- **Runs added:** the real-sandbox tests on CI's Linux job, once each, by `uv run pytest tests/test_sandboxed.py -q` under `MF_REQUIRE_SANDBOX`.
- **Removed:** `test_a_required_seatbelt_that_cannot_apply_fails_and_else_skips`, renamed, mapped below.

| removed | carried by |
|---|---|
| `test_a_required_seatbelt_that_cannot_apply_fails_and_else_skips` | `test_a_required_sandbox_that_cannot_apply_fails_and_else_skips` carries its assertions: a required sandbox that cannot apply fails, an optional one skips |

## Dependencies

None.

## Risks / Trade-offs

- How `bwrap` behaves on the runner and in the cloud is not proven by reading: the texts of its refusals, user namespaces on Ubuntu 24.04 and whether `git worktree remove` passes with the sandbox's `.claude/` left behind. Phase 5 reads the texts and the namespaces in CI, and probe 4 the removal.
- The kill of a command past its deadline rests on `--die-with-parent`; no CI case runs it under real `bwrap`. Probe 4 reads it.
- A worker's own gate skips the real-sandbox tests where its sandbox refuses a nested one, so the proof is CI after the push. A red job is a follow-up patch, and the pin stays at its tag until it is green.
- The probe is cached for a process: a `bwrap` that breaks mid-run reads as a red command, not as "no sandbox".
- The disk is readable under `--ro-bind / /`, as Seatbelt's `(allow default)` leaves it; the denied paths are masked, and nothing else is hidden.
- The npm fetch runs with the network open, so it unshares no network on Linux, as the profile omits the denial on a Mac.
- On Linux an untracked file named as one of [D2](#d2)'s marks is unseen by the clean-tree checks; D51 records it.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the side, the Linux side, the callers, the names, the real proof, the record.
