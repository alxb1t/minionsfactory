# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Hold a change's plan to the tree built from it, and print each place they differ.

Exit 0 clean · 1 a problem · 2 unreadable. Why: 0103-fewer-rounds design D4, D5.
"""

import argparse
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple

TIMEOUT_SECONDS = 600
SHOWN = 5
CHANGE = re.compile(r"[a-z0-9-]+")
SUBTASK = re.compile(r"- \[([ x])\] (\d+\.\d+\b.*)$")
PHASE = re.compile(r"- \[([ x])\] (\d+) — (.*)$", re.MULTILINE)
SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
MATCH = re.compile(r"^(.+?):(\d+):(.*)$", re.MULTILINE)
# A span after one of these words is the output a command must give, not a command.
OUTPUT_VERBS = {
    "prints",
    "reports",
    "outputs",
    "shows",
    "lists",
    "names",
    "holds",
    "contains",
    "returns",
    "exits",
    "reads",
    "says",
}
NOTHING = re.compile(r"\bprints nothing\b")
DEFINED = re.compile(r"-\s*(?:async\s+)?(?:def|class) (\w+)")
CONSTANT = re.compile(r"-(_?[A-Z][A-Z0-9_]*)\s*[=:]")
REMOVAL = re.compile(
    r"delet|remov|renam|retir|drop|replac|→|\*\*Reason\*\*|\*\*Migration\*\*",
    re.IGNORECASE,
)
TEST_DEF = r"^[[:space:]]*(async[[:space:]]+)?def test_[A-Za-z0-9_]*"
TEST_NAME = re.compile(r"\bdef (test_\w+)")
CORPUS = re.compile(r"\*\*CORPUS\*\* `([a-z0-9-]+)`")


class Stop(Exception):
    """End the check with exit 2; the message says what could not be read."""


class Unparsed(ValueError):
    """A `Verify:` that cannot be read; the message says why."""


class Task(NamedTuple):
    """One sub-task: its box, its id, such as `1.2`, and its lines joined."""

    ticked: bool
    name: str
    text: str


class Command(NamedTuple):
    """One backticked command of a `Verify:`, and what its words say it prints.

    `nothing` is set when the words after it say `prints nothing`; `count` is the
    number it prints alone.
    """

    text: str
    count: int | None
    nothing: bool = False


def _git(
    root: Path, *argv: str, ok: tuple[int, ...] = (0,)
) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run in `root`; a code outside `ok` stops."""
    try:
        done = subprocess.run(
            ["git", *argv], cwd=root, capture_output=True, text=True, errors="replace"
        )
    except FileNotFoundError:
        raise Stop("git is missing") from None
    if done.returncode not in ok:
        first = done.stderr.strip().partition("\n")[0]
        raise Stop(f"git {argv[0]} failed: {first}")
    return done


def subtasks(tasks: str) -> list[Task]:
    """Return each sub-task of a `tasks.md`, its wrapped lines joined to its first."""
    found: list[tuple[bool, list[str]]] = []
    wrapped = False
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            found.append((match[1] == "x", [match[2]]))
            wrapped = True
        elif wrapped and line[:1] in (" ", "\t") and line.strip():
            found[-1][1].append(line.strip())
        else:
            wrapped = False
    return [
        Task(ticked, " ".join(lines).split()[0], " ".join(lines))
        for ticked, lines in found
    ]


def commands(verify: str) -> list[Command]:
    """Return the commands of a `Verify:`'s text, each with the count it must print.

    A span is output when the words before it end in an output verb, or in a bare
    `and` or `or` after output. e.g. "`grep -c x a` prints `2`" → [("grep -c x a", 2)]
    """
    if "`" in SPAN.sub("", verify):
        raise Unparsed("a backtick opens no span")
    found: list[Command] = []
    end, output = 0, False
    for match in SPAN.finditer(verify):
        before = verify[end : match.start()]
        if found and not output and NOTHING.search(before):
            found[-1] = found[-1]._replace(nothing=True)
        words = before.split()
        output = (bool(words) and words[-1] in OUTPUT_VERBS) or (
            output and before.strip() in ("and", "or")
        )
        text = match[2]
        if len(match[1]) > 1 and text.startswith(" ") and text.endswith(" "):
            text = text[1:-1]
        if not output:
            found.append(Command(text, None))
        elif words[-1:] in (["prints"], ["reports"]) and text.isdigit() and found:
            found[-1] = found[-1]._replace(count=int(text))
        end = match.end()
    if found and not output and NOTHING.search(verify[end:]):
        found[-1] = found[-1]._replace(nothing=True)
    return found


def tokens(command: str) -> list[str]:
    """Return a command's shell words, each run of operator characters its own word."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError as error:
        raise Unparsed(f"{error}: `{command}`") from None


def verify_of(text: str) -> str | None:
    """Return the text after a sub-task's `Verify:`, one a span holds not counted."""
    masked = SPAN.sub(lambda span: " " * len(span[0]), text)
    at = masked.find("Verify:")
    return None if at < 0 else text[at + len("Verify:") :]


def rerun(name: str, command: Command, root: Path) -> list[str]:
    """Return the lines a command that fails prints, none when it passes.

    A command passes on exit 0 printing what its `Verify:` says: nothing, not even a
    blank line, the number alone, or anything when it says neither. A `grep` or
    `git grep` also passes on exit 1 printing nothing when its `Verify:` says it
    prints nothing or `0`, or printing `0` alone when it says `0`. Why:
    0103-fewer-rounds design D4.
    """
    argv = tokens(command.text)
    search = argv[:1] == ["grep"] or argv[:2] == ["git", "grep"]
    wanted = (
        "" if command.nothing else None if command.count is None else str(command.count)
    )
    try:
        done = subprocess.run(
            argv,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
        code, stdout = done.returncode, done.stdout
    except subprocess.TimeoutExpired:
        return [f"plan: {name} — `{command.text}` timed out"]
    except OSError as error:
        code, stdout = 127, str(error.strerror)
    output = stdout.splitlines()
    # Nothing is no byte at all, blank lines included; a count is read stripped.
    printed = stdout if command.nothing else stdout.strip()
    if code == 0 and wanted in (None, printed):
        return []
    if code == 1 and search and wanted in ("", "0") and printed in ("", wanted):
        return []
    shown = [f"  | {line}" for line in output[:SHOWN]]
    result = "printed other than its Verify: says" if code == 0 else f"exited {code}"
    return [f"plan: {name} — `{command.text}` {result}", *shown]


def phases(tasks: str) -> tuple[set[int], set[int]]:
    """Return the ticked phases of `## Progress`, and those a person does."""
    ticked: set[int] = set()
    human: set[int] = set()
    for match in PHASE.finditer(tasks):
        if match[1] == "x":
            ticked.add(int(match[2]))
        if "**HUMAN" in match[3]:
            human.add(int(match[2]))
    return ticked, human


def check_verifies(tasks: list[Task], human: set[int], root: Path) -> list[str]:
    """Return a line for each ticked `Verify:` command that fails run again.

    Not run: a `**HALT CHECK**` sub-task, a sub-task of a `**HUMAN` phase, and a
    command naming `plan_check.py`, so a `Verify:` that runs this check ends.
    """
    problems: list[str] = []
    for task in tasks:
        skipped = "**HALT CHECK**" in task.text or int(task.name.split(".")[0]) in human
        if not task.ticked or skipped or (verify := verify_of(task.text)) is None:
            continue
        try:
            for command in commands(verify):
                if "plan_check.py" not in command.text:
                    problems += rerun(task.name, command, root)
        except Unparsed as error:
            raise Stop(f"{task.name}: {error}") from None
    return problems


def check_boxes(tasks: list[Task], ticked: set[int]) -> list[str]:
    """Return a line for each sub-task left unticked under a ticked phase."""
    lines: list[str] = []
    for task in tasks:
        phase = int(task.name.split(".")[0])
        if not task.ticked and phase in ticked:
            lines.append(f"plan: {task.name} — unticked under the ticked phase {phase}")
    return lines


def tests_section(design: str) -> tuple[str, range]:
    """Return a design's `## Tests` section, and the numbers of its lines."""
    lines = design.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## Tests")), -1)
    if start < 0:
        return "", range(0)
    heading = (i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    end = next(heading, len(lines))
    return "\n".join(lines[start:end]), range(start + 1, end + 1)


def removed_names(root: Path, merge_base: str) -> list[str]:
    """Return each name the diff removes that no code outside `openspec/` holds.

    The names are the `def` and `class` lines and the unindented constants the diff
    removes from `*.py`, and the base name of each file it deletes.
    """
    diff = _git(root, "diff", "--unified=0", "--no-renames", merge_base, "--", "*.py")
    names = [
        match[1]
        for line in diff.stdout.splitlines()
        if (match := DEFINED.match(line) or CONSTANT.match(line))
    ]
    listed = ("diff", "--name-only", "--diff-filter=D", "--no-renames", merge_base)
    names += [Path(path).name for path in _git(root, *listed).stdout.splitlines()]
    held = ("grep", "--untracked", "-q", "-w", "-F")

    def gone(name: str) -> bool:
        argv = (*held, "-e", name, "--", ".", ":(exclude)openspec")
        return _git(root, *argv, ok=(0, 1)).returncode == 1

    return [name for name in dict.fromkeys(names) if gone(name)]


def check_names(
    root: Path, change: str, merge_base: str, tests: tuple[str, range]
) -> list[str]:
    """Return a line for each removed name the plan still names.

    A line saying it is removed is out, as are `tasks.md` and the design's
    `## Tests` section.
    """
    folder = f"openspec/changes/{change}"
    lines: list[str] = []
    for name in removed_names(root, merge_base):
        found = _git(
            root,
            *("grep", "--untracked", "-n", "-w", "-F", "-e", name, "--"),
            "openspec/specs",
            folder,
            ok=(0, 1),
        )
        for match in MATCH.finditer(found.stdout):
            path, number, text = match[1], int(match[2]), match[3]
            out = path == f"{folder}/tasks.md" or (
                path == f"{folder}/design.md" and number in tests[1]
            )
            if not out and not REMOVAL.search(text):
                lines.append(
                    f"plan: {path}:{number} names {name}, which the diff removes"
                )
    return lines


def check_tests(root: Path, merge_base: str, tests: tuple[str, range]) -> list[str]:
    """Return a line for each `def test_` name of the base gone from `tests/`.

    A name the design's `## Tests` section names as a word is planned, so not listed.
    """
    then = _git(
        root, "grep", "-h", "-E", "-e", TEST_DEF, merge_base, "--", "tests/", ok=(0, 1)
    )
    now = _git(
        root,
        "grep",
        "--untracked",
        "-h",
        "-E",
        "-e",
        TEST_DEF,
        "--",
        "tests/",
        ok=(0, 1),
    )
    gone = set(TEST_NAME.findall(then.stdout)) - set(TEST_NAME.findall(now.stdout))
    return [
        f"plan: {name} is gone since the base"
        for name in sorted(gone)
        if not re.search(rf"\b{name}\b", tests[0])
    ]


def check_corpus(tasks: list[Task], root: Path) -> list[str]:
    """Return a line for each `**CORPUS**` case that `scripts/corpus.toml` lacks.

    A sub-task, ticked or not, carries `**CORPUS** `<case>``; a missing file holds no
    case. Why: 0103-fewer-rounds design D5.
    """
    marked = [(t.name, case) for t in tasks for case in CORPUS.findall(t.text)]
    if not marked:
        return []
    try:
        with (root / "scripts" / "corpus.toml").open("rb") as handle:
            cases = tomllib.load(handle).get("case", [])
    except OSError:
        cases = []
    except tomllib.TOMLDecodeError as error:
        raise Stop(f"scripts/corpus.toml: {error}") from None
    names = {case.get("name") for case in cases if isinstance(case, dict)}
    return [
        f"plan: {name} — no case {case} in scripts/corpus.toml"
        for name, case in marked
        if case not in names
    ]


def check(change: str, base: str) -> list[str]:
    """Return every problem line of a change's plan against the working tree."""
    if not CHANGE.fullmatch(change) or base.startswith("-"):
        raise Stop("the change id or the base is not one this check reads")
    root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    folder = root / "openspec" / "changes" / change
    try:
        tasks = (folder / "tasks.md").read_text(errors="replace")
    except OSError as error:
        raise Stop(f"tasks.md: {error.strerror}") from None
    merge_base = _git(root, "merge-base", base, "HEAD").stdout.strip()
    design = folder / "design.md"
    tests = tests_section(
        design.read_text(errors="replace") if design.is_file() else ""
    )
    found, human = phases(tasks)
    parsed = subtasks(tasks)
    return [
        *check_verifies(parsed, human, root),
        *check_boxes(parsed, found),
        *check_names(root, change, merge_base, tests),
        *check_tests(root, merge_base, tests),
        *check_corpus(parsed, root),
    ]


def main(argv: list[str] | None = None) -> int:
    """Check a change's plan from inside the repository; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Hold a change's plan to the tree built from it."
    )
    parser.add_argument("--change", required=True, help="the change id")
    parser.add_argument("--base", required=True, help="the revision the branch left")
    args = parser.parse_args(argv)
    try:
        problems = check(args.change, args.base)
    except Stop as stop:
        print(f"plan: cannot check — {stop}")
        return 2
    print(*(problems or ["plan: clean"]), sep="\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
