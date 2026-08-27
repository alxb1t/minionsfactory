"""Entry-point tests: the preflight reads nothing outside the repo, and the wiring."""

import os
import subprocess
from pathlib import Path

import pytest

from orchestrator.__main__ import _fanout_roles, _make_release, main
from orchestrator.gate import FakeGate, GateResult
from orchestrator.provider import Profile, RoleResult
from orchestrator.release import FakeReleaseGit, ReleaseStatus

_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)
_RED = GateResult(passed=False, steps=())
_GREEN = GateResult(passed=True, steps=())


class _RecordingProvider:
    """Records each spawn; returns a scripted result and starts no process."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Path, Profile]] = []

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        """Record the spawn and return the scripted result."""
        self.calls.append((role_prompt, repo, profile))
        return _ROLE


# The one test in the suite that shells out to real `git`. Isolated from the operator's
# own configuration — a global `commit.gpgsign`, hooks path or commit template would
# otherwise decide whether it passes.
_ISOLATED_GIT = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _git(repo: Path, *args: str) -> None:
    """Run a git command in `repo`, failing the test on a non-zero exit."""
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env={**os.environ, **_ISOLATED_GIT},
    )


def _target_repo(root: Path) -> Path:
    """A git repo carrying one well-formed change — and no `.env`, no settings."""
    repo = root / "target"
    change_dir = repo / "openspec" / "changes" / "0001-a-change"
    (change_dir / "specs").mkdir(parents=True)
    (change_dir / "proposal.md").write_text("---\nversion: v0.1\n---\n\n# proposal\n")
    (change_dir / "design.md").write_text("# design\n")
    (change_dir / "tasks.md").write_text("## Progress\n\n- [ ] 1 — First phase\n")
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "the change")
    return repo


@pytest.mark.spec("cli:preflight:no-env-no-grant-runs")
def test_run_spawns_against_a_repo_with_no_env_and_no_settings_grant(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The preflight resolves nothing outside the repository, so a target that declares
    # no vault and grants no directory is not misconfigured — it is ordinary. The
    # provider and gate seams are faked: nothing is spawned and no gate is run.
    repo = _target_repo(tmp_path)
    provider = _RecordingProvider()
    monkeypatch.setattr(
        "orchestrator.__main__.ClaudeCodeProvider",
        lambda model, effort: provider,
    )
    monkeypatch.setattr("orchestrator.__main__.SubprocessGate", lambda: FakeGate(_RED))

    assert not (repo / ".env").exists()
    assert not (repo / ".claude").exists()

    exit_code = main(["run", "--repo", str(repo)])

    # The red gate halts the run after the first phase; what this asserts is that the
    # coder was reached at all — the preflight passed to the change-state read.
    assert "preflight failed" not in capsys.readouterr().out
    assert exit_code == 1
    assert len(provider.calls) == 1
    assert "0001-a-change" in provider.calls[0][0]


_CHANGELOG_READY = """\
# Changelog

## [Unreleased]

- something worth releasing
"""


def _release_ready(repo: Path) -> None:
    """Bring `repo` to a state the release gate passes: changelog, pyproject, findings.

    Everything the gate reads that `_target_repo` does not already provide. No
    deferred-work file (absent reads as nothing deferred) and no tags.
    """
    (repo / "CHANGELOG.md").write_text(_CHANGELOG_READY)
    (repo / "pyproject.toml").write_text('[project]\nversion = "0.0.0"\n')
    findings = repo / ".minions" / "findings"
    findings.mkdir(parents=True)
    for role in ("review", "security", "simplify"):
        (findings / f"0001-a-change_{role}.md").write_text(
            "---\nverdict: clean\nopen_blocking: 0\nround: 2\nhead: abc123\n---\n"
        )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "release-ready")


@pytest.mark.spec_exempt("wiring — composition root hands the change id to the release")
def test_release_closure_stamps_the_change_trailer_on_the_release_commit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `prepare_release` stamps the trailer only when given a `change_id`, and its own
    # tests pass one in. What is untested — and is where the trailer went missing — is
    # the seam: whether the composition root, which already holds the change directory,
    # actually passes it. So this drives `_make_release` end to end against a real repo
    # with only the git-writing seam faked, and reads the message git would have got.
    repo = _target_repo(tmp_path)
    _release_ready(repo)
    git = FakeReleaseGit()
    monkeypatch.setattr("orchestrator.__main__.SubprocessReleaseGit", lambda: git)

    release = _make_release(
        gate=FakeGate(_GREEN),
        repo=repo,
        version="v0.1",
        branch="main",
        today="2026-08-27",
        roles=_fanout_roles(),
    )
    result = release()
    capsys.readouterr()  # the handoff block; not what this test is about

    assert result.status is ReleaseStatus.PREPARED, result.reason
    assert git.commits[0].endswith("\n\nChange: 0001-a-change")
