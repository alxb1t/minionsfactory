"""Write a staged state file, and read a regular one, following no link.

Each argument holds a difference between the copies until they are fixed to one side.
Why: 0136-status-log design D1, D3, D4 and D5, and its differences.
"""

import contextlib
import errno
import os
import stat
from pathlib import Path
from typing import Literal

type Step = Literal["create", "replace"]
type Removal = Literal["any", "rename", "never"]


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
    remove: Removal,
    folder: int | None = None,
    mode: int = 0o644,
) -> None:
    """Replace `path` with `text` through `<name>.tmp`, cleared, made anew and renamed.

    `remove` names the failures that remove the staged file: `any`, a failed `rename`,
    or `never`. A link at `path` is a `replace` failure under `refuse_link`.
    """
    staged = path.with_name(f"{path.name}.tmp")
    if refuse_link:
        with contextlib.suppress(FileNotFoundError):
            held = os.stat(path, dir_fd=folder, follow_symlinks=False)
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
        if remove == "any" or (remove == "rename" and step == "replace"):
            with contextlib.suppress(OSError):
                os.unlink(staged, dir_fd=folder)
        raise WriteFailed(step, error) from error


def read_bytes(
    path: Path | str,
    *,
    folder: int | None = None,
    limit: int | None = None,
    tail: bool = False,
    guard: bool = True,
) -> bytes:
    """Return a file's bytes, read through one descriptor that follows no link.

    `limit` bounds the bytes, the last ones under `tail`. Under `guard` the open does
    not block, and a file that is no regular file raises `OSError` `EINVAL`.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | (os.O_NONBLOCK if guard else 0)
    fd = _open(Path(path), flags, folder)
    with os.fdopen(fd, "rb") as file:
        status = os.fstat(fd)
        if guard and not stat.S_ISREG(status.st_mode):
            raise OSError(errno.EINVAL, "it is not a file")
        if tail and limit is not None and status.st_size > limit:
            file.seek(status.st_size - limit)
        return file.read(limit)


def read(
    path: Path | str,
    *,
    folder: int | None = None,
    limit: int | None = None,
    tail: bool = False,
    guard: bool = True,
) -> str:
    """Return `read_bytes` of `path` as text, a bad byte replaced.

    e.g. the bytes 61 ff → "a�"
    """
    data = read_bytes(path, folder=folder, limit=limit, tail=tail, guard=guard)
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
