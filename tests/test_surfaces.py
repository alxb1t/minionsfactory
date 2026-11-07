"""Converge's security head by rule: a fix that reaches no surface needs no verify.

Each repository built under `tmp_path`. Why: 0094-lighter-converge design D8.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "surfaces.py"
_IDENTITY = ["-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
_IDENTITY += ["-c", "commit.gpgsign=false"]


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("surfaces", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


surfaces = _load(_SCRIPT)

_THREATS = (
    "# threat model\n\n## Entry points\n\n- `not/a/surface` — prose\n\n"
    "## Surfaces\n\nThe globs `surfaces.py` reads.\n\n"
    "- `skills/*/scripts/*` — a script runs\n\n## Out of scope\n\n- none\n"
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *_IDENTITY, *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def _fix(root: Path, path: str) -> tuple[str, str]:
    """Return the heads before and after a fix that touches `path`."""
    _git(root, "init", "-q", "-b", "main")
    (root / "THREAT_MODEL.md").write_text(_THREATS)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    start = _git(root, "rev-parse", "HEAD")
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text("fixed\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "fix")
    return start, _git(root, "rev-parse", "HEAD")


def _security(root: Path, verdict: str = "clean", status: str = "verified") -> Path:
    path = root / "security.md"
    path.write_text(
        f"---\nverdict: {verdict}\nhead: x\nround: 2\n---\n\n"
        "- **S1 — a finding**\n  - **Priority:** low · security — why.\n"
        f"  - **Status:** {status} — a note\n\n## Resolution log\n\n- d · round 1\n"
    )
    return path


def _run(
    capsys: pytest.CaptureFixture[str], security: Path, start: str, end: str
) -> tuple[int, str]:
    code = surfaces.main([str(security), start, end])
    return code, capsys.readouterr().out


def test_a_fix_that_reaches_no_surface_is_by_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    start, end = _fix(tmp_path, "docs/a.md")
    security = _security(tmp_path)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(security), start, end],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "surfaces: no surface\n")

    # A security file with no card has none awaiting its checker.
    security.write_text("---\nverdict: clean\nhead: x\nround: 1\n---\n")
    assert surfaces.main([str(security), start, end]) == 0


def test_a_fix_that_reaches_security_is_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    start, end = _fix(tmp_path, "skills/x/scripts/y.py")
    security = _security(tmp_path)
    assert _run(capsys, security, start, end) == (
        1,
        "surfaces: verify — skills/x/scripts/y.py matches skills/*/scripts/*\n",
    )

    for status in ("fixed", "wontfix"):
        _security(tmp_path, status=status)
        assert _run(capsys, security, start, start) == (
            1,
            f"surfaces: verify — security card S1 is {status}\n",
        )
    _security(tmp_path, verdict="changes-requested")
    assert _run(capsys, security, start, start) == (
        1,
        "surfaces: verify — security.md is not clean\n",
    )

    _security(tmp_path)
    (tmp_path / "THREAT_MODEL.md").write_text("# threat model\n\n## Out of scope\n")
    assert _run(capsys, security, start, start) == (
        1,
        "surfaces: verify — THREAT_MODEL.md lists no surface\n",
    )

    (tmp_path / "THREAT_MODEL.md").write_text(_THREATS)
    code, said = _run(capsys, security, "nowhere", end)
    assert code == 2 and said.startswith("surfaces: cannot read — git diff failed: ")
    security.unlink()
    assert _run(capsys, security, start, end) == (
        2,
        f"surfaces: cannot read — {security}: No such file or directory\n",
    )
