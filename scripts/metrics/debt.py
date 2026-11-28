# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the open cards in the primary's `.minions/debt.md`; none is a gap, not zero.

A card is the title `- **<digits>·<id> — ` that `debtfile.count` reads.
Why: 0030-change-impact design D7.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills"))
import mflib.debtfile
import mflib.layout

TIMEOUT_SECONDS = 600
DEBT = mflib.layout.debt_file(Path())


def cards(root: Path) -> int | None:
    """Return the open cards, or None when the repo keeps no debt file.

    A debt file `debtfile.read` refuses, a link, raises `debtfile.Unreadable`.
    """
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=TIMEOUT_SECONDS,
    ).stdout.strip()
    path = mflib.layout.debt_file(mflib.layout.primary_of(common))
    if not path.is_file():
        return None
    return mflib.debtfile.count(mflib.debtfile.read(path))


if __name__ == "__main__":
    try:
        found = cards(Path.cwd())
    except mflib.debtfile.Unreadable as error:
        sys.exit(f"no {DEBT}: {error.reason}")
    if found is None:
        sys.exit(f"no {DEBT}")
    print(found)
