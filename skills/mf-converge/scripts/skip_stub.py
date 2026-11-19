# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a skipped checker's findings file as a clean stub at `HEAD`.

skip_stub.py <findings-file> <round>
"""

import argparse
import errno
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.findings
import mflib.statefile

TIMEOUT_SECONDS = 600
ROLES = ("conformance", "adversarial")


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _today() -> date:
    """Return the local date."""
    return date.today()


def _git(*args: str, cwd: Path | None = None) -> str:
    """Return git's output for `args` in `cwd`, else the current directory, or stop."""
    done = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
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
    return mflib.findings.stub(
        role,
        path.parent.name,
        common.parent.name,
        _git("branch", "--show-current", cwd=cwd),
        head,
        _today().isoformat(),
        round_,
    )


def uncleared(text: str) -> bool:
    """Return whether a findings file holds a checker's round not yet cleared."""
    return mflib.findings.uncleared_skip_stub_legacy(text)


def write(path: Path, text: str) -> None:
    """Replace the file with `text` through a staged file; a link is refused."""
    try:
        # why: a skip added after a round keeps its cards; 0105-converge-switches D3
        if path.is_file() and uncleared(mflib.statefile.read(path)):
            raise Stop(
                f"{path} holds a checker's round not cleared:"
                " clearing it is the person's act"
            )
        mflib.statefile.write(path, text, refuse_link=True)
    except (OSError, mflib.statefile.WriteFailed) as failed:
        error = (
            failed.error if isinstance(failed, mflib.statefile.WriteFailed) else failed
        )
        if error.errno == errno.ELOOP:
            raise Stop(f"{path} is a link") from failed
        raise Stop(f"{path.name} could not be written") from failed


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
