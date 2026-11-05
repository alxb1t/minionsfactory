# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run each search a `tasks.md`'s checks name at HEAD, and halt on a check out of shape.

    verify_check.py <tasks.md>

Exit 0 no break · 1 a check breaks `I19` · 2 a check cannot be parsed or run. Run
from the repository root. A `grep` or `git grep` runs as argv, no shell, over HEAD's
tree, or the revision a `git grep` names; each match prints as
`<sub-task>: <path>:<line>: <text>`. A search takes the options below alone, and no
path outside the repository: any other option, a pager's among them, or such a
path, breaks `I19`. Why: 0066-plan-halts design D1.
"""

import argparse
import io
import os
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import NamedTuple

TIMEOUT_SECONDS = 60
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
VARIABLE = re.compile(r"\$\{?[A-Za-z_]")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
MATCH = re.compile(r"(.+?):(\d+):(.*)")
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
LOOPS = {"for", "while", "until"}
OPERATOR = set("();<>|&")
# Flags that hide the matching lines; the search prints them.
HIDING = set("clLqh")
HIDING_LONG = {
    "--count",
    "--files-with-matches",
    "--files-without-match",
    "--quiet",
    "--silent",
    "--no-filename",
}
# The options a search runs with; `e`, last in its word, takes the next as a pattern.
SHORT = HIDING | set("eEFGHinorRsvwx")
LONG = HIDING_LONG | {
    "--basic-regexp",
    "--extended-regexp",
    "--fixed-strings",
    "--ignore-case",
    "--invert-match",
    "--line-number",
    "--line-regexp",
    "--only-matching",
    "--recursive",
    "--word-regexp",
}


class Stop(Exception):
    """End the check with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


class Unparsed(ValueError):
    """A `Verify:` that cannot be read or run; the message says why."""


class Command(NamedTuple):
    """One backticked command of a `Verify:`, and the count its output names."""

    text: str
    count: int | None


class Search(NamedTuple):
    """The argv that prints a search's matching lines, and what it would read.

    `refused` holds each option it does not run, `paths` each file operand, and
    `revision` the operand a `git grep` reads as one when git resolves it.
    """

    argv: list[str]
    refused: list[str]
    paths: list[str]
    revision: str | None


def _spawn(
    argv: list[str], what: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Return a finished process; a missing program or a timeout stops with exit 2."""
    try:
        return subprocess.run(
            argv, cwd=cwd, env=env, capture_output=True, timeout=TIMEOUT_SECONDS
        )
    except FileNotFoundError:
        raise Stop(2, f"verify: cannot check — {argv[0]} is missing") from None
    except subprocess.TimeoutExpired:
        raise Stop(2, f"verify: cannot check — {what} timed out") from None


def _git(argv: list[str], what: str, env: dict[str, str] | None = None) -> bytes:
    """Return a git command's stdout, run here; a failure stops with exit 2."""
    done = _spawn(["git", *argv], what, Path.cwd(), env)
    if done.returncode != 0:
        first = done.stderr.decode(errors="replace").strip().partition("\n")[0]
        raise Stop(2, f"verify: cannot check — {what} failed: {first}")
    return done.stdout


def subtasks(tasks: str) -> list[list[str]]:
    """Return each sub-task's lines, stripped: its first, then each wrapped line."""
    found: list[list[str]] = []
    wrapped = False
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            found.append([match[1]])
            wrapped = True
        elif wrapped and line[:1] in (" ", "\t") and line.strip():
            found[-1].append(line.strip())
        else:
            wrapped = False
    return found


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
    return found


def tokens(command: str) -> list[str]:
    """Return a command's shell words, each run of operator characters its own word."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError as error:
        raise Unparsed(f"{error}: `{command}`") from None


def masked(command: str, kinds: str = "'\"") -> str:
    """Return `command`, each escaped character and each in a `kinds` quote `_`.

    A shell reads no `$` or operator there, and the words keep their bounds.
    e.g. `a '$x|' "$y"`, "'" → `a _____ "$y"`
    """
    out, quote, escaped = list(command), "", False
    for i, char in enumerate(command):
        if escaped or (quote != "'" and char == "\\"):
            escaped, out[i] = not escaped, "_"
            continue
        inside = quote or (char if char in "'\"" else "")
        if inside and inside in kinds:
            out[i] = "_"
        if not quote and char in "'\"":
            quote = char
        elif char == quote:
            quote = ""
    return "".join(out)


def breaks(command: str, shell: list[str]) -> list[str]:
    """Return how a command breaks `I19`'s one plain command; none when it holds.

    `shell` is the command's words as a shell reads them, quoted text masked.
    """
    expands = masked(command, "'")
    found = ["`$(…)`"] if "$(" in expands else []
    found += ["a backtick"] if "`" in command else []
    starts = [
        word
        for i, word in enumerate(shell)
        if i == 0 or set(shell[i - 1]) <= OPERATOR or shell[i - 1] in ("do", "then")
    ]
    if VARIABLE.search(expands) or any(ASSIGNMENT.match(word) for word in starts):
        found.append("a shell variable")
    found += ["a loop"] if LOOPS & set(starts) else []
    found += ["`cd`"] if "cd" in starts else []
    return found


def plain(words: list[str], shell: list[str]) -> list[str]:
    """Return the words before the first operator a shell reads, a quoted one not.

    e.g. ["grep", "|", "a", ">", "o"], ["grep", "___", "a", ">", "o"]
    → ["grep", "|", "a"]
    """
    ends = [i for i, word in enumerate(shell) if set(word) <= OPERATOR]
    return words[: (ends or [len(words)])[0]]


def search(words: list[str]) -> Search | None:
    """Return how a search's plain words run, printing its lines; None for no search.

    `-n` is added, and the flags that hide lines dropped. A `git grep` reads HEAD's
    index, unless its first operand after the pattern is a revision git resolves.
    e.g. ["grep", "-c", "x", "a"] → (["grep", "-H", "-n", "x", "a"], [], ["a"], None)
    """
    if words[:1] == ["grep"]:
        head, rest = ["grep", "-H", "-n"], words[1:]
    elif words[:2] == ["git", "grep"]:
        head, rest = ["git", "grep", "--no-color", "-n"], words[2:]
    else:
        return None
    kept: list[str] = []
    refused: list[str] = []
    operands: list[str] = []
    tail: list[str] = []
    pattern = value = False
    for i, word in enumerate(rest):
        if value or not word.startswith("-"):
            operands += [] if value else [word]
            kept.append(word)
            value = False
        elif word == "--":
            tail = rest[i:]
            break
        elif word in LONG:
            kept += [] if word in HIDING_LONG else [word]
        elif re.fullmatch(r"-(?:[A-Za-df-z]+e?|e)", word) and set(word[1:]) <= SHORT:
            # `e` ends its word, so a pattern attached to it is refused, never read.
            value = word.endswith("e")
            pattern = pattern or value
            flags = "".join(flag for flag in word[1:] if flag not in HIDING)
            kept += [f"-{flags}"] if flags else []
        else:
            refused.append(word)
    after = operands[0 if pattern else 1 :]
    revision = after[0] if head[0] == "git" and after else None
    paths = (operands + tail[1:])[0 if pattern else 1 :]
    return Search(head + kept + tail, refused, paths, revision)


class Head:
    """HEAD's tree, exported and indexed on first use, in a scratch directory."""

    def __init__(self, scratch: Path) -> None:
        """Keep the scratch directory; export nothing yet."""
        self.scratch = scratch
        self.tree: Path | None = None
        self.env: dict[str, str] | None = None

    def run(self, query: Search) -> list[str]:
        """Return a search's output lines, run over HEAD: stdout, then stderr.

        A `git grep` reads HEAD's index, or the revision it names. One git refuses,
        a revision it cannot read among them, raises `Unparsed`: it searched nothing.
        """
        argv = query.argv
        if argv[0] == "grep":
            done = _spawn(argv, "grep", self.export())
        elif query.revision is not None and self.resolves(query.revision):
            done = _spawn(argv, "git grep", Path.cwd())
        else:
            argv = [*argv[:2], "--cached", *argv[2:]]
            done = _spawn(argv, "git grep", Path.cwd(), self.index())
        err = done.stderr.decode(errors="replace").splitlines()
        if argv[0] == "git" and done.returncode > 1:
            raise Unparsed(f"git grep failed: {(err or ['no message'])[0]}")
        return done.stdout.decode(errors="replace").splitlines() + err

    def resolves(self, word: str) -> bool:
        """Return whether git reads `word` as a revision, as `git grep` does."""
        argv = ["git", "rev-parse", "--verify", "--quiet", word]
        return _spawn(argv, "git rev-parse", Path.cwd()).returncode == 0

    def outside(self, path: str) -> bool:
        """Return whether a search's path is absolute, climbs, or leaves HEAD's tree."""
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            return True
        tree = self.export().resolve()
        return not (tree / path).resolve().is_relative_to(tree)

    def export(self) -> Path:
        """Return HEAD's tree, written out once."""
        if self.tree is None:
            archive = _git(["archive", "--format=tar", "HEAD"], "git archive")
            self.tree = self.scratch / "tree"
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(self.tree, filter="data")
        return self.tree

    def index(self) -> dict[str, str]:
        """Return the environment of an index holding HEAD, read once."""
        if self.env is None:
            self.env = {**os.environ, "GIT_INDEX_FILE": str(self.scratch / "index")}
            _git(["read-tree", "HEAD"], "git read-tree", self.env)
        return self.env


def check_command(subtask: str, command: Command, head: Head) -> bool:
    """Print a command's breaks, else its search's matches; return whether it broke."""
    words, shell = tokens(command.text), tokens(masked(command.text))
    if found := breaks(command.text, shell):
        print(f"{subtask}: I19 — {' · '.join(found)}: `{command.text}`")
        return True
    query = search(plain(words, shell))
    if query is None:
        return False
    if query.refused:
        refused = " · ".join(query.refused)
        print(
            f"{subtask}: I19 — an option the search does not run: {refused}: "
            f"`{command.text}`"
        )
        return True
    if outside := [path for path in query.paths if head.outside(path)]:
        print(
            f"{subtask}: I19 — a path outside the repository: {' · '.join(outside)}: "
            f"`{command.text}`"
        )
        return True
    matches = 0
    for line in head.run(query):
        if match := MATCH.fullmatch(line):
            matches += 1
            line = f"{match[1]}:{match[2]}: {match[3]}"
        print(f"{subtask}: {line}")
    if command.count is not None and matches > command.count:
        print(
            f"{subtask}: I19 — an exact count `{command.count}` beside {matches} "
            f"matches: `{command.text}`"
        )
        return True
    return False


def check(tasks: str, head: Head) -> list[str]:
    """Return the sub-tasks whose checks break `I19`; print what each search finds."""
    broken: list[str] = []
    for lines in subtasks(tasks):
        text = " ".join(lines)
        name = lines[0].split()[0]
        # A task may name `Verify:` in a span; the check's marker stands outside one.
        masked = SPAN.sub(lambda span: " " * len(span[0]), text)
        if (at := masked.find("Verify:")) < 0:
            continue
        verify = text[at + len("Verify:") :]
        try:
            hits = [check_command(name, command, head) for command in commands(verify)]
        except Unparsed as error:
            raise Stop(2, f"verify: cannot check — {name}: {error}") from None
        if any(hits):
            broken.append(name)
    return broken


def main(argv: list[str] | None = None) -> int:
    """Check a `tasks.md` from the repository root; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Run a tasks.md's searches at HEAD and check I19's shape."
    )
    parser.add_argument("tasks", type=Path, help="the change's tasks.md")
    path = parser.parse_args(argv).tasks
    try:
        try:
            tasks = path.read_text()
        except OSError as error:
            raise Stop(2, f"verify: cannot check — {path}: {error.strerror}") from None
        with tempfile.TemporaryDirectory() as scratch:
            broken = check(tasks, Head(Path(scratch)))
    except Stop as stop:
        print(stop)
        return stop.code
    if broken:
        print(f"verify: halt — I19: {', '.join(broken)}")
        return 1
    print("verify: every check is one plain command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
