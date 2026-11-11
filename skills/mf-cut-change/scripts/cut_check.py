# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Decide the self-check rows a script can, and list the rest for the cut to judge.

    cut_check.py <id> [--bump <bump>]
Exit 0 ready · 1 a row failed · 2 unrunnable. Why: 0106-cut-scripts design D6.
"""

import argparse
import functools
import itertools
import re
import runpy
import subprocess
import sys
from collections.abc import Callable
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, NamedTuple

TIMEOUT_SECONDS = 600
HERE = Path(__file__).resolve().parent
CUT_PRE = HERE / "cut_pre.py"
VERIFY_CHECK = HERE / "verify_check.py"
CONVERGE = HERE.parents[1] / "mf-converge" / "scripts"
GATE_CHECK = CONVERGE / "gate_check.py"
PLAN_CHECK = CONVERGE / "plan_check.py"
CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")
PROGRESS = re.compile(r"^- \[[ x]\] (\d+) — (.+)$")
PHASE = re.compile(r"(\d+) — ")
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
DEFINED = re.compile(r"^### ([A-Z]\d+)\b")
SKIP_SPECS = re.compile(r"^skip_specs:\s*true\s*$", re.MULTILINE)
SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
SENTENCE = re.compile(r"[.!?](?=\s+[A-Z`*\[(]|\s*$)")
COUNTED = re.compile(
    r"(?<![\w.])(?:\d+|(?i:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))"
    r"\s+(?:[a-z-]+\s+)?[a-z]+s\b"
)
RITUAL = re.compile(
    r"(?:\*\*[A-Z ]+\*\*\s*(?:`[^`]*`\s*)?)?(?:"
    r"run\s+`?(?:make\s+(?:gate|check)\b|mf-[a-z]+)"
    r"|(?:add|write|append)\b[^`.]{0,40}\bCHANGELOG\b"
    r"|(?:tick|commit|tag|archive|release)\b)",
    re.IGNORECASE,
)
HALT_CHECK = "**HALT CHECK**"
OPERATORS = set("();<>|&")
REGEX_META = set("^$.*+?()[]{}|")
PATH_SUFFIXES = (".py", ".md", ".toml", ".yaml", ".yml", ".mk")
RUN_PATHS = ("openspec/changes/", ".minions/")
CITED_LINES = re.compile(r":\d+(?:-\d+)?$")
CITE = re.compile(r"[\w./-]+\.\w+:\d+(?:-\d+)?")
DESIGN_LINK = re.compile(r"design\.md#([a-z]\d+)")
TABLE_ID = re.compile(r"^\|\s*\[?([A-Z]\d+)\b")
STEP = re.compile(r"\bStep (\d+(?:\.\d+)?)")
CONSTANT = re.compile(r"(?=.*[A-Z])[A-Z0-9_]{3,}")
NEW_FILE = re.compile(r"\b(?:add|new|create)\b", re.IGNORECASE)
CHANGES_TEST = re.compile(r"\b(?:adds?|removes?|merges?|renames?)\b", re.IGNORECASE)
PROPOSAL_HEADINGS = [
    "Why",
    "What Changes",
    "Capabilities",
    "Impact",
    "Not in this change",
]
DESIGN_HEADINGS = [
    "Context",
    "Goals / Non-Goals",
    "Decisions",
    "Tests",
    "Dependencies",
    "Risks / Trade-offs",
    "Verdict",
]
ROWS = [
    "I2",
    "I3",
    "I4",
    "I11",
    "I12",
    "I13",
    "I14",
    "I17",
    "I18",
    "I19",
    "A1",
    "A2",
    "P9",
    "P13",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "K1",
    "K2",
    "K3",
    "K4",
    "K5",
    "K6",
    "corpus",
]
JUDGED = {
    "I5": "each `Verify:` runs on this machine, or is a fact on disk",
    "I6": "each task has one reading: files named, no `or`, things named not counted",
    "I7": "each existing file the change turns red is named in a task",
    "I8": "each phase ends on a green `make check`, the last on a green gate",
    "I9": "a delta for each behaviour change; each MODIFIED title is a requirement",
    "I10": "each file and symbol `design.md` names exists, or an `after:` adds it",
    "I15": "`**HALT CHECK**` on each sub-task whose failure means the plan is wrong",
    "I16": "each deleted or merged test is in `## Tests`, with the test that keeps it",
    "P12": "no counts in prose: read each candidate",
    "P13": "no paragraph past 3 sentences: read each candidate",
}


class Stop(Exception):
    """End the check with exit 2; the message says what could not run."""


class Failure(NamedTuple):
    """A failed row, why, and the output lines of the check that failed it."""

    row: str
    why: str
    detail: list[str]


class Change(NamedTuple):
    """The texts of a change directory, empty when a file is missing."""

    id: str
    folder: Path
    proposal: str
    design: str
    tasks: str


def _spawn(argv: list[str], name: str) -> tuple[int, list[str]]:
    """Return a program's exit code and its output lines; one that cannot run stops."""
    try:
        done = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        gone = isinstance(error, FileNotFoundError)
        raise Stop(f"{name} is not on PATH" if gone else f"{name}: {error}") from None
    return done.returncode, done.stdout.splitlines()


def _script(path: Path, *args: str) -> tuple[int, list[str]]:
    """Run a sibling script under this interpreter; an exit above 1 stops."""
    code, lines = _spawn([sys.executable, str(path), *args], path.name)
    if code > 1:
        raise Stop(next((line for line in lines if line.strip()), path.name))
    return code, lines


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Return each numbered line outside a code fence and a leading frontmatter."""
    kept: list[tuple[int, str]] = []
    fenced = False
    front = text.startswith("---\n")
    for number, line in enumerate(text.splitlines(), 1):
        if front:
            front = number == 1 or line.strip() != "---"
        elif line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            kept.append((number, line))
    return kept


def headings(text: str) -> list[str]:
    """Return the title of each `## ` heading outside a fence."""
    return [line[3:].strip() for _, line in prose_lines(text) if line.startswith("## ")]


def section(text: str, title: str) -> list[str] | None:
    """Return the stripped, non-blank lines under `## <title>`, or None without it."""
    found: list[str] | None = None
    for _, line in prose_lines(text):
        if line.startswith("## "):
            if found is not None:
                break
            found = [] if line[3:].strip() == title else None
        elif found is not None and line.strip():
            found.append(line.strip())
    return found


def frontmatter(text: str) -> dict[str, str]:
    """Return the `key: value` pairs of a leading `---` block."""
    lines = text.splitlines()
    if lines[:1] != ["---"]:
        return {}
    pairs: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, colon, value = line.partition(":")
        if colon:
            pairs[key.strip()] = value.strip()
    return pairs


def masked(line: str) -> str:
    """Return a line with its code spans and links blanked."""
    return LINK.sub(" ", SPAN.sub(" ", line))


def blocks(tasks: str) -> list[tuple[str, list[str]]]:
    """Return each sub-task's name and its lines outside a fence, wrapped ones too."""
    found: list[tuple[str, list[str]]] = []
    wrapped = fenced = False
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            found.append((match[1].split()[0], [line]))
            wrapped, fenced = True, False
        elif wrapped and line[:1] in (" ", "\t") and line.strip():
            if line.strip().startswith("```"):
                fenced = not fenced
            elif not fenced:
                found[-1][1].append(line)
        else:
            wrapped = False
    return found


def in_order(wanted: list[str], found: list[str]) -> str | None:
    """Return the first of `wanted` that `found` lacks in that order, or None."""
    at = 0
    for title in wanted:
        if title not in found[at:]:
            return title
        at = found.index(title, at) + 1
    return None


def row_i2(change: Change) -> str | None:
    """Return why the artifacts or the delta are not in place, or None."""
    for name in ("proposal.md", "design.md", "tasks.md"):
        if not (change.folder / name).is_file():
            return f"{name} is missing"
    specs = change.folder / "specs"
    delta = sorted(specs.glob("*/spec.md"))
    meta = change.folder / ".openspec.yaml"
    skip = meta.is_file() and SKIP_SPECS.search(meta.read_text())
    if not skip:
        return None if delta else "no specs/*/spec.md, and no `skip_specs: true`"
    if delta:
        return "`skip_specs: true` beside a spec file"
    return (
        None if (specs / ".gitkeep").is_file() else "no specs/.gitkeep for `skip_specs`"
    )


def row_i4(change: Change, plan: dict[str, Any]) -> str | None:
    """Return what is out of shape in `tasks.md`'s progress list and sub-tasks."""
    problems: list[str] = []
    lines = change.tasks.splitlines()
    first = next((n for n, line in enumerate(lines) if line.startswith("## ")), None)
    if not (
        first is not None
        and lines[0].startswith("# ")
        and lines[first].strip() == "## Progress"
        and any(line.strip() for line in lines[1:first])
    ):
        problems.append("`## Progress` does not follow the title and its line")
    sections = {
        int(m[1])
        for _, line in prose_lines(change.tasks)
        if line.startswith("## ") and (m := PHASE.match(line[3:]))
    }
    listed = section(change.tasks, "Progress") or []
    phases = [m for line in listed if (m := PROGRESS.match(line))]
    if not phases:
        problems.append("`## Progress` lists no phase")
    for phase in phases:
        suffixed = phase[2].endswith((" · moderate", " · hard"))
        if not suffixed and "**HUMAN" not in phase[2]:
            problems.append(f"phase {phase[1]} lacks ` · moderate` or ` · hard`")
        if int(phase[1]) not in sections:
            problems.append(f"phase {phase[1]} has no `## {phase[1]} — …` section")
    ids = [int(phase[1]) for phase in phases]
    problems.extend(
        f"section {number} is not listed in `## Progress`"
        for number in sorted(sections - set(ids))
    )
    problems.extend(
        f"phase {number} is listed twice in `## Progress`"
        for number in sorted({n for n in ids if ids.count(n) > 1})
    )
    for task in plan["subtasks"](change.tasks):
        if plan["verify_of"](task.text) is None:
            problems.append(f"{task.name} has no Verify:")
        if int(task.name.split(".")[0]) not in ids:
            problems.append(f"sub-task {task.name} is not of a listed phase")
    current: int | None = None
    for _, line in prose_lines(change.tasks):
        if line.startswith("## "):
            current = int(m[1]) if (m := PHASE.match(line[3:])) else None
        elif (
            (m := SUBTASK.match(line))
            and (name := m[1].split()[0])
            and int(name.split(".")[0]) in ids
            and int(name.split(".")[0]) != current
        ):
            problems.append(f"sub-task {name} sits outside its `## … —` section")
    return " · ".join(problems) or None


def row_i11(change: Change) -> str | None:
    """Return why `## Dependencies` is neither `None.` nor the package table."""
    lines = section(change.design, "Dependencies")
    if lines is None:
        return "design.md has no `## Dependencies`"
    header = [cell.strip().lower() for cell in "".join(lines[:1]).strip("|").split("|")]
    if lines == ["None."] or (header == ["package", "constraint", "why"] and lines[2:]):
        return None
    return "`## Dependencies` is not `None.` or a table of package, constraint, why"


def row_i12(change: Change, plan: dict[str, Any]) -> str | None:
    """Return the sub-tasks that open with another station's step, a person's apart."""
    human = plan["phases"](change.tasks)[1]
    found = [
        task.name
        for task in plan["subtasks"](change.tasks)
        if int(task.name.split(".")[0]) not in human
        and RITUAL.match(task.text[len(task.name) :].strip())
    ]
    return (
        f"{', '.join(found)} open with a step another station owns" if found else None
    )


def row_i13(change: Change, bump: str | None) -> str | None:
    """Return why the proposal's `bump:` is not `minor` or `patch`, or not the given."""
    found = frontmatter(change.proposal).get("bump")
    if found not in ("minor", "patch"):
        return "proposal.md opens no frontmatter with `bump: minor` or `bump: patch`"
    if bump not in (None, found):
        return f"`bump: {found}` is not the bump given, {bump}"
    return None


def row_i14(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each phase a person does that holds no sub-task with a `Verify:`."""
    human = plan["phases"](change.tasks)[1]
    checked = {
        int(task.name.split(".")[0])
        for task in plan["subtasks"](change.tasks)
        if plan["verify_of"](task.text) is not None
    }
    bare = ", ".join(str(phase) for phase in sorted(human - checked))
    return f"phase {bare} holds no sub-task with Verify:" if bare else None


def row_i17(change: Change, pre: dict[str, Any]) -> str | None:
    """Return why an `after:` id is not an open version of a lower number, or None."""
    value = frontmatter(change.proposal).get("after", "")
    ids = [named.strip() for named in value.strip("[]").split(",") if named.strip()]
    if not ids:
        return None
    return pre["after_problem"](change.id, ids, pre["default_branch"]())


def row_a1(change: Change) -> str | None:
    """Return the headings each file lacks, in the order `A1` gives."""
    named = headings(change.tasks)
    lacking = [
        f"{file} lacks `## {title}` in order"
        for file, wanted, found in (
            ("proposal.md", PROPOSAL_HEADINGS, headings(change.proposal)),
            ("design.md", DESIGN_HEADINGS, headings(change.design)),
        )
        if (title := in_order(wanted, found))
    ]
    if named[:1] != ["Progress"] or not all(PHASE.match(h) for h in named[1:]):
        lacking.append("tasks.md headings are not `## Progress`, then `## N — Title`")
    return " · ".join(lacking) or None


def row_a2(change: Change) -> str | None:
    """Return why the proposal does not end with `## Not in this change`."""
    if headings(change.proposal)[-1:] == ["Not in this change"]:
        return None
    return "proposal.md does not end with `## Not in this change`"


def row_p9(change: Change) -> str | None:
    """Return each id of the design cited outside a link in the tasks or proposal."""
    defined = {
        m[1] for _, line in prose_lines(change.design) if (m := DEFINED.match(line))
    }
    found = [
        f"{name}:{number} cites {cited}"
        for name, text in (("tasks.md", change.tasks), ("proposal.md", change.proposal))
        for number, line in prose_lines(text)
        for cited in re.findall(r"\b[A-Z]\d+\b", masked(line))
        if cited in defined
    ]
    return " · ".join(found) + " outside a link" if found else None


def row_p13(change: Change) -> str | None:
    """Return each sub-task of more than 3 lines, wrapped ones counted."""
    long = [
        f"{name} ({len(lines)} lines)"
        for name, lines in blocks(change.tasks)
        if len(lines) > 3
    ]
    return f"{', '.join(long)} hold more than 3 lines" if long else None


@functools.cache
def _plan() -> dict[str, Any]:
    """Return the names of `plan_check.py`, loaded once."""
    return runpy.run_path(str(PLAN_CHECK))


def _git(*argv: str) -> tuple[int, list[str]]:
    """Return a git command's exit code and output lines; an exit above 1 stops."""
    code, lines = _spawn(["git", *argv], "git")
    if code > 1:
        raise Stop(f"git {argv[0]} failed: {' '.join(lines)}")
    return code, lines


def _words(command: str) -> list[str]:
    """Return a command's shell words, none when it does not parse."""
    try:
        return _plan()["tokens"](command)
    except ValueError:
        return []


def _literal(pattern: str, fixed: bool) -> str:
    """Return the text a search pattern matches, empty when it is a regex.

    e.g. ("a-b", False) → "a-b"; ("^a", False) → ""
    """
    if fixed:
        return pattern
    text = pattern.replace("\\", "")
    return "" if REGEX_META & set(text) else text


def _before_operator(command: str) -> str:
    """Return a command up to its first shell operator outside a quote.

    e.g. `git grep -nF "|" a.py | wc` → `git grep -nF "|" a.py `
    """
    quote, escaped = "", False
    for at, char in enumerate(command):
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char in OPERATORS:
            return command[:at]
    return command


def search_parts(command: str) -> tuple[list[str], list[str]]:
    """Return the literal needles and file operands of a `grep` or `git grep`.

    A command that is no search gives none. e.g. `git grep -n -e 'a b' HEAD -- x.py`
    → (["a b"], ["x.py"])
    """
    words = _words(_before_operator(command))
    if words[:1] == ["grep"]:
        rest = words[1:]
    elif words[:2] == ["git", "grep"]:
        rest = words[2:]
    else:
        return [], []
    patterns: list[str] = []
    operands: list[str] = []
    fixed = takes = ended = False
    for word in rest:
        if takes:
            patterns.append(word)
            takes = False
        elif ended or not word.startswith("-"):
            operands.append(word)
        elif word == "--":
            ended = True
        elif word.startswith("--"):
            fixed = fixed or word == "--fixed-strings"
        else:
            fixed = fixed or "F" in word
            takes = word.endswith("e")
    if not patterns:
        patterns, operands = operands[:1], operands[1:]
    needles = [needle for pattern in patterns if (needle := _literal(pattern, fixed))]
    return needles, [operand for operand in operands if operand != "HEAD"]


def _commands(text: str, plan: dict[str, Any]) -> list[str]:
    """Return the commands of a sub-task's `Verify:`, none when it parses no span."""
    try:
        return [c.text for c in plan["commands"](plan["verify_of"](text) or "")]
    except ValueError:
        return []


def _body(text: str, plan: dict[str, Any]) -> str:
    """Return a sub-task's text before its `Verify:`."""
    verify = plan["verify_of"](text)
    if verify is None:
        return text
    return text[: len(text) - len(verify) - len("Verify:")]


def _searches(text: str, plan: dict[str, Any]) -> list[tuple[list[str], list[str]]]:
    """Return the needles and files of each search in a sub-task text's `Verify:`."""
    return [search_parts(command) for command in _commands(text, plan)]


def _phase(name: str) -> str:
    """Return the phase number of a sub-task's name, as `1` for `1.2`."""
    return name.split(".", maxsplit=1)[0]


def _at_head(path: str, tree: set[str]) -> bool:
    """Return whether a file, a directory or a glob matches a path of `HEAD`'s tree."""
    prefix = path.rstrip("/") + "/"
    return path in tree or any(
        p.startswith(prefix) or fnmatchcase(p, path) for p in tree
    )


def _same(path: str, other: str) -> bool:
    """Return whether two paths are equal, or one is a directory holding the other."""
    return (
        path == other
        or (other.endswith("/") and path.startswith(other))
        or (path.endswith("/") and other.startswith(path))
    )


def decision_texts(design: str) -> dict[str, str]:
    """Return the text of each `### D<n>` section of a design, by its lowercase id."""
    found: dict[str, list[str]] = {}
    current, fenced = "", False
    for line in design.splitlines():
        fenced ^= line.lstrip().startswith("```")
        heading = None if fenced else DEFINED.match(line)
        if not fenced and line.startswith("## "):
            current = ""
        elif heading:
            current = heading[1].lower()
            found[current] = []
        elif current:
            found[current].append(line)
    return {key: "\n".join(lines) for key, lines in found.items()}


def path_spans(text: str) -> list[str]:
    """Return each code span of a text that names a path, the run's own apart.

    e.g. "Edit `a/b.py:3` and `make gate`" → ["a/b.py"]
    """
    spans = [CITED_LINES.sub("", match[2]) for match in SPAN.finditer(text)]
    return [
        span
        for span in spans
        if " " not in span
        and ("/" in span or span.endswith(PATH_SUFFIXES) or span == "Makefile")
        and not span.startswith(RUN_PATHS)
    ]


def row_v1(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each search whose needle an earlier sub-task naming its file quotes."""
    tasks = plan["subtasks"](change.tasks)
    found: list[str] = []
    for at, task in enumerate(tasks):
        if HALT_CHECK in task.text:
            continue
        for needles, files in _searches(task.text, plan):
            for needle in needles:
                earlier = next(
                    (
                        other
                        for other in tasks[:at]
                        if needle in other.text and any(f in other.text for f in files)
                    ),
                    None,
                )
                if earlier is not None:
                    found.append(f"{task.name}: `{needle}` is quoted in {earlier.name}")
    return " · ".join(found) or None


class _KExpression:
    """Evaluate one `-k` expression against one test name, by recursive descent."""

    def __init__(self, tokens: list[str], name: str) -> None:
        """Hold the tokens, the lowercased name and the cursor."""
        self.tokens = tokens
        self.name = name.lower()
        self.at = 0
        self.positive = False

    def accept(self, word: str) -> bool:
        """Return whether the next token is `word`, and step over it when it is."""
        found = self.at < len(self.tokens) and self.tokens[self.at] == word
        self.at += found
        return found

    def either(self, depth: int) -> bool:
        """Evaluate `a or b`; `depth` counts the `not`s around it."""
        value = self.both(depth)
        while self.accept("or"):
            value = self.both(depth) or value
        return value

    def both(self, depth: int) -> bool:
        """Evaluate `a and b`."""
        value = self.operand(depth)
        while self.accept("and"):
            value = self.operand(depth) and value
        return value

    def operand(self, depth: int) -> bool:
        """Evaluate `not x`, `( … )` or an identifier; anything else is an error."""
        if self.accept("not"):
            return not self.operand(depth + 1)
        if self.accept("("):
            value = self.either(depth)
            if not self.accept(")"):
                raise ValueError("no closing parenthesis")
            return value
        word = self.tokens[self.at] if self.at < len(self.tokens) else ""
        if word in ("", "and", "or", ")"):
            raise ValueError("no identifier")
        self.at += 1
        held = word.lower() in self.name
        self.positive |= held and depth == 0
        return held


def selects(expression: str, name: str) -> bool:
    """Return whether a `-k` expression picks the test `name` by a positive match.

    The expression is true for the name and an identifier outside every `not` holds
    in it; one that does not parse picks nothing. e.g. "not a and b", "test_b" → True
    """
    tokens = re.findall(r"[()]|[\w:+\-.\[\]\\/]+", expression)
    if "".join(tokens) != "".join(expression.split()):
        return False
    parsed = _KExpression(tokens, name)
    try:
        value = parsed.either(0)
    except (ValueError, RecursionError):
        return False
    return value and parsed.positive and parsed.at == len(tokens)


def _selected(text: str, plan: dict[str, Any]) -> list[str]:
    """Return the `-k` expression of each `pytest` command of a sub-task text."""
    found: list[str] = []
    for command in _commands(text, plan):
        words = _words(command)
        if "pytest" in words:
            found += [e for flag, e in itertools.pairwise(words) if flag == "-k"]
    return found


def row_v2(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each `-k` expression that selects a test a later sub-task changes."""
    tasks = plan["subtasks"](change.tasks)
    found = [
        f"{task.name}: `-k {expression}` selects a test that {later.name} changes"
        for at, task in enumerate(tasks)
        for expression in _selected(task.text, plan)
        for later in tasks[at + 1 :]
        if CHANGES_TEST.search(later.text)
        and any(selects(expression, n) for n in re.findall(r"test_\w+", later.text))
    ]
    return " · ".join(found) or None


def row_v3(change: Change, plan: dict[str, Any], tree: set[str]) -> str | None:
    """Return each `git grep` of a file `HEAD` lacks that its own phase first names."""
    tasks = plan["subtasks"](change.tasks)
    found: list[str] = []
    for task in tasks:
        for command in _commands(task.text, plan):
            if command.split()[:2] != ["git", "grep"]:
                continue
            for file in search_parts(command)[1]:
                first = next((other for other in tasks if file in other.text), task)
                if not _at_head(file, tree) and _phase(first.name) == _phase(task.name):
                    found.append(f"{task.name}: `{file}` is no file of HEAD yet")
    return " · ".join(found) or None


def row_v4(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each needle a sub-task and the decisions it links never name."""
    sections = decision_texts(change.design)
    found: list[str] = []
    for task in plan["subtasks"](change.tasks):
        if HALT_CHECK in task.text:
            continue
        linked = [sections.get(cited, "") for cited in DESIGN_LINK.findall(task.text)]
        named = "\n".join([_body(task.text, plan), *linked])
        found += [
            f"{task.name}: `{needle}` is in neither the task nor a decision it links"
            for needles, _ in _searches(task.text, plan)
            for needle in needles
            if needle not in named
        ]
    return " · ".join(found) or None


def _test_path(word: str) -> bool:
    """Return whether a command word names a test: a `.py` file, a node id or a path.

    e.g. "tests/test_a.py" → True; "tests/" → False; "-m" → False
    """
    if word.startswith("-"):
        return False
    named = "/" in word and bool(word.rpartition("/")[2])
    return word.endswith(".py") or "::" in word or named


VALUE_OPTIONS = frozenset(
    [
        "-c",
        "-k",
        "-m",
        "-o",
        "-p",
        "-W",
        "--basetemp",
        "--cache-dir",
        "--confcutdir",
        "--deselect",
        "--html",
        "--ignore",
        "--ignore-glob",
        "--junit-xml",
        "--junitxml",
        "--log-file",
        "--override-ini",
        "--report-log",
        "--rootdir",
    ]
)


def _operands(words: list[str]) -> list[str]:
    """Return the words that are no option and no value of an option taking one.

    e.g. ["pytest", "--junitxml", "out/r.xml", "t.py"] → ["pytest", "t.py"]
    """
    kept: list[str] = []
    skip = False
    for word in words:
        if skip:
            skip = False
        elif word in VALUE_OPTIONS:
            skip = True
        else:
            kept.append(word)
    return kept


def row_v5(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each `pytest` command of a `Verify:` that names no test file."""
    found = [
        f"{task.name}: {command} names no test file"
        for task in plan["subtasks"](change.tasks)
        for command in _commands(task.text, plan)
        if plan["is_pytest"](words := _words(command))
        and not any(_test_path(word) for word in _operands(words))
    ]
    return " · ".join(found) or None


def _record(
    heading: str,
    spans: list[str],
    change: Change,
    plan: dict[str, Any],
    applies: Callable[[str], bool],
) -> str | None:
    """Return the paths of a record section no sub-task holds, and those it lacks."""
    tasks = plan["subtasks"](change.tasks)
    found = [
        f"`{path}` of `## {heading}` is held by no sub-task"
        for path in spans
        if not any(path in task.text for task in tasks)
    ]
    found += [
        f"{name}: `{path}` is absent from `## {heading}`"
        for name, lines in blocks(change.tasks)
        for path in path_spans(lines[0])
        if applies(path) and not any(_same(path, kept) for kept in spans)
    ]
    return " · ".join(found) or None


def row_k1(change: Change, plan: dict[str, Any], tree: set[str]) -> str | None:
    """Return the paths `## Impact` and the sub-tasks disagree on."""
    spans = path_spans(" ".join(section(change.proposal, "Impact") or []))
    return _record("Impact", spans, change, plan, lambda path: _at_head(path, tree))


def row_k2(change: Change, plan: dict[str, Any]) -> str | None:
    """Return the `tests/` paths `## Tests` and the sub-tasks disagree on."""
    spans = path_spans(" ".join(section(change.design, "Tests") or []))
    kept = [span for span in spans if span.startswith("tests/")]
    return _record("Tests", kept, change, plan, lambda path: path.startswith("tests/"))


def row_k3(change: Change) -> str | None:
    """Return why the `## Decisions` table and the `### D` headings differ."""
    table = [
        m[1]
        for line in section(change.design, "Decisions") or []
        if (m := TABLE_ID.match(line))
    ]
    headed = [
        m[1] for _, line in prose_lines(change.design) if (m := DEFINED.match(line))
    ]
    if table == headed:
        return None
    return f"the table holds {', '.join(table)} and the headings {', '.join(headed)}"


def row_k4(change: Change) -> str | None:
    """Return each `design.md#d<n>` link that no `### D<n>` heading answers."""
    defined = set(decision_texts(change.design))
    cited = {
        f"{name} links design.md#{link}"
        for name, text in (("tasks.md", change.tasks), ("proposal.md", change.proposal))
        for link in DESIGN_LINK.findall(text)
        if link not in defined
    }
    return " · ".join(sorted(cited)) or None


def row_k5(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each step and constant a sub-task's one file lacks at HEAD."""
    found: list[str] = []
    for task in plan["subtasks"](change.tasks):
        paths = set(path_spans(task.text))
        if len(paths) != 1 or NEW_FILE.search(task.text):
            continue
        (path,) = paths
        for step in STEP.findall(task.text):
            pattern = rf"^## Step {re.escape(step)}( |$)"
            if _git("grep", "-q", "-E", pattern, "HEAD", "--", path)[0]:
                found.append(f"{task.name}: {path} has no `## Step {step}` at HEAD")
        constants = {m[2] for m in SPAN.finditer(task.text) if CONSTANT.fullmatch(m[2])}
        found += [
            f"{task.name}: {path} has no `{constant}` at HEAD"
            for constant in sorted(constants - {"HEAD"})
            if _git("grep", "-q", "-w", "-F", "-e", constant, "HEAD", "--", path)[0]
        ]
    return " · ".join(found) or None


def row_k6(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each `path:line` cite that stands in two sub-tasks."""
    cited: dict[str, list[str]] = {}
    for task in plan["subtasks"](change.tasks):
        for cite in sorted(set(CITE.findall(task.text))):
            cited.setdefault(cite, []).append(task.name)
    found = [f"`{c}` stands in {', '.join(n)}" for c, n in cited.items() if len(n) > 1]
    return " · ".join(found) or None


def counted_lines(change: Change) -> list[str]:
    """Return each line naming a number before a plural noun, as `path:line: text`."""
    texts = (
        ("proposal.md", change.proposal),
        ("design.md", change.design),
        ("tasks.md", change.tasks),
    )
    return [
        f"{name}:{number}: {line.strip()}"
        for name, text in texts
        for number, line in prose_lines(text)
        if COUNTED.search(masked(line))
    ]


def long_paragraphs(change: Change) -> list[str]:
    """Return each paragraph past 3 sentences, as `path:line: its first words`."""
    found: list[str] = []
    for name, text in (("proposal.md", change.proposal), ("design.md", change.design)):
        start, words = 0, []
        for number, line in [*prose_lines(text), (0, "")]:
            if line.strip() and line[:1] not in " \t#|-*>" and not line[:1].isdigit():
                start = start or number
                words.append(line.strip())
                continue
            if len(SENTENCE.findall(masked(" ".join(words)))) > 3:
                found.append(f"{name}:{start}: {words[0][:60]}")
            start, words = 0, []
    return found


def folded(change: Change) -> tuple[list[Failure], list[str]]:
    """Run `openspec validate`, the gate-edit check and the search script.

    A failure keeps the output lines under its row; each match of the search script is
    returned as a line of its own.
    """
    tasks = str(change.folder / "tasks.md")
    failures: list[Failure] = []
    code, lines = _spawn(["openspec", "validate", change.id, "--strict"], "openspec")
    if code:
        why = f"`openspec validate {change.id} --strict` failed"
        failures.append(Failure("I3", why, lines))
    if not (change.folder / "tasks.md").is_file():
        return failures, []
    code, lines = _script(GATE_CHECK, "--tasks", tasks)
    if code:
        failures.append(Failure("I18", lines[0], lines[1:]))
    code, lines = _script(VERIFY_CHECK, tasks)
    summary = [line for line in lines if line.startswith("verify:")]
    detail = [line for line in lines if "I19 —" in line]
    matches = [line for line in lines if line not in summary + detail]
    if code:
        failures.append(Failure("I19", summary[0], detail))
    return failures, matches


def check(
    identifier: str, bump: str | None
) -> tuple[list[Failure], list[str], list[str]]:
    """Return the failed rows, the search matches and the judgment lines of a change."""
    folder = Path("openspec/changes") / identifier
    if not folder.is_dir():
        raise Stop(f"no {folder}/")
    proposal, design, tasks = (
        path.read_text(errors="replace") if path.is_file() else ""
        for path in (folder / name for name in ("proposal.md", "design.md", "tasks.md"))
    )
    change = Change(identifier, folder, proposal, design, tasks)
    pre = runpy.run_path(str(CUT_PRE))
    plan = _plan()
    tree = set(_git("ls-tree", "-r", "--name-only", "HEAD")[1])
    if why := row_v3(change, plan, tree):
        return [Failure("V3", why, [])], [], []
    failures, matches = folded(change)
    try:
        corpus = plan["check_corpus"](plan["subtasks"](tasks), Path.cwd())
        rows = [
            ("I2", row_i2(change)),
            ("I4", row_i4(change, plan)),
            ("I11", row_i11(change)),
            ("I12", row_i12(change, plan)),
            ("I13", row_i13(change, bump)),
            ("I14", row_i14(change, plan)),
            ("I17", row_i17(change, pre)),
            ("A1", row_a1(change)),
            ("A2", row_a2(change)),
            ("P9", row_p9(change)),
            ("P13", row_p13(change)),
            ("V1", row_v1(change, plan)),
            ("V2", row_v2(change, plan)),
            ("V4", row_v4(change, plan)),
            ("V5", row_v5(change, plan)),
            ("K1", row_k1(change, plan, tree)),
            ("K2", row_k2(change, plan)),
            ("K3", row_k3(change)),
            ("K4", row_k4(change)),
            ("K5", row_k5(change, plan)),
            ("K6", row_k6(change, plan)),
            *[("corpus", line.removeprefix("plan: ")) for line in corpus],
        ]
    except (pre["Stop"], plan["Stop"]) as error:
        raise Stop(str(error)) from None
    failures += [Failure(row, why, []) for row, why in rows if why]
    judge = [f"{row} — {what}" for row, what in JUDGED.items()]
    judge += [f"P12 — {line}" for line in counted_lines(change)]
    judge += [f"P13 — {line}" for line in long_paragraphs(change)]
    failures.sort(key=lambda failure: ROWS.index(failure.row))
    return failures, matches, judge


def main(argv: list[str] | None = None) -> int:
    """Check a change from the repository root; print its rows, return the exit code."""
    parser = argparse.ArgumentParser(
        description="Check a cut change's mechanical rows."
    )
    parser.add_argument("change", help="the change id, <digits>-<slug>")
    parser.add_argument("--bump", help="the bump the cut was given")
    args = parser.parse_args(argv)
    try:
        if not CHANGE_ID.fullmatch(args.change):
            raise Stop(f"`{args.change}` is not <digits>-<slug>")
        failures, matches, judge = check(args.change, args.bump)
    except Stop as stop:
        print(f"cut_check: cannot check — {stop}")
        return 2
    out: list[str] = []
    for failure in failures:
        out.append(f"cut_check: halt — {failure.row} — {failure.why}")
        out += [f"  {line.strip()}" for line in failure.detail]
    out += [f"cut_check: match — {line}" for line in matches]
    out += [f"cut_check: judge — {line}" for line in judge]
    failed = {failure.row for failure in failures}
    if failed:
        out.append(f"cut_check: halt — {len(failed)} rows failed")
    else:
        out.append(f"cut_check: ready — {len(ROWS)} rows met, {len(JUDGED)} to judge")
    print("\n".join(out))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
