"""Write and parse a change's status log: its title, its runs and their events.

Why: 0136-status-log design D1, D6 and D13; the log's form is the sdd spec's.
"""

import contextlib
import errno
import itertools
import os
import re
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from . import layout, statefile

HEADING = "## Run"
EVENT = re.compile(
    r"^\d\d:\d\d:\d\d · round (\d+) · (by rule|[a-z-]+)(?: —(?: (.*))?)?$"
)
LINE_BREAKS = re.compile(r"[\r\n]+")
WORKER = re.compile(r" worker exit -?\d+| timed out after ")
NAMES = (
    *("start", "freeze", "fan-out", "verdicts", "shadow", "fix", "verify"),
    *("pickup", "catch-up", "by rule", "debt", "halt", "done"),
)
ENDS = ("done", "halt")
FALLBACK = "fallback: codex usage limit"
FAILED = "fallback: codex failed"
_NUMBER = re.compile(r"## Run ([0-9]+)")
_VERDICTS = re.compile(r"(conformance|adversarial) \S+ · open_blocking \d+ · (.*)")
_SPENT = re.compile(r"(executor|model|effort|tokens) (\S+)")


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


class Section(NamedTuple):
    """One run of the log: its heading's number and mark, and its events in order."""

    number: int | None
    mark: str | None
    events: list[Event]


class Verdicts(NamedTuple):
    """What a `verdicts` line says a role spent, and whether it fell back to Codex."""

    role: str
    executor: str | None
    model: str | None
    effort: str | None
    tokens: int | None
    fallback: bool


class Block(NamedTuple):
    """A run's heading, and its lines to the next heading, blank lines skipped."""

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


def create(log: Path, change: str, folder: int | None = None) -> None:
    """Create the log holding its title, in `folder` if given, through no link.

    A log that stands is left as it is.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    name = log if folder is None else log.name
    try:
        fd = os.open(name, flags, 0o644, dir_fd=folder)
    except FileExistsError:
        return
    with os.fdopen(fd, "w") as file:
        file.write(f"{title(change)}\n")


def heading(number: int, now: datetime, mark: str | None) -> str:
    """Return a run's heading, with its mark when one is given.

    e.g. 4, 2026-11-05 10:04, "grant" → "## Run 4 — 2026-11-05 10:04 · grant"
    """
    line = f"{HEADING} {number} — {now:%Y-%m-%d %H:%M}"
    return line if mark is None else f"{line} · {mark}"


def mark_of(line: str) -> str | None:
    """Return the text after a heading's first ` · `, stripped, or None.

    e.g. "## Run 3 — d · catch-up " → "catch-up"
    """
    return line.partition(" · ")[2].strip() or None


def marked(line: str, mark: str) -> bool:
    """Return whether a heading's mark is `mark`."""
    return mark_of(line) == mark


def is_heading(line: str) -> bool:
    """Return whether a line is a run's heading."""
    return line.startswith(HEADING)


def parse_event(line: str) -> Event | None:
    """Return the event a stripped line holds in the spec's form, or None.

    The detail is optional.
    e.g. "10:00:00 · round 12 · fix — R1" → Event(12, "fix", "R1")
    """
    found = EVENT.match(line.strip())
    return Event(int(found[1]), found[2], found[3] or "") if found else None


def is_event(line: str, name: str) -> bool:
    """Return whether a line holds the event `name`, its detail aside.

    e.g. "10:00:00 · round 1 · done — ok", "done" → True
    """
    event = parse_event(line)
    return event is not None and event.name == name


def ends(line: str) -> str | None:
    """Return `done` or `halt` for a line that ends a run, else None."""
    event = parse_event(line)
    return event.name if event is not None and event.name in ENDS else None


def _heading_at(lines: list[str]) -> int | None:
    """Return the index of the first heading in `lines`, or None."""
    return next((i for i, line in enumerate(lines) if is_heading(line)), None)


def newest(text: str) -> Block | None:
    """Return the newest run's heading and its lines, or None with no run."""
    lines = text.splitlines()
    at = _heading_at(lines)
    if at is None:
        return None
    run = itertools.takewhile(lambda line: not is_heading(line), lines[at + 1 :])
    return Block(lines[at], [line for line in run if line.strip()])


def latest(text: str) -> Run:
    """Return the newest run's mark and events; no run has no event."""
    block = newest(text)
    if block is None:
        return Run(None, [])
    events = [event for event in map(parse_event, block.lines) if event]
    return Run(mark_of(block.heading), events)


def runs(text: str) -> list[Section]:
    """Return every run of the log's text, newest first, as a `Section`.

    A line that starts `## Run` is a heading; its number is the ASCII digits after
    `## Run `, None with none. No date and no clock is read. Why: 0161-viewer D41.
    """
    found: list[Section] = []
    for line in text.splitlines():
        if is_heading(line):
            number = _NUMBER.match(line)
            found.append(Section(int(number[1]) if number else None, mark_of(line), []))
        elif found and (event := parse_event(line)):
            found[-1].events.append(event)
    return found


def spent(
    models: tuple[str, str | None, str | None], tokens: int | None, fallback: bool | str
) -> str:
    """Return the executor, model, effort and tokens a checker spent, as the log shows.

    A fallback of any string reads as a failure; None tokens read `unavailable`.
    e.g. ("claude", None, "high"), 5, False → "executor claude · model default · …"
    """
    executor, model, effort = models
    shown = "unavailable" if tokens is None else tokens
    text = (
        f"executor {executor} · model {model or 'default'}"
        f" · effort {effort or 'default'} · tokens {shown}"
    )
    if isinstance(fallback, str):
        return f"{text} · {FAILED}"
    return text + (f" · {FALLBACK}" if fallback else "")


def verdicts_line(role: str, verdict: str, open_blocking: int, spent: str) -> str:
    """Return the `verdicts` event's text converge writes for a role.

    e.g. "conformance", "clean", 0, "tokens 5" →
    "verdicts — conformance clean · open_blocking 0 · tokens 5"
    """
    return f"verdicts — {role} {verdict} · open_blocking {open_blocking} · {spent}"


def verdicts(event: Event) -> Verdicts | None:
    """Return the fields of a `verdicts` event, or None for any other event.

    A fallback is either fallback phrase as a field of the detail; a field it lacks is
    None, as is a token count that is no ASCII number. Why: 0161-viewer design D34.
    """
    found = _VERDICTS.fullmatch(event.detail) if event.name == "verdicts" else None
    if found is None:
        return None
    fields = dict(_SPENT.findall(found[2]))
    tokens = fields.get("tokens")
    parts = found[2].split(" · ")
    return Verdicts(
        found[1],
        fields.get("executor"),
        fields.get("model"),
        fields.get("effort"),
        int(tokens) if tokens and tokens.isascii() and tokens.isdigit() else None,
        FALLBACK in parts or FAILED in parts,
    )


def names_lock(text: str) -> bool:
    """Return whether a halt names the debt lock or its old name.

    e.g. "waited for .minions/debt.lock" → True; "waited for debt.lock" → False
    """
    here = Path()
    locks = (layout.debt_lock(here), layout.backlog_lock(here))
    return any(str(lock) in text for lock in locks)


def names_worker(text: str) -> bool:
    """Return whether a halt names a worker's exit or timeout.

    e.g. "converge-fix-r1 worker exit 1" → True; "gate_run.py exit 2" → False
    Why: 0145-halts-alone design D6.
    """
    return WORKER.search(text) is not None


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
    block = newest(text)
    if at is None or block is None:
        raise Refused(f"no {HEADING} heading")
    written = [f"{now:%H:%M:%S} · {event}" for event in events]
    if ended := next((e for e in map(ends, written[:-1]) if e), None):
        raise Refused(f"{ended} goes last in a call")
    top = next(iter(block.lines), "")
    if (ended := ends(top)) and not (ended == "halt" and names_lock(top)):
        raise Refused(f"the run ends on {ended}: open a {HEADING} for a new event")
    return [*lines[: at + 1], *reversed(written), *lines[at + 1 :]], written


def _refusal(log: Path, error: OSError) -> Refused:
    """Return the refusal an `OSError` at the log reads as."""
    if error.errno == errno.ELOOP:
        return Refused(f"{log} is a link")
    return Refused(f"{log}: {error.strerror}")


def read(log: Path) -> str:
    """Return the log's text, a bad byte replaced, read through no link.

    A link, a file that is no regular file or a missing log raises `Refused`.
    """
    try:
        return statefile.read(log)
    except OSError as error:
        raise _refusal(log, error) from error


@contextlib.contextmanager
def _held(log: Path, folder: int | None) -> Iterator[int]:
    """Yield `folder`, else a descriptor on the log's folder opened by pathname.

    The descriptor opened here makes nothing, and is closed after.
    """
    if folder is not None:
        yield folder
        return
    try:
        fd = os.open(log.parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise _refusal(log, error) from error
    try:
        yield fd
    finally:
        os.close(fd)


def _read_held(log: Path, folder: int) -> str:
    """Return the log's text, read in `folder`; a byte that is not UTF-8 is refused."""
    try:
        data = statefile.read_bytes(log.name, folder=folder)
    except OSError as error:
        raise _refusal(log, error) from error
    try:
        return data.decode()
    except UnicodeDecodeError as error:
        raise Refused(f"{log} holds a byte that is not UTF-8") from error


def stamp(
    log: Path,
    events: list[str],
    run: int | None,
    mark: str | None,
    folder: int | None = None,
) -> list[str]:
    """Write events or a run heading into the log; return the lines written.

    A line break run is one space; one descriptor on the folder holds every step.
    Why: card 0109·S1; 0136-status-log design D7, D8.
    """
    flat = [LINE_BREAKS.sub(" ", event) for event in events]
    with _held(log, folder) as fd:
        lines, written = insert(_read_held(log, fd), flat, run, mark)
        try:
            text = "\n".join(lines) + "\n"
            statefile.write(Path(log.name), text, refuse_link=True, folder=fd)
        except statefile.WriteFailed as failed:
            if failed.error.errno == errno.ELOOP:
                raise Refused(f"{log} is a link") from failed
            if failed.step == "create":
                raise Refused(f"{log.name}.tmp could not be created") from failed
            raise Refused(f"{log.name} could not be replaced") from failed
    return written


def command(
    log: Path,
    events: list[str],
    run: int | None,
    mark: str | None,
    folder: int | None = None,
) -> int:
    """Stamp the log and print each line written, or the refusal; return the exit."""
    try:
        written = stamp(log, events, run, mark, folder)
    except Refused as refused:
        print(f"stamp: cannot stamp — {refused}")
        return 2
    print("\n".join(written))
    return 0


def open_run(
    log: Path, change: str, mark: str | None = None, folder: int | None = None
) -> int:
    """Open the next run, making the log's folder and the log; return the exit.

    The runs are counted by their heading lines. A link at the log raises `Refused`.
    """
    if folder is None:
        log.parent.mkdir(parents=True, exist_ok=True)
    with _held(log, folder) as fd:
        create(log, change, fd)
        try:
            text = statefile.read(log.name, folder=fd)
        except OSError as error:
            raise _refusal(log, error) from error
        return command(log, [], text.count(f"\n{HEADING}") + 1, mark, fd)
