# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the words a station reads before it starts: `converge` or `shared`.

Why: 0030-change-impact design D7.
"""

import sys
from pathlib import Path

SHARED = (
    "AGENTS.md",
    "docs/principles.md",
    "docs/decisions.md",
    "CODING_STANDARDS.md",
    "CONTRIBUTING.md",
)
SETS = {
    "shared": SHARED,
    "converge": (*SHARED, "THREAT_MODEL.md", "skills/mf-converge/SKILL.md"),
}


def words(root: Path, name: str) -> int:
    """Return the whitespace-separated words of the reading set `name`."""
    return sum(
        len((root / path).read_text(encoding="utf-8").split()) for path in SETS[name]
    )


if __name__ == "__main__":
    print(words(Path.cwd(), sys.argv[1]))
