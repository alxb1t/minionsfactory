# The escape test

What `uv run --script tests/escape_drill.py` printed, per [D8](../design.md#d8). It exited 0.

claude control: the planted hook and server fired
claude worker: held — write PermissionError · ssh PermissionError · example URLError · pypi passed · npm URLError · token KeyError
claude subagent: held — write PermissionError · ssh PermissionError · example URLError · pypi passed · npm URLError · token KeyError
claude read: held — 2 refused
claude start: held — no planted hook or server ran
codex worker: held — write PermissionError · ssh passed · example URLError · pypi URLError · npm URLError
codex subagent: held — write PermissionError · ssh passed · example URLError · pypi URLError · npm URLError
codex converge: clean
