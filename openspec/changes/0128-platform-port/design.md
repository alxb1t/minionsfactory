# Platform port — design

The scripts' OS calls move into one port, `skills/mflib/platform.py`, in a pin, a home, a move and a fix. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Where each OS call is today, at the base of this change:

| piece | where | after |
|---|---|---|
| the sandbox's profile, `_profile` | `skills/mf-ship/scripts/conduct.py:3306-3335` | replaced by `profile` and `confine` |
| the `sandbox-exec` lookup, `_sandbox_exec` | `skills/mf-ship/scripts/conduct.py:3338-3344` | replaced by `has_sandbox` |
| the `sandbox-exec -p` sites | `sandboxed` at `conduct.py:3418`, `_fetch_run` at `conduct.py:7269` | each calls `confine` |
| the refusal text, `CODEX_DENIAL` | `conduct.py:247`, read at `conduct.py:3434`, `:3817`, `:3830` | replaced by `refused` |
| the native-architecture read, `_native` | `conduct.py:2391-2407`, read at `:2450` and `:6387` | replaced by `arch` |
| the conductor's awake hold, `_hold_awake` | `conduct.py:4254-4269`, `CAFFEINATE` at `conduct.py:214` | stays, calls `hold_awake`; the constant is removed |
| the cut's awake hold | `skills/mf-cut-change/scripts/awake.py:91-121`, `CAFFEINATE` at `awake.py:20` | calls `hold_awake`; the constant is removed |
| each `ps` reader | `_ps` at `conduct.py:4272-4286`, `_ps` at `awake.py:56-64`, `run_ps` at `skills/mf-ui/scripts/viewer.py:875-884` | replaced by `process`; `run_ps` stays and calls it |
| the liveness probe, `_started` | `conduct.py:4289-4302` | stays, reads through `process` |

What the plan measured:

- **The mutants** run on this region left survivors and unreached lines: they are the pin.
- **The seed:** one `sys.path.insert` call, then `import mflib.platform`, passes `ruff` and `ty`; `ty` needs `skills/` as an extra path for `tests/`.
- **The rule for `0107·S1`,** in a plain terminal on macOS 27: `(deny signal)` then `(allow signal (target same-sandbox))` refuses a signal, signal 0 included, to a process outside, and lets a command signal its own child. `(deny signal (target others))` refuses nothing.

The structure test of [0124](../../../docs/decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate) reads every string of a script for an OS word, and has no exemption for a home file. Its `OS_NAMES` list holds a pair for each file and OS command it allows. The home's seat, `skills/mflib/`, is already in its `_SEATS`.

```
phases    1 pin ─────▶ 2 home ─────▶ 3 move ─────▶ 4 fix
          today's code  mflib born    names follow  0107·S1
          cases red     arch first    asserts stay  profile text
          CI macOS job  rules, seed   OS_NAMES      real sandbox
                                      shrinks       holds it
```

## Goals / Non-Goals

**Goals**

- Every OS call of a script goes through `skills/mflib/platform.py`.
- The move changes no behaviour a test or an operator can see, save the named ones in [D5](#d5).
- The gate holds the seed, the surfaces and the port's exemption.
- A command run under the sandbox cannot signal a process outside it.

**Non-Goals**

- The Linux side of the port, and a fake of the port in the tests.
- The runners: they stay in the conductor with their timeouts, group and streamed output.
- The deny lists: `SECRETS`, `TOKENS`, `NETWORK` and `HOOKS_OFF` stay the conductor's data.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The port is `skills/mflib/platform.py`, the first file of the home `skills/mflib/` | Linux is then one file that renders the same policy; the pin's export carries the folder and its link rule skips it | a loose `platform.py` beside the scripts, which hides the standard library's; a Python package, which needs a build and an install |
| [D2](#d2) | A script loads the port after one seed line; `ty` and `pytest` get `skills/` on their path | `ty` then checks calls across files, which `runpy` hides; no build, so [D55](../../../docs/decisions.md) holds | `runpy`, which hands back a dict; `from mflib import platform`, whose edge the structure test cannot see; a four-line seed that stops bytecode |
| [D3](#d3) | `confine(policy)` takes a `Policy` and returns the command's prefix; `profile(policy)` renders today's text | each OS renders the same policy; a Linux stand-in had to parse the profile text to recover it | a policy that is the profile text |
| [D4](#d4) | The port's other members are `refused`, `arch`, `process`, `has_sandbox`, `has_hold`, `hold_awake` and `CAFFEINATE` | the smallest port that holds what moves; each is a call a script makes on the OS today | a class holding the OS; a function per OS command |
| [D5](#d5) | One `ps` reader, `process`, in the conductor's way | the readers differ only by accident; one is covered by the pin | the readers kept apart |
| [D6](#d6) | A caller keeps its operator messages and the order of its checks | no operator sees a changed line; `OS_NAMES` keeps a pair only where a file keeps the word in a message | the port printing a message |
| [D7](#d7) | The pin comes first, on today's code, each case seen red under its named change | a move is judged by an unchanged assert, and an assert that cannot fail judges nothing | pinning after the move |
| [D8](#d8) | In the move no assert changes; a test reaches a moved name through `mflib.platform`; the fakes stay binaries on `PATH` | an unchanged assert over moved code is the proof the move changed nothing | a fake of the port; a split of `tests/test_conduct.py` |
| [D9](#d9) | The OS-command rule exempts the port; `OS_NAMES` shrinks; the seed rule and the surfaces rule join | the port is the one place an OS command may be named; a list may not grow | an allowlist entry for the port |
| [D10](#d10) | The record agrees: D83, the map, the OS recipe and the threat model's surfaces | a decision is edited where it lives; the map and the recipes are held to the tree | a new decision for the port |
| [D11](#d11) | The fix of `0107·S1` is a signal rule between the write allow and the read deny, in a phase after the move | a checker judges a pure move; the lines arrive in a new file | the fix inside the move; `(deny signal (target others))`, which refuses nothing |
| [D12](#d12) | CI gains a macOS job that runs `tests/test_sandboxed.py` and fails where a real-sandbox test would skip | the real-sandbox tests skip in a worker's gate and on Ubuntu, so the fix has no other automatic proof | a skip that passes |

### D1

`skills/mflib/__init__.py` holds a docstring only. `skills/mflib/platform.py` holds the port. The module map gives both a `home` row. Both are standard library alone, so no step installs anything.

### D2

The seed is the one statement, placed after the script's other imports and before its first `mflib` import:

```
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.platform
```

`resolve()` follows an installed link into the pinned tree, so `parents[2]` is that tree's `skills/`. A script run by `runpy` or by the tests' loader has `__file__`, so the same line works there. A `noqa` on it fails `RUF100`.

`pyproject.toml` gains `[tool.ty.environment] extra-paths = ["skills"]` and, under pytest's settings, `pythonpath = ["skills"]`. Each run of a seeded script in one process adds one entry to `sys.path`; the tests' loader `tests/conduct_load.py` runs the conductor many times, so it restores the path after each run.

### D3

```python
class Policy(NamedTuple):
    writes: tuple[Path, ...]  # writable roots, in order
    denied: tuple[Path, ...]  # paths neither read nor written
    network: bool = False  # True leaves the network open
    tmp: Path | None = None  # the command's temporary folder: writable, after `writes`
```

`profile(policy)` replaces `_profile` and renders the Seatbelt text exactly as it does today: each root and each denied path resolved and quoted, the devices as literals, a later rule beating an earlier one. `confine(policy)` returns `[<the path `shutil.which` finds for sandbox-exec>, "-p", profile(policy)]`: the full path, since `_fetch_run` runs with an `env` of its own whose `PATH` decides where `subprocess` looks. The conductor builds the policy from `SECRETS` and the home through one function, `_policy(trees, home, network=False, tmp=None)`. `sandboxed` passes the command's temporary folder as `tmp`, so the writable roots read `[*trees, tmp]`, as before.

A literal test holds the profile byte for byte. It is written in the pin on today's text and re-pointed in the move.

### D4

| member | does | goes |
|---|---|---|
| `refused(text)` | whether the OS's refusal, `Operation not permitted`, is in `text` | replaces `CODEX_DENIAL` |
| `arch()` | the host's native architecture: `sysctl -n hw.optional.arm64` printing `1` gives `arm64`, else `os.uname().machine`, which also answers when `sysctl` cannot run | replaces `_native` |
| `process(pid, field)` | `ps -o <field>= -p <pid>`, the field's text | replaces each `ps` reader |
| `has_sandbox()` | whether `sandbox-exec` is on `PATH` | replaces the lookup of `_sandbox_exec` |
| `has_hold()` | whether `caffeinate` is on `PATH` | replaces each hold's lookup |
| `hold_awake(pid, seconds=None)` | starts `caffeinate -is [-t seconds] -w pid` in a session of its own, its streams closed, and returns the process | replaces each hold's start |
| `CAFFEINATE` | the tool's name, public so a test can name an absent one | replaces each constant of the same name |

### D5

`process` is the conductor's reader: `ps` with `LC_ALL=C` and `TZ=UTC0`, a timeout of 60 s, and an empty string when `ps` cannot start or times out. `awake.py` and the viewer take it. Their named differences:

- Where `ps` is absent or hangs, each used to end in a traceback and now reads no process: `awake.py` prints `awake: not held — no host process`, and the viewer's `stop` reads a stale file.
- Their timeouts, 600 s and 5 s, become 60 s.

No test or operator line holds either.

### D6

The conductor's `_hold_awake` stays, as the one place that prints `awake: held` and `awake: not held — caffeinate not on PATH`. It asks `has_hold()` first. `awake.py`'s `_start` asks `has_hold()` before it looks for a host, so with both missing it still prints the `caffeinate` line first. `sandboxed` asks `has_sandbox()` at the place `_sandbox_exec` was asked before and is now removed, ahead of the run-folder check and the temporary folder, and stops with 2 with the same line. `_fetch_run` stops the same way, after the policy is built.

### D7

Each case of the pin is written on today's code, reaches the name through `_conduct()` or the script's own module, and is seen red under the change its task names: the change is applied, the case fails, the change is restored. The build's commit body names each case and its change. The cases that fake an OS tool put a binary of that name first on `PATH`.

### D8

In the move phase a test line changes only by how it reaches a name:

- `conduct["_profile"](a, b)` is replaced by `platform.profile(conduct["_policy"](a, b))`.
- `conduct["_ps"](pid, "lstart=")` is replaced by `platform.process(pid, "lstart")`.
- A test that sets `CAFFEINATE` sets it on the port through `monkeypatch`, since the port is one module for every test of a process.

The fake `sandbox-exec` becomes stricter in the pin: it refuses a first word that is not `-p`. The deny-list literals stay in `tests/test_sandboxed.py`. The native-architecture tests reach `platform.arch()` from the phase that moves it.

### D9

- `check_os` skips `skills/mflib/platform.py`.
- `OS_NAMES` keeps a pair only where a file still holds the word in an operator's message: `conduct.py` for `caffeinate`, `ps` and `sandbox-exec`, and `awake.py` for `caffeinate`. The `sysctl` pair and the `ps` pairs of `awake.py` and `viewer.py` go.
- `check_seed` fails a script under `skills/` whose first `mflib` import has no seed statement before it.
- `check_surfaces` fails a Python file under `skills/` that matches no glob of the threat model's `## Surfaces`.

The seed and surfaces rules start with no exception. Each rule takes the root as its argument, so a planted-breach twin passes its own tree.

### D10

`docs/decisions.md` D83 names the port file and says the rules hold the seed and the surfaces. `docs/modules.md` gains a `home` row for each file of `skills/mflib/` and the new names cells. `docs/recipes.md` `## An OS` names `skills/mflib/platform.py` as the file an OS edits. `THREAT_MODEL.md` `## Surfaces` gains a `skills/mflib/*` line.

### D11

The rule sits after `(allow file-write* …)` and before `(deny file-read* file-write* …)`: `(deny signal)`, then `(allow signal (target same-sandbox))`. No existing assertion of the profile's shape changes: the version, default-allow and write-deny lines, the allow line, the deny line and the last line stay where they are.

- The literal test of [D3](#d3) changes in this phase, as it holds a changed text.
- The proof is a test of the text in the gate, and tests under the real sandbox, which skip where a profile cannot apply.

### D12

The job runs on `macos-latest` with the same SHA-pinned actions as the gate and runs `uv run pytest tests/test_sandboxed.py -q` with `MF_REQUIRE_SEATBELT=1`. The `real_sandbox` fixture then fails instead of skipping when a profile cannot apply. The job is not `make gate`: the secret scanner has no asset for it.

## The port in one view

```
conduct.py ──┐ _policy, _hold_awake, sandboxed, _fetch_run, _started, _clear
awake.py   ──┼──▶ mflib.platform ──▶ sandbox-exec · caffeinate · sysctl · ps
viewer.py  ──┘     Policy profile confine has_sandbox refused arch
                   process has_hold hold_awake CAFFEINATE

stays in the callers: the messages, the deny lists, the runners, the claim,
                      the liveness probe's signal 0, HOLD_SECONDS
```

## Tests

The change adds tests and removes none: no test is deleted or merged, so no `I16` table is due. Counts of `def test_` before the change, by `git grep -c "^def test_" -- tests/test_structure.py tests/test_awake.py tests/test_sandboxed.py tests/test_viewer.py tests/test_conduct.py tests/test_platform.py`: `tests/test_structure.py` 37, `tests/test_awake.py` 3, `tests/test_sandboxed.py` 20, `tests/test_viewer.py` 26, `tests/test_conduct.py` 192, `tests/test_platform.py` none. The build prints the same command at the end.

| layer | file | added |
|---|---|---|
| unit | `tests/test_platform.py` | the native architecture with a fake `sysctl` printing each answer, and the `uname` fallback; `ps` on an error and on a timeout |
| unit | `tests/test_structure.py` | the seed rule, the surfaces rule and the port exemption, each with a planted-breach twin and a passing twin |
| unit | `tests/test_sandboxed.py` | the profile's text byte for byte; the profile's signal rule; the fixture's fail-or-skip choice |
| integration | `tests/test_conduct.py` | the fetch under the strict fake; the stop code of a surviving group; signal 0 of the liveness probe; the conductor's hold in a session of its own |
| integration | `tests/test_awake.py` | the cut's hold in a session of its own; the walk ending at pid 1; both tools missing |
| integration | `tests/test_viewer.py` | `run_ps` on a failing `ps` |
| end-to-end | `tests/test_sandboxed.py` | under the real sandbox: a signal to an outside process is refused, one to the command's child passes, the cut's hold is released |
| support | `tests/conftest.py` | the fake `sandbox-exec` refuses a first word that is not `-p` |
| support | `tests/conduct_load.py` | the loader restores `sys.path` after each run of the conductor |

The end-to-end runs it adds: one CI job, `macos`, running `tests/test_sandboxed.py` on one engine, the real Seatbelt: the real-sandbox tests × 1.

- **Reason** ([T1](../../../skills/mf-build/SKILL.md)): only the real sandbox shows that a profile applies.
- **Placement** ([T2](../../../skills/mf-build/SKILL.md), [T3](../../../skills/mf-build/SKILL.md)): the new real-sandbox tests extend the file that holds the ones that exist, and each stands alone.
- **Cost:** each test is under 5 s, so none takes the `slow` marker. No target test rule conflicts with `T1`–`T6`.

## Dependencies

None.

## Risks / Trade-offs

| risk | what holds it |
|---|---|
| A hosted macOS runner may not apply a profile, or may bill the repo | the job fails loudly under `MF_REQUIRE_SEATBELT`; a red job is a follow-up patch. Whether the repo is public was not checked at the cut: the cut's sandbox reaches no GitHub API |
| The signal rule stops a sandboxed command that signals a process it did not start | the sites that signal are `awake.py`'s release of its own child, the plan check's own group and the pin's probe, which reads a refused signal 0 as alive; the real-sandbox test runs the release |
| The real-sandbox tests of the fix skip in a worker's gate, so their first real run is the macOS job | the text test of the rule stands in the gate; a red job is a follow-up patch |
| The release of the cut's hold rests on `same-sandbox` covering a process that a sibling process started; the plan measured a command's own child alone | the real-sandbox test of the hold is the first measure; a red job is a follow-up patch |
| The seed adds one `sys.path` entry per run in one process | the tests' loader restores the path after each run |
| A moved line has no test, and the gate asks 100% of changed lines | the pin covers the `uname` fallback and the `ps` error and timeout, the lines the plan found unreached |
| The pin's cases pass for the wrong reason | each is seen red under a named change before it is kept |

## Verdict

The port is one file, its seams are named, each move is held by an unchanged assert and the one fix has its own phase. Ready to build.
