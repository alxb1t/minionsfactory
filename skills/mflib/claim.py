"""Write and read a ship run's claim: the conductor's start and pid, and its groups.

The kill of a group, the process table and what a stale claim means are the caller's.
Why: 0140-run-log design D1 and D2.
"""

import shutil
from pathlib import Path


def take(active: Path) -> None:
    """Make the claim's folder at once; a standing claim raises `FileExistsError`."""
    active.mkdir()


def present(active: Path) -> bool:
    """Return whether a claim stands."""
    return active.exists()


def mark(active: Path, start: str, pid: int) -> None:
    """Write the conductor's start time and pid into the claim."""
    (active / "start").write_text(start)
    (active / "pid").write_text(str(pid))


def conductor(active: Path) -> tuple[int, str] | None:
    """Return the claim's pid and its start time, stripped; None when either is unread.

    e.g. `pid` " 41 ", `start` "Sat Nov 21 10:00:00 2026 " → (41, "Sat Nov 21 …")
    """
    try:
        pid = int((active / "pid").read_text())
        start = (active / "start").read_text().strip()
    except (OSError, ValueError):
        return None
    return pid, start


def groups(active: Path) -> list[tuple[int, str]]:
    """Return each worker group's entry named by a decimal, and its start, stripped."""
    return [
        (int(entry.name), entry.read_text(errors="replace").strip())
        for entry in active.iterdir()
        if entry.is_file() and entry.name.isdecimal()
    ]


def enter(active: Path, pid: int, start: str) -> Path:
    """Write a worker group's entry, named by its leader's pid; return it."""
    entry = active / str(pid)
    entry.write_text(start)
    return entry


def leave(entry: Path) -> None:
    """Remove a worker group's entry, gone or not."""
    entry.unlink(missing_ok=True)


def remove(active: Path) -> None:
    """Remove the claim and every entry in it."""
    shutil.rmtree(active)
