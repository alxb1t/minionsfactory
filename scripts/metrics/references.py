# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the broken references in `AGENTS.md`, `README.md` and `docs/*.md`.

A link to a missing file or heading is broken, and so is a cited `D<n>` with no
`### D<n> ·` heading. The skills are not read: their links are examples.
Why: 0030-change-impact design D7.
"""

import re
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
DECISION = re.compile(r"\bD(\d+)\b")
HEADING = re.compile(r"^#+\s+(.*)$", re.MULTILINE)


def _unfenced(text: str) -> str:
    """Return `text` without fenced code."""
    return re.sub(r"^\s*```.*?^\s*```", "", text, flags=re.MULTILINE | re.DOTALL)


def _prose(text: str) -> str:
    """Return `text` without fenced or inline code, where links are examples."""
    return re.sub(r"`[^`\n]*`", "", _unfenced(text))


def anchors(text: str) -> set[str]:
    """Return the heading anchors GitHub gives a markdown text.

    A heading's inline code keeps its text, as GitHub's anchor does.
    e.g. "### D14 · Converge is optional" → "d14--converge-is-optional"
    """
    found: set[str] = set()
    for heading in HEADING.findall(_unfenced(text)):
        slug = re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
        number = 0
        while (candidate := slug + (f"-{number}" if number else "")) in found:
            number += 1
        found.add(candidate)
    return found


def broken(root: Path) -> int:
    """Return the broken links and the cited decisions with no heading."""
    files = [root / "AGENTS.md", root / "README.md", *sorted(root.glob("docs/*.md"))]
    texts = {path: path.read_text(encoding="utf-8") for path in files if path.is_file()}
    headings = {
        int(n)
        for text in texts.values()
        for n in re.findall(r"^### D(\d+) ·", text, re.M)
    }
    known: dict[Path, set[str]] = {}
    total = 0
    for path, text in texts.items():
        prose = _prose(text)
        for target in LINK.findall(prose):
            if re.match(r"[a-z]+:", target):
                continue
            name, _, anchor = target.partition("#")
            linked = (path.parent / name) if name else path
            if not linked.exists():
                total += 1
            elif anchor and linked.suffix == ".md":
                if linked not in known:
                    known[linked] = anchors(linked.read_text(encoding="utf-8"))
                total += anchor not in known[linked]
        if path.name != "README.md":
            total += sum(int(n) not in headings for n in DECISION.findall(prose))
    return total


if __name__ == "__main__":
    print(broken(Path.cwd()))
