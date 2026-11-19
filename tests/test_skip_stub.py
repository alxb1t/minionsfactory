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

    # A checker's file holding a round not yet cleared is kept: the person clears it.
    front = "---\ntype: adversarial\nmode: parallel\nverdict: {}\n---\n\n"
    card = "- **S1 — a finding**\n  - **Status:** {}\n"
    held = (
        f"{stub} holds a checker's round not cleared: clearing it is the person's act"
    )
    for text in (
        front.format("changes-requested"),
        front.format("clean") + card.format("open"),
        front.format("clean") + card.format("fixed — a test"),
        front.format("clean") + card.format("wontfix — the card is wrong"),
        front.format("clean") + card.format("verified") + card.format("accepted"),
    ):
        stub.write_text(text)
        refused([str(stub), "1"], held)
        assert stub.read_text() == text
    for text in (
        front.format("clean") + card.format("verified") + card.format("verified"),
        "---\nmode: skipped\nverdict: changes-requested\n---\n",
    ):
        stub.write_text(text)
        assert skip_stub.main([str(stub), "1"]) == 0
        assert "\nmode: skipped\n" in stub.read_text()
        capsys.readouterr()
    stub.unlink()

    missing = folder.parent / "0002-b" / "adversarial.md"
    refused([str(missing), "1"], "adversarial.md could not be written")

    bare = tmp_path / "bare"
    (bare / "changes" / _CHANGE).mkdir(parents=True)
    monkeypatch.chdir(bare)
    unborn = bare / "changes" / _CHANGE / "conformance.md"
    refused([str(unborn), "1"], "no repository with a commit here")
    assert not unborn.exists()


def test_case_g_the_file_replaced_is_read_with_a_bad_byte_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Why: 0136-status-log design, the pin.
    folder = _repo(tmp_path / "proj", monkeypatch)
    stub = folder / "adversarial.md"
    stub.write_bytes(b"---\nmode: skipped\n---\n\xff\n")
    assert skip_stub.main([str(stub), "1"]) == 0
    assert "\nmode: skipped\n" in stub.read_text()
    capsys.readouterr()
    # Twin: the text past the bad byte is read, so a round not cleared is kept.
    held = b"---\nmode: parallel\nverdict: changes-requested\n---\n\xff\n"
    stub.write_bytes(held)
    assert skip_stub.main([str(stub), "1"]) == 2
    assert "holds a checker's round not cleared" in capsys.readouterr().out
    assert stub.read_bytes() == held


# The pin: `skip_stub.py`'s copy of the findings format, as it stands.
# Why: 0138-findings design D2, its case m.

_PIN_CLEAN = "---\nverdict: clean\n---\n\n"


def _pin_status(status: str) -> str:
    return f"- **S1 — a**\n  - **Status:** {status}\n"


def test_pin_m_uncleared_clears_on_verified_alone() -> None:
    assert not skip_stub.uncleared(_PIN_CLEAN + _pin_status("verified"))
    for status in ("accepted", "fixed", "wontfix"):
        assert skip_stub.uncleared(_PIN_CLEAN + _pin_status(status)), status


def test_pin_m_role_of_refuses_a_path_off_the_form(tmp_path: Path) -> None:
    folder = tmp_path / "changes" / _CHANGE
    folder.mkdir(parents=True)
    assert skip_stub.role_of(folder / "conformance.md") == "conformance"
    for path in (
        folder / "conformance.txt",
        folder / "review.md",
        tmp_path / "other" / _CHANGE / "conformance.md",
    ):
        with pytest.raises(skip_stub.Stop, match="is not …/changes/"):
            skip_stub.role_of(path)
    (folder / "adversarial.md").symlink_to(tmp_path / "target.md")
    with pytest.raises(skip_stub.Stop, match=r"is a link$"):
        skip_stub.role_of(folder / "adversarial.md")
    (tmp_path / "changes" / "0002-b").symlink_to(folder)
    with pytest.raises(skip_stub.Stop, match=r"is a link$"):
        skip_stub.role_of(tmp_path / "changes" / "0002-b" / "conformance.md")


def test_pin_link_skip_stub_write_refuses_a_link(tmp_path: Path) -> None:
    target = tmp_path / "target.md"
    target.write_text(_PIN_CLEAN + _pin_status("verified"))
    stub = tmp_path / "adversarial.md"
    stub.symlink_to(target)

    with pytest.raises(skip_stub.Stop, match=r"is a link$"):
        skip_stub.write(stub, "stub\n")

    assert target.read_text() == _PIN_CLEAN + _pin_status("verified")


# The fix: `skip_stub.py` on the module's one form; its case m turns, but `verified`.
# Why: 0138-findings design D2, D4, D5, D7, D8 and D11.


def test_fix_frontmatter_skip_stub_reads_the_leading_block() -> None:
    open_card = _pin_status("open")
    assert skip_stub.uncleared("mode: skipped\n---\n" + open_card)
    assert skip_stub.uncleared("mode: parallel\n---\n" + open_card)
    assert not skip_stub.uncleared(
        "---\nmode: skipped\nverdict: changes-requested\n---\n" + open_card
    )


def test_fix_field_skip_stub_reads_a_colon_outside() -> None:
    assert skip_stub.uncleared(_PIN_CLEAN + "- **S1 — a**\n  - **Status**: open\n")
    assert not skip_stub.uncleared(
        _PIN_CLEAN + "- **S1 — a**\n  - **Status**: verified\n"
    )


def test_fix_word_skip_stub_reads_the_status_word() -> None:
    for status in ("`open`", "**open**", "reopened", ""):
        assert skip_stub.uncleared(_PIN_CLEAN + _pin_status(status)), status
    for status in ("`Verified`", "**verified** — held"):
        assert not skip_stub.uncleared(_PIN_CLEAN + _pin_status(status)), status


def test_fix_first_skip_stub_reads_the_first_status() -> None:
    twice = _pin_status("verified") + "  - **Status:** open\n"
    assert not skip_stub.uncleared(_PIN_CLEAN + twice)
    assert skip_stub.uncleared(
        _PIN_CLEAN + _pin_status("open") + "  - **Status:** verified\n"
    )


def test_fix_ids_skip_stub_keeps_a_malformed_file(tmp_path: Path) -> None:
    stub = tmp_path / "adversarial.md"
    for body, why in (
        ("- **S-1 — a**\n  - **Status:** verified\n", "card S-1 is not R<n> or S<n>"),
        ("## Notes\n\n  - **Status:** verified\n", "a Status under no card: unnamed"),
    ):
        stub.write_text(_PIN_CLEAN + body)
        with pytest.raises(skip_stub.Stop) as stopped:
            skip_stub.write(stub, "stub\n")
        assert str(stopped.value) == f"{stub} is malformed: {why}"
        assert stub.read_text() == _PIN_CLEAN + body
    # Twin: the same card on the contract's ids is replaced.
    stub.write_text(_PIN_CLEAN + _pin_status("verified"))
    skip_stub.write(stub, "stub\n")
    assert stub.read_text() == "stub\n"
