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
FILE = re.compile(r"^diff --git a/\S+ b/(\S+)$", re.MULTILINE)
DELETED = re.compile(r"^diff --git a/\S+ b/(\S+)\ndeleted file mode", re.MULTILINE)
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
MATCH = re.compile(r"^(.+?):(\d+):(.*)$", re.MULTILINE)
DEFINED = re.compile(r"\s*(?:async\s+)?(?:def|class) (\w+)")
CONSTANT = re.compile(r"(_?[A-Z][A-Z0-9_]*)\s*[=:]")
TEST_DEF = re.compile(r"\s*(?:async\s+)?def (test_\w+)")
BOOT = re.compile(r"_main\(.*[\"']run[\"']")
CASE = re.compile(r"<testcase\b([^>]*)>")
NAME = re.compile(r'\bname="([^"]*)"')
SECONDS = re.compile(r'\btime="([\d.]+)"')
TESTS = re.compile(r"^## Tests\b.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)

type Change = tuple[str, str, int, str]


def _changes(patch: str) -> Iterator[Change]:
    """Yield `(sign, path, number, text)` for each added or removed line of a patch.

    e.g. "+x" on new line 7 of a.py → ("+", "a.py", 7, "x"); a removal is numbered old
    """
    path, old, new, hunk = "", 0, 0, False
    for line in patch.splitlines():
        if header := FILE.match(line):
            path, hunk = header[1], False
        elif start := HUNK.match(line):
            old, new, hunk = int(start[1]), int(start[2]), True
        elif hunk and line[:1] in {"+", "-", " "}:
            sign, text = line[0], line[1:]
            if sign != " ":
                yield sign, path, new if sign == "+" else old, text
            old += sign != "+"
            new += sign != "-"


def touched(patch: str) -> set[str]:
    """Return the path of each file the patch changes."""
    return set(FILE.findall(patch))


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
    gone += [Path(path).name for path in DELETED.findall(patch)]
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


def _seconds(report: str) -> dict[str, str]:
    """Return each test's seconds from a junit report, a parametrized test summed.

    e.g. name="t[1]" time="0.1" and name="t[2]" time="0.25" → {"t": "0.35 s"}
    """
    total: dict[str, float] = {}
    for case in CASE.findall(report):
        name, time = NAME.search(case), SECONDS.search(case)
        if name and time:
            key = name[1].partition("[")[0]
            total[key] = total.get(key, 0.0) + float(time[1])
    return {name: f"{seconds:.2f} s" for name, seconds in total.items()}


def _naming(name: str, section: str) -> str:
    """Return `named` when the section holds the name as a word, else `not named`."""
    return "named" if re.search(rf"\b{re.escape(name)}\b", section) else "not named"


def test_cost(patch: str, report: str, design: str) -> list[str]:
    """Return the cost lines of the tests a patch adds, slows, boots or removes.

    A test removed and added again is neither; a removal reads against `## Tests`.
    """
    changes = [change for change in _changes(patch) if change[1][-3:] == ".py"]
    plus = [(path, number, text) for sign, path, number, text in changes if sign == "+"]
    minus = [text for sign, _, _, text in changes if sign == "-"]
    made, lost = _tests(text for _, _, text in plus), _tests(minus)
    seconds, section = _seconds(report), TESTS.search(design)
    held = section[0] if section else ""
    return [
        *(
            f"added · {path}:{number} · {name} · {seconds.get(name, NO_TIME)}"
            for path, number, text in plus
            for name in _tests([text])
            if name not in lost
        ),
        *(
            f"slow · {path}:{number} · {text.strip()[:WIDTH]}"
            for path, number, text in plus
            if "pytest.mark.slow" in text
        ),
        *(
            f"boot · {path}:{number} · {text.strip()[:WIDTH]}"
            for path, number, text in plus
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
