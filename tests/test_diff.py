"""compute_diff builds the git argv (no shell) and returns the diff text."""

from pathlib import Path

from orchestrator.diff import compute_diff, run_role_with_diff
from orchestrator.provider import FakeProvider, RoleResult, read_only_profile

_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)


def test_compute_diff_builds_the_range_argv_and_returns_output() -> None:
    caputed: dict[str, object] = {}

    def fake_runner(argv: list[str], repo: Path) -> str:
        caputed["argv"] = argv
        caputed["repo"] = repo
        return "diff --git a/f /b/f\n+new line\n"

    diff = compute_diff(Path("/repo"), "base123", "head456", runner=fake_runner)

    assert diff == "diff --git a/f /b/f\n+new line\n"
    assert caputed["argv"] == ["git", "diff", "base123..head456"]
    assert caputed["repo"] == Path("/repo")


def test_run_role_with_diff_writes_the_diff_file_then_runs_the_role(
    tmp_path: Path,
) -> None:
    diff_path = tmp_path / ".minions" / "diff.patch"
    result = run_role_with_diff(
        FakeProvider(_ROLE),
        "review the diff at .minions/diff.patch",
        tmp_path,
        read_only_profile(tmp_path / "findings.md"),
        diff="diff --git a/f b/f\n+x\n",
        diff_path=diff_path,
    )
    assert diff_path.read_text() == "diff --git a/f b/f\n+x\n"
    assert result is _ROLE
