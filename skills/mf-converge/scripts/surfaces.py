# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Decide whether a converge fix needs a security verify.

    surfaces.py <security.md> <from> <to>

Run from the repository root. Exit 0, `surfaces: no surface`: the security file is
clean, every card and Status line `verified` or `accepted`, and no path of
`<from>..<to>` matches a glob of `THREAT_MODEL.md`'s `## Surfaces` as `<from>` holds
it. Exit 1,
`surfaces: verify — <reason>`, the first that holds. Exit 2,
`surfaces: cannot read — <why>`.
Why: 0094-lighter-converge design D8.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

THREAT_MODEL = Path("THREAT_MODEL.md")
# Settled by an allowlist: any other Status, one off the card's form or none at all,
# waits for its checker. A `wontfix` waits too, an amend card's staying `wontfix`.
SETTLED = ("verified", "accepted")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CARD = re.compile(r"^- \*\*(\S+) — ", re.MULTILINE)
# Any top-level bold line, off the card's form or not: names a stray Status's card.
TITLE = re.compile(r"^[-*] \*\*([^\s*:]+)", re.MULTILINE)
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*[`*_]*(\w*)", re.MULTILINE)
GLOB = re.compile(r"^- `([^`]+)`", re.MULTILINE)


class Unread(Exception):
    """End the run with the reason it prints, and exit 2."""


class Verify(Exception):
    """End the run with the reason security verifies the fix, and exit 1."""


def surfaces(text: str) -> list[str]:
    r"""Return the globs a threat model's `## Surfaces` lists, in order.

    e.g. "## Surfaces\n\n- `scripts/*` — run\n" → ["scripts/*"]
    """
    found = re.search(r"^## Surfaces\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return GLOB.findall(found[1]) if found else []


def decide(security: Path, start: str, end: str) -> None:
    """Return when the fix reaches no surface; raise `Verify` or `Unread` else."""
    try:
        text = security.read_text()
    except OSError as error:
        raise Unread(f"{security}: {error.strerror}") from error
    head = FRONTMATTER.match(text)
    if not head or not re.search(r"^verdict: clean$", head[1], re.MULTILINE):
        raise Verify(f"{security.name} is not clean")
    starts = list(CARD.finditer(text))
    ends = [card.start() for card in starts[1:]] + [len(text)]
    for card, end_at in zip(starts, ends[: len(starts)], strict=True):
        status = STATUS.search(text, card.end(), end_at)
        said = status[1] if status else ""
        if said not in SETTLED:
            raise Verify(f"security card {card[1]} is {said or 'unsettled'}")
    # Every Status line too, so one under a title `CARD` misses still waits.
    for status in STATUS.finditer(text):
        if status[1] not in SETTLED:
            titles = TITLE.findall(text, 0, status.start())
            named = titles[-1] if titles else "unnamed"
            raise Verify(f"security card {named} is {status[1] or 'unsettled'}")
    # Replacement off, as `pin.py`'s and `conduct.py`'s history reads: a worker can
    # write `refs/replace/`, and swap the list read at `<from>`.
    unreplaced = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    done = subprocess.run(
        # `-z`: else git quotes a path holding an unusual byte, and no glob matches it.
        ["git", "diff", "-z", "--name-only", "--no-renames", start, end],
        capture_output=True,
        text=True,
        env=unreplaced,
    )
    if done.returncode != 0:
        raise Unread(f"git diff failed: {done.stderr.strip().split('\n')[0]}")
    # Read at `<from>`, which git just read: the fix being judged cannot edit the list
    # that judges it. A threat model absent there lists nothing.
    shown = subprocess.run(
        ["git", "show", f"{start}:{THREAT_MODEL}"],
        capture_output=True,
        text=True,
        env=unreplaced,
    )
    listed = surfaces(shown.stdout) if shown.returncode == 0 else []
    if not listed:
        raise Verify(f"{THREAT_MODEL} lists no surface")
    for path in filter(None, done.stdout.split("\0")):
        if glob := next((g for g in listed if fnmatch.fnmatchcase(path, g)), None):
            raise Verify(f"{path} matches {glob}")


def main(argv: list[str] | None = None) -> int:
    """Print whether the fix needs a security verify; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Decide whether a converge fix needs a security verify."
    )
    parser.add_argument("security", type=Path, help="the security findings file")
    parser.add_argument("start", metavar="from", help="the head the last round judged")
    parser.add_argument("end", metavar="to", help="the head the fix produced")
    args = parser.parse_args(argv)
    try:
        decide(args.security, args.start, args.end)
    except Verify as verify:
        print(f"surfaces: verify — {verify}")
        return 1
    except Unread as unread:
        print(f"surfaces: cannot read — {unread}")
        return 2
    print("surfaces: no surface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
