# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check that a branch's gate is the base's, or that the cut planned its change.

    gate_check.py --change <id> --base <rev>

Exit 0 the gate passes · 1 halt · 2 the gate cannot be read.
Why: 0034-gate-recipe-hardening design D1…D4.
"""

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

EXPORTS = Path(".minions/gate-check")
TIMEOUT_SECONDS = 300
# A make that runs this script passes its flags down, `-i` or `-q` among them.
CLEARED = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")
# `gate_makefiles` parses make's English `Reading makefile` and directory lines.
PINNED = {"LC_ALL": "C"}
CHANGE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
DIRECTORY = re.compile(r": Entering directory [`'](.*)'$")
READING = re.compile(r"Reading makefile [`'](.+?)'(?: \(|\.\.\.)")
# A recipe's `-`, after a tab or a rule's `;`, or a `$` that may expand to one.
RECIPE_PREFIX = re.compile(r"\t[@+\s]*[-$]")
RULE_RECIPE = re.compile(r"[^\t#=]*:[^;=]*;[@+\s]*[-$]")
SHELL_SET = re.compile(
    r"(?:^|[\s:;])(?:SHELL|\.SHELLFLAGS|\.RECIPEPREFIX)\s*(?:[+?!]|:{1,3})?="
)
SPECIAL_TARGETS = (".IGNORE", ".ONESHELL")
MAKEFLAGS_SET = re.compile(
    r"\s*(?:(?:export|override)\s+)*MAKEFLAGS\s*(?:[+?!]|::?)?=(.*)$"
)
IGNORE_FLAG = re.compile(r"-[A-Za-z]*i[A-Za-z]*")


class Stop(Exception):
    """End the check with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _env() -> dict[str, str]:
    """Return this process's environment without the inherited make flags."""
    kept = {key: value for key, value in os.environ.items() if key not in CLEARED}
    return kept | PINNED


def _run(argv: list[str], cwd: Path, what: str) -> str:
    """Return a command's stdout; a failure stops the check with exit 2."""
    try:
        done = subprocess.run(
            argv,
            cwd=cwd,
            env=_env(),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        raise Stop(2, f"gate: cannot check — {argv[0]} is missing") from None
    except subprocess.TimeoutExpired:
        raise Stop(2, f"gate: cannot check — {what} timed out") from None
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(2, f"gate: cannot check — {what} failed: {first}")
    return done.stdout


def _git(*args: str) -> str:
    """Return the output of a git command run in the repository root."""
    return _run(["git", *args], Path("."), f"git {args[0]}")


def cut_commit(change: str) -> str:
    """Return the one commit that adds the change's `design.md`; else halt."""
    design = f"openspec/changes/{change}/design.md"
    commits = _git("log", "--diff-filter=A", "--format=%h", "--", design).split()
    if len(commits) != 1:
        named = ", ".join(commits) or "no commit"
        raise Stop(
            1, f"gate: halt — no single cut commit: {design} is added by {named}"
        )
    return commits[0]


def planning_tasks(tasks: str) -> list[str]:
    """Return each sub-task naming both `Makefile` and `gate`, its wrapped lines joined.

    e.g. "- [ ] 1.2 Edit the `gate` recipe in `Makefile`." → "1.2 Edit the `gate` …"
    """
    found: list[str] = []
    wrapped = False
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            found.append(match[1])
            wrapped = True
        elif wrapped and line[:1] in (" ", "\t") and line.strip():
            found[-1] += " " + line.strip()
        else:
            wrapped = False
    return [text for text in found if "Makefile" in text and "`gate`" in text]


def export(rev: str, dest: Path, side: str) -> None:
    """Write the tree at `rev` into `dest`, an empty directory it creates."""
    dest.mkdir(parents=True)
    archive = dest.with_suffix(".tar")
    argv = ["git", "archive", "--format=tar", f"--output={archive}", rev]
    _run(argv, Path("."), f"the {side}'s export")
    try:
        with tarfile.open(archive) as tar:
            tar.extractall(dest, filter="data")
    except (tarfile.TarError, OSError) as error:
        raise Stop(2, f"gate: cannot check — the {side}'s export failed: {error}")
    # `export-ignore` drops a path the checkout's make still reads.
    for entry in _git("ls-tree", "-r", "-z", "--full-tree", rev).split("\0"):
        meta, _, name = entry.partition("\t")
        if name and meta.split()[1] != "commit" and not os.path.lexists(dest / name):
            raise Stop(2, f"gate: cannot check — the {side}'s export lacks {name}")


def gate_makefiles(root: Path, trace: str) -> set[str]:
    """Return the files make reads in `make -pn -r -w -d gate`, as paths inside `root`.

    Names come from make's `Reading makefile` lines and each `MAKEFILE_LIST`. A makefile
    can reassign the list or print a directory line, so each name is tried against every
    directory the trace enters, and kept where `root` holds that file.
    e.g. "Reading makefile `gate.mk' (search path)..." → {"gate.mk"}
    """
    top = root.resolve()
    directories = {top}
    names: set[str] = set()
    for line in trace.splitlines():
        if match := DIRECTORY.search(line):
            directories.add(Path(match[1]))
        elif match := READING.search(line):
            names.add(match[1])
        elif line.startswith("MAKEFILE_LIST :="):
            names.update(line.removeprefix("MAKEFILE_LIST :=").split())
    paths = {(where / name).resolve() for where in directories for name in names}
    return {
        path.relative_to(top).as_posix()
        for path in paths
        if path.is_relative_to(top) and path.is_file()
    }


def dry_run(root: Path, side: str) -> list[str]:
    """Return `make -n gate`'s lines in `root`, its own path made `<export>`."""
    output = _run(["make", "-n", "gate"], root, f"the {side}'s dry run")
    return output.replace(str(root.resolve()), "<export>").splitlines()


def ignores_errors(line: str) -> bool:
    """Return whether a makefile line may hide a failing command.

    A `-` recipe prefix after a tab or a rule's `;`, or a variable there that may expand
    to one; `.IGNORE` or `.ONESHELL`; a `SHELL`, `.SHELLFLAGS` or `.RECIPEPREFIX`
    assignment; or `-i` in `MAKEFLAGS`.
    """
    if RECIPE_PREFIX.match(line) or RULE_RECIPE.match(line) or SHELL_SET.search(line):
        return True
    if any(target in line for target in SPECIAL_TARGETS):
        return True
    if match := MAKEFLAGS_SET.match(line):
        words = match[1].split()
        # The first word may be bare flag letters: `MAKEFLAGS += ki`.
        flags = [f"-{word}" for word in words[:1]] + words
        return any(w == "--ignore-errors" or IGNORE_FLAG.fullmatch(w) for w in flags)
    return False


def ignore_marks(base: str, files: list[str]) -> list[tuple[str, str]]:
    """Return each line the branch adds to `files` that ignores errors, by file."""
    marks: list[tuple[str, str]] = []
    if not files:
        return marks
    current = ""
    for line in _git("diff", "-U0", base, "HEAD", "--", *files).splitlines():
        if line.startswith("+++ "):
            current = line.removeprefix("+++ b/")
        elif line.startswith("+") and ignores_errors(line[1:]):
            marks.append((current, line[1:].strip()))
    return marks


def read_side(rev: str, root: Path, side: str) -> tuple[set[str], list[str]]:
    """Export `rev` to `root`; return its gate makefiles and its dry run."""
    export(rev, root, side)
    trace = _run(
        ["make", "-pn", "-r", "-w", "-d", "gate"], root, f"the {side}'s make database"
    )
    return gate_makefiles(root, trace), dry_run(root, side)


def check(change: str, base: str) -> str:
    """Return the passing verdict; a halt or an unreadable gate raises `Stop`."""
    cut = cut_commit(change)
    tasks = planning_tasks(_git("show", f"{cut}:openspec/changes/{change}/tasks.md"))
    root = EXPORTS / change
    shutil.rmtree(root, ignore_errors=True)
    try:
        base_files, base_lines = read_side(base, root / "base", "base")
        head_files, head_lines = read_side("HEAD", root / "head", "head")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    changed = set(_git("diff", "--name-only", base, "HEAD").splitlines())
    touched = sorted((base_files | head_files) & changed)
    diff = "\n".join(
        difflib.unified_diff(
            base_lines,
            head_lines,
            "base: make -n gate",
            "head: make -n gate",
            lineterm="",
        )
    )
    if not touched and not diff:
        return "gate: the base's"
    if not tasks:
        # The changed makefiles, or else the dry runs' diff.
        shown = "".join(f"\n  {name}" for name in touched) or f"\n{diff}"
        raise Stop(
            1,
            "gate: halt — the branch changes the gate, and no cut task names "
            f"`Makefile` and `gate`:{shown}",
        )

    def quoted(text: str) -> bool:
        return any(text.strip() in task for task in tasks)

    kept = set(head_lines)
    problems = [
        f"  dropped: {line}"
        for line in base_lines
        if line.strip() and line not in kept and not quoted(line)
    ]
    problems += [
        f"  ignore mark: {name}: {text}"
        for name, text in ignore_marks(base, touched)
        if not quoted(text)
    ]
    if problems:
        raise Stop(
            1,
            "gate: halt — the planned change hides a failure the task does not quote:\n"
            + "\n".join(problems)
            + f"\n{diff}",
        )
    return f"gate: planned — {' · '.join(tasks)}\n{diff}"


def main(argv: list[str] | None = None) -> int:
    """Run the check from the repository root; return its exit code."""
    parser = argparse.ArgumentParser(
        description="Halt on a gate the change's cut did not plan."
    )
    parser.add_argument("--change", required=True, help="the change id")
    parser.add_argument("--base", required=True, help="the base commit")
    args = parser.parse_args(argv)
    if not CHANGE_ID.fullmatch(args.change):
        parser.error(f"--change: not a change id: {args.change}")
    if args.base.startswith("-"):
        parser.error(f"--base: not a commit: {args.base}")
    try:
        print(check(args.change, args.base))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
