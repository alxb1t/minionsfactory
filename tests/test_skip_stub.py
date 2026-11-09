"""A skipped checker's stub: its findings file written clean at `HEAD`, `mode: skipped`.

A repository under `tmp_path`, the script run in-process from inside it.
Why: 0105-converge-switches design D3.
"""

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "skip_stub.py"
_CHANGE = "0001-a"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("skip_stub", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


skip_stub = _load()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Commit one file in `root`, enter it, and return the change's run folder."""
    root.mkdir()
    _git(root, "init", "-q")
    (root / "a.txt").write_text("a\n")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-q", "-m", "base")
    monkeypatch.chdir(root)
    folder = root / ".minions" / "changes" / _CHANGE
    folder.mkdir(parents=True)
    return folder


def test_a_stub_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(skip_stub, "_today", lambda: date(2026, 11, 9))
    folder = _repo(tmp_path / "proj", monkeypatch)
    head = _git(tmp_path / "proj", "rev-parse", "HEAD")
    branch = _git(tmp_path / "proj", "branch", "--show-current")
    for role, round_ in (("adversarial", "2"), ("conformance", "1")):
        stub = folder / f"{role}.md"
        assert skip_stub.main([str(stub), round_]) == 0
        assert capsys.readouterr().out == (
            f"skip_stub: {stub} at {head[:7]} · round {round_}\n"
        )
        assert stub.read_text() == (
            f"---\ntype: {role}\nplan: {_CHANGE}\nproject: proj\nbranch: {branch}\n"
            f"head: {head}\nreviewed: 2026-11-09\nround: {round_}\nopen_blocking: 0\n"
            "verdict: clean\nmode: skipped\nworkers: 0\nmodel: none\nexecutor: none\n"
            "packet: skipped: all\n---\n\n"
            "Skipped by the plan: no worker judged this round.\n"
        )

    # A second call replaces the first stub: the round and the head it judges move.
    (tmp_path / "proj" / "b.txt").write_text("b\n")
    _git(tmp_path / "proj", "add", "b.txt")
    _git(tmp_path / "proj", "commit", "-q", "-m", "next")
    moved = _git(tmp_path / "proj", "rev-parse", "HEAD")
    assert skip_stub.main([str(folder / "adversarial.md"), "3"]) == 0
    text = (folder / "adversarial.md").read_text()
    assert f"head: {moved}\n" in text
    assert "round: 3\n" in text
    assert not list(folder.glob("*.tmp"))

    ran = subprocess.run(
        [sys.executable, str(_SCRIPT), str(folder / "conformance.md"), "4"],
        cwd=tmp_path / "proj",
        capture_output=True,
        text=True,
    )
    assert ran.returncode == 0
    assert "round: 4\n" in (folder / "conformance.md").read_text()


def test_a_stub_it_cannot_write_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _repo(tmp_path / "proj", monkeypatch)
    stub = folder / "adversarial.md"

    def refused(args: list[str], said: str) -> None:
        assert skip_stub.main(args) == 2
        assert capsys.readouterr().out == f"skip_stub: cannot stub — {said}\n"

    form = "is not …/changes/<change-id>/conformance.md or adversarial.md"
    other = folder / "review.md"
    refused([str(other), "1"], f"{other} {form}")
    loose = tmp_path / "x" / "conformance.md"
    refused([str(loose), "1"], f"{loose} {form}")
    refused(["conformance.md", "1"], f"conformance.md {form}")

    # A worker can write the run directory: no stub is written through a link.
    note = tmp_path / "note.md"
    note.write_text("kept\n")
    stub.symlink_to(note)
    refused([str(stub), "1"], f"{stub} is a link")
    assert note.read_text() == "kept\n"
    stub.unlink()
    moved = tmp_path / "moved"
    folder.rename(moved)
    folder.symlink_to(moved)
    refused([str(stub), "1"], f"{stub} is a link")
    assert list(moved.iterdir()) == []
    folder.unlink()
    moved.rename(folder)

    for bad in ("0", "-1", "x", "1.5", ""):
        refused([str(stub), bad], f"round {bad} is not a positive integer")
    assert not stub.exists()

    missing = folder.parent / "0002-b" / "adversarial.md"
    refused([str(missing), "1"], "adversarial.md could not be written")

    bare = tmp_path / "bare"
    (bare / "changes" / _CHANGE).mkdir(parents=True)
    monkeypatch.chdir(bare)
    unborn = bare / "changes" / _CHANGE / "conformance.md"
    refused([str(unborn), "1"], "no repository with a commit here")
    assert not unborn.exists()
