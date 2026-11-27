"""Write, read, list and remove the conductor's kept files in the home folder.

The kept origin, `.default`, the offline base, the release ledger, the gate approval,
the live mark, `repos` and the probe mark. Why: 0159-kept design D1, D2 and D5.
"""

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

# why: 0159-kept design D6; remove the noqa when a read goes through statefile
from . import layout, statefile  # noqa: F401

type Urls = tuple[list[str], list[str]]

_ONCE = os.O_CREAT | os.O_EXCL | os.O_WRONLY


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


def _made(folder: Path, *, parents: bool = False) -> None:
    """Make `folder` at 0700 unless it stands; a failure raises `Refused`."""
    try:
        folder.mkdir(mode=0o700, parents=parents, exist_ok=True)
    except OSError as error:
        raise Refused(error) from None


def _fresh(file: Path, text: str) -> None:
    """Write `text` to `file`, made anew at 0600; a failure raises `Unwritten`."""
    try:
        file.unlink(missing_ok=True)
        with os.fdopen(os.open(file, _ONCE, 0o600), "w") as written:
            written.write(text)
    except OSError as error:
        raise Unwritten(file, error) from None


def origin(primary: Path) -> Urls | None:
    """Return the URLs a run kept for `primary`, or None before its first."""
    file = layout.kept_file(primary)
    if not file.is_file():
        return None
    fetch, push = json.loads(file.read_text())
    return fetch, push


def origin_stands(primary: Path) -> bool:
    """Return whether a kept origin stands for `primary`."""
    return layout.kept_file(primary).is_file()


def keep_origin(primary: Path, urls: Urls) -> None:
    """Keep `urls` as `primary`'s origin, once: a name that stands is left.

    Why: 0053-sandbox-patch design D2.
    """
    file = layout.kept_file(primary)
    try:
        file.parent.mkdir(mode=0o700, exist_ok=True)
    except FileExistsError:
        return
    except OSError as error:
        raise Refused(error) from None
    try:
        with os.fdopen(os.open(file, _ONCE, 0o600), "w") as kept:
            json.dump(urls, kept)
    except FileExistsError:
        return
    except OSError as error:
        raise Unwritten(file, error) from None


def default(primary: Path) -> str | None:
    """Return the text of the default branch a run kept, or None."""
    file = layout.default_file(primary)
    return file.read_text() if file.is_file() else None


def default_stands(primary: Path) -> bool:
    """Return whether the name of the kept default branch stands, through a link."""
    return layout.default_file(primary).exists()


def keep_default(primary: Path, name: str) -> None:
    """Keep `name` as `primary`'s default branch, once: a name that stands is left."""
    file = layout.default_file(primary)
    try:
        with os.fdopen(os.open(file, _ONCE, 0o600), "w") as kept:
            kept.write(name)
    except FileExistsError:
        return
    except OSError as error:
        raise Unwritten(file, error) from None


def base(primary: Path) -> str | None:
    """Return the offline base's sha, stripped, or None when none stands."""
    file = layout.pushed_file(primary)
    if not file.is_file():
        return None
    return file.read_text().strip() or None


def base_stands(primary: Path) -> bool:
    """Return whether an offline base stands for `primary`."""
    return layout.pushed_file(primary).is_file()


def keep_base(primary: Path, sha: str) -> None:
    """Keep `sha` as the offline base, over an older one, through a temp file."""
    file = layout.pushed_file(primary)
    _made(file.parent)
    try:
        fd, temp = tempfile.mkstemp(dir=file.parent, prefix=f".{file.name}-")
        with os.fdopen(fd, "w") as kept:
            kept.write(f"{sha}\n")
        os.replace(temp, file)
    except OSError as error:
        raise Unwritten(file, error) from None


def record_release(primary: Path, change: str, head: str) -> None:
    """Record `head` as the change's in the release ledger, over an older entry."""
    folder = layout.released_dir(primary)
    _made(folder, parents=True)
    _fresh(folder / change, f"{head}\n")


def release_entries(primary: Path) -> list[Path]:
    """Return every name in the release ledger's folder; none with no folder."""
    folder = layout.released_dir(primary)
    return list(folder.iterdir()) if folder.is_dir() else []


def release_heads(primary: Path) -> Heads:
    """Return the heads the release ledger holds: each entry's first line."""
    entries = release_entries(primary)
    return Heads({entry.read_text().partition("\n")[0] for entry in entries}, [])


def close_releases(primary: Path, landed: Callable[[str], bool]) -> None:
    """Remove each ledger entry whose head `landed` says is on the default branch.

    Why: 0053-sandbox-patch design D2.
    """
    for entry in release_entries(primary):
        if landed(entry.read_text().partition("\n")[0]):
            entry.unlink()


def approve(primary: Path, change: str, hashed: str) -> None:
    """Record `hashed` as a person's approval of the change's gate, over an older one.

    Why: 0060-gate-planning design D4.
    """
    entry = layout.gate_approval(primary, change)
    _made(entry.parent, parents=True)
    _fresh(entry, f"{hashed}\n")


def approval(primary: Path, change: str) -> str | None:
    """Return the approval's first line, or None when it cannot be read."""
    try:
        return layout.gate_approval(primary, change).read_text().partition("\n")[0]
    except OSError:
        return None


def holder(mark: Path) -> int | None:
    """Return the pid a live mark holds while that process runs, else None."""
    try:
        pid = int(mark.read_text())
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
    marks = sorted(folder.iterdir()) if folder.is_dir() else []
    return [mark.name for mark in marks if mark != mine and holder(mark)]


def mark_live(primary: Path, pid: int, parent: int) -> Path | None:
    """Write the run's live mark, holding `pid`; None when another process holds it.

    A mark that cannot be written is None too. Why: 0068-pinned-release design D2.
    """
    mark = layout.live_mark(primary)
    if holder(mark) not in (None, pid, parent):
        return None
    try:
        mark.parent.parent.mkdir(mode=0o700, exist_ok=True)
        mark.parent.mkdir(mode=0o700, exist_ok=True)
        mark.write_text(f"{pid}\n")
    except OSError:
        return None
    return mark


def unmark(mark: Path | None, pid: int) -> None:
    """Remove the live mark `mark` when it still holds `pid`."""
    if mark and holder(mark) == pid:
        mark.unlink()


def record_repo(primary: Path) -> None:
    """Add the primary to the list of repos a run started in, once.

    A home folder that refuses it records nothing. Why: 0100-worker-diet C1, D12.
    """
    path = layout.repos_file()
    line = str(primary.resolve())
    try:
        path.parent.mkdir(mode=0o700, exist_ok=True)
        if path.is_file() and line in path.read_text(errors="replace").splitlines():
            return
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        with os.fdopen(os.open(path, flags, 0o600), "a") as file:
            file.write(f"{line}\n")
    except OSError:
        return


def make_probe_mark(executor: str, pid: int) -> Path:
    """Return the probe mark of `executor` for `pid`, made anew, empty, at 0600."""
    mark = layout.probe_mark(executor, pid)
    _made(mark.parent, parents=True)
    try:
        mark.unlink(missing_ok=True)
        os.close(os.open(mark, _ONCE, 0o600))
    except OSError as error:
        raise Unwritten(mark, error) from None
    return mark


def remove_probe_mark(mark: Path) -> None:
    """Remove the probe mark `mark`; a gone one is quiet."""
    mark.unlink(missing_ok=True)


def probe_executor(mark: Path) -> str:
    """Return the executor a probe mark's name holds.

    e.g. `probe-codex-41` → "codex"
    """
    return mark.name.split("-")[1]


def probe_untouched(mark: Path) -> bool:
    """Return whether the probe mark stands as a regular file and is empty."""
    return mark.is_file() and not mark.stat().st_size
