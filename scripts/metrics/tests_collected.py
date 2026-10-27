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

done = subprocess.run(
    ["uv", "run", "pytest", "--collect-only", "-q"], capture_output=True, text=True
)
found = re.search(r"(\d+) tests? collected", done.stdout)
if not found:
    sys.exit(f"pytest printed no count (exit {done.returncode})")
print(found.group(1))
