# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a skipped checker's findings file as a clean stub at `HEAD`.

    skip_stub.py <findings-file> <round>

e.g. `…/changes/0001-a/adversarial.md 2` → that file at `HEAD`, round 2; exit 0, or 2.
Its keys, line and refusals: 0105-converge-switches design D3.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROLES = ("conformance", "adversarial")
BODY = "Skipped by the plan: no worker judged this round."
STATUS = re.compile(r"^[ \t]+- \*\*Status:\*\*[ \t]*(\w+)", re.MULTILINE)


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _today() -> date:
    """Return the local date."""
    return date.today()


def _git(*args: str, cwd: Path | None = None) -> str:
    """Return git's output for `args` in `cwd`, else the current directory, or stop."""
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise Stop("no repository with a commit here")
    return done.stdout.strip()


def role_of(path: Path) -> str:
    """Return the role the findings file's name holds, or stop.

    e.g. "x/changes/0001-a/adversarial.md" → "adversarial"
    """
    role = path.stem
    if (
        path.suffix != ".md"
        or role not in ROLES
        or path.parent.parent.name != "changes"
    ):
        raise Stop(
            f"{path} is not …/changes/<change-id>/conformance.md or adversarial.md"
        )
    if path.is_symlink() or path.parent.is_symlink():
        raise Stop(f"{path} is a link")
    return role


def round_of(text: str) -> int:
    """Return the round `text` names, or stop."""
    if not (text.isascii() and text.isdigit() and int(text) > 0):
        raise Stop(f"round {text} is not a positive integer")
    return int(text)


def stub(path: Path, role: str, round_: int, head: str, cwd: Path | None = None) -> str:
    """Return the stub's text for `role` at `head`, read from the worktree `cwd`."""
    common = Path(
        _git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=cwd)
    )
    keys = {
        "type": role,
        "plan": path.parent.name,
        "project": common.parent.name,
        "branch": _git("branch", "--show-current", cwd=cwd),
        "head": head,
        "reviewed": _today().isoformat(),
        "round": round_,
        "open_blocking": 0,
        "verdict": "clean",
        "mode": "skipped",
        "workers": 0,
        "model": "none",
        "executor": "none",
        "packet": "skipped: all",
    }
    front = "".join(f"{key}: {value}\n" for key, value in keys.items())
    return f"---\n{front}---\n\n{BODY}\n"


def uncleared(text: str) -> bool:
    r"""Return whether a findings file holds a checker's round not yet cleared.

    A stub never does; another does when not clean or a card is other than verified,
    since Step 9 has yet to write an accepted card to the debt.
    e.g. "---\nmode: parallel\nverdict: clean\n---\n" → False
    """
    lines = text.split("\n---", 1)[0].splitlines()
    pairs = (line.partition(":") for line in lines)
    front = {key.strip(): value.strip() for key, _, value in pairs}
    if front.get("mode") == "skipped":
        return False
    statuses = STATUS.findall(text)
    return front.get("verdict") != "clean" or any(s != "verified" for s in statuses)


def write(path: Path, text: str) -> None:
    """Replace the file with `text`, through a staged file that refuses a link.

    The staged `.tmp` is removed, created anew with `O_NOFOLLOW`, then renamed over the
    file, so nothing is written through a link a worker planted.
    """
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        # why: a skip added after a round keeps its cards; 0105-converge-switches D3
        if path.is_file() and uncleared(path.read_text(errors="replace")):
            raise Stop(
                f"{path} holds a checker's round not cleared:"
                " clearing it is the person's act"
            )
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(text)
        staged.replace(path)
    except OSError as error:
        raise Stop(f"{path.name} could not be written") from error


def main(argv: list[str] | None = None) -> int:
    """Write the stub for the file and round given; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write a skipped checker's findings file as a clean stub."
    )
    parser.add_argument("file", type=Path, help="the checker's findings file")
    parser.add_argument("round", help="the round the freeze judges")
    args = parser.parse_args(argv)
    try:
        role = role_of(args.file)
        round_ = round_of(args.round)
        head = _git("rev-parse", "HEAD")
        write(args.file, stub(args.file, role, round_, head))
    except Stop as stop:
        print(f"skip_stub: cannot stub — {stop}")
        return 2
    print(f"skip_stub: {args.file} at {head[:7]} · round {round_}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
