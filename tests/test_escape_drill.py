"""The escape drill's verdicts, judged without a worker: no gate runs the drill.

Why: 0054-loopback design D6.
"""

import runpy
from pathlib import Path

_DRILL = Path(__file__).with_name("escape_drill.py")


def test_codex_held() -> None:
    held = runpy.run_path(str(_DRILL))["_codex_held"]
    marks = ["codex-notify", "codex-mcp"]
    assert held(marks, [], False)
    # Each is a way the untrusted start failed, or proved nothing.
    assert not held([], [], False)
    assert not held(marks, ["codex-mcp"], False)
    assert not held(marks, [], True)
