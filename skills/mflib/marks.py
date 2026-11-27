"""Name the marks of a change folder, write the text of each and read it back.

One read, one `head:` rule and one staged write serve every mark.
Why: 0154-marks design D1, D2, D4, D5 and D6.
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
_HEAD = re.compile(r"[0-9a-f]{7,40}")
_HALT_KEYS = re.compile(r"^(sub-task|stop):[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_CUT_HALT_WIDTH = 300
_PHRASES = {errno.ELOOP: "it is a link", errno.EINVAL: "it is not a regular file"}


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
    return statefile.folder(primary, layout.MINIONS, layout.CHANGES, change)


def read(primary: Path, change: str, name: str, bound: int = BOUND) -> str | None:
    """Return a mark's text, read through no link and without blocking; None for none.

    A link, no regular file, a file over `bound` bytes or one not UTF-8 raises
    `Broken`. Why: 0154-marks design D5.
    """
    try:
        fd = statefile.open_folder(primary, layout.MINIONS, layout.CHANGES, change)
    except FileNotFoundError:
        return None
    except OSError as error:
        why = f"its folder cannot be opened — {error.strerror}"
        raise Broken(f"{name} cannot be read: {why}") from None
    try:
        data = statefile.read_bytes(name, folder=fd, limit=bound + 1)
    except FileNotFoundError:
        return None
    except OSError as error:
        why = _PHRASES.get(error.errno, str(error.strerror))
        raise Broken(f"{name} cannot be read: {why}") from None
    finally:
        os.close(fd)
    if len(data) > bound:
        raise Broken(f"{name} cannot be read: it is over {bound} bytes")
    try:
        return data.decode()
    except UnicodeDecodeError:
        raise Broken(f"{name} cannot be read: it is not UTF-8") from None


def _passed(primary: Path, change: str, name: str, bound: int = BOUND) -> str:
    """Return a mark's text; "" when it is missing or cannot be read."""
    try:
        return read(primary, change, name, bound) or ""
    except Broken:
        return ""


def head_of(text: str) -> str | None:
    r"""Return the value of the text's one `head:` line when it is 7 to 40 hex digits.

    e.g. "head: abc1234\r\n" → "abc1234"; a second `head:` line → None
    """
    values = [
        line.removeprefix("head:").strip(" \t\r")
        for line in text.split("\n")
        if line.startswith("head:")
    ]
    return values[0] if len(values) == 1 and _HEAD.fullmatch(values[0]) else None


def done_head(primary: Path, change: str) -> str | None:
    """Return the head `build.done` holds; None when it holds none or cannot be read."""
    return head_of(_passed(primary, change, BUILD_DONE))


def simplified_head(primary: Path, change: str) -> str | None:
    """Return the head `build.simplified` holds; None when it holds none or is bad."""
    return head_of(_passed(primary, change, BUILD_SIMPLIFIED))


def red_head(primary: Path, change: str) -> str | None:
    """Return the head `integrate.red` holds, or None; a broken one raises `Broken`."""
    return head_of(read(primary, change, INTEGRATE_RED) or "")


def build_halt(primary: Path, change: str) -> tuple[str, str, str] | None:
    r"""Return `build.halt`'s sub-task and stop, the last of each, and head; or None.

    A mark that cannot be read raises `Broken`.
    e.g. "sub-task: 1.2\nstop: 3\nhead: abc1234\n" → ("1.2", "3", "abc1234")
    """
    text = read(primary, change, BUILD_HALT) or ""
    keys = dict(_HALT_KEYS.findall(text))
    if (head := head_of(text)) is None or not {"sub-task", "stop"} <= keys.keys():
        return None
    return keys["sub-task"], keys["stop"], head


def stacked_head(primary: Path, change: str) -> str | None:
    """Return `stacked-on`'s first word when it is a full sha, else None."""
    words = _passed(primary, change, STACKED_ON).split()
    return words[0] if words and _FULL_SHA.fullmatch(words[0]) else None


def cutter_halt(primary: Path, change: str) -> str | None:
    """Return `cut.halt`'s first line, stripped and cut; None with no file.

    A mark that cannot be read raises `Broken`.
    """
    if (text := read(primary, change, CUT_HALT)) is None:
        return None
    return text.partition("\n")[0].strip()[:_CUT_HALT_WIDTH]


def plan_check_text(primary: Path, change: str) -> str | None:
    """Return `plan-check.txt`'s text; None when it is missing or cannot be read."""
    try:
        return read(primary, change, PLAN_CHECK, NOTES_BOUND)
    except Broken:
        return None


def release_pre(primary: Path, change: str) -> dict[str, str] | None:
    r"""Return `release.pre`'s keys, the last of two winning but `head`; None with none.

    A mark that cannot be read, or lacks a key of `RELEASE_KEYS`, raises `Broken`.
    e.g. "tag: v1.2.0\nversion: v1.2\ngate: 9\nhead: abc1234\n" → {"gate": "9", …}
    """
    if (text := read(primary, change, RELEASE_PRE)) is None:
        return None
    pairs = (line.partition(":") for line in text.splitlines())
    keys = {key.strip(): value.strip() for key, colon, value in pairs if colon}
    keys["head"] = head_of(text) or ""
    for key in RELEASE_KEYS:
        if not keys.get(key):
            raise Broken(f"{RELEASE_PRE} has no {key}:")
    return keys


def standing(primary: Path, change: str, name: str) -> bool:
    """Return whether a stop mark stands; one that cannot be read raises `Broken`."""
    return read(primary, change, name) is not None


def stands(primary: Path, change: str, name: str) -> bool:
    """Return whether a regular file stands at the mark, read through no link."""
    try:
        return standing(primary, change, name)
    except Broken:
        return False


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
    """Return `gate.red`'s text; "" when it is missing or cannot be read."""
    return _passed(primary, change, GATE_RED, NOTES_BOUND)


def open_notes(primary: Path, change: str, flags: int) -> int | None:
    """Return a descriptor on `build-notes.md`, opened with `flags`; None with no file.

    A link, a file that cannot be opened, one that is no regular file of one name or
    one over `NOTES_BOUND` raises `Broken`. Why: 0102-build-per-phase design D3.
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
    if found.st_size > NOTES_BOUND:
        os.close(file)
        raise Broken(f"{BUILD_NOTES} is over {NOTES_BOUND} bytes")
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

    Why: 0144-gate-outside design D2; 0154-marks design D6.
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


def remove(primary: Path, change: str, name: str) -> None:
    """Remove the mark `name` by its name, through no link; none there is no error."""
    fd = _folder(primary, change)
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=fd)
    finally:
        os.close(fd)
