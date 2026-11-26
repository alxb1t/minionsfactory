"""Name the marks of a change folder, write the text of each and read it back.

Each function reads, writes or removes a mark as the copy it replaces does.
Why: 0154-marks design D1, D2 and D3.
"""

import contextlib
import errno
import os
import re
import stat
from pathlib import Path

from . import layout, statefile

BUILD_DONE = "build.done"
BUILD_HALT = "build.halt"
BUILD_CLOSING = "build.closing"
BUILD_SIMPLIFIED = "build.simplified"
BUILD_NOTES = "build-notes.md"
STACKED_ON = "stacked-on"
CUT_HALT = "cut.halt"
CUT_RED = "cut.red"
INTEGRATE_MD = "integrate.md"
INTEGRATE_RED = "integrate.red"
INTEGRATE_SETTLED = "integrate.settled"
INTEGRATE_RESOLVED = "integrate.resolved"
RELEASE_HELD = "release.held"
RELEASE_FLAG = "release.flag"
RELEASE_PRE = "release.pre"
RESCUE = "rescue.md"
REPLAN = "replan.mark"
PLAN_CHECK = "plan-check.txt"
GATE_RED = "gate.red"
BOUND = 65536
NOTES_BOUND = 1048576
RELEASE_KEYS = ("tag", "version", "gate", "head")
# Each copy's own `head:` pattern: remove when one head rule reads every mark.
# Why: 0154-marks design D3.
_DONE_HEAD = re.compile(r"^head:\s*(\S+)", re.MULTILINE)
_RED_HEAD = re.compile(r"^head:[ \t]*(\S+)", re.MULTILINE)
_HALT_KEYS = re.compile(r"^(sub-task|stop|head):[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_CUT_HALT_WIDTH = 300


class Broken(ValueError):
    """Say what is wrong with a mark, as a phrase that starts with its name."""


class Unwritten(Exception):
    """Say which mark a write failed at, and the `OSError` it failed with."""

    def __init__(self, name: str, cause: OSError) -> None:
        """Hold the mark's name and the cause; the message names both."""
        super().__init__(f"{name} cannot be written: {cause.strerror}")
        self.name = name
        self.cause = cause


def discarded(n: int) -> str:
    """Return the name of a release's saved patch.

    e.g. 2 → "release.discarded.2.patch"
    """
    return f"release.discarded.{n}.patch"


def _path(primary: Path, change: str, name: str) -> Path:
    """Return the path of the change's mark `name`."""
    return layout.change_dir(primary, change) / name


def _folder(primary: Path, change: str) -> int:
    """Return a descriptor on the change's folder, made, none of its parts a link."""
    return statefile.folder(layout.run_dir(primary), layout.CHANGES, change)


def _path_text(primary: Path, change: str, name: str) -> str | None:
    """Return a mark's text read by its path, a link followed; "" for no file.

    None when it cannot be read or decoded.
    """
    file = _path(primary, change, name)
    try:
        return file.read_text() if file.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return None


def done_head(primary: Path, change: str) -> str | None:
    """Return the word `build.done`'s first `head:` names, or None."""
    found = _DONE_HEAD.search(_path_text(primary, change, BUILD_DONE) or "")
    return found[1] if found else None


def simplified_head(primary: Path, change: str) -> str | None:
    """Return the word `build.simplified`'s first `head:` names, or None."""
    found = _DONE_HEAD.search(_path_text(primary, change, BUILD_SIMPLIFIED) or "")
    return found[1] if found else None


def red_head(primary: Path, change: str) -> str | None:
    """Return the word `integrate.red`'s first `head:` line names, or None."""
    found = _RED_HEAD.search(_path_text(primary, change, INTEGRATE_RED) or "")
    return found[1] if found else None


def build_halt(primary: Path, change: str) -> tuple[str, str, str] | None:
    r"""Return `build.halt`'s sub-task, stop and head, the last of each; or None.

    e.g. "sub-task: 1.2\nstop: 3\nhead: abc1234\n" → ("1.2", "3", "abc1234")
    """
    text = _path_text(primary, change, BUILD_HALT) or ""
    keys = dict(_HALT_KEYS.findall(text))
    if not {"sub-task", "stop", "head"} <= keys.keys():
        return None
    return keys["sub-task"], keys["stop"], keys["head"]


def stacked_head(primary: Path, change: str) -> str | None:
    """Return `stacked-on`'s first word when it is a full sha, else None."""
    words = (_path_text(primary, change, STACKED_ON) or "").split()
    return words[0] if words and _FULL_SHA.fullmatch(words[0]) else None


def cutter_halt(primary: Path, change: str) -> str | None:
    """Return `cut.halt`'s first line, stripped and cut; None when it cannot be opened.

    The open follows no link; a bad byte is replaced.
    """
    fd = _folder(primary, change)
    try:
        halt = os.open(CUT_HALT, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    except OSError:
        halt = None
    finally:
        os.close(fd)
    if halt is None:
        return None
    with os.fdopen(halt, errors="replace") as file:
        return file.readline().strip()[:_CUT_HALT_WIDTH]


def done_lines(primary: Path, change: str) -> list[str]:
    """Return `build.done`'s lines, through no link; none when it cannot be read."""
    text = ""
    with contextlib.suppress(OSError):
        text = statefile.read(_path(primary, change, BUILD_DONE))
    return text.splitlines()


def plan_check_text(primary: Path, change: str) -> str | None:
    """Return `plan-check.txt`'s text, a bad byte replaced; None with no file.

    A link, or a file that is no regular file, raises `OSError`.
    """
    try:
        return statefile.read(_path(primary, change, PLAN_CHECK))
    except FileNotFoundError:
        return None


def release_pre(primary: Path, change: str) -> dict[str, str] | None:
    r"""Return `release.pre`'s keys, the last of two winning; None with no file.

    A mark that cannot be read, or lacks a key of `RELEASE_KEYS`, raises `Broken`.
    e.g. "tag: v1.2.0\nversion: v1.2\ngate: 9\nhead: abc\n" → {"tag": "v1.2.0", …}
    """
    try:
        text = statefile.read(_path(primary, change, RELEASE_PRE))
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Broken(f"{RELEASE_PRE} cannot be read: {error.strerror}") from None
    pairs = (line.partition(":") for line in text.splitlines())
    keys = {key.strip(): value.strip() for key, colon, value in pairs if colon}
    for key in RELEASE_KEYS:
        if not keys.get(key):
            raise Broken(f"{RELEASE_PRE} has no {key}:")
    return keys


def stands(primary: Path, change: str, name: str) -> bool:
    """Return whether a regular file stands at the mark, a link followed."""
    return _path(primary, change, name).is_file()


def present(primary: Path, change: str, name: str) -> bool:
    """Return whether anything stands at the mark, no link followed."""
    return os.path.lexists(_path(primary, change, name))


def mtime(primary: Path, change: str, name: str) -> int | None:
    """Return the mark's modification time in nanoseconds, by `lstat`.

    None for no regular file, or on any error.
    """
    try:
        status = _path(primary, change, name).lstat()
    except OSError:
        return None
    return status.st_mtime_ns if stat.S_ISREG(status.st_mode) else None


def gate_red_text(primary: Path, change: str) -> str:
    """Return `gate.red`'s text, a link followed; "" when it cannot be read."""
    shown = ""
    with contextlib.suppress(OSError, UnicodeDecodeError):
        shown = _path(primary, change, GATE_RED).read_text()
    return shown


def open_notes(primary: Path, change: str, flags: int) -> int | None:
    """Return a descriptor on `build-notes.md`, opened with `flags`; None with no file.

    A link, a file that cannot be opened, or one that is no regular file of one name
    raises `Broken`. Why: 0102-build-per-phase design D3.
    """
    fd = _folder(primary, change)
    try:
        file = os.open(BUILD_NOTES, flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        return None
    except OSError as error:
        linked = error.errno == errno.ELOOP
        why = "is a link" if linked else f"cannot be opened — {error.strerror}"
        raise Broken(f"{BUILD_NOTES} {why}") from None
    finally:
        os.close(fd)
    found = os.fstat(file)
    if not stat.S_ISREG(found.st_mode) or found.st_nlink != 1:
        os.close(file)
        raise Broken(f"{BUILD_NOTES} is not a regular file of one name")
    return file


def note_lines(primary: Path, change: str) -> int:
    """Return the lines of `build-notes.md`; 0 with no file."""
    file = open_notes(primary, change, os.O_RDONLY)
    if file is None:
        return 0
    with os.fdopen(file, "rb") as notes:
        return len(notes.read().splitlines())


def done_text(head: str, simplify: str) -> str:
    r"""Return `build.done`'s text.

    e.g. ("abc", "none") → "head: abc\nsimplify: none\n"
    """
    return f"head: {head}\nsimplify: {simplify}\n"


def halt_text(sub_task: str, stop: str, evidence: str, head: str) -> str:
    r"""Return `build.halt`'s text, the evidence on one line.

    e.g. evidence "red\n  x" → the line "evidence: red x"
    """
    said = " ".join(evidence.split())
    return f"sub-task: {sub_task}\nstop: {stop}\nevidence: {said}\nhead: {head}\n"


def diagnosis_text(change: str, halt: str) -> str:
    """Return `rescue.md`'s text: the run's diagnosis of a verify halt."""
    return (
        f"# {change} — rescue diagnosis\n\nhalt: {halt}\nsub-task: none\n"
        "cause: a Verify: changed since the cut\n"
        f"proposal: commit docs({change}): amend the change directory, then"
        f" conduct.py rejoin {change}, or /mf-ship with no run live\n"
    )


def head_text(head: str) -> str:
    r"""Return the text of a mark that holds a head alone.

    e.g. "abc" → "head: abc\n"
    """
    return f"head: {head}\n"


def stacked_text(head: str) -> str:
    r"""Return `stacked-on`'s text.

    e.g. "abc" → "abc\n"
    """
    return f"{head}\n"


def plan_check_body(base: str, output: str) -> str:
    r"""Return `plan-check.txt`'s text: a `base:` line, then the output.

    e.g. ("abc", "ok\n") → "base: abc\nok\n"
    """
    return f"base: {base}\n{output}"


def write(primary: Path, change: str, name: str, text: str) -> None:
    """Write the mark `name` staged, refusing a link; a failure raises `Unwritten`.

    Why: 0144-gate-outside design D2.
    """
    try:
        fd = _folder(primary, change)
        try:
            statefile.write(Path(name), text, refuse_link=True, folder=fd)
        finally:
            os.close(fd)
    except (OSError, statefile.WriteFailed) as error:
        cause = error.error if isinstance(error, statefile.WriteFailed) else error
        raise Unwritten(name, cause) from None


def write_in_place(primary: Path, change: str, name: str, text: str) -> None:
    """Write `text` over the mark `name`, truncated, through no link.

    A failure raises `OSError`. Why: 0071-ship-fixes design D8.
    """
    fd = _folder(primary, change)
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_TRUNC
    try:
        file = os.open(name, flags, 0o644, dir_fd=fd)
    finally:
        os.close(fd)
    with os.fdopen(file, "w") as out:
        out.write(text)


def remove(primary: Path, change: str, name: str) -> None:
    """Remove the mark `name` by its name, through no link; none there is no error."""
    fd = _folder(primary, change)
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=fd)
    finally:
        os.close(fd)
