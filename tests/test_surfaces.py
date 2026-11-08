"""Converge's adversarial head by rule: a fix that reaches no surface needs no verify.

Each repository built under `tmp_path`. Why: 0094-lighter-converge design D8;
0095-converge-roles design D3.
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


def _commit(root: Path, path: str, text: str = "fixed\n") -> str:
    """Commit `text` at `path` and return the new head."""
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text)
    _git(root, "add", path)
    _git(root, "commit", "-q", "-m", path)
    return _git(root, "rev-parse", "HEAD")


def _fix(root: Path, path: str) -> tuple[str, str]:
    """Return the heads before and after a fix that touches `path`."""
    _git(root, "init", "-q", "-b", "main")
    start = _commit(root, "THREAT_MODEL.md", _THREATS)
    return start, _commit(root, path)


def _adversarial(root: Path, verdict: str = "clean", status: str = "verified") -> Path:
    path = root / "adversarial.md"
    path.write_text(
        f"---\nverdict: {verdict}\nhead: x\nround: 2\n---\n\n"
        "- **S1 — a finding**\n  - **Priority:** low · adversarial · security — why.\n"
        f"  - **Status:** {status} — a note\n\n## Resolution log\n\n- d · round 1\n"
    )
    return path


def _run(
    capsys: pytest.CaptureFixture[str], adversarial: Path, start: str, end: str
) -> tuple[int, str]:
    code = surfaces.main([str(adversarial), start, end])
    return code, capsys.readouterr().out


def test_a_fix_that_reaches_no_surface_is_by_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    start, end = _fix(tmp_path, "docs/a.md")
    adversarial = _adversarial(tmp_path)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(adversarial), start, end],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "surfaces: no surface\n")

    # An adversarial file with no card has none awaiting its checker.
    adversarial.write_text("---\nverdict: clean\nhead: x\nround: 1\n---\n")
    assert surfaces.main([str(adversarial), start, end]) == 0


def test_a_fix_that_reaches_security_is_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    start, end = _fix(tmp_path, "skills/x/scripts/y.py")
    adversarial = _adversarial(tmp_path)
    assert _run(capsys, adversarial, start, end) == (
        1,
        "surfaces: verify — skills/x/scripts/y.py matches skills/*/scripts/*\n",
    )

    # A path git would quote is matched as it is named.
    quoted = _commit(tmp_path, "skills/x/scripts/helper_é.py")
    assert _run(capsys, adversarial, end, quoted) == (
        1,
        "surfaces: verify — skills/x/scripts/helper_é.py matches skills/*/scripts/*\n",
    )

    # The list is read at `<from>`, so a fix cannot drop the glob its own edit matches.
    _commit(tmp_path, "THREAT_MODEL.md", _THREATS.replace("skills/*/", "docs/"))
    edited = _commit(tmp_path, "skills/x/scripts/z.py")
    assert _run(capsys, adversarial, quoted, edited) == (
        1,
        "surfaces: verify — skills/x/scripts/z.py matches skills/*/scripts/*\n",
    )

    # A replace ref cannot swap the list read at `<from>`.
    listed = _git(tmp_path, "rev-parse", f"{quoted}:THREAT_MODEL.md")
    narrowed = _git(tmp_path, "rev-parse", f"{edited}:THREAT_MODEL.md")
    _git(tmp_path, "replace", listed, narrowed)
    assert _run(capsys, adversarial, quoted, edited) == (
        1,
        "surfaces: verify — skills/x/scripts/z.py matches skills/*/scripts/*\n",
    )
    _git(tmp_path, "replace", "-d", listed)

    # A Status off the card's exact form is not settled: only `verified` and
    # `accepted` are.
    for status, said in (
        ("fixed", "fixed"),
        ("wontfix", "wontfix"),
        ("**fixed**", "fixed"),
        ("*open*", "open"),
        ("Fixed", "Fixed"),
    ):
        _adversarial(tmp_path, status=status)
        assert _run(capsys, adversarial, start, start) == (
            1,
            f"surfaces: verify — adversarial card S1 is {said}\n",
        )
    # A Status under a title off the card's form is settled by the same allowlist.
    adversarial.write_text(
        "---\nverdict: clean\n---\n\n- **S1 – a finding**\n"
        "  - **Status:** fixed — a note\n"
    )
    assert _run(capsys, adversarial, start, start) == (
        1,
        "surfaces: verify — adversarial card S1 is fixed\n",
    )
    adversarial.write_text("---\nverdict: clean\n---\n\n- **S1 — a finding**\n")
    assert _run(capsys, adversarial, start, start) == (
        1,
        "surfaces: verify — adversarial card S1 is unsettled\n",
    )
    _adversarial(tmp_path, verdict="changes-requested")
    assert _run(capsys, adversarial, start, start) == (
        1,
        "surfaces: verify — adversarial.md is not clean\n",
    )

    # A threat model that lists no glob at `<from>`, or holds no file there.
    _adversarial(tmp_path)
    bare = _commit(tmp_path, "THREAT_MODEL.md", "# threat model\n\n## Out of scope\n")
    _git(tmp_path, "rm", "-q", "THREAT_MODEL.md")
    _git(tmp_path, "commit", "-q", "-m", "gone")
    for head in (bare, _git(tmp_path, "rev-parse", "HEAD")):
        assert _run(capsys, adversarial, head, head) == (
            1,
            "surfaces: verify — THREAT_MODEL.md lists no surface\n",
        )

    code, said = _run(capsys, adversarial, "nowhere", end)
    assert code == 2 and said.startswith("surfaces: cannot read — git diff failed: ")
    adversarial.unlink()
    assert _run(capsys, adversarial, start, end) == (
        2,
        f"surfaces: cannot read — {adversarial}: No such file or directory\n",
    )
