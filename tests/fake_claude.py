"""The fake `claude` the `fake_codex` fixture puts on `PATH`, for a Claude worker.

It records its argv and acts on the prompt after `-p` as `fake_worker.py` does.
Why: 0097-cross-model design D7.
"""

import json
import os
import runpy
import sys
from pathlib import Path

_WORKER = Path(__file__).with_name("fake_worker.py")


def _claude(args: list[str]) -> int:
    with open(os.environ["FAKE_CLAUDE_ARGV"], "a") as calls:
        calls.write(json.dumps(args) + "\n")
    os.environ["FAKE_HOST"] = "claude"
    runpy.run_path(str(_WORKER))["_fake"](args[args.index("-p") + 1])
    return 0


if __name__ == "__main__":
    sys.exit(_claude(sys.argv[1:]))
