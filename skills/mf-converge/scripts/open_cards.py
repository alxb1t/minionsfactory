# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the cards of a findings file a verify worker judges.

    open_cards.py <findings.md> <out.md>

A card is judged when its Status reads `open`, `fixed` or `wontfix`, backticks
dropped; it is copied verbatim. Prints `open cards: <n> of <findings name>` and exits
0, or `open cards: cannot read — <why>` and exits 2, writing nothing; an out path
that is a link is refused. Why: 0095-converge-roles design D10.
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

JUDGED = ("open", "fixed", "wontfix")
TITLE = re.compile(r"^- \*\*\S+ — ")
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*`?(\w*)", re.MULTILINE)


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _read(path: Path) -> str:
    """Return a file's text; one that cannot be read stops the run."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Stop(f"{path}: {why}") from error


# `debt_match.py`'s `cards`.
def cards(text: str) -> list[str]:
    """Return each card, its title to the line before the next title or heading."""
    found: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if TITLE.match(line):
            current = [line]
            found.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None:
            current.append(line)
    return ["\n".join(card).rstrip() + "\n" for card in found]


def judged(card: str) -> bool:
    """Return whether a card's Status asks a verify for its verdict.

    e.g. "  - **Status:** `fixed` — a note" → True; "verified — held" → False
    """
    status = STATUS.search(card)
    return status is not None and status[1] in JUDGED


# `bundle.py`'s `write`.
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
    """Write the cards a verify judges; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write the cards of a findings file a verify worker judges."
    )
    parser.add_argument("findings", type=Path, help="the findings file")
    parser.add_argument("out", type=Path, help="the open cards file to write")
    args = parser.parse_args(argv)
    name = args.findings.name
    try:
        found = [card for card in cards(_read(args.findings)) if judged(card)]
        body = "".join(found) or "None.\n"
        write(args.out, f"# {name} — the cards a verify judges\n\n{body}")
    except Stop as stop:
        print(f"open cards: cannot read — {stop}")
        return 2
    print(f"open cards: {len(found)} of {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
