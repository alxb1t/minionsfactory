"""Name the run directory's paths, each computed when asked, and its old layout.

It runs no git: a caller asks git for the common directory, and keeps its own guard.
Why: 0134-run-layout design D1, D2 and D3.
"""

import os
import re
from pathlib import Path

MINIONS = ".minions"
CHANGES = "changes"
# Each old-layout path of a change, by its name in the change's folder.
# Why: 0080-minions-layout design D1, D4; 0095-converge-roles design D2.
OLD_LAYOUT = {
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
# A change folder's old findings names. Why: 0095-converge-roles design D2.
OLD_ROLES = {"review.md": "conformance.md", "security.md": "adversarial.md"}
OLD_ID = r"(\d{4}-[a-z0-9-]+)"
OLD_STAMP = re.compile(r"\d{8}-\d{6}(?:-\d+)?")
OLD_LOG = re.compile(rf"{OLD_ID}_([a-z][a-z-]*?)(-\d+)?\.log")


def primary_of(common: str | Path) -> Path:
    """Return the primary checkout of git's common directory, as git gave it.

    e.g. "<primary>/.git" → <primary>
    """
    return Path(common).parent


def run_dir(primary: Path) -> Path:
    """Return the primary's run directory.

    e.g. <primary> → <primary>/.minions
    """
    return primary / MINIONS


def change_dir(primary: Path, change: str) -> Path:
    """Return the change's folder in the run directory.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo
    """
    return run_dir(primary) / CHANGES / change


def runs_dir(primary: Path) -> Path:
    """Return the folder of the runs' logs and their claim."""
    return run_dir(primary) / "runs"


def claim_file(primary: Path) -> Path:
    """Return the live run's claim.

    e.g. <primary> → <primary>/.minions/runs/active
    """
    return runs_dir(primary) / "active"


def debt_file(primary: Path) -> Path:
    """Return the repo's debt file."""
    return run_dir(primary) / "debt.md"


def debt_lock(primary: Path) -> Path:
    """Return the lock a writer of the debt file holds."""
    return run_dir(primary) / "debt.lock"


def backlog_file(primary: Path) -> Path:
    """Return the debt file's old name, read when no debt file stands."""
    return run_dir(primary) / "backlog.md"


def backlog_lock(primary: Path) -> Path:
    """Return the debt lock's old name."""
    return run_dir(primary) / "backlog.lock"


def gate_dir(primary: Path) -> Path:
    """Return the folder of the gate's green records."""
    return run_dir(primary) / "gate"


def cut_reservation(primary: Path, change: str) -> Path:
    """Return the file that reserves a change's id for its cut.

    e.g. "0001-todo" → <primary>/.minions/cuts/0001-todo
    """
    return run_dir(primary) / "cuts" / change


def metrics_page(primary: Path, change: str) -> Path:
    """Return the change's metrics page.

    e.g. "0001-todo" → <primary>/.minions/metrics/0001-todo.html
    """
    return run_dir(primary) / "metrics" / f"{change}.html"


def old_files(primary: Path) -> dict[str, list[tuple[Path, str]]]:
    """Return each change's old-layout files, each with its path in the change's folder.

    Why: 0080-minions-layout design D4; 0095-converge-roles design D2.
    """
    minions = run_dir(primary)
    found: dict[str, list[tuple[Path, str]]] = {}
    for old, new in OLD_LAYOUT.items():
        folder, name = old.split("/")
        pattern = re.compile(re.escape(name).replace(re.escape("{}"), OLD_ID))
        listed = (minions / folder).iterdir() if (minions / folder).is_dir() else ()
        for path in listed:
            if matched := pattern.fullmatch(path.name):
                found.setdefault(matched[1], []).append((path, new))
    changes = minions / CHANGES
    folders = sorted(changes.iterdir()) if changes.is_dir() else []
    for folder in (f for f in folders if f.is_dir()):
        for name, new in OLD_ROLES.items():
            if os.path.lexists(folder / name):
                found.setdefault(folder.name, []).append((folder / name, new))
    runs = runs_dir(primary)
    stamps = runs.iterdir() if runs.is_dir() else ()
    for stamp in (s for s in stamps if OLD_STAMP.fullmatch(s.name) and s.is_dir()):
        for path in stamp.iterdir():
            if matched := OLD_LOG.fullmatch(path.name):
                change, station, n = matched[1], matched[2], matched[3] or ""
                new = f"logs/{stamp.name}-{station}{n}.log"
                found.setdefault(change, []).append((path, new))
    return found


def old_layout(primary: Path, change: str) -> str | None:
    """Return the change's first old-layout file, relative to the primary, or None.

    Why: 0080-minions-layout design D4.
    """
    held = sorted(path for path, _ in old_files(primary).get(change, []))
    return str(held[0].relative_to(primary)) if held else None
