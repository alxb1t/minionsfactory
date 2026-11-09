# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py>=3,<4"]
# ///
"""Check a hard brief has the shape the cut station needs, before its cut is queued.

    brief_check.py <brief>

Exit 0 ready · 1 a check halts · 2 the brief cannot be checked. Each halt prints
`brief: halt — …`. A command is a span of an Acceptance or `Verify:` item that holds a
space, held to `verify_check.py`'s shell rules; none runs. Each `## For the cut` item's
slug, bump, `after`, `beside` and models, which the close pastes into `conduct.py cut`,
are held to their shape; a models line may add checker and fixer parts, a host on a
model, and a last `shadow`. Each `## For the cut` line is a blank, a head `<n>. ` at
column 0, a `- models: ` or `- **Acceptance:** ` line under it, an Acceptance's
continuation, or the cut's `Cut` line. `## Dependencies` is `None.` or a table of
item · package · constraint · why. A checked line is printable, and each checked
heading is written one way, once. Sections and headings are read as CommonMark reads
them, so a fence holds none; a carriage return not before a newline halts its line.
Why: 0083-plan-queues design D1; 0088-paydown-2
design D5; 0091-cut-halts design D2; 0097-cross-model design D1;
0098-beside design D1, D2; 0098-beside security S1; 0103-fewer-rounds design D6.
"""

import argparse
import html
import re
import runpy
import sys
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt

VERIFY_CHECK = (
    Path(__file__).resolve().parents[2]
    / "mf-cut-change"
    / "scripts"
    / "verify_check.py"
)
CONDUCT = Path(__file__).resolve().parents[2] / "mf-ship" / "scripts" / "conduct.py"
AT = re.compile(r"At ([0-9a-f]{7,40}), (\d{4}-\d{2}-\d{2})\.")
ITEM = re.compile(r"- |\d+\. |\| ")
HEAD = re.compile(r"(\d+)\. (\S.*)")
MARKER = re.compile(r"(?:[-*+]|\d+[.)])(?:\s|$)|\|")
ACCEPTANCE = "- **Acceptance:** "
CUT = re.compile(r"Cut \d{4}-\d{2}-\d{2} as \d+-[a-z0-9-]+ at [0-9a-f]{7,40}\.")
LABEL = re.compile(r"\*\*Acceptance:\*\*|Verify:")
TOKEN = re.compile(r"[A-Za-z0-9._-]+")
TAG = re.compile(r"<[^>]*>")
LONE = re.compile(r"\r(?!\n)")
INLINE_HEADING = re.compile(r"<h[1-6](?:[\s/>]|$)", re.IGNORECASE)
# The parser the brief is read with: CommonMark, and GFM's tables.
# Why: 0103-fewer-rounds design D6.
MARKDOWN = MarkdownIt("commonmark").enable("table")
CHECKED = ("## Decisions", "## For the cut")
HEADINGS = ("## Decisions", "## Dependencies", "## For the cut")
BUMPS = ("minor", "patch")
STATIONS = ("build", "converge", "release", "cut")
CHECKS = ("conformance", "adversarial", "fix")
# The optional parts, in order. Why: 0102-build-per-phase design D6.
PARTS = ("build-moderate", *CHECKS)
HOSTS = ("claude", "codex")
HOSTLESS = ("cut", "fix", "build-moderate")
SKIPPABLE = ("converge", "conformance", "adversarial")
SHADOW = ["shadow"]
LIGHT = "the title says light: /mf-plan <what> depth=hard from=<brief>"
MODELS = (
    "the models line is not build · converge · release · cut, then any of"
    " build-moderate · conformance · adversarial · fix, each <model> <effort>,"
    " or skip for converge, conformance and adversarial, then shadow"
)
NEITHER = (
    "## Dependencies is neither None. nor a table of item · package · constraint · why"
)


def depth(brief: str) -> str | None:
    """Return the depth check's halt, or None when the title says `hard`."""
    title = next((line for line in brief.splitlines() if line.startswith("# ")), "")
    parts = [part.strip() for part in title[2:].split(" · ")]
    if "hard" in parts:
        return None
    return LIGHT if "light" in parts else "the title names no depth"


def parsed(brief: str) -> tuple[list[str], list[Any]]:
    """Return the brief's lines and its CommonMark tokens.

    A carriage return not before a newline reads as a space, so a token's `map` indexes
    the lines split at a newline alone. A vertical tab or another `str.splitlines`
    separator stays inside its line. Why: 0103-fewer-rounds design D6.
    """
    text = LONE.sub(" ", brief)
    return text.split("\n"), MARKDOWN.parse(text)


def headed(brief: str) -> list[tuple[str, list[str]]]:
    """Return each section's key and the lines under it, in order.

    A section opens on a heading token of level one or two, ATX or setext, or an HTML
    block opening `<h1` or `<h2`, a fence or code block holding none; it keys by its
    line as written and holds the lines to the next such line.
    Why: 0103-fewer-rounds design D6.
    """
    lines, tokens = parsed(brief)
    starts = sorted(
        {
            token.map[0]
            for token in tokens
            if (token.type == "heading_open" and token.tag in ("h1", "h2"))
            or (
                token.type == "html_block"
                and token.content.lstrip().lower().startswith(("<h1", "<h2"))
            )
        }
    )
    ends = [*starts[1:], len(lines)]
    return [(lines[a], lines[a + 1 : b]) for a, b in zip(starts, ends, strict=True)]


def sections(brief: str) -> dict[str, list[str]]:
    """Return each `## ` section's lines, keyed by its heading, which they exclude.

    A heading written twice keys one section, its lines in order, per `headed`.
    """
    found: dict[str, list[str]] = {}
    for heading, lines in headed(brief):
        found.setdefault(heading, []).extend(lines)
    return found


def items(lines: list[str]) -> list[str]:
    """Return each item of a section: its lines, stripped, joined by a space.

    An item's line wraps onto each deeper line after it that opens no item, and, as
    Markdown's lazy continuation does, onto any other line before a blank one that
    opens no list marker or `|`. As in CommonMark, only spaces and tabs indent a line
    or blank it: a line of NBSP or a form feed is text.
    e.g. ["- a", "  b", "c", "- d", "* e"] → ["- a b c", "- d"]
    """
    found: list[str] = []
    indent: int | None = None
    for line in lines:
        text = line.lstrip(" \t")
        at = len(line) - len(text)
        if ITEM.match(text):
            found.append(text.strip())
            indent = at
        elif indent is not None and text and (at > indent or not MARKER.match(text)):
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


def ids(number: str, kind: str, value: str, slug: re.Pattern[str]) -> list[str]:
    """Return a halt for each entry of a head's `after` or `beside` part `slug` refuses.

    `kind` names the entry; `none` names none.
    e.g. "1", "a beside", " [x, a;b]" → ["item 1 — not a beside id: `a;b`"]
    """
    if (value := value.strip("[] `")) == "none":
        return []
    return [
        f"item {number} — not {kind} id: `{named}`"
        for named in (entry.strip("` ") for entry in value.split(","))
        if not slug.fullmatch(named)
    ]


def head(number: str, parts: list[str], slug: re.Pattern[str]) -> list[str]:
    """Return a halt for each field of an item's head out of shape.

    `parts` is the head split on ` · `; its slug and each `after` and `beside` entry
    match `slug`. `beside:` is optional.
    e.g. "1", ["**x$(y)**", "minor", "after: none"] → ["item 1 — not a slug: `x$(y)`"]
    """
    found: list[str] = []
    if not slug.fullmatch(name := parts[0].strip("*` ")):
        found.append(f"item {number} — not a slug: `{name}`")
    if (bump := "".join(parts[1:2]).strip("` ")) not in BUMPS:
        found.append(f"item {number} — not a bump: `{bump}`")
    afters = [part[6:] for part in parts if part.startswith("after:")]
    if len(afters) > 1:
        found.append(f"item {number} — more than one after:")
    elif not afters:
        found.append(f"item {number} — no after:")
    else:
        found += ids(number, "an after", afters[0], slug)
    besides = [part[7:] for part in parts if part.startswith("beside:")]
    if len(besides) > 1:
        found.append(f"item {number} — more than one beside:")
    elif besides:
        found += ids(number, "a beside", besides[0], slug)
    return found


def models(number: str, text: str) -> list[str]:
    """Return a halt for each word of an item's `models:` line out of shape.

    The stations, then an ordered subset of `PARTS`. A model may open `<host>/`,
    save on `HOSTLESS`. `converge`, `conformance` and `adversarial` may read `skip`
    for their model and effort.
    e.g. "1", " build a b · converge a b · release a b · cut a b;c" →
    ["item 1 — not a model or effort: `b;c`"]
    """
    parts = [part.split() for part in text.split(" · ")]
    shadowed = parts[-1:] == [SHADOW]
    if shadowed:
        parts.pop()
    # A part's name is read from three words, or from a skip of a checker or converge.
    # Why: 0105-converge-switches design D1.
    names = [
        part[0]
        if len(part) == 3 or (part[1:] == ["skip"] and part[0] in SKIPPABLE)
        else None
        for part in parts
    ]
    optional = names[len(STATIONS) :]
    if names[: len(STATIONS)] != list(STATIONS) or optional != [
        part for part in PARTS if part in optional
    ]:
        return [f"item {number} — {MODELS}"]
    found: list[str] = []
    skipped = {part[0] for part in parts if part[1:] == ["skip"]}
    for name, *rest in parts:
        if rest == ["skip"]:
            continue
        model, effort = rest
        if model == "skip":
            found.append(f"item {number} — a skip takes no model or effort")
            continue
        host, slash, word = model.rpartition("/")
        if slash and name in HOSTLESS:
            found.append(f"item {number} — {name} takes no host: `{model}`")
        elif slash and host not in HOSTS:
            found.append(f"item {number} — not a host: `{host}`")
        found += [
            f"item {number} — not a model or effort: `{token}`"
            for token in (word, effort)
            if not TOKEN.fullmatch(token)
        ]
    if shadowed and skipped:
        found.append(f"item {number} — a skip is not beside shadow")
    if "converge" in skipped and any(part[0] in CHECKS for part in parts):
        found.append(
            f"item {number} — converge skip takes no conformance, adversarial or fix"
            " part"
        )
    elif {"conformance", "adversarial"} <= skipped:
        found.append(
            f"item {number} — conformance skip and adversarial skip together:"
            " write converge skip"
        )
    return found


def fields(lines: list[str], slug: re.Pattern[str]) -> list[str]:
    """Return a halt for each `## For the cut` field `conduct.py cut` takes, misshapen.

    `lines` are one heading's. Each head is read from its own line, opening `<n>. `
    at column 0, and each `- models: ` line after it, as `grammar` places one, once
    a head.
    """
    found: list[str] = []
    numbers: list[str] = []
    named: set[str] = set()
    column = 3
    for line in lines:
        text = line.lstrip(" ")
        if opened := HEAD.match(line):
            numbers.append(opened[1])
            column = len(opened[1]) + 2
            found += head(opened[1], opened[2].split(" · "), slug)
        elif (
            numbers
            and len(line) - len(text) in (3, column)
            and text.startswith("- models: ")
        ):
            if numbers[-1] in named:
                found.append(f"item {numbers[-1]} — more than one models line")
            named.add(numbers[-1])
            found += models(numbers[-1], text.removeprefix("- models:"))
    found += [
        f"item {number} — no models line" for number in numbers if number not in named
    ]
    return [f"## For the cut: {line}" for line in found]


def packages(brief: str, lines: list[str], conduct: dict[str, Any]) -> list[str]:
    """Return a halt for each way `## Dependencies` is out of shape.

    `lines` are `## For the cut`'s, whose heads name the items a row may name;
    `conduct` is `conduct.py`'s namespace, whose `_rows` reads the table.
    """
    rows = conduct["_rows"](brief, conduct["DEPENDENCIES"])
    if rows is None or rows[:1] not in ([], [conduct["APPROVED"]]):
        return [NEITHER]
    slugs = {
        opened[2].split(" · ")[0].strip("*` ")
        for line in lines
        if (opened := HEAD.match(line))
    }
    found: list[str] = []
    for number, (item, package, constraint, _) in enumerate(rows[1:], 1):
        if item not in slugs:
            found.append(
                f"## Dependencies row {number} — not an item of ## For the cut:"
                f" `{item}`"
            )
        if not package or not constraint:
            found.append(f"## Dependencies row {number} — no package or constraint")
    return found


def grammar(lines: list[str]) -> list[str]:
    """Return a halt for each `## For the cut` line outside the item grammar.

    A line is a blank of spaces; a head, `<n>. ` and text at column 0; under a head, a
    `- models: ` or `- **Acceptance:** ` line three spaces in or at its head's text; a
    continuation, two or more spaces past the Acceptance line, right after it or
    another; or the cut's `Cut` line. Lines count from 1 under the heading.
    Why: 0098-beside design D1, D2.
    e.g. ["1. **a** · minor", "| · after: x"] → ["## For the cut line 2: …"]
    """
    found: list[str] = []
    column = 3
    seen_head = False
    accepted: int | None = None
    for number, line in enumerate(lines, 1):
        text = line.lstrip(" ")
        at = len(line) - len(text)
        nested = None
        if opened := HEAD.match(line):
            column = len(opened[1]) + 2
            seen_head = True
        elif (
            seen_head
            and at in (3, column)
            and text.startswith(("- models: ", ACCEPTANCE))
        ):
            nested = at if text.startswith(ACCEPTANCE) else None
        elif accepted is not None and at >= accepted + 2 and text:
            nested = accepted
        elif text and not CUT.fullmatch(line):
            found.append(
                f"## For the cut line {number}: outside the item grammar: `{line}`"
            )
        accepted = nested
    return found


def printable(heading: str, lines: list[str]) -> list[str]:
    r"""Return a halt for each line of a section holding a character not printable.

    Lines count from 1 under the heading.
    e.g. "## Decisions", ["| 1 |\ta |"] → ["## Decisions line 1: a character …"]
    """
    return [
        f"{heading} line {number}: a character isprintable() refuses"
        for number, line in enumerate(lines, 1)
        if not line.isprintable()
    ]


def fold(text: str) -> str:
    r"""Return the letters and digits `text` renders as, case-folded.

    Its HTML tags, heading and inline, drop, then its character references read as
    the characters they name. Why: 0098-beside design D1, D2; 0098-beside security S1.
    e.g. "<h2><em>For the C&#117;t</em></h2>" → "forthecut"
    """
    text = html.unescape(TAG.sub("", text))
    return "".join(char for char in text if char.isalnum()).casefold()


def alike(line: str, heading: str) -> bool:
    """Return whether a folded line reads as a folded heading.

    They match where `line` holds an ASCII character; a non-ASCII one stands for any.
    `line` keeps at least one ASCII letter.
    e.g. "fоrthecut", a Cyrillic `о`, "forthecut" → True
    """
    return (
        len(line) == len(heading)
        and any(char.isascii() and char.isalpha() for char in line)
        and all(
            ours == theirs or not ours.isascii()
            for ours, theirs in zip(line, heading, strict=True)
        )
    )


def headings(brief: str) -> list[str]:
    """Return a halt per line reading as a checked heading not written so, or twice.

    The lines checked are those of a heading token, an HTML block, and a paragraph
    whose inline HTML opens `<h1>`…`<h6>`; a fence holds none. A line reads as a
    heading when `alike` holds for their folds, unless it is an ATX `h2` written so,
    which counts. Lines count from 1 in the brief.
    Why: 0098-beside design D1, D2; 0103-fewer-rounds design D6.
    e.g. " ## For the cut" → ["line 1 reads as `## For the cut` but is not written so"]
    """
    lines, tokens = parsed(brief)
    checked: set[int] = set()
    atx: set[int] = set()
    block = (0, 0)
    for token in tokens:
        if token.type == "heading_open":
            checked.update(range(*token.map))
            if token.tag == "h2" and token.markup == "##":
                atx.add(token.map[0])
        elif token.type == "html_block":
            checked.update(range(*token.map))
        elif token.map:
            block = token.map
        if token.type == "inline" and any(
            child.type == "html_inline" and INLINE_HEADING.match(child.content)
            for child in token.children or []
        ):
            checked.update(range(*(token.map or block)))
    found: list[str] = []
    seen: set[str] = set()
    for number in sorted(checked):
        for heading in HEADINGS:
            if number in atx and lines[number] == heading:
                if heading in seen:
                    found.append(f"line {number + 1}: a second `{heading}`")
                seen.add(heading)
            elif alike(fold(lines[number]), fold(heading)):
                found.append(
                    f"line {number + 1} reads as `{heading}` but is not written so"
                )
    return found


def carriage(brief: str) -> list[str]:
    r"""Return a halt per line holding a carriage return not before a newline.

    Lines count from 1, split at a newline alone. Why: 0103-fewer-rounds design D6.
    e.g. "a\rb\n" → ["line 1: a carriage return not before a newline"]
    """
    numbers = sorted(
        {brief.count("\n", 0, lone.start()) + 1 for lone in LONE.finditer(brief)}
    )
    return [
        f"line {number}: a carriage return not before a newline" for number in numbers
    ]


def main(argv: list[str] | None = None) -> int:
    """Check a brief; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Check a hard brief before its cut is queued."
    )
    parser.add_argument("brief", type=Path, help="the brief to check")
    path = parser.parse_args(argv).brief
    try:
        with path.open(newline="") as handle:
            raw = handle.read()
    except OSError as error:
        print(f"brief: cannot check — {path}: {error.strerror}")
        return 2
    brief = re.sub(r"\r\n?", lambda end: "\n" if end[0] == "\r\n" else " ", raw)
    for script in (VERIFY_CHECK, CONDUCT):
        if not script.is_file():
            print(f"brief: cannot check — no {script.name} beside this skill")
            return 2
    rules = runpy.run_path(str(VERIFY_CHECK))
    conduct = runpy.run_path(str(CONDUCT))
    slug = conduct["SLUG"]
    parts = sections(brief)
    found: list[str] = []
    if title := depth(brief):
        found.append(title)
    if not any(AT.fullmatch(line) for line in brief.splitlines()):
        found.append("no At <sha>, <YYYY-MM-DD>. line")
    if not any(line.strip() for line in parts.get("## For the cut", [])):
        found.append("## For the cut is empty")
    found += carriage(raw)
    found += headings(brief)
    if "## Dependencies" not in parts:
        found.append("no ## Dependencies section")
    else:
        found += packages(brief, parts.get("## For the cut", []), conduct)
    for heading in HEADINGS:
        found += printable(heading, parts.get(heading, []))
    found += grammar(parts.get("## For the cut", []))
    for heading, lines in headed(brief):
        if heading == "## For the cut":
            found += fields(lines, slug)
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
