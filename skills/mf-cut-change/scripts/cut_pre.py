# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run every precondition of the cut, one line a check.

    cut_pre.py <id> [--unattended] [--after <id>[,<id>]]
Exit 0 no halt · 1 a halt · 2 unrunnable. Why: 0106-cut-scripts design D5.
"""

import argparse
import contextlib
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.layout
import mflib.statefile

TIMEOUT_SECONDS = 60
CHANGE_ID = re.compile(r"(\d+)-[a-z0-9]+(?:-[a-z0-9]+)*")
NO_WORK = ("is up to date", "Nothing to be done")
CLEARED = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")


class Stop(Exception):
    """End the run with exit 2; the message is what it prints."""


def _tool(
    argv: list[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str] | None:
    """Return a finished process run here, or None when it cannot start or hangs."""
    try:
        return subprocess.run(
            argv,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git(*args: str, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run here; a code outside `ok` stops."""
    done = _tool(["git", *args])
    if done is None:
        raise Stop(f"git {args[0]} did not run")
    if done.returncode not in ok:
        first = done.stderr.strip().partition("\n")[0]
        raise Stop(f"git {args[0]} failed: {first}")
    return done


def default_branch() -> str:
    """Return the default branch: `origin/HEAD`'s, else `main`.

    e.g. `refs/remotes/origin/trunk` → "trunk"
    """
    named = _git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", ok=(0, 128))
    if named.returncode:
        return "main"
    return named.stdout.strip().removeprefix("origin/")


def _primary() -> Path:
    """Return the primary checkout, the same from every worktree."""
    common = _git("rev-parse", "--path-format=absolute", "--git-common-dir")
    return mflib.layout.primary_of(common.stdout.strip())


def run_directory() -> Path:
    """Return the primary checkout's `.minions/`, the same from every worktree."""
    return mflib.layout.run_dir(_primary())


def open_versions(default: str) -> list[str]:
    """Return each unmerged `[0-9]*` branch, the versions still open."""
    listed = _git(
        "branch",
        "--no-merged",
        default,
        "--list",
        "[0-9]*",
        "--format=%(refname:short)",
    )
    return listed.stdout.split()


def _number(change: str) -> int:
    """Return the number of a change id.

    e.g. "0106-cut-scripts" → 106
    """
    return int(change.partition("-")[0])


def _held(branch: str) -> list[int]:
    """Return the number of each change and archived change `branch` holds."""
    numbers: list[int] = []
    for folder in ("openspec/changes/", "openspec/changes/archive/"):
        tree = _git("ls-tree", "--name-only", branch, folder)
        names = [Path(line).name for line in tree.stdout.splitlines()]
        numbers += [_number(name) for name in names if CHANGE_ID.fullmatch(name)]
    return numbers


def check_agents(change: str, unattended: bool) -> str | None:
    """Return why root `AGENTS.md` is missing, or None."""
    return None if Path("AGENTS.md").is_file() else "root AGENTS.md is missing"


def check_tree(change: str, unattended: bool) -> str | None:
    """Return why the tree is not where the cut starts, or None.

    By hand: the default branch, clean. Unattended: a linked worktree on the branch
    `change`, `HEAD` an ancestor of the default branch, clean.
    """
    default = default_branch()
    branch = _git("branch", "--show-current").stdout.strip()
    if not unattended and branch != default:
        return f"on `{branch}`, not the default branch `{default}`"
    if unattended:
        absolute = ("rev-parse", "--path-format=absolute")
        here = _git(*absolute, "--git-dir").stdout
        if here == _git(*absolute, "--git-common-dir").stdout:
            return "not in a linked worktree"
        if branch != change:
            return f"on `{branch}`, not the branch `{change}`"
        if _git("merge-base", "--is-ancestor", "HEAD", default, ok=(0, 1)).returncode:
            return f"HEAD is not an ancestor of `{default}`"
    return "the tree is not clean" if _git("status", "--porcelain").stdout else None


def check_openspec(change: str, unattended: bool) -> str | None:
    """Return why `openspec --version` does not run, or None."""
    done = _tool(["openspec", "--version"])
    if done is None:
        return "openspec is not on PATH"
    return f"`openspec --version` exited {done.returncode}" if done.returncode else None


def check_gate(change: str, unattended: bool) -> str | None:
    """Return why `make -n gate` prints no command, or None.

    `make -n` is not a sandbox: it still runs `$(shell …)`, `+` lines and `$(MAKE)`.
    """
    env = {key: value for key, value in os.environ.items() if key not in CLEARED}
    done = _tool(["make", "-n", "gate"], env)
    if done is None or done.returncode:
        return "`make -n gate` does not run: the root Makefile has no `gate` target"
    commands = [
        line
        for line in done.stdout.splitlines()
        if line.strip() and not any(text in line for text in NO_WORK)
    ]
    return None if commands else "`make -n gate` prints no command: the recipe is empty"


def _cuts_folder() -> tuple[int | None, str | None]:
    """Return a descriptor on `.minions/cuts` and no reason, or none and why not.

    A missing folder holds no reservation: no descriptor, no reason. A link at
    `.minions` or `cuts` gives the reason `<part>: <error>`, naming it.
    """
    parts = (mflib.layout.MINIONS, mflib.layout.CUTS)
    try:
        return mflib.statefile.open_folder(_primary(), *parts), None
    except FileNotFoundError:
        return None, None
    except OSError as error:
        return None, f"{error.filename}: {error.strerror}"


def check_reserved(change: str, unattended: bool) -> str | None:
    """Return why the reservation is wrong, or None.

    By hand it must not stand; unattended it must, as the run made it under its lock.
    A link or a folder at the reservation is wrong, named.
    """
    fd, why = _cuts_folder()
    if why:
        return why
    stands = False
    if fd is not None:
        try:
            with contextlib.suppress(FileNotFoundError):
                held = os.stat(change, dir_fd=fd, follow_symlinks=False)
                if not stat.S_ISREG(held.st_mode):
                    return f"{change} is a link or a folder in .minions/cuts/"
                stands = True
        finally:
            os.close(fd)
    if unattended and not stands:
        return f"{change} has no reservation in .minions/cuts/"
    if stands and not unattended:
        return (
            f"{change} is queued for the cut station: answer it in the brief, "
            f"then conduct.py rejoin {change}"
        )
    return None


def check_id(change: str, unattended: bool) -> str | None:
    """Return why the id's number is not above every other, or None.

    The others: each change and archived change on the default branch and on each open
    version, and each other reservation. Why: 0106-cut-scripts design D5.
    """
    fd, why = _cuts_folder()
    if why:
        return why
    default = default_branch()
    taken = _held(default)
    for branch in open_versions(default):
        taken += _held(branch)
    if fd is not None:
        try:
            taken += [_number(name) for name in os.listdir(fd) if name != change]
        finally:
            os.close(fd)
    if (top := max(taken, default=0)) >= _number(change):
        return f"the number is not above {top}, one that is taken"
    return None


def _released(default: str, name: str) -> bool:
    """Return whether `default` holds the archive folder of `name`."""
    path = f"{default}:openspec/changes/archive/{name}"
    return _git("cat-file", "-e", path, ok=(0, 1, 128)).returncode == 0


def after_problem(change: str, after: list[str], default: str) -> str | None:
    """Return why an id of `after` is not met or not of a lower number, or None.

    An id is met when it is an open version or the default branch archived it.
    """
    opened = open_versions(default)
    for named in after:
        if named not in opened and not _released(default, named):
            return f"{named} is not an open or released version"
        if _number(named) >= _number(change):
            return f"{named} is not lower than {change}"
    return None


CHECKS: list[tuple[str, Callable[[str, bool], str | None], bool]] = [
    ("agents", check_agents, True),
    ("tree", check_tree, True),
    ("openspec", check_openspec, True),
    ("gate", check_gate, True),
    ("reserved", check_reserved, True),
    ("id", check_id, False),
]


def main(argv: list[str] | None = None) -> int:
    """Run each check, print one line each, and return the exit code."""
    parser = argparse.ArgumentParser(description="Run the cut's preconditions.")
    parser.add_argument("change", help="the change id, <digits>-<slug>")
    parser.add_argument("--unattended", action="store_true", help="the run's cut")
    parser.add_argument("--after", default="", help="the versions it builds on")
    args = parser.parse_args(argv)
    try:
        if not CHANGE_ID.fullmatch(args.change):
            raise Stop(f"`{args.change}` is not <digits>-<slug>")
        _git("rev-parse", "--git-dir")
        after = [named for named in args.after.split(",") if named]
        results = [
            (name, check(args.change, args.unattended))
            for name, check, unattended_too in CHECKS
            if unattended_too or not args.unattended
        ]
        results.append(("after", after_problem(args.change, after, default_branch())))
    except Stop as stop:
        print(f"cut_pre: cannot check — {stop}")
        return 2
    for name, why in results:
        print(f"cut_pre: halt — {name}: {why}" if why else f"cut_pre: ok — {name}")
    return 1 if any(why for _, why in results) else 0


if __name__ == "__main__":
    sys.exit(main())
