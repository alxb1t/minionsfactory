"""The old layout's entries as literals, each mapped to its name in the change's folder.

Why: 0134-run-layout design D5, D11.
"""

from pathlib import Path

ENTRIES = {
    "findings/{}_review.md": "conformance.md",
    "findings/{}_security.md": "adversarial.md",
    "findings/{}_status_log.md": "status_log.md",
    "findings/{}_diff.patch": "diff.patch",
    "models/{}.toml": "models.toml",
    "integrate/{}.md": "integrate.md",
    "integrate/{}.red": "integrate.red",
    "integrate/{}.resolved": "integrate.resolved",
    "build/{}.done": "build.done",
    "build/{}.halt": "build.halt",
    "build/{}.closing": "build.closing",
    "build/{}.discarded.patch": "build.discarded.patch",
    "rescue/{}.md": "rescue.md",
    "release/{}.held": "release.held",
    "gate-check/{}": "gate-check",
}
ROLES = {
    "changes/{}/review.md": "conformance.md",
    "changes/{}/security.md": "adversarial.md",
}
LOG = {
    "runs/20261101-230000/{}_converge-2.log": "logs/20261101-230000-converge-2.log",
}


def plant(minions: Path, change: str, old: str) -> Path:
    """Write the one file at the change's old path under `minions`, and return it."""
    path = minions / old.format(change)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("old\n")
    return path
