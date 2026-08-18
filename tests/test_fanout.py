from pathlib import Path

from orchestrator.fanout import RoleSpec, run_fanout
from orchestrator.findings import FindingsState
from orchestrator.provider import Profile, RoleResult
from orchestrator.status import Event

_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)


class _RecordingProvider:
    """Records each run_role call's (prompt, profile); returns a scripted result."""

    def __init__(self, result: RoleResult) -> None:
        self.calls: list[tuple[str, Profile]] = []
        self._result = result

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        self.calls.append((role_prompt, profile))
        return self._result


def test_run_fanout_runs_three_read_only_roles_over_the_frozen_diff(
    tmp_path: Path,
) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    vault.mkdir()
    for name in ("review", "security", "simplify"):
        (vault / f"v0.2_{name}.md").write_text(
            "---\nhead: h\nround: 1\nopen_blocking: 0\nverdict: clean\n---\n"
        )
    fake = _RecordingProvider(_ROLE)
    roles = [
        RoleSpec("review", "R"),
        RoleSpec("security", "S"),
        RoleSpec("simplify", "P"),
    ]

    states = run_fanout(
        fake, repo, vault, "v0.2", "THE DIFF", repo / ".minions" / "diff.patch", roles
    )

    assert len(fake.calls) == 3
    assert all("Bash" in p.disallowed_tools for _, p in fake.calls)
    assert (repo / ".minions" / "diff.patch").read_text() == "THE DIFF"
    expected = FindingsState(verdict="clean", open_blocking=0, round=1, head="h")
    assert states == [expected, expected, expected]


def test_run_fanout_emits_spawn_and_returned_per_role(tmp_path: Path) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    fake = _RecordingProvider(_ROLE)
    events: list[Event] = []
    roles = [
        RoleSpec("review", "R"),
        RoleSpec("security", "S"),
        RoleSpec("simplify", "P"),
    ]
    run_fanout(
        fake,
        repo,
        vault,
        "v0.2",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        roles,
        emit_event=events.append,
    )
    assert [e.kind for e in events] == [
        "role-spawn",
        "role-returned",
        "role-spawn",
        "role-returned",
        "role-spawn",
        "role-returned",
    ]
