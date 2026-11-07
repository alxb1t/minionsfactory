# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check a hard brief has the shape the cut station needs, before its cut is queued.

    brief_check.py <brief>

Exit 0 ready · 1 a check halts · 2 the brief cannot be checked. Each halt prints
`brief: halt — …`. A command is a span of an Acceptance or `Verify:` item that holds a
space, held to `verify_check.py`'s shell rules; none runs. Each `## For the cut` item's
slug, bump, `after` and models, which the close pastes into `conduct.py cut`, are held
to their shape. Why: 0083-plan-queues design D1; 0088-paydown-2 design D5.
"""

import argparse
import re
import runpy
import sys
from pathlib import Path
from typing import Any

VERIFY_CHECK = (
    Path(__file__).resolve().parents[2]
    / "mf-cut-change"
    / "scripts"
    / "verify_check.py"
)
CONDUCT = Path(__file__).resolve().parents[2] / "mf-ship" / "scripts" / "conduct.py"
AT = re.compile(r"At ([0-9a-f]{7,40}), (\d{4}-\d{2}-\d{2})\.")
ITEM = re.compile(r"- |\d+\. |\| ")
HEAD = re.compile(r"(\d+)\. (.*)")
LABEL = re.compile(r"\*\*Acceptance:\*\*|Verify:")
TOKEN = re.compile(r"[A-Za-z0-9._-]+")
CHECKED = ("## Decisions", "## For the cut")
BUMPS = ("minor", "patch")
STATIONS = ("build", "converge", "release", "cut")
LIGHT = "the title says light: /mf-plan <what> depth=hard from=<brief>"
MODELS = (
    "the models line is not build · converge · release · cut, each <model> <effort>"
)


def depth(brief: str) -> str | None:
    """Return the depth check's halt, or None when the title says `hard`."""
    title = next((line for line in brief.splitlines() if line.startswith("# ")), "")
    parts = [part.strip() for part in title[2:].split(" · ")]
    if "hard" in parts:
        return None
    return LIGHT if "light" in parts else "the title names no depth"


def sections(brief: str) -> dict[str, list[str]]:
    """Return each `## ` section's lines, keyed by its heading, which they exclude."""
    found: dict[str, list[str]] = {}
    lines: list[str] | None = None
    for line in brief.splitlines():
        if line.startswith("## "):
            lines = found.setdefault(line.rstrip(), [])
        elif lines is not None:
            lines.append(line)
    return found


def items(lines: list[str]) -> list[str]:
    """Return each item of a section: its lines, stripped, joined by a space.

    An item's line wraps onto each deeper line after it that opens no item.
    e.g. ["- a", "  b", "- c"] → ["- a b", "- c"]
    """
    found: list[str] = []
    indent: int | None = None
    for line in lines:
        text = line.lstrip()
        at = len(line) - len(text)
        if ITEM.match(text):
            found.append(text.strip())
            indent = at
        elif indent is not None and text and at > indent:
            found[-1] += " " + text.strip()
        else:
            indent = None
    return found


def halts(heading: str, lines: list[str], rules: dict[str, Any]) -> list[str]:
    """Return a halt for each command of a section's items that breaks `I19`.

    `rules` is `verify_check.py`'s namespace; its `Unparsed` is raised to the caller.
    """
    found: list[str] = []
    for item in items(lines):
        hidden = rules["SPAN"].sub(lambda span: " " * len(span[0]), item)
        if (label := LABEL.search(hidden)) is None:
            continue
        for command in rules["commands"](item[label.end() :]):
            text = command.text
            if " " not in text:
                continue
            # Masking hides an unclosed quote; the raw text raises the cut's Unparsed.
            rules["tokens"](text)
            if broken := rules["breaks"](text, rules["tokens"](rules["masked"](text))):
                found.append(f"{heading}: I19 — {' · '.join(broken)}: `{text}`")
    return found


def head(number: str, parts: list[str], slug: re.Pattern[str]) -> list[str]:
    """Return a halt for each field of an item's head out of shape.

    `parts` is the head split on ` · `; its slug and each `after` entry match `slug`.
    e.g. "1", ["**x$(y)**", "minor", "after: none"] → ["item 1 — not a slug: `x$(y)`"]
    """
    found: list[str] = []
    if not slug.fullmatch(name := parts[0].strip("*` ")):
        found.append(f"item {number} — not a slug: `{name}`")
    if (bump := "".join(parts[1:2]).strip("` ")) not in BUMPS:
        found.append(f"item {number} — not a bump: `{bump}`")
    afters = [part[6:] for part in parts if part.startswith("after:")]
    if len(afters) > 1:
        return [*found, f"item {number} — more than one after:"]
    if not afters:
        return [*found, f"item {number} — no after:"]
    after = afters[0]
    if (after := after.strip("[] `")) == "none":
        return found
    for named in after.split(","):
        if not slug.fullmatch(named := named.strip("` ")):
            found.append(f"item {number} — not an after id: `{named}`")
    return found


def models(number: str, text: str) -> list[str]:
    """Return a halt for each word of an item's `models:` line out of shape.

    e.g. "1", " build a b · converge a b · release a b · cut a b;c" →
    ["item 1 — not a model or effort: `b;c`"]
    """
    parts = [part.split() for part in text.split(" · ")]
    if [part[0] if len(part) == 3 else None for part in parts] != list(STATIONS):
        return [f"item {number} — {MODELS}"]
    return [
        f"item {number} — not a model or effort: `{word}`"
        for part in parts
        for word in part[1:]
        if not TOKEN.fullmatch(word)
    ]


def fields(lines: list[str], slug: re.Pattern[str]) -> list[str]:
    """Return a halt for each `## For the cut` field `conduct.py cut` takes, misshapen.

    A head is an item opening `<n>. `; its `- models:` item follows it. An item with
    no indent opens a head.
    """
    found = [
        f"not a numbered item: `{line.rstrip()}`"
        for line in lines
        if ITEM.match(line) and not HEAD.match(line)
    ]
    numbers: list[str] = []
    named: set[str] = set()
    for item in items(lines):
        if opened := HEAD.match(item):
            numbers.append(opened[1])
            found += head(opened[1], opened[2].split(" · "), slug)
        elif numbers and item.startswith("- models:"):
            named.add(numbers[-1])
            found += models(numbers[-1], item.removeprefix("- models:"))
    found += [
        f"item {number} — no models line" for number in numbers if number not in named
    ]
    return [f"## For the cut: {line}" for line in found]


def main(argv: list[str] | None = None) -> int:
    """Check a brief; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Check a hard brief before its cut is queued."
    )
    parser.add_argument("brief", type=Path, help="the brief to check")
    path = parser.parse_args(argv).brief
    try:
        brief = path.read_text()
    except OSError as error:
        print(f"brief: cannot check — {path}: {error.strerror}")
        return 2
    for script in (VERIFY_CHECK, CONDUCT):
        if not script.is_file():
            print(f"brief: cannot check — no {script.name} beside this skill")
            return 2
    rules = runpy.run_path(str(VERIFY_CHECK))
    slug = runpy.run_path(str(CONDUCT))["SLUG"]
    parts = sections(brief)
    found: list[str] = []
    if title := depth(brief):
        found.append(title)
    if not any(AT.fullmatch(line) for line in brief.splitlines()):
        found.append("no At <sha>, <YYYY-MM-DD>. line")
    if not any(line.strip() for line in parts.get("## For the cut", [])):
        found.append("## For the cut is empty")
    found += fields(parts.get("## For the cut", []), slug)
    for line in found:
        print(f"brief: halt — {line}")
    for heading in CHECKED:
        try:
            broken = halts(heading, parts.get(heading, []), rules)
        except rules["Unparsed"] as error:
            print(f"brief: cannot check — {heading}: {error}")
            return 2
        for line in broken:
            print(f"brief: halt — {line}")
        found += broken
    if found:
        return 1
    print("brief: ready for the cut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
