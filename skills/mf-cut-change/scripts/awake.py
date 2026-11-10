# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Hold the Mac awake while a cut runs by hand, and release the hold.

Why: 0081-cut-awake design D1.
"""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 600
CAFFEINATE = "caffeinate"
HOLD_SECONDS = 7200
LAUNCHERS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "csh", "tcsh", "uv"}
CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")


class Stop(Exception):
    """End the run with the message it prints, and exit 2."""


def _record(change_id: str) -> Path:
    """Return the hold's record for `change_id`, beside the primary checkout.

    A git that fails outside "not a git repository" names its own error.
    Why: 0086-ship-fixes-3 design D6.
    """
    if not CHANGE_ID.fullmatch(change_id):
        raise Stop(f"awake: cannot run — not a change id: {change_id}")
    done = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if done.returncode != 0 and "not a git repository" in done.stderr:
        raise Stop("awake: cannot run — not in a git repository")
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(
            f"awake: cannot run — git rev-parse failed: {first};"
            f" run it as uv run --script {Path(__file__)}"
        )
    return Path(done.stdout.strip()).parent / ".minions" / "awake" / change_id


def _ps(field: str, pid: int) -> str:
    """Return `ps`'s `field` for `pid`, or "" when it names nothing."""
    done = subprocess.run(
        ["ps", "-o", f"{field}=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    return done.stdout.strip()


def _name(pid: int) -> str:
    """Return the process name of `pid`, e.g. `-zsh` → `zsh`, or "" when unknown."""
    return Path(_ps("comm", pid)).name.removeprefix("-")


def _host() -> int | None:
    """Return the nearest ancestor that is neither a shell nor `uv`, or None.

    Why `uv`: it parents the script and exits at once. Why: 0081-cut-awake design D1.
    """
    pid = os.getppid()
    while pid > 1:
        name = _name(pid)
        if not name:
            return None
        if name not in LAUNCHERS:
            return pid
        parent = _ps("ppid", pid)
        if not parent.isdigit():
            return None
        pid = int(parent)
    return None


def _release(record: Path) -> str:
    """Kill the recorded hold while it is a `caffeinate`; return the line to print."""
    if not record.is_file():
        return "awake: none held"
    text = record.read_text().strip()
    record.unlink()
    if text.isdigit() and int(text) > 1 and _name(int(text)) == CAFFEINATE:
        os.kill(int(text), signal.SIGTERM)
        return "awake: released"
    return "awake: none held"


def _start(record: Path) -> str:
    """Hold the machine awake and record the hold; return the line to print."""
    _release(record)
    found = shutil.which(CAFFEINATE)
    if found is None:
        return "awake: not held — caffeinate not on PATH"
    host = _host()
    if host is None:
        return "awake: not held — no host process"
    hold = subprocess.Popen(
        [found, "-is", "-t", str(HOLD_SECONDS), "-w", str(host)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(f"{hold.pid}\n")
    return "awake: held (2 h at most)"


def main(argv: list[str] | None = None) -> int:
    """Start or stop the hold for a change id; return the exit code."""
    parser = argparse.ArgumentParser(description="Hold the Mac awake for a cut.")
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument("change_id")
    args = parser.parse_args(argv)
    try:
        record = _record(args.change_id)
    except Stop as stop:
        print(stop)
        return 2
    print(_start(record) if args.action == "start" else _release(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
