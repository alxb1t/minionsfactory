# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Write converge status-log events or a run heading with the clock's time.

Why: 0088-paydown-2 design D7; 0100-worker-diet design D9;
0109-converge-done-order design D1; 0136-status-log design D10.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.statuslog

USAGE = "give events, or --run with an optional --mark"


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
    if (not args.event) == (args.run is None) or (
        args.mark is not None and args.run is None
    ):
        print(f"stamp: cannot stamp — {USAGE}")
        return 2
    return mflib.statuslog.command(args.log, args.event, args.run, args.mark)


if __name__ == "__main__":
    sys.exit(main())
