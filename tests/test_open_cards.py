"""Converge's open cards: what a verify worker judges, out of its findings file.

Each file written under `tmp_path`. Why: 0095-converge-roles design D10.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "open_cards.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("open_cards", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


open_cards = _load(_SCRIPT)


def _card(card: str, status: str) -> str:
    return (
        f"- **{card} — a finding**\n"
        "  - **Priority:** blocking · conformance · stability — why.\n"
        f"  - **Status:** {status}\n"
    )


_OPEN = _card("R1", "open")
_FIXED = _card("R2", "`fixed` — the guard is back")
_WONTFIX = _card("R3", "wontfix — the design asks for it")
_FRONT = "---\nverdict: changes-requested\nhead: a\nround: 2\n---\n\n## Findings\n\n"
_FILE = (
    _FRONT
    + _OPEN
    + _FIXED
    + _WONTFIX
    + _card("R4", "verified — held")
    + _card("R5", "accepted — the note holds")
    + "\n## Refuted\n\n- **x.** why\n\n## Resolution log\n\n- d · round 1 · R2 fixed\n"
)


def _run(
    capsys: pytest.CaptureFixture[str], findings: Path, out: Path
) -> tuple[int, str]:
    code = open_cards.main([str(findings), str(out)])
    return code, capsys.readouterr().out


def test_open_cards_extract_what_a_verify_judges(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings, out = tmp_path / "conformance.md", tmp_path / "conformance.open.md"
    findings.write_text(_FILE)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(findings), str(out)],
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "open cards: 3 of conformance.md\n")
    assert out.read_text() == (
        f"# conformance.md — the cards a verify judges\n\n{_OPEN}{_FIXED}{_WONTFIX}"
    )

    # A file with no card to judge writes `None.` over the last.
    findings.write_text(_FRONT + _card("R4", "verified — held"))
    assert _run(capsys, findings, out) == (0, "open cards: 0 of conformance.md\n")
    assert out.read_text() == "# conformance.md — the cards a verify judges\n\nNone.\n"


def test_open_cards_leave_a_bold_bullet_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings, out = tmp_path / "conformance.md", tmp_path / "conformance.open.md"
    findings.write_text(_FRONT + "## Passes\n\n- **stale-claim** — ran.\n\n" + _OPEN)

    assert _run(capsys, findings, out) == (0, "open cards: 1 of conformance.md\n")
    assert out.read_text() == f"# conformance.md — the cards a verify judges\n\n{_OPEN}"


def test_open_cards_refuse_what_they_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings, out = tmp_path / "adversarial.md", tmp_path / "adversarial.open.md"
    assert _run(capsys, findings, out) == (
        2,
        f"open cards: cannot read — {findings}: No such file or directory\n",
    )
    assert not out.exists()

    findings.write_text(_FILE)
    target = tmp_path / "elsewhere.md"
    target.write_text("theirs\n")
    out.symlink_to(target)
    assert _run(capsys, findings, out) == (
        2,
        f"open cards: cannot read — {out} is a link\n",
    )
    assert target.read_text() == "theirs\n"
    out.unlink()

    # A staged file that cannot be written leaves no out file.
    (tmp_path / "adversarial.open.md.tmp").mkdir()
    code, said = _run(capsys, findings, out)
    assert code == 2 and said.startswith(f"open cards: cannot read — {out}: ")
    assert not out.exists()
    (tmp_path / "adversarial.open.md.tmp").rmdir()

    # A Status in another case, or in bold, is judged as its folded word.
    folded = _card("S1", "`Fixed` — guarded the path") + _card(
        "S2", "**WONTFIX** — why"
    )
    findings.write_text(_FRONT + folded + _card("S3", "Verified — held"))
    assert _run(capsys, findings, out) == (0, "open cards: 2 of adversarial.md\n")
    assert (
        out.read_text() == f"# adversarial.md — the cards a verify judges\n\n{folded}"
    )
    out.unlink()

    # Any other Status, none at all, or a Status line under no card fails closed.
    for card, why in (
        (_card("S4", "reopened — the guard is gone"), "card S4: Status reopened"),
        (_card("S5", "won't fix — by design"), "card S5: Status won't"),
        ("- **S6 — a finding**\n  - **Round:** 1\n", "card S6: no Status"),
        (
            "- **S7: off the form**\n  - **Status:** fixed\n",
            "a Status under no card: S7",
        ),
        ("## Findings\n\n  - **Status:** fixed\n", "a Status under no card: unnamed"),
    ):
        findings.write_text(_FRONT + _OPEN + card)
        assert _run(capsys, findings, out) == (2, f"open cards: cannot read — {why}\n")
        assert not out.exists()
