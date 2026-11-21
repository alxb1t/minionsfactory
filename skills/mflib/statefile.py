"""Write a staged state file, append to one, and read a regular one, following no link.

Why: 0136-status-log design D1, D4 and D5; 0140-run-log design D6.
"""

import contextlib
import errno
import os
import stat
from pathlib import Path
from typing import Literal

type Step = Literal["create", "replace"]


class WriteFailed(Exception):
    """Say which step of a staged write failed, `create` or `replace`, and its error."""

    def __init__(self, step: Step, error: OSError) -> None:
        """Hold the step and the `OSError` it raised."""
        super().__init__(step, error)
        self.step: Step = step
        self.error = error


def _open(path: Path, flags: int, folder: int | None, mode: int = 0o777) -> int:
    """Return a descriptor on `path`, relative to the folder `folder` holds if given."""
    if folder is None:
        return os.open(path, flags, mode)
    return os.open(path, flags, mode, dir_fd=folder)


def write(
    path: Path,
    text: str,
    *,
    refuse_link: bool = False,
    folder: int | None = None,
    mode: int = 0o644,
) -> None:
    """Replace `path` with `text` through `<name>.tmp`, cleared, made anew and renamed.

    A failure removes the staged file. A link at `path` is a `replace` failure under
    `refuse_link`, and any other error of its check a `create` failure.
    """
    staged = path.with_name(f"{path.name}.tmp")
    if refuse_link:
        try:
            held = os.stat(path, dir_fd=folder, follow_symlinks=False)
        except FileNotFoundError:
            pass
        except OSError as error:
            # why: the callers word `WriteFailed` alone; 0136-status-log card S1
            raise WriteFailed("create", error) from error
        else:
            if stat.S_ISLNK(held.st_mode):
                link = OSError(errno.ELOOP, os.strerror(errno.ELOOP), str(path))
                raise WriteFailed("replace", link)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    step: Step = "create"
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(staged, dir_fd=folder)
        with os.fdopen(_open(staged, flags, folder, mode), "w") as file:
            file.write(text)
        step = "replace"
        os.replace(staged, path, src_dir_fd=folder, dst_dir_fd=folder)
    except OSError as error:
        with contextlib.suppress(OSError):
            os.unlink(staged, dir_fd=folder)
        raise WriteFailed(step, error) from error


def _regular(path: Path | str, flags: int, folder: int | None) -> int:
    """Return a descriptor on a regular file, opened with `flags` through no link.

    The open does not block. A file that is no regular file raises `OSError` `EINVAL`.
    """
    fd = _open(Path(path), flags | os.O_NOFOLLOW | os.O_NONBLOCK, folder)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError(errno.EINVAL, "it is not a file")
    return fd


def open_regular(path: Path | str, folder: int | None = None) -> int:
    """Return a descriptor to read a regular file through, following no link."""
    return _regular(path, os.O_RDONLY, folder)


def append(path: Path | str, text: str, folder: int | None = None) -> None:
    """Append `text` to a regular file in one write, following no link.

    The file must stand: the open makes nothing, and does not block.
    """
    fd = _regular(path, os.O_WRONLY | os.O_APPEND, folder)
    try:
        os.write(fd, text.encode())
    finally:
        os.close(fd)


def read_bytes(
    path: Path | str,
    *,
    folder: int | None = None,
    limit: int | None = None,
    tail: bool = False,
    offset: int = 0,
) -> bytes:
    """Return a file's bytes from `offset`, read through one descriptor and no link.

    `limit` bounds the bytes, the last ones under `tail`. The open does not block, and
    a file that is no regular file raises `OSError` `EINVAL`.
    """
    fd = open_regular(path, folder)
    with os.fdopen(fd, "rb") as file:
        size = os.fstat(fd).st_size
        if tail and limit is not None:
            offset = max(offset, size - limit)
        file.seek(offset)
        return file.read(limit)


def read(
    path: Path | str,
    *,
    folder: int | None = None,
    limit: int | None = None,
    tail: bool = False,
    offset: int = 0,
) -> str:
    """Return `read_bytes` of `path` as text, a bad byte replaced.

    e.g. the bytes 61 ff → "a�"
    """
    data = read_bytes(path, folder=folder, limit=limit, tail=tail, offset=offset)
    return data.decode(errors="replace")


def folder(root: Path, *parts: str) -> int:
    """Return a descriptor on `root`'s folder `parts`, each made, none read as a link.

    A link at any of `parts` raises `OSError`; `root` itself is followed.
    """
    root.mkdir(parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            with contextlib.suppress(FileExistsError):
                os.mkdir(part, dir_fd=fd)
            inner = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = inner
    except BaseException:
        os.close(fd)
        raise
    return fd
