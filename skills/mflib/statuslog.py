"""Write and parse a change's status log: its title, its runs and their events.

Each argument holds a difference between the copies until they are fixed to one side.
Why: 0136-status-log design D1, D3, D6 and D13; the log's form is the sdd spec's.
"""

import contextlib
import errno
import itertools
import re
from datetime import datetime
from pathlib import Path
from typing import Literal, NamedTuple

from . import layout, statefile

type Extent = Literal["blank", "heading", "line"]
HEADING = "## Run"
EVENT = re.compile(r"^\d\d:\d\d:\d\d · round (\d+) · (by rule|[a-z-]+) — (.*)$")
NAMES = (
    *("start", "freeze", "fan-out", "verdicts", "shadow", "fix", "verify"),
    *("pickup", "catch-up", "by rule", "debt", "halt", "done"),
)
ENDS = ("done", "halt")


class Refused(Exception):
    """Say why the writer wrote nothing; the command prints it."""


class Event(NamedTuple):
    """One status-log event: its round, its name and its detail."""

    round: int
    name: str
    detail: str


class Run(NamedTuple):
    """The status log's newest run: its heading's mark and its events, newest first."""

    mark: str | None
    events: list[Event]


class Block(NamedTuple):
    """A run's heading, and the lines its extent holds."""

    heading: str
    lines: list[str]


def _now() -> datetime:
    """Return the local time."""
    return datetime.now()


def title(change: str) -> str:
    """Return the log's first line.

    e.g. "0001-todo" → "# 0001-todo — converge status"
    """
    return f"# {change} — converge status"


def create(log: Path, change: str) -> None:
    """Create the log holding its title; a log that stands is left as it is."""
    with contextlib.suppress(FileExistsError), log.open("x") as file:
        file.write(f"{title(change)}\n")


def heading(number: int, now: datetime, mark: str | None) -> str:
    """Return a run's heading, with its mark when one is given.

    e.g. 4, 2026-11-05 10:04, "grant" → "## Run 4 — 2026-11-05 10:04 · grant"
    """
    line = f"{HEADING} {number} — {now:%Y-%m-%d %H:%M}"
    return line if mark is None else f"{line} · {mark}"


def mark_of(line: str) -> str | None:
    """Return the text after a heading's first ` · `, as it stands, or None.

    e.g. "## Run 3 — d · catch-up" → "catch-up"
    """
    return line.partition(" · ")[2] or None


def marked(line: str, mark: str) -> bool:
    """Return whether a heading ends ` · <mark>`, its trailing blanks dropped."""
    return line.rstrip().endswith(f" · {mark}")


def is_heading(line: str) -> bool:
    """Return whether a line is a run's heading."""
    return line.startswith(HEADING)


def parse_event(line: str) -> Event | None:
    """Return the event a line holds in the spec's form, or None.

    e.g. "10:00:00 · round 12 · fix — R1" → Event(12, "fix", "R1")
    """
    found = EVENT.match(line)
    return Event(int(found[1]), found[2], found[3]) if found else None


def is_event(line: str, name: str) -> bool:
    """Return whether a line holds the event `name`, its detail aside.

    e.g. "10:00:00 · round 1 · done — ok", "done" → True
    """
    return line.split(" — ", maxsplit=1)[0].endswith(f" · {name}")


def ends(line: str) -> str | None:
    """Return `done` or `halt` for a line that ends a run, else None."""
    return next((name for name in ENDS if is_event(line, name)), None)


def _heading_at(lines: list[str]) -> int | None:
    """Return the index of the first heading in `lines`, or None."""
    return next((i for i, line in enumerate(lines) if is_heading(line)), None)


def newest(text: str, *, extent: Extent) -> Block | None:
    """Return the newest run's heading and lines, or None with no run.

    The lines run to a blank line or a heading under `blank`, to the next heading,
    blanks skipped, under `heading`, and are the first line not blank under `line`.
    """
    lines = text.splitlines()
    at = _heading_at(lines)
    if at is None:
        return None
    rest = lines[at + 1 :]
    run = list(itertools.takewhile(lambda line: not is_heading(line), rest))
    if extent == "blank":
        held = list(itertools.takewhile(str.strip, run))
    elif extent == "heading":
        held = [line for line in run if line.strip()]
    else:
        held = [line for line in rest if line.strip()][:1]
    return Block(lines[at], held)


def latest(text: str) -> Run:
    """Return the newest run to a blank line or a heading; no run has no event."""
    block = newest(text, extent="blank")
    if block is None:
        return Run(None, [])
    events = [event for event in map(parse_event, block.lines) if event]
    return Run(mark_of(block.heading), events)


def names_lock(text: str) -> bool:
    """Return whether a halt names the debt lock or its old name.

    e.g. "waited for .minions/debt.lock" → True; "waited for debt.lock" → False
    """
    here = Path()
    locks = (layout.debt_lock(here), layout.backlog_lock(here))
    return any(str(lock) in text for lock in locks)


def insert(
    text: str, events: list[str], run: int | None, mark: str | None
) -> tuple[list[str], list[str]]:
    """Return the log's lines with the new lines inserted, and those lines.

    A run's heading goes under the title; events go on top of the newest run, the
    last given on top. A refusal raises `Refused`.
    """
    lines = text.splitlines()
    now = _now()
    if run is not None:
        if not lines or not lines[0].startswith("# "):
            raise Refused("no # title")
        line = heading(run, now, mark)
        rest = lines[1:]
        while rest and not rest[0].strip():
            rest.pop(0)
        return [lines[0], "", line, *(["", *rest] if rest else [])], [line]
    at = _heading_at(lines)
    block = newest(text, extent="line")
    if at is None or block is None:
        raise Refused(f"no {HEADING} heading")
    if ended := next((e for e in map(ends, events[:-1]) if e), None):
        raise Refused(f"{ended} goes last in a call")
    top = next(iter(block.lines), "")
    if (ended := ends(top)) and not (ended == "halt" and names_lock(top)):
        raise Refused(f"the run ends on {ended}: open a {HEADING} for a new event")
    written = [f"{now:%H:%M:%S} · {event}" for event in events]
    return [*lines[: at + 1], *reversed(written), *lines[at + 1 :]], written


def read(log: Path) -> str:
    """Return the log's text, read through one descriptor that refuses a link.

    A link raises `Refused`, and a byte that is not UTF-8 `UnicodeDecodeError`.
    """
    try:
        data = statefile.read_bytes(log, guard=False)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise Refused(f"{log} is a link") from error
        raise Refused(f"{log}: {error.strerror}") from error
    return data.decode()


def stamp(log: Path, events: list[str], run: int | None, mark: str | None) -> list[str]:
    """Write events or a run heading into the log; return the lines written."""
    lines, written = insert(read(log), events, run, mark)
    try:
        statefile.write(log, "\n".join(lines) + "\n", remove="rename")
    except statefile.WriteFailed as failed:
        if failed.step == "create":
            raise Refused(f"{log.name}.tmp could not be created") from failed
        raise Refused(f"{log.name} could not be replaced") from failed
    return written


def command(log: Path, events: list[str], run: int | None, mark: str | None) -> int:
    """Stamp the log and print each line written, or the refusal; return the exit."""
    try:
        written = stamp(log, events, run, mark)
    except Refused as refused:
        print(f"stamp: cannot stamp — {refused}")
        return 2
    print("\n".join(written))
    return 0


def open_run(log: Path, change: str, mark: str | None = None) -> int:
    """Open the next run, making the log's folder and the log; return the exit.

    The runs are counted by their heading lines. A link at the log raises `Refused`.
    """
    log.parent.mkdir(parents=True, exist_ok=True)
    create(log, change)
    runs = read(log).count(f"\n{HEADING}")
    return command(log, [], runs + 1, mark)
