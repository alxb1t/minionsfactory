"""The fake `codex` the `fake_codex` fixture puts on `PATH`: a worker's `--json` events.

It records its argv, acts on the prompt as `fake_worker.py` does, `FAKE_HOST` naming
it, and prints the events `FAKE_CODEX_MODE` names. With `FAKE_CODEX_ROLLOUT` it appends
a `token_count` event to that file: the primary window at `FAKE_CODEX_USED` percent,
the secondary a fifth of it, both resetting at `_RESETS`. Why: 0096-codex-ready
design D2; 0097-cross-model design D7; 0104-codex-limits design D5.
"""

import json
import os
import runpy
import sys
from pathlib import Path

_WORKER = Path(__file__).with_name("fake_worker.py")
_USAGE = {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 100}
_ITEMS = {
    "deny": {
        "type": "command_execution",
        "command": "rm -rf ~/x",
        "aggregated_output": "rm: ~/x: Operation not permitted",
        "exit_code": 1,
        "status": "failed",
    },
    "mcp": {
        "type": "mcp_tool_call",
        "server": "pencil",
        "tool": "draw",
        "status": "completed",
    },
}
_LIMIT = "You've hit your usage limit. Try again at 5:50 PM."
_RESETS = 4_000_000_000


def _window(used: float) -> dict[str, float]:
    return {"used_percent": used, "window_minutes": 300, "resets_at": _RESETS}


def _token_count() -> None:
    """Append a `token_count` event at `FAKE_CODEX_USED` to `FAKE_CODEX_ROLLOUT`."""
    used = float(os.environ["FAKE_CODEX_USED"])
    rates = {"primary": _window(used), "secondary": _window(used / 5)}
    payload = {"type": "token_count", "rate_limits": rates}
    with open(os.environ["FAKE_CODEX_ROLLOUT"], "a") as rollout:
        rollout.write(json.dumps({"type": "event_msg", "payload": payload}) + "\n")


def _print(event: dict[str, object]) -> None:
    print(json.dumps(event), flush=True)


def _codex(args: list[str]) -> int:
    with open(os.environ["FAKE_CODEX_ARGV"], "a") as calls:
        calls.write(json.dumps(args) + "\n")
    if "-C" in args:
        os.chdir(args[args.index("-C") + 1])
    mode = os.environ.get("FAKE_CODEX_MODE", "")
    _print({"type": "thread.started", "thread_id": "fake"})
    os.environ["FAKE_HOST"] = "codex"
    runpy.run_path(str(_WORKER))["_fake"](args[-1])
    if "FAKE_CODEX_ROLLOUT" in os.environ:
        _token_count()
    if item := _ITEMS.get(mode):
        _print({"type": "item.completed", "item": item})
    if mode == "limit":
        _print({"type": "turn.failed", "error": {"message": _LIMIT}})
        return 1
    _print({"type": "turn.completed", "usage": _USAGE})
    return 0


if __name__ == "__main__":
    sys.exit(_codex(sys.argv[1:]))
