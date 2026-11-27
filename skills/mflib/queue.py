"""Read and write the home queue: its entries, lock, requests and records.

Why: 0156-queue design D1, D2, D5 and D7.
"""

import contextlib
import fcntl
import json
import os
import re
import stat
import tempfile
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from . import layout, statefile

CHANGE_ID = re.compile(r"(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)")
UNREADABLE = {"halt": "the queue entry is unreadable"}
_REJOIN = "rejoin"


class Entry(TypedDict):
    """Hold a queued cut's keys and types; the keys from `dependencies` on are optional.

    Why: 0156-queue design D2.
    """

    bump: str
    brief: str
    executor: str
    after: list[str]
    halt: str | None
    model: str | None
    effort: str | None
    dependencies: NotRequired[list[list[str]]]
    models: NotRequired[str | None]
    beside: NotRequired[list[str]]
    waits: NotRequired[str]


REQUIRED = Entry.__required_keys__


class Refused(OSError):
    """Say the home folder refused the queue's lock; `strerror` holds the error's."""


class Unwritten(OSError):
    """Say a queue write failed, naming its file and the cause's error."""

    def __init__(self, path: Path, cause: OSError) -> None:
        """Hold the file as `filename` and the cause's `errno` and `strerror`."""
        super().__init__(cause.errno, cause.strerror, str(path))
        self.cause = cause


def halted_text(name: str) -> str:
    """Return the halt of a queued cut that waits on `name`, cut-halted.

    e.g. "0001-a" → "after 0001-a is cut-halted"
    """
    return f"after {name} is cut-halted"


@contextlib.contextmanager
def lock(primary: Path) -> Iterator[None]:
    """Hold the queue's lock, blocking; the kernel drops it when its process ends.

    A folder or lock that cannot be made raises `Refused`.
    Why: 0082-cut-station design D2.
    """
    path = layout.queue_lock(primary)
    try:
        for folder in (path.parent.parent, path.parent):
            folder.mkdir(mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    except OSError as error:
        raise Refused(error.errno, error.strerror) from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _names(folder: Path, *, unlink: bool) -> list[str]:
    """Return the names in `folder`, opened through no link at its last part, sorted.

    Under `unlink` each is removed, and only the names removed come back. A folder
    that cannot be opened or listed holds none.
    """
    try:
        fd = statefile.open_folder(folder.parent, folder.name)
    except OSError:
        return []
    try:
        names = sorted(os.listdir(fd))
        if not unlink:
            return names
        removed = []
        for name in names:
            try:
                os.unlink(name, dir_fd=fd)
            except OSError:
                continue
            removed.append(name)
        return removed
    except OSError:
        return []
    finally:
        os.close(fd)


def entries(primary: Path) -> dict[str, dict[str, Any]]:
    """Return each queued cut's entry by its id, in id order.

    A name that is no change id is skipped. An entry that is no JSON object, or
    lacks a key of `REQUIRED`, is a copy of `UNREADABLE`.
    """
    folder = layout.queue_cuts(primary)
    found: dict[str, dict[str, Any]] = {}
    for name in _names(folder, unlink=False):
        if not CHANGE_ID.fullmatch(name):
            continue
        try:
            entry = json.loads((folder / name).read_text())
        except (OSError, ValueError):
            entry = None
        if not isinstance(entry, dict) or not entry.keys() >= REQUIRED:
            entry = dict(UNREADABLE)
        found[name] = entry
    return found


def write(primary: Path, change: str, entry: Mapping[str, object]) -> None:
    """Write a queued cut's entry whole: to a temporary name, then moved in."""
    folder = layout.queue_cuts(primary)
    folder.mkdir(mode=0o700, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=folder, prefix=".")
    with os.fdopen(fd, "w") as file:
        json.dump(entry, file)
    os.replace(temp, folder / change)


def remove(primary: Path, change: str) -> None:
    """Remove a queued cut's entry; a missing one raises `FileNotFoundError`."""
    (layout.queue_cuts(primary) / change).unlink()


def request(primary: Path, name: str) -> None:
    """Write the rejoin request `name` for the live run, in the queue."""
    folder = layout.queue_rejoin(primary)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    (folder / name).touch()


def requests(queue: Path) -> set[str]:
    """Remove the rejoin requests in the queue folder `queue`; return their names.

    Why: 0063-rejoin design D2.
    """
    return set(_names(queue / _REJOIN, unlink=True))


def requested(queue: Path) -> bool:
    """Return whether the queue folder `queue` holds a request: a regular file.

    Read through the folder's descriptor, as `requests` removes, following no link.
    """
    try:
        fd = statefile.open_folder(queue, _REJOIN)
    except OSError:
        return False
    try:
        return any(
            stat.S_ISREG(os.lstat(name, dir_fd=fd).st_mode) for name in os.listdir(fd)
        )
    except OSError:
        return False
    finally:
        os.close(fd)


def brief(primary: Path, change: str) -> str | None:
    """Return the brief path a passed cut recorded for `change`, stripped; or None.

    An empty record, or one that cannot be read, is none.
    Why: 0090-supervisor-merge design D1.
    """
    try:
        named = (layout.queue_briefs(primary) / change).read_text().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return named or None


def write_brief(primary: Path, change: str, path: str) -> None:
    """Record the brief path `path` a passed cut of `change` was cut from."""
    folder = layout.queue_briefs(primary)
    folder.mkdir(mode=0o700, exist_ok=True)
    (folder / change).write_text(f"{path}\n")


def merge_tried(primary: Path, change: str, merge: str) -> bool:
    """Return whether a supervisor was spawned on `change`'s open merge `merge`.

    The record is read stripped and must equal `merge` whole.
    Why: 0090-supervisor-merge design D2.
    """
    try:
        record = layout.queue_supervised(primary) / change
        return record.read_text().strip() == merge
    except (OSError, UnicodeDecodeError):
        return False


def write_supervised(primary: Path, change: str, merge: str) -> None:
    """Record that a supervisor is spawned on `change`'s open merge `merge`."""
    folder = layout.queue_supervised(primary)
    folder.mkdir(mode=0o700, exist_ok=True)
    (folder / change).write_text(f"{merge}\n")
