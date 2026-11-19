"""Write and parse a findings file: its cards, their fields and words, its frontmatter.

Converge's form is the one form; a `_legacy` function holds another script's copy.
Remove each `_legacy` function once its script reads the one form: 0138 design D2.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from . import statefile

BLOCKS = {"conformance": ("blocking",), "adversarial": ("critical", "high")}
# A blocking adversarial card of none of these categories is a security one.
# Why: 0119-debt-paydown-3b design D3.
NON_SECURITY = (
    "stability",
    "data integrity",
    "functional correctness",
    "performance",
    "maintainability",
)
SMALL = ("one line", "a test", "one line and a test")
SIZE = re.compile(r"size:([^:]*)$")
TITLE = re.compile(r"^- \*\*([^\s*]+) — ")
FIELD = re.compile(r"^[ \t]+- \*\*(.+?):?\*\*:?[ \t]*(.*)$")
# Any top-level bold line, off the card's form or not: names a stray Status's card.
NAMED = re.compile(r"^[-*] \*\*([^\s*:]+)")
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*(\S*)", re.MULTILINE)
FRONT = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
INTEGERS = ("round", "open_blocking", "files", "commits")
LISTS = ("passes", "inconclusive")
VERDICTS = ("clean", "changes-requested")
HALT_ID = re.compile(r"\b[RS]\d+\b")
STUB_BODY = "Skipped by the plan: no worker judged this round."


class Unread(Exception):
    """Say which findings file a legacy read could not read, and why."""


@dataclass(frozen=True)
class Card:
    """One finding of a findings file: its id, its role, its fields and its lines."""

    id: str
    role: str
    fields: dict[str, str]
    lines: list[str] = field(default_factory=list)

    def word(self, name: str) -> str:
        """Return the field's first word, case folded, its backticks and bold dropped.

        e.g. "**Fixed** — a note" → "fixed"
        """
        words = self.fields.get(name, "").replace("`", "").replace("*", "").split()
        return words[0].rstrip(".,;:").casefold() if words else ""

    @property
    def severity(self) -> str:
        """Return the grade its Priority opens with."""
        return self.word("Priority")

    @property
    def blocking(self) -> bool:
        """Return whether its grade blocks on its role's scale."""
        return self.severity in BLOCKS.get(self.role, ())

    @property
    def status(self) -> str:
        """Return its Status word: open, fixed, verified, wontfix or accepted."""
        return self.word("Status")

    @property
    def amend(self) -> bool:
        """Return whether it is an amend card."""
        return self.word("Amend") == "yes"

    @property
    def small(self) -> bool:
        """Return whether its Fix size is one of `SMALL`, read literally."""
        sized = SIZE.search(self.fields.get("Fix", ""))
        return bool(sized) and sized[1].strip(" `.") in SMALL

    @property
    def security(self) -> bool:
        """Return whether it is an adversarial card of category `security`."""
        parts = self.fields.get("Priority", "").split(" · ")
        category = parts[2].split(" — ")[0].strip() if len(parts) > 2 else ""
        return self.role == "adversarial" and category == "security"


def cards(text: str, role: str) -> list[Card]:
    """Return the cards of a findings file's body, each with its fields.

    A card is its title and the indented lines after it; a repeated field's first wins.
    """
    found: list[Card] = []
    current: Card | None = None
    for line in text.splitlines():
        if title := TITLE.match(line):
            current = Card(title[1], role, {}, [line])
            found.append(current)
        elif current is None or not line.startswith((" ", "\t")):
            current = None
        else:
            current.lines.append(line)
            if named := FIELD.match(line):
                current.fields.setdefault(named[1], named[2].strip())
    return found


def strays(text: str) -> list[str]:
    r"""Return, for each Status line under no card title, the bold line above it.

    e.g. "- **Note**\n  - **Status:** open\n" → ["Note"]; none above, "unnamed"
    """
    found: list[str] = []
    name, inside = "unnamed", False
    for line in text.splitlines():
        if line.startswith("#"):
            name, inside = "unnamed", False
        elif bold := NAMED.match(line):
            name, inside = bold[1], TITLE.match(line) is not None
        elif STATUS.match(line) and not inside:
            found.append(name)
    return found


def front(text: str) -> tuple[dict[str, str], str]:
    r"""Return the leading block's keys and values, stripped, and the text after it.

    A line with no colon is no key. e.g. "---\nverdict: clean\n---\nx" → ({…}, "x")
    """
    found = FRONT.match(text)
    pairs = (line.partition(":") for line in (found[1] if found else "").splitlines())
    keys = {key.strip(): value.strip() for key, colon, value in pairs if colon}
    return keys, text[found.end() :] if found else text


def frontmatter(text: str, key: str) -> str | None:
    """Return a key's value in the text's leading block, or None."""
    return front(text)[0].get(key)


def fault(keys: dict[str, str], role: str, stub: bool) -> str | None:
    """Return why the frontmatter's keys break the contract's fields, else None."""
    needed = ["head", "round", "open_blocking", "verdict"]
    if not stub:
        needed += ["files", "commits", "inconclusive"]
        needed += ["passes"] if role == "conformance" else []
    for key in needed:
        value = keys.get(key)
        if value is None:
            return f"{key} is missing"
        if key in INTEGERS and not (value.isascii() and value.isdigit()):
            return f"{key} is not an integer"
        if key in LISTS and not (value.startswith("[") and value.endswith("]")):
            return f"{key} is not a list"
    if keys["verdict"] not in VERDICTS:
        return "verdict is neither clean nor changes-requested"
    return None


def listed(value: str) -> tuple[str, ...]:
    """Return a frontmatter list's items.

    e.g. "[stale-claim, test-cost]" → ("stale-claim", "test-cost"); "[]" → ()
    """
    items = (item.strip().strip("'\"") for item in value[1:-1].split(","))
    return tuple(item for item in items if item)


def read(path: Path) -> str | None:
    """Return a findings file's text through one descriptor that refuses a link.

    None when it is missing; a link, or a file that is no regular file, raises OSError.
    """
    try:
        return statefile.read(path)
    except FileNotFoundError:
        return None


def halt_ids(halt: str) -> set[str]:
    """Return the card ids an `amend needed` halt names.

    e.g. "halt — amend needed — R1, S2 · head a" → {"R1", "S2"}
    """
    return set(HALT_ID.findall(halt.partition("amend needed — ")[2]))


def stub(
    role: str,
    plan: str,
    project: str,
    branch: str,
    head: str,
    reviewed: str,
    round_: int,
) -> str:
    """Return a skipped checker's findings file: a clean stub of `role` at `head`."""
    keys = {
        "type": role,
        "plan": plan,
        "project": project,
        "branch": branch,
        "head": head,
        "reviewed": reviewed,
        "round": round_,
        "open_blocking": 0,
        "verdict": "clean",
        "mode": "skipped",
        "workers": 0,
        "model": "none",
        "executor": "none",
        "packet": "skipped: all",
    }
    lines = "".join(f"{key}: {value}\n" for key, value in keys.items())
    return f"---\n{lines}---\n\n{STUB_BODY}\n"


def uncleared(text: str) -> bool:
    """Return whether a findings file holds a checker's round not yet cleared.

    Cleared is a stub, or a clean verdict with each card `verified`: design D11.
    """
    keys, body = front(text)
    if keys.get("mode") == "skipped":
        return False
    return keys.get("verdict") != "clean" or any(
        card.status != "verified" for card in cards(body, "")
    )


def stamped(text: str, model: str | None, tokens: int | None) -> str | None:
    """Return a findings file with its frontmatter's `model:` and `tokens:` set.

    None when it has no frontmatter. e.g. `model: x` → `model: m`, then `tokens: 5`
    """
    found = FRONT.match(text)
    if found is None:
        return None
    kept = [
        line
        for line in found[1].splitlines(keepends=True)
        if not line.startswith("tokens:")
    ]
    stamp = [f"model: {model or 'default'}\n"]
    stamp += [] if tokens is None else [f"tokens: {tokens}\n"]
    at = next((i for i, line in enumerate(kept) if line.startswith("model:")), None)
    if at is None:
        kept += stamp
    else:
        kept[at : at + 1] = stamp
    return f"---\n{''.join(kept)}---\n{text[found.end() :]}"


def cards_conduct_legacy(text: str) -> Iterator[tuple[str, str]]:
    r"""Yield each card's id and its text, to the next card: `conduct.py`'s extent.

    e.g. "- **R1 — a finding**\n  - **Status:** open\n" → ("R1", that text)
    """
    starts = list(re.finditer(TITLE.pattern, text, re.MULTILINE))
    ends = [card.start() for card in starts[1:]] + [len(text)]
    for title, end in zip(starts, ends[: len(starts)], strict=True):
        yield title[1], text[title.start() : end]


def field_conduct_legacy(card: str, name: str) -> str:
    """Return a card's `- **<name>:** <value>` value, or "" with none."""
    found = re.search(rf"^[ \t]+- \*\*{name}:\*\*[ \t]*(.*)$", card, re.MULTILINE)
    return found[1].strip() if found else ""


def severity_conduct_legacy(card: str) -> str:
    """Return a card's severity: its `Priority`'s first part, in lower case."""
    return field_conduct_legacy(card, "Priority").split(" · ")[0].strip(" `").lower()


def category_conduct_legacy(card: str) -> str:
    """Return a card's category: its `Priority`'s third part, in lower case, or "".

    e.g. "high · adversarial · security — why" → "security"
    """
    parts = field_conduct_legacy(card, "Priority").split(" · ")
    return parts[2].split(" — ")[0].strip(" `").lower() if len(parts) > 2 else ""


def status_conduct_legacy(card: str) -> str:
    """Return a card's `Status`, its backticks dropped, as the severity drops them."""
    return field_conduct_legacy(card, "Status").strip(" `")


def security_conduct_legacy(card: str) -> bool:
    """Return whether an adversarial card blocks, in a security or unread category."""
    return (
        severity_conduct_legacy(card) in BLOCKS["adversarial"]
        and category_conduct_legacy(card) not in NON_SECURITY
    )


def frontmatter_conduct_legacy(text: str, key: str) -> str | None:
    """Return the first word of a key's value in the text's leading `---` block.

    e.g. a findings file opening `verdict: clean` in its block, "verdict" → "clean"
    """
    if not text.startswith("---\n"):
        return None
    block = text[4:].split("\n---", 1)[0]
    found = re.search(rf"^{key}:\s*(\S+)", block, re.MULTILINE)
    return found[1] if found else None


# `integrate.py`'s copy is the conductor's.
frontmatter_integrate_legacy = frontmatter_conduct_legacy


def cards_open_cards_legacy(text: str) -> list[str]:
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


# `overlap.py`'s copy is `open_cards.py`'s.
cards_overlap_legacy = cards_open_cards_legacy


def statuses_open_cards_legacy(card: str) -> list[tuple[str, str]]:
    """Return each `**Status:**` line's value and its word, `open_cards.py`'s way.

    e.g. "`*Fixed*`. — a note" → ("`*Fixed*`.", "fixed")
    """
    said = [status[1] for status in STATUS.finditer(card)]
    return [
        (each, re.split(r"\W", each.lstrip("`*_"), maxsplit=1)[0].casefold())
        for each in said
    ]


def read_open_cards_legacy(path: Path) -> str:
    """Return a file's text; one that cannot be read raises `Unread`, saying why."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Unread(f"{path}: {why}") from error


def affects_overlap_legacy(card: str) -> str | None:
    """Return a card's `What it affects` value as written, or None with none."""
    found = re.search(r"^[ \t]+- \*\*What it affects:\*\*(.*)$", card, re.MULTILINE)
    return found[1] if found else None


def blocks_overlap_legacy(card: str, blocking: tuple[str, ...]) -> bool:
    """Return whether a card's Priority opens with one of its role's blocking grades."""
    found = re.search(r"^[ \t]+- \*\*Priority:\*\*\s*(\S+)", card, re.MULTILINE)
    return found is not None and found[1] in blocking


def first_round_overlap_legacy(card: str) -> bool:
    """Return whether a card's **Round** is 1 or absent."""
    found = re.search(r"^[ \t]+- \*\*Round:\*\*\s*(\d+)", card, re.MULTILINE)
    return found is None or found[1] == "1"


def executor_overlap_legacy(text: str) -> str:
    """Return a findings file's frontmatter `executor:`, else `unknown`."""
    block = text.split("\n---", 1)[0] if text.startswith("---\n") else ""
    found = re.search(r"^executor:\s*(\S+)\s*$", block, re.MULTILINE)
    return found[1] if found else "unknown"


def read_overlap_legacy(path: Path) -> str:
    """Return a findings file's text; an unread one raises `Unread`, naming its path."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        raise Unread(str(path)) from error


def uncleared_skip_stub_legacy(text: str) -> bool:
    r"""Return whether a findings file holds a checker's round not yet cleared.

    Its keys are the lines before the first `\n---`; every Status line is read.
    """
    lines = text.split("\n---", 1)[0].splitlines()
    pairs = (line.partition(":") for line in lines)
    keys = {key.strip(): value.strip() for key, _, value in pairs}
    if keys.get("mode") == "skipped":
        return False
    statuses = re.findall(r"^[ \t]+- \*\*Status:\*\*[ \t]*(\w+)", text, re.MULTILINE)
    return keys.get("verdict") != "clean" or any(s != "verified" for s in statuses)
