"""Converge's bundle: the decisions and living requirements a change cites.

Each tree built under `tmp_path`. Why: 0094-lighter-converge design D5.
"""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "bundle.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("bundle", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load(_SCRIPT)

_DECISIONS = (
    "# Decisions\n\n## The shape\n\n"
    "### D1 · One feature is one change\n\nD1's body.\n\n"
    "### D2 · Two rules hold\n\nD2's body.\n\n"
    "## The check loop\n\n"
    "### D48 · A known home\n\nD48's body.\n"
)
_LIVING = (
    "# sdd\n\n## Requirements\n\n"
    "### Requirement: A\n\nA's text.\n\n#### Scenario: a\n- a\n\n"
    "### Requirement: B\n\nB's text.\n\n"
    "### Requirement: C\n\nC's text.\n"
)


def _change(root: Path, design: str, delta: str | None = None) -> None:
    folder = root / "openspec" / "changes" / "0001-a"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "proposal.md").write_text("---\nbump: minor\n---\n")
    (folder / "design.md").write_text(design)
    (folder / "tasks.md").write_text("## Progress\n\n- [ ] 1 — One\n")
    if delta is not None:
        (folder / "specs" / "sdd").mkdir(parents=True, exist_ok=True)
        (folder / "specs" / "sdd" / "spec.md").write_text(delta)


def _run(capsys: pytest.CaptureFixture[str], out: Path) -> tuple[int, str]:
    code = bundle.main(["0001-a", str(out)])
    return code, capsys.readouterr().out


def test_a_bundle_holds_what_the_change_cites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    decisions = tmp_path / "docs" / "decisions.md"
    decisions.write_text(_DECISIONS)
    (tmp_path / "openspec" / "specs" / "sdd").mkdir(parents=True)
    (tmp_path / "openspec" / "specs" / "sdd" / "spec.md").write_text(_LIVING)
    design = (
        "Per [D48](../../../docs/decisions.md#d48--x), and D2 · Two rules.\n"
        "### D1\n\nOur own D1, [D1](#d1).\n"
    )
    delta = (
        "## MODIFIED Requirements\n\n### Requirement: A\n\nNew A.\n\n"
        "## REMOVED Requirements\n\n### Requirement: B\n\n**Reason**: gone.\n"
    )
    _change(tmp_path, design, delta)
    out = tmp_path / "bundle.md"

    assert _run(capsys, out) == (0, "bundle: 2 decisions cited · 2 requirements\n")
    text = out.read_text()
    cites, index, required = text.split("\n## ")[1:]
    assert cites.startswith("Decisions the change cites\n")
    assert "D2's body." in cites and "D48's body." in cites
    assert "D1's body." not in text
    assert "## The check loop" not in cites
    assert index == (
        "Every decision\n\n- D1 · One feature is one change\n- D2 · Two rules hold\n"
        "- D48 · A known home\n"
    )
    assert required.startswith("Requirements the delta modifies or removes, as diffs\n")
    assert "```diff\n--- living\n+++ delta\n" in required
    assert "-A's text.\n" in required and "+New A.\n" in required
    assert "-### Requirement: B\n-\n-B's text.\n" in required
    assert "C's text." not in required

    # A decisions file with no heading goes in whole.
    decisions.write_text("# Decisions\n\nNone yet.\n")
    assert _run(capsys, out)[0] == 0
    assert "## Every decision\n\n# Decisions\n\nNone yet.\n" in out.read_text()

    decisions.unlink()
    assert _run(capsys, out)[0] == 0
    assert "## Every decision\n\nNo docs/decisions.md.\n" in out.read_text()

    # A title the living spec lacks is named.
    _change(tmp_path, design, "## MODIFIED Requirements\n\n### Requirement: Z\n")
    assert _run(capsys, out)[0] == 0
    assert "- `Z` — not in the living spec" in out.read_text()

    # A change citing nothing, with no delta, writes `None.` under each empty section.
    shutil.rmtree(tmp_path / "openspec" / "changes" / "0001-a" / "specs")
    decisions.write_text("")
    _change(tmp_path, "No citation.\n")
    assert _run(capsys, out) == (0, "bundle: 0 decisions cited · 0 requirements\n")
    assert out.read_text().count("\n\nNone.\n") == 3


def test_decisions_print_what_the_files_cite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    monkeypatch.chdir(repo)
    (repo / "docs" / "decisions.md").write_text(_DECISIONS)
    brief = repo / "brief.md"
    brief.write_text("Per D2 · Two rules.\n")
    tasks = repo / "tasks.md"
    tasks.write_text("Per [D48](docs/decisions.md#d48--x).\n")

    assert bundle.main(["--decisions", str(brief), str(tasks)]) == 0

    assert capsys.readouterr().out == (
        "## Decisions the change cites\n\n"
        "### D2 · Two rules hold\n\nD2's body.\n\n"
        "### D48 · A known home\n\nD48's body.\n\n"
        "## Every decision\n\n- D1 · One feature is one change\n"
        "- D2 · Two rules hold\n- D48 · A known home\n"
    )
    assert sorted(path.name for path in repo.iterdir()) == [
        "brief.md",
        "docs",
        "tasks.md",
    ]

    gone = repo / "gone.md"
    assert bundle.main(["--decisions", str(gone)]) == 2
    said = f"bundle: cannot bundle — {gone}: No such file or directory\n"
    assert capsys.readouterr().out == said

    # The positional form takes both or neither, and neither beside `--decisions`.
    for args in (["0001-a"], ["0001-a", "b.md", "--decisions", str(brief)], []):
        with pytest.raises(SystemExit) as raised:
            bundle.main(args)
        assert raised.value.code == 2


def test_a_bundle_that_cannot_be_written_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "bundle.md"
    missing = "openspec/changes/0001-a/proposal.md: No such file or directory"
    assert _run(capsys, out) == (2, f"bundle: cannot bundle — {missing}\n")
    assert not out.exists()

    # A plan file that is not UTF-8 is a file it cannot read.
    _change(tmp_path, "Design.\n")
    design = tmp_path / "openspec" / "changes" / "0001-a" / "design.md"
    design.write_bytes(b"caf\xe9\n")
    reason = "openspec/changes/0001-a/design.md: invalid continuation byte"
    assert _run(capsys, out) == (2, f"bundle: cannot bundle — {reason}\n")
    assert not out.exists()

    _change(tmp_path, "Design.\n")
    target = tmp_path / "operator.rc"
    target.write_text("kept\n")
    out.symlink_to(target)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "0001-a", str(out)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (
        2,
        f"bundle: cannot bundle — {out} is a link\n",
    )
    assert target.read_text() == "kept\n"

    # A bundle path the rename cannot replace leaves no staged file.
    out.unlink()
    out.mkdir()
    code, said = _run(capsys, out)
    assert code == 2 and said.startswith(f"bundle: cannot bundle — {out}: ")
    assert not out.with_name("bundle.md.tmp").exists()
