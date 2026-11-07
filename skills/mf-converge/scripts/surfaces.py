# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Decide whether a converge fix needs a security verify.

    surfaces.py <security.md> <from> <to>

Run from the repository root. Exit 0, `surfaces: no surface`: the security file is
clean, no card awaits its checker, and no path of `<from>..<to>` matches a glob of
`THREAT_MODEL.md`'s `## Surfaces`. Exit 1, `surfaces: verify — <reason>`, the first
that holds. Exit 2, `surfaces: cannot read — <why>`.
Why: 0094-lighter-converge design D8.
"""

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

THREAT_MODEL = Path("THREAT_MODEL.md")
# A `wontfix` waits too: the fixer's claim, or an amend card's, which stays `wontfix`.
AWAITING = ("open", "fixed", "wontfix")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CARD = re.compile(r"^- \*\*(\S+) — ", re.MULTILINE)
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*`?(\w*)", re.MULTILINE)
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
        if status and status[1] in AWAITING:
            raise Verify(f"security card {card[1]} is {status[1]}")
    listed = surfaces(THREAT_MODEL.read_text()) if THREAT_MODEL.is_file() else []
    if not listed:
        raise Verify(f"{THREAT_MODEL} lists no surface")
    done = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", start, end],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        raise Unread(f"git diff failed: {done.stderr.strip().split('\n')[0]}")
    for path in done.stdout.splitlines():
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
