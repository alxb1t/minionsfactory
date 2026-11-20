"""Write and parse the debt file: its read, cards, headings, lock and staged write.

The callers find each path and word each halt. Why: 0139-debt design D2 and D3.
"""

import errno
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import findings, statefile

TITLE = re.compile(r"^- \*\*([^\s*]+) — ", re.MULTILINE)
PREAMBLE = (
    "# Debt\n\n*Deferred work from converge, one heading per change; a paydown change"
    " lists the ids it closes under `debt:`.*\n"
)
HEADING = "# Debt cards on the diff's files"
DIFF = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)
AFFECTS = re.compile(r"^[ \t]+- \*\*What it affects:\*\*(.*)$", re.MULTILINE)
SPAN = re.compile(r"`([^`]+)`")
LINES = re.compile(r":\d+(?:-\d+)?$")
# The lock's poll, in seconds. Why: 0139-debt design D6.
LOCK_POLL = 5


class Unreadable(Exception):
    """Say why the debt cannot be read: a link, or a file that is no regular file."""

    def __init__(self, reason: str) -> None:
        """Hold the reason."""
        super().__init__(reason)
        self.reason = reason


class Held(Exception):
    """Say the lock is held past the wait given."""


def read(path: Path) -> str:
    """Return the debt's text, "" when missing, a bad byte replaced.

    A link, a folder or a pipe raises `Unreadable`.
    """
    try:
        return statefile.read(path)
    except FileNotFoundError:
        return ""
    except OSError as error:
        link = error.errno == errno.ELOOP
        raise Unreadable("it is a link" if link else str(error.strerror)) from error


def ids(text: str, change: str | None = None) -> list[str]:
    """Return each title's id, of the whole text or of the section `## <change>`.

    e.g. "- **0016·R5 — a title**" → ["0016·R5"]
    """
    if change is None:
        return TITLE.findall(text)
    found: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == f"## {change}"
        elif inside and (card := TITLE.match(line)):
            found.append(card[1])
    return found


def blocks(text: str) -> list[str]:
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


def card_id(block: str) -> str:
    """Return the id a card's title opens with, or "".

    e.g. "- **0113·S4 — a title**" → "0113·S4"
    """
    found = TITLE.match(block)
    return found[1] if found else ""


def paths(patch: str) -> set[str]:
    """Return both sides' paths of each `diff --git` line.

    e.g. "diff --git a/old.md b/new.md" → {"old.md", "new.md"}
    """
    return {side for pair in DIFF.findall(patch) for side in pair}


def matched(block: str, changed: set[str]) -> bool:
    """Return whether a backticked span of the card's `What it affects` names a path.

    e.g. "`src/a.py:12`" and {"src/a.py"} → True
    """
    affects = AFFECTS.search(block)
    spans = SPAN.findall(affects[1]) if affects else []
    return any(LINES.sub("", span) in changed for span in spans)


def page(found: list[str]) -> str:
    """Return the cards file: its heading, a blank line, then the cards or `None.`."""
    return f"{HEADING}\n\n{''.join(found) or 'None.\n'}"


def filed(text: str, change: str, cards: list[str]) -> str:
    """Return the debt with `cards` at the end of `## <change>`, made if missing."""
    if not cards:
        return text
    lines = [line if line.endswith("\n") else f"{line}\n" for line in text.splitlines()]
    heading = f"## {change}\n"
    if heading not in lines:
        return f"{''.join(lines).rstrip()}\n\n{heading}\n{''.join(cards)}"
    at = lines.index(heading) + 1
    end = _section_end(lines, at)
    while end > at and not lines[end - 1].strip():
        end -= 1
    gap = ["\n"] if end < len(lines) and lines[end].startswith("## ") else []
    return "".join([*lines[:end], *cards, *gap, *lines[end:]])


def _section_end(lines: list[str], at: int) -> int:
    """Return the index of the first `## ` heading at or past `at`, else the end."""
    return next(
        (i for i in range(at, len(lines)) if lines[i].startswith("## ")), len(lines)
    )


def unfiled(text: str, ident: str) -> str:
    """Return the debt without the card `ident`, and its heading when left empty.

    The card's extent is `findings.cards`'s, blanks inside it included.
    """
    lines = text.splitlines(keepends=True)
    start = next(
        i for i, line in enumerate(lines) if line.startswith(f"- **{ident} — ")
    )
    card = next(c for c in findings.cards(text, "") if c.id == ident)
    del lines[start : start + len(card.lines)]
    tops = [i for i in range(start) if lines[i].startswith("## ")]
    if tops and not "".join(lines[tops[-1] + 1 : _section_end(lines, start)]).strip():
        del lines[tops[-1] : _section_end(lines, start)]
    return "".join(lines)


def clear(text: str, ids: list[str]) -> str:
    """Return the debt without each card of `ids`, in order; an unknown id raises.

    Why: 0139-debt design D12.
    """
    for ident in ids:
        text = unfiled(text, ident)
    return text


def spoiled(
    number: str, index: int, role: str, why: str, round_: int, change: str, where: str
) -> str:
    """Return the debt card of a role's findings file malformed after its rewrite.

    `where` is the file's path as the card names it.
    """
    return (
        f"- **{number}·M{index} — {role}'s findings file was malformed"
        " after a rewrite**\n"
        "  - **Why it's a problem:** converge read the role as clean at HEAD with"
        " no card, so a finding in the file went unjudged.\n"
        "  - **When you'd hit it:** the release reads the file's own verdict.\n"
        f"  - **What it affects:** `{where}`.\n"
        f"  - **Evidence:** {why} · read.\n"
        "  - **Verdict:** confirmed.\n"
        "  - **Priority:** medium · conformance · maintainability — the role's"
        " verdict this run is the script's, not its checker's.\n"
        f"  - **Round:** {round_}\n"
        "  - **Fix:** rewrite the file to the findings file contract, then converge"
        " again · size: a design change.\n"
        "  - **Amend:** no\n"
        f"  - **Trigger:** the release of {change}.\n"
        f"  - **Still true?** read `{where}` against the contract.\n"
        "  - **Related:** none.\n"
        "  - **Status:** open\n"
    )


def qualify(lines: list[str], ident: str, qualified: str) -> str:
    r"""Return a card's lines, each ended by a newline, its title's id replaced.

    e.g. ["- **R2 — a title**"], "R2", "0001·R2" → "- **0001·R2 — a title**\n"
    """
    title = lines[0].replace(f"- **{ident} — ", f"- **{qualified} — ")
    return "".join(f"{line}\n" for line in [title, *lines[1:]])


@contextmanager
def lock(path: Path, wait: int = 0) -> Iterator[None]:
    """Hold the lock `path`, made by `mkdir`, while the body runs; `rmdir` it after.

    A held lock is polled every `LOCK_POLL` seconds up to `wait`, then raises `Held`.
    """
    waited = 0
    while True:
        try:
            path.mkdir()
            break
        except FileExistsError:
            if waited >= wait:
                raise Held from None
            time.sleep(LOCK_POLL)
            waited += LOCK_POLL
    try:
        yield
    finally:
        path.rmdir()


def write(path: Path, text: str, folder: int | None = None) -> None:
    """Replace `path` with `text` through a staged file; a link is refused.

    A failure raises `statefile.WriteFailed`.
    """
    statefile.write(path, text, refuse_link=True, folder=folder)
