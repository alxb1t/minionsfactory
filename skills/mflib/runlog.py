"""Write and parse a ship run's log: its title, its events, its order and its readers.

Why: 0140-run-log design D1 and D5 to D8, D10; the log's form is the sdd spec's.
"""

import itertools
import os
import re
import threading
import time
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

from . import layout, statefile

STOPPED = "stopped by the person"
# why: the plan's skipped converge logs `converge skipped — plan`, the spec's words;
# 0105-converge-switches design D2
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (converge skipped|\S+) — ")
EVENTS = (
    *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
    *("push", "ledger", "unlock", "unkept", "kept", "removed", "rejoin", "grant"),
    *("rescue", "move", "cut", "supervise", "wait", "stacked", "reset", "notes"),
    *("limited", "sync", "codex"),
    "converge skipped",
)
# Why: 0148-run-fields design D3.
CAUSES = (
    *("plan-text", "gate-red", "check-red", "worker", "limit", "probe", "merge"),
    *("cut", "amend", "cap", "human", "release", "run", "other"),
)
_STAMPED = re.compile(r"\d{8}-\d{6}(-\d+)?")
_STAMP = "%Y%m%d-%H%M%S"
_HALF_DAY = 12 * 3600
_CAUSE = re.compile(r" · cause ([a-z-]+)$")
# The most bytes `wait` reads of a log at one poll. Why: 0140-run-log design D7.
BOUND = 262_144


class Event(NamedTuple):
    """One run-log event: its whole line, who logged it, its name and its detail."""

    line: str
    who: str
    name: str
    detail: str


def title(stamp: str) -> str:
    """Return a log's first line.

    e.g. "20261101-100000" → "# Ship run 20261101-100000"
    """
    return f"# Ship run {stamp}"


def line(who: str, event: str, detail: str) -> str:
    """Return an event's line at the local time, its detail on one line, no newline.

    e.g. "run", "halt", "a  b " → "10:20:30 · run · halt — a b"
    """
    folded = " ".join(detail.split())
    return f"{time.strftime('%H:%M:%S')} · {who} · {event} — {folded}"


def cause_suffix(cause: str) -> str:
    """Return a halt line's cause field; a word off `CAUSES` raises `ValueError`.

    e.g. "gate-red" → " · cause gate-red"
    """
    if cause not in CAUSES:
        raise ValueError(f"not a cause: {cause}")
    return f" · cause {cause}"


def parse(text: str) -> Event | None:
    """Return the event a line holds, or None; the detail follows the first ` — `.

    e.g. "10:00:00 · run · halt — a — b" → Event(…, "run", "halt", "a — b")
    """
    found = EVENT.match(text)
    if found is None:
        return None
    return Event(text, found[1], found[2], text[found.end() :])


def timed(stem: str, lines: Iterable[str]) -> Iterator[tuple[Event, float]]:
    """Yield each event of `lines` with its epoch second, dated from the log's stem.

    The first event is a day on when its clock is `_HALF_DAY` or more before the stem's;
    a clock that steps back from the event before is a day on. Why: 0161-viewer D25.
    """
    base = datetime.strptime(stem[:15], _STAMP)
    start = base.hour * 3600 + base.minute * 60 + base.second
    days, before = 0, None
    for text in lines:
        if (event := parse(text)) is None:
            continue
        hours, minutes, seconds = (int(part) for part in text[:8].split(":"))
        moment = hours * 3600 + minutes * 60 + seconds
        if before is None:
            days += start - moment >= _HALF_DAY
        else:
            days += moment < before
        before = moment
        at = base.replace(hour=hours, minute=minutes, second=seconds)
        yield event, (at + timedelta(days=days)).timestamp()


def cause(detail: str) -> str | None:
    """Return the word a detail ends with after ` · cause `, or None.

    The word is lower-case letters and hyphens, any word, not `CAUSES` alone.
    e.g. "build check fail · cause check-red" → "check-red"
    """
    found = _CAUSE.search(detail)
    return found[1] if found else None


def order(log: Path) -> tuple[str, int, str]:
    """Return a run log's sort key, oldest first.

    e.g. `20261029-163000.md` sorts before `20261029-163000-2.md`
    """
    return log.stem[:15], len(log.stem), log.stem


def _dated(stem: str) -> bool:
    """Return whether a stem's stamp is a real date and time.

    e.g. "20261029-163000-2" → True; "20261399-250000" → False
    """
    try:
        datetime.strptime(stem[:15], _STAMP)
    except ValueError:
        return False
    return True


def _logs(runs: Path) -> list[Path]:
    """Return the run logs in `runs`: each `*.md` a real stamp names, suffixed or not.

    e.g. `20261029-163000-2.md` is one; `notes.md` and `20261399-250000.md` are none.
    Why: 0161-viewer design D21.
    """
    found = runs.glob("*.md")
    return [log for log in found if _STAMPED.fullmatch(log.stem) and _dated(log.stem)]


def newest(runs: Path) -> Path | None:
    """Return the newest run log in `runs`, or None.

    e.g. `20261029-163000.md`, `20261029-163000-2.md` → the second
    """
    logs = _logs(runs)
    if not logs:
        return None
    return max(logs, key=order)


def _lines(log: Path) -> list[str]:
    """Return a log's lines, a bad byte replaced; none for a log it may not read."""
    try:
        return statefile.read(log).splitlines()
    except OSError:
        return []


def events(log: Path) -> list[Event]:
    """Return each line of the log that holds an event, in order."""
    return [event for text in _lines(log) if (event := parse(text))]


def release_died(runs: Path, change: str) -> bool:
    """Return whether the change's newest release ended any way but its merge.

    The newest `release · script` line decides, else the newest release worker's.
    Why: 0152-release-script design D12.
    """
    worker: bool | None = None
    for log in sorted(_logs(runs), key=order, reverse=True):
        for event in reversed(events(log)):
            if event.who != change or event.name not in ("spawn", "finish"):
                continue
            if event.detail.startswith("release · script "):
                merged = event.detail.startswith("release · script merge · exit 0 · ")
                return not merged
            if worker is None and event.detail.startswith("release · "):
                worker = event.name == "spawn" or not event.detail.startswith(
                    "release · exit 0 · "
                )
    return bool(worker)


def rescuing(runs: Path, change: str) -> bool:
    """Return whether the newest log's last rescue or supervisor event is a spawn.

    e.g. `… · 0001-todo · spawn — rescue · model default`, no `finish — rescue` after
    """
    log = newest(runs)
    names = [
        event.name
        for event in (events(log) if log else [])
        if event.who == change
        and event.name in ("spawn", "finish")
        and event.detail.startswith(("rescue · ", "supervise · "))
    ]
    return names[-1:] == ["spawn"]


def verify(log: Path) -> str | None:
    """Return why a run log is incomplete, or None when it is complete.

    A log it may not read, a link or a pipe, raises `OSError`.
    """
    lines = [
        text
        for text in statefile.read(log).splitlines()
        if text.strip() and not text.startswith("# ")
    ]
    spawned: dict[tuple[str, str], int] = {}
    last: Event | None = None
    for text in lines:
        last = parse(text)
        if last is None or last.name not in EVENTS:
            return f"unknown event: {text}"
        station = last.detail.split(" · ")[0]
        if last.name == "spawn":
            spawned[last.who, station] = spawned.get((last.who, station), 0) + 1
        elif last.name == "finish" and spawned.get((last.who, station)):
            spawned[last.who, station] -= 1
    stopped = last is not None and (last.who, last.name, last.detail) == (
        "run",
        "halt",
        STOPPED,
    )
    for (who, station), count in spawned.items():
        if count and not stopped:
            return f"a spawn with no finish: {who} {station}"
    if last is None or last.name not in ("halt", "done"):
        return "the run ends on neither halt nor done"
    return None


def _runs_fd(runs: Path) -> int:
    """Return a descriptor on the runs folder, made, `.minions` read as no link."""
    root, parts = layout.beneath(runs)
    return statefile.folder(root, *parts)


def stop(runs: Path) -> Path | None:
    """Append the stop to the newest run log; return that log, or None with none.

    A link, a hard link or a pipe at the log raises `OSError`, and nothing is written.
    """
    if (log := newest(runs)) is not None:
        folder = _runs_fd(runs)
        try:
            stopped = f"{line('run', 'halt', STOPPED)}\n"
            statefile.append(log.name, stopped, folder, one_name=True)
        finally:
            os.close(folder)
    return log


class RunLog:
    """The run log: one event per line, each one append under the process's lock."""

    def __init__(self, runs: Path, stamp: str) -> None:
        """Create `<stamp>.md` in `runs`, titled; `<stamp>-2.md`, … when taken.

        The create follows no link: a name that stands, a link or not, is taken.
        """
        self.runs = runs
        self.lock = threading.Lock()
        self.held: list[tuple[str, str, str]] | None = None
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        folder = _runs_fd(runs)
        try:
            for n in itertools.count(1):
                self.stamp = stamp if n == 1 else f"{stamp}-{n}"
                self.path = runs / f"{self.stamp}.md"
                try:
                    fd = os.open(self.path.name, flags, 0o644, dir_fd=folder)
                except FileExistsError:
                    continue
                try:
                    os.write(fd, f"{title(self.stamp)}\n\n".encode())
                finally:
                    os.close(fd)
                break
        finally:
            os.close(folder)

    def event(self, who: str, event: str, detail: str) -> None:
        """Append the event's line; while `held` is a list, the event waits there.

        A link, a hard link or a pipe at the log raises `OSError`, and nothing is
        written. Why: 0140-run-log's converge card S2.
        """
        if self.held is not None:
            self.held.append((who, event, detail))
            return
        with self.lock:
            folder = _runs_fd(self.runs)
            try:
                text = f"{line(who, event, detail)}\n"
                statefile.append(self.path.name, text, folder, one_name=True)
            finally:
                os.close(folder)


class Tail:
    """The newest run log's new whole lines, read at each poll, `BOUND` bytes at most.

    The log stays open across the polls of one log. Why: 0140-run-log design D7.
    """

    def __init__(self, runs: Path) -> None:
        """Hold the newest log in `runs` and its end; its old lines are not read."""
        self.runs = runs
        self.held = newest(runs)
        self.fd = self._open()
        self.offset = os.fstat(self.fd).st_size if self.fd is not None else 0
        self.skipping = False

    def _open(self) -> int | None:
        """Return a descriptor on the held log; None for none, a link or a pipe.

        A hard link is none too: it can name a host file. Why: 0140-run-log's
        converge card S2.
        """
        if self.held is None:
            return None
        try:
            return statefile.open_regular(self.held, one_name=True)
        except OSError:
            return None

    def poll(self) -> list[str]:
        """Return the whole lines written since the last poll, a newer log's all.

        A line longer than `BOUND` is passed over whole, nothing of it returned.
        """
        if (log := newest(self.runs)) != self.held:
            self.close()
            self.held, self.offset, self.skipping = log, 0, False
            self.fd = self._open()
        if self.fd is None:
            return []
        gained = os.pread(self.fd, BOUND, self.offset)
        if self.skipping:
            end = gained.find(b"\n")
            self.offset += len(gained) if end < 0 else end + 1
            if end < 0:
                return []
            self.skipping, gained = False, gained[end + 1 :]
        elif len(gained) == BOUND and b"\n" not in gained:
            self.offset += BOUND
            self.skipping = True
            return []
        whole = gained[: gained.rfind(b"\n") + 1]
        self.offset += len(whole)
        return whole.decode(errors="replace").splitlines()

    def close(self) -> None:
        """Close the held log's descriptor, when one is open."""
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
