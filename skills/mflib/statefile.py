"""Write a staged state file, append to one, read a regular one, open a folder: no link.

Why: 0136-status-log design D1, D4 and D5; 0140-run-log design D6; 0142-models D13.
"""

import contextlib
import errno
import os
import stat
from collections.abc import Iterator
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
        with os.fdopen(
            _open(staged, flags, folder, mode), "w", encoding="utf-8"
        ) as file:
            file.write(text)
        step = "replace"
        os.replace(staged, path, src_dir_fd=folder, dst_dir_fd=folder)
    except OSError as error:
        with contextlib.suppress(OSError):
            os.unlink(staged, dir_fd=folder)
        raise WriteFailed(step, error) from error


def write_or_say(path: Path, text: str) -> str | None:
    """Replace `path` with `text` through a staged write refusing a link; say a failure.

    e.g. a link at "a.md" → "a.md is a link"; a full disk → "a.md: No space left"
    """
    try:
        write(path, text, refuse_link=True)
    except WriteFailed as failed:
        if failed.error.errno == errno.ELOOP:
            return f"{path} is a link"
        return f"{path}: {failed.error.strerror}"
    return None


def _regular(
    path: Path | str, flags: int, folder: int | None, *, one_name: bool = False
) -> int:
    """Return a descriptor on a regular file, opened with `flags` through no link.

    The open does not block. A file that is no regular file, or under `one_name` one
    with a second name, a hard link, raises `OSError` `EINVAL`.
    """
    fd = _open(Path(path), flags | os.O_NOFOLLOW | os.O_NONBLOCK, folder)
    held = os.fstat(fd)
    if not stat.S_ISREG(held.st_mode):
        os.close(fd)
        raise OSError(errno.EINVAL, "it is not a file")
    if one_name and held.st_nlink != 1:
        os.close(fd)
        raise OSError(errno.EINVAL, "it is not a file of one name")
    return fd


def open_regular(
    path: Path | str, folder: int | None = None, *, one_name: bool = False
) -> int:
    """Return a descriptor to read a regular file through, following no link."""
    return _regular(path, os.O_RDONLY, folder, one_name=one_name)


def append(
    path: Path | str, text: str, folder: int | None = None, *, one_name: bool = False
) -> None:
    """Append `text` to a regular file in one write, following no link.

    The file must stand: the open makes nothing, and does not block.
    """
    fd = _regular(path, os.O_WRONLY | os.O_APPEND, folder, one_name=one_name)
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


def lines(path: Path | str, cut: int) -> Iterator[str]:
    """Yield a regular file's lines one at a time, each cut at `cut` characters.

    The whole file is streamed, so one line is held; a long line's rest is dropped.
    A link, a pipe, a folder or a missing file yields no line. Why: 0161-viewer D4, D30.
    """
    try:
        fd = open_regular(path)
    except OSError:
        return
    with os.fdopen(fd, encoding="utf-8", errors="replace") as file:
        while piece := file.readline(cut):
            if not piece.endswith("\n") and len(piece) == cut:
                while (rest := file.readline(cut)) and not rest.endswith("\n"):
                    pass
            yield piece.rstrip("\n")


def folder(root: Path, *parts: str, mode: int = 0o777) -> int:
    """Return a descriptor on `root`'s folder `parts`, each made, none read as a link.

    A link at any of `parts` raises `OSError`; `root` itself is followed. `mode` is
    the mode of `root` and of each part it makes; `root`'s parents take the default.
    """
    root.mkdir(mode=mode, parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            with contextlib.suppress(FileExistsError):
                os.mkdir(part, mode, dir_fd=fd)
            inner = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = inner
    except BaseException:
        os.close(fd)
        raise
    return fd


def touch(path: Path | str, folder: int, mode: int) -> None:
    """Make an empty file by its name in the folder `folder` holds, of mode `mode`.

    A file that stands is left as it is. The open follows no link and does not
    block, so a link raises `ELOOP` and a FIFO with no reader `ENXIO`.
    """
    flags = os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    os.close(os.open(path, flags, mode, dir_fd=folder))


def open_folder(root: Path, *parts: str) -> int:
    """Return a descriptor on `root`'s folder `parts`, none made, none read as a link.

    `root` is followed. A missing part raises `FileNotFoundError`, a link `OSError`
    `ELOOP` and a file `NotADirectoryError`. Why: 0142-models design D13.
    """
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            try:
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                inner = os.open(part, flags, dir_fd=fd)
            except OSError as error:
                if error.errno not in (errno.ELOOP, errno.ENOTDIR):
                    raise
                # why: Linux says ENOTDIR for a link under O_DIRECTORY, macOS ELOOP
                held = os.stat(part, dir_fd=fd, follow_symlinks=False)
                code = errno.ELOOP if stat.S_ISLNK(held.st_mode) else errno.ENOTDIR
                raise OSError(code, os.strerror(code), part) from None
            os.close(fd)
            fd = inner
    except BaseException:
        os.close(fd)
        raise
    return fd
