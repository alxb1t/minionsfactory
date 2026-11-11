# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py>=3,<4"]
# ///
"""Check a hard brief has the shape the cut station needs, before its cut is queued.

Why: 0083-plan-queues D1; 0088-paydown-2 D5; 0091-cut-halts D2; 0097-cross-model D1;
0098-beside D1, D2, security S1; 0103-fewer-rounds D6; 0106-cut-scripts D1, D2, D3.
"""

import argparse
import html
import json
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
BLOCK_HEADING = re.compile(r"<h[12](?:[\s/>]|$)", re.IGNORECASE)
# A path is components of `[A-Za-z0-9._-]`, none `.` or `..`, with a `/` or a leading
# `./`: a basename is no path. Why: 0106-cut-scripts design D1.
COMPONENT = r"(?!\.{1,2}(?=[/:]))[A-Za-z0-9._-]+"
PATH = rf"(?:\./{COMPONENT}(?:/{COMPONENT})*|{COMPONENT}(?:/{COMPONENT})+)"
LINES = r"\d+(?:-\d+)?"
FACT = re.compile(
    rf" \((?P<cites>`{PATH}:{LINES}`(?:, `{PATH}:{LINES}`)*)"
    r" at `(?P<sha>[0-9a-f]{7,40})`\)$"
)
CITE = re.compile(rf"`(?P<path>{PATH}):(?P<start>\d+)(?:-(?P<end>\d+))?`")
# The tables of a models file, by the part that names each.
# Why: 0106-cut-scripts design D2.
TABLES = {
    "build": "build",
    "build-moderate": "build.moderate",
    "converge": "converge",
    "conformance": "converge.conformance",
    "adversarial": "converge.adversarial",
    "fix": "converge.fix",
    "release": "release",
}
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
HOSTLESS = ("cut", "build-moderate")
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

    Why: 0103-fewer-rounds design D6.
    """
    text = LONE.sub(" ", brief)
    return text.split("\n"), MARKDOWN.parse(text)


def headed(brief: str) -> list[tuple[str, list[str]]]:
    """Return each section's key and the lines under it, in order.

    An `h1` or `h2` heading or HTML block opens one. Why: 0103-fewer-rounds design D6.
    """
    lines, tokens = parsed(brief)
    starts = sorted(
        {
            token.map[0]
            for token in tokens
            if (token.type == "heading_open" and token.tag in ("h1", "h2"))
            or (
                token.type == "html_block"
                and BLOCK_HEADING.match(token.content.lstrip())
            )
        }
    )
    ends = [*starts[1:], len(lines)]
    return [(lines[a], lines[a + 1 : b]) for a, b in zip(starts, ends, strict=True)]


def sections(brief: str) -> dict[str, list[str]]:
    """Return the lines under each `# ` or `## ` heading, keyed by the heading.

    A heading written twice keys one section, its lines in order, per `headed`.
    """
    found: dict[str, list[str]] = {}
    for heading, lines in headed(brief):
        found.setdefault(heading, []).extend(lines)
    return found


def items(lines: list[str]) -> list[str]:
    """Return each item of a section: its lines, stripped, joined by a space."""
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


def facts(lines: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return the `## Facts` items as facts, and a halt for each out of grammar.

    A fact is its text, its cites (`./` dropped) and its sha. Why: 0106 design D1.
    """
    found: list[dict[str, Any]] = []
    halted: list[str] = []
    for number, item in enumerate(items(lines), 1):
        text = ITEM.sub("", item, count=1)
        if (tail := FACT.search(text)) is None:
            halted.append(f"## Facts: fact {number} — {text}")
            continue
        cites = [
            {
                "path": cite["path"].removeprefix("./"),
                "start": int(cite["start"]),
                "end": int(cite["end"] or cite["start"]),
            }
            for cite in CITE.finditer(tail["cites"])
        ]
        found.append({"fact": text[: tail.start()], "cites": cites, "sha": tail["sha"]})
    return found, halted


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
    """Return a halt for each field of an item's head out of shape."""
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
    """Return a halt for each word of an item's `models:` line out of shape."""
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


def modelled(line: str, column: int) -> bool:
    """Return whether a line is an item's `- models: ` line, as `grammar` places one."""
    text = line.lstrip(" ")
    return len(line) - len(text) in (3, column) and text.startswith("- models: ")


def chosen(lines: list[str], name: str) -> tuple[re.Match[str], list[str]] | None:
    """Return the head and lines of the `## For the cut` item `name` heads, or None.

    The item runs from its head to the next one. Why: 0106 design D2.
    """
    heads = [
        (number, opened)
        for number, line in enumerate(lines)
        if (opened := HEAD.match(line))
        and opened[2].split(" · ")[0].strip("*` ") == name
    ]
    if not heads:
        return None
    start, opened = heads[0]
    rest = lines[start + 1 :]
    stop = next((n for n, line in enumerate(rest) if HEAD.match(line)), len(rest))
    return opened, lines[start : start + 1 + stop]


def models_toml(opened: re.Match[str], item: list[str]) -> str:
    """Return the models file of a checked `## For the cut` item, as TOML.

    One table per stage of `TABLES`, in order; its shape is in 0106 design D2.
    """
    line = next(line for line in item if modelled(line, len(opened[1]) + 2))
    parts = [part.split() for part in line.lstrip(" ")[len("- models:") :].split(" · ")]
    named = {name: rest for name, *rest in parts}
    shadowed = parts[-1:] == [SHADOW]
    decided = "decide: recommended" in opened[2].rstrip().split(" · ")
    blocks = ['decide = "recommended"'] if decided else []
    for name, table in TABLES.items():
        if (rest := named.get(name)) is None:
            continue
        lines = [f"[{table}]"]
        if rest == ["skip"]:
            lines.append("skip = true")
        else:
            host, slash, model = rest[0].rpartition("/")
            lines += [f'model = "{model}"', f'effort = "{rest[1]}"']
            lines += [f'executor = "{host}"'] if slash else []
        lines += ["shadow = true"] if name == "converge" and shadowed else []
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def fields(lines: list[str], slug: re.Pattern[str]) -> list[str]:
    """Return a halt per misshapen `## For the cut` field `conduct.py cut` takes."""
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
        elif numbers and modelled(line, column):
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

    Why: 0098-beside design D1, D2.
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

    Why: 0098-beside design D1, D2; 0098-beside security S1.
    """
    text = html.unescape(TAG.sub("", text))
    return "".join(char for char in text if char.isalnum()).casefold()


def alike(line: str, heading: str) -> bool:
    """Return whether a folded line reads as a folded heading."""
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

    Why: 0098-beside design D1, D2; 0103-fewer-rounds design D6.
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
    parser.add_argument("slug", nargs="?", help="the item `--models` prints")
    form = parser.add_mutually_exclusive_group()
    form.add_argument("--facts", action="store_true", help="print the facts as JSON")
    form.add_argument(
        "--sections", action="store_true", help="print the sections as JSON"
    )
    form.add_argument(
        "--models", action="store_true", help="print the item's models file as TOML"
    )
    args = parser.parse_args(argv)
    if args.models != (args.slug is not None):
        parser.error("--models takes a brief and a slug, and a slug only --models")
    path = args.brief
    try:
        with path.open(newline="") as handle:
            raw = handle.read()
    except OSError as error:
        print(f"brief: cannot check — {path}: {error.strerror}")
        return 2
    brief = re.sub(r"\r\n?", lambda end: "\n" if end[0] == "\r\n" else " ", raw)
    if args.facts:
        found, halted = facts(sections(brief).get("## Facts", []))
        for line in halted:
            print(f"brief: halt — {line}")
        if not halted:
            print(json.dumps(found))
        return 1 if halted else 0
    if args.sections:
        print(json.dumps(sections(brief)))
        return 0
    for script in (VERIFY_CHECK, CONDUCT):
        if not script.is_file():
            print(f"brief: cannot check — no {script.name} beside this skill")
            return 2
    rules = runpy.run_path(str(VERIFY_CHECK))
    conduct = runpy.run_path(str(CONDUCT))
    slug = conduct["SLUG"]
    parts = sections(brief)
    if args.models:
        if (item := chosen(parts.get("## For the cut", []), args.slug)) is None:
            print(
                f"brief: cannot check — no item named `{args.slug}` in ## For the cut"
            )
            return 2
        for line in (broken := fields(item[1], slug)):
            print(f"brief: halt — {line}")
        if not broken:
            print(models_toml(*item), end="")
        return 1 if broken else 0
    found: list[str] = []
    if title := depth(brief):
        found.append(title)
    if not any(AT.fullmatch(line) for line in brief.splitlines()):
        found.append("no At <sha>, <YYYY-MM-DD>. line")
    if not any(line.strip() for line in parts.get("## For the cut", [])):
        found.append("## For the cut is empty")
    found += carriage(raw)
    found += headings(brief)
    found += facts(parts.get("## Facts", []))[1]
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
