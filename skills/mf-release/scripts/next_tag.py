# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the tag the next release takes, from the cwd's tags and a bump.

    next_tag.py minor|patch

Exit 0 printed · 2 another bump, or git failed.
Why: 0047-version-at-merge design D2.
"""

import argparse
import re
import subprocess
import sys

TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
TIMEOUT_SECONDS = 60


def next_tag(tags: list[str], bump: str) -> str:
    """Return the tag after the highest `vX.Y.Z` in `tags`, or `v0.1.0` with none.

    e.g. ["v0.9.2", "v0.10.0"], "minor" → "v0.11.0"
    """
    found = [TAG.fullmatch(tag) for tag in tags]
    numbers = [tuple(int(part) for part in match.groups()) for match in found if match]
    if not numbers:
        return "v0.1.0"
    major, minor, patch = max(numbers)
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    return f"v{major}.{minor}.{patch + 1}"


def main(argv: list[str] | None = None) -> int:
    """Print the next tag; return the exit code."""
    parser = argparse.ArgumentParser(description="Print the next release's tag.")
    parser.add_argument("bump", choices=("minor", "patch"))
    args = parser.parse_args(argv)
    try:
        listing = subprocess.run(
            ["git", "tag", "--list", "v*"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"next_tag: cannot run — {error}", file=sys.stderr)
        return 2
    print(next_tag(listing.stdout.split(), args.bump))
    return 0


if __name__ == "__main__":
    sys.exit(main())
