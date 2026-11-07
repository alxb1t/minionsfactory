# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write a converge status-log event or run heading with the clock's time.

    stamp.py <log> '<round N · event — detail>'
    stamp.py <log> --run <N> [--mark <mark>]

An event goes directly under the first `## Run` line; a run heading directly under
the `# ` title, a blank line before the older runs. Prints the line written. Exit 0,
or 2 with `stamp: cannot stamp — …` and the log unchanged.
Why: 0088-paydown-2 design D7.
"""

import argparse
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
        try:
            text = args.log.read_text()
        except OSError as error:
            raise Stop(f"{args.log}: {error.strerror}") from error
        lines, line = stamp(text, args.event, args.run, args.mark)
        args.log.write_text("\n".join(lines) + "\n")
    except Stop as stop:
        print(f"stamp: cannot stamp — {stop}")
        return 2
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
