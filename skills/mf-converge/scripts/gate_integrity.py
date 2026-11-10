# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the gate-integrity lines of a frozen patch, one for each fact.

Why: 0110-gate-hardening design D5.
"""

import argparse
import itertools
import re
import sys
from pathlib import Path

WIDTH = 120
ALLOWLIST = ".betterleaks.toml"
PYPROJECT = "pyproject.toml"
OPEN = re.compile(r"^(?=diff --git )", re.MULTILINE)
MOVED = re.compile(r"^(?:rename|copy) to (.*)$")
PREFIX = re.compile(r"^[ab]/")
QUOTED = re.compile(rb'\\([0-7]{3}|[\\"abtnvfr])')
ESCAPES = {
    b"a": b"\a",
    b"b": b"\b",
    b"t": b"\t",
    b"n": b"\n",
    b"v": b"\v",
    b"f": b"\f",
    b"r": b"\r",
    b"\\": b"\\",
    b'"': b'"',
}
NULL = "/dev/null"
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
ADDED = {
    "noqa": re.compile(r"#\s*noqa"),
    "type-ignore": re.compile(r"#\s*(?:type|ty):\s*ignore"),
    "no-cover": re.compile(r"#\s*pragma:\s*no cover"),
    "skip": re.compile(r"pytest\.mark\.skip|pytest\.skip\("),
    "xfail": re.compile(r"pytest\.mark\.xfail|pytest\.xfail\("),
}
REMOVED = {
    "test-removed": re.compile(r"def test_"),
    "assert-removed": re.compile(r"assert\b"),
}
EXCEPT = re.compile(r"except\b.*:\s*(?:#.*)?$")
EXCEPT_PASS = re.compile(r"except\b.*:\s*pass\b\s*(?:#.*)?$")
PASS = re.compile(r"pass\b\s*(?:#.*)?$")
DEPENDENCY = re.compile(
    r'"[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9,._-]+\])?\s*[<>=!~][^"]*",?$'
)
VERSION = re.compile(r"version\s*=")

type Entry = tuple[str, int, str]


def _byte(match: re.Match[bytes]) -> bytes:
    """Return the byte one escape of a Git-quoted name stands for."""
    code = match[1]
    return bytes([int(code, 8) & 0xFF]) if code.isdigit() else ESCAPES[code]


def _unquote(name: str) -> str:
    """Return the text a name in Git's quotes spells; any other name as it is.

    e.g. a quoted `b/caf` with the octal bytes of `é` → "b/café"
    """
    if name[:1] != '"' or name[-1:] != '"':
        return name
    return QUOTED.sub(_byte, name[1:-1].encode()).decode(errors="replace")


def _path(name: str) -> str:
    """Return the path of a name in a header: unquoted, with no ending tab or `a/`."""
    return PREFIX.sub("", _unquote(name.removesuffix("\t")))


def _named(first: str, head: list[str]) -> str:
    """Return the path a file's `diff --git` line and header lines name, or "".

    e.g. the lines "diff --git a/p b/q" and "+++ b/a b/x.py" → "a b/x.py"
    """
    rest = first.removeprefix("diff --git ")
    size = (len(rest) - 1) // 2
    left, right = rest[:size], rest[size + 1 :]
    same = len(rest) % 2 == 1 and rest[size] == " " and _path(left) == _path(right)
    path = _path(right) if same else ""
    for line in head:
        if move := MOVED.match(line):
            path = _unquote(move[1])
        elif line[:4] in {"--- ", "+++ "} and line[4:] != NULL:
            path = _path(line[4:])
    return path


def _entries(body: list[str]) -> list[Entry]:
    """Return the hunk lines of a file as `(sign, number, text)`.

    e.g. "+x" on new line 7 → ("+", 7, "x"); a removed line is numbered on the old side
    """
    entries: list[Entry] = []
    old = new = 0
    for line in body:
        if start := HUNK.match(line):
            old, new = int(start[1]), int(start[2])
        elif line[:1] in {"+", "-", " ", ""}:
            sign, text = line[:1] or " ", line[1:].strip()
            entries.append((sign, old if sign == "-" else new, text))
            old += sign != "+"
            new += sign != "-"
    return entries


def _files(patch: str) -> list[tuple[str, list[Entry]]]:
    """Return each named file's path and hunk lines; a file with no path is skipped.

    Each `diff --git` line opens a file; its header lines name it until its first `@@`.
    """
    files: list[tuple[str, list[Entry]]] = []
    for block in OPEN.split(patch)[1:]:
        lines = block.removesuffix("\n").split("\n")  # LF alone: U+2028 is text
        cut = next((n for n, line in enumerate(lines) if HUNK.match(line)), len(lines))
        if path := _named(lines[0], lines[1:cut]):
            files.append((path, _entries(lines[cut:])))
    return files


def _unmoved(entries: list[Entry]) -> list[Entry]:
    """Return the entries with each line removed and added again made no change.

    The removal goes and the addition reads as context; each pairs with one other.
    """
    removed: dict[str, list[int]] = {}
    for index, (sign, _, text) in enumerate(entries):
        if sign == "-":
            removed.setdefault(text, []).append(index)
    gone: set[int] = set()
    kept: list[Entry] = []
    for sign, number, text in entries:
        moved = sign == "+" and bool(removed.get(text))
        if moved:
            gone.add(removed[text].pop(0))
        kept.append((" " if moved else sign, number, text))
    return [entry for index, entry in enumerate(kept) if index not in gone]


def _kinds(path: str, sign: str, text: str) -> list[str]:
    """Return the kinds of one changed line; a context line holds none."""
    if sign == "+":
        kinds = [kind for kind, pattern in ADDED.items() if pattern.search(text)]
        if path == ALLOWLIST and text and not text.startswith("#"):
            kinds.append("allowlist")
        if EXCEPT_PASS.match(text):
            kinds.append("swallow")
    elif sign == "-":
        kinds = [kind for kind, pattern in REMOVED.items() if pattern.match(text)]
    else:
        return []
    if (
        path == PYPROJECT
        and text
        and not DEPENDENCY.match(text)
        and not VERSION.match(text)
    ):
        kinds.append("pyproject")
    return kinds


def _swallows(entries: list[Entry]) -> list[Entry]:
    """Return each `except` line followed by a `pass`, one of the two added."""
    new = [entry for entry in entries if entry[0] != "-"]
    return [
        first
        for first, second in itertools.pairwise(new)
        if EXCEPT.match(first[2])
        and PASS.match(second[2])
        and second[1] == first[1] + 1
        and "+" in {first[0], second[0]}
    ]


def lines(patch: str) -> list[str]:
    """Return one `<kind> · <path>:<line> · <text>` line for each fact the patch holds.

    e.g. `x = f()  # noqa: A` added at a.py:12 → "noqa · a.py:12 · x = f()  # noqa: A"
    """
    found: list[str] = []
    for path, raw in _files(patch):
        entries = _unmoved(raw)
        facts = [
            (kind, number, text)
            for sign, number, text in entries
            for kind in _kinds(path, sign, text)
        ]
        facts += [("swallow", number, text) for _, number, text in _swallows(entries)]
        found += [
            f"{kind} · {path}:{number} · {text[:WIDTH]}" for kind, number, text in facts
        ]
    return found


def main(argv: list[str] | None = None) -> int:
    """Print the lines of a patch file, or `None.`; return 2 for one unreadable."""
    parser = argparse.ArgumentParser(
        description="Print the gate-integrity lines of a frozen patch."
    )
    parser.add_argument("patch", type=Path, help="the frozen diff patch")
    args = parser.parse_args(argv)
    try:
        text = args.patch.read_text()
    except (OSError, UnicodeDecodeError) as error:
        why = error.strerror if isinstance(error, OSError) else error.reason
        print(f"gate integrity: cannot read {args.patch} — {why}")
        return 2
    print(*(lines(text) or ["None."]), sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
