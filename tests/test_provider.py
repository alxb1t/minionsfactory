import subprocess
from pathlib import Path

import pytest

from orchestrator.provider import (
    ClaudeCodeProvider,
    FakeProvider,
    Profile,
    ProviderError,
    RoleResult,
    build_command,
    parse_result,
    read_only_profile,
)


@pytest.mark.spec("provider:result:nonzero-exit-raises-provider-error")
def test_claude_provider_raises_provider_error_on_a_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ["claude"], stderr="usage limit reached")

    monkeypatch.setattr(subprocess, "run", boom)

    with pytest.raises(ProviderError, match="usage limit reached"):
        ClaudeCodeProvider().run_role("build", Path("/repo"), Profile())


@pytest.mark.spec("provider:result:parses-headless-json")
def test_parse_result_reads_the_headless_json_fields() -> None:
    stdout = (
        '{"type": "result", "subtype": "success", "is_error": false, '
        '"result": "PONG", "session_id": "abc-123", "total_cost_usd": 0.012}'
    )
    result = parse_result(stdout)

    assert result.is_error is False
    assert result.result == "PONG"
    assert result.session_id == "abc-123"
    assert result.total_cost_usd == 0.012


@pytest.mark.spec_exempt("test double — FakeProvider scripted-result smoke")
def test_fake_providers_returns_the_scripted_results() -> None:
    scripted = RoleResult(
        subtype="success",
        is_error=False,
        result="done",
        session_id="s-1",
        total_cost_usd=0.0,
    )
    provider = FakeProvider(scripted)

    result = provider.run_role("build phase 1", Path("/tmp/repo"), Profile())

    assert result is scripted


@pytest.mark.spec("provider:build-command:headless-json")
def test_build_command_requests_headless_json() -> None:
    profile = Profile(permission_mode="default", allowed_tools=("Edit", "Bash"))

    command = build_command("build phase 1", profile)

    assert command[:3] == ["claude", "-p", "build phase 1"]
    assert "--output-format" in command and "json" in command
    assert command[command.index("--permission-mode") + 1] == "default"
    assert command[command.index("--allowedTools") + 1 :] == ["Edit", "Bash"]


@pytest.mark.spec("provider:build-command:pins-model")
def test_build_command_pins_the_model_when_given() -> None:
    command = build_command("build phase 1", Profile(), model="claude-opus-4-8")

    assert command[command.index("--model") + 1] == "claude-opus-4-8"


@pytest.mark.spec("provider:build-command:omits-model-by-default")
def test_build_command_omits_the_model_flag_by_default() -> None:
    assert "--model" not in build_command("build phase 1", Profile())


@pytest.mark.spec("provider:build-command:sets-effort")
def test_build_command_sets_the_reasoning_effort_when_given() -> None:
    command = build_command("build phase 1", Profile(), effort="xhigh")

    assert command[command.index("--effort") + 1] == "xhigh"


@pytest.mark.spec("provider:build-command:omits-effort-by-default")
def test_build_command_omits_the_effort_flag_by_default() -> None:
    assert "--effort" not in build_command("build phase 1", Profile())


@pytest.mark.spec("provider:read-only-profile:denies-and-scopes-write")
def test_read_only_profile_emits_deny_perms_and_a_scoped_findings_write() -> None:
    findings = Path("/vault/v0.2_review.md")
    command = build_command("review the diff", read_only_profile(findings))

    assert "--disallowedTools" in command
    assert "Bash" in command
    assert "Edit" in command
    assert f"Write({findings})" in command
