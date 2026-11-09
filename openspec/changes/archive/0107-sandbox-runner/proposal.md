---
bump: minor
version: 0.89
beside: [0106-cut-scripts]
---

# Sandbox runner

`conduct.py` gains `sandboxed()`: it runs one plain command — a gate, a check script, a `Verify:` line — under macOS Seatbelt,
writing only to the version's trees, reading no credential, with no network, and failing closed where no OS sandbox stands.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Why

The gate, `gate_check.py` and `plan_check.py` run today inside an LLM conductor's own sandbox ([design](design.md#context), F1).
The next change turns that conductor into a script, which runs outside any sandbox, and D51 says a builder's code never does
([D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)). The tool evidence that follows it
needs the same runner. No wrapper for a plain command exists (F2). This change delivers it alone, so a person and the tests
can run it before anything depends on it.

## What Changes

- **The runner** — `sandboxed(argv, cwd, trees)` in `skills/mf-ship/scripts/conduct.py` builds a Seatbelt profile from the
  lists `worker_settings` already holds, and runs `argv` under `sandbox-exec` with no network and `UV_OFFLINE=1`.
- **Fail closed** — no `sandbox-exec` stops the command with exit 2 and `no OS sandbox`; the command never runs bare.
- **The exit** — the command's exit code passes through. A refusal in its output gets one `sandboxed: denied —` line.
- **The command** — `conduct.py sandboxed -- <cmd>` runs it in the current directory over the version's trees.
- **The record of decisions** — D51 amended in `docs/decisions.md`; `skills/mf-ship/SKILL.md`'s command table gains a row.
- **The tests** — `tests/test_sandboxed.py`: a fake `sandbox-exec` proves the profile, the environment, the exit and the
  halt; the real-Seatbelt tests apply the real one and skip where it cannot nest.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A plain command runs in an OS sandbox* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `docs/decisions.md` and adds
`tests/test_sandboxed.py`. Nothing calls `sandboxed()` yet but its own command.

Dependencies: none. The gate recipe stays unchanged. `0106-cut-scripts` opens `conduct.py` too, in other functions and the
same `main`: a merge there is a text merge ([design](design.md#risks--trade-offs)).

## Not in this change

- A caller of `sandboxed()`: the converge script and the evidence step run it when they land.
- Linux: bubblewrap waits for a run on Linux, when a target repo's operator has no `sandbox-exec`.
- Network by host: Seatbelt cannot filter by name, so a command that needs the network fails.
- A change to a Claude or Codex worker's own sandbox ([D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)
  keeps them).
