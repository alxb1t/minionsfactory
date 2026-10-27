# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the distinct rule ids the skills' tables define, each counted once.

An id is a table row's bold first cell — `| **I4** |` — with the letter
`I`, `P`, `T`, `W`, `C` or `A`. Why: 0030-change-impact design D7.
"""

import re
from pathlib import Path

ROW = re.compile(r"^\| \*\*([IPTWCA]\d+)\*\* \|", re.MULTILINE)


def rule_ids(root: Path) -> int:
    """Return the distinct rule ids across `skills/*/SKILL.md`."""
    found: set[str] = set()
    for path in sorted(root.glob("skills/*/SKILL.md")):
        found |= set(ROW.findall(path.read_text(encoding="utf-8")))
    return len(found)


if __name__ == "__main__":
    print(rule_ids(Path.cwd()))
