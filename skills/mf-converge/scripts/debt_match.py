# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Append to a converge bundle the debt cards on the diff's files.

    debt_match.py <debt.md> <diff.patch> <bundle.md>

Run from the repository root. A card matches when a backticked span of its
`What it affects` line, a `:<line>` or `:<from>-<to>` suffix dropped, is a path the
patch changes. Prints `debt: <n> cards on the diff's files` and exits 0, or
`debt: cannot match — <why>` and exits 2, writing nothing; a bundle path that is a
link is refused. Why: 0095-converge-roles design D8.
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

SECTION = "## Debt cards on the diff's files"
DIFF = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)
TITLE = re.compile(r"^- \*\*\S+ — ")
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


def section(bundle: str, found: list[str]) -> str:
    """Return the bundle with its debt section dropped, then appended afresh."""
    kept: list[str] = []
    inside = False
    for line in bundle.splitlines():
        if line.startswith("## "):
            inside = line.strip() == SECTION
        if not inside:
            kept.append(line)
    body = "".join(found) or "None.\n"
    return "\n".join(kept).rstrip() + f"\n\n{SECTION}\n\n{body}"


def write(path: Path, text: str) -> None:
    """Replace `path` with `text` through a staged file; a link is refused.

    As `bundle.py`'s `write`: the staged `.tmp` is created anew with `O_NOFOLLOW`,
    then renamed over the bundle; a failure removes it and leaves the bundle as it
    stood.
    """
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
    """Append the matched debt cards to the bundle; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Append to a converge bundle the debt cards on the diff's files."
    )
    parser.add_argument("debt", type=Path, help="the debt file")
    parser.add_argument("patch", type=Path, help="the frozen diff patch")
    parser.add_argument("bundle", type=Path, help="the bundle to append to")
    args = parser.parse_args(argv)
    try:
        bundle = _read(args.bundle)
        changed = paths(_read(args.patch))
        debt = _read(args.debt) if os.path.lexists(args.debt) else ""
        found = [card for card in cards(debt) if matched(card, changed)]
        write(args.bundle, section(bundle, found))
    except Stop as stop:
        print(f"debt: cannot match — {stop}")
        return 2
    print(f"debt: {len(found)} cards on the diff's files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
