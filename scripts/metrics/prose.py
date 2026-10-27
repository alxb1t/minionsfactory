# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the skills' hedge words (`hedge`) or sentences over 30 words (`long`).

The text is `skills/*/SKILL.md` and `skills/*/references/*.md`, outside
frontmatter, fenced code, inline code and table rows. Why: 0030-change-impact
design D7.
"""

import re
import sys
from pathlib import Path

HEDGES = re.compile(
    r"\b(should|might|appropriately|as needed|if possible|probably|typically"
    r"|generally|various)\b|\betc\.",
    re.IGNORECASE,
)
LONG = 30
FRONTMATTER = re.compile(r"\A---\n.*?^---$", re.DOTALL | re.MULTILINE)
ITEM = re.compile(r"\s*([-*+]|\d+\.)\s")


def paragraphs(text: str) -> list[str]:
    r"""Return the prose paragraphs of a markdown text, each joined to one line.

    A leading `---` frontmatter block is skipped, and a list item starts a paragraph.
    e.g. "A `b` c.\n| x |\n\nD.\n- e" → ["A  c.", "D.", "- e"]
    """
    text = FRONTMATTER.sub("", text, count=1)
    found: list[str] = []
    lines: list[str] = []
    fenced = False
    for line in [*text.splitlines(), ""]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or line.lstrip().startswith("|"):
            continue
        if lines and (not line.strip() or ITEM.match(line)):
            found.append(" ".join(lines))
            lines = []
        if line.strip():
            lines.append(re.sub(r"`[^`]*`", "", line.strip()))
    return found


def sentences(paragraph: str) -> list[str]:
    """Return a paragraph's sentences: each ends at `.`, `!` or `?` before a space."""
    return [s for s in re.split(r"(?<=[.!?])\s+", paragraph) if s]


def count(root: Path, kind: str) -> int:
    """Return the hedge words or long sentences across the skills' text."""
    paths = sorted(root.glob("skills/*/SKILL.md"))
    paths += sorted(root.glob("skills/*/references/*.md"))
    total = 0
    for path in paths:
        for paragraph in paragraphs(path.read_text(encoding="utf-8")):
            if kind == "hedge":
                total += len(HEDGES.findall(paragraph))
            else:
                total += sum(len(s.split()) > LONG for s in sentences(paragraph))
    return total


if __name__ == "__main__":
    print(count(Path.cwd(), sys.argv[1]))
