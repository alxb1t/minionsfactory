"""Write and parse a ship run's log: its title, its events, its order and its readers.

Why: 0140-run-log design D1 and D2; the log's form is the sdd spec's.
"""

import itertools
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

STOPPED = "stopped by the person"
# why: the plan's skipped converge logs `converge skipped — plan`, the spec's words;
# 0105-converge-switches design D2
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (converge skipped|\S+) — ")
EVENTS = (
    *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
    *("push", "ledger", "unlock", "unkept", "kept", "removed", "rejoin", "grant"),
    *("rescue", "move", "cut", "supervise", "wait", "stacked", "reset", "notes"),
    "limited",
    "converge skipped",
)
LOCK_SECONDS = 30


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


def parse(text: str) -> Event | None:
    """Return the event a line holds, or None; the detail follows the first ` — `.

    e.g. "10:00:00 · run · halt — a — b" → Event(…, "run", "halt", "a — b")
    """
    found = EVENT.match(text)
    if found is None:
        return None
    return Event(text, found[1], found[2], text[found.end() :])


def order(log: Path) -> tuple[str, int, str]:
    """Return a run log's sort key, oldest first.

    e.g. `20261029-163000.md` sorts before `20261029-163000-2.md`
    """
    return log.stem[:15], len(log.stem), log.stem


def newest(runs: Path) -> Path | None:
    """Return the newest run log in `runs`, or None.

    e.g. `20261029-163000.md`, `20261029-163000-2.md` → the second
    """
    logs = list(runs.glob("*.md"))
    if not logs:
        return None
    return max(logs, key=order)


def events(log: Path) -> list[Event]:
    """Return each line of the log that holds an event, in order."""
    return [event for text in log.read_text().splitlines() if (event := parse(text))]


def release_died(runs: Path, change: str) -> bool:
    """Return whether the change's newest release worker ended any way but exit 0.

    A person's no ran no worker, and a release that stopped on purpose exits 0.
    """
    for log in sorted(runs.glob("*.md"), key=order, reverse=True):
        for text in reversed(log.read_text().splitlines()):
            event = parse(text)
            if event and event.who == change and event.detail.startswith("release · "):
                if event.name == "spawn":
                    return True
                if event.name == "finish":
                    return not event.detail.startswith("release · exit 0 · ")
    return False


def rescuing(runs: Path, change: str) -> bool:
    """Return whether the newest log's last rescue or supervisor event is a spawn.

    e.g. `… · 0001-todo · spawn — rescue · model default`, no `finish — rescue` after
    """
    log = newest(runs)
    lines = log.read_text(errors="replace").splitlines() if log else []
    names = [
        event.name
        for text in lines
        if (event := parse(text))
        and event.who == change
        and event.name in ("spawn", "finish")
        and event.detail.startswith(("rescue · ", "supervise · "))
    ]
    return names[-1:] == ["spawn"]


def verify(log: Path) -> str | None:
    """Return why a run log is incomplete, or None when it is complete."""
    lines = [
        text
        for text in log.read_text().splitlines()
        if text.strip() and not text.startswith("# ")
    ]
    spawned: dict[tuple[str, str], int] = {}
    last = detail = ""
    for text in lines:
        event = parse(text)
        if event is None or event.name not in EVENTS:
            return f"unknown event: {text}"
        who, last, detail = event.who, event.name, event.detail
        station = detail.split(" · ")[0]
        if last == "spawn":
            spawned[who, station] = spawned.get((who, station), 0) + 1
        elif last == "finish" and spawned.get((who, station)):
            spawned[who, station] -= 1
    for (who, station), count in spawned.items():
        if count and detail != STOPPED:
            return f"a spawn with no finish: {who} {station}"
    if last not in ("halt", "done"):
        return "the run ends on neither halt nor done"
    return None


def stop(runs: Path) -> Path | None:
    """Append the stop to the newest run log; return that log, or None with none."""
    if (log := newest(runs)) is not None:
        with log.open("a") as file:
            file.write(f"{line('run', 'halt', STOPPED)}\n")
    return log


class RunLog:
    """The run log: one event per line, appended under a lock folder."""

    def __init__(
        self, runs: Path, stamp: str, busy: Callable[[str], Exception]
    ) -> None:
        """Create `<stamp>.md` in `runs`, titled; `<stamp>-2.md`, … when taken.

        `busy` makes the error an append raises, from the lock's name, past its wait.
        """
        runs.mkdir(parents=True, exist_ok=True)
        for n in itertools.count(1):
            self.stamp = stamp if n == 1 else f"{stamp}-{n}"
            self.path = runs / f"{self.stamp}.md"
            try:
                with self.path.open("x") as log:
                    log.write(f"{title(self.stamp)}\n\n")
                break
            except FileExistsError:
                continue
        self.lock = runs / f"{self.stamp}.lock"
        self.busy = busy
        self.held: list[tuple[str, str, str]] | None = None

    def event(self, who: str, event: str, detail: str) -> None:
        """Append the event's line; while `held` is a list, the event waits there."""
        if self.held is not None:
            self.held.append((who, event, detail))
            return
        deadline = time.monotonic() + LOCK_SECONDS
        while True:
            try:
                self.lock.mkdir()
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise self.busy(self.lock.name) from None
                time.sleep(0.05)
        try:
            with self.path.open("a") as log:
                log.write(f"{line(who, event, detail)}\n")
        finally:
            self.lock.rmdir()


class Tail:
    """The newest run log's new whole lines, read at each poll."""

    def __init__(self, runs: Path) -> None:
        """Hold the newest log in `runs` and its end; its old lines are not read."""
        self.runs = runs
        self.held = newest(runs)
        self.offset = self.held.stat().st_size if self.held else 0

    def poll(self) -> list[str]:
        """Return the whole lines written since the last poll, a newer log's all."""
        if (log := newest(self.runs)) != self.held:
            self.held, self.offset = log, 0
        gained = self.held.read_bytes()[self.offset :] if self.held else b""
        whole = gained[: gained.rfind(b"\n") + 1]
        self.offset += len(whole)
        return whole.decode(errors="replace").splitlines()

    def close(self) -> None:
        """Let the log go; the tail holds nothing open."""
