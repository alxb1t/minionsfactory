# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write converge status-log events or a run heading with the clock's time.

    stamp.py <log> '<round N · event — detail>' ['<event>' …]
    stamp.py <log> --run <N> [--mark <mark>]

Events go under the first `## Run`, the last given on top. Exit 0, or 2 with
`stamp: cannot stamp — …`, the log unchanged: a link, a misordered `done` or `halt`.
Why: 0088-paydown-2 design D7; 0100-worker-diet design D9;
0109-converge-done-order design D1.
"""

import argparse
import contextlib
import errno
import os
import sys
from datetime import datetime
from pathlib import Path

USAGE = "give events, or --run with an optional --mark"
LOCKS = (".minions/debt.lock", ".minions/backlog.lock")


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _now() -> datetime:
    """Return the local time."""
    return datetime.now()


def _ends(line: str) -> str | None:
    """Return `done` or `halt` for an event line that ends a run, else None.

    e.g. "10:00:00 · round 1 · done — ok" → "done"
    """
    name = line.split(" — ", maxsplit=1)[0]
    return next((e for e in ("done", "halt") if name.endswith(f" · {e}")), None)


def stamp(
    text: str, events: list[str], run: int | None, mark: str | None
) -> tuple[list[str], list[str]]:
    """Return the log's lines with the new lines inserted, and those lines.

    e.g. the lines "# t", "", "## Run 1 — d" and the events "round 1 · go" and
    "round 1 · on" → "10:02:03 · round 1 · on" then "10:02:03 · round 1 · go",
    inserted after "## Run 1 — d"; a misordered `done` or `halt` raises `Stop`
    """
    lines = text.splitlines()
    now = _now()
    if run is not None:
        if not lines or not lines[0].startswith("# "):
            raise Stop("no # title")
        line = f"## Run {run} — {now:%Y-%m-%d %H:%M}"
        if mark is not None:
            line += f" · {mark}"
        rest = lines[1:]
        while rest and not rest[0].strip():
            rest.pop(0)
        return [lines[0], "", line, *(["", *rest] if rest else [])], [line]
    at = next((i for i, line in enumerate(lines) if line.startswith("## Run")), None)
    if at is None:
        raise Stop("no ## Run heading")
    if ended := next((e for e in map(_ends, events[:-1]) if e), None):
        raise Stop(f"{ended} goes last in a call")
    top = next((line for line in lines[at + 1 :] if line.strip()), "")
    if (ended := _ends(top)) and not (ended == "halt" and any(k in top for k in LOCKS)):
        raise Stop(f"the run ends on {ended}: open a ## Run for a new event")
    written = [f"{now:%H:%M:%S} · {event}" for event in events]
    return [*lines[: at + 1], *reversed(written), *lines[at + 1 :]], written


def read(log: Path) -> str:
    """Return the log's text, read through one descriptor that refuses a link.

    One `O_NOFOLLOW` open checks and reads, so a link swapped in after a check by name
    has no outside file's text copied into the log.
    """
    try:
        with os.fdopen(os.open(log, os.O_RDONLY | os.O_NOFOLLOW)) as file:
            return file.read()
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise Stop(f"{log} is a link") from error
        raise Stop(f"{log}: {error.strerror}") from error


def write(log: Path, text: str) -> None:
    """Replace the log with `text`, through a staged file that refuses a link.

    A worker can write the run directory, so nothing is written through a link: the
    staged `.tmp` is removed, created anew with `O_NOFOLLOW`, then renamed over the log.
    A rename that fails removes the `.tmp` and leaves the log as it stood.
    """
    staged = log.with_name(f"{log.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(text)
    except OSError as error:
        raise Stop(f"{staged.name} could not be created") from error
    try:
        staged.replace(log)
    except OSError as error:
        with contextlib.suppress(OSError):
            staged.unlink()
        raise Stop(f"{log.name} could not be replaced") from error


def main(argv: list[str] | None = None) -> int:
    """Stamp events or a run heading into a status log; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write status-log events or a run heading with the clock's time."
    )
    parser.add_argument("log", type=Path, help="the status log")
    parser.add_argument("event", nargs="*", help="'round N · event — detail'")
    parser.add_argument("--run", type=int, help="open run N under the title")
    parser.add_argument("--mark", help="the run heading's mark, e.g. catch-up")
    args = parser.parse_args(argv)
    try:
        if (not args.event) == (args.run is None) or (
            args.mark is not None and args.run is None
        ):
            raise Stop(USAGE)
        text = read(args.log)
        lines, written = stamp(text, args.event, args.run, args.mark)
        write(args.log, "\n".join(lines) + "\n")
    except Stop as stop:
        print(f"stamp: cannot stamp — {stop}")
        return 2
    print("\n".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
