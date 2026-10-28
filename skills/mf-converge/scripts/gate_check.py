# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Halt on a change to the gate's makefiles or dry run that the cut did not plan.

    gate_check.py --change <id> --base <rev>

Exit 0 no unplanned change · 1 halt · 2 the gate cannot be read.
It reads makefiles and dry runs; a file read at parse time, or a program the
recipe calls, is out of its reach. Why: 0034-gate-recipe-hardening design D1…D4, D7.
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

TIMEOUT_SECONDS = 300
# A make that runs this script passes its flags down, `-i` or `-q` among them.
CLEARED = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")
# `gate_makefiles` parses make's English `Reading makefile` and directory lines.
PINNED = {"LC_ALL": "C"}
CHANGE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
DIRECTORY = re.compile(r": Entering directory [`'](.*)'$")
READING = re.compile(r"Reading makefile [`'](.+?)'(?: \(|\.\.\.)")


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


def exports() -> Path:
    """Return `.minions/gate-check` beside the primary checkout, from any worktree."""
    common = _git("rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common.strip()).parent / ".minions" / "gate-check"


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


def gate_makefiles(root: Path, trace: str) -> dict[str, set[str]]:
    """Map each makefile inside `root` to the paths its resolution depends on.

    Names come from make's `Reading makefile` lines and each `MAKEFILE_LIST`. A makefile
    can reassign the list or print a directory line, so each name is tried against every
    directory the trace enters, and kept where `root` holds that file. Keep the
    lexical name and every followed link beside the target: Git tracks the links.
    e.g. "Reading makefile `gate.mk' (search path)..." → {"gate.mk": {"gate.mk"}}
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
    files: dict[str, set[str]] = {}
    for where in directories:
        for name in names:
            path = Path.cwd() / where / name
            lexical = Path(os.path.abspath(path))
            target = path.resolve()
            if not lexical.is_relative_to(top) or not target.is_relative_to(top):
                continue
            if not path.is_file():
                continue
            dependencies = _resolution_paths(path) | {lexical, target}
            files[path.relative_to(top).as_posix()] = {
                entry.relative_to(top).as_posix()
                for entry in dependencies
                if entry.is_relative_to(top)
            }
    return files


def _resolution_paths(path: Path) -> set[Path]:
    """Return every symlink followed through `path`, including link targets' parents.

    Resolve components in order: `..` follows a link's target, not its lexical parent.
    The caller has resolved the path already, so a cycle cannot reach this walk.
    """
    cursor = Path(path.anchor)
    pending = list(path.parts[1:])
    links: set[Path] = set()
    while pending:
        part = pending.pop(0)
        if part == "..":
            cursor = cursor.parent
            continue
        entry = cursor / part
        if entry.is_symlink():
            links.add(entry)
            target = entry.readlink()
            if target.is_absolute():
                cursor = Path(target.anchor)
                pending = list(target.parts[1:]) + pending
            else:
                pending = list(target.parts) + pending
        else:
            cursor = entry
    return links


def changed_lines(
    base: Path, head: Path, files: list[str]
) -> list[tuple[str, str, str]]:
    """Return each non-blank line of `files` that the `head` export adds or removes.

    Any added line may hide a failure — a `-` prefix, `.IGNORE`, a `SHELL`, `-i` in
    `MAKEFLAGS` — through forms no pattern list keeps up with: a continued line,
    `define`, a computed name, `$(eval)`. A removed one may too: a `SHELL` with
    `pipefail`, which no dry run prints. So every one needs the task's quote.
    e.g. "SHELL := /bin/bash -o pipefail" in base only → ("removed", "Makefile", …)
    """
    changed: list[tuple[str, str, str]] = []
    for name in files:
        old, new = (_lines(side / name) for side in (base, head))
        matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                changed += [("removed", name, t.strip()) for t in old[i1:i2]]
                changed += [("added", name, t.strip()) for t in new[j1:j2]]
    return [line for line in changed if line[2]]


def _lines(path: Path) -> list[str]:
    """Return a file's lines; a file the side lacks has none."""
    return path.read_text(errors="replace").splitlines() if path.is_file() else []


def read_side(rev: str, root: Path, side: str) -> tuple[dict[str, set[str]], list[str]]:
    """Export `rev` to `root`; return its gate makefiles and its dry run.

    The dry run's lines carry `<export>` in place of `root`'s own path.
    """
    export(rev, root, side)
    trace = _run(
        ["make", "-pn", "-r", "-w", "-d", "gate"], root, f"the {side}'s make database"
    )
    output = _run(["make", "-n", "gate"], root, f"the {side}'s dry run")
    lines = output.replace(str(root.resolve()), "<export>").splitlines()
    return gate_makefiles(root, trace), lines


def check(change: str, base: str) -> str:
    """Return the passing verdict; a halt or an unreadable gate raises `Stop`."""
    cut = cut_commit(change)
    tasks = planning_tasks(_git("show", f"{cut}:openspec/changes/{change}/tasks.md"))
    root = exports() / change
    shutil.rmtree(root, ignore_errors=True)
    try:
        base_files, base_lines = read_side(base, root / "base", "base")
        head_files, head_lines = read_side("HEAD", root / "head", "head")
        changed = set(_git("diff", "--name-only", "-z", base, "HEAD").split("\0"))
        touched = sorted(
            set().union(*base_files.values(), *head_files.values()) & changed
        )
        # A changed directory link is no text file; compare the makefiles it redirects.
        affected = sorted(
            name
            for name in base_files.keys() | head_files.keys()
            if (base_files.get(name, set()) | head_files.get(name, set())) & changed
        )
        edits = changed_lines(root / "base", root / "head", affected)
    finally:
        shutil.rmtree(root, ignore_errors=True)

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
        return "gate: no unplanned change"
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
        f"  {kind}: {name}: {text}" for kind, name, text in edits if not quoted(text)
    ]
    if problems:
        raise Stop(
            1,
            "gate: halt — the planned change adds, removes or drops a line "
            "the task does not quote:\n" + "\n".join(problems) + f"\n{diff}",
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
