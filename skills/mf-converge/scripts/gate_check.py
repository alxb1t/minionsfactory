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
import contextlib
import difflib
import io
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
CHANGE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
DIRECTORY = re.compile(r": (Entering|Leaving) directory [`'](.*)'$")
DASH_PREFIX = re.compile(r"\t[@+]*-")
MAKEFLAGS_SET = re.compile(
    r"\s*(?:(?:export|override)\s+)*MAKEFLAGS\s*(?:\+|::?|\?|!)?=(.*)$"
)
IGNORE_FLAG = re.compile(r"-[A-Za-z]*i[A-Za-z]*")
IGNORE_LETTERS = re.compile(r"[A-Za-z]*i[A-Za-z]*")


class Stop(Exception):
    """End the check with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _env() -> dict[str, str]:
    """Return this process's environment without the inherited make flags."""
    return {key: value for key, value in os.environ.items() if key not in CLEARED}


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
    found: list[list[str]] = []
    current: list[str] | None = None
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            current = [match[1]]
            found.append(current)
        elif current is not None and line[:1] in (" ", "\t") and line.strip():
            current.append(line.strip())
        else:
            current = None
    texts = [" ".join(parts) for parts in found]
    return [text for text in texts if "Makefile" in text and "`gate`" in text]


def export(rev: str, dest: Path, side: str) -> None:
    """Write the tree at `rev` into `dest`, an empty directory it creates."""
    dest.mkdir(parents=True)
    failed = f"gate: cannot check — the {side}'s export failed"
    try:
        archive = subprocess.run(
            ["git", "archive", "--format=tar", rev],
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
        if archive.returncode != 0:
            error = archive.stderr.decode(errors="replace").strip().splitlines()
            raise Stop(2, f"{failed}: {error[0] if error else archive.returncode}")
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(dest, filter="data")
    except FileNotFoundError:
        raise Stop(2, "gate: cannot check — git is missing") from None
    except (subprocess.SubprocessError, tarfile.TarError, OSError) as error:
        raise Stop(2, f"{failed}: {error}") from None


def gate_makefiles(root: Path, database: str) -> set[str]:
    """Return the files of each `MAKEFILE_LIST` in `make -pn -r -w gate`, inside `root`.

    A sub-make's names are relative to its `Entering directory` line's directory.
    e.g. "MAKEFILE_LIST :=  Makefile gate.mk" → {"Makefile", "gate.mk"}
    """
    top = root.resolve()
    directories = [top]
    found: set[str] = set()
    for line in database.splitlines():
        if match := DIRECTORY.search(line):
            if match[1] == "Entering":
                directories.append(Path(match[2]))
            elif len(directories) > 1:
                directories.pop()
        elif line.startswith("MAKEFILE_LIST :="):
            for name in line.removeprefix("MAKEFILE_LIST :=").split():
                path = (directories[-1] / name).resolve()
                if path.is_relative_to(top):
                    found.add(path.relative_to(top).as_posix())
    return found


def dry_run(root: Path, side: str) -> list[str]:
    """Return `make -n gate`'s lines in `root`, its own path made `<export>`."""
    output = _run(["make", "-n", "gate"], root, f"the {side}'s dry run")
    # Longest first: a resolved `/private/var/…` holds the unresolved `/var/…`.
    paths = sorted({str(root.resolve()), str(root.absolute())}, key=len, reverse=True)
    lines = []
    for line in output.splitlines():
        for path in paths:
            line = line.replace(path, "<export>")
        lines.append(line)
    return lines


def ignores_errors(line: str) -> bool:
    """Return whether a makefile line adds a `-` recipe prefix, `.IGNORE` or `-i`."""
    if DASH_PREFIX.match(line) or ".IGNORE" in line:
        return True
    if match := MAKEFLAGS_SET.match(line):
        words = match[1].split()
        if words and IGNORE_LETTERS.fullmatch(words[0]):
            return True
        return any(w == "--ignore-errors" or IGNORE_FLAG.fullmatch(w) for w in words)
    return False


def ignore_marks(base: str, files: list[str]) -> list[tuple[str, str]]:
    """Return each line the branch adds to `files` that ignores errors, by file."""
    marks: list[tuple[str, str]] = []
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
    database = _run(
        ["make", "-pn", "-r", "-w", "gate"], root, f"the {side}'s make database"
    )
    return gate_makefiles(root, database), dry_run(root, side)


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
        with contextlib.suppress(OSError):
            EXPORTS.rmdir()

    changed = set(_git("diff", "--name-only", base, "HEAD").splitlines())
    touched = sorted((base_files | head_files) & changed)
    if not touched:
        return "gate: the base's"
    if not tasks:
        listed = "".join(f"\n  {name}" for name in touched)
        raise Stop(
            1,
            "gate: halt — the branch changes a gate makefile, and no cut task names "
            f"`Makefile` and `gate`:{listed}",
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
    diff = "\n".join(
        difflib.unified_diff(
            base_lines,
            head_lines,
            "base: make -n gate",
            "head: make -n gate",
            lineterm="",
        )
    )
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
