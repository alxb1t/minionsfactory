"""Converge's debt match: the debt cards on the diff's files go to their own file.

Each file written under `tmp_path`. Why: 0095-converge-roles design D8;
0101-cut-converge-diet design D4.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
from mflib import debtfile

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "debt_match.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("debt_match", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


debt_match = _load(_SCRIPT)

_HEADING = "# Debt cards on the diff's files"


def _card(card: str, affects: str) -> str:
    return (
        f"- **{card} — a finding**\n"
        "  - **Why it's a problem:** a harm.\n"
        f"  - **What it affects:** {affects}.\n"
        "  - **Status:** open\n"
    )


_A = _card("0001·R1", "`save()` in `src/a.py` (`src/a.py:12`)")
_B = _card("0001·R2", "`src/b.py`")
_X = _card("0002·S1", "the intro (`docs/x.md:3-9`)")
_DEBT = f"# Debt\n\nDeferred work.\n\n## 0001-a\n\n{_A}{_B}\n## 0002-b\n\n{_X}"
_PATCH = (
    "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n"
    "diff --git a/docs/old.md b/docs/x.md\nrename from docs/old.md\n"
)


def _run(
    capsys: pytest.CaptureFixture[str], debt: Path, patch: Path, cards: Path
) -> tuple[int, str]:
    code = debt_match.main([str(debt), str(patch), str(cards)])
    return code, capsys.readouterr().out


def test_debt_match_bundles_the_cards_on_the_diffs_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    debt, patch, cards = (
        tmp_path / "debt.md",
        tmp_path / "diff.patch",
        tmp_path / "debt-cards.md",
    )
    debt.write_text(_DEBT)
    patch.write_text(_PATCH)

    assert _run(capsys, debt, patch, cards) == (
        0,
        "debt: 2 cards on the diff's files\n",
    )
    text = cards.read_text()
    assert text == f"{_HEADING}\n\n{_A}{_X}"
    assert "0001·R2" not in text

    # A second run, as the conductor runs it, writes the same.
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(debt), str(patch), str(cards)],
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "debt: 2 cards on the diff's files\n")
    assert cards.read_text() == text

    # A stale file is replaced whole.
    cards.write_text("# t\n\nstale\n\n## After\n\nkept\n")
    assert _run(capsys, debt, patch, cards)[0] == 0
    assert cards.read_text() == text

    # No debt file matches none.
    debt.unlink()
    assert _run(capsys, debt, patch, cards) == (
        0,
        "debt: 0 cards on the diff's files\n",
    )
    assert cards.read_text() == f"{_HEADING}\n\nNone.\n"


def test_debt_match_refuses_what_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    debt, patch, cards = (
        tmp_path / "debt.md",
        tmp_path / "diff.patch",
        tmp_path / "debt-cards.md",
    )
    debt.write_text(_DEBT)
    patch.write_text(_PATCH)

    target = tmp_path / "elsewhere.md"
    target.write_text("theirs\n")
    cards.symlink_to(target)
    assert _run(capsys, debt, patch, cards) == (
        2,
        f"debt: cannot match — {cards} is a link\n",
    )
    assert target.read_text() == "theirs\n"
    cards.unlink()

    # A missing cards file is written.
    assert _run(capsys, debt, patch, cards) == (
        0,
        "debt: 2 cards on the diff's files\n",
    )
    assert cards.read_text() == f"{_HEADING}\n\n{_A}{_X}"
    cards.write_text("# t\n")
    patch.unlink()
    assert _run(capsys, debt, patch, cards) == (
        2,
        f"debt: cannot match — {patch}: No such file or directory\n",
    )
    assert cards.read_text() == "# t\n"
    # A debt file that cannot be read is no missing one.
    patch.write_text(_PATCH)
    debt.unlink()
    debt.mkdir()
    code, said = _run(capsys, debt, patch, cards)
    assert code == 2 and said.startswith(f"debt: cannot match — {debt}: ")
    assert cards.read_text() == "# t\n"
    debt.rmdir()
    # A staged file that cannot be written leaves the cards file as it stood.
    debt.write_text(_DEBT)
    (tmp_path / "debt-cards.md.tmp").mkdir()
    code, said = _run(capsys, debt, patch, cards)
    assert code == 2 and said.startswith(f"debt: cannot match — {cards}: ")
    assert cards.read_text() == "# t\n"


def test_debt_pin_match(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Why: 0139-debt design D1, the pin of `debt_match.py` as it stands.
    assert debtfile.paths(
        "diff --git a/old.md b/new.md\n diff --git a/no.md b/no.md\n"
        "diff --git a/src/a.py b/src/a.py\n"
    ) == {"old.md", "new.md", "src/a.py"}
    # A blank line does not end a card; a line at column 0 does.
    debt = (
        "# Debt\n\n## 0001-a\n\n- **0001·R1 — one**\n  - **Fix:** x\n\n"
        "  - **What it affects:** `a.py`\nloose prose\n  - **Round:** 1\n"
        "- **R2 — two**\n  - **What it affects:** `b.py`\n### a note\n"
        "  - **Status:** open\n"
    )
    assert debtfile.blocks(debt) == [
        "- **0001·R1 — one**\n  - **Fix:** x\n\n  - **What it affects:** `a.py`\n",
    ]
    assert debtfile.matched(debtfile.blocks(debt)[0], {"a.py"})
    card = (
        "- **0001·R1 — a**\n"
        "  - **What it affects:** `save()` in `src/a.py:12`, `docs/x.md:3-9`\n"
        "  - **Fix:** `src/c.py`\n"
    )
    for changed in ({"src/a.py"}, {"docs/x.md"}, {"save()"}):
        assert debtfile.matched(card, changed), changed
    assert not debtfile.matched(card, {"src/c.py"})
    flat = "- **0001·R1 — a**\n- **What it affects:** `src/a.py`\n"
    assert not debtfile.matched(flat, {"src/a.py"})

    patch, cards = tmp_path / "diff.patch", tmp_path / "debt-cards.md"
    patch.write_text(_PATCH)
    # A link halts, dangling or not, and is never followed.
    linked, target = tmp_path / "debt.md", tmp_path / "target.md"
    linked.symlink_to(target)
    refused = (2, f"debt: cannot match — {linked}: it is a link\n")
    assert _run(capsys, linked, patch, cards) == refused
    assert not cards.exists()
    target.write_text(_DEBT)
    assert _run(capsys, linked, patch, cards) == refused
    assert not cards.exists()
    linked.unlink()
    # A bad byte is replaced, and the cards still match.
    linked.write_bytes(_DEBT.encode() + b"\xff\n")
    assert _run(capsys, linked, patch, cards) == (
        0,
        "debt: 2 cards on the diff's files\n",
    )
    assert cards.read_text() == f"{_HEADING}\n\n{_A}{_X}"
