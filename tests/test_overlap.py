"""Converge's shadow overlap: what round 1 and its shadow each caught, and both.

Each findings file written under `tmp_path`. Why: 0097-cross-model design D10.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "overlap.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("overlap", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


overlap = _load(_SCRIPT)


def _card(card: str, grade: str, affects: str, round: str | None = "1") -> str:
    role = "adversarial" if card.startswith("S") else "conformance"
    held = f"  - **Round:** {round}\n" if round else ""
    return (
        f"- **{card} — a finding**\n"
        f"  - **What it affects:** {affects}\n"
        f"  - **Priority:** {grade} · {role} · stability — why.\n"
        f"{held}"
        "  - **Status:** open\n"
    )


def _file(executor: str | None, *cards: str) -> str:
    line = f"executor: {executor}\n" if executor else ""
    return f"---\nverdict: changes-requested\n{line}---\n\n## Findings\n\n" + "".join(
        cards
    )


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "0001-todo"
    folder.mkdir()
    files = {
        "conformance.md": _file(
            "codex",
            _card("R1", "blocking", "`total()` in `total.py` (`total.py:12`)"),
            _card("R2", "nit", "`notes.md:3`", round=None),
            _card("R3", "blocking", "`late.py:1`", round="2"),
        ),
        "shadow-conformance.md": _file(
            "claude",
            _card("R1", "drift", "`total.py:14`"),
            _card("R2", "blocking", "`README.md`"),
        ),
        "adversarial.md": _file(
            "codex",
            _card("S1", "high", "`a.py:40-42`"),
            _card("S2", "medium", "`a.py:44`"),
        ),
        "shadow-adversarial.md": _file(
            None,
            _card("S1", "critical", "`a.py:47`"),
            _card("S2", "low", "`a.py:60`"),
        ),
    }
    for name, text in files.items():
        (folder / name).write_text(text)
    return folder


def test_the_overlap_counts_shared_and_unique_catches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    line = (
        "conformance shared 1 · primary (codex) alone 1 · shadow (claude) alone 1 ·"
        " blockers shared 1 · primary 0 · shadow 1; adversarial shared 1 · primary"
        " (codex) alone 1 · shadow (unknown) alone 1 · blockers shared 1 · primary 0"
        " · shadow 0\n"
    )
    assert overlap.main([str(folder)]) == 0
    assert capsys.readouterr().out == line
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(folder)], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout) == (0, line)

    # A card near the line of another, or naming its path bare, matches it once; a
    # shadow card takes the first primary card it matches.
    near, far = _card("R1", "blocking", "`x.py:10`"), _card("R2", "nit", "`x.py:20`")
    assert overlap.overlap(
        [near, far, _card("R3", "nit", "`x.py:30`")],
        [_card("R9", "nit", "`x.py:15`"), _card("R8", "blocking", "`x.py`")],
        ("blocking",),
    ) == {
        "shared": 2,
        "primary_alone": 1,
        "shadow_alone": 0,
        "shared_blockers": 2,
        "primary_blockers": 0,
        "shadow_blockers": 0,
    }
    # Twin: past `NEAR`, or on another path, nothing matches.
    assert overlap.overlap(
        [near], [_card("R9", "nit", "`x.py:16`"), _card("R8", "nit", "`y.py:10`")], ()
    ) == {
        "shared": 0,
        "primary_alone": 1,
        "shadow_alone": 2,
        "shared_blockers": 0,
        "primary_blockers": 0,
        "shadow_blockers": 0,
    }
    # A span is a path only with a `/` or a file suffix, and a card that gives a path a
    # line names it bare nowhere: a shared function name, or a far line on the file
    # the card also names bare, matches nothing.
    held = _card("S1", "high", "`main()` in `a.py` (`a.py:10`)")
    assert overlap.overlap(
        [held],
        [
            _card("S9", "high", "`main()` in `b.py` (`b.py:900`)"),
            _card("S8", "high", "`main()` in `a.py` (`a.py:400`)"),
            _card("S7", "high", "`os.O_RDONLY` and `:1079` in `skills/x/run`"),
        ],
        ("high",),
    ) == {
        "shared": 0,
        "primary_alone": 1,
        "shadow_alone": 3,
        "shared_blockers": 0,
        "primary_blockers": 1,
        "shadow_blockers": 3,
    }
    assert overlap.anchors(held) == [("a.py", 10, 10)]


def test_the_overlap_refuses_what_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    (folder / "shadow-adversarial.md").unlink()
    assert overlap.main([str(folder)]) == 2
    missing = folder / "shadow-adversarial.md"
    assert capsys.readouterr().out == f"overlap: cannot read — {missing}\n"
    (folder / "conformance.md").write_bytes(b"\xff\xfe")
    assert overlap.main([str(folder)]) == 2
    unreadable = folder / "conformance.md"
    assert capsys.readouterr().out == f"overlap: cannot read — {unreadable}\n"
