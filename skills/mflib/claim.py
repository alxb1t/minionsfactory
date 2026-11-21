"""Write and read a ship run's claim: the conductor's start and pid, and its groups.

The kill of a group, the process table and what a stale claim means are the caller's.
Why: 0140-run-log design D1 and D9.
"""

import contextlib
import errno
import os
import shutil
from pathlib import Path

from . import statefile

# The most bytes read of one entry. Why: 0140-run-log design D9.
BOUND = 4096


class Refused(Exception):
    """Say the claim is no folder: a link or a file stands at its name."""

    def __init__(self, path: Path) -> None:
        """Hold the claim's path."""
        super().__init__(f"{path} is no folder")
        self.path = path


def _open(active: Path) -> int | None:
    """Return a descriptor on the claim folder, never made; None when none stands.

    A link or a file at the claim raises `Refused`.
    """
    if not active.parent.is_dir():
        return None
    try:
        return statefile.open_folder(active.parent, active.name)
    except FileNotFoundError:
        return None
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise Refused(active) from None
        raise


def _entry(fd: int, name: str) -> str | None:
    """Return an entry's text, a bad byte replaced; None over the bound or unread."""
    try:
        data = statefile.read_bytes(name, folder=fd, limit=BOUND + 1)
    except OSError:
        return None
    return None if len(data) > BOUND else data.decode(errors="replace")


def take(active: Path) -> None:
    """Make the claim's folder at once; what stands there raises `FileExistsError`."""
    parent = statefile.folder(active.parent)
    try:
        os.mkdir(active.name, dir_fd=parent)
    finally:
        os.close(parent)


def present(active: Path) -> bool:
    """Return whether anything stands at the claim's name, a link included."""
    return os.path.lexists(active)


def mark(active: Path, start: str, pid: int) -> None:
    """Write the conductor's start time and pid into the claim."""
    for name, text in (("start", start), ("pid", str(pid))):
        _write(active, name, text)


def _write(active: Path, name: str, text: str) -> None:
    """Write `text` to the claim's entry `name`, under the claim's descriptor.

    No claim raises `FileNotFoundError`; a failed write raises `WriteFailed`.
    """
    if (fd := _open(active)) is None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(active))
    try:
        statefile.write(Path(name), text, refuse_link=True, folder=fd)
    finally:
        os.close(fd)


def conductor(active: Path) -> tuple[int, str] | None:
    """Return the claim's pid and its start time, stripped; None when either is unread.

    e.g. `pid` " 41 ", `start` "Sat Nov 21 10:00:00 2026 " → (41, "Sat Nov 21 …")
    """
    if (fd := _open(active)) is None:
        return None
    try:
        pid, start = _entry(fd, "pid"), _entry(fd, "start")
    finally:
        os.close(fd)
    if pid is None or start is None:
        return None
    try:
        return int(pid), start.strip()
    except ValueError:
        return None


def groups(active: Path) -> list[tuple[int, str]]:
    """Return each worker group's entry named by a decimal, and its start, stripped.

    An entry over the bound, a folder, a link or a pipe is passed over.
    """
    if (fd := _open(active)) is None:
        return []
    try:
        held = [
            (int(name), text.strip())
            for name in os.listdir(fd)
            if name.isdecimal() and (text := _entry(fd, name)) is not None
        ]
    finally:
        os.close(fd)
    return held


def enter(active: Path, pid: int, start: str) -> Path:
    """Write a worker group's entry, named by its leader's pid; return it."""
    _write(active, str(pid), start)
    return active / str(pid)


def leave(entry: Path) -> None:
    """Remove a worker group's entry, gone or not, under the claim's descriptor."""
    if (fd := _open(entry.parent)) is None:
        return
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(entry.name, dir_fd=fd)
    finally:
        os.close(fd)


def remove(active: Path) -> None:
    """Remove the claim and every entry in it; no claim raises `FileNotFoundError`."""
    if (fd := _open(active)) is None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(active))
    os.close(fd)
    parent = statefile.folder(active.parent)
    try:
        shutil.rmtree(active.name, dir_fd=parent)
    finally:
        os.close(parent)
