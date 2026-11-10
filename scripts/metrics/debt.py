# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the open cards in the primary's `.minions/debt.md`; none is a gap, not zero.

A card opens with `- **<4 digits>·`. Why: 0030-change-impact design D7.
"""

import re
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 600
DEBT = Path(".minions/debt.md")
CARD = re.compile(r"^- \*\*\d{4}·", re.MULTILINE)


def cards(root: Path) -> int | None:
    """Return the open cards, or None when the repo keeps no debt file."""
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=TIMEOUT_SECONDS,
    ).stdout.strip()
    path = Path(common).parent / DEBT
    if not path.is_file():
        return None
    return len(CARD.findall(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    found = cards(Path.cwd())
    if found is None:
        sys.exit(f"no {DEBT}")
    print(found)
