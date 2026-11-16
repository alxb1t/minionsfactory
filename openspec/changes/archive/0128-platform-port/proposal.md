---
bump: minor
version: v0.102
---

# Platform port

The calls the scripts make on the operating system move into one file, `skills/mflib/platform.py`, the first file of the shared home, and the sandbox profile stops a command from signalling a process outside it.

Reading map: [design](design.md) holds the port's shape, the seed and the decisions, [tasks](tasks.md) its phases: the pin, the home, the move and the fix.

## Why

Today `ps` runs in the conductor, in `awake.py` and in the viewer, both the conductor and `awake.py` start the awake hold, and the conductor alone renders the Seatbelt profile and reads `sysctl`. A second OS has no place to go: each file holds its own macOS call, and the tests fake each one differently.

```
today                                     after
  conduct.py  ── sandbox-exec, sysctl,      conduct.py ─┐
                 caffeinate, ps             awake.py   ─┼─▶ mflib/platform.py ─▶ the OS
  awake.py    ── caffeinate, ps             viewer.py  ─┘
  viewer.py   ── ps
```

The port is the seam [D83](../../../docs/decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate) names first. One file that renders the same policy for another OS later is all a Linux sandbox then needs.

The move is a pure move. The one change in behaviour is the card `0107·S1`: a command run under the sandbox can today signal the conductor and any process the operator owns. That fix is a phase of its own, after the move, so a checker can judge the move alone.

## What Changes

- **The pin.** Cases are added on today's code for each region survivor of the mutants run at the plan: the native-architecture read, the first word of `sandbox-exec`, each awake hold's own session, the stop code of a surviving group, the fetch's captured output, the viewer's `ps` on a failure, the cut's walk ending at pid 1, signal 0 of the liveness probe, and `ps` on an error and on a timeout. CI gains a macOS job that runs the real-sandbox tests and fails when one skips.
- **The home.** `skills/mflib/` is born, with `platform.py` and its first function, the native-architecture read. A script loads it after one seed line. `ty` and `pytest` get `skills/` on their path. `skills/mflib/*` joins the threat model's surfaces. The structure test gains a rule for the seed, a rule for the surfaces, and a port exemption in the OS-command rule.
- **The move.** The sandbox as `confine(policy)`, the refusal text, process inspection and the awake hold follow into `platform.py`. The conductor, `awake.py` and `viewer.py` call them. No assert of a test changes, only the line by which a test reaches a name. The rendered profile stays byte for byte.
- **The fix.** The profile gains `(deny signal)` and `(allow signal (target same-sandbox))`. A test under the real sandbox and a text test in the gate hold the rule.

Requirements the delta touches, one line each:

- ADDED `The platform is reached through one port` — each OS call goes through `skills/mflib/platform.py`, loaded after one seed line.
- MODIFIED `A plain command runs in an OS sandbox` — a command sends no signal to a process outside its sandbox.
- MODIFIED `The gate holds the structure rules` — the OS-command rule names the port file, and new rules hold the seed and the surfaces.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` — the requirements of the list above, in [the delta](specs/sdd/spec.md).

## Impact

- **New:** `skills/mflib/__init__.py`, `skills/mflib/platform.py`, `tests/test_platform.py`.
- **Edited scripts:** `skills/mf-ship/scripts/conduct.py`, `skills/mf-cut-change/scripts/awake.py`, `skills/mf-ui/scripts/viewer.py`.
- **Edited tests:** `tests/conftest.py`, `tests/conduct_load.py`, `tests/test_structure.py`, `tests/test_sandboxed.py`, `tests/test_conduct.py`, `tests/test_awake.py`, `tests/test_viewer.py`.
- **Edited record:** `docs/decisions.md` (D83), `docs/modules.md`, `docs/recipes.md`, `THREAT_MODEL.md`, `pyproject.toml`, `.github/workflows/ci.yml`.
- **Debt:** the card `0107·S1` is paid by the last phase; the release deletes it.
- **After the push, outside this change:** the macOS job is read, and the machine's pin moves past this version only when it is green with the real-sandbox tests run. A red job is a follow-up patch.

## Not in this change

- The Linux runner, its sandbox tool and its probes: when a Linux machine or a cloud session runs the line.
- A fake at the port's level in the tests: it arrives with the second OS. The fakes stay binaries on `PATH`.
- The runners — their timeouts, the process group, the streamed output — and the card `0114·S3` with them: when the executor adapter moves the runner.
- The deny lists, `SECRETS`, `TOKENS`, `NETWORK` and `HOOKS_OFF`: they stay the conductor's data.
- The cards `0112·S1` and `0121·S4`: they do not move with the port.
- Signal sites outside the sandbox's reach: the pin's probe and the plan check's own group.
- Python's bytecode beside the home: no step compares the installed tree to its tag, and git ignores it.
- A package, a build or an install: the shared code is the standard library alone.
