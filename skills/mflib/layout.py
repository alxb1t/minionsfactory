"""Name the run directory's paths, each computed from a primary checkout when asked.

It runs no git: a caller asks git for the common directory, and keeps its own guard.
Why: 0134-run-layout design D1, D2 and D3.
"""

from pathlib import Path

MINIONS = ".minions"
CHANGES = "changes"


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
