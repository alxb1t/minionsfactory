# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the open cards in `.minions/backlog.md`; no backlog is a gap, not zero.

A card opens with `- **<4 digits>·`. Why: 0030-change-impact design D7.
"""

import re
import sys
from pathlib import Path

BACKLOG = Path(".minions/backlog.md")
CARD = re.compile(r"^- \*\*\d{4}·", re.MULTILINE)


def cards(root: Path) -> int | None:
    """Return the open cards, or None when the repo keeps no backlog."""
    path = root / BACKLOG
    if not path.is_file():
        return None
    return len(CARD.findall(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    found = cards(Path.cwd())
    if found is None:
        sys.exit(f"no {BACKLOG}")
    print(found)
