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
    # A bare span is a path only with a `/` or a file suffix, and a card that gives a
    # path a line names it bare nowhere: a shared function name, or a far line on the
    # file the card also names bare, matches nothing.
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
    # A span with a line is a path whatever its shape, and a bare span only with a `/`
    # or a named file suffix: neighbouring `Makefile` lines match, and a method name
    # on far lines of one file does not.
    make = _card("S1", "high", "the gate in `Makefile` (`Makefile:12`)")
    ship = _card("S2", "medium", "`Run.ship` in `conduct.py` (`conduct.py:100`)")
    assert overlap.overlap(
        [make, ship],
        [
            _card("S8", "medium", "`Run.ship` in `conduct.py` (`conduct.py:3000`)"),
            _card("S9", "medium", "the gate in `Makefile` (`Makefile:14`)"),
        ],
        ("high",),
    ) == {
        "shared": 1,
        "primary_alone": 1,
        "shadow_alone": 1,
        "shared_blockers": 1,
        "primary_blockers": 0,
        "shadow_blockers": 0,
    }
    assert [overlap.anchors(card) for card in (make, ship)] == [
        [("Makefile", 12, 12)],
        [("conduct.py", 100, 100)],
    ]


def test_the_overlap_refuses_what_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    (folder / "shadow-adversarial.md").unlink()
    assert overlap.main([str(folder)]) == 2
    missing = folder / "shadow-adversarial.md"
    assert capsys.readouterr().out == f"overlap: cannot read — {missing}\n"


# The pin: `overlap.py`'s copy of the findings format, as it stands.
# Why: 0138-findings design D2, its case l.


def test_pin_l_overlap_card_runs_to_a_title_or_heading() -> None:
    first = "- **R1 — a**\n  - **Status:** open\n\n  - **Fix:** f\n"
    second = "- **A4 — b**\n  - **Status:** fixed\n"

    found = overlap.cards(f"{first}## Refuted\n  - **Fix:** g\n{second}")

    assert found == [first, second]


# The fix: `overlap.py` on the module's one form; its case l turns.
# Why: 0138-findings design D2, D4, D5, D7, D8 and D9.


def test_fix_extent_overlap_a_card_ends_at_an_unindented_line() -> None:
    first = "- **R1 — a**\n  - **Status:** open\n\n  - **Fix:** f\n"
    second = "- **S4 — b**\n  - **Status:** fixed\n"

    assert overlap.cards(f"{first}a line\n  - **Fix:** g\n{second}") == [
        first,
        second,
    ]


def test_fix_field_overlap_reads_a_colon_outside() -> None:
    title = "- **R1 — a**\n"
    for colon in (":**", "**:"):
        assert overlap.anchors(f"{title}  - **What it affects{colon} `a.py:1`\n") == [
            ("a.py", 1, 1)
        ], colon
        card = f"{title}  - **Priority{colon} blocking · c\n"
        assert overlap.overlap([card], [], ("blocking",))["primary_blockers"] == 1
        assert not overlap.first_round(f"{title}  - **Round{colon} 2\n"), colon
    assert overlap.anchors(f"{title}- **What it affects:** `a.py:1`\n") == []
    assert overlap.first_round(title)


def test_fix_word_overlap_reads_a_grade_as_a_word() -> None:
    for grade in ("blocking", "**blocking**", "`Blocking`"):
        card = f"- **R1 — a**\n  - **Priority:** {grade} · c\n"
        assert overlap.overlap([card], [], ("blocking",))["primary_blockers"] == 1
    nit = "- **R1 — a**\n  - **Priority:** nit · c\n"
    assert overlap.overlap([nit], [], ("blocking",))["primary_blockers"] == 0


def test_fix_frontmatter_overlap_reads_the_whole_value() -> None:
    for text, executor in (
        ("---\nexecutor: codex\n---\n", "codex"),
        ("---\nexecutor:  codex  \n---\n", "codex"),
        ("---\nexecutor: codex # x\n---\n", "codex # x"),
        ("---\nexecutor:\n---\n", "unknown"),
        ("executor: codex\n", "unknown"),
        ("---\nhead: a\n---\nexecutor: codex\n", "unknown"),
    ):
        assert overlap.executor(text) == executor, text


def test_fix_ids_overlap_refuses_a_card_off_the_ids(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    held = folder / "conformance.md"
    held.write_text(held.read_text().replace("- **R1 — ", "- **R-1 — "))

    with pytest.raises(overlap.Unread) as unread:
        overlap.line(folder)

    assert str(unread.value) == f"{held}: card R-1 is not R<n> or S<n>"


def test_fix_read_overlap_replaces_a_bad_byte(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    counted = overlap.line(folder)
    held = folder / "adversarial.md"
    held.write_bytes(held.read_bytes() + b"\xff\n")

    assert overlap.line(folder) == counted


def test_fix_read_overlap_refuses_a_link(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    target = tmp_path / "target.md"
    (folder / "conformance.md").rename(target)
    (folder / "conformance.md").symlink_to(target)

    assert overlap.main([str(folder)]) == 2
    assert capsys.readouterr().out == (
        f"overlap: cannot read — {folder / 'conformance.md'}\n"
    )
