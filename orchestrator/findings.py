"""Findings-file reader: a role's convergence verdict, read + validated from disk."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from orchestrator.state import parse_frontmatter


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
