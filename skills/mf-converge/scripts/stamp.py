# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a converge status-log event or run heading with the clock's time.

    stamp.py <log> '<round N · event — detail>'
    stamp.py <log> --run <N> [--mark <mark>]

An event goes directly under the first `## Run` line; a run heading directly under
the `# ` title, a blank line before the older runs. Prints the line written. Exit 0,
or 2 with `stamp: cannot stamp — …` and the log unchanged; a log that is a link is
refused, as `gate_run.py` refuses one.
Why: 0088-paydown-2 design D7.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

USAGE = "give one event, or --run with an optional --mark"


class Stop(Exception):
    """End the run with the reason it prints, and exit 2."""


def _now() -> datetime:
    """Return the local time."""
    return datetime.now()


def stamp(
    text: str, event: str | None, run: int | None, mark: str | None
) -> tuple[list[str], str]:
    """Return the log's lines with the new line inserted, and that line.

    e.g. the lines "# t", "", "## Run 1 — d" and the event "round 1 · go" →
    "10:02:03 · round 1 · go", inserted after "## Run 1 — d"
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
        return [lines[0], "", line, *(["", *rest] if rest else [])], line
    at = next((i for i, line in enumerate(lines) if line.startswith("## Run")), None)
    if at is None:
        raise Stop("no ## Run heading")
    line = f"{now:%H:%M:%S} · {event}"
    return [*lines[: at + 1], line, *lines[at + 1 :]], line


def write(log: Path, text: str) -> None:
    """Replace the log with `text`, through a staged file that refuses a link.

    A worker can write the run directory, so nothing is written through a link: the
    staged `.tmp` is removed, created anew with `O_NOFOLLOW`, then renamed over the log.
    """
    staged = log.with_name(f"{log.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(text)
    except OSError as error:
        raise Stop(f"{staged.name} could not be created") from error
    staged.replace(log)


def main(argv: list[str] | None = None) -> int:
    """Stamp one line into a status log; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Write a status-log event or run heading with the clock's time."
    )
    parser.add_argument("log", type=Path, help="the status log")
    parser.add_argument("event", nargs="?", help="'round N · event — detail'")
    parser.add_argument("--run", type=int, help="open run N under the title")
    parser.add_argument("--mark", help="the run heading's mark, e.g. catch-up")
    args = parser.parse_args(argv)
    try:
        if (args.event is None) == (args.run is None) or (
            args.mark is not None and args.run is None
        ):
            raise Stop(USAGE)
        if args.log.is_symlink():
            raise Stop(f"{args.log} is a link")
        try:
            text = args.log.read_text()
        except OSError as error:
            raise Stop(f"{args.log}: {error.strerror}") from error
        lines, line = stamp(text, args.event, args.run, args.mark)
        write(args.log, "\n".join(lines) + "\n")
    except Stop as stop:
        print(f"stamp: cannot stamp — {stop}")
        return 2
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
