"""Read the forms an old run left: an old role's verdicts count, a `## Refused` section.

It reads and writes nothing, and no station loads it.
Why: 0162-metric-scripts design D5.
"""

import itertools
import re

from . import statuslog

REFUSED = "## Refused"
_OLD_ROLES = ("review ", "security ")
_OPEN = " · open_blocking "
_COUNT = re.compile(r"[0-9]{1,18}(?![0-9])")
_COLON = re.compile(r"open_blocking: ([0-9]{1,18})(?![0-9])")


def blocking(event: statuslog.Event) -> int | None:
    """Return the count a `verdicts` event of an old form holds, or None.

    e.g. detail "review changes-requested · open_blocking 2 (R1, R2)" → 2
    e.g. detail "review verdict: clean; open_blocking: 0; scope 3" → 0
    """
    if event.name != "verdicts":
        return None
    old = event.detail.startswith(_OLD_ROLES)
    if old and (found := _COUNT.match(event.detail.partition(_OPEN)[2])):
        return int(found[0])
    colon = _COLON.search(event.detail)
    return int(colon[1]) if colon else None


def refuted(text: str) -> list[str] | None:
    r"""Return the top-level `- ` lines of the `## Refused` section, None without one.

    e.g. "## Refused\n- a\n## Next\n" → ["- a"]
    """
    lines = text.splitlines()
    at = next((i for i, line in enumerate(lines) if line.startswith(REFUSED)), None)
    if at is None:
        return None
    rest = itertools.takewhile(lambda line: not line.startswith("## "), lines[at + 1 :])
    return [line for line in rest if line.startswith("- ")]
