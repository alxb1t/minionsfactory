"""Write, read, list and remove the conductor's kept files in the home folder.

The kept origin, `.default`, the offline base, the release ledger, the gate approval,
the live mark, `repos`, the probe mark, the pin's files and `ship.toml`.
"""

import contextlib
import errno
import json
import os
import re
import stat
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from . import layout, statefile

type Urls = tuple[list[str], list[str]]

# Why: 0159-kept design D1, D2 and D5 to D8; 0160-pins design D1.
BOUND = 65536
REPOS_BOUND = 262144

# Why: 0159-kept design D10.
_SHA = re.compile("[0-9a-f]{40}")
_NOT_A_FILE = "it is not a file"
_PHRASES = {errno.ELOOP: _NOT_A_FILE, errno.EINVAL: _NOT_A_FILE}


class Heads(NamedTuple):
    """Hold the release ledger's heads, and the entries that are no head."""

    heads: set[str]
    bad: list[str]


class Refused(OSError):
    """Say a kept folder cannot be made or opened; `strerror` holds the error's."""

    def __init__(self, cause: OSError) -> None:
        """Hold the cause's `errno` and `strerror`, and the cause."""
        super().__init__(cause.errno, cause.strerror)
        self.cause = cause


class Unwritten(OSError):
    """Say a write of a kept file failed, naming the file and the cause's error."""

    def __init__(self, path: Path, cause: OSError) -> None:
        """Hold the file as `filename`, the cause's error, and the cause."""
        super().__init__(cause.errno, cause.strerror, str(path))
        self.cause = cause


class Broken(OSError):
    """Say a file cannot be read, holding its `path` and the `phrase` that says why."""

    def __init__(self, path: Path, phrase: str) -> None:
        """Hold the text a halt line names, worded by where `path` lies.

        Under the kept folder: `~/.mf-ship-origin/<name> cannot be read: <phrase>`.
        Elsewhere: `<path>: <phrase>`.
        """
        self.path = path
        self.phrase = phrase
        try:
            name = path.relative_to(layout.kept_dir())
        except ValueError:
            self.text = f"{path}: {phrase}"
        else:
            self.text = f"~/{layout.KEPT_ORIGINS}/{name} cannot be read: {phrase}"
        super().__init__(errno.EINVAL, self.text, str(path))

    def __str__(self) -> str:
        """Return the text, as a halt line names it."""
        return self.text


def _read(file: Path, bound: int = BOUND) -> str | None:
    """Return a kept file's text, read through no link and without blocking.

    A missing name is None. A name that is no regular file, a file over `bound`
    bytes or one not UTF-8 raises `Broken`. Why: 0159-kept design D6.
    """
    try:
        data = statefile.read_bytes(file, limit=bound + 1)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Broken(file, _PHRASES.get(error.errno, str(error.strerror))) from None
    if len(data) > bound:
        raise Broken(file, f"it is over {bound} bytes")
    try:
        return data.decode()
    except UnicodeDecodeError:
        raise Broken(file, "it is not text") from None


def _parts(file: Path) -> tuple[str, ...]:
    """Return the folder `file` sits in, as parts under the kept folder.

    e.g. `~/.mf-ship-origin/live/<digest>` → ("live",); `~/.mf-ship-origin/repos` → ()
    """
    return () if file.parent == layout.kept_dir() else (file.parent.name,)


def _folder(file: Path) -> int:
    """Return a descriptor on `file`'s folder, made at 0700; a failure is `Refused`."""
    try:
        return statefile.folder(layout.kept_dir(), *_parts(file), mode=0o700)
    except OSError as error:
        raise Refused(error) from None


def _write(file: Path, text: str, folder: int) -> None:
    """Replace `file` in the folder `folder` holds, staged at 0600; else `Unwritten`."""
    try:
        statefile.write(Path(file.name), text, folder=folder, mode=0o600)
    except statefile.WriteFailed as failed:
        raise Unwritten(file, failed.error) from None


def _replace(file: Path, text: str) -> None:
    """Replace `file` with `text`, staged at 0600, its folder made at 0700."""
    fd = _folder(file)
    try:
        _write(file, text, fd)
    finally:
        os.close(fd)


def _once(file: Path, text: str) -> None:
    """Write `file` once, staged at 0600: a name of any kind that stands is left.

    A file at the kept folder's name writes nothing. Why: 0159-kept design D8.
    """
    try:
        fd = _folder(file)
    except Refused as refused:
        if isinstance(refused.cause, FileExistsError):
            return
        raise
    try:
        try:
            os.stat(file.name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            _write(file, text, fd)
    finally:
        os.close(fd)


def _remove(file: Path) -> None:
    """Remove `file` by name under its folder's descriptor; a gone one is quiet.

    A folder that cannot be opened removes nothing.
    """
    try:
        fd = statefile.open_folder(layout.kept_dir(), *_parts(file))
    except OSError:
        return
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file.name, dir_fd=fd)
    finally:
        os.close(fd)


def _stands(file: Path) -> bool:
    """Return whether a regular file stands at `file`; any other name is `Broken`."""
    try:
        held = os.lstat(file)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise Broken(file, str(error.strerror)) from None
    if not stat.S_ISREG(held.st_mode):
        raise Broken(file, _NOT_A_FILE)
    return True


def _urls(text: str) -> Urls | None:
    """Return `text` read as a pair of lists of strings, or None for another shape."""
    try:
        urls = json.loads(text)
    except ValueError:
        return None
    if not (isinstance(urls, list) and len(urls) == 2):
        return None
    fetch, push = urls
    for side in (fetch, push):
        if not (isinstance(side, list) and all(isinstance(url, str) for url in side)):
            return None
    return fetch, push


def origin(primary: Path) -> Urls | None:
    """Return the URLs a run kept for `primary`, or None before its first."""
    file = layout.kept_file(primary)
    text = _read(file)
    if text is None:
        return None
    if (urls := _urls(text)) is None:
        raise Broken(file, "it is not a pair of URL lists")
    return urls


def origin_stands(primary: Path) -> bool:
    """Return whether a kept origin stands for `primary`."""
    return _stands(layout.kept_file(primary))


def keep_origin(primary: Path, urls: Urls) -> None:
    """Keep `urls` as `primary`'s origin, once: a name that stands is left.

    Text over `BOUND` bytes is `Unwritten`, as `origin` could not read it back.
    Why: 0053-sandbox-patch design D2.
    """
    file = layout.kept_file(primary)
    text = json.dumps(urls)
    if len(text.encode()) > BOUND:
        raise Unwritten(file, OSError(errno.EFBIG, f"it is over {BOUND} bytes"))
    _once(file, text)


def default(primary: Path) -> str | None:
    """Return the default branch a run kept, stripped, or None."""
    text = _read(layout.default_file(primary))
    return None if text is None else text.strip()


def default_stands(primary: Path) -> bool:
    """Return whether a name of any kind stands at the kept default branch."""
    try:
        os.lstat(layout.default_file(primary))
    except FileNotFoundError:
        return False
    return True


def keep_default(primary: Path, name: str) -> None:
    """Keep `name` as `primary`'s default branch, once: a name that stands is left.

    Why: 0159-kept design D12.
    """
    _once(layout.default_file(primary), f"{name}\n")


def base(primary: Path) -> str | None:
    """Return the offline base's sha, or None when none stands or it is blank."""
    file = layout.pushed_file(primary)
    sha = (_read(file) or "").strip()
    if not sha:
        return None
    if not _SHA.fullmatch(sha):
        raise Broken(file, "it is not a commit id")
    return sha


def base_stands(primary: Path) -> bool:
    """Return whether an offline base stands for `primary`."""
    return _stands(layout.pushed_file(primary))


def keep_base(primary: Path, sha: str) -> None:
    """Keep `sha` as the offline base, over an older one."""
    _replace(layout.pushed_file(primary), f"{sha}\n")


def record_release(primary: Path, change: str, head: str) -> None:
    """Record `head` as the change's in the release ledger, over an older entry."""
    _replace(layout.released_dir(primary) / change, f"{head}\n")


def release_entries(primary: Path) -> list[Path]:
    """Return every name in the release ledger's folder; none with no folder.

    A folder that cannot be opened, a link among them, lists none.
    """
    folder = layout.released_dir(primary)
    try:
        fd = statefile.open_folder(layout.kept_dir(), folder.name)
    except OSError:
        return []
    try:
        return [folder / name for name in os.listdir(fd)]
    finally:
        os.close(fd)


def _head(entry: Path) -> str | None:
    """Return the commit id a ledger entry holds, its whole text stripped, or None."""
    try:
        sha = (_read(entry) or "").strip()
    except Broken:
        return None
    return sha if _SHA.fullmatch(sha) else None


def release_heads(primary: Path) -> Heads:
    """Return the heads the release ledger holds, and the entries that hold none.

    Why: 0159-kept design D10.
    """
    heads: set[str] = set()
    bad: list[str] = []
    for entry in release_entries(primary):
        if (head := _head(entry)) is None:
            bad.append(entry.name)
        else:
            heads.add(head)
    return Heads(heads, sorted(bad))


def close_releases(primary: Path, landed: Callable[[str], bool]) -> None:
    """Remove each ledger entry whose head `landed` says is on the default branch.

    An entry that holds no head stays. Why: 0053-sandbox-patch design D2.
    """
    for entry in release_entries(primary):
        if (head := _head(entry)) is not None and landed(head):
            _remove(entry)


def approve(primary: Path, change: str, hashed: str) -> None:
    """Record `hashed` as a person's approval of the change's gate, over an older one.

    Why: 0060-gate-planning design D4.
    """
    _replace(layout.gate_approval(primary, change), f"{hashed}\n")


def approval(primary: Path, change: str) -> str | None:
    """Return the approval's first line, or None when it cannot be read."""
    try:
        text = _read(layout.gate_approval(primary, change))
    except OSError:
        return None
    return None if text is None else text.partition("\n")[0]


def holder(mark: Path) -> int | None:
    """Return the pid a live mark holds while that process runs, else None."""
    try:
        pid = int(_read(mark) or "")
    except (OSError, ValueError):
        return None
    if pid <= 1:
        return None
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return None
    except PermissionError:
        pass
    return pid


def live(mine: Path | None = None) -> list[str]:
    """Return the live marks standing, `mine` aside; one whose pid is gone is none."""
    folder = layout.live_dir()
    try:
        fd = statefile.open_folder(layout.kept_dir(), folder.name)
    except OSError:
        return []
    try:
        names = sorted(os.listdir(fd))
    finally:
        os.close(fd)
    marks = [folder / name for name in names]
    return [mark.name for mark in marks if mark != mine and holder(mark)]


def mark_live(primary: Path, pid: int, parent: int) -> Path | None:
    """Write the run's live mark, holding `pid`; None when another process holds it.

    A mark that cannot be written is None too. Why: 0068-pinned-release design D2.
    """
    mark = layout.live_mark(primary)
    if holder(mark) not in (None, pid, parent):
        return None
    try:
        _replace(mark, f"{pid}\n")
    except OSError:
        return None
    return mark


def unmark(mark: Path | None, pid: int) -> None:
    """Remove the live mark `mark` when it still holds `pid`."""
    if mark and holder(mark) == pid:
        _remove(mark)


def record_repo(primary: Path) -> None:
    """Add the primary to the list of repos a run started in, once.

    A list that cannot be read, or a home folder that refuses it, records nothing.
    Why: 0100-worker-diet C1, D12; 0159-kept design D7.
    """
    path = layout.repos_file()
    line = str(primary.resolve())
    try:
        listed = _read(path, REPOS_BOUND)
        if listed is not None and line in listed.splitlines():
            return
        fd = _folder(path)
        try:
            statefile.touch(path.name, fd, 0o600)
            statefile.append(path.name, f"{line}\n", fd)
        finally:
            os.close(fd)
    except OSError:
        return


def repos(path: Path) -> list[str]:
    """Return each line of the record of repos, stripped, a blank one skipped.

    A missing file gives no line; a record `_read` cannot read, or a line holding a
    NUL byte, raises `Broken`. Why: 0161-viewer design D22, D35.
    """
    lines = [line.strip() for line in (_read(path, REPOS_BOUND) or "").splitlines()]
    if any("\x00" in line for line in lines):
        raise Broken(path, "a line holds a NUL byte")
    return [line for line in lines if line]


def make_probe_mark(executor: str, pid: int) -> Path:
    """Return the probe mark of `executor` for `pid`, made anew, empty, at 0600."""
    mark = layout.probe_mark(executor, pid)
    fd = _folder(mark)
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(mark.name, dir_fd=fd)
        statefile.touch(mark.name, fd, 0o600)
    except OSError as error:
        raise Unwritten(mark, error) from None
    finally:
        os.close(fd)
    return mark


def remove_probe_mark(mark: Path) -> None:
    """Remove the probe mark `mark`; a gone one is quiet."""
    _remove(mark)


def _pin_read(file: Path) -> str | None:
    """Return the pin file's text, stripped, or None when none stands.

    A name that `_read` cannot read raises `Broken`. Why: 0160-pins design D3.
    """
    text = _read(file)
    return None if text is None else text.strip()


def _pin_keep(file: Path, text: str) -> None:
    """Replace the pin file with `text` and one newline, as `_replace` writes.

    Why: 0160-pins design D7.
    """
    _replace(file, f"{text}\n")


def _pin_clear(file: Path) -> None:
    """Remove the pin file by name, as `_remove` does; a gone one is quiet."""
    _remove(file)


def source() -> str | None:
    """Return the primary an install ran in, or None before the first or for blank.

    Why: 0160-pins design D8.
    """
    return _pin_read(layout.pin_source()) or None


def pending() -> str | None:
    """Return the release the links wait to move to, or None."""
    return _pin_read(layout.pin_pending())


def hold() -> str | None:
    """Return the release the links are held at, or None."""
    return _pin_read(layout.pin_hold())


def checkout() -> str | None:
    """Return the checkout a live install links, or None."""
    return _pin_read(layout.pin_checkout())


def keep_source(text: str) -> None:
    """Keep `text` as the primary an install ran in."""
    _pin_keep(layout.pin_source(), text)


def keep_pending(text: str) -> None:
    """Keep `text` as the release the links wait to move to."""
    _pin_keep(layout.pin_pending(), text)


def keep_hold(text: str) -> None:
    """Keep `text` as the release the links are held at."""
    _pin_keep(layout.pin_hold(), text)


def keep_checkout(text: str) -> None:
    """Keep `text` as the checkout a live install links."""
    _pin_keep(layout.pin_checkout(), text)


def clear_pending() -> None:
    """Remove the pending release; a gone one is quiet."""
    _pin_clear(layout.pin_pending())


def clear_hold() -> None:
    """Remove the held release; a gone one is quiet."""
    _pin_clear(layout.pin_hold())


def ship_data() -> dict[str, Any]:
    """Return the operator's `ship.toml` parsed, `{}` for no file.

    A file `_read` cannot read, or that does not parse, raises `Broken`.
    Why: 0160-pins design D4.
    """
    file = layout.ship_file()
    text = _read(file)
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError) as error:
        # Why: an integer past Python's digit limit is a bare ValueError.
        raise Broken(file, str(error)) from None
    except RecursionError:
        raise Broken(file, "it is nested too deep") from None


def ship_cap(data: dict[str, Any]) -> int | None:
    """Return `in_flight` of `[queue]` in `data`, None when none is set.

    A value that is no whole number above 0 raises `Broken`.
    """
    table = data.get("queue")
    if not isinstance(table, dict) or "in_flight" not in table:
        return None
    value = table["in_flight"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Broken(layout.ship_file(), "`in_flight` is not a whole number above 0")
    return value


def ship_tags(data: dict[str, Any]) -> bool:
    """Return `tags` of `[push]` in `data`, True when none is set.

    A value that is no boolean raises `Broken`.
    """
    table = data.get("push")
    if not isinstance(table, dict) or "tags" not in table:
        return True
    value = table["tags"]
    if not isinstance(value, bool):
        raise Broken(layout.ship_file(), "`tags` is not true or false")
    return value


def probe_executor(mark: Path) -> str:
    """Return the executor a probe mark's name holds.

    e.g. `probe-codex-41` → "codex"
    """
    return mark.name.split("-")[1]


def probe_untouched(mark: Path) -> bool:
    """Return whether the probe mark stands as a regular file and is empty."""
    return mark.is_file() and not mark.stat().st_size
