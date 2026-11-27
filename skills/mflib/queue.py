"""Read and write the home queue: its entries, lock, requests and records.

Why: 0156-queue design D1 to D5 and D7.
"""

import contextlib
import errno
import fcntl
import json
import os
import re
import stat
import types
import typing
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, NotRequired, TypedDict, TypeGuard

from . import layout, statefile

CHANGE_ID = re.compile(r"(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)")
UNREADABLE = {"halt": "the queue entry is unreadable"}
BOUND_ENTRY = 262144
BOUND_RECORD = 65536
_REJOIN = "rejoin"
_ALL = "all"


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
_TYPES = typing.get_type_hints(Entry)


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


def is_wait(entry: Mapping[str, object]) -> bool:
    """Return whether `entry` waits for room under the cap: a non-empty `waits`.

    e.g. {"waits": "1 in flight, cap 1"} → True; {"waits": ""} → False
    """
    waits = entry.get("waits")
    return isinstance(waits, str) and bool(waits)


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


@contextlib.contextmanager
def _opened(folder: Path) -> Iterator[int | None]:
    """Yield a descriptor on `folder`, opened through no link at its last part.

    A folder that cannot be opened yields None.
    """
    try:
        fd = statefile.open_folder(folder.parent, folder.name)
    except OSError:
        yield None
        return
    try:
        yield fd
    finally:
        os.close(fd)


def _names(folder: Path, *, unlink: bool) -> list[str]:
    """Return the names in `folder`, opened through no link at its last part, sorted.

    Under `unlink` each is removed, and only the names removed come back. A folder
    that cannot be opened or listed holds none.
    """
    with _opened(folder) as fd:
        if fd is None:
            return []
        try:
            names = sorted(os.listdir(fd))
        except OSError:
            return []
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


def _bounded(name: str, folder: int, bound: int) -> str:
    """Return the file `name` under `folder` as text, decoded strictly.

    A file that is no regular file, a bad byte, or past `bound` raises `ValueError`.
    """
    try:
        data = statefile.read_bytes(name, folder=folder, limit=bound + 1)
    except OSError as error:
        raise ValueError(name) from error
    if len(data) > bound:
        raise ValueError(name)
    return data.decode()


def _fits(value: object, hint: object) -> bool:
    """Return whether `value`, read from JSON, is of the record's type `hint`.

    e.g. ["a"], list[str] → True; None, str → False
    """
    if hint is type(None):
        return value is None
    if typing.get_origin(hint) is types.UnionType:
        return any(_fits(value, arg) for arg in typing.get_args(hint))
    if typing.get_origin(hint) is list:
        (item,) = typing.get_args(hint)
        return isinstance(value, list) and all(_fits(each, item) for each in value)
    return isinstance(hint, type) and isinstance(value, hint)


def _typed(entry: object) -> TypeGuard[dict[str, Any]]:
    """Return whether `entry` is an `Entry`: each required key, each value its type."""
    if not isinstance(entry, dict) or not entry.keys() >= REQUIRED:
        return False
    return all(_fits(entry[key], hint) for key, hint in _TYPES.items() if key in entry)


def entries(primary: Path) -> dict[str, dict[str, Any]]:
    """Return each queued cut's entry by its id, in id order.

    A name that is no change id is skipped. An entry that cannot be read as an
    `Entry` is a copy of `UNREADABLE`. Why: 0156-queue design D3.
    """
    folder = layout.queue_cuts(primary)
    found: dict[str, dict[str, Any]] = {}
    with _opened(folder) as fd:
        if fd is None:
            return found
        try:
            names = sorted(os.listdir(fd))
        except OSError:
            return found
        for name in (name for name in names if CHANGE_ID.fullmatch(name)):
            try:
                entry = json.loads(_bounded(name, fd, BOUND_ENTRY))
            except (ValueError, RecursionError):
                entry = None
            found[name] = entry if _typed(entry) else dict(UNREADABLE)
    return found


def _staged(folder: Path, name: str, text: str) -> None:
    """Write `text` to `folder`'s file `name`, staged, 0600, following no link.

    `folder` alone is made, 0700. A failure raises `Unwritten`. Why: 0156-queue D4.
    """
    path = folder / name
    try:
        with contextlib.suppress(FileExistsError):
            folder.mkdir(mode=0o700)
        fd = statefile.open_folder(folder.parent, folder.name)
    except OSError as error:
        raise Unwritten(path, error) from None
    try:
        statefile.write(Path(name), text, folder=fd, mode=0o600)
    except statefile.WriteFailed as failed:
        raise Unwritten(path, failed.error) from None
    finally:
        os.close(fd)


def write(primary: Path, change: str, entry: Mapping[str, object]) -> None:
    """Write a queued cut's entry whole, compact JSON; one over its bound is refused.

    A failure raises `Unwritten`, and the entry that stands is left.
    """
    folder = layout.queue_cuts(primary)
    text = json.dumps(entry)
    if len(text.encode()) > BOUND_ENTRY:
        big = OSError(errno.EFBIG, os.strerror(errno.EFBIG))
        raise Unwritten(folder / change, big)
    _staged(folder, change, text)


def remove(primary: Path, change: str) -> None:
    """Remove a queued cut's entry; a missing one raises `FileNotFoundError`."""
    (layout.queue_cuts(primary) / change).unlink()


def _is_request(name: str) -> bool:
    """Return whether `name` names a request: a change id, or `all`."""
    return name == _ALL or bool(CHANGE_ID.fullmatch(name))


def request(primary: Path, name: str) -> None:
    """Write the rejoin request `name` for the live run, an empty file, 0600.

    The folder is made with its parents, 0700; no link is followed, and a failure
    raises `Unwritten`. Why: 0156-queue design D5.
    """
    folder = layout.queue_rejoin(primary)
    try:
        fd = statefile.folder(
            folder.parent.parent, folder.parent.name, folder.name, mode=0o700
        )
    except OSError as error:
        raise Unwritten(folder / name, error) from None
    try:
        statefile.touch(name, fd, 0o600)
    except OSError as error:
        raise Unwritten(folder / name, error) from None
    finally:
        os.close(fd)


def requests(queue: Path) -> set[str]:
    """Remove every name in the queue folder `queue`'s requests; return the requests.

    A name that is no change id and not `all` is removed and left out.
    Why: 0063-rejoin design D2; 0156-queue design D5.
    """
    return {name for name in _names(queue / _REJOIN, unlink=True) if _is_request(name)}


def requested(queue: Path) -> bool:
    """Return whether the queue folder `queue` holds a request: a regular file so named.

    Read through the folder's descriptor, as `requests` removes, following no link.
    """
    with _opened(queue / _REJOIN) as fd:
        if fd is None:
            return False
        try:
            return any(
                stat.S_ISREG(os.lstat(name, dir_fd=fd).st_mode)
                for name in os.listdir(fd)
                if _is_request(name)
            )
        except OSError:
            return False


def _record(folder: Path, change: str) -> str | None:
    """Return `folder`'s record `change`, stripped; or None when it cannot be read.

    Why: 0156-queue design D3.
    """
    with _opened(folder) as fd:
        if fd is None:
            return None
        try:
            return _bounded(change, fd, BOUND_RECORD).strip()
        except ValueError:
            return None


def brief(primary: Path, change: str) -> str | None:
    """Return the brief path a passed cut recorded for `change`, stripped; or None.

    An empty record, or one that cannot be read, is none.
    Why: 0090-supervisor-merge design D1.
    """
    return _record(layout.queue_briefs(primary), change) or None


def write_brief(primary: Path, change: str, path: str) -> None:
    """Record the brief path `path` a passed cut of `change` was cut from."""
    _staged(layout.queue_briefs(primary), change, f"{path}\n")


def merge_tried(primary: Path, change: str, merge: str) -> bool:
    """Return whether a supervisor was spawned on `change`'s open merge `merge`.

    The record is read stripped and must equal `merge` whole.
    Why: 0090-supervisor-merge design D2.
    """
    return _record(layout.queue_supervised(primary), change) == merge


def write_supervised(primary: Path, change: str, merge: str) -> None:
    """Record that a supervisor is spawned on `change`'s open merge `merge`."""
    _staged(layout.queue_supervised(primary), change, f"{merge}\n")
