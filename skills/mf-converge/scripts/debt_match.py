# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the debt cards on the diff's files to their own file.

    debt_match.py <debt.md> <diff.patch> <debt-cards.md>

Why: 0095-converge-roles design D8; 0101-cut-converge-diet design D4.
"""

import argparse
import errno
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.debtfile
import mflib.statefile


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _read(path: Path) -> str:
    """Return a file's text; one that cannot be read stops the run."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Stop(f"{path}: {why}") from error


def write(path: Path, text: str) -> None:
    """Replace `path` with `text` through a staged file; a link is refused."""
    try:
        mflib.debtfile.write(path, text)
    except mflib.statefile.WriteFailed as failed:
        if failed.error.errno == errno.ELOOP:
            raise Stop(f"{path} is a link") from failed
        raise Stop(f"{path}: {failed.error.strerror}") from failed


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
        changed = mflib.debtfile.paths(_read(args.patch))
        try:
            debt = mflib.debtfile.read(args.debt)
        except mflib.debtfile.Unreadable as unread:
            raise Stop(f"{args.debt}: {unread.reason}") from unread
        found = [
            card
            for card in mflib.debtfile.blocks(debt)
            if mflib.debtfile.matched(card, changed)
        ]
        write(args.cards, mflib.debtfile.page(found))
    except Stop as stop:
        print(f"debt: cannot match — {stop}")
        return 2
    print(f"debt: {len(found)} cards on the diff's files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
