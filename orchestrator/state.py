"""Plan-state reader: reconstruct 'where are we' from disk (plan + git)."""

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_PLAN_PATTERN = re.compile(r"v(\d+)\.(\d+)_.*implementation_plan\.md$")
_CODE_PHASE_STATUSES = frozenset({"done", "wip", "planned", "todo"})
_CHANGE_PATTERN = re.compile(r"^(\d+)-")
_PROGRESS_ITEM = re.compile(r"^- \[([ xX])\]\s*(\d+)\s*[—–-]+\s*(.+?)\s*$")
_CHANGE_ARTIFACTS = ("proposal.md", "design.md", "tasks.md", "specs")


def select_plan(vault_project_dir: Path) -> Path:
    """Return the highest-version plan in implementation_plans/, ignoring archive/."""
    plans_dir = vault_project_dir / "implementation_plans"
    candidates: list[tuple[tuple[int, int], Path]] = []
    for path in plans_dir.glob("v*implementation_plan.md"):
        match = _PLAN_PATTERN.match(path.name)
        if match is None:
            continue
        version = (int(match.group(1)), int(match.group(2)))
        candidates.append((version, path))
    best = max(candidates, key=lambda item: item[0])
    return best[1]


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a plan's leading YAML frontmatter into flat key -> string values."""
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


@dataclass(frozen=True)
class PlanState:
    """Where-are-we, read from disk: the plan's phase pointer + git head."""

    current_phase: str
    phases: dict[str, str]
    head: str


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


def read_plan_state(
    vault_project_dir: Path,
    repo: Path,
    head_reader: Callable[[Path], str] = read_head,
) -> PlanState:
    """Read where-are-we from disk.

    The highest-version plan's phase state + the repo's git head.
    """
    plan_path = select_plan(vault_project_dir)
    frontmatter = parse_frontmatter(plan_path.read_text())
    validate_plan(frontmatter)
    phases = {
        key: value for key, value in frontmatter.items() if key.startswith("phase")
    }
    return PlanState(
        current_phase=frontmatter["current_phase"],
        phases=phases,
        head=head_reader(repo),
    )


class PlanContractError(ValueError):
    """A plan breaks the execution contract — refused at read time with a diagnostic."""


def validate_plan(frontmatter: dict[str, str]) -> None:
    """Raise PlanContractError if the plan frontmatter breaks the execution contract.

    The contract: a YAML frontmatter fence carrying `current_phase` and at least one
    `phaseN` flag, each with a recognized code-phase status (execution plans contain
    only code phases). A malformed plan is refused here, at read time — never a silent
    empty `{}`, a mid-run KeyError, or a non-code phase the driver would false-halt on.
    """
    if not frontmatter:
        raise PlanContractError("plan has no YAML frontmatter (expected a --- fence)")
    if "current_phase" not in frontmatter:
        raise PlanContractError("plan frontmatter is missing 'current_phase'")
    phases = {
        key: value for key, value in frontmatter.items() if key.startswith("phase")
    }
    if not phases:
        raise PlanContractError("plan frontmatter has no phaseN flags")
    for name, status in phases.items():
        if status not in _CODE_PHASE_STATUSES:
            raise PlanContractError(
                f"plan phase '{name}' has non-code status '{status}' — "
                f"execution plans contain only code phases "
                f"(expected one of {sorted(_CODE_PHASE_STATUSES)})"
            )


class PreflightError(Exception):
    """The target repo isn't configured for a run — halt before spending."""


def _covers(directory: Path, target: Path) -> bool:
    """Whether `directory` is `target` or an ancestor of it."""
    return target.is_relative_to(directory)


def verify_vault_access(repo: Path, vault_project_dir: Path) -> None:
    """Raise PreflightError unless the target grants the coder vault write access.

    The coder and read-only roles write vault files (findings, bookkeeping) that live
    OUTSIDE the repo cwd, so the target's `.claude/settings.local.json` must list the
    vault (or an ancestor) under `additionalDirectories`. Checked before any spawn, so
    a misconfigured target halts before spending, not mid-run.
    """
    settings_path = repo / ".claude" / "settings.local.json"
    if not settings_path.exists():
        raise PreflightError(
            f"no .claude/settings.local.json in {repo} — the target must grant the "
            f"coder write access to the vault ({vault_project_dir})"
        )
    settings = json.loads(settings_path.read_text())
    permissions = settings.get("permissions", {})
    granted = [
        *permissions.get("additionalDirectories", []),
        *settings.get("additionalDirectories", []),
    ]
    if not any(_covers(Path(directory), vault_project_dir) for directory in granted):
        raise PreflightError(
            f"the target's .claude/settings.local.json does not grant vault access "
            f"({vault_project_dir}) via additionalDirectories"
        )


# --- in-tree change-state reader (sibling to the vault-plan reader above) ---------
#
# Change progress lives in the repo (`openspec/changes/<id>/tasks.md`), no vault hop
# (R5). This reader is built and unit-tested here as a ready-for-v0.5 sibling; the
# driver keeps running the vault-plan reader until the loop self-hosts on changes.


@dataclass(frozen=True)
class Phase:
    """One ordered phase from a change's tasks.md `## Progress` checklist."""

    index: int
    title: str
    done: bool


@dataclass(frozen=True)
class ChangeState:
    """Where-are-we for an in-tree change: ordered phases + git head, read from disk."""

    change_id: str
    phases: tuple[Phase, ...]
    head: str

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
    return best[1]


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
    excluding archive/), refuse a malformed change (contract-guard), and parse its
    `tasks.md` progress checklist into ordered phases with the current phase = the first
    unchecked item. Consults no vault path (R5): the only inputs are repo + head reader.
    """
    change_dir = select_change(repo)
    validate_change(change_dir)
    phases = parse_progress((change_dir / "tasks.md").read_text())
    if not phases:
        raise PlanContractError(
            f"change '{change_dir.name}' tasks.md has no '## Progress' checklist"
        )
    return ChangeState(
        change_id=change_dir.name,
        phases=tuple(phases),
        head=head_reader(repo),
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
