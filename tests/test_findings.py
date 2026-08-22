from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.findings import FindingsState, read_findings_state


@pytest.mark.spec("fanout:findings:parses-frontmatter-verdict")
def test_read_findings_state_parses_the_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "v0.2_review.md"
    f.write_text(
        "---\ntype: review\nplan: v0.2\nhead: abc1234\n"
        "round: 2\nopen_blocking: 3\nverdict: changes-requested\n---\n\n# Review\n"
    )
    assert read_findings_state(f) == FindingsState(
        verdict="changes-requested", open_blocking=3, round=2, head="abc1234"
    )


@pytest.mark.spec("fanout:findings:missing-file-is-none")
def test_read_findings_state_returns_none_for_a_missing_file(tmp_path: Path) -> None:
    assert read_findings_state(tmp_path / "nope.md") is None


@pytest.mark.spec("fanout:findings:rejects-unknown-verdict")
def test_read_findings_state_rejects_an_unknown_verdict(tmp_path: Path) -> None:
    f = tmp_path / "bad.md"
    f.write_text("---\nhead: a\nround: 1\nopen_blocking: 0\nverdict: cleen\n---\n")
    with pytest.raises(ValidationError):
        read_findings_state(f)
