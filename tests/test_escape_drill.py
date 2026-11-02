"""The escape drill's verdicts, judged without a worker: no gate runs the drill.

Why: 0054-loopback design D6.
"""

import json
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


def test_judged(tmp_path: Path) -> None:
    judged = runpy.run_path(str(_DRILL))["_judged"]
    refused = {"write": "PermissionError", "ssh": "PermissionError"}
    refused |= {"example": "URLError", "npm": "URLError", "token": "KeyError"}
    results = tmp_path / "results-worker.json"
    results.write_text(json.dumps({**refused, "pypi": "passed", "bind": "OSError"}))
    assert judged(tmp_path, "claude", "worker")
    # The drill's primary declares no `Ship loopback:`: a bind there fails the line.
    results.write_text(json.dumps({**refused, "pypi": "passed", "bind": "passed"}))
    assert not judged(tmp_path, "claude", "worker")
