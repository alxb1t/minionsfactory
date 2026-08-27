"""Change-state reader: reconstruct 'where are we' from disk (the change + git)."""

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_CHANGE_PATTERN = re.compile(r"^(\d+)-")
# Anchored with `\A`/`\Z`, not `^`/`$`: in Python `$` also matches immediately
# before a *trailing newline*, and a newline is legal in a POSIX directory name —
# so `0009-evil\n` passed the `$` form and reached the interpolated write grant.
_CHANGE_ID_PATTERN = re.compile(r"\A\d+-[a-z0-9-]+\Z")
_PROGRESS_ITEM = re.compile(r"^- \[([ xX])\]\s*(\d+)\s*[—–-]+\s*(.+?)\s*$")
_CHANGE_ARTIFACTS = ("proposal.md", "design.md", "tasks.md", "specs")
_VERSION_PATTERN = re.compile(r"^v\d+\.\d+$")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a document's leading YAML frontmatter into flat key -> string values."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if not separator:
            continue
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


def read_head(repo: Path) -> str:
    """Return the target repo's current git HEAD commit sha."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


class PlanContractError(ValueError):
    """A change breaks the execution contract — refused at read time with a diagnostic.

    Keeps its name although its subject is now a change: renaming it would touch every
    raise site, every `except` clause in `__main__`, and the preflight's contract, for
    no behavioural payoff.
    """


class PreflightError(Exception):
    """The target repo isn't configured for a run — halt before spending."""


# --- in-tree change-state reader — the reader the driver runs -------------------
#
# Change progress lives in the repo (`openspec/changes/<id>/tasks.md`), no vault hop
# (R5): the reader's only inputs are the repo and a git-head seam, so it structurally
# cannot consult a vault path. `driver.run` reads its state through it.


@dataclass(frozen=True)
class Phase:
    """One ordered phase from a change's tasks.md `## Progress` checklist."""

    index: int
    title: str
    done: bool


@dataclass(frozen=True)
class ChangeState:
    """Where-are-we for an in-tree change: phases, git head + declared version."""

    change_id: str
    phases: tuple[Phase, ...]
    head: str
    version: str

    @property
    def current(self) -> Phase | None:
        """The first unchecked phase, or None when every phase is done (complete)."""
        for phase in self.phases:
            if not phase.done:
                return phase
        return None

    @property
    def is_complete(self) -> bool:
        """Whether every phase is checked off (nothing left to build)."""
        return self.current is None

    @property
    def current_index(self) -> int | None:
        """The current phase's index, or None when complete — the advance cursor."""
        phase = self.current
        return None if phase is None else phase.index


def select_change(repo: Path) -> Path:
    """Return the active change dir under changes/ (highest version-id, no archive/).

    A change dir is named `<version-id>-<slug>` (e.g. `0003-sdd-adoption`); the active
    change is the highest numeric version-id. `changes/archive/` is excluded.
    """
    changes_dir = repo / "openspec" / "changes"
    candidates: list[tuple[int, Path]] = []
    if changes_dir.exists():
        for path in changes_dir.iterdir():
            if not path.is_dir() or path.name == "archive":
                continue
            match = _CHANGE_PATTERN.match(path.name)
            if match is None:
                continue
            candidates.append((int(match.group(1)), path))
    if not candidates:
        raise PlanContractError(
            f"no active change under {changes_dir} — expected a changes/<id>/ dir "
            f"(excluding changes/archive/)"
        )
    best = max(candidates, key=lambda item: item[0])
    change_dir = best[1]
    if not _CHANGE_ID_PATTERN.match(change_dir.name):
        raise PlanContractError(
            f"change id '{change_dir.name}' is malformed — a change dir is named "
            f"'<digits>-<lowercase-slug>'. The id keys the findings path and the "
            f"role's write grant, so it is refused here rather than interpolated"
        )
    return change_dir


def validate_change(change_dir: Path) -> None:
    """Raise PlanContractError if the change is missing any required artifact.

    A well-formed change is `changes/<id>/` containing `proposal.md`, `design.md`,
    `tasks.md`, and a `specs/` delta dir. A missing artifact is refused here, at read
    time, with a diagnostic naming it — never a silent empty state or a late KeyError.
    """
    for artifact in _CHANGE_ARTIFACTS:
        if not (change_dir / artifact).exists():
            raise PlanContractError(
                f"change '{change_dir.name}' is missing '{artifact}' — a well-formed "
                f"change has proposal.md, design.md, tasks.md, and specs/"
            )


def _read_change_artifact(change_dir: Path, name: str) -> str:
    """Read one of a change's artifacts as text, or refuse with a diagnostic.

    An artifact that is unreadable or not valid UTF-8 is a broken change, refused like
    every other contract failure. Without this the decode failure escapes as a
    `UnicodeDecodeError` — a `ValueError` *sibling* of `PlanContractError`, like the
    `JSONDecodeError` the preflight already converts — so a target with a non-UTF-8
    `proposal.md` or `tasks.md` would die on a traceback instead of the preflight
    diagnostic. Not caught as a bare `ValueError`: that would swallow real bugs, and
    `PlanContractError` is itself one, so the catch order would mask contract failures.
    """
    path = change_dir / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise PlanContractError(
            f"change '{change_dir.name}' has a {name} that cannot be read "
            f"({error.strerror})"
        ) from error
    except UnicodeDecodeError as error:
        raise PlanContractError(
            f"change '{change_dir.name}' has a {name} that is not valid UTF-8 — a "
            f"change artifact is read as text ({error.reason} at byte {error.start})"
        ) from error


def read_change_version(change_dir: Path) -> str:
    """Return the release version a change declares in its proposal.md frontmatter.

    The change is the unit of release, so the version travels with it: `proposal.md`
    opens with a `---` fence carrying `version: vX.Y`. Absent, unparseable, or not
    `vX.Y` is refused here, at read time, with a diagnostic naming the file and the
    field — never a version guessed from a filename or a prose header.
    """
    frontmatter = parse_frontmatter(_read_change_artifact(change_dir, "proposal.md"))
    version = frontmatter.get("version", "")
    if not _VERSION_PATTERN.match(version):
        raise PlanContractError(
            f"change '{change_dir.name}' declares no release version — its "
            f"proposal.md must open with leading frontmatter 'version: vX.Y' "
            f"(found: {version!r})"
        )
    return version


def parse_progress(text: str) -> list[Phase]:
    """Parse a tasks.md `## Progress` checklist into ordered phases (checked = done).

    Reads only the `## Progress` section: it opens at the `## Progress` heading and
    closes at the next `## ` heading, so checkbox-shaped lines elsewhere in the file
    (e.g. under a phase's prose) never leak into the phase list.
    """
    phases: list[Phase] = []
    in_progress = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_progress:
                break
            in_progress = stripped == "## Progress"
            continue
        if not in_progress:
            continue
        match = _PROGRESS_ITEM.match(line)
        if match:
            phases.append(
                Phase(
                    index=int(match.group(2)),
                    title=match.group(3).strip(),
                    done=match.group(1).lower() == "x",
                )
            )
    return phases


def read_change_state(
    repo: Path,
    head_reader: Callable[[Path], str] = read_head,
) -> ChangeState:
    """Read where-are-we for the active in-tree change — purely from the repo.

    Resolve the active change dir under `<repo>/openspec/changes/` (highest version-id,
    excluding archive/), refuse a malformed change (contract-guard), parse its
    `tasks.md` progress checklist into ordered phases with the current phase = the first
    unchecked item, and surface the version its `proposal.md` declares. Consults no
    vault path (R5): the only inputs are repo + head reader.
    """
    change_dir = select_change(repo)
    validate_change(change_dir)
    version = read_change_version(change_dir)
    phases = parse_progress(_read_change_artifact(change_dir, "tasks.md"))
    if not phases:
        raise PlanContractError(
            f"change '{change_dir.name}' tasks.md has no '## Progress' checklist"
        )
    return ChangeState(
        change_id=change_dir.name,
        phases=tuple(phases),
        head=head_reader(repo),
        version=version,
    )


def change_advanced(before: ChangeState, after: ChangeState) -> bool:
    """Whether the change advanced: a new commit AND the current-phase index moved.

    The change-state analog of the plan advance signal (`driver.decide`): deterministic,
    no LLM. A checkbox progressing (the current index moves) is trusted only when proven
    by a real commit landing, so the agent it drives cannot game the advance.
    """
    committed = after.head != before.head
    phase_moved = after.current_index != before.current_index
    return committed and phase_moved
