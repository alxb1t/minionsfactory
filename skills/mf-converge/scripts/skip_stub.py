# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a skipped checker's findings file as a clean stub at `HEAD`.

    skip_stub.py <findings-file> <round>

The file is `.minions/changes/<change-id>/conformance.md` or `adversarial.md`; the role
comes from its name, the plan from its folder. Run from the version's checkout: `head`
and `branch` are that checkout's. The stub holds every key of the findings contract,
`verdict: clean`, `mode: skipped`, `workers: 0`, and no card.
Prints `skip_stub: <path> at <short head> · round <round>`. Exit 0, or 2 with
`skip_stub: cannot stub — …` for a path that is a link or not of that form, a round
that is no positive integer, a directory with no repository, or an unwritable file.
e.g. `…/changes/0001-a/adversarial.md 2` → that file at `HEAD`, round 2
Why: 0105-converge-switches design D3.
"""

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROLES = ("conformance", "adversarial")
BODY = "Skipped by the plan: no worker judged this round."


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _today() -> date:
    """Return the local date."""
    return date.today()


def _git(*args: str) -> str:
    """Return git's output for `args` in the current directory, or stop."""
    done = subprocess.run(["git", *args], capture_output=True, text=True)
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


def stub(path: Path, role: str, round_: int, head: str) -> str:
    """Return the stub's text for `role` at `head`."""
    common = Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    keys = {
        "type": role,
        "plan": path.parent.name,
        "project": common.parent.name,
        "branch": _git("branch", "--show-current"),
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


def write(path: Path, text: str) -> None:
    """Replace the file with `text`, through a staged file that refuses a link.

    The staged `.tmp` is removed, created anew with `O_NOFOLLOW`, then renamed over the
    file, so nothing is written through a link a worker planted.
    """
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
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
