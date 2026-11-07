"""Converge's debt match: the debt cards on the diff's files go into the bundle.

Each file written under `tmp_path`. Why: 0095-converge-roles design D8.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "debt_match.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("debt_match", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


debt_match = _load(_SCRIPT)

_SECTION = "## Debt cards on the diff's files"


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
    capsys: pytest.CaptureFixture[str], debt: Path, patch: Path, bundle: Path
) -> tuple[int, str]:
    code = debt_match.main([str(debt), str(patch), str(bundle)])
    return code, capsys.readouterr().out


def test_debt_match_bundles_the_cards_on_the_diffs_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    debt, patch, bundle = (
        tmp_path / "debt.md",
        tmp_path / "diff.patch",
        tmp_path / "b.md",
    )
    debt.write_text(_DEBT)
    patch.write_text(_PATCH)
    bundle.write_text("# 0003-c — bundle\n\n## Every decision\n\n- D1 · x\n")

    assert _run(capsys, debt, patch, bundle) == (
        0,
        "debt: 2 cards on the diff's files\n",
    )
    text = bundle.read_text()
    assert text.startswith("# 0003-c — bundle\n\n## Every decision\n\n- D1 · x\n")
    section = text.split(f"{_SECTION}\n\n")[1]
    assert section == f"{_A}{_X}"
    assert "0001·R2" not in text

    # A second run, as the conductor runs it, replaces the section, leaving one.
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(debt), str(patch), str(bundle)],
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "debt: 2 cards on the diff's files\n")
    assert bundle.read_text() == text

    # A section held above another keeps the one below.
    bundle.write_text(f"# t\n\n{_SECTION}\n\nstale\n\n## After\n\nkept\n")
    assert _run(capsys, debt, patch, bundle)[0] == 0
    assert bundle.read_text() == f"# t\n\n## After\n\nkept\n\n{_SECTION}\n\n{_A}{_X}"

    # No debt file matches none.
    debt.unlink()
    assert _run(capsys, debt, patch, bundle) == (
        0,
        "debt: 0 cards on the diff's files\n",
    )
    assert bundle.read_text().endswith(f"{_SECTION}\n\nNone.\n")


def test_debt_match_refuses_what_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    debt, patch, bundle = (
        tmp_path / "debt.md",
        tmp_path / "diff.patch",
        tmp_path / "b.md",
    )
    debt.write_text(_DEBT)
    patch.write_text(_PATCH)

    target = tmp_path / "elsewhere.md"
    target.write_text("theirs\n")
    bundle.symlink_to(target)
    assert _run(capsys, debt, patch, bundle) == (
        2,
        f"debt: cannot match — {bundle} is a link\n",
    )
    assert target.read_text() == "theirs\n"
    bundle.unlink()

    assert _run(capsys, debt, patch, bundle) == (
        2,
        f"debt: cannot match — {bundle}: No such file or directory\n",
    )
    bundle.write_text("# t\n")
    patch.unlink()
    assert _run(capsys, debt, patch, bundle) == (
        2,
        f"debt: cannot match — {patch}: No such file or directory\n",
    )
    assert bundle.read_text() == "# t\n"
    # A debt file that cannot be read is no missing one.
    patch.write_text(_PATCH)
    debt.write_bytes(b"\xff")
    code, said = _run(capsys, debt, patch, bundle)
    assert code == 2 and said.startswith(f"debt: cannot match — {debt}: ")
    # A staged file that cannot be written leaves the bundle as it stood.
    debt.write_text(_DEBT)
    (tmp_path / "b.md.tmp").mkdir()
    code, said = _run(capsys, debt, patch, bundle)
    assert code == 2 and said.startswith(f"debt: cannot match — {bundle}: ")
    assert bundle.read_text() == "# t\n"
