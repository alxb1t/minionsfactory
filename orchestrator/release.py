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

# An ordinary markdown list line: a `-`/`*`/`+` bullet or an ordered `N.`/`N)` marker,
# followed by whitespace. The trailing `\s` is what keeps prose out — `-- note`,
# `*emphasis*` and `1.5x` all carry a marker character but no separator after it.
_LIST_LINE_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s")

# What `deferred_work_text` returns when it cannot read the file: itself a list line, so
# the guard blocks on it, and one that names the problem instead of inventing an item.
_UNREADABLE_BACKLOG = "- the deferred-work file could not be read ({reason})\n"


@dataclass(frozen=True)
class Commit:
    """A base..HEAD commit and its `Change:` trailer value (None when absent).

    Gathered by the effectful caller so the trailer predicate stays pure.
    """

    sha: str
    change: str | None


def deferred_work_text(repo: Path, version: str) -> str:
    """Read `<repo>/.minions/<version>_backlog.md` as text the guard can judge.

    The asymmetry is deliberate. An **absent** file passes: the deferred-work file is
    per-version and lives in ephemeral run-artifact space, so its absence means nothing
    was deferred (`design.md` §3) — it reads as `""`, which holds no list line. An
    **unreadable** one blocks: a directory at that path, a broken symlink or any other
    `OSError` — or a file that is not valid UTF-8 — means we cannot tell whether work
    was deferred, so rather than raising a
    traceback out of the release gate — or, for a broken symlink, silently reading as
    absent — it returns a single list line naming the problem, which `_backlog_blocker`
    turns into a named blocking reason. The read is the effectful half; the predicate
    judges the text it returns.
    """
    path = repo / ".minions" / f"{version}_backlog.md"
    try:
        return path.read_text()
    except FileNotFoundError:
        if path.is_symlink():  # a dirent that exists but resolves to nothing
            return _UNREADABLE_BACKLOG.format(reason="broken symlink")
        return ""
    except OSError as error:
        return _UNREADABLE_BACKLOG.format(reason=error.strerror or type(error).__name__)
    except UnicodeDecodeError:  # a ValueError, so it escapes the OSError arm above
        return _UNREADABLE_BACKLOG.format(reason="not valid UTF-8")


def _backlog_blocker(backlog_text: str, version: str) -> str | None:
    """Why the deferred-work file blocks release, or None when it holds no item.

    **Any** markdown list line blocks — `-`, `*` or `+` bullets and ordered items
    (`1.` / `1)`) alike — whatever its checkbox state: an item leaves the file by being
    fixed and removed, or exported by the human, never by being ticked. The marker must
    be followed by whitespace, so prose such as `-- note`, `*emphasis*` or `1.5x` is not
    an item. Empty text — including the empty string a missing file reads as — does not
    block. The first offending line is quoted in the reason, so a file the reader could
    not read names *that* as the problem rather than claiming an item was found.
    """
    for line in backlog_text.splitlines():
        item = line.lstrip()
        if _LIST_LINE_RE.match(item):
            return (
                f"backlog: deferred work remains in "
                f".minions/{version}_backlog.md: {item}"
            )
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


def _release_message(tag: str, change_id: str | None) -> str:
    """Build the release commit message, appending a `Change:` trailer when known."""
    message = f"chore(release): {tag}"
    if change_id:
        message += f"\n\nChange: {change_id}"
    return message


def prepare_release(
    verdict: ReleaseVerdict,
    repo: Path,
    version: str,
    today: str,
    branch: str,
    git: ReleaseGit,
    change_id: str | None = None,
) -> ReleaseResult:
    """Prepare the release on a green verdict, then hand off to the human; else refuse.

    On a red verdict: do nothing, return REFUSED with the reason. On green: cut the
    CHANGELOG, bump pyproject, commit (with a `Change: <id>` trailer when the change is
    known) + annotated-tag locally, and return PREPARED with the merge+push handoff.
    Never pushes or merges — the git seam has no such operation — and writes nothing
    outside `repo`: the durable release record is `git log`, `CHANGELOG.md` and the tag.
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
