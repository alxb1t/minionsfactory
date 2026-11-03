# Sandboxed gate — the proof

A real Claude worker, in its OS sandbox, ran `make gate` in this worktree once, and it passed, per
[D3](../design.md#d3).

## The run

- **Command**, from this worktree, at `be3b7aa`:
  `uv run --script skills/mf-ship/scripts/conduct.py agent --executor claude "Run make gate in this directory, once, and report its exit code and the last line of its output."`
- **Conductor:** `agent: exit 0 · .minions/runs/agent-20261103-112444.log`, with no `agent: denied` line.
- **Sandbox:** `worker_settings` gives `enabled`, `failIfUnavailable` and `allowUnsandboxedCommands: false`; the worker's
  `Bash` call was `make gate` alone, with no `dangerouslyDisableSandbox`.
- **Tool result:** `is_error: false`, `interrupted: false`, stderr empty.

## The worker's report

- `make gate`: exit 0.
- Last line: `101 passed in 256.31s (0:04:16)`.
