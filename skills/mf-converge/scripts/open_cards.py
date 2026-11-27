# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the cards of a findings file a verify worker judges.

Why: 0095-converge-roles design
D10, 0108-converge-script design D11.
"""

import argparse
import errno
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.findings
import mflib.statefile

JUDGED = ("open", "fixed", "wontfix")
KNOWN = (*JUDGED, "verified", "accepted")


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def judged(card: mflib.findings.Card) -> bool:
    """Return whether a card's Status asks a verify for its verdict.

    e.g. Status "`Fixed` — a note" → True; "verified — held" → False.
    A Status word none of `KNOWN`, or none at all, stops the run, naming the card.
    """
    if "Status" not in card.fields:
        raise Stop(f"card {card.id}: no Status")
    if card.status not in KNOWN:
        said = card.fields["Status"].split()
        raise Stop(f"card {card.id}: Status {said[0] if said else 'empty'}")
    return card.status in JUDGED


# `bundle.py`'s `write`.
def write(path: Path, text: str) -> None:
    """Replace `path` with `text` through a staged file; a link is refused."""
    if said := mflib.statefile.write_or_say(path, text):
        raise Stop(said)


def open_page(findings: Path, out: Path) -> int:
    """Write the cards of `findings` a verify judges to `out`; return how many.

    Raises `Stop` as `main` exits 2.
    """
    try:
        text = mflib.findings.read(findings)
    except OSError as error:
        raise Stop(f"{findings}: {error.strerror}") from error
    if text is None:
        raise Stop(f"{findings}: {os.strerror(errno.ENOENT)}")
    if why := mflib.findings.malformed(text, ""):
        raise Stop(why)
    found = [card for card in mflib.findings.cards(text, "") if judged(card)]
    body = "".join("\n".join(card.lines) + "\n" for card in found) or "None.\n"
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
