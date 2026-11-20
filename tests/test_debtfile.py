"""The debt file's writer and parser in the home, each function a case.

Why: 0139-debt design D2 and D3.
"""

import errno
import os
import threading
import time
from pathlib import Path

import pytest
from mflib import debtfile, statefile

_OLD = "- **0001·R1 — old**\n  - **Status:** open\n"
_NEW = "- **0001·R2 — new**\n  - **Status:** open\n"


def test_debtfile_read(tmp_path: Path) -> None:
    debt = tmp_path / "debt.md"
    assert debtfile.read(debt) == ""
    debt.write_bytes(b"# Debt\n\xff\n")
    assert debtfile.read(debt) == "# Debt\n�\n"
    debt.unlink()
    target = tmp_path / "target.md"
    target.write_text("# Debt\n")
    debt.symlink_to(target)
    with pytest.raises(debtfile.Unreadable) as linked:
        debtfile.read(debt)
    assert linked.value.reason == "it is a link"
    cause = linked.value.__cause__
    assert isinstance(cause, OSError)
    assert cause.errno == errno.ELOOP
    debt.unlink()
    debt.mkdir()
    with pytest.raises(debtfile.Unreadable) as folder:
        debtfile.read(debt)
    # why: Linux opens a folder and the read names its kind; macOS refuses the open
    assert folder.value.reason in {"it is not a file", "Is a directory"}
    debt.rmdir()

    os.mkfifo(debt)
    said: list[str] = []

    def piped() -> None:
        try:
            debtfile.read(debt)
        except debtfile.Unreadable as unread:
            said.append(unread.reason)

    reader = threading.Thread(target=piped, daemon=True)
    reader.start()
    # A FIFO opened blocking waits for a writer: the join bounds a red run.
    reader.join(10)
    assert not reader.is_alive()
    assert said == ["it is not a file"]


def test_debtfile_read_holds_the_title_and_the_preamble() -> None:
    assert debtfile.TITLE.pattern == r"^- \*\*([0-9]+·[^\s*]+) — "
    assert debtfile.PREAMBLE == (
        "# Debt\n\n*Deferred work from converge, one heading per change; a paydown"
        " change lists the ids it closes under `debt:`.*\n"
    )


def test_debtfile_ids() -> None:
    text = (
        "# Debt\n\n## 0001-a  \n\n- **0001·R1 — a**\n  - **0001·R9 — no title**\n"
        "-  **0001·R4 — d**\n- **0001·R5 —e**\n### a note\n- **0001·R2 — b**\n"
        "## 0000-z\n\n- **0000·R1 — z**\n## 0001-a\n- **0001·R3 — c**\n"
    )
    assert debtfile.ids(text) == ["0001·R1", "0001·R2", "0000·R1", "0001·R3"]
    # A heading's trailing blanks are forgiven; a section ends at the next `## `.
    assert debtfile.ids(text, "0001-a") == ["0001·R1", "0001·R2", "0001·R3"]
    assert debtfile.ids(text, "0000-z") == ["0000·R1"]
    assert debtfile.ids(text, "0002-b") == []
    assert debtfile.ids("- **0001·R1 — before any heading**\n", "0001-a") == []


def test_debtfile_title() -> None:
    text = (
        "# Debt\n\n## 0001-a\n\n- **0001·R1 — a**\n- **R2 — unqualified**\n"
        "- **001·R3 — three digits**\n- **0001R4 — no dot**\n- **0001·M1 — spoiled**\n"
        "- **00001·R5 — five digits**\n- **0001· — no id**\n"
        "## 0000-z\n\n- **0000·S1 — z**\n- **S2 — unqualified**\n"
    )
    assert debtfile.ids(text) == ["0001·R1", "001·R3", "0001·M1", "00001·R5", "0000·S1"]
    assert debtfile.ids(text, "0001-a") == ["0001·R1", "001·R3", "0001·M1", "00001·R5"]
    assert debtfile.count(text) == 5
    assert debtfile.count(text, "0001-a") == 4
    assert debtfile.count(text, "0000-z") == 1
    assert debtfile.count(text, "0002-b") == 0
    assert debtfile.count("") == 0
    assert debtfile.card_id("- **R2 — unqualified**\n") == ""


def test_debtfile_title_width() -> None:
    for number in ["1", "10000"]:
        card = debtfile.qualify(
            ["- **R1 — a title**", "  - **Status:** open"], "R1", f"{number}·R1"
        )
        assert debtfile.ids(card) == [f"{number}·R1"]
        assert debtfile.blocks(card) == [card]


def test_debtfile_blocks() -> None:
    text = (
        "# Debt\n\n## 0001-a\n\n"
        "- **0001·R1 — a**\n  - **Status:** open\n\n  - **Round:** 1\n"
        "- **0001·R2 — b**\n  - **Status:** open\n"
        "### a note\n  - **Round:** 2\n"
        "- **0001·R3 — c**\n\nloose prose\n  - **Round:** 3\n"
        "- **R4 — unqualified**\n  - **Status:** open\n"
    )
    assert debtfile.blocks(text) == [
        "- **0001·R1 — a**\n  - **Status:** open\n\n  - **Round:** 1\n",
        "- **0001·R2 — b**\n  - **Status:** open\n",
        "- **0001·R3 — c**\n",
    ]
    assert debtfile.blocks("# Debt\n\nno card\n") == []
    assert debtfile.card_id("- **0113·S4 — a title**\n  - x\n") == "0113·S4"
    assert debtfile.card_id("  - **0113·S4 — indented**\n") == ""
    assert debtfile.card_id("") == ""


def test_debtfile_match() -> None:
    patch = (
        "diff --git a/old.md b/new.md\n--- a/old.md\n"
        "diff --git a/src/a.py b/src/a.py\n"
        "not diff --git a/x.md b/x.md\n"
    )
    assert debtfile.paths(patch) == {"old.md", "new.md", "src/a.py"}
    assert debtfile.paths("") == set()
    card = (
        "- **0001·R1 — a**\n"
        "  - **What it affects:** `docs/x.md` and `src/a.py:12-14`.\n"
    )
    assert debtfile.matched(card, {"src/a.py"})
    assert debtfile.matched(card, {"docs/x.md"})
    assert not debtfile.matched(card, {"src/b.py"})
    flush = "- **0001·R1 — a**\n- **What it affects:** `src/a.py`.\n"
    assert not debtfile.matched(flush, {"src/a.py"})
    assert not debtfile.matched("- **0001·R1 — a**\n", {"src/a.py"})
    assert debtfile.page([]) == "# Debt cards on the diff's files\n\nNone.\n"
    assert debtfile.page([card, card]) == (
        f"# Debt cards on the diff's files\n\n{card}{card}"
    )


def test_debtfile_filed() -> None:
    assert debtfile.filed("# Debt\n", "0001-a", []) == "# Debt\n"
    assert debtfile.filed("# Debt\n\n", "0001-a", [_NEW]) == (
        f"# Debt\n\n## 0001-a\n\n{_NEW}"
    )
    # A heading with trailing blanks is found, and no second one is written.
    blank = f"# Debt\n\n## 0001-a  \n\n{_OLD}"
    assert debtfile.filed(blank, "0001-a", [_NEW]) == f"{blank}{_NEW}"
    assert debtfile.filed(blank, "0001-ab", [_NEW]) == (
        f"{blank.rstrip()}\n\n## 0001-ab\n\n{_NEW}"
    )
    # A `### ` line is inside; the cards go after the last non-blank line.
    inner = f"# Debt\n\n## 0001-a\n\n{_OLD}### a note\n"
    other = "## 0000-z\n\n- **0000·R1 — z**\n"
    assert debtfile.filed(f"{inner}\n\n{other}", "0001-a", [_NEW]) == (
        f"{inner}{_NEW}\n\n{other}"
    )
    assert debtfile.filed(f"{inner}{other}", "0001-a", [_NEW]) == (
        f"{inner}{_NEW}\n{other}"
    )
    assert debtfile.filed(f"{inner}\n", "0001-a", [_NEW]) == f"{inner}{_NEW}\n"
    assert debtfile.filed("## 0001-a", "0001-a", [_NEW]) == f"## 0001-a\n{_NEW}"


def test_debtfile_unfiled() -> None:
    gapped = "- **0001·R3 — gapped**\n  - **Status:** open\n\n  - **Round:** 1\n"
    text = (
        f"# Debt\n\n## 0001-a\n\n{_OLD}{gapped}{_NEW}\n## 0000-z\n\n- **0000·R1 — z**\n"
    )
    # The card's extent holds its blank line and its indented lines, the id whole.
    assert debtfile.unfiled(text, "0001·R3") == (
        f"# Debt\n\n## 0001-a\n\n{_OLD}{_NEW}\n## 0000-z\n\n- **0000·R1 — z**\n"
    )
    # An emptied section loses its heading.
    alone = f"# Debt\n\n## 0001-a\n\n{_OLD}\n## 0000-z\n\n- **0000·R1 — z**\n"
    assert debtfile.unfiled(alone, "0001·R1") == (
        "# Debt\n\n## 0000-z\n\n- **0000·R1 — z**\n"
    )
    assert debtfile.unfiled(f"{_OLD}", "0001·R1") == ""
    with pytest.raises(StopIteration):
        debtfile.unfiled(text, "0001·R")


def test_debtfile_clear() -> None:
    text = f"# Debt\n\n## 0001-a\n\n{_OLD}{_NEW}\n## 0000-z\n\n- **0000·R1 — z**\n"
    assert debtfile.clear(text, []) == text
    assert debtfile.clear(text, ["0001·R2", "0000·R1"]) == (
        f"# Debt\n\n## 0001-a\n\n{_OLD}\n"
    )
    assert debtfile.clear(text, ["0001·R1", "0001·R2"]) == (
        "# Debt\n\n## 0000-z\n\n- **0000·R1 — z**\n"
    )
    with pytest.raises(StopIteration):
        debtfile.clear(text, ["0001·R1", "0001·R1"])


def test_debtfile_spoiled() -> None:
    where = ".minions/changes/0001-a/adversarial.md"
    card = debtfile.spoiled("0001", 2, "adversarial", "no verdict", 3, "0001-a", where)
    assert card.startswith(
        "- **0001·M2 — adversarial's findings file was malformed after a rewrite**\n"
    )
    assert debtfile.ids(card) == ["0001·M2"]
    assert f"  - **What it affects:** `{where}`.\n" in card
    assert "  - **Evidence:** no verdict · read.\n" in card
    assert "  - **Round:** 3\n" in card
    assert "  - **Trigger:** the release of 0001-a.\n" in card
    assert f"  - **Still true?** read `{where}` against the contract.\n" in card
    assert card.endswith("  - **Related:** none.\n  - **Status:** open\n")


def test_debtfile_qualify() -> None:
    lines = ["- **R2 — a title, R2 — kept**", "  - **Status:** open"]
    assert debtfile.qualify(lines, "R2", "0001·R2") == (
        "- **0001·R2 — a title, R2 — kept**\n  - **Status:** open\n"
    )
    assert debtfile.qualify(["- **S1 — b**"], "R2", "0001·R2") == "- **S1 — b**\n"


def test_debtfile_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    held = tmp_path / "debt.lock"
    assert debtfile.LOCK_POLL == 5
    with debtfile.lock(held):
        assert held.is_dir()
    assert not os.path.lexists(held)
    with pytest.raises(RuntimeError), debtfile.lock(held):
        raise RuntimeError
    assert not os.path.lexists(held)

    waits: list[float] = []
    monkeypatch.setattr(time, "sleep", waits.append)
    held.mkdir()
    with pytest.raises(debtfile.Held), debtfile.lock(held):
        pass
    assert waits == []
    with pytest.raises(debtfile.Held), debtfile.lock(held, 12):
        pass
    assert waits == [5, 5, 5]
    assert held.is_dir()

    waits.clear()
    monkeypatch.setattr(time, "sleep", lambda s: (waits.append(s), held.rmdir()))
    with debtfile.lock(held, 600):
        assert held.is_dir()
    assert waits == [5]
    assert not os.path.lexists(held)


def _age(path: Path, seconds: float) -> None:
    at = time.time() - seconds
    os.utime(path, (at, at), follow_symlinks=False)


def test_debtfile_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    held = tmp_path / "debt.lock"
    owner = held / "owner"
    with debtfile.lock(held) as first:
        token = owner.read_text()
        assert first.token == token and first.holds()
        assert oct(owner.stat().st_mode & 0o777) == "0o600"
    assert not os.path.lexists(held)
    with debtfile.lock(held) as second:
        assert second.token != token

    # The renewal sets the lock's time; a run's start then leaves a live hold.
    with debtfile.lock(held) as holder:
        _age(held, 700)
        holder.renew()
        assert debtfile.break_stale(held, 600) is None
        assert held.is_dir() and holder.holds()

    # A lock broken and taken by another stands after the release, and no error.
    with debtfile.lock(held) as holder:
        owner.unlink()
        held.rmdir()
        held.mkdir()
        owner.write_text("another\n")
        _age(held, 700)
        holder.renew()
        assert not holder.holds()
    assert owner.read_text() == "another\n"
    assert debtfile.break_stale(held, 600) is not None
    # A lock gone is no error.
    with debtfile.lock(held) as holder:
        owner.unlink()
        held.rmdir()
        holder.renew()
    assert not os.path.lexists(held)

    # A token that cannot be written takes no lock.
    def refused(*_: object) -> int:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "open", refused)
    with pytest.raises(OSError, match="No space"), debtfile.lock(held):
        pass
    monkeypatch.undo()
    assert not os.path.lexists(held)


def test_debtfile_token_break_stale(tmp_path: Path) -> None:
    held = tmp_path / "debt.lock"
    assert debtfile.break_stale(held, 600) is None
    held.write_text("")
    _age(held, 700)
    assert debtfile.break_stale(held, 600) is None
    held.unlink()
    held.symlink_to(tmp_path)
    _age(held, 700)
    assert debtfile.break_stale(held, 600) is None
    assert held.is_symlink()
    held.unlink()

    held.mkdir()
    (held / "owner").write_text("x\n")
    _age(held, 600)
    assert debtfile.break_stale(held, 600) is None
    _age(held, 601)
    assert debtfile.break_stale(held, 600) == 601
    assert not os.path.lexists(held)
    # A lock with no owner, the release prose's, is broken as any other.
    held.mkdir()
    _age(held, 700)
    assert debtfile.break_stale(held, 600) == 700
    assert not os.path.lexists(held)

    held.mkdir()
    (held / "owner").write_text("x\n")
    (held / "other").write_text("")
    _age(held, 700)
    assert debtfile.break_stale(held, 600) is None
    assert sorted(os.listdir(held)) == ["other", "owner"]
    (held / "other").unlink()
    (held / "owner").unlink()
    (held / "owner").mkdir()
    _age(held, 700)
    assert debtfile.break_stale(held, 600) is None
    assert (held / "owner").is_dir()


def test_debtfile_write(tmp_path: Path) -> None:
    debt = tmp_path / "debt.md"
    debtfile.write(debt, "# Debt\n")
    assert debt.read_text() == "# Debt\n"
    target = tmp_path / "target.md"
    target.write_text("kept\n")
    debt.unlink()
    debt.symlink_to(target)
    with pytest.raises(statefile.WriteFailed) as failed:
        debtfile.write(debt, "# Debt\n")
    assert failed.value.error.errno == errno.ELOOP
    assert target.read_text() == "kept\n"

    held = tmp_path / "held"
    held.mkdir()
    fd = os.open(held, os.O_RDONLY | os.O_DIRECTORY)
    try:
        debtfile.write(Path("debt.md"), "# Held\n", folder=fd)
        (held / "link").symlink_to(held / "debt.md")
        with pytest.raises(statefile.WriteFailed):
            debtfile.write(Path("link"), "# Held\n", folder=fd)
    finally:
        os.close(fd)
    assert (held / "debt.md").read_text() == "# Held\n"
