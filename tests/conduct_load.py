"""Load the conductor script into a fresh module, compiling it once.

Why: 0127-test-cost design D2.
"""

import sys
import types
from pathlib import Path
from typing import Any

_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-ship"
    / "scripts"
    / "conduct.py"
)
_CODE = compile(_SCRIPT.read_text(), str(_SCRIPT), "exec")


def conduct() -> dict[str, Any]:
    """Return the names of a fresh run of the conductor script, as `runpy` does."""
    module = types.ModuleType("<run_path>")
    module.__file__ = str(_SCRIPT)
    old = sys.modules.get("<run_path>")
    sys.modules["<run_path>"] = module
    try:
        # why: the conductor's compiled source, run as `runpy` runs it
        exec(_CODE, module.__dict__)  # noqa: S102
    finally:
        if old is None:
            del sys.modules["<run_path>"]
        else:
            sys.modules["<run_path>"] = old
    return dict(module.__dict__)
