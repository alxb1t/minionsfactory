# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the number of tests pytest collects in this repository.

Why: 0030-change-impact design D7.
"""

import re
import subprocess
import sys


def collected(stdout: str, returncode: int) -> int:
    """Return the count `pytest --collect-only -q` printed; exit with why if none.

    A failed collection still prints a partial count, so its exit code wins.
    """
    if returncode != 0:
        sys.exit(f"pytest collection failed (exit {returncode})")
    found = re.search(r"(\d+) tests? collected", stdout)
    if not found:
        sys.exit(f"pytest printed no count (exit {returncode})")
    return int(found.group(1))


if __name__ == "__main__":
    done = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"], capture_output=True, text=True
    )
    print(collected(done.stdout, done.returncode))
