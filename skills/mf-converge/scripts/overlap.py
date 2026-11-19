# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Count what round 1's checkers and their shadows each caught, and both.

Why: 0097-cross-model design
D10.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.findings

NEAR = 5
ROLES = {"conformance": ("blocking",), "adversarial": ("critical", "high")}
# `debt_match.py`'s `What it affects` spans, copied.
SPAN = re.compile(r"`([^`]+)`")
LINES = re.compile(r":\d+(?:-\d+)?$")
# A bare file path: a `/` or a named suffix, so `main()`, `os.O_RDONLY` and `Run.ship`
# are not one; a span with a line is a path whatever its shape, so `Makefile:12` is.
SUFFIXES = "py|md|toml|json|jsonl|yaml|yml|txt|sh|cfg|ini|lock|log|patch|html|css|js|ts"
PATH = re.compile(rf"[\w.-]*(?:/[\w.-]*)+|[\w.-]*\.(?:{SUFFIXES})")

type Anchor = tuple[str, int | None, int | None]

# A findings file that cannot be read; its path is the message.
Unread = mflib.findings.Unread
# `review_metrics.py` takes these names: 0138-findings design D3.
cards = mflib.findings.cards_overlap_legacy
executor = mflib.findings.executor_overlap_legacy
first_round = mflib.findings.first_round_overlap_legacy


def anchors(card: str) -> list[Anchor]:
    """Return the path and lines of each path span of a card's `What it affects`.

    e.g. "`f()` in `a.py:12-14`, `b.py`" → [("a.py", 12, 14), ("b.py", None, None)]
    """
    affects = mflib.findings.affects_overlap_legacy(card)
    found: list[Anchor] = []
    for span in SPAN.findall(affects) if affects is not None else []:
        path = LINES.sub("", span)
        if not path or (path == span and not PATH.fullmatch(path)):
            continue
        numbers = [int(number) for number in span[len(path) + 1 :].split("-") if number]
        low, high = (numbers[0], numbers[-1]) if numbers else (None, None)
        found.append((path, low, high))
    lined = {path for path, low, _ in found if low is not None}
    return [
        anchor for anchor in found if anchor[1] is not None or anchor[0] not in lined
    ]


def matches(one: list[Anchor], other: list[Anchor]) -> bool:
    """Return whether two cards' anchors share a path, near or bare."""
    for path, low, high in one:
        for named, start, end in other:
            if path != named:
                continue
            if low is None or high is None or start is None or end is None:
                return True
            if max(start - high, low - end) <= NEAR:
                return True
    return False


def overlap(
    primary: list[str], shadow: list[str], blocking: tuple[str, ...]
) -> dict[str, int]:
    """Return the shared cards, each side's own, and the blockers among them.

    Each shadow card matches at most one primary card, the first in order. A shared
    pair is a blocker when either card blocks.
    """
    taken: set[int] = set()
    shared: list[tuple[str, str]] = []
    alone: list[str] = []
    for card in shadow:
        hit = next(
            (
                index
                for index, held in enumerate(primary)
                if index not in taken and matches(anchors(held), anchors(card))
            ),
            None,
        )
        if hit is None:
            alone.append(card)
            continue
        taken.add(hit)
        shared.append((primary[hit], card))
    left = [card for index, card in enumerate(primary) if index not in taken]
    blocks = mflib.findings.blocks_overlap_legacy
    return {
        "shared": len(shared),
        "primary_alone": len(left),
        "shadow_alone": len(alone),
        "shared_blockers": sum(
            blocks(one, blocking) or blocks(other, blocking) for one, other in shared
        ),
        "primary_blockers": sum(blocks(card, blocking) for card in left),
        "shadow_blockers": sum(blocks(card, blocking) for card in alone),
    }


def line(folder: Path) -> str:
    """Return each role's counts, joined by `; `."""
    read = mflib.findings.read_overlap_legacy
    found: list[str] = []
    for role, blocking in ROLES.items():
        held = read(folder / f"{role}.md")
        shade = read(folder / f"shadow-{role}.md")
        primary = [card for card in cards(held) if first_round(card)]
        counts = overlap(primary, cards(shade), blocking)
        found.append(
            f"{role} shared {counts['shared']}"
            f" · primary ({executor(held)}) alone {counts['primary_alone']}"
            f" · shadow ({executor(shade)}) alone {counts['shadow_alone']}"
            f" · blockers shared {counts['shared_blockers']}"
            f" · primary {counts['primary_blockers']}"
            f" · shadow {counts['shadow_blockers']}"
        )
    return "; ".join(found)


def main(argv: list[str] | None = None) -> int:
    """Print the shadow overlap of a change's round 1; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Count what round 1's checkers and their shadows each caught."
    )
    parser.add_argument("folder", type=Path, help="the change's .minions folder")
    args = parser.parse_args(argv)
    try:
        print(line(args.folder))
    except Unread as unread:
        print(f"overlap: cannot read — {unread}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
