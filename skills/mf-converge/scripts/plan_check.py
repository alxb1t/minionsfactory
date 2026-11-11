# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Hold a change's plan to the tree built from it, and print each place they differ.

Why: 0103-fewer-rounds design D4, D5;
the skip, 0108-converge-script.
"""

import argparse
import contextlib
import functools
import hashlib
import json
import os
import re
import runpy
import shlex
import signal
import subprocess
import sys
import threading
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Any, NamedTuple

TIMEOUT_SECONDS = 600
DRAIN_SECONDS = 5
CPUS = os.cpu_count() or 1
RUNNING: set[subprocess.Popen[str]] = set()
PROCESSES = re.compile(r"-n(\d+|auto|logical)?|--numprocesses(=.*)?")
REVISION = re.compile(r"[0-9a-f]{7,40}")
TEST_MODULE = re.compile(r"test_.*\.py|.*_test\.py")
EXCLUDES = re.compile(r"collect_ignore|pytest_ignore_collect")
QUIET_OPTIONS = frozenset({"-q", "-qq", "-v", "-vv", "-x", "-s"})
COLLECTED = re.compile(
    r"^\S+::\S|^\S+: [1-9]\d*$|(?<![/\d])[1-9]\d* tests? collected", re.M
)
COLLECT_ONLY = " --collect-only -q"
SHOWN = 5
CHANGE = re.compile(r"[a-z0-9-]+")
ID = re.compile(r"\d+\.\d+")
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
REQUIREMENT = "### Requirement:"
REMOVED = "## REMOVED Requirements"
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


class Result(NamedTuple):
    """One command's finish: its exit code, its output, and whether it timed out."""

    code: int
    output: str
    timed_out: bool = False


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
            ["git", *argv],
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
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


def _kill(process: subprocess.Popen[str]) -> None:
    """End a command's process group; one already gone is no error."""
    with contextlib.suppress(OSError):
        os.killpg(process.pid, signal.SIGKILL)


def run(command: str, root: Path) -> Result:
    """Return a command's finish, run in `root` as argv with no shell.

    It runs in a session of its own, so a timeout ends the command's whole group.
    Why: 0114-faster-plan-check design D4, D5.
    """
    held = os.environ.get("PYTEST_ADDOPTS", "")
    env = {**os.environ, "PYTEST_ADDOPTS": f"{held} -p no:cacheprovider".strip()}
    try:
        process = subprocess.Popen(
            tokens(command),
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            start_new_session=True,
        )
    except OSError as error:
        return Result(127, str(error.strerror))
    RUNNING.add(process)
    try:
        output, _ = process.communicate(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        _kill(process)
        try:
            process.communicate(timeout=DRAIN_SECONDS)
        except subprocess.TimeoutExpired:
            if process.stdout:
                process.stdout.close()
            process.wait()
        return Result(-1, "", True)
    finally:
        RUNNING.discard(process)
    return Result(process.returncode, output)


def weight(argv: list[str]) -> int:
    """Return the slots a command takes: every one for a pytest with `-n`, else one."""
    if is_pytest(argv) and any(PROCESSES.fullmatch(word) for word in argv):
        return CPUS
    return 1


def schedule(work: list[str], root: Path) -> dict[str, Result]:
    """Return each command's result by its text, the commands run side by side.

    A command starts when its `weight` in slots is free, a `make` also when no other
    `make` runs; one that waits holds back every later command.
    """
    results: dict[str, Result] = {}
    free = threading.Condition()
    used = makes = 0

    def ready(need: int, make: bool) -> bool:
        return used + need <= CPUS and not (make and makes)

    def finish(text: str, need: int, make: bool) -> None:
        nonlocal used, makes
        try:
            results[text] = run(text, root)
        finally:
            with free:
                used -= need
                makes -= make
                free.notify_all()

    threads: list[threading.Thread] = []
    for text in work:
        argv = tokens(text)
        need, make = weight(argv), argv[:1] == ["make"]
        with free:
            free.wait_for(functools.partial(ready, need, make))
            used += need
            makes += make
        threads.append(threading.Thread(target=finish, args=(text, need, make)))
        threads[-1].daemon = True
        threads[-1].start()
    for thread in threads:
        thread.join()
    return results


def report(name: str, command: Command, result: Result) -> list[str]:
    """Return the lines a command that fails prints, none when it passes.

    Why:
    0103-fewer-rounds design D4; 0114-faster-plan-check design D1.
    """
    if result.timed_out:
        return [f"plan: {name} — `{command.text}` timed out"]
    if passed(command, result.code, result.output):
        return []
    shown = [f"  | {line}" for line in result.output.splitlines()[:SHOWN]]
    code = result.code
    verdict = "printed other than its Verify: says" if code == 0 else f"exited {code}"
    return [f"plan: {name} — `{command.text}` {verdict}", *shown]


def passed(command: Command, code: int, stdout: str) -> bool:
    """Return whether a command's exit and output are what its `Verify:` says.

    The rule is `report`'s.
    """
    argv = tokens(command.text)
    search = argv[:1] == ["grep"] or argv[:2] == ["git", "grep"]
    wanted = (
        "" if command.nothing else None if command.count is None else str(command.count)
    )
    # Nothing is no byte at all, blank lines included; a count is read stripped.
    printed = stdout if command.nothing else stdout.strip()
    if code == 0 and wanted in (None, printed):
        return True
    return code == 1 and search and wanted in ("", "0") and printed in ("", wanted)


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


def jobs(
    tasks: list[Task], human: set[int], only: set[str] | None
) -> list[tuple[str, Command]]:
    """Return the `(sub-task, command)` pairs a check judges, in task order.

    Not judged: a `**HALT CHECK**` sub-task, a sub-task of a `**HUMAN` phase, and a
    command naming `plan_check.py`. `only` names the sub-tasks, ticked or not.
    """
    found: list[tuple[str, Command]] = []
    for task in tasks:
        skipped = "**HALT CHECK**" in task.text or int(task.name.split(".")[0]) in human
        wanted = task.ticked if only is None else task.name in only
        if not wanted or skipped or (verify := verify_of(task.text)) is None:
            continue
        try:
            for command in commands(verify):
                if "plan_check.py" not in command.text:
                    tokens(command.text)
                    found.append((task.name, command))
        except Unparsed as error:
            raise Stop(f"{task.name}: {error}") from None
    return found


@functools.cache
def gate() -> dict[str, Any]:
    """Return the names of `gate_run.py`, loaded once from this script's folder."""
    return runpy.run_path(str(Path(__file__).resolve().parent / "gate_run.py"))


def _guarded[T](call: Callable[[], T]) -> T | None:
    """Return a `gate_run.py` call's result, or None when it stops or times out."""
    stops = (gate()["Stop"], subprocess.TimeoutExpired)
    try:
        return call()
    except stops:
        return None


def gate_green() -> bool:
    """Return whether the gate's green record stands for this tree and dry run."""
    tree = _guarded(gate()["settled_tree"])
    if tree is None:
        return False
    folder, dry = _guarded(gate()["records"]), _guarded(gate()["dry_run"])
    return (
        folder is not None
        and dry is not None
        and gate()["read_record"](folder / tree).get("dry") == dry
    )


def is_pytest(argv: list[str]) -> bool:
    """Return whether argv starts `pytest`, `uv run pytest` or `python -m pytest`."""
    return argv[:1] == ["pytest"] or argv[:3] in (
        ["uv", "run", "pytest"],
        ["python", "-m", "pytest"],
    )


def names_tests(argv: list[str], root: Path) -> bool:
    """Return whether each operand is a test module whose `::` nodes are tests.

    A directory, non-test file or node, or `[` id runs: only collection settles it.
    """
    for word in argv:
        path, *nodes = word.split("::")
        file = root / path
        if not file.is_file() or not TEST_MODULE.fullmatch(file.name):
            return False
        text = _read(file) if nodes else ""
        for node in nodes:
            if "[" in node:  # a parameter id exists only on collection: run it
                return False
            kind = "def" if node.startswith("test") else "class"
            if not node.startswith(("test", "Test")) or not re.search(
                rf"^\s*(?:async\s+)?{kind}\s+{re.escape(node)}\b", text, re.M
            ):
                return False
    return True


def gate_discovers(operand: str, root: Path) -> bool:
    """Return whether the gate's bare pytest reaches an operand's file.

    `testpaths` name where it looks, and an ignore option or a conftest's
    `collect_ignore` hook may exclude what an explicit operand still collects.
    """
    try:
        config = tomllib.loads((root / "pyproject.toml").read_text())
    except (OSError, tomllib.TOMLDecodeError):
        config = {}
    options = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
    paths = options.get("testpaths") or ["."]
    file = (root / operand.split("::", maxsplit=1)[0]).resolve()
    if not any(file.is_relative_to((root / str(path)).resolve()) for path in paths):
        return False
    if re.search(r"--(?:ignore|deselect)", str(options.get("addopts", ""))):
        return False
    folder = file.parent
    while folder.is_relative_to(root.resolve()):
        if EXCLUDES.search(_read(folder / "conftest.py")):
            return False
        folder = folder.parent
    return True


def _vouched(word: str, root: Path) -> bool:
    """Return whether a word after the pytest prefix keeps the gate's proof."""
    return word in QUIET_OPTIONS or (
        not word.startswith("-")
        and names_tests([word], root)
        and gate_discovers(word, root)
    )


def bare_pytest(command: Command, root: Path) -> bool:
    """Return whether a pytest command's `Verify:` says it exits 0 and no more.

    Only a quiet option or an operand that exists follows the prefix: a selection
    or any other option runs, so a green gate vouches for the rest.
    """
    argv = tokens(command.text)
    return (
        is_pytest(argv)
        and command.count is None
        and not command.nothing
        and all(
            _vouched(word, root) for word in argv[1 if argv[0] == "pytest" else 3 :]
        )
    )


def collecting(texts: list[str], root: Path) -> set[str]:
    """Return the commands whose collection exits 0 and prints a collected test.

    The collection is the command with `--collect-only -q` appended, run as any
    command is. Why: 0114-faster-plan-check design D2.
    """
    found = schedule([text + COLLECT_ONLY for text in texts], root)
    return {
        text
        for text in texts
        if found[text + COLLECT_ONLY].code == 0
        and COLLECTED.search(found[text + COLLECT_ONLY].output)
    }


def names_revision(argv: list[str]) -> bool:
    """Return whether a command reads a revision, so `HEAD` is part of its key.

    A word starting `HEAD` or a hex sha, a `git` command but `ls-files`, or a word
    that holds `git` as a word of its own, as a shell's script does.
    """
    if any(word.startswith("HEAD") or REVISION.fullmatch(word) for word in argv):
        return True
    if argv[:1] == ["git"]:
        return argv[1:2] != ["ls-files"]
    return any(re.search(r"\bgit\b", word) for word in argv)


def reads_git(argv: list[str], root: Path) -> bool:
    """Return whether a word names a file in the tree whose text holds `git`."""
    for word in argv:
        path = root / word
        try:
            if path.is_file() and re.search(
                r"\bgit\b", path.read_text(errors="replace")
            ):
                return True
        except OSError:
            return True  # unreadable: tree-only behaviour is unproven
    return False


def keyed(text: str, head: str, root: Path | None = None) -> str:
    """Return a command's key: its text, and the refs' state when it names a revision.

    `head` is `HEAD`'s sha and every ref's, so another branch moving ends a reuse.
    A script file the command names counts when its text holds `git`.
    """
    argv = tokens(text)
    if names_revision(argv) or (root is not None and reads_git(argv, root)):
        return f"{text}\n{head}"
    return text


def store(tree: str) -> Path:
    """Return the folder that keeps a settled tree's results."""
    return gate()["records"]().parent / "plan-check" / tree


def keep(tree: str, key: str, result: Result) -> None:
    """Write a result under its key; a store that is a link keeps nothing."""
    folder = store(tree)
    if folder.is_symlink() or folder.parent.is_symlink():
        return
    path = folder / hashlib.sha256(key.encode()).hexdigest()
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    with contextlib.suppress(OSError):
        folder.mkdir(parents=True, exist_ok=True)
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            json.dump({"exit": result.code, "output": result.output}, file)
        staged.replace(path)


def load(tree: str, key: str) -> Result | None:
    """Return the result kept under a key, or None when none can be read."""
    path = store(tree) / hashlib.sha256(key.encode()).hexdigest()
    try:
        kept = json.loads(path.read_text(errors="replace"))
        return Result(int(kept["exit"]), str(kept["output"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def check_verifies(
    tasks: list[Task], human: set[int], root: Path, only: set[str] | None = None
) -> list[str]:
    """Return a line for each judged `Verify:` command that fails run again.

    Each distinct command runs once. A bare pytest passes unrun on the gate's green
    record when its collection finds a test; kept results are read and written.
    """
    pairs = jobs(tasks, human, only)
    bare = list(dict.fromkeys(c.text for _, c in pairs if bare_pytest(c, root)))
    vouched = collecting(bare, root) if bare and gate_green() else set()
    pending = [
        (n, c) for n, c in pairs if not (c.text in vouched and bare_pytest(c, root))
    ]
    refs = _git(root, "for-each-ref", "--format=%(objectname) %(refname)").stdout
    head = _git(root, "rev-parse", "HEAD").stdout.strip() + "\n" + refs
    tree = _guarded(gate()["settled_tree"])
    keys = {command.text: keyed(command.text, head, root) for _, command in pending}
    results: dict[str, Result] = {}
    if tree is not None:
        results = {t: kept for t, k in keys.items() if (kept := load(tree, k))}
    fresh = schedule([text for text in keys if text not in results], root)
    results |= fresh
    if tree is not None and _guarded(gate()["settled_tree"]) == tree:
        for text, result in fresh.items():
            if not result.timed_out:
                keep(tree, keys[text], result)
    problems: list[str] = []
    for name, command in pending:
        problems += report(name, command, results[command.text])
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


def _read(path: Path) -> str:
    """Return a file's text, or nothing when it cannot be read."""
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def removed_lines(root: Path, folder: str, path: str) -> set[int]:
    """Return the numbers of a living spec's lines in requirements the delta removes."""
    parts = Path(path).parts
    if len(parts) != 4 or parts[:2] != ("openspec", "specs") or parts[3] != "spec.md":
        return set()
    titles: set[str] = set()
    listed = False
    for line in _read(root / folder / "specs" / parts[2] / "spec.md").splitlines():
        if line.startswith("## "):
            listed = line.rstrip() == REMOVED
        elif listed and line.startswith(REQUIREMENT):
            titles.add(line.removeprefix(REQUIREMENT).strip())
    numbers: set[int] = set()
    inside = False
    for number, line in enumerate(_read(root / path).splitlines(), start=1):
        if line.startswith(REQUIREMENT):
            inside = line.removeprefix(REQUIREMENT).strip() in titles
        elif line.startswith("## "):
            inside = False
        if inside:
            numbers.add(number)
    return numbers


def check_names(
    root: Path, change: str, merge_base: str, tests: tuple[str, range]
) -> list[str]:
    """Return a line for each removed name the plan still names.

    Why: 0108-converge-script design C8.
    """
    folder = f"openspec/changes/{change}"
    lines: list[str] = []
    removed: dict[str, set[int]] = {}
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
            if path not in removed:
                removed[path] = removed_lines(root, folder, path)
            out = (
                path == f"{folder}/tasks.md"
                or (path == f"{folder}/design.md" and number in tests[1])
                or number in removed[path]
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


def check(change: str, base: str, only: set[str] | None = None) -> list[str]:
    """Return every problem line of a change's plan against the working tree.

    With `only`, the `Verify:` lines of those sub-tasks, ticked or not, and no other.
    """
    if not CHANGE.fullmatch(change) or base.startswith("-"):
        raise Stop("the change id or the base is not one this check reads")
    root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    folder = root / "openspec" / "changes" / change
    try:
        tasks = (folder / "tasks.md").read_text(errors="replace")
    except OSError as error:
        raise Stop(f"tasks.md: {error.strerror}") from None
    found, human = phases(tasks)
    parsed = subtasks(tasks)
    if only is not None:
        return check_verifies(parsed, human, root, only)
    merge_base = _git(root, "merge-base", base, "HEAD").stdout.strip()
    design = folder / "design.md"
    tests = tests_section(
        design.read_text(errors="replace") if design.is_file() else ""
    )
    return [
        *check_verifies(parsed, human, root),
        *check_boxes(parsed, found),
        *check_names(root, change, merge_base, tests),
        *check_tests(root, merge_base, tests),
        *check_corpus(parsed, root),
    ]


def _terminate(_signum: int, _frame: FrameType | None) -> None:
    """End the group of each running command, and exit 143."""
    for process in tuple(RUNNING):
        _kill(process)
    sys.exit(143)


def main(argv: list[str] | None = None) -> int:
    """Check a change's plan from inside the repository; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Hold a change's plan to the tree built from it."
    )
    parser.add_argument("--change", required=True, help="the change id")
    parser.add_argument("--base", required=True, help="the revision the branch left")
    parser.add_argument(
        "--only", nargs="+", metavar="N.M", help="check only these sub-tasks' Verify:"
    )
    args = parser.parse_args(argv)
    only = None if args.only is None else set(args.only)
    if only is not None and not all(ID.fullmatch(name) for name in only):
        print(f"plan: cannot check — --only takes ids like 3.2, not {sorted(only)}")
        return 2
    previous = signal.signal(signal.SIGTERM, _terminate)
    try:
        problems = check(args.change, args.base, only)
    except Stop as stop:
        print(f"plan: cannot check — {stop}")
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous)
    print(*(problems or ["plan: clean"]), sep="\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
