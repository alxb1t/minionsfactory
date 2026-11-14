# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the debt cards on the diff's files to their own file.

    debt_match.py <debt.md> <diff.patch> <debt-cards.md>

Why: 0095-converge-roles design D8; 0101-cut-converge-diet design D4.
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

HEADING = "# Debt cards on the diff's files"
DIFF = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)
TITLE = re.compile(r"^- \*\*[^\s*]+ — ")
AFFECTS = re.compile(r"^[ \t]+- \*\*What it affects:\*\*(.*)$", re.MULTILINE)
SPAN = re.compile(r"`([^`]+)`")
LINES = re.compile(r":\d+(?:-\d+)?$")


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _read(path: Path) -> str:
    """Return a file's text; one that cannot be read stops the run."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Stop(f"{path}: {why}") from error


def paths(patch: str) -> set[str]:
    """Return both sides' paths of each `diff --git` line.

    e.g. "diff --git a/old.md b/new.md" → {"old.md", "new.md"}
    """
    return {side for pair in DIFF.findall(patch) for side in pair}


def cards(debt: str) -> list[str]:
    """Return each card, its title to the line before the next title or heading."""
    found: list[list[str]] = []
    current: list[str] | None = None
    for line in debt.splitlines():
        if TITLE.match(line):
            current = [line]
            found.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None:
            current.append(line)
    return ["\n".join(card).rstrip() + "\n" for card in found]


def matched(card: str, changed: set[str]) -> bool:
    """Return whether a backticked span of the card's `What it affects` names a path.

    e.g. "`src/a.py:12`" and {"src/a.py"} → True
    """
    affects = AFFECTS.search(card)
    spans = SPAN.findall(affects[1]) if affects else []
    return any(LINES.sub("", span) in changed for span in spans)


def page(found: list[str]) -> str:
    """Return the cards file: its heading, a blank line, then the cards or `None.`."""
    return f"{HEADING}\n\n{''.join(found) or 'None.\n'}"


def write(path: Path, text: str) -> None:
    """Replace `path` with `text` through a staged file; a link is refused."""
    if path.is_symlink():
        raise Stop(f"{path} is a link")
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(text)
        staged.replace(path)
    except OSError as error:
        with contextlib.suppress(OSError):
            staged.unlink()
        raise Stop(f"{path}: {error.strerror}") from error


def main(argv: list[str] | None = None) -> int:
    """Write the matched debt cards to their own file; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write the debt cards on the diff's files to their own file."
    )
    parser.add_argument("debt", type=Path, help="the debt file")
    parser.add_argument("patch", type=Path, help="the frozen diff patch")
    parser.add_argument("cards", type=Path, help="the cards file to write")
    args = parser.parse_args(argv)
    try:
        changed = paths(_read(args.patch))
        debt = _read(args.debt) if os.path.lexists(args.debt) else ""
        found = [card for card in cards(debt) if matched(card, changed)]
        write(args.cards, page(found))
    except Stop as stop:
        print(f"debt: cannot match — {stop}")
        return 2
    print(f"debt: {len(found)} cards on the diff's files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
