# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Build the sections of a freeze's `evidence.md` from a patch, a report and a design.

Why: 0110-gate-hardening design D6.
"""

import re
from collections.abc import Iterable, Iterator
from pathlib import Path

LIMIT = 40
WIDTH = 120
NO_TIME = "no time in the report"
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
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@ ?(.*)$")
MATCH = re.compile(r"^(.+?):(\d+):(.*)$", re.MULTILINE)
DEFINED = re.compile(r"\s*(?:async\s+)?(?:def|class) (\w+)")
CLASS_DEF = re.compile(r"\s*class (\w+)")
CONSTANT = re.compile(r"(_?[A-Z][A-Z0-9_]*)\s*[=:]")
TEST_DEF = re.compile(r"\s*(?:async\s+)?def (test_\w+)")
BOOT = re.compile(r"_main\(.*[\"']run[\"']")
CASE = re.compile(r"<testcase\b([^>]*)>")
NAME = re.compile(r'\bname="([^"]*)"')
CLASS = re.compile(r'\bclassname="([^"]*)"')
SECONDS = re.compile(r'\btime="([\d.]+)"')
TESTS = re.compile(r"^## Tests\b.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)

type Line = tuple[str, int, str]
type Hunk = tuple[str, list[Line]]
type File = tuple[str, bool, list[Hunk]]
type Change = tuple[str, str, int, str]


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


def _named(first: str, head: list[str]) -> tuple[str, bool]:
    """Return the path a file's header names, "" for none, and whether it is deleted.

    e.g. the lines "diff --git a/p b/q" and "+++ b/a b/x.py" → ("a b/x.py", False)
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
    deleted = f"+++ {NULL}" in head or any(
        line.startswith("deleted file mode") for line in head
    )
    return path, deleted


def _hunks(body: list[str]) -> list[Hunk]:
    """Return each hunk's header text and its lines as `(sign, number, text)`.

    e.g. "+x" on new line 7 → ("+", 7, "x"); a removed line is numbered on the old side
    """
    hunks: list[Hunk] = []
    old = new = 0
    for line in body:
        if start := HUNK.match(line):
            old, new = int(start[1]), int(start[2])
            hunks.append((start[3], []))
        elif line[:1] in {"+", "-", " "}:
            sign = line[0]
            hunks[-1][1].append((sign, old if sign == "-" else new, line[1:]))
            old += sign != "+"
            new += sign != "-"
    return hunks


def _files(patch: str) -> list[File]:
    """Return each named file's path, whether it is deleted and its hunks.

    Each `diff --git` line opens a file; its header lines name it until its first `@@`.
    """
    files: list[File] = []
    for block in OPEN.split(patch)[1:]:
        lines = block.splitlines()
        cut = next((n for n, line in enumerate(lines) if HUNK.match(line)), len(lines))
        path, deleted = _named(lines[0], lines[1:cut])
        if path:
            files.append((path, deleted, _hunks(lines[cut:])))
    return files


def _changes(patch: str) -> Iterator[Change]:
    """Yield `(sign, path, number, text)` for each added or removed line of a patch.

    e.g. "+x" on new line 7 of a.py → ("+", "a.py", 7, "x"); a removal is numbered old
    """
    for path, _, hunks in _files(patch):
        for _, lines in hunks:
            for sign, number, text in lines:
                if sign != " ":
                    yield sign, path, number, text


def touched(patch: str) -> set[str]:
    """Return the path of each file the patch changes."""
    return {path for path, _, _ in _files(patch)}


def _names(text: str) -> list[str]:
    """Return the name a line of code defines: a function, a class or a constant."""
    found = DEFINED.match(text) or CONSTANT.match(text)
    return [found[1]] if found else []


def candidates(patch: str) -> list[str]:
    """Return each name the patch removes from Python code and never adds back.

    A deleted file counts by its base name. e.g. "-def old():" → ["old"]
    """
    code = [
        (sign, text) for sign, path, _, text in _changes(patch) if path[-3:] == ".py"
    ]
    added = {name for sign, text in code if sign == "+" for name in _names(text)}
    gone = [
        name
        for sign, text in code
        if sign == "-"
        for name in _names(text)
        if name not in added
    ]
    gone += [Path(path).name for path, deleted, _ in _files(patch) if deleted]
    return list(dict.fromkeys(gone))


def stale(names: list[str], found: str, changed: set[str]) -> list[str]:
    """Return a line for each mention of a name in a file the patch leaves alone.

    e.g. "old", "docs/g.md:4:call old" → ["old · docs/g.md:4: call old"]
    """
    mentions = [match for match in MATCH.finditer(found) if match[1] not in changed]
    return [
        f"{name} · {match[1]}:{match[2]}: {match[3].strip()[:WIDTH]}"
        for name in names
        for match in mentions
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", match[3])
    ]


def _tests(texts: Iterable[str]) -> list[str]:
    """Return the name of each test the lines define."""
    return [match[1] for text in texts if (match := TEST_DEF.match(text))]


def _seconds(report: str) -> dict[tuple[str, str], float]:
    """Return each test's seconds by its class and name, a parametrized test summed.

    e.g. m's t[1] 0.1 s and t[2] 0.25 s → {("m", "t"): 0.35}
    """
    total: dict[tuple[str, str], float] = {}
    for case in CASE.findall(report):
        where, name, time = CLASS.search(case), NAME.search(case), SECONDS.search(case)
        if name and time:
            key = (where[1] if where else "", name[1].partition("[")[0])
            total[key] = total.get(key, 0.0) + float(time[1])
    return total


def _indent(text: str) -> int:
    """Return the count of whitespace characters a line starts with."""
    return len(text) - len(text.lstrip())


def _owner(lines: list[Line], index: int, header: str) -> str | None:
    """Return the class of the test line at `index`: "" for none, None when unshown.

    e.g. "    def test_a" under the line "class TestX:" → "TestX"
    """
    indent = _indent(lines[index][2])
    if not indent:
        return ""
    above = [line for sign, _, line in lines[:index] if sign != "-" and line.strip()]
    nearest = next(
        (line for line in [*reversed(above), header] if _indent(line) < indent), ""
    )
    return found[1] if (found := CLASS_DEF.match(nearest)) else None


def _fits(where: str, module: str, owner: str | None) -> bool:
    """Return whether the report's `where` is the identity of a test of class `owner`.

    e.g. "tests.test_a.TestX" fits module "tests.test_a" with owner "TestX", or None
    """
    inside = where.startswith(f"{module}.")
    if owner is None:
        return inside or where == module
    return where == module if owner == "" else inside and where.endswith(f".{owner}")


def _time(
    seconds: dict[tuple[str, str], float], path: str, name: str, owner: str | None
) -> str:
    """Return the seconds of the test `name` of class `owner` in `path`, or `NO_TIME`.

    e.g. owner "TestX" in tests/test_a.py → the time of `tests.test_a.TestX`'s test
    """
    module = path.removesuffix(".py").replace("/", ".")
    found = {
        where: time
        for (where, test), time in seconds.items()
        if test == name and _fits(where, module, owner)
    }
    if len(found) > 1:
        return " · ".join(
            f"{time:.2f} s in {where.rpartition('.')[2]}"
            for where, time in found.items()
        )
    return f"{sum(found.values()):.2f} s" if found else NO_TIME


def _naming(name: str, section: str) -> str:
    """Return `named` when the section holds the name as a word, else `not named`."""
    return "named" if re.search(rf"\b{re.escape(name)}\b", section) else "not named"


def test_cost(patch: str, report: str, design: str) -> list[str]:
    """Return the cost lines of the tests a patch adds, slows, boots or removes.

    A test removed and added again is neither; a removal reads against `## Tests`.
    """
    plus: list[tuple[str, int, str, str | None]] = []
    minus: list[str] = []
    code = [file for file in _files(patch) if file[0][-3:] == ".py"]
    for path, _, hunks in code:
        for header, lines in hunks:
            for index, (sign, number, text) in enumerate(lines):
                if sign == "+":
                    owner = _owner(lines, index, header) if _tests([text]) else None
                    plus.append((path, number, text, owner))
                elif sign == "-":
                    minus.append(text)
    made, lost = _tests(text for _, _, text, _ in plus), _tests(minus)
    seconds, section = _seconds(report), TESTS.search(design)
    held = section[0] if section else ""
    return [
        *(
            f"added · {path}:{number} · {name} · {_time(seconds, path, name, owner)}"
            for path, number, text, owner in plus
            for name in _tests([text])
            if name not in lost
        ),
        *(
            f"slow · {path}:{number} · {text.strip()[:WIDTH]}"
            for path, number, text, _ in plus
            if "pytest.mark.slow" in text
        ),
        *(
            f"boot · {path}:{number} · {text.strip()[:WIDTH]}"
            for path, number, text, _ in plus
            if BOOT.search(text)
        ),
        *(
            f"removed · {name} · {_naming(name, held)} in ## Tests"
            for name in dict.fromkeys(lost)
            if name not in made
        ),
    ]


def render(change: str, base: str, head: str, sections: dict[str, list[str]]) -> str:
    """Return `evidence.md`: a title and each section's lines, capped at `LIMIT`.

    A section with nothing reads `None.`; its lines past `LIMIT` read `… <n> more`.
    """
    parts = [
        f"# Evidence — {change} · {base[:7]}..{head[:7]}",
        "",
        "Facts a tool found, not verdicts. Start from them; judge them.",
    ]
    for heading, found in sections.items():
        more = found[LIMIT:]
        shown = [*found[:LIMIT], *([f"… {len(more)} more"] if more else [])]
        parts += ["", f"## {heading}", *(shown or ["None."])]
    return "\n".join(parts) + "\n"
