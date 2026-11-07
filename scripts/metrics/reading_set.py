# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the words a station reads before it starts.

The set is `converge`, `conformance`, `adversarial` or `shared`. Conformance reads
the decisions' index, `INDEX`, in place of the whole file; adversarial reads the
threat model and no decision. Why: 0030-change-impact design D7; 0076-context-cost
design D4; 0094-lighter-converge design D10; 0095-converge-roles design D13.
"""

import sys
from pathlib import Path

DECISIONS = "docs/decisions.md"
INDEX = f"{DECISIONS} · index"
SHARED = (
    "AGENTS.md",
    "docs/principles.md",
    DECISIONS,
    "CODING_STANDARDS.md",
    "CONTRIBUTING.md",
)
SETS = {
    "shared": SHARED,
    "converge": (
        *SHARED,
        "THREAT_MODEL.md",
        "skills/mf-converge/SKILL.md",
        "skills/mf-converge/references/worker.md",
    ),
    "conformance": (
        "AGENTS.md",
        "CODING_STANDARDS.md",
        "CONTRIBUTING.md",
        INDEX,
        "skills/mf-converge/references/worker.md",
        "skills/mf-converge/references/generic-conformance.md",
    ),
    "adversarial": (
        "AGENTS.md",
        "THREAT_MODEL.md",
        "skills/mf-converge/references/worker.md",
        "skills/mf-converge/references/generic-adversarial.md",
    ),
}


def _text(root: Path, path: str) -> str:
    """Return a file's text; for `INDEX`, the decisions' `### D` lines, else all."""
    if path != INDEX:
        return (root / path).read_text(encoding="utf-8")
    text = (root / DECISIONS).read_text(encoding="utf-8")
    index = [line for line in text.splitlines() if line.startswith("### D")]
    return "\n".join(index) if index else text


def words(root: Path, name: str) -> int:
    """Return the whitespace-separated words of the reading set `name`."""
    return sum(len(_text(root, path).split()) for path in SETS[name])


if __name__ == "__main__":
    print(words(Path.cwd(), sys.argv[1]))
