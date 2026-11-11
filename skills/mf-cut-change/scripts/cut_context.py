# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write the cut's context pack, or with --scaffold its artifacts, from a brief.

    cut_context.py <brief> <change-id> [--scaffold]
Exit 0 done · 1 a fact unplaced or a scaffold refused · 2 unreadable. Why: 0116 D4, D5.
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
# The runner is a constant so a test swaps it for the interpreter.
RUNNER = ("uv", "run", "--script")
BRIEF_CHECK = SCRIPTS.parents[1] / "mf-plan" / "scripts" / "brief_check.py"
FACTS = SCRIPTS / "facts.py"
BUNDLE = SCRIPTS.parents[1] / "mf-converge" / "scripts" / "bundle.py"
DEBT_MATCH = SCRIPTS.parents[1] / "mf-converge" / "scripts" / "debt_match.py"
SLICE_LINES = 80
TIMEOUT_SECONDS = 60
FOR_THE_CUT = "## For the cut"
ITEM_HEAD = re.compile(r"\d+\. (\S.*)")
REQUIREMENT = "### Requirement: "
FENCE = "~~~~"
CARD_ID = re.compile(r"- \*\*(\S+) — ")
CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")
PHASES = "## Phases"
DECISIONS = "## Decisions"
DEPENDENCIES = "## Dependencies"
NOT_IN_THIS = "## Not in this"
FRONT_KEYS = ("after", "beside", "debt")
PHASE_HEAD = re.compile(r"(\d+) {2,}(\S.*)")
RATED = re.compile(r"(.*) · (hard|moderate)\b")
DECISION_ID = re.compile(r"[QC]\d+")
FENCE_OPENERS = ("```", "~~~")
# The headings of each artifact in order, per the cut's rule A1.
SKELETONS = {
    "proposal.md": """\
---
bump: <minor | patch>
---

# <Title>

<one line>

Reading map: [design](design.md) <what it holds>, [tasks](tasks.md) <its phases>.

## Why

## What Changes

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

## Not in this change
""",
    "design.md": """\
# <Title> — design

<one line> Verdict: <ready to build, in the phases of [tasks](tasks.md)>.

## Context

## Goals / Non-Goals

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | <decision> | <reason> | <rejected> |

### D1

## Tests

## Dependencies

None.

## Risks / Trade-offs

## Migration Plan

## Verdict
""",
    "tasks.md": """\
# <Title> — tasks

<one line>

## Progress

- [ ] <N> — <Title> · <hard | moderate>

## <N> — <Title>

- [ ] <N.M> <the task, naming its files>.
  Verify: `<one plain command>` <what it prints or exits>.
""",
    "specs/<capability>/spec.md": """\
## ADDED Requirements

### Requirement: <title>

<the requirement, holding SHALL>

#### Scenario: <name>
- **WHEN** <a condition>
- **THEN** <the outcome>
- **AND** <a further outcome>

## MODIFIED Requirements

### Requirement: <an existing title, exactly>

<the whole requirement as it now reads>

## REMOVED Requirements

### Requirement: <an existing title, exactly>

**Reason:** <why it goes>
**Migration:** <what replaces it>
""",
}


class Stop(Exception):
    """End the run with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _run(argv: list[str], what: str) -> subprocess.CompletedProcess[str]:
    """Return a finished process; a missing program or a timeout stops with exit 2."""
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Stop(2, f"cut_context: cannot write — {what}: {error}") from None


def _load(path: Path) -> ModuleType:
    """Return the script at `path` as a module, run by `importlib`."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise Stop(2, f"cut_context: cannot write — no {path.name} beside this skill")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except OSError as error:
        raise Stop(2, f"cut_context: cannot write — {path}: {error.strerror}") from None
    return module


def _read(path: Path) -> str:
    """Return a file's text; one that cannot be read stops with exit 2."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Stop(2, f"cut_context: cannot write — {path}: {why}") from None


def brief_sections(brief: Path) -> dict[str, list[str]]:
    """Return the brief's sections, read by `brief_check.py --sections`.

    A brief it cannot read stops with exit 2, naming its first line.
    """
    done = _run([*RUNNER, str(BRIEF_CHECK), "--sections", str(brief)], "brief_check.py")
    if done.returncode:
        first = (done.stdout or done.stderr).strip().partition("\n")[0]
        raise Stop(2, f"cut_context: cannot write — {first}")
    try:
        found = json.loads(done.stdout)
    except ValueError:
        raise Stop(
            2, "cut_context: cannot write — brief_check.py printed no JSON"
        ) from None
    return found


def item_parts(sections: dict[str, list[str]], slug: str) -> list[str] | None:
    """Return the ` · ` parts of the `## For the cut` item `slug` heads, or None.

    e.g. "1. **`a-b`** · `minor`" → ["**`a-b`**", "`minor`"]
    """
    for line in sections.get(FOR_THE_CUT, []):
        if head := ITEM_HEAD.match(line):
            parts = [part.strip() for part in head[1].split(" · ")]
            if parts[0].strip("*` ") == slug:
                return parts
    return None


def cite_lines(cite: tuple[str, int, int]) -> list[str]:
    """Return a cite's numbered lines at HEAD, cut at `SLICE_LINES`, or one saying none.

    e.g. ("a.py", 2, 3) → ["2: def f():", "3:     return 1"]
    """
    path, start, end = cite
    done = _run(["git", "show", f"HEAD:{path}"], "git show")
    if done.returncode:
        return [f"{path} — missing at HEAD"]
    text = done.stdout.splitlines()
    if start > len(text):
        return [f"{path}:{start}-{end} — past the end of the file, at {len(text)}"]
    last = min(end, start + SLICE_LINES - 1, len(text))
    shown = [f"{number}: {text[number - 1]}" for number in range(start, last + 1)]
    if last < min(end, start + SLICE_LINES - 1):
        shown.append(
            f"… {path}:{last + 1}-{end} — past the end of the file, at {len(text)}"
        )
    elif last < end:
        shown.append(
            f"… cut at {SLICE_LINES} lines — {path}:{last + 1}-{end} not shown"
        )
    return shown


def _facts() -> ModuleType:
    """Return `facts.py` as a module that runs by this script's `RUNNER`."""
    facts = _load(FACTS)
    vars(facts)["RUNNER"] = RUNNER
    return facts


def facts_section(brief: Path) -> tuple[str, list[Any]]:
    """Return the `## The facts at HEAD` text and the brief's placed facts.

    `facts.py` runs by this script's `RUNNER`; its `Stop` ends the run with its code.
    """
    facts = _facts()
    try:
        placed = facts.place_all(facts.brief_facts(brief))
    except facts.Stop as stop:
        raise Stop(stop.code, str(stop)) from None
    parts = [
        "\n".join(
            [
                f"### {one.state} · {one.fact.text}",
                *(
                    line
                    for cite in one.cites
                    for line in (
                        "",
                        f"`{facts.where(cite)}`",
                        FENCE,
                        *cite_lines(tuple(cite)),
                        FENCE,
                    )
                ),
            ]
        )
        for one in placed
    ]
    return _section("The facts at HEAD", parts), placed


def decisions_section(brief: Path) -> str:
    """Return the `## The decisions` text: `bundle.py --decisions` on the brief.

    A run of it that fails stops with exit 2, naming its first line.
    """
    done = _run([*RUNNER, str(BUNDLE), "--decisions", str(brief)], "bundle.py")
    if done.returncode:
        first = (done.stdout or done.stderr).strip().partition("\n")[0]
        raise Stop(2, f"cut_context: cannot write — {first}")
    return _section("The decisions", [done.stdout.strip()])


def requirements_sections(brief: Path) -> tuple[str, str]:
    """Return the requirements the brief names, in full, and the index of every one.

    A title is named when the brief holds it, case apart; an index line is
    `<capability>:<line> · <title>`, e.g. "sdd:10 · The skills run the gate".
    """
    text = _read(brief).casefold()
    named: list[str] = []
    index: list[str] = []
    for spec in sorted(Path("openspec/specs").glob("*/spec.md")):
        block: list[str] | None = None
        for number, line in enumerate(_read(spec).splitlines(), 1):
            if block is not None and line.startswith(("# ", "## ", REQUIREMENT)):
                named.append("\n".join(block).strip())
                block = None
            if line.startswith(REQUIREMENT):
                title = line.removeprefix(REQUIREMENT).strip()
                index.append(f"{spec.parent.name}:{number} · {title}")
                block = [line] if title.casefold() in text else None
            elif block is not None:
                block.append(line)
        if block is not None:
            named.append("\n".join(block).strip())
    return (
        _section("The requirements the brief names", named),
        _section("Every requirement", ["\n".join(index)] if index else []),
    )


def run_dir() -> Path:
    """Return the run directory, `.minions/` beside the primary checkout.

    e.g. a common git dir `/w/main/.git` → `/w/main/.minions`
    """
    done = _run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], "git"
    )
    if done.returncode:
        first = done.stderr.strip().partition("\n")[0]
        raise Stop(2, f"cut_context: cannot write — git rev-parse failed: {first}")
    return Path(done.stdout.strip()).parent / ".minions"


def debt_section(item: list[str] | None, placed: list[Any]) -> str:
    """Return the `## Debt cards` text: cards on a cited path or listed by the item.

    The cards are the run directory's `debt.md`, read by `debt_match.py`.
    """
    path = run_dir() / "debt.md"
    if not path.exists():
        return _section("Debt cards", [])
    debt_match = _load(DEBT_MATCH)
    cited = {cite.path for one in placed for cite in one.cites}
    listed = set(_ids(item_flags(item or []).get("debt", "")))
    kept = [
        card.strip()
        for card in debt_match.cards(_read(path))
        if debt_match.matched(card, cited) or _card_id(card) in listed
    ]
    return _section("Debt cards", kept)


def item_flags(parts: list[str]) -> dict[str, str]:
    """Return each `key: value` part of an item, from its third part on.

    e.g. ["**`a`**", "`minor`", "after: none", "debt: [x]"] → {"after": "none", ...}
    """
    flags = (part.partition(":") for part in parts[2:])
    return {key.strip(): value.strip() for key, _, value in flags}


def _ids(value: str) -> list[str]:
    """Return the ids of a `[a, b]` list, a bare one or `none`.

    e.g. "[0113·S4, 0114·S1]" → ["0113·S4", "0114·S1"]
    """
    return [one for entry in value.split(",") if (one := entry.strip("[]` "))]


def _card_id(card: str) -> str:
    """Return the id a card's title opens with, or none.

    e.g. "- **0113·S4 — a title**" → "0113·S4"
    """
    found = CARD_ID.match(card)
    return found[1] if found else ""


def skeletons_section() -> str:
    """Return the `## The skeletons` text: each artifact's headings, in order."""
    note = (
        "Each artifact keeps these headings in order;"
        " the design has a `## Migration Plan` only when the change migrates."
    )
    return _section(
        "The skeletons",
        [
            note,
            *(
                f"### {name}\n\n{FENCE}markdown\n{text}{FENCE}"
                for name, text in SKELETONS.items()
            ),
        ],
    )


def _section(heading: str, parts: list[str]) -> str:
    """Return a pack section: its heading and parts, or `None.` when it has none."""
    return f"## {heading}\n\n{'\n\n'.join(parts) or 'None.'}"


def _slug(change: str) -> str:
    """Return a change id without its number; a malformed id stops with exit 2.

    e.g. "0116-cut-diet" → "cut-diet"
    """
    if not CHANGE_ID.fullmatch(change):
        raise Stop(2, f"cut_context: cannot write — `{change}` is no change id")
    return change.partition("-")[2]


def _mkdir(folder: Path) -> None:
    """Create `folder` and its parents; an unwritable path stops with exit 2."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Stop(
            2, f"cut_context: cannot write — {folder}: {error.strerror}"
        ) from None


def _write(path: Path, text: str) -> None:
    """Write `text` to `path`; a link or an unwritable path stops with exit 2."""
    if path.is_symlink():
        raise Stop(2, f"cut_context: cannot write — {path} is a link")
    try:
        path.write_text(text)
    except OSError as error:
        raise Stop(2, f"cut_context: cannot write — {path}: {error.strerror}") from None


def pack(brief: Path, change: str) -> int:
    """Write the pack and the notes of `change`, print one line; return the code.

    The code is 0 when every fact is placed and 1 when one is not.
    """
    slug = _slug(change)
    text = _read(brief)
    sections = brief_sections(brief)
    item = item_parts(sections, slug)
    facts_text, placed = facts_section(brief)
    named, index = requirements_sections(brief)
    parts = [
        _section("The brief", [text.strip()]),
        facts_text,
        decisions_section(brief),
        named,
        index,
        debt_section(item, placed),
        skeletons_section(),
    ]
    folder = run_dir() / "changes" / change
    _mkdir(folder)
    _write(folder / "context.md", "\n\n".join(parts) + "\n")
    facts = _facts()
    lines = [
        f"{one.fact.text} — {one.state} · {', '.join(map(facts.where, one.cites))}"
        for one in placed
    ]
    try:
        facts.write_notes(folder / "cut-notes.md", lines, fresh=True)
    except facts.Stop as stop:
        raise Stop(stop.code, str(stop)) from None
    unplaced = sum(one.state == "unplaced" for one in placed)
    print(
        f"cut_context: pack — {folder / 'context.md'} · {len(placed)} facts,"
        f" {unplaced} unplaced"
    )
    return 1 if unplaced else 0


def title_of(slug: str) -> str:
    """Return the slug's words, the first capitalised.

    e.g. "cut-diet" → "Cut diet"
    """
    words = slug.replace("-", " ")
    return words[:1].upper() + words[1:]


def _cells(line: str) -> list[str]:
    """Return a table row's cells, split on `|` outside code spans and escapes.

    e.g. "| a | `b | c` |" → ["a", "`b | c`"]
    """
    cells: list[str] = []
    current, code, previous = "", False, ""
    for char in line.strip():
        code ^= char == "`"
        if char == "|" and not code and previous != "\\":
            cells.append(current.strip())
            current = ""
        else:
            current += char
        previous = char
    return cells[1:]


def _rows(lines: list[str]) -> list[list[str]]:
    """Return the cells of each table row among `lines`."""
    return [_cells(line) for line in lines if line.lstrip().startswith("|")]


def proposal_text(sections: dict[str, list[str]], slug: str) -> str:
    """Return the proposal scaffold: frontmatter, title, one line, what is out.

    A slug with no `## For the cut` item stops with exit 2.
    """
    item = item_parts(sections, slug)
    if item is None or len(item) < 2:
        raise Stop(2, f"cut_context: cannot write — no `## For the cut` item `{slug}`")
    flags = item_flags(item)
    front = [f"bump: {item[1].strip('` ')}"]
    for key in FRONT_KEYS:
        ids = [one for one in _ids(flags.get(key, "")) if one != "none"]
        if ids:
            front.append(f"{key}: [{', '.join(ids)}]")
    under = next(
        (lines for head, lines in sections.items() if head.startswith("# ")), []
    )
    one = next((line.strip().strip("*") for line in under if line.strip()), "")
    out = [line.rstrip() for line in sections.get(NOT_IN_THIS, []) if line.strip()]
    return "\n".join(
        ["---", *front, "---", "", f"# {title_of(slug)}", "", one, ""]
        + ["## Not in this change", "", *(out or ["None."])]
        + [""]
    )


def design_text(sections: dict[str, list[str]], slug: str) -> str:
    """Return the design scaffold: the decisions table and the dependencies.

    A row is a `Q` or `C` row of the brief's `## Decisions`, a blank cell a `—`,
    and a row whose decision is `—` is left out.
    """
    kept = [
        cells
        for cells in _rows(sections.get(DECISIONS, []))
        if len(cells) >= 3
        and DECISION_ID.fullmatch(cells[0].strip("*` "))
        and cells[1] != "—"
    ]
    table = [
        f"| [D{n}](#d{n}) | {cells[1] or '—'} | {cells[2] or '—'} | — |"
        for n, cells in enumerate(kept, 1)
    ]
    mine = [
        cells[1:4]
        for cells in _rows(sections.get(DEPENDENCIES, []))
        if len(cells) >= 4 and cells[0].strip("*` ") == slug
    ]
    needs = (
        ["| package | constraint | why |", "|---|---|---|"]
        + [f"| {' | '.join(row)} |" for row in mine]
        if mine
        else ["None."]
    )
    return "\n".join(
        [f"# {title_of(slug)} — design", "", DECISIONS, ""]
        + ["| id | decision | because | rejected |", "|---|---|---|---|", *table]
        + ["", DEPENDENCIES, "", *needs, ""]
    )


def phases(sections: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    """Return `(number, title, rating)` of each phase of the brief's `## Phases`.

    A phase starts at `<n>  <text>` and runs over the lines indented below it; one
    with no ` · hard` or ` · moderate` stops with exit 1.
    """
    body = [
        line
        for line in sections.get(PHASES, [])
        if line.strip() and not line.lstrip().startswith(FENCE_OPENERS)
    ]
    margin = min((len(line) - len(line.lstrip()) for line in body), default=0)
    found: list[list[str]] = []
    for line in body:
        indent = len(line) - len(line.lstrip())
        head = PHASE_HEAD.fullmatch(line.strip()) if indent == margin else None
        if head:
            found.append([head[1], head[2]])
        elif found and indent > margin:
            found[-1].append(line.strip())
    done: list[tuple[str, str, str]] = []
    for number, *words in found:
        rated = RATED.match(" ".join(" ".join(words).split()))
        if rated is None:
            raise Stop(1, f"cut_context: scaffold — phase {number} has no rating")
        done.append((number, rated[1], rated[2]))
    return done


def tasks_text(sections: dict[str, list[str]]) -> str:
    """Return the tasks scaffold after its title: `## Progress` and a heading a phase.

    A brief with no phase, or a phase with no rating, stops with exit 1.
    """
    found = phases(sections)
    if not found:
        raise Stop(1, "cut_context: scaffold — the brief's ## Phases holds no phase")
    return "\n".join(
        ["## Progress", ""]
        + [f"- [ ] {number} — {title} · {rating}" for number, title, rating in found]
        + [
            line
            for number, title, _ in found
            for line in ("", f"## {number} — {title}")
        ]
        + [""]
    )


def scaffold(brief: Path, change: str) -> int:
    """Write the proposal, design and tasks scaffold of `change`; return 0.

    One that exists, a malformed id or a brief that cannot be read stops the run
    before any file is written.
    """
    slug = _slug(change)
    sections = brief_sections(brief)
    texts = {
        "proposal.md": proposal_text(sections, slug),
        "design.md": design_text(sections, slug),
        "tasks.md": f"# {title_of(slug)} — tasks\n\n{tasks_text(sections)}",
    }
    folder = Path("openspec") / "changes" / change
    for name in texts:
        if (folder / name).exists() or (folder / name).is_symlink():
            raise Stop(
                1, f"cut_context: scaffold — {folder / name} exists, none written"
            )
    _mkdir(folder)
    for name, text in texts.items():
        _write(folder / name, text)
    print(f"cut_context: scaffold — {folder} · {', '.join(texts)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Write a change's context pack, or its scaffold, from the repository root."""
    parser = argparse.ArgumentParser(
        description="Write the cut's context pack and notes from a brief."
    )
    parser.add_argument("brief", type=Path, help="the brief")
    parser.add_argument("change", help="the change id")
    parser.add_argument(
        "--scaffold", action="store_true", help="write the artifacts' scaffold instead"
    )
    args = parser.parse_args(argv)
    try:
        if args.scaffold:
            return scaffold(args.brief, args.change)
        return pack(args.brief, args.change)
    except Stop as stop:
        print(stop)
        return stop.code


if __name__ == "__main__":
    sys.exit(main())
