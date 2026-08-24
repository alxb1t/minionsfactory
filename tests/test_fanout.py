from pathlib import Path

import pytest

from orchestrator.fanout import (
    RoleSpec,
    assemble_prompt,
    build_inputs_block,
    run_fanout,
)
from orchestrator.findings import FindingsState, findings_path
from orchestrator.provider import Profile, RoleResult
from orchestrator.status import Event

_ROLE = RoleResult(
    subtype="success", is_error=False, result="ok", session_id="s", total_cost_usd=0.0
)
_ROLES = [RoleSpec("review", "R"), RoleSpec("security", "S"), RoleSpec("simplify", "P")]
_CHANGE_ID = "0005-change-cutover"
_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


class _RecordingProvider:
    """Records each run_role call's (prompt, profile); returns a scripted result."""

    def __init__(self, result: RoleResult) -> None:
        self.calls: list[tuple[str, Profile]] = []
        self._result = result

    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult:
        self.calls.append((role_prompt, profile))
        return self._result


@pytest.mark.spec("fanout:read-only-roles:runs-each-over-frozen-diff")
def test_run_fanout_runs_three_read_only_roles_over_the_frozen_diff(
    tmp_path: Path,
) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    findings = vault / "findings"
    findings.mkdir(parents=True)
    for name in ("review", "security", "simplify"):
        (findings / f"{_CHANGE_ID}_{name}.md").write_text(
            "---\nhead: h\nround: 1\nopen_blocking: 0\nverdict: clean\n---\n"
        )
    fake = _RecordingProvider(_ROLE)

    states = run_fanout(
        fake,
        repo,
        vault,
        _CHANGE_ID,
        "v0.5",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        "abc123",
        repo / "openspec" / "changes" / _CHANGE_ID,
        _ROLES,
    )

    assert len(fake.calls) == 3
    assert all("Bash" in p.disallowed_tools for _, p in fake.calls)
    assert (repo / ".minions" / "diff.patch").read_text() == "THE DIFF"
    expected = FindingsState(verdict="clean", open_blocking=0, round=1, head="h")
    assert states == [expected, expected, expected]


@pytest.mark.spec("fanout:findings-path:change-id-keyed-path")
def test_findings_path_is_keyed_to_the_change_id(tmp_path: Path) -> None:
    assert findings_path(tmp_path, _CHANGE_ID, "review") == (
        tmp_path / "findings" / f"{_CHANGE_ID}_review.md"
    )


@pytest.mark.spec("fanout:findings-path:fanout-writes-through-helper")
def test_run_fanout_scopes_each_write_to_the_resolved_findings_path(
    tmp_path: Path,
) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    fake = _RecordingProvider(_ROLE)

    run_fanout(
        fake,
        repo,
        vault,
        _CHANGE_ID,
        "v0.5",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        "abc123",
        repo / "openspec" / "changes" / _CHANGE_ID,
        _ROLES,
    )

    for role, (prompt, profile) in zip(_ROLES, fake.calls, strict=True):
        expected = findings_path(vault, _CHANGE_ID, role.name)
        # the role is granted write access to exactly that file, and told to write it
        assert f"Write({expected})" in profile.allowed_tools
        assert str(expected) in prompt


@pytest.mark.spec("fanout:findings-path:creates-findings-dir")
def test_run_fanout_creates_the_findings_dir_before_the_first_spawn(
    tmp_path: Path,
) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    vault.mkdir()
    existed_at_spawn: list[bool] = []

    class _DirWatchingProvider(_RecordingProvider):
        def run_role(
            self, role_prompt: str, repo: Path, profile: Profile
        ) -> RoleResult:
            existed_at_spawn.append((vault / "findings").is_dir())
            return super().run_role(role_prompt, repo, profile)

    assert not (vault / "findings").exists()

    run_fanout(
        _DirWatchingProvider(_ROLE),
        repo,
        vault,
        _CHANGE_ID,
        "v0.5",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        "abc123",
        repo / "openspec" / "changes" / _CHANGE_ID,
        _ROLES,
    )

    # the read-only role has no Bash to mkdir for itself: the dir is there on spawn 1
    assert existed_at_spawn == [True, True, True]


@pytest.mark.spec("fanout:read-only-roles:prepends-inputs-block")
def test_run_fanout_prepends_the_orchestrator_inputs_block(tmp_path: Path) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    change_dir = repo / "openspec" / "changes" / _CHANGE_ID
    fake = _RecordingProvider(_ROLE)

    run_fanout(
        fake,
        repo,
        vault,
        _CHANGE_ID,
        "v0.5",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        "abc123",
        change_dir,
        [RoleSpec("review", "REVIEW-BODY")],
        mode="review",
    )

    prompt, _ = fake.calls[0]
    inputs_block = prompt.split("REVIEW-BODY")[0]
    assert "## Inputs" in prompt
    assert "Mode: review" in prompt
    assert "abc123" in prompt  # the head SHA the orchestrator supplied
    findings = findings_path(vault, _CHANGE_ID, "review")
    assert str(findings) in prompt  # the findings path to write
    assert str(change_dir) in prompt  # the change dir, not a plan file
    assert "REVIEW-BODY" in prompt  # the role prompt follows the Inputs block
    assert "Plan" not in inputs_block  # no line of the block names a plan file


@pytest.mark.spec("fanout:role-inputs:block-carries-change-and-findings")
def test_inputs_block_carries_the_change_findings_head_and_version(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    change_dir = tmp_path / "repo" / "openspec" / "changes" / _CHANGE_ID
    findings: dict[str, Path] = {
        str(r.name): findings_path(vault, _CHANGE_ID, r.name) for r in _ROLES
    }

    block = build_inputs_block(change_dir, findings, "abc123", "v0.5", vault)

    assert str(change_dir) in block
    for path in findings.values():
        assert str(path) in block
    assert "abc123" in block
    assert "v0.5" in block


@pytest.mark.parametrize("role", ["coder", "fixer", "release"])
@pytest.mark.spec("fanout:role-inputs:prompt-leads-with-inputs")
def test_an_assembled_role_prompt_leads_with_the_inputs_block(
    tmp_path: Path, role: str
) -> None:
    vault = tmp_path / "vault"
    change_dir = tmp_path / "repo" / "openspec" / "changes" / _CHANGE_ID
    body = f"# {role.upper()}-BODY\n\nthe role's own mandate.\n"

    findings: dict[str, Path] = {
        str(r.name): findings_path(vault, _CHANGE_ID, r.name) for r in _ROLES
    }

    block = build_inputs_block(change_dir, findings, "abc123", "v0.5", vault)
    prompt = assemble_prompt(block, body)

    assert prompt.startswith("## Inputs")
    assert prompt.endswith(body)  # the Inputs block first, then the role body
    assert prompt == block + body


@pytest.mark.parametrize("prompt_file", ["coder.md", "fixer.md", "release.md"])
@pytest.mark.spec("fanout:role-inputs:prompt-leads-with-inputs")
def test_a_role_prompt_body_derives_no_path_by_shell(prompt_file: str) -> None:
    # The orchestrator resolves paths in code and supplies them in the Inputs block;
    # a prompt that shells for its own paths is the thing this replaces.
    body = (_PROMPTS / prompt_file).read_text()

    assert "PLAN_FILE" not in body
    assert "implementation_plans" not in body


@pytest.mark.spec("fanout:read-only-roles:emits-spawn-and-returned")
def test_run_fanout_emits_spawn_and_returned_per_role(tmp_path: Path) -> None:
    vault, repo = tmp_path / "vault", tmp_path / "repo"
    fake = _RecordingProvider(_ROLE)
    events: list[Event] = []

    run_fanout(
        fake,
        repo,
        vault,
        _CHANGE_ID,
        "v0.5",
        "THE DIFF",
        repo / ".minions" / "diff.patch",
        "abc123",
        repo / "openspec" / "changes" / _CHANGE_ID,
        _ROLES,
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
