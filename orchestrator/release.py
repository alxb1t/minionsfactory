"""Release automation: verify the release gate, then prepare the release."""

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from orchestrator.findings import FindingsState, all_findings_clean
from orchestrator.gate import GateResult
from orchestrator.specs import check as _specs_check

_FOLD_SECTION_RE = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED)\s+Requirements", re.IGNORECASE
)
_REQUIREMENT_RE = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$")


@dataclass(frozen=True)
class Commit:
    """A base..HEAD commit and its `Change:` trailer value (None when absent).

    Gathered by the effectful caller so the trailer predicate stays pure.
    """

    sha: str
    change: str | None


def _backlog_blocker(backlog_text: str, version: str) -> str | None:
    """Why the backlog blocks release, or None when current-release section is clear.

    Fail-closed: a missing `## Current release (`version`)` section is treated as
    a malformed backlog (a release-blocking reason), never as an all-clear.
    """
    in_section = False
    seen_section = False
    for line in backlog_text.splitlines():
        if line.startswith("## "):
            in_section = line.startswith("## Current release") and f"{version}" in line
            seen_section = seen_section or in_section
            continue
        if in_section and line.lstrip().startswith("- [ ]"):
            return f"backlog: open item in the {version} current-release section"
    if not seen_section:
        return f"backlog: no current-release section for {version}"
    return None


def _changelog_blocker(changelog_text: str) -> str | None:
    """Why the CHANGELOG blocks release, or None when [Unreleased] has entries.

    Fail-closed: a missing `## [Unreleased]` section, or one with no `- ` entry
    (nothing to release), is a release-blocking reason.
    """
    in_section = False
    seen_section = False
    for line in changelog_text.splitlines():
        if line.startswith("## "):
            in_section = line.startswith("## [Unreleased]")
            seen_section = seen_section or in_section
            continue
        if in_section and line.lstrip().startswith("- "):
            return None
    if not seen_section:
        return "changelog: no [Unreleased] section"
    return "changelog: [Unreleased] has no entries"


@dataclass(frozen=True)
class ReleaseVerdict:
    """The release gate's verdict: releasable, or blocked with a reason."""

    ok: bool
    reason: str


def _gate_blocker(gate_result: GateResult) -> str | None:
    """Why the gate blocks release, or None when it is green."""
    return None if gate_result.passed else "gate is red"


def _findings_blocker(findings: Sequence[FindingsState | None]) -> str | None:
    """Why the findings block release, or None when all are clean."""
    if all_findings_clean(findings):
        return None
    return "findings: review/security/simplify are not all clean"


def _tag_blocker(existing_tags: Sequence[str], version: str) -> str | None:
    """Why the release tag is unavailable, or None when it is free."""
    tag = f"{version}.0"
    if tag in existing_tags:
        return f"tag {tag} already exists"
    return None


def _tree_blocker(tree_is_clean: bool) -> str | None:
    """Why the working tree blocks release, or None when it is clean."""
    return None if tree_is_clean else "working tree has uncommitted changes"


def _specs_blocker(specs_valid: bool, change_folded: bool) -> str | None:
    """Why the specs block release, or None when specs validate and the change folded.

    A pure predicate over facts the caller gathered (running the spec validator and
    checking whether the active change's delta has been folded into top-level `specs/`).
    """
    if not specs_valid:
        return "specs: invalid after fold"
    if not change_folded:
        return "specs: active change is not folded into specs/"
    return None


def _trailer_blocker(
    commits: Sequence[Commit], known_change_ids: Sequence[str]
) -> str | None:
    """Why the commit trailers block release, or None when every commit resolves.

    Every `base..HEAD` commit must carry a `Change:` trailer whose id resolves to a
    known (active or archived) change; a commit missing the trailer, or carrying one
    that resolves to no known change, blocks and is named. Pure — the commit list and
    the known-id set are gathered by the effectful caller.
    """
    for commit in commits:
        if commit.change is None:
            return f"commit {commit.sha} has no Change: trailer"
        if commit.change not in known_change_ids:
            return (
                f"commit {commit.sha} trailer '{commit.change}' "
                f"resolves to no known change"
            )
    return None


def verify_release_gate(
    version: str,
    gate_result: GateResult,
    findings: Sequence[FindingsState | None],
    backlog_text: str,
    changelog_text: str,
    existing_tags: Sequence[str],
    tree_is_clean: bool,
    specs_valid: bool = True,
    change_folded: bool = True,
    commits: Sequence[Commit] = (),
    known_change_ids: Sequence[str] = (),
) -> ReleaseVerdict:
    """Verify every release precondition; return ok, or the first blocking reason.

    Pure — the release-time analog of `driver.decide`: it judges over
    already-gathered facts. The effectful gathering (running the gate, reading
    the backlog/changelog, listing git tags, checking the tree, running the spec
    validator, and reading the commit trailers) lives in the caller, so the whole
    gate is one first-non-None scan over the blockers.
    """
    for blocker in (
        _gate_blocker(gate_result),
        _findings_blocker(findings),
        _backlog_blocker(backlog_text, version),
        _tag_blocker(existing_tags, version),
        _changelog_blocker(changelog_text),
        _tree_blocker(tree_is_clean),
        _specs_blocker(specs_valid, change_folded),
        _trailer_blocker(commits, known_change_ids),
    ):
        if blocker is not None:
            return ReleaseVerdict(ok=False, reason=blocker)

    return ReleaseVerdict(ok=True, reason="")


def _cut_changelog(changelog_text: str, version: str, today: str) -> str:
    """Promote [Unreleased] to a dated release, seeding a fresh empty [Unreleased].

    `## [Unreleased]` becomes `## [X.Y.0] - <today>` (version's leading `v`
    stripped) with a new empty `## [Unreleased]` above it. Only the heading line
    is rewritten, so the entries beneath it move under the dated release.
    """
    number = version.removeprefix("v")
    return changelog_text.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{number}.0] - {today}",
        1,
    )


def _bump_pyproject(pyproject_text: str, version: str) -> str:
    """Bump the first `version = "..."` line to `X.Y.0` (leading `v` stripped).

    A line-anchored regex replace, so comments/formatting are preserved (no TOML
    round-trip, no new dependency). Assumes one project `version` key — true for
    the standard `[project]` layout where it is the first `version = ` line.
    """
    number = version.removeprefix("v")
    return re.sub(
        r'(?m)^version = "[^"]*"',
        f'version = "{number}.0"',
        pyproject_text,
        count=1,
    )


class ReleaseStatus(Enum):
    """Terminal status of release-prep: prepared for the human, or refused."""

    PREPARED = auto()
    REFUSED = auto()


@dataclass(frozen=True)
class ReleaseResult:
    """Outcome of prepare_release: how it ended, why, and the human handoff."""

    status: ReleaseStatus
    reason: str  # "" when prepared; the blocking reason when refused
    handoff: str  # merge+push instructions when prepared; "" when refused


class ReleaseGit(Protocol):
    """The git operations release-prep needs: commit and an annotated local tag.

    Deliberately has no push or merge: the boundary is structural — prepare_release
    can only prepare locally, never ship.
    """

    def commit_all(self, repo: Path, message: str) -> None:
        """Stage every change in `repo` and commit it."""
        ...

    def tag(self, repo: Path, name: str, message: str) -> None:
        """Annotated-tag HEAD in `repo` — local only, never pushed."""
        ...


class SubprocessReleaseGit:
    """Real ReleaseGit: stage+commit and annotated-tag via git (no shell, no push)."""

    def commit_all(self, repo: Path, message: str) -> None:
        """Run: git add -A then git commit -m <message>."""
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)

    def tag(self, repo: Path, name: str, message: str) -> None:
        """Run: git tag -a <name> -m <message> — local, never pushed."""
        subprocess.run(["git", "tag", "-a", name, "-m", message], cwd=repo, check=True)


class FakeReleaseGit:
    """Recording ReleaseGit double for tests — records calls, runs no git."""

    def __init__(self) -> None:
        """Start with empty commit + tag ledgers."""
        self.commits: list[str] = []
        self.tags: list[str] = []

    def commit_all(self, repo: Path, message: str) -> None:
        """Record the commit message."""
        self.commits.append(message)

    def tag(self, repo: Path, name: str, message: str) -> None:
        """Record the tag name."""
        self.tags.append(name)


def _handoff(tag: str, branch: str) -> str:
    """Merge and push instructions printed after a prepared release."""
    return (
        f"Release {tag} prepared on branch {branch} (release commit + local tag).\n"
        f"NOT merged, NOT pushed — over to you:\n\n"
        f"  git checkout main\n"
        f"  git merge --no-ff {branch}\n"
        f"  git push origin main\n"
        f"  git push origin {tag}\n"
    )


def _release_log_entry(tag: str, today: str, branch: str) -> str:
    """Release-log entry in the vault's documented format."""
    number = tag.removeprefix("v")
    return (
        f"## {tag} — {today}\n"
        f"- **Tag:** `{tag}` (created locally; **merged + pushed by a human**)\n"
        f"- **Shipped:** see CHANGELOG `[{number}]`.\n"
        f"- **Gate at ship:** ruff + ty + pytest green.\n"
        f"- **Review/security/simplify:** `verdict: clean`.\n"
        f"- **Branch → main:** `{branch}` → `main`.\n\n"
    )


def _prepend_release_log(path: Path, entry: str) -> None:
    """Insert an entry after the template marker in the vault's release_log.md.

    Entries go directly after the format comment's closing `-->`, so the newest
    sits at the top of the entries region; a file without the marker gets the
    entry appended.
    """
    existing = path.read_text() if path.exists() else ""
    marker = "-->"
    idx = existing.find(marker)
    if idx == -1:
        path.write_text(existing + "\n" + entry)
        return
    cut = idx + len(marker)
    path.write_text(existing[:cut] + "\n\n" + entry + existing[cut:])


def _release_message(tag: str, change_id: str | None) -> str:
    """Build the release commit message, appending a `Change:` trailer when known."""
    message = f"chore(release): {tag}"
    if change_id:
        message += f"\n\nChange: {change_id}"
    return message


def prepare_release(
    verdict: ReleaseVerdict,
    repo: Path,
    vault_dir: Path,
    version: str,
    today: str,
    branch: str,
    git: ReleaseGit,
    change_id: str | None = None,
) -> ReleaseResult:
    """Prepare the release on a green verdict, then hand off to the human; else refuse.

    On a red verdict: do nothing, return REFUSED with the reason. On green: cut the
    CHANGELOG, bump pyproject, commit (with a `Change: <id>` trailer when the change is
    known) + annotated-tag locally, prepend the release log, return PREPARED with the
    merge+push handoff. Never pushes or merges — the git seam has no such operation.
    """
    if verdict.ok is False:
        return ReleaseResult(ReleaseStatus.REFUSED, verdict.reason, "")

    tag = f"{version}.0"

    changelog = repo / "CHANGELOG.md"
    changelog.write_text(_cut_changelog(changelog.read_text(), version, today))
    pyproject = repo / "pyproject.toml"
    pyproject.write_text(_bump_pyproject(pyproject.read_text(), version))

    git.commit_all(repo, _release_message(tag, change_id))
    git.tag(repo, tag, tag)

    _prepend_release_log(
        vault_dir / "release_log.md", _release_log_entry(tag, today, branch)
    )

    return ReleaseResult(ReleaseStatus.PREPARED, "", _handoff(tag, branch))


# --- spec-delta fold: openspec/changes/<id>/specs/ into the living openspec/specs/ ---


@dataclass(frozen=True)
class RequirementBlock:
    """One `### Requirement:` block: its delta section, title, and full text.

    `section` is `""` for a shipped spec, or `ADDED` / `MODIFIED` / `REMOVED` under a
    change delta's section. `text` is the whole block, from its heading to (but not
    including) the next requirement / section heading.
    """

    section: str
    title: str
    text: str


def _parse_requirement_blocks(text: str) -> tuple[str, list[RequirementBlock]]:
    """Split a spec file into its preamble and its ordered requirement blocks.

    The preamble is everything before the first `### Requirement:` heading. Each block
    runs to the next requirement heading or `## ` section heading; a
    `## ADDED/MODIFIED/REMOVED Requirements` line sets the delta section for the blocks
    beneath it (and is not itself part of any block).
    """
    preamble: list[str] = []
    blocks: list[RequirementBlock] = []
    section = ""
    current: tuple[str, str, list[str]] | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            sec, title, lines = current
            while lines and lines[-1].strip() == "":
                lines.pop()
            blocks.append(RequirementBlock(sec, title, "\n".join(lines)))
            current = None

    for line in text.splitlines():
        section_match = _FOLD_SECTION_RE.match(line)
        if section_match:
            flush()
            section = section_match.group(1).upper()
            continue
        requirement_match = _REQUIREMENT_RE.match(line)
        if requirement_match:
            flush()
            current = (section, requirement_match.group(1).strip(), [line])
            continue
        if line.startswith("## "):  # a non-requirements section heading ends a block
            flush()
            if not blocks:
                preamble.append(line)
            continue
        if current is not None:
            current[2].append(line)
        elif not blocks:
            preamble.append(line)
    flush()
    return "\n".join(preamble).rstrip(), blocks


def _apply_fold(
    target_text: str, delta_blocks: list[RequirementBlock], capability: str
) -> tuple[str, list[tuple[str, str]]]:
    """Apply a delta's requirement blocks to a target spec; return (new_text, edits).

    ADDED/MODIFIED upsert the requirement by title (replace the whole block in place, or
    append when absent); REMOVED deletes it. Upsert semantics make a re-fold idempotent:
    re-applying an already-folded block reproduces identical text. `edits` lists
    `(action, title)` for each block that actually changes the target.
    """
    target_preamble, target_blocks = _parse_requirement_blocks(target_text)
    result = list(target_blocks)
    edits: list[tuple[str, str]] = []
    for delta in delta_blocks:
        index = next(
            (i for i, block in enumerate(result) if block.title == delta.title), None
        )
        if delta.section == "REMOVED":
            if index is not None:
                result.pop(index)
                edits.append(("removed", delta.title))
            continue
        new_block = RequirementBlock("", delta.title, delta.text)
        if index is None:
            result.append(new_block)
            edits.append(("added", delta.title))
        elif result[index].text != delta.text:
            result[index] = new_block
            edits.append(("modified", delta.title))
    preamble = target_preamble if target_text.strip() else f"# Capability: {capability}"
    body = "\n\n".join(block.text for block in result)
    new_text = (preamble + "\n\n" + body).strip() + "\n"
    return new_text, edits


@dataclass(frozen=True)
class FoldEdit:
    """One planned fold edit: which capability, action, and requirement title."""

    capability: str
    action: str
    requirement: str


@dataclass(frozen=True)
class FoldResult:
    """Outcome of a fold: whether it held, the planned edits, and what it did."""

    ok: bool
    reason: str
    edits: tuple[FoldEdit, ...]
    changed: bool
    moved: bool


def _resolve_delta_specs(repo: Path, change_id: str) -> Path:
    """Return the change's delta specs dir — active, or archived if already folded."""
    active = repo / "openspec" / "changes" / change_id / "specs"
    if active.exists():
        return active
    archived = repo / "openspec" / "changes" / "archive" / change_id / "specs"
    if archived.exists():
        return archived
    raise FileNotFoundError(
        f"no specs delta for change '{change_id}' under {repo / 'openspec' / 'changes'}"
    )


def _archive_change(repo: Path, change_id: str) -> bool:
    """Move openspec/changes/<id>/ to its archive/ subdir; return whether it moved."""
    source = repo / "openspec" / "changes" / change_id
    if not source.exists():
        return False
    destination = repo / "openspec" / "changes" / "archive" / change_id
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.rename(destination)
    return True


def _specs_valid(repo: Path) -> bool:
    """Whether the top-level specs bind cleanly (the verify-after-fold check)."""
    return _specs_check(repo).ok


def fold_change(
    repo: Path,
    change_id: str,
    dry_run: bool = False,
    validator: Callable[[Path], bool] = _specs_valid,
) -> FoldResult:
    """Fold a change's spec delta into the living `openspec/specs/`.

    ADDED adds, MODIFIED overwrites the whole requirement, REMOVED deletes. `dry_run`
    reports the planned edits and writes nothing. Otherwise it writes the folds, runs
    the validator (verify-after-fold) and HALTs without moving the change if the specs
    are invalid, and on success moves the change to `openspec/changes/archive/<id>/`.
    Idempotent:
    re-folding an already-folded change writes nothing and moves nothing.
    """
    delta_specs = _resolve_delta_specs(repo, change_id)
    edits: list[FoldEdit] = []
    writes: list[tuple[Path, str]] = []
    for spec_file in sorted(delta_specs.rglob("spec.md")):
        relative = spec_file.relative_to(delta_specs)
        capability = relative.parts[0]
        target_path = repo / "openspec" / "specs" / relative
        _, delta_blocks = _parse_requirement_blocks(spec_file.read_text())
        target_text = target_path.read_text() if target_path.exists() else ""
        new_text, block_edits = _apply_fold(target_text, delta_blocks, capability)
        edits.extend(
            FoldEdit(capability, action, title) for action, title in block_edits
        )
        if new_text != target_text:
            writes.append((target_path, new_text))

    changed = bool(writes)
    if dry_run:
        return FoldResult(True, "", tuple(edits), changed, moved=False)

    for path, new_text in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text)

    if not validator(repo):
        return FoldResult(
            False, "specs invalid after fold", tuple(edits), changed, moved=False
        )

    moved = _archive_change(repo, change_id)
    return FoldResult(True, "", tuple(edits), changed, moved)
