"""Write and parse a findings file: its cards, their fields and words, its frontmatter.

Why: 0138-findings design D1.
"""

import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from . import layout, statefile

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
# The contract's card ids; any other titled card makes the file malformed.
ID = re.compile(r"[RS]\d+")
# Any top-level bold line, off the card's form or not: names a stray field's card.
NAMED = re.compile(r"^[-*] \*\*([^\s*:]+)")
# The fields a line under no card makes the file malformed by: 0138-findings design D7.
STRAYS = ("Status", "Priority")
FRONT = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
INTEGERS = ("round", "open_blocking", "files", "commits")
LISTS = ("passes", "inconclusive")
VERDICTS = ("clean", "changes-requested")
HALT_ID = re.compile(r"\b[RS]\d+\b")
STUB_BODY = "Skipped by the plan: no worker judged this round."


def _words(value: str) -> list[str]:
    """Return a value's words, its backticks and bold dropped.

    e.g. "`**Fixed**` — a note" → ["Fixed", "—", "a", "note"]
    """
    return value.replace("`", "").replace("*", "").split()


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
        words = _words(self.fields.get(name, ""))
        return words[0].rstrip(".,;:").casefold() if words else ""

    @property
    def severity(self) -> str:
        """Return the grade its Priority opens with."""
        return self.word("Priority")

    @property
    def category(self) -> str:
        """Return the category its Priority names third, read as a word is, or "".

        e.g. "high · adversarial · `Data integrity` — why" → "data integrity"
        """
        parts = self.fields.get("Priority", "").split(" · ")
        named = _words(parts[2].split(" — ")[0]) if len(parts) > 2 else []
        return " ".join(named).rstrip(".,;:").casefold()

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
    def size(self) -> str:
        """Return the size its Fix names last, or "" with none.

        e.g. "a fix · size: `a test`." → "a test"
        """
        sized = SIZE.search(self.fields.get("Fix", ""))
        return sized[1].strip(" `.") if sized else ""

    @property
    def small(self) -> bool:
        """Return whether its Fix size is one of `SMALL`, read literally."""
        return self.size in SMALL

    @property
    def security(self) -> bool:
        """Return whether it is a blocking adversarial card of no category named safe.

        An unread category is security: 0138-findings design D6.
        """
        return (
            self.role == "adversarial"
            and self.blocking
            and self.category not in NON_SECURITY
        )


def cards(text: str, role: str) -> list[Card]:
    """Return the cards of a findings file, each with its fields; the first field wins.

    A card is its title and its indented lines, blanks between: 0138 design D4.
    """
    found: list[Card] = []
    current: Card | None = None
    blanks: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            blanks.append(line)
            continue
        if title := TITLE.match(line):
            current = Card(title[1], role, {}, [line])
            found.append(current)
        elif current is None or not line.startswith((" ", "\t")):
            current = None
        else:
            current.lines.extend([*blanks, line])
            if named := FIELD.match(line):
                current.fields.setdefault(named[1], named[2].strip())
        blanks = []
    return found


def strays(text: str) -> list[tuple[str, str]]:
    r"""Return each Status or Priority line under no card: its field and the bold above.

    e.g. "- **Note**\n  - **Status:** open\n" → [("Status", "Note")]; none, "unnamed"
    """
    found: list[tuple[str, str]] = []
    name, inside = "unnamed", False
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("#"):
            name, inside = "unnamed", False
        elif bold := NAMED.match(line):
            name, inside = bold[1], TITLE.match(line) is not None
        elif not line.startswith((" ", "\t")):
            name, inside = "unnamed", False
        elif (named := FIELD.match(line)) and named[1] in STRAYS and not inside:
            found.append((named[1], name))
    return found


def malformed(text: str, role: str) -> str | None:
    """Return why a findings file's cards break the contract, else None.

    e.g. a card titled `S-1` → "card S-1 is not R<n> or S<n>".
    Why: 0138-findings design D7.
    """
    for card in cards(text, role):
        if not ID.fullmatch(card.id):
            return f"card {card.id} is not R<n> or S<n>"
    if found := strays(text):
        name, under = found[0]
        return f"a {name} under no card: {under}"
    return None


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


def keyed(text: str, values: Mapping[str, object]) -> str:
    r"""Return the text with each key of its leading block that `values` names set.

    A key the block lacks stays unset. Why: 0138-findings design D8.
    e.g. "---\nround: 1\n---\nround: 7\n", {"round": 2} → "round: 2" above, 7 kept
    """
    found = FRONT.match(text)
    if found is None:
        return text
    lines = found[1].splitlines(keepends=True)
    for at, line in enumerate(lines):
        key, colon, _ = line.partition(":")
        if colon and key.strip() in values:
            lines[at] = f"{key.strip()}: {values[key.strip()]}\n"
    return f"---\n{''.join(lines)}---\n{text[found.end() :]}"


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


def _staged(folder: Path, name: str, edit: Callable[[str], str | None]) -> bool:
    """Write `edit` of a findings file over it, following no link; else leave it.

    Staged as `<name>.tmp` at mode 0600 and renamed over it: 0138-findings design D12.
    False when a read or the write failed; True when it wrote, or `edit` left it.
    """
    root, parts = layout.beneath(folder.parent)
    try:
        fd = statefile.folder(root, *parts, folder.name)
        try:
            text = statefile.read(name, folder=fd)
            if (done := edit(text)) is not None:
                statefile.write(Path(name), done, folder=fd, mode=0o600)
        finally:
            os.close(fd)
    except (OSError, statefile.WriteFailed):
        return False
    return True


def stamp(folder: Path, name: str, model: str | None, tokens: int | None) -> None:
    """Set a findings file's `model:` and `tokens:`, following no link, or leave it."""
    _staged(folder, name, lambda text: stamped(text, model, tokens))


def counted(text: str, values: Mapping[str, object]) -> str | None:
    r"""Return the text with each key of `values` set in its leading block, or added.

    None for no frontmatter, a stub or a by-rule file. Why: 0151-stamps design D3.
    e.g. "---\nfiles: 3\n---\n", {"files": 4, "round": 2} → "files: 4", "round: 2"
    """
    found, keys = FRONT.match(text), front(text)[0]
    if found is None or keys.get("mode") in ("skipped", "by-rule"):
        return None
    block = keyed(found[0], values).removesuffix("---\n")
    added = "".join(
        f"{key}: {value}\n" for key, value in values.items() if key not in keys
    )
    return f"{block}{added}---\n{text[found.end() :]}"


def count(folder: Path, name: str, values: Mapping[str, object]) -> bool:
    """Set a findings file's keys to `values`, following no link, or leave it.

    False when the file could not be read or written, so the caller can halt.
    """
    return _staged(folder, name, lambda text: counted(text, values))
