# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the cards of a findings file a verify worker judges.

Why: 0095-converge-roles design
D10, 0108-converge-script design D11.
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

JUDGED = ("open", "fixed", "wontfix")
KNOWN = (*JUDGED, "verified", "accepted")
TITLE = re.compile(r"^- \*\*(\S+) — ")
# Any top-level bold line, off the card's form or not: names a stray Status's card.
NAMED = re.compile(r"^[-*] \*\*([^\s*:]+)")
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*(\S*)", re.MULTILINE)
WORD_END = re.compile(r"\W")


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


def strays(text: str) -> None:
    """Stop on a Status line under no card title, naming the bold line above it."""
    name, inside = "unnamed", False
    for line in text.splitlines():
        if line.startswith("#"):
            name, inside = "unnamed", False
        elif bold := NAMED.match(line):
            name, inside = bold[1], TITLE.match(line) is not None
        elif STATUS.match(line) and not inside:
            raise Stop(f"a Status under no card: {name}")


def judged(card: str) -> bool:
    """Return whether a card's Status asks a verify for its verdict.

    e.g. "  - **Status:** `Fixed` — a note" → True; "verified — held" → False.
    A Status word none of `KNOWN`, or none at all, stops the run, naming the card.
    """
    title = TITLE.match(card)
    name = title[1] if title else "unnamed"
    said = [status[1] for status in STATUS.finditer(card)]
    if not said:
        raise Stop(f"card {name}: no Status")
    words = [
        WORD_END.split(each.lstrip("`*_"), maxsplit=1)[0].casefold() for each in said
    ]
    for each, word in zip(said, words, strict=True):
        if word not in KNOWN:
            raise Stop(f"card {name}: Status {each or 'empty'}")
    return words[0] in JUDGED


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


def open_page(findings: Path, out: Path) -> int:
    """Write the cards of `findings` a verify judges to `out`; return how many.

    Raises `Stop` as `main` exits 2.
    """
    text = _read(findings)
    strays(text)
    found = [card for card in cards(text) if judged(card)]
    body = "".join(found) or "None.\n"
    write(out, f"# {findings.name} — the cards a verify judges\n\n{body}")
    return len(found)


def main(argv: list[str] | None = None) -> int:
    """Write the cards a verify judges; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write the cards of a findings file a verify worker judges."
    )
    parser.add_argument("findings", type=Path, help="the findings file")
    parser.add_argument("out", type=Path, help="the open cards file to write")
    args = parser.parse_args(argv)
    try:
        found = open_page(args.findings, args.out)
    except Stop as stop:
        print(f"open cards: cannot read — {stop}")
        return 2
    print(f"open cards: {found} of {args.findings.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
