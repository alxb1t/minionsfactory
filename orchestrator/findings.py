"""Findings-file reader: a role's convergence verdict, read + validated from disk."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from orchestrator.state import parse_frontmatter


def findings_dir(repo: Path) -> Path:
    """Resolve the directory every findings file lives in: `<repo>/.minions/findings/`.

    Exists so the fan-out can create the directory without rebuilding the path: the
    single-resolution-site rule the findings contract states covers the directory as
    well as the file, and a literal `.minions/findings` elsewhere would keep creating
    the old location on the day this one moves.
    """
    return repo / ".minions" / "findings"


def findings_path(repo: Path, change_id: str, role: str) -> Path:
    """Resolve a role's findings file: `<repo>/.minions/findings/<change-id>_<role>.md`.

    The single resolution site: the fan-out, the converge loop and the release stage
    all resolve a findings path through here, so the location is one edit away and the
    three stages cannot drift. The root is the **repository being built** — findings are
    run artefacts of that repo (`.minions/` is gitignored), so nothing resolves outside
    it. Keyed on the **change id** — the same identifier as the change directory and the
    `Change:` commit trailer — not on the release version, which is a property of the
    change rather than its name.
    """
    return findings_dir(repo) / f"{change_id}_{role}.md"


class FindingsState(BaseModel):
    """A role's findings verdict, read from the file's frontmatter (trust boundary)."""

    model_config = ConfigDict(frozen=True)
    verdict: Literal["clean", "changes-requested"]
    open_blocking: int
    round: int
    head: str


def read_findings_state(path: Path) -> FindingsState | None:
    """Read a findings file into a validated state; a missing file → None."""
    if not path.exists():
        return None
    return FindingsState.model_validate(parse_frontmatter(path.read_text()))


def all_findings_clean(states: Sequence[FindingsState | None]) -> bool:
    """Whether every findings file is present and its verdict is clean.

    A missing file (None) counts as not clean, so a not-yet-run role can never
    let the loop converge — or the release gate pass — falsely.
    """
    return all(s is not None and s.verdict == "clean" for s in states)
