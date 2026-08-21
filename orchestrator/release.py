"""Release automation: verify the release gate, then prepare the release."""

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from orchestrator.findings import FindingsState, all_findings_clean
from orchestrator.gate import GateResult


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


def verify_release_gate(
    version: str,
    gate_result: GateResult,
    findings: Sequence[FindingsState | None],
    backlog_text: str,
    changelog_text: str,
    existing_tags: Sequence[str],
    tree_is_clean: bool,
) -> ReleaseVerdict:
    """Verify every release precondition; return ok, or the first blocking reason.

    Pure — the release-time analog of `driver.decide`: it judges over
    already-gathered facts. The effectful gathering (running the gate, reading
    the backlog/changelog, listing git tags, checking the tree) lives in the
    caller, so the whole gate is one first-non-None scan over the blockers.
    """
    for blocker in (
        _gate_blocker(gate_result),
        _findings_blocker(findings),
        _backlog_blocker(backlog_text, version),
        _tag_blocker(existing_tags, version),
        _changelog_blocker(changelog_text),
        _tree_blocker(tree_is_clean),
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


def prepare_release(
    verdict: ReleaseVerdict,
    repo: Path,
    vault_dir: Path,
    version: str,
    today: str,
    branch: str,
    git: ReleaseGit,
) -> ReleaseResult:
    """Prepare the release on a green verdict, then hand off to the human; else refuse.

    On a red verdict: do nothing, return REFUSED with the reason. On green: cut the
    CHANGELOG, bump pyproject, commit + annotated-tag locally, prepend the release
    log, return PREPARED with the merge+push handoff. Never pushes or merges — the
    git seam has no such operation.
    """
    if verdict.ok is False:
        return ReleaseResult(ReleaseStatus.REFUSED, verdict.reason, "")

    tag = f"{version}.0"

    changelog = repo / "CHANGELOG.md"
    changelog.write_text(_cut_changelog(changelog.read_text(), version, today))
    pyproject = repo / "pyproject.toml"
    pyproject.write_text(_bump_pyproject(pyproject.read_text(), version))

    git.commit_all(repo, f"chore(release): {tag}")
    git.tag(repo, tag, tag)

    _prepend_release_log(
        vault_dir / "release_log.md", _release_log_entry(tag, today, branch)
    )

    return ReleaseResult(ReleaseStatus.PREPARED, "", _handoff(tag, branch))
