# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a converge worker's bundle of the decisions and requirements a change cites.

    bundle.py <change-id> <bundle.md>
    bundle.py --decisions <file>…

Run from the repository root. The bundle holds each repo decision the change cites,
in full, an index of every decision, and each living requirement the delta modifies
or removes. Prints `bundle: <n> decisions cited · <m> requirements` and exits 0, or
`bundle: cannot bundle — <why>` and exits 2, writing nothing; a bundle path that is
a link is refused. `--decisions` prints the decisions the files cite and the index,
for the cut and the build, and writes nothing. Why: 0094-lighter-converge design D5;
0100-worker-diet design D7.
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

DECISIONS = Path("docs/decisions.md")
LINKED = re.compile(r"decisions\.md#d(\d+)\b")
HEADING = re.compile(r"### D(\d+) · ")
# `gate_check.py`'s `TITLED` and `PLANNED`, and its `_planned`'s title rule.
TITLED = re.compile(r"^### D(\d+) · (.+)$", re.MULTILINE)
PLANNED = re.compile(r"\bD(\d+) · ([^*`'\"|\n]+)")
TRIM = " .,;:"
SECTIONS = ("## MODIFIED Requirements", "## REMOVED Requirements")
REPLACES = (
    "In place of `docs/decisions.md` and the living specs: the decisions the change"
    " cites, in full, an index of all, and the living requirements its delta modifies"
    " or removes."
)


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _read(path: Path) -> str:
    """Return a file's text; one that cannot be read stops the run."""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        raise Stop(f"{path}: {why}") from error


def cited(plan: list[str], decisions: str) -> list[int]:
    """Return the ids of the repo decisions the plan cites, in file order.

    A `decisions.md#d<n>` link cites; so does `D<n> · <title>` when it and the
    heading's title, each trimmed, match where one starts with the other.
    e.g. "D2 · Two rules" and "### D2 · Two rules hold" → [2]; a bare "D3" → []
    """
    headed = {int(n): title.strip(TRIM) for n, title in TITLED.findall(decisions)}
    ids = {int(n) for text in plan for n in LINKED.findall(text)}
    for text in plan:
        for number, title in PLANNED.findall(text):
            heading, cut = headed.get(int(number)), title.strip(TRIM)
            if heading and cut and (heading.startswith(cut) or cut.startswith(heading)):
                ids.add(int(number))
    return [n for n in headed if n in ids]


def _blocks(decisions: str) -> dict[int, str]:
    """Return each decision's text, from its heading to the next `### ` or `## `."""
    blocks: dict[int, list[str]] = {}
    current: list[str] | None = None
    for line in decisions.splitlines():
        if found := HEADING.match(line):
            current = blocks.setdefault(int(found[1]), [])
        elif line.startswith(("### ", "## ")):
            current = None
        if current is not None:
            current.append(line)
    return {n: "\n".join(lines).strip() for n, lines in blocks.items()}


# `integrate.py`'s `_requirements` and `_requirement`.
def _requirements(spec: str, sections: tuple[str, ...]) -> list[str]:
    """Return the requirement titles under the named `## ` sections."""
    titles, inside = [], False
    for line in spec.splitlines():
        if line.startswith("## "):
            inside = line.strip() in sections
        elif inside and line.startswith("### Requirement: "):
            titles.append(line.removeprefix("### Requirement: ").strip())
    return titles


def _requirement(spec: str | None, title: str) -> str | None:
    """Return a requirement's block by title, or None when the spec lacks it."""
    block: list[str] | None = None
    for line in (spec or "").splitlines():
        if line.strip() == f"### Requirement: {title}":
            block = [line]
        elif block is not None:
            if line.startswith(("# ", "## ", "### Requirement: ")):
                break
            block.append(line)
    return "\n".join(block).strip() if block is not None else None


def _section(heading: str, parts: list[str]) -> str:
    """Return a bundle section: its heading and parts, or `None.` when it has none."""
    return f"\n## {heading}\n\n{'\n\n'.join(parts) or 'None.'}\n"


def decisions_text(plan: list[str], decisions: str | None) -> tuple[str, int]:
    """Return the cited decisions, in full, and the index; and how many are cited.

    `decisions` is the decisions file's text, None when the repo has none.
    """
    ids = cited(plan, decisions or "")
    blocks = _blocks(decisions or "")
    if decisions is None:
        index = "No docs/decisions.md."
    elif headings := TITLED.findall(decisions):
        index = "\n".join(f"- D{n} · {title}" for n, title in headings)
    else:
        index = decisions.strip()
    text = _section("Decisions the change cites", [blocks[n] for n in ids])
    text += _section("Every decision", [index] if index else [])
    return text, len(ids)


def _decisions() -> str | None:
    """Return the repo's decisions file's text, None when it has none."""
    return _read(DECISIONS) if DECISIONS.exists() else None


def bundle(change: str) -> tuple[str, int, int]:
    """Return the bundle's text, its cited decisions and its listed requirements."""
    folder = Path("openspec/changes") / change
    deltas = sorted((folder / "specs").glob("**/spec.md"))
    names = ("proposal.md", "design.md", "tasks.md")
    plan = [_read(folder / name) for name in names] + [_read(d) for d in deltas]
    cites, count = decisions_text(plan, _decisions())
    required = []
    for delta, text in zip(deltas, plan[len(names) :], strict=True):
        living = Path("openspec/specs") / delta.parent.relative_to(folder / "specs")
        spec = _read(living / "spec.md") if (living / "spec.md").exists() else None
        for title in _requirements(text, SECTIONS):
            missing = f"- `{title}` — not in the living spec"
            required.append(_requirement(spec, title) or missing)
    body = cites + _section("Requirements the delta modifies or removes", required)
    return f"# {change} — bundle\n\n{REPLACES}\n{body}", count, len(required)


def write(path: Path, text: str) -> None:
    """Replace `path` with `text` through a staged file; a link is refused.

    As `stamp.py`'s `write`: the staged `.tmp` is created anew with `O_NOFOLLOW`,
    then renamed over the bundle; a failure removes it and leaves the bundle as it
    stood.
    """
    if path.is_symlink():
        raise Stop(f"{path} is a link")
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(text)
        staged.replace(path)
    except OSError as error:
        with contextlib.suppress(OSError):
            staged.unlink()
        raise Stop(f"{path}: {error.strerror}") from error


def main(argv: list[str] | None = None) -> int:
    """Write a change's bundle, or print a plan's decisions; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write the decisions and requirements a change cites.",
        usage=(
            "bundle.py <change-id> <bundle.md>\n       bundle.py --decisions <file>…"
        ),
    )
    parser.add_argument("change", nargs="?", help="the change id")
    parser.add_argument("bundle", nargs="?", type=Path, help="the bundle to write")
    parser.add_argument("--decisions", nargs="+", type=Path, help="the files to read")
    args = parser.parse_args(argv)
    positional = (args.change, args.bundle)
    if positional.count(None) != (2 if args.decisions else 0):
        parser.error("give <change-id> <bundle.md>, or --decisions <file>… alone")
    try:
        if args.decisions:
            plan = [_read(path) for path in args.decisions]
            print(decisions_text(plan, _decisions())[0].strip())
            return 0
        text, decisions, requirements = bundle(args.change)
        write(args.bundle, text)
    except Stop as stop:
        print(f"bundle: cannot bundle — {stop}")
        return 2
    print(f"bundle: {decisions} decisions cited · {requirements} requirements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
