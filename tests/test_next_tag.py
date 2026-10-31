"""The next release's tag, computed from the repository's tags and a bump.

Why: 0047-version-at-merge design D2.
"""

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-release" / "scripts" / "next_tag.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _next(root: Path, bump: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), bump],
        cwd=root,
        capture_output=True,
        text=True,
    )


def _assert_next(root: Path, minor: str, patch: str) -> None:
    assert _next(root, "minor").stdout == f"{minor}\n"
    assert _next(root, "patch").stdout == f"{patch}\n"


def test_next_tag_follows_the_bump(tmp_path: Path) -> None:
    assert _next(tmp_path, "minor").returncode == 2

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    _assert_next(tmp_path, "v0.1.0", "v0.1.0")

    _git(tmp_path, "tag", "v1")
    _git(tmp_path, "tag", "nightly")
    _assert_next(tmp_path, "v0.1.0", "v0.1.0")

    _git(tmp_path, "tag", "v0.9.2")
    _git(tmp_path, "tag", "v0.10.0")
    _assert_next(tmp_path, "v0.11.0", "v0.10.1")

    _git(tmp_path, "tag", "v0.40.0")
    _assert_next(tmp_path, "v0.41.0", "v0.40.1")

    assert _next(tmp_path, "major").returncode == 2
